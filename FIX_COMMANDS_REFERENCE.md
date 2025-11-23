# QUICK COMMAND REFERENCE - v2.0.19 Fixes

**Copy-paste these commands directly into your terminal**

---

## 🔴 CRITICAL FIX #1: Template Filter Bug (5 minutes)

### Fix the intcomma filter

```bash
# Backup current file
cp apps/reports/templatetags/report_filters.py apps/reports/templatetags/report_filters.py.backup

# Apply fix (replaces entire file)
cat > apps/reports/templatetags/report_filters.py << 'EOF'
"""
Custom template filters for reports.
"""

from django import template
from decimal import Decimal, InvalidOperation
from django.contrib.humanize.templatetags.humanize import intcomma as django_intcomma

register = template.Library()


@register.filter
def multiply(value, arg):
    """
    Multiply the value by the argument.
    Usage: {{ value|multiply:3 }}
    """
    try:
        if value is None or arg is None:
            return 0
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError, InvalidOperation):
        return 0


@register.filter
def intcomma(value, use_l10n=True):
    """
    Format a number with thousand separators (commas).
    Usage: {{ value|intcomma }}
    Example: 26970 -> "26,970"

    This is a wrapper around Django's built-in humanize intcomma.
    """
    return django_intcomma(value, use_l10n=use_l10n)
EOF

# Restart services
docker restart azure-advisor-backend azure-advisor-celery

# Or if using systemd
# sudo systemctl restart azure-advisor-backend
# sudo systemctl restart azure-advisor-celery
```

### Verify the fix

```bash
python manage.py shell << 'PYEOF'
from django.template import Context, Template

# Test intcomma
t = Template("{% load report_filters %}{{ value|intcomma }}")
r = t.render(Context({'value': 12345}))
print(f"Test 1: {r} (expected: 12,345)")

# Test combined
t = Template("{% load report_filters %}{{ value|floatformat:0|intcomma }}")
r = t.render(Context({'value': 12345.67}))
print(f"Test 2: {r} (expected: 12,346)")

# Test currency
t = Template("{% load report_filters %}"${{ value|floatformat:0|intcomma }}")
r = t.render(Context({'value': 125450.50}))
print(f"Test 3: {r} (expected: $125,451)")
PYEOF
```

**Expected output:**
```
Test 1: 12,345 (expected: 12,345)
Test 2: 12,346 (expected: 12,346)
Test 3: $125,451 (expected: $125,451)
```

---

## 🟡 FIX #2: Database Diagnostic (3 minutes)

### Run diagnostic script

```bash
# Run diagnostic
python manage.py shell < scripts/diagnose_database_state.py

# Or save output to file
python manage.py shell < scripts/diagnose_database_state.py > diagnostic_$(date +%Y%m%d_%H%M%S).txt 2>&1
```

### Quick database check (alternative)

```bash
python manage.py shell << 'PYEOF'
from apps.reports.models import Recommendation
from django.db.models import Count

total = Recommendation.objects.count()
dist = Recommendation.objects.values('commitment_category').annotate(
    count=Count('id')
).order_by('-count')

print(f"\nTotal recommendations: {total:,}\n")
print("Categorization breakdown:")
print("-" * 60)

for item in dist:
    cat = item['commitment_category']
    count = item['count']
    pct = (count / total * 100) if total > 0 else 0
    symbol = "⚠" if cat == 'uncategorized' else "✓"
    print(f"{symbol} {cat:30s} {count:>6,} ({pct:5.1f}%)")

uncategorized = Recommendation.objects.filter(commitment_category='uncategorized').count()
uncategorized_pct = (uncategorized / total * 100) if total > 0 else 0

print("\n" + "="*60)
if uncategorized_pct < 1:
    print(f"✓ SUCCESS: Only {uncategorized_pct:.1f}% uncategorized")
elif uncategorized_pct < 10:
    print(f"⚠ WARNING: {uncategorized_pct:.1f}% uncategorized")
else:
    print(f"✗ ISSUE: {uncategorized_pct:.1f}% uncategorized - recategorization needed")
    print("  Run the recategorization command (see below)")
PYEOF
```

---

## 🟢 FIX #3: Recategorize Data (15 minutes)

**Only run if diagnostic shows >10% uncategorized**

### Create management command

```bash
# Create command file
cat > apps/reports/management/commands/recategorize_reservations.py << 'EOF'
"""
Management command to recategorize recommendations using ReservationAnalyzer.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.reports.models import Recommendation
from apps.reports.services.reservation_analyzer import ReservationAnalyzer


class Command(BaseCommand):
    help = 'Recategorize existing recommendations using ReservationAnalyzer'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Recategorize all recommendations (default: only uncategorized)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        if options['all']:
            recs = Recommendation.objects.all()
            self.stdout.write("Processing ALL recommendations...")
        else:
            recs = Recommendation.objects.filter(commitment_category='uncategorized')
            self.stdout.write("Processing only uncategorized recommendations...")

        total = recs.count()
        self.stdout.write(f"Found {total:,} recommendations to process")

        if total == 0:
            self.stdout.write(self.style.SUCCESS("No recommendations to process!"))
            return

        updated = 0
        errors = 0

        with transaction.atomic():
            for i, rec in enumerate(recs.iterator(chunk_size=100), 1):
                try:
                    analysis = ReservationAnalyzer.analyze_recommendation(
                        rec.recommendation,
                        rec.potential_benefits
                    )

                    if options['dry_run']:
                        if rec.commitment_category != analysis['commitment_category']:
                            self.stdout.write(
                                f"  [{i}/{total}] Would change: "
                                f"{rec.commitment_category} → {analysis['commitment_category']}"
                            )
                    else:
                        rec.is_reservation_recommendation = analysis['is_reservation']
                        rec.reservation_type = analysis['reservation_type']
                        rec.commitment_term_years = analysis['commitment_term_years']
                        rec.is_savings_plan = analysis['is_savings_plan']
                        rec.commitment_category = analysis['commitment_category']
                        rec.save(update_fields=[
                            'is_reservation_recommendation',
                            'reservation_type',
                            'commitment_term_years',
                            'is_savings_plan',
                            'commitment_category'
                        ])

                    updated += 1
                    if i % 100 == 0:
                        self.stdout.write(f"  Processed {i}/{total}...")

                except Exception as e:
                    errors += 1
                    self.stderr.write(f"  Error processing {rec.id}: {str(e)}")

            if options['dry_run']:
                transaction.set_rollback(True)
                self.stdout.write(
                    self.style.WARNING(
                        f"\nDRY RUN: No changes made. "
                        f"Would have updated {updated:,} recommendations"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\nSuccessfully recategorized {updated:,} recommendations"
                    )
                )

            if errors > 0:
                self.stdout.write(
                    self.style.ERROR(f"Encountered {errors} errors")
                )
EOF

# Ensure management directory structure exists
mkdir -p apps/reports/management/commands
touch apps/reports/management/__init__.py
touch apps/reports/management/commands/__init__.py
```

### Run recategorization

```bash
# First, DRY RUN to see what would change (safe)
python manage.py recategorize_reservations --dry-run

# If results look good, run for real
python manage.py recategorize_reservations

# Or recategorize EVERYTHING (including already categorized)
python manage.py recategorize_reservations --all
```

---

## ✅ VALIDATION COMMANDS

### Verify numeric formatting works

```bash
python manage.py shell << 'PYEOF'
from django.template import Context, Template

tests = [
    ("{% load report_filters %}{{ v|intcomma }}", {'v': 1234567}, "1,234,567"),
    ("{% load report_filters %}{{ v|floatformat:0|intcomma }}", {'v': 12345.67}, "12,346"),
    ("{% load report_filters %}"${{ v|floatformat:2|intcomma }}", {'v': 1234.567}, "$1,234.57"),
]

print("\nNumeric Formatting Validation")
print("=" * 60)
passed = 0
failed = 0

for template_str, context, expected in tests:
    t = Template(template_str)
    result = t.render(Context(context)).strip()
    if result == expected:
        print(f"✓ {expected:20s} = {result}")
        passed += 1
    else:
        print(f"✗ Expected: {expected:20s}")
        print(f"  Got:      {result:20s}")
        failed += 1

print("\n" + "=" * 60)
print(f"Results: {passed} passed, {failed} failed")
if failed == 0:
    print("✓ All formatting tests passed!")
else:
    print(f"✗ {failed} tests failed - check template filter implementation")
PYEOF
```

### Check categorization status

```bash
python manage.py shell << 'PYEOF'
from apps.reports.models import Recommendation, Report
from django.db.models import Count

total = Recommendation.objects.count()
uncategorized = Recommendation.objects.filter(commitment_category='uncategorized').count()
uncategorized_pct = (uncategorized / total * 100) if total > 0 else 0

pure_1y = Recommendation.objects.filter(commitment_category='pure_reservation_1y').count()
pure_3y = Recommendation.objects.filter(commitment_category='pure_reservation_3y').count()
combined_1y = Recommendation.objects.filter(commitment_category='combined_sp_1y').count()
combined_3y = Recommendation.objects.filter(commitment_category='combined_sp_3y').count()
savings_plan = Recommendation.objects.filter(commitment_category='pure_savings_plan').count()

print("\nCategorization Status")
print("=" * 60)
print(f"Total Recommendations:     {total:>6,}")
print(f"Pure 1Y Reservations:      {pure_1y:>6,}")
print(f"Pure 3Y Reservations:      {pure_3y:>6,}")
print(f"Combined SP + 1Y:          {combined_1y:>6,}")
print(f"Combined SP + 3Y:          {combined_3y:>6,}")
print(f"Pure Savings Plans:        {savings_plan:>6,}")
print(f"Uncategorized:             {uncategorized:>6,} ({uncategorized_pct:.1f}%)")
print("=" * 60)

if uncategorized_pct < 1:
    print("✓ Excellent: <1% uncategorized")
elif uncategorized_pct < 10:
    print("⚠ Acceptable: <10% uncategorized")
else:
    print("✗ Problem: >10% uncategorized - recategorization recommended")

# Check if sections would appear in cost reports
latest_cost_report = Report.objects.filter(report_type='cost', status='completed').first()
if latest_cost_report:
    report_pure_3y = latest_cost_report.recommendations.filter(
        commitment_category='pure_reservation_3y'
    ).count()
    report_pure_1y = latest_cost_report.recommendations.filter(
        commitment_category='pure_reservation_1y'
    ).count()

    print(f"\nLatest Cost Report: {latest_cost_report.client.company_name}")
    print(f"  Pure 3Y section would show: {'YES ✓' if report_pure_3y > 0 else 'NO ✗'} ({report_pure_3y} recommendations)")
    print(f"  Pure 1Y section would show: {'YES ✓' if report_pure_1y > 0 else 'NO ✗'} ({report_pure_1y} recommendations)")
PYEOF
```

### Generate test report (via API)

```bash
# If you have API access, test generating a new report
curl -X POST http://your-server/api/reports/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "client_id=YOUR_CLIENT_ID" \
  -F "report_type=cost" \
  -F "csv_file=@path/to/test.csv"

# Then download and verify:
# 1. Numbers have commas: $12,345 not $12345
# 2. Sections appear if data exists
```

---

## 🔄 ROLLBACK COMMANDS

### Rollback template filter fix

```bash
# Restore original (broken) file
cp apps/reports/templatetags/report_filters.py.backup apps/reports/templatetags/report_filters.py

# Restart services
docker restart azure-advisor-backend azure-advisor-celery
```

### Reset all categorization (nuclear option)

```bash
# WARNING: This resets EVERYTHING to uncategorized
python manage.py shell << 'PYEOF'
from apps.reports.models import Recommendation

count = Recommendation.objects.update(
    commitment_category='uncategorized',
    is_savings_plan=False,
    is_reservation_recommendation=False,
    reservation_type=None,
    commitment_term_years=None
)

print(f"Reset {count:,} recommendations to uncategorized")
print("You can now re-run recategorization")
PYEOF
```

---

## 📊 MONITORING COMMANDS

### Watch Celery logs for errors

```bash
# Real-time log monitoring
docker logs -f azure-advisor-celery | grep -i "error\|exception\|failed"

# Check recent errors
docker logs --since 1h azure-advisor-celery | grep -i "error\|exception"
```

### Check deployment version

```bash
python manage.py shell << 'PYEOF'
import azure_advisor_reports
print(f"Version: {getattr(azure_advisor_reports, '__version__', 'unknown')}")
PYEOF
```

### Database connection test

```bash
python manage.py shell << 'PYEOF'
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]

print(f"Database: {connection.settings_dict['NAME']}")
print(f"Host: {connection.settings_dict['HOST']}")
print(f"Version: {version}")
print("✓ Connection successful")
PYEOF
```

---

## 🚀 COMPLETE FIX SEQUENCE (ALL STEPS)

```bash
#!/bin/bash
# Complete fix sequence - copy and paste entire block

echo "==================================================================="
echo "Azure Advisor Reports v2.0.19 - Complete Fix Sequence"
echo "==================================================================="

# Step 1: Backup
echo "\n[1/6] Creating backup..."
cp apps/reports/templatetags/report_filters.py apps/reports/templatetags/report_filters.py.backup
echo "✓ Backup created"

# Step 2: Fix template filter
echo "\n[2/6] Fixing template filter..."
cat > apps/reports/templatetags/report_filters.py << 'EOF'
"""Custom template filters for reports."""
from django import template
from decimal import Decimal, InvalidOperation
from django.contrib.humanize.templatetags.humanize import intcomma as django_intcomma

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument."""
    try:
        if value is None or arg is None:
            return 0
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError, InvalidOperation):
        return 0

@register.filter
def intcomma(value, use_l10n=True):
    """Format a number with thousand separators."""
    return django_intcomma(value, use_l10n=use_l10n)
EOF
echo "✓ Template filter fixed"

# Step 3: Restart services
echo "\n[3/6] Restarting services..."
docker restart azure-advisor-backend azure-advisor-celery
echo "✓ Services restarted"

# Step 4: Run diagnostic
echo "\n[4/6] Running database diagnostic..."
python manage.py shell < scripts/diagnose_database_state.py > diagnostic_output.txt 2>&1
echo "✓ Diagnostic complete (see diagnostic_output.txt)"

# Step 5: Check if recategorization needed
echo "\n[5/6] Checking categorization status..."
UNCATEGORIZED=$(python manage.py shell -c "from apps.reports.models import Recommendation; print(Recommendation.objects.filter(commitment_category='uncategorized').count())")
TOTAL=$(python manage.py shell -c "from apps.reports.models import Recommendation; print(Recommendation.objects.count())")

if [ "$TOTAL" -gt 0 ]; then
    PCT=$((UNCATEGORIZED * 100 / TOTAL))
    echo "  Uncategorized: $UNCATEGORIZED / $TOTAL ($PCT%)"

    if [ "$PCT" -gt 10 ]; then
        echo "  ⚠ >10% uncategorized - recategorization recommended"
        echo "  Run: python manage.py recategorize_reservations"
    else
        echo "  ✓ Categorization acceptable (<10% uncategorized)"
    fi
else
    echo "  No recommendations found"
fi

# Step 6: Validate
echo "\n[6/6] Validating fixes..."
python manage.py shell << 'PYEOF'
from django.template import Context, Template
t = Template("{% load report_filters %}{{ value|intcomma }}")
r = t.render(Context({'value': 12345}))
if r.strip() == "12,345":
    print("✓ Template filter working correctly")
else:
    print(f"✗ Template filter broken (got: {r})")
PYEOF

echo "\n==================================================================="
echo "Fix sequence complete!"
echo "==================================================================="
echo "\nNext steps:"
echo "  1. Review diagnostic_output.txt"
echo "  2. Run recategorization if needed"
echo "  3. Generate test reports and verify"
echo ""
```

---

## 📞 GETTING HELP

If fixes don't work, collect this diagnostic info:

```bash
# Collect all diagnostic information
mkdir -p diagnostic_$(date +%Y%m%d)
cd diagnostic_$(date +%Y%m%d)

# Database diagnostic
python ../manage.py shell < ../scripts/diagnose_database_state.py > database_diagnostic.txt 2>&1

# Template verification
python ../scripts/verify_template_tags.py > template_verification.txt 2>&1

# Service logs
docker logs azure-advisor-backend --tail 200 > backend.log 2>&1
docker logs azure-advisor-celery --tail 200 > celery.log 2>&1

# Git info
git log --oneline -10 > git_log.txt
git diff HEAD~5 apps/reports/templatetags/report_filters.py > template_filter_changes.txt

# System info
docker ps > docker_ps.txt
python ../manage.py showmigrations > migrations.txt

cd ..
tar -czf diagnostic_$(date +%Y%m%d).tar.gz diagnostic_$(date +%Y%m%d)/
echo "Diagnostic package created: diagnostic_$(date +%Y%m%d).tar.gz"
```

Share the generated tar.gz file with the development team.
