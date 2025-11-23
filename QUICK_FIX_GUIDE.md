# QUICK FIX GUIDE - v2.0.19 Issues

**Target Audience:** User running production deployment
**Time Required:** 15-30 minutes
**Difficulty:** Medium

---

## CRITICAL FINDINGS

### Issue #1: Savings/Reservations Sections Missing
**Root Cause:** Likely old data with `commitment_category='uncategorized'`

### Issue #2: Numeric Formatting Working in Cost Reports Only
**Root Cause:** FOUND! Custom `intcomma` filter implementation has a bug
**File:** `/apps/reports/templatetags/report_filters.py` lines 67-70

---

## NUMERIC FORMATTING BUG - CRITICAL FIX

### The Bug (Lines 67-70 in report_filters.py)

```python
# BROKEN CODE - Reverses string incorrectly
int_part_with_commas = ','.join(
    int_part[::-1][i:i+3][::-1]
    for i in range(0, len(int_part), 3)
)[::-1]
```

**What it does:**
- For "12345": Splits into "123", "45" → "321", "54" → joins "321,54" → reverses to "45,123"
- WRONG! Should be "12,345"

**Why cost_enhanced.html works:**
- Cost template uses `floatformat` BEFORE `intcomma`
- `floatformat` converts Decimal to string first
- Something in that conversion path makes it work
- Other templates use `intcomma` directly on integers = broken

### The Fix

**Replace lines 37-84 in `/apps/reports/templatetags/report_filters.py`:**

```python
from django.contrib.humanize.templatetags.humanize import intcomma as django_intcomma

@register.filter
def intcomma(value, use_l10n=True):
    """
    Format a number with thousand separators (commas).

    This is a wrapper around Django's built-in humanize intcomma filter
    to ensure consistent behavior across all templates.

    Usage in templates:
        {{ total_recommendations|intcomma }}
        {{ 26970|intcomma }}  -> "26,970"

    Args:
        value: The number to format (int, float, Decimal, or string)
        use_l10n: Whether to use localization (default: True)

    Returns:
        A string with the number formatted with commas
    """
    return django_intcomma(value, use_l10n=use_l10n)
```

**Why this works:**
- Uses Django's proven implementation
- Consistent across all templates
- Handles all edge cases correctly

---

## STEP-BY-STEP FIX PROCEDURES

### Step 1: Run Diagnostic Script (5 minutes)

```bash
# Connect to production server
ssh your-production-server

# Navigate to project
cd /path/to/azure_advisor_reports

# Run diagnostic (as Django user)
python manage.py shell < scripts/diagnose_database_state.py > diagnostic_output.txt 2>&1

# View results
cat diagnostic_output.txt
```

**Look for:**
- Total recommendations count
- Uncategorized percentage
- Pure reservation counts

**Decision tree:**
- If uncategorized > 50% → Go to Step 2 (Recategorize Data)
- If uncategorized < 10% → Go to Step 3 (Fix Template Filter)
- In all cases → Do Step 3 (Template filter is definitely broken)

---

### Step 2: Fix Template Filter Bug (5 minutes) - **DO THIS FIRST**

```bash
# Backup current file
cp apps/reports/templatetags/report_filters.py apps/reports/templatetags/report_filters.py.backup

# Edit the file
nano apps/reports/templatetags/report_filters.py
# Or use vim, or any editor
```

**Replace lines 37-84 with:**

```python
from django.contrib.humanize.templatetags.humanize import intcomma as django_intcomma

@register.filter
def intcomma(value, use_l10n=True):
    """
    Format a number with thousand separators (commas).

    Wrapper around Django's humanize intcomma for consistency.

    Usage: {{ value|intcomma }}
    Example: 26970 -> "26,970"
    """
    return django_intcomma(value, use_l10n=use_l10n)
```

**Or use this one-liner to patch the file:**

```bash
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

    Wrapper around Django's humanize intcomma for consistency.

    Usage: {{ value|intcomma }}
    Example: 26970 -> "26,970"
    """
    return django_intcomma(value, use_l10n=use_l10n)
EOF
```

**Restart the application:**

```bash
# Docker deployment
docker restart azure-advisor-backend
docker restart azure-advisor-celery

# Or systemd
sudo systemctl restart azure-advisor-backend
sudo systemctl restart azure-advisor-celery

# Or kill and restart Gunicorn workers
pkill -HUP gunicorn
```

**Test immediately:**

```bash
python manage.py shell
```

```python
from django.template import Context, Template

template = Template("{% load report_filters %}{{ value|intcomma }}")
result = template.render(Context({'value': 12345}))
print(f"Result: '{result}' (expected '12,345')")

# Should print: Result: '12,345' (expected '12,345')
```

---

### Step 3: Recategorize Old Data (10-15 minutes)

**Only if diagnostic shows high uncategorized count (>10%)**

```bash
# Create management command file
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
        self.stdout.write(f"Found {total} recommendations to process")

        if total == 0:
            self.stdout.write(self.style.SUCCESS("No recommendations to process!"))
            return

        updated = 0
        errors = 0

        # Use transaction for safety
        with transaction.atomic():
            for i, rec in enumerate(recs.iterator(chunk_size=100), 1):
                try:
                    # Analyze with ReservationAnalyzer
                    analysis = ReservationAnalyzer.analyze_recommendation(
                        rec.recommendation,
                        rec.potential_benefits
                    )

                    # Show what changed (if dry-run)
                    if options['dry_run']:
                        if rec.commitment_category != analysis['commitment_category']:
                            self.stdout.write(
                                f"  [{i}/{total}] Would change: {rec.commitment_category} → {analysis['commitment_category']}"
                            )
                    else:
                        # Update fields
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

                    # Progress indicator
                    if i % 100 == 0:
                        self.stdout.write(f"  Processed {i}/{total}...")

                except Exception as e:
                    errors += 1
                    self.stderr.write(f"  Error processing recommendation {rec.id}: {str(e)}")

            # Rollback if dry-run
            if options['dry_run']:
                transaction.set_rollback(True)
                self.stdout.write(
                    self.style.WARNING(f"\nDRY RUN: No changes made. Would have updated {updated} recommendations")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"\nSuccessfully recategorized {updated} recommendations")
                )

            if errors > 0:
                self.stdout.write(
                    self.style.ERROR(f"Encountered {errors} errors during processing")
                )
EOF

# First, do a dry run to see what would change
python manage.py recategorize_reservations --dry-run

# If results look good, run for real
python manage.py recategorize_reservations

# Or recategorize everything
python manage.py recategorize_reservations --all
```

**Monitor progress:**
- Should process ~100 recommendations per second
- Shows progress every 100 items
- Safe to interrupt (uses transactions)

---

### Step 4: Verify Fixes (5 minutes)

**4.1: Test numeric formatting**

```bash
python manage.py shell
```

```python
from django.template import Context, Template

# Test intcomma
t1 = Template("{% load report_filters %}{{ value|intcomma }}")
r1 = t1.render(Context({'value': 1234567}))
print(f"intcomma test: {r1} (expected: 1,234,567)")

# Test floatformat + intcomma
t2 = Template("{% load report_filters %}{{ value|floatformat:0|intcomma }}")
r2 = t2.render(Context({'value': 12345.67}))
print(f"combined test: {r2} (expected: 12,346)")

# Test currency format
t3 = Template("{% load report_filters %}"${{ value|floatformat:0|intcomma }}")
r3 = t3.render(Context({'value': 125450.50}))
print(f"currency test: {r3} (expected: $125,451)")
```

**Expected output:**
```
intcomma test: 1,234,567 (expected: 1,234,567)
combined test: 12,346 (expected: 12,346)
currency test: $125,451 (expected: $125,451)
```

**4.2: Check categorization status**

```bash
python manage.py shell
```

```python
from apps.reports.models import Recommendation
from django.db.models import Count

# Check distribution
dist = Recommendation.objects.values('commitment_category').annotate(
    count=Count('id')
).order_by('-count')

total = Recommendation.objects.count()

print("\nCategorization Distribution:")
print("-" * 60)
for item in dist:
    cat = item['commitment_category']
    count = item['count']
    pct = (count / total * 100) if total > 0 else 0
    print(f"{cat:30s} {count:>6,} ({pct:5.1f}%)")

uncategorized = Recommendation.objects.filter(commitment_category='uncategorized').count()
uncategorized_pct = (uncategorized / total * 100) if total > 0 else 0

print(f"\n{'='*60}")
if uncategorized_pct < 1:
    print(f"✓ SUCCESS: Only {uncategorized_pct:.1f}% uncategorized")
elif uncategorized_pct < 10:
    print(f"⚠ WARNING: {uncategorized_pct:.1f}% uncategorized (acceptable)")
else:
    print(f"✗ ISSUE: {uncategorized_pct:.1f}% uncategorized (needs recategorization)")
```

**4.3: Generate test report**

```bash
# Via Django admin or API, generate a new cost report
# Then download and check:

# 1. Numbers should have commas: 1,234 not 1234
# 2. Currency should format correctly: $12,345 not $12345
# 3. Sections should appear if data exists:
#    - Pure Reserved Instances - 3 Year
#    - Pure Reserved Instances - 1 Year
#    - Combined strategies
```

---

## VALIDATION CHECKLIST

After completing steps above:

### Numeric Formatting (ALL report types)

- [ ] Cost report shows $12,345 format (not $12345)
- [ ] Security report shows 1,234 format (not 1234)
- [ ] Executive report shows proper formatting
- [ ] Detailed report shows proper formatting

### Savings/Reservations Sections (Cost reports only)

- [ ] "Pure Reserved Instances - 3 Year" section appears (if data exists)
- [ ] "Pure Reserved Instances - 1 Year" section appears (if data exists)
- [ ] "Estrategia Combinada: SP + 3Y" appears (if data exists)
- [ ] "Estrategia Combinada: SP + 1Y" appears (if data exists)
- [ ] Each section shows correct counts and totals
- [ ] Top recommendations table populated

### Database State

- [ ] Uncategorized percentage < 10%
- [ ] Pure reservations separated by term (1Y/3Y)
- [ ] Savings Plans identified separately
- [ ] Combined commitments categorized

---

## TROUBLESHOOTING

### "Still seeing 1234 instead of 1,234"

**Cause:** Template cache not cleared or old workers running

**Fix:**
```bash
# Clear Django cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# Restart ALL services
docker restart azure-advisor-backend azure-advisor-celery azure-advisor-frontend

# Or force kill workers
pkill -9 -f gunicorn
pkill -9 -f celery
# Then restart them
```

### "Sections still not appearing"

**Cause:** No data in those categories OR template condition bug

**Debug:**
```python
from apps.reports.models import Report
from apps.reports.generators.cost import CostOptimizationReportGenerator

# Get latest cost report
report = Report.objects.filter(report_type='cost').latest('created_at')

# Generate context
generator = CostOptimizationReportGenerator(report)
context = generator.get_base_context()

# Check metrics
pure_3y = context['pure_reservation_metrics']['three_year']
print(f"Pure 3Y count: {pure_3y['count']}")
print(f"Pure 3Y total: ${pure_3y['total_annual_savings']}")

# If count > 0 but section not appearing:
# - Check template conditional on line 314 of cost_enhanced.html
# - Ensure context variable names match exactly
```

### "Recategorization command not found"

**Cause:** Management command file not created properly

**Fix:**
```bash
# Ensure directory exists
mkdir -p apps/reports/management/commands
touch apps/reports/management/commands/__init__.py

# Check parent __init__.py exists
touch apps/reports/management/__init__.py

# Recreate command file (see Step 3 above)

# Verify Django finds it
python manage.py help | grep recategorize
```

### "Getting errors in recategorization"

**Cause:** ReservationAnalyzer import or pattern matching issues

**Debug:**
```bash
# Check if analyzer exists
python manage.py shell -c "from apps.reports.services.reservation_analyzer import ReservationAnalyzer; print('OK')"

# Test analyzer directly
python manage.py shell
```

```python
from apps.reports.services.reservation_analyzer import ReservationAnalyzer

# Test with sample text
result = ReservationAnalyzer.analyze_recommendation(
    "Consider using Reserved Instance for 3-year commitment",
    "Save up to 72% with 3-year reserved instances"
)

print(result)
# Should show:
# {
#   'is_reservation': True,
#   'reservation_type': 'reserved_instance',
#   'commitment_term_years': 3,
#   'is_savings_plan': False,
#   'commitment_category': 'pure_reservation_3y'
# }
```

---

## ROLLBACK PROCEDURES

### If template filter fix causes issues:

```bash
# Restore backup
cp apps/reports/templatetags/report_filters.py.backup apps/reports/templatetags/report_filters.py

# Restart services
docker restart azure-advisor-backend azure-advisor-celery
```

### If recategorization causes issues:

```bash
# Reset all to uncategorized
python manage.py shell
```

```python
from apps.reports.models import Recommendation

Recommendation.objects.all().update(
    commitment_category='uncategorized',
    is_savings_plan=False,
    is_reservation_recommendation=False,
    reservation_type=None,
    commitment_term_years=None
)
```

Then re-run recategorization with `--dry-run` first to verify.

---

## SUCCESS CRITERIA

After all fixes, you should see:

1. **All numeric values formatted with commas** in ALL report types
2. **Cost reports show 4 sections** (if corresponding data exists):
   - Pure Reservations 3-Year
   - Pure Reservations 1-Year
   - Combined SP + 3Y
   - Combined SP + 1Y
3. **Database shows <10% uncategorized** recommendations
4. **New CSV uploads automatically categorized** properly

---

## GETTING HELP

If issues persist after following this guide:

1. **Collect diagnostic output:**
   ```bash
   python manage.py shell < scripts/diagnose_database_state.py > diagnostic.txt 2>&1
   python scripts/verify_template_tags.py > template_check.txt 2>&1
   docker logs azure-advisor-backend --tail 100 > backend.log 2>&1
   docker logs azure-advisor-celery --tail 100 > celery.log 2>&1
   ```

2. **Check recent changes:**
   ```bash
   git log --oneline -10
   git diff HEAD~5 apps/reports/templatetags/report_filters.py
   ```

3. **Verify deployment version:**
   ```bash
   docker exec azure-advisor-backend python manage.py shell -c "from azure_advisor_reports import __version__; print(__version__)"
   # Should show: 2.0.19
   ```

4. **Share logs and diagnostic output** with development team

---

## ESTIMATED TIME

- Template filter fix: **5 minutes**
- Restart services: **2 minutes**
- Run diagnostic: **3 minutes**
- Recategorize data: **10-15 minutes** (depending on volume)
- Validation: **5 minutes**

**Total: 25-30 minutes**

Most important: **Do the template filter fix first** - it's quick and solves the numeric formatting issue immediately!
