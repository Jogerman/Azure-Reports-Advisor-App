# Quick Validation Guide: Reservation Categorization Fix

## 1. Verify the Fix is Applied

### Check that tasks.py has been updated:
```bash
grep -A 5 "NEW FIELDS" apps/reports/tasks.py
```

**Expected output:**
```python
# NEW FIELDS - Savings Plan categorization
is_savings_plan=rec_data.get('is_savings_plan', False),
commitment_category=rec_data.get('commitment_category', 'uncategorized'),
```

---

## 2. Test with Sample Data (Recommended)

### Step 1: Create a test CSV file
Create a file named `test_recommendations.csv`:

```csv
Category,Recommendation,Business Impact,Potential Benefits,Subscription ID,Subscription Name,Resource Group,Resource Name,Resource Type,Potential Annual Cost Savings,Currency
Cost,Consider using Azure Reserved VM Instances to save money on virtual machines,High,Reduce virtual machine costs by committing to one or three-year terms,sub-123,Production,rg-prod,vm-prod-01,Microsoft.Compute/virtualMachines,5000,USD
Cost,Consider SQL PaaS DB reserved instance to save costs on Azure SQL,High,Save money with 1 or 3 year reservations,sub-123,Production,rg-prod,sql-prod-01,Microsoft.Sql/servers,3000,USD
Cost,Purchase Azure Savings Plan for flexible compute savings,Medium,Get discounts across VM families with Savings Plan,sub-123,Production,rg-prod,,Microsoft.Compute,2000,USD
Performance,Enable accelerated networking for better VM performance,Medium,Improve network throughput and latency,sub-123,Production,rg-prod,vm-prod-02,Microsoft.Compute/virtualMachines,0,USD
```

### Step 2: Upload via API or Admin Interface
Upload this CSV file as a new report.

### Step 3: Verify Categorization
Check the database or admin interface to verify:

```sql
-- Via Django shell or database query
SELECT
    recommendation,
    is_reservation_recommendation,
    commitment_category,
    is_savings_plan
FROM recommendations
WHERE report_id = '<YOUR_REPORT_ID>'
ORDER BY commitment_category;
```

**Expected Results:**
| Recommendation | is_reservation | commitment_category | is_savings_plan |
|---------------|----------------|---------------------|-----------------|
| Azure Reserved VM Instances | True | pure_reservation_3y | False |
| SQL PaaS DB reserved instance | True | pure_reservation_3y | False |
| Azure Savings Plan | True | pure_savings_plan | True |
| Enable accelerated networking | False | uncategorized | False |

---

## 3. Fix Existing Reports

### Option A: Re-upload CSV Files (Simplest)
1. Download the original CSV file
2. Delete the old report
3. Upload the CSV again
4. Verify correct categorization

### Option B: Run Reclassification Script

#### Dry Run (Check what would change):
```bash
python manage.py reclassify_reservations --dry-run
```

#### Fix Specific Report:
```bash
python manage.py reclassify_reservations --report-id 22b8837d-1e7b-4cfc-b8b4-d8c54730725b
```

#### Fix ALL Reports (Use with caution):
```bash
python manage.py reclassify_reservations
```

#### Fix Only Uncategorized:
```bash
python manage.py reclassify_reservations --only-uncategorized
```

---

## 4. Verify Report 22b8837d-1e7b-4cfc-b8b4-d8c54730725b

### Check current state:
```bash
python manage.py shell
```

```python
from apps.reports.models import Report, Recommendation
from django.db.models import Count

report = Report.objects.get(id='22b8837d-1e7b-4cfc-b8b4-d8c54730725b')
print(f"Report: {report.title}")
print(f"Total recommendations: {report.recommendations.count()}")

# Check distribution
categories = report.recommendations.values('commitment_category').annotate(count=Count('id'))
print("\nCurrent Distribution:")
for cat in categories:
    print(f"  {cat['commitment_category']}: {cat['count']}")

# Sample some recommendations with 'reserved' in the text
samples = report.recommendations.filter(recommendation__icontains='reserved')[:5]
print("\nSample recommendations containing 'reserved':")
for rec in samples:
    print(f"  {rec.recommendation[:80]}...")
    print(f"    Category: {rec.commitment_category}")
```

### Run reclassification:
```bash
python manage.py reclassify_reservations --report-id 22b8837d-1e7b-4cfc-b8b4-d8c54730725b
```

### Verify after reclassification:
```python
# Run the same check again to see the changes
categories = report.recommendations.values('commitment_category').annotate(count=Count('id'))
print("\nAfter Reclassification:")
for cat in categories:
    print(f"  {cat['commitment_category']}: {cat['count']}")
```

**Expected Change:**
- Before: 716 uncategorized
- After: Mix of pure_reservation_3y, pure_reservation_1y, pure_savings_plan, uncategorized

---

## 5. Frontend Verification

### Check Report Display
1. Open the report in the frontend
2. Navigate to the recommendations section
3. Verify that tables show data:
   - "Pure Reservations - 1 Year" table (if any 1-year recommendations)
   - "Pure Reservations - 3 Years" table (should have data)
   - "Pure Savings Plans" table (if any savings plan recommendations)

---

## 6. Monitor New Uploads

### After Deployment:
1. Upload a test CSV with known reservation recommendations
2. Check immediately if categorization is correct
3. Verify no errors in logs:
   ```bash
   tail -f logs/django.log | grep -i "reservation\|category"
   ```

---

## Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'apps.reports.services.reservation_analyzer'"
**Solution**: Check that the file exists:
```bash
ls -la apps/reports/services/reservation_analyzer.py
```

### Issue: "Field 'commitment_category' doesn't exist"
**Solution**: Run migrations:
```bash
python manage.py migrate reports
```

### Issue: Reclassification shows "0 updated"
**Possible causes:**
1. The report already has correct categorization (check current distribution)
2. No reservation-related recommendations in the report
3. The text doesn't contain reservation keywords

---

## Success Criteria

✅ New CSV uploads correctly categorize recommendations
✅ Report 22b8837d-1e7b-4cfc-b8b4-d8c54730725b shows non-zero counts for reservation categories
✅ Frontend displays recommendations in the correct tables
✅ No errors in application logs during CSV processing

---

## Quick Command Reference

```bash
# Check code fix
grep -A 5 "NEW FIELDS" apps/reports/tasks.py

# Dry run reclassification
python manage.py reclassify_reservations --dry-run

# Fix specific report
python manage.py reclassify_reservations --report-id <UUID>

# Fix all uncategorized
python manage.py reclassify_reservations --only-uncategorized

# Check report status
python manage.py shell -c "from apps.reports.models import Report; r = Report.objects.get(id='<UUID>'); print(f'Total: {r.recommendations.count()}')"

# View logs
tail -f logs/django.log | grep -i "reservation"
```

---

## Need Help?

Refer to the comprehensive report: `CRITICAL_BUG_FIX_REPORT.md`
