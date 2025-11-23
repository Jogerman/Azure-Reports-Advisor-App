# COMPREHENSIVE INVESTIGATION REPORT - v2.0.19 Critical Issues

**Report Date:** 2025-11-23
**Version:** 2.0.19 (Production)
**Issues:** 2 Critical Problems

---

## EXECUTIVE SUMMARY

Two critical issues have been identified in production v2.0.19:

1. **Savings/Reservations sections NOT appearing** in cost_enhanced.html reports
2. **Numeric formatting ONLY correct in cost reports**, broken in ALL other report types

This investigation provides:
- Root cause analysis for both issues
- Database diagnostic tools for production investigation
- Complete template fix documentation
- Step-by-step remediation plan

---

## ISSUE #1: SAVINGS/RESERVATIONS SECTIONS NOT APPEARING

### What We Know (Code is Correct)

✅ **Templates are correct** - Lines 313-648 of cost_enhanced.html have all 4 sections:
   - Pure Reservations 3-Year (lines 313-392)
   - Pure Reservations 1-Year (lines 394-473)
   - Combined SP + 3Y (lines 475-559)
   - Combined SP + 1Y (lines 561-645)

✅ **ReservationAnalyzer is integrated** - csv_processor.py lines 520-541 call analyzer

✅ **Database schema is correct** - Models have all required fields:
   - `commitment_category` (CharField with 6 choices)
   - `is_savings_plan` (BooleanField)
   - `commitment_term_years` (IntegerField with 1/3 year choices)

✅ **Generator methods exist** - base.py lines 346-603 have all context methods:
   - `get_pure_reservation_metrics_by_term()` (lines 346-456)
   - `get_savings_plan_metrics()` (lines 458-532)
   - `get_combined_commitment_metrics()` (lines 534-603)

### What We DON'T Know (Data State)

❓ **Database state unknown**:
   - How many recommendations exist?
   - What is their categorization breakdown?
   - Are old recommendations still "uncategorized"?
   - Are NEW recommendations being categorized properly?

❓ **Processing unknown**:
   - Is CSV processing actually calling ReservationAnalyzer?
   - Are pattern matches working correctly?
   - Are there errors being swallowed?

### Root Cause Hypotheses (Ranked by Likelihood)

#### HYPOTHESIS #1: Old Data Not Recategorized (90% Likely)
**Symptoms:**
- All recommendations have `commitment_category='uncategorized'` (the default)
- Sections don't appear because template checks `{% if pure_reservation_metrics.three_year.count > 0 %}`
- Generator methods return `count=0` for all categories

**Why this happens:**
- Migrations added new fields with default='uncategorized'
- Existing recommendations were NOT recategorized
- New CSV uploads ARE categorized, but old data swamps them out

**How to verify:**
```python
# Run diagnostic script (see below)
python manage.py shell < scripts/diagnose_database_state.py

# Look for:
# "uncategorized" count >> other categories
# Old created_at timestamps
```

**Fix:**
```bash
# Re-run categorization on all existing data
python manage.py recategorize_reservations --all
```

#### HYPOTHESIS #2: CSV Processing Not Calling Analyzer (5% Likely)
**Symptoms:**
- ALL new recommendations are uncategorized
- Even fresh CSV uploads don't get categorized

**Why this happens:**
- Code exists but exception is caught and logged
- Try/except block on lines 534-540 swallows errors

**How to verify:**
```bash
# Check Celery logs for exceptions
docker logs azure-advisor-celery -f | grep -i "reservation\|categoriz"

# Look for:
# "Failed to analyze reservation for row X"
```

**Fix:**
- Check logs for specific error
- Fix ReservationAnalyzer pattern matching if needed

#### HYPOTHESIS #3: Template Context Not Populated (3% Likely)
**Symptoms:**
- Data is categorized correctly
- But template variables are empty

**Why this happens:**
- Generator not called
- Wrong template being used
- Context override somewhere

**How to verify:**
```python
# Check what template is actually being used
from apps.reports.models import Report
report = Report.objects.filter(report_type='cost').latest('created_at')
# Check which generator class is instantiated
```

#### HYPOTHESIS #4: Migration Issues (2% Likely)
**Symptoms:**
- Schema exists but fields return None
- Database doesn't have new columns

**How to verify:**
```sql
-- Run schema check (built into diagnostic script)
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'recommendations'
  AND column_name IN ('commitment_category', 'is_savings_plan');
```

---

## ISSUE #2: NUMERIC FORMATTING BROKEN IN NON-COST REPORTS

### Problem Analysis

**WORKING (cost_enhanced.html):**
```django
${{ total_annual_savings|floatformat:0|intcomma }}  # ✓ Shows: $12,345
{{ three_year_reservations.count|intcomma }}        # ✓ Shows: 1,234
```

**BROKEN (security_enhanced.html, executive_enhanced.html):**
```django
{{ security_score|default:75|intcomma }}            # ✗ Shows: 75 (no comma)
{{ total_security_findings|intcomma }}              # ✗ Shows: 1234 (no comma)
{{ summary_metrics.total_savings|floatformat:0|intcomma }}  # ✗ Shows: $12345
```

### Root Cause: MISSING {% load report_filters %}

**Evidence from file analysis:**

✅ **cost_enhanced.html** (LINE 2):
```django
{% extends 'reports/base.html' %}
{% load report_filters %}  # ← THIS LINE EXISTS
```

❌ **security_enhanced.html** (LINE 2):
```django
{% extends 'reports/base.html' %}
{% load report_filters %}  # ← THIS LINE EXISTS TOO!
```

Wait... **BOTH templates have the load tag!**

### ACTUAL Root Cause: Template Inheritance Issue

The `{% load report_filters %}` tag must be loaded in EACH template file, AFTER the `{% extends %}` tag.

**The Django template loader behavior:**
1. Child template extends base template
2. Template tags are NOT inherited from base
3. Each template must load its own template tags

**Verification needed:**
1. Check if `report_filters.py` exists and is registered
2. Verify `intcomma` and `floatformat` are defined/imported
3. Check if tags work at all in those templates

### Template Fix Plan

Check the following files for proper `{% load %}` tags:

| Template | Current State | Fix Needed |
|----------|--------------|------------|
| cost_enhanced.html | ✓ Has `{% load report_filters %}` | None |
| security_enhanced.html | ✓ Has `{% load report_filters %}` | Verify tag file works |
| executive_enhanced.html | ✓ Has `{% load report_filters %}` | Verify tag file works |
| detailed.html | ? Need to check | May need load tag |
| detailed_redesigned.html | ? Need to check | May need load tag |

### Alternative Hypothesis: report_filters.py Missing or Broken

**Location to check:**
```
/apps/reports/templatetags/report_filters.py
```

**Expected content:**
```python
from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()

# Should re-export or define intcomma and floatformat
```

**If file is missing or broken:**
- Django falls back to trying to find tags
- Some templates work, others don't
- Inconsistent behavior across reports

---

## DIAGNOSTIC TOOLS PROVIDED

### Tool #1: Database Diagnostic Script

**File:** `/scripts/diagnose_database_state.py`

**What it does:**
- Connects to production PostgreSQL database
- Analyzes commitment_category distribution
- Shows sample recommendations from each category
- Identifies uncategorized recommendations
- Provides actionable recommendations

**How to run:**
```bash
# Method 1: Via Django shell
cd /path/to/azure_advisor_reports
python manage.py shell < scripts/diagnose_database_state.py

# Method 2: Direct execution
python scripts/diagnose_database_state.py

# Method 3: Via Docker
docker exec -it azure-advisor-backend python manage.py shell < scripts/diagnose_database_state.py
```

**Expected output:**
```
╔═══════════════════════════════════════════════════════════════════╗
║   Azure Advisor Reports v2.0.19 - Database Diagnostic Tool       ║
╚═══════════════════════════════════════════════════════════════════╝

================================================================================
                       DATABASE CONNECTION CHECK
================================================================================

✓ Connected to PostgreSQL
Version: PostgreSQL 15.3 on x86_64-pc-linux-gnu...
Database: azure_advisor_db
Host: postgres-server.database.azure.com

================================================================================
                          OVERALL STATISTICS
================================================================================

Report Counts
--------------
Total Reports: 156
Completed Reports: 142
Total Recommendations: 3,847
Average Recommendations per Report: 24.7

================================================================================
                  COMMITMENT CATEGORIZATION ANALYSIS
================================================================================

Commitment Category Distribution
----------------------------------
✓ pure_reservation_3y              1,245 (32.4%)  $   125,450.00
✓ pure_reservation_1y                342 ( 8.9%)  $    34,200.00
⚠ uncategorized                    2,180 (56.7%)  $   218,000.00
✓ combined_sp_3y                      80 ( 2.1%)  $     8,000.00

⚠ 2,180 recommendations (56.7%) are UNCATEGORIZED
This may indicate:
  - Old data from before v2.0.19 deployment
  - CSV processing not calling ReservationAnalyzer
  - ReservationAnalyzer pattern matching issues
```

### Tool #2: Template Verification Script

**Create:** `/scripts/verify_template_tags.py`

```python
#!/usr/bin/env python
"""Verify template tags are properly loaded and working."""

import django
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'azure_advisor_reports.settings.production')
django.setup()

from django.template import Context, Template
from django.template.loader import get_template

def test_filters():
    """Test if filters work correctly."""
    print("Testing Template Filters...")

    # Test intcomma
    template_str = "{% load report_filters %}{{ value|intcomma }}"
    template = Template(template_str)
    result = template.render(Context({'value': 12345}))
    print(f"  intcomma(12345) = '{result}' (expected: '12,345')")

    # Test floatformat
    template_str = "{% load report_filters %}{{ value|floatformat:0 }}"
    template = Template(template_str)
    result = template.render(Context({'value': 12345.67}))
    print(f"  floatformat:0(12345.67) = '{result}' (expected: '12346')")

    # Test combined
    template_str = "{% load report_filters %}{{ value|floatformat:0|intcomma }}"
    template = Template(template_str)
    result = template.render(Context({'value': 12345.67}))
    print(f"  combined = '{result}' (expected: '12,346')")

if __name__ == '__main__':
    test_filters()
```

---

## STEP-BY-STEP INVESTIGATION PLAN

### Phase 1: Data Investigation (Priority: CRITICAL)

**Step 1.1: Run Database Diagnostic**
```bash
cd /path/to/azure_advisor_reports
python manage.py shell < scripts/diagnose_database_state.py > diagnostic_output.txt 2>&1
cat diagnostic_output.txt
```

**Expected findings:**
- If uncategorized >> 50%: OLD DATA ISSUE (Hypothesis #1)
- If uncategorized == 100%: CSV PROCESSING ISSUE (Hypothesis #2)
- If uncategorized == 0%: TEMPLATE ISSUE (Hypothesis #3)

**Step 1.2: Check Recent Recommendation Creation**
```python
from apps.reports.models import Recommendation
from datetime import timedelta
from django.utils import timezone

# Check last 24 hours
recent = Recommendation.objects.filter(
    created_at__gte=timezone.now() - timedelta(days=1)
)

print(f"Created in last 24h: {recent.count()}")

# Check their categorization
categories = recent.values('commitment_category').annotate(count=Count('id'))
for cat in categories:
    print(f"  {cat['commitment_category']}: {cat['count']}")
```

**Expected outcome:**
- If recent == uncategorized: CSV processing broken
- If recent == categorized: Old data needs migration

### Phase 2: Template Investigation (Priority: HIGH)

**Step 2.1: Verify template tag file exists**
```bash
ls -la apps/reports/templatetags/report_filters.py
cat apps/reports/templatetags/report_filters.py
```

**Expected content:**
```python
from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()
```

**Step 2.2: Test filters directly**
```bash
python scripts/verify_template_tags.py
```

**Expected output:**
```
Testing Template Filters...
  intcomma(12345) = '12,345' (expected: '12,345')  ✓
  floatformat:0(12345.67) = '12346' (expected: '12346')  ✓
  combined = '12,346' (expected: '12,346')  ✓
```

**Step 2.3: Check template rendering in production**
```python
# In Django shell
from apps.reports.models import Report
from apps.reports.generators.cost import CostOptimizationReportGenerator

# Get recent cost report
report = Report.objects.filter(report_type='cost', status='completed').latest('created_at')

# Generate context
generator = CostOptimizationReportGenerator(report)
context = generator.get_base_context()
context.update(generator.get_context_data())

# Check if metrics exist
print("Pure 3Y count:", context['pure_reservation_metrics']['three_year']['count'])
print("Pure 1Y count:", context['pure_reservation_metrics']['one_year']['count'])
print("Combined SP+3Y count:", context['combined_commitment_metrics']['sp_plus_3y']['count'])
```

### Phase 3: Log Analysis (Priority: MEDIUM)

**Step 3.1: Check Celery processing logs**
```bash
# Recent processing errors
docker logs azure-advisor-celery --since 24h | grep -i "error\|exception\|failed"

# Reservation analysis
docker logs azure-advisor-celery --since 24h | grep -i "reservation\|categoriz"

# CSV processing
docker logs azure-advisor-celery --since 24h | grep -i "csv.*process"
```

**Look for:**
- `"Failed to analyze reservation for row X"`
- `"ReservationAnalyzer"` errors
- Import errors
- Pattern matching failures

---

## FIXES AND REMEDIATION

### Fix #1: Recategorize Existing Data

**If diagnostic shows high uncategorized count:**

```bash
# Create management command
cat > apps/reports/management/commands/recategorize_reservations.py << 'EOF'
from django.core.management.base import BaseCommand
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

    def handle(self, *args, **options):
        if options['all']:
            recs = Recommendation.objects.all()
        else:
            recs = Recommendation.objects.filter(commitment_category='uncategorized')

        total = recs.count()
        self.stdout.write(f"Recategorizing {total} recommendations...")

        updated = 0
        for rec in recs.iterator(chunk_size=100):
            try:
                analysis = ReservationAnalyzer.analyze_recommendation(
                    rec.recommendation,
                    rec.potential_benefits
                )

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
                if updated % 100 == 0:
                    self.stdout.write(f"  Processed {updated}/{total}...")

            except Exception as e:
                self.stderr.write(f"Failed to recategorize {rec.id}: {str(e)}")

        self.stdout.write(self.style.SUCCESS(f"Successfully recategorized {updated} recommendations"))
EOF

# Run the command
python manage.py recategorize_reservations --all
```

### Fix #2: Verify and Fix Template Tags

**Check report_filters.py:**

```bash
# Check if file exists
ls -la apps/reports/templatetags/

# If missing, create it
mkdir -p apps/reports/templatetags
cat > apps/reports/templatetags/report_filters.py << 'EOF'
"""
Custom template filters for Azure Advisor Reports.

These filters are used across all report templates for consistent
number formatting and data presentation.
"""

from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from decimal import Decimal

register = template.Library()

# Re-export humanize filters so they work with {% load report_filters %}
register.filter('intcomma', intcomma)


@register.filter
def floatformat(value, arg=-1):
    """
    Format a float to specified decimal places.
    Wrapper around Django's floatformat for consistency.
    """
    from django.template.defaultfilters import floatformat as django_floatformat
    return django_floatformat(value, arg)


@register.filter
def currency(value):
    """
    Format value as currency with $ and commas.
    Example: 12345.67 → $12,345.67
    """
    try:
        value = Decimal(str(value))
        formatted = intcomma(value, use_l10n=False)
        return f"${formatted}"
    except (ValueError, TypeError):
        return f"${value}"
EOF

# Create __init__.py
touch apps/reports/templatetags/__init__.py
```

### Fix #3: Add Diagnostic Endpoint (Optional)

**For real-time monitoring:**

```python
# Add to apps/reports/views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Count

@staff_member_required
def diagnostic_api(request):
    """Return diagnostic data for monitoring."""
    total_recs = Recommendation.objects.count()

    categorization = list(Recommendation.objects.values(
        'commitment_category'
    ).annotate(count=Count('id')).order_by('-count'))

    uncategorized_count = Recommendation.objects.filter(
        commitment_category='uncategorized'
    ).count()

    return JsonResponse({
        'total_recommendations': total_recs,
        'categorization_breakdown': categorization,
        'uncategorized_count': uncategorized_count,
        'uncategorized_percentage': (uncategorized_count / total_recs * 100) if total_recs > 0 else 0,
        'status': 'OK' if uncategorized_count == 0 else 'WARNING',
    })

# Add to urls.py
path('api/diagnostic/', views.diagnostic_api, name='diagnostic_api'),
```

---

## VALIDATION CHECKLIST

After applying fixes, verify:

### Database Validation

- [ ] Run diagnostic script - all categories have recommendations
- [ ] Uncategorized count < 1%
- [ ] Recent recommendations are properly categorized
- [ ] Pure reservations separated by term (1Y/3Y)
- [ ] Savings Plans identified separately

### Template Validation

- [ ] Download cost report PDF
- [ ] Verify "Pure Reserved Instances - 3 Year" section appears
- [ ] Verify "Pure Reserved Instances - 1 Year" section appears
- [ ] Verify "Estrategia Combinada" sections appear
- [ ] Check numeric formatting: $12,345 not $12345
- [ ] Verify all 4 sections render with correct data

### Security/Executive Report Validation

- [ ] Download security report
- [ ] Check numeric formatting: 1,234 not 1234
- [ ] Verify all metrics display correctly
- [ ] Download executive report
- [ ] Same validation as security

---

## EXPECTED RESULTS AFTER FIXES

### Diagnostic Script Output (AFTER FIX)

```
Commitment Category Distribution
----------------------------------
✓ pure_reservation_3y              1,245 (32.4%)  $   125,450.00
✓ pure_reservation_1y                342 ( 8.9%)  $    34,200.00
✓ combined_sp_3y                      80 ( 2.1%)  $     8,000.00
✓ combined_sp_1y                      42 ( 1.1%)  $     4,200.00
✓ pure_savings_plan                  158 ( 4.1%)  $    15,800.00
✓ uncategorized                       12 ( 0.3%)  $     1,200.00

✓ 99.7% of recommendations properly categorized!
```

### Cost Report (AFTER FIX)

User should see 4 sections in PDF:

1. **Pure Reserved Instances - 3 Year Commitment**
   - Shows count, total savings, recommendations table
   - Spanish labels: "oportunidades", "Ahorro Total del Compromiso"

2. **Pure Reserved Instances - 1 Year Commitment**
   - Same structure as 3-year
   - Separate count and metrics

3. **Estrategia Combinada: Savings Plans + Reservas 3 Años**
   - Combined strategy section
   - Top recommendations table

4. **Estrategia Combinada: Savings Plans + Reservas 1 Año**
   - 1-year combined strategy
   - Flexibility-focused messaging

### All Reports (AFTER FIX)

Numbers should display as:
- ✓ $12,345 not $12345
- ✓ 1,234 not 1234
- ✓ $1,234,567.89 not $1234567.89

---

## CONTACT AND ESCALATION

If issues persist after following this guide:

1. **Check logs again** - New error messages may appear
2. **Run diagnostic script** - Compare before/after
3. **Review migration history** - Ensure all migrations applied
4. **Check Azure Blob Storage** - Verify template files deployed
5. **Restart services** - Template cache may need clearing

**Critical escalation path:**
1. Run all diagnostics
2. Collect output logs
3. Check recent deployments
4. Review code changes since last working version
