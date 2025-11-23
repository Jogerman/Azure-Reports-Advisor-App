# Investigation Report: Why Reservation Tables Show No Data

## Executive Summary

The 4 new reservation tables in `cost_enhanced.html` are not showing data because **existing recommendations in the database were created BEFORE the enhanced categorization fields were added**, and the data migration that backfills these fields has a critical gap.

## Problem Statement

Templates check for:
```django
{% if pure_reservation_metrics.three_year.count > 0 %}
```

The backend filters on:
```python
pure_reservations = self.recommendations.filter(
    Q(commitment_category='pure_reservation_1y') |
    Q(commitment_category='pure_reservation_3y')
)
```

But **no recommendations have `commitment_category` set to these values**, so `count` is always 0.

---

## Detailed Data Flow Analysis

### 1. CSV Upload Process (csv_processor.py)

**Lines 520-540**: When a CSV is uploaded, the processor analyzes each recommendation:

```python
# Analyze for Saving Plans & Reserved Instances
reservation_analysis = ReservationAnalyzer.analyze_recommendation(
    recommendation_text,
    potential_benefits_text
)
recommendation_data['is_reservation_recommendation'] = reservation_analysis['is_reservation']
recommendation_data['reservation_type'] = reservation_analysis['reservation_type']
recommendation_data['commitment_term_years'] = reservation_analysis['commitment_term_years']

# NEW FIELDS - Enhanced categorization
recommendation_data['is_savings_plan'] = reservation_analysis['is_savings_plan']
recommendation_data['commitment_category'] = reservation_analysis['commitment_category']
```

**This is working correctly!** The CSV processor DOES populate the new fields.

### 2. ReservationAnalyzer Service (reservation_analyzer.py)

**Lines 346-409**: The analyzer correctly categorizes recommendations:

```python
def analyze_recommendation(cls, recommendation_text, potential_benefits=''):
    # ... analysis logic ...
    result['commitment_category'] = cls.categorize_commitment(
        recommendation_text,
        potential_benefits,
        result['commitment_term_years']
    )
```

**Test confirms this works:**
```
Sample: "Consider using Azure Reserved VM Instances to save money on virtual machines"
Benefits: "Reduce virtual machine costs by committing to one or three-year terms"

Result:
  is_reservation: True
  reservation_type: reserved_instance
  commitment_term_years: 3
  is_savings_plan: False
  commitment_category: pure_reservation_3y  ✓ CORRECT
```

### 3. Database Models (models.py)

**Lines 352-372**: Model has the correct fields:

```python
is_savings_plan = models.BooleanField(
    default=False,
    db_index=True,
)
commitment_category = models.CharField(
    max_length=50,
    choices=[
        ('pure_reservation_1y', 'Pure Reservation - 1 Year'),
        ('pure_reservation_3y', 'Pure Reservation - 3 Years'),
        ('pure_savings_plan', 'Pure Savings Plan'),
        ('combined_sp_1y', 'Savings Plan + 1Y Reservation'),
        ('combined_sp_3y', 'Savings Plan + 3Y Reservation'),
        ('uncategorized', 'Uncategorized'),
    ],
    default='uncategorized',
    db_index=True,
)
```

### 4. Report Generation (generators/base.py)

**Lines 346-456**: Backend methods correctly filter:

```python
def get_pure_reservation_metrics_by_term(self):
    pure_reservations = self.recommendations.filter(
        Q(commitment_category='pure_reservation_1y') |
        Q(commitment_category='pure_reservation_3y')
    )

    one_year_reservations = pure_reservations.filter(commitment_term_years=1)
    three_year_reservations = pure_reservations.filter(commitment_term_years=3)
    # ... calculates metrics ...
```

**This logic is correct!** It properly filters by `commitment_category`.

---

## The Gap: Migration vs. Existing Data

### Migration 0009 Backfill Logic (PROBLEMATIC)

**Lines 24-46 of 0009_populate_savings_plan_flags.py**:

```python
# Categorize pure reservations - 1 Year
updated_1y = Recommendation.objects.filter(
    is_reservation_recommendation=True,
    reservation_type__in=['reserved_instance', 'reserved_capacity'],
    commitment_term_years=1
).update(
    commitment_category='pure_reservation_1y',
    is_savings_plan=False
)

# Categorize pure reservations - 3 Years
updated_3y = Recommendation.objects.filter(
    is_reservation_recommendation=True,
    reservation_type__in=['reserved_instance', 'reserved_capacity'],
    commitment_term_years=3
).update(
    commitment_category='pure_reservation_3y',
    is_savings_plan=False
)
```

### THE PROBLEM

**This migration ONLY updates recommendations that already have ALL THREE fields populated:**

1. `is_reservation_recommendation=True`
2. `reservation_type` in ['reserved_instance', 'reserved_capacity']
3. `commitment_term_years` set to 1 or 3

**However**, recommendations created from CSV uploads BEFORE these fields existed have:
- `is_reservation_recommendation=False` (migration 0007 set all NULL to FALSE)
- `reservation_type=NULL`
- `commitment_term_years=NULL`

**Therefore, the migration finds ZERO matching records and updates nothing!**

---

## Why New Uploads Work But Old Data Doesn't

### Scenario A: New CSV Upload (after code update)
1. User uploads CSV
2. CSV processor calls `ReservationAnalyzer.analyze_recommendation()`
3. All fields populated correctly: ✓
   - `is_reservation_recommendation=True`
   - `reservation_type='reserved_instance'`
   - `commitment_term_years=3`
   - `is_savings_plan=False`
   - `commitment_category='pure_reservation_3y'`
4. Report shows data in tables: ✓

### Scenario B: Existing Data (created before enhancement)
1. Recommendations exist in database with:
   - `is_reservation_recommendation=False` (from migration 0007)
   - `reservation_type=NULL`
   - `commitment_term_years=NULL`
   - `is_savings_plan=False` (from migration 0008 default)
   - `commitment_category='uncategorized'` (from migration 0008 default)
2. Migration 0009 runs but finds NO matching records: ✗
3. All fields remain at default values: ✗
4. Report filters find zero records: ✗
5. Tables don't render: ✗

---

## Root Cause Summary

**The migration assumes that existing recommendations already have reservation analysis data (`reservation_type`, `commitment_term_years`), but they don't.**

The old CSV processor (before the enhancement) did NOT populate these fields, so migration 0007 set everything to `FALSE/NULL`, and migration 0009 couldn't backfill because it filtered on those very fields.

---

## Solution Required

### Option 1: Re-analyze Existing Recommendations (RECOMMENDED)

Create a new data migration that:

1. **Reads the recommendation text** from existing records
2. **Re-runs the ReservationAnalyzer** on each recommendation
3. **Updates ALL reservation-related fields** based on the analysis

```python
def reanalyze_existing_recommendations(apps, schema_editor):
    """Re-analyze all existing recommendations to populate categorization fields."""
    Recommendation = apps.get_model('reports', 'Recommendation')

    # Import analyzer (need to vendor the logic or use raw text analysis)
    for rec in Recommendation.objects.all():
        # Re-analyze the recommendation text
        analysis = analyze_text(rec.recommendation, rec.potential_benefits)

        # Update ALL fields
        rec.is_reservation_recommendation = analysis['is_reservation']
        rec.reservation_type = analysis['reservation_type']
        rec.commitment_term_years = analysis['commitment_term_years']
        rec.is_savings_plan = analysis['is_savings_plan']
        rec.commitment_category = analysis['commitment_category']
        rec.save()
```

**Pros:**
- Correctly categorizes all existing data
- Most accurate solution
- Future-proof

**Cons:**
- Requires re-importing ReservationAnalyzer logic in migration
- Potentially slow for large datasets (need batching)

### Option 2: Manual Re-upload (TEMPORARY WORKAROUND)

Instruct users to:
1. Delete old reports
2. Re-upload CSV files
3. Regenerate reports

**Pros:**
- No code changes needed
- Guaranteed fresh data

**Cons:**
- Loses historical data
- Manual effort required
- Not scalable

### Option 3: Management Command (HYBRID)

Create a management command that users can run to backfill existing data:

```bash
python manage.py backfill_reservation_categories
```

**Pros:**
- Can be run on-demand
- Doesn't require migration rollback
- Can be re-run if needed

**Cons:**
- Users must manually run it
- Doesn't auto-fix on deployment

---

## Verification Steps

To verify which recommendations are affected:

```python
# Count total recommendations
total = Recommendation.objects.count()

# Count categorized reservations
categorized = Recommendation.objects.filter(
    commitment_category__in=[
        'pure_reservation_1y',
        'pure_reservation_3y',
        'pure_savings_plan',
        'combined_sp_1y',
        'combined_sp_3y'
    ]
).count()

# Count uncategorized
uncategorized = Recommendation.objects.filter(
    commitment_category='uncategorized'
).count()

# Count potential reservations (text analysis needed)
potential_reservations = Recommendation.objects.filter(
    Q(recommendation__icontains='reservation') |
    Q(recommendation__icontains='reserved') |
    Q(recommendation__icontains='savings plan') |
    Q(potential_benefits__icontains='commit')
).count()
```

---

## Recommended Fix (DETAILED)

### Step 1: Create New Migration `0010_reanalyze_recommendations.py`

```python
from django.db import migrations
import re


def analyze_recommendation_text(recommendation_text, potential_benefits=''):
    """
    Vendored version of ReservationAnalyzer logic for migration.
    Cannot import from apps.reports.services due to migration constraints.
    """
    if not recommendation_text:
        return {
            'is_reservation': False,
            'reservation_type': None,
            'commitment_term_years': None,
            'is_savings_plan': False,
            'commitment_category': 'uncategorized',
        }

    full_text = f"{recommendation_text} {potential_benefits}".lower()

    # Check for savings plan
    sp_keywords = ['savings plan', 'compute savings', 'azure savings plan']
    is_savings_plan = any(kw in full_text for kw in sp_keywords)

    # Check for traditional reservation
    res_keywords = ['reserved instance', 'reserved vm', 'reserved capacity',
                    'reservation', 'commit', 'reserve', 'reserved']
    is_reservation = any(kw in full_text for kw in res_keywords) or is_savings_plan

    if not is_reservation:
        return {
            'is_reservation': False,
            'reservation_type': None,
            'commitment_term_years': None,
            'is_savings_plan': False,
            'commitment_category': 'uncategorized',
        }

    # Determine reservation type
    if 'savings plan' in full_text or 'compute savings' in full_text:
        reservation_type = 'savings_plan'
    elif 'reserved vm' in full_text or 'reserved instance' in full_text:
        reservation_type = 'reserved_instance'
    elif 'reserved capacity' in full_text:
        reservation_type = 'reserved_capacity'
    else:
        reservation_type = 'other'

    # Extract commitment term
    if re.search(r'(?:one|1)\s*or\s*(?:three|3)[\s-]*year', full_text, re.IGNORECASE):
        commitment_term = 3
    elif re.search(r'(?:three|3)[\s-]*year|36[\s-]*month', full_text, re.IGNORECASE):
        commitment_term = 3
    elif re.search(r'(?:one|1)[\s-]*year|12[\s-]*month', full_text, re.IGNORECASE):
        commitment_term = 1
    else:
        commitment_term = 3  # Default

    # Categorize
    if is_savings_plan:
        category = 'pure_savings_plan'
    elif reservation_type in ['reserved_instance', 'reserved_capacity']:
        if commitment_term == 1:
            category = 'pure_reservation_1y'
        else:
            category = 'pure_reservation_3y'
    else:
        category = 'uncategorized'

    return {
        'is_reservation': is_reservation,
        'reservation_type': reservation_type,
        'commitment_term_years': commitment_term if is_reservation else None,
        'is_savings_plan': is_savings_plan,
        'commitment_category': category,
    }


def reanalyze_all_recommendations(apps, schema_editor):
    """Re-analyze all existing recommendations."""
    Recommendation = apps.get_model('reports', 'Recommendation')

    total = Recommendation.objects.count()
    updated = 0
    batch_size = 100

    print(f"Re-analyzing {total} recommendations...")

    for offset in range(0, total, batch_size):
        batch = Recommendation.objects.all()[offset:offset + batch_size]

        for rec in batch:
            analysis = analyze_recommendation_text(
                rec.recommendation,
                rec.potential_benefits
            )

            # Only update if analysis found a reservation
            if analysis['is_reservation']:
                rec.is_reservation_recommendation = True
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

    print(f"✓ Re-analyzed and updated {updated} reservation recommendations")


def reverse_reanalysis(apps, schema_editor):
    """Reverse migration."""
    Recommendation = apps.get_model('reports', 'Recommendation')
    Recommendation.objects.all().update(
        is_reservation_recommendation=False,
        reservation_type=None,
        commitment_term_years=None,
        is_savings_plan=False,
        commitment_category='uncategorized'
    )


class Migration(migrations.Migration):
    dependencies = [
        ('reports', '0009_populate_savings_plan_flags'),
    ]

    operations = [
        migrations.RunPython(reanalyze_all_recommendations, reverse_reanalysis),
    ]
```

### Step 2: Run Migration

```bash
python manage.py migrate reports
```

### Step 3: Verify

```python
python manage.py shell

from apps.reports.models import Recommendation

# Check categorization
print("Pure Reservation 1Y:", Recommendation.objects.filter(commitment_category='pure_reservation_1y').count())
print("Pure Reservation 3Y:", Recommendation.objects.filter(commitment_category='pure_reservation_3y').count())
print("Pure Savings Plan:", Recommendation.objects.filter(commitment_category='pure_savings_plan').count())
print("Uncategorized:", Recommendation.objects.filter(commitment_category='uncategorized').count())
```

---

## Conclusion

The issue is **NOT with the template, backend logic, or CSV processor**. All of that code is working correctly.

The problem is that **existing data in the database lacks the necessary field values** because:

1. The data was created before the enhancement
2. Migration 0007 set all NULL reservation flags to FALSE
3. Migration 0009 couldn't backfill because it filtered on fields that were NULL/FALSE
4. Therefore, no recommendations have `commitment_category` set to the values needed for the tables to render

**Fix: Create a new migration that re-analyzes ALL recommendations based on their text content and populates the categorization fields correctly.**
