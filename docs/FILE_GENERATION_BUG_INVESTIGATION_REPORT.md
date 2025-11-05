# File Generation Bug Investigation Report

## Executive Summary

The "Generate Files" button was not working due to **absolute file paths being stored in the database** instead of relative paths. This caused Django's FileField to double-prepend the `/media/` prefix, resulting in broken URLs like `/media/app/media/reports/...`.

**Status**: FIXED ✓

All issues have been resolved:
1. File path storage bug fixed in generators
2. Download endpoint updated to display HTML inline (not download)
3. Existing reports migrated to correct paths
4. New file generation tested and working correctly

---

## Problem Description

### User Experience
- User clicks "Generate Files" button
- API returns 202 Accepted
- Celery task completes successfully
- BUT: Buttons remain disabled
- Reason: Files were being generated but paths were broken

### Root Cause
The file generation process was saving **absolute paths** (`/app/media/reports/html/...`) to the database instead of **relative paths** (`reports/html/...`), causing Django's FileField to malfunction.

---

## Technical Investigation

### 1. Flow Analysis

```
┌─────────────────────────────────────────────────────────────────┐
│ Frontend: Click "Generate Files"                                 │
│   POST /api/v1/reports/{id}/generate/ (format='both')           │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Backend View (views.py:412)                                      │
│   - Validates report status                                      │
│   - Triggers Celery task: generate_report.delay()                │
│   - Returns 202 Accepted                                         │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Celery Task (tasks.py:166)                                       │
│   - Calls generator.generate_html()                              │
│   - Calls generator.generate_pdf()                               │
│   - ❌ BUG: Stored absolute paths to database                    │
│   - Task returns success                                         │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Database (Report model)                                          │
│   html_file: '/app/media/reports/html/xxx.html' ❌ WRONG         │
│   pdf_file: '/app/media/reports/pdf/xxx.pdf'    ❌ WRONG         │
│                                                                   │
│   SHOULD BE:                                                     │
│   html_file: 'reports/html/xxx.html' ✓                          │
│   pdf_file: 'reports/pdf/xxx.pdf'    ✓                          │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Serializer Output (API Response)                                 │
│   html_file: '/media/app/media/reports/html/xxx.html' ❌         │
│   pdf_file: '/media/app/media/reports/pdf/xxx.pdf'    ❌         │
│                                                                   │
│   Django prepended /media/ to the absolute path!                 │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Frontend (ReportList.tsx:266)                                    │
│   Checks: !report.html_file && !report.pdf_file                  │
│   Result: FALSE (broken paths are truthy strings)                │
│   Action: Hides "Generate Files" button ❌                       │
│           Enables download buttons (but URLs are broken) ❌      │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Bug Locations

#### Bug #1: Absolute Path Storage in `base.py`

**File**: `azure_advisor_reports/apps/reports/generators/base.py`

**Lines 228-260**: `save_html()` method
```python
# ❌ BEFORE (Line 256):
self.report.html_file = relative_path
self.report.save(update_fields=['html_file'])
logger.info(f"HTML file saved: {filepath}")
return filepath  # ❌ Returns ABSOLUTE path

# ✓ AFTER:
logger.info(f"HTML file saved: {filepath}")
return relative_path  # ✓ Returns RELATIVE path
# Caller handles saving to database
```

**Lines 261-355**: `generate_pdf()` method
```python
# ❌ BEFORE (Line 338-339):
self.report.pdf_file = pdf_relative_path
self.report.save(update_fields=['pdf_file'])
return pdf_filepath  # ❌ Returns ABSOLUTE path

# ✓ AFTER:
return pdf_relative_path  # ✓ Returns RELATIVE path
# Caller handles saving to database
```

**Impact**: Generators were returning absolute filesystem paths AND saving them directly to the database.

#### Bug #2: HTML Download vs Display

**File**: `azure_advisor_reports/apps/reports/views.py`

**Lines 654-751**: `download_report()` method
```python
# ❌ BEFORE (Line 716):
as_attachment=True  # Forces download for BOTH HTML and PDF

# ✓ AFTER (Line 728):
as_attachment = file_format == 'pdf'  # Only PDF downloads, HTML displays inline
```

**Impact**: HTML files were being downloaded instead of displayed in the browser.

#### Bug #3: Path Handling in Download Endpoint

**File**: `azure_advisor_reports/apps/reports/views.py`

**Lines 691-698**: Added path normalization
```python
# ✓ ADDED: Handle both relative and absolute paths
file_path_str = file_field.name if hasattr(file_field, 'name') else str(file_field)
file_path_str = file_path_str.replace('/app/media/', '').replace('/media/', '')
full_path = os.path.join(settings.MEDIA_ROOT, file_path_str)
```

**Impact**: Download endpoint can now handle legacy absolute paths gracefully.

### 3. Database Evidence

**Before Fix**:
```sql
SELECT id, html_file, pdf_file FROM reports;

id: 9acb270d-6c9b-4509-bafe-d3b1581c19ec
html_file: /app/media/reports/html/9acb270d-6c9b-4509-bafe-d3b1581c19ec_detailed.html
pdf_file:  /app/media/reports/pdf/9acb270d-6c9b-4509-bafe-d3b1581c19ec_detailed.pdf
```

**After Fix**:
```sql
id: 9acb270d-6c9b-4509-bafe-d3b1581c19ec
html_file: reports/html/9acb270d-6c9b-4509-bafe-d3b1581c19ec_detailed.html
pdf_file:  reports/pdf/9acb270d-6c9b-4509-bafe-d3b1581c19ec_detailed.pdf
```

### 4. API Serializer Output

**Before Fix**:
```json
{
  "html_file": "/media/app/media/reports/html/xxx.html",  ❌ BROKEN
  "pdf_file": "/media/app/media/reports/pdf/xxx.pdf"      ❌ BROKEN
}
```

**After Fix**:
```json
{
  "html_file": "/media/reports/html/xxx.html",  ✓ CORRECT
  "pdf_file": "/media/reports/pdf/xxx.pdf"      ✓ CORRECT
}
```

---

## Fixes Implemented

### Fix #1: Corrected File Path Storage
**Files Modified**:
- `azure_advisor_reports/apps/reports/generators/base.py`

**Changes**:
1. Modified `save_html()` to return relative path only (line 259)
2. Removed direct database save from `save_html()` (let caller handle it)
3. Modified `generate_pdf()` to return relative path only (line 345)
4. Removed direct database save from `generate_pdf()` (let caller handle it)
5. Added path normalization in `generate_pdf()` for backwards compatibility (lines 284-287)

### Fix #2: Updated Download Endpoint Behavior
**Files Modified**:
- `azure_advisor_reports/apps/reports/views.py`

**Changes**:
1. Updated docstring to clarify HTML displays inline, PDF downloads (lines 657-664)
2. Added path normalization for both relative and absolute paths (lines 691-698)
3. Changed `as_attachment` to be conditional: `file_format == 'pdf'` (line 728)
4. Updated logging to reflect display vs download action (line 738)
5. Added debug info to 404 responses (lines 707-710)

### Fix #3: Migrated Existing Reports
**Method**: Direct database update via Django shell

**Script Used**:
```python
from apps.reports.models import Report

reports = Report.objects.all()
fixed_count = 0

for report in reports:
    updated = False

    if report.html_file:
        html_path = str(report.html_file)
        if '/app/media/' in html_path or '/media/' in html_path:
            fixed_html = html_path.replace('/app/media/', '').replace('/media/', '')
            report.html_file = fixed_html.lstrip('/')
            updated = True

    if report.pdf_file:
        pdf_path = str(report.pdf_file)
        if '/app/media/' in pdf_path or '/media/' in pdf_path:
            fixed_pdf = pdf_path.replace('/app/media/', '').replace('/media/', '')
            report.pdf_file = fixed_pdf.lstrip('/')
            updated = True

    if updated:
        report.save(update_fields=['html_file', 'pdf_file'])
        fixed_count += 1

print(f"Fixed {fixed_count} reports")
```

**Result**: Fixed 1 existing report

### Fix #4: Created Management Command
**Files Created**:
- `azure_advisor_reports/apps/reports/management/__init__.py`
- `azure_advisor_reports/apps/reports/management/commands/__init__.py`
- `azure_advisor_reports/apps/reports/management/commands/fix_report_paths.py`

**Usage** (for future reference):
```bash
python manage.py fix_report_paths --dry-run  # Preview changes
python manage.py fix_report_paths            # Apply changes
```

---

## Testing Results

### Test #1: Existing Report Migration
```
✓ Database values updated correctly
✓ Serializer output shows correct paths
✓ FileField.url() returns correct URLs
```

### Test #2: Fresh File Generation
```
✓ HTML file generated with relative path: reports/html/xxx.html
✓ PDF file generated with relative path: reports/pdf/xxx.pdf
✓ Task returns success with correct file paths
✓ Database contains relative paths
✓ Serializer outputs correct /media/ URLs
```

### Test #3: Celery Task Logs
```
[2025-10-13 23:24:41] INFO HTML report generated: reports/html/xxx.html
[2025-10-13 23:24:41] INFO PDF report generated: reports/pdf/xxx.pdf
[2025-10-13 23:24:41] INFO Report generation completed for xxx: HTML, PDF
[2025-10-13 23:24:41] Task succeeded in 3.6s
```

---

## Frontend Behavior Changes

### Before Fix
1. User clicks "Generate Files" ✓
2. Files are generated ✓
3. "Generate Files" button **remains visible** ❌ (paths are broken but truthy)
4. HTML button enabled but **download link is broken** ❌
5. PDF button enabled but **download link is broken** ❌

### After Fix
1. User clicks "Generate Files" ✓
2. Files are generated ✓
3. "Generate Files" button **disappears** ✓ (condition checks pass)
4. HTML button enabled and **displays report in browser** ✓
5. PDF button enabled and **downloads PDF file** ✓

---

## File Access URLs

### HTML Report (Display in Browser)
```
URL: GET /api/v1/reports/{id}/download/html/
Behavior: Content-Disposition: inline
Result: HTML displays in browser tab (not downloaded)
```

### PDF Report (Download)
```
URL: GET /api/v1/reports/{id}/download/pdf/
Behavior: Content-Disposition: attachment
Result: PDF file downloads to user's computer
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        File Generation Flow                      │
└─────────────────────────────────────────────────────────────────┘

Frontend                Backend                Celery Worker
   │                       │                         │
   │  Generate Files       │                         │
   ├──────────────────────>│                         │
   │  POST /generate/      │  Trigger Task           │
   │                       ├────────────────────────>│
   │                       │                         │
   │  202 Accepted         │                         │ Generate HTML
   │<──────────────────────│                         │   ↓
   │                       │                         │ Save to:
   │                       │                         │ /app/media/reports/html/xxx.html
   │                       │                         │   ↓
   │  (Poll for status)    │                         │ Store in DB:
   │  ───────────────────> │                         │ 'reports/html/xxx.html' ✓
   │                       │                         │   ↓
   │                       │                         │ Generate PDF
   │                       │                         │   ↓
   │                       │                         │ Save to:
   │                       │                         │ /app/media/reports/pdf/xxx.pdf
   │                       │                         │   ↓
   │                       │                         │ Store in DB:
   │                       │  Task Complete          │ 'reports/pdf/xxx.pdf' ✓
   │                       │<────────────────────────│
   │                       │                         │
   │  GET /reports/{id}/   │                         │
   │<──────────────────────│                         │
   │  {                    │                         │
   │    html_file: "/media/reports/html/xxx.html" ✓ │
   │    pdf_file: "/media/reports/pdf/xxx.pdf"    ✓ │
   │  }                    │                         │
   │                       │                         │
   │  Click HTML button    │                         │
   │  ──────────────────>  │                         │
   │  GET /download/html/  │                         │
   │                       │ Read file               │
   │                       │ /app/media/reports/html/xxx.html
   │  <HTML content>       │                         │
   │  (displays inline)    │                         │
   │<──────────────────────│                         │
   │                       │                         │
   │  Click PDF button     │                         │
   │  ──────────────────>  │                         │
   │  GET /download/pdf/   │                         │
   │                       │ Read file               │
   │                       │ /app/media/reports/pdf/xxx.pdf
   │  <PDF binary>         │                         │
   │  (downloads file)     │                         │
   │<──────────────────────│                         │
```

---

## Key Learnings

### 1. Django FileField Path Handling
- **ALWAYS** store relative paths in FileField (relative to MEDIA_ROOT)
- Django automatically prepends MEDIA_URL when accessing `.url` property
- Absolute paths break this mechanism and cause double-prefixing

### 2. File Response Types
- Use `as_attachment=True` for file downloads
- Use `as_attachment=False` (or `inline`) for browser display
- HTML reports should display inline for better UX
- PDF reports should download for user's convenience

### 3. Celery Task Design
- Generators should return paths, not save to database
- Tasks should handle all database updates
- Separation of concerns improves testability and flexibility

### 4. Migration Strategy
- Always provide migration path for existing data
- Use management commands for one-time fixes
- Include dry-run option for safety
- Log all changes for audit trail

---

## Checklist for Future File Storage

When implementing file storage features:

- [ ] Store relative paths in FileField (relative to MEDIA_ROOT)
- [ ] Never save absolute filesystem paths to database
- [ ] Use Django's built-in URL generation (`.url` property)
- [ ] Test serializer output to verify correct /media/ prefix
- [ ] Handle legacy data gracefully (normalize paths on read)
- [ ] Document expected path format in docstrings
- [ ] Add validation for path format in model save()
- [ ] Test file access from both API and browser
- [ ] Verify Content-Disposition header for downloads vs display

---

## Files Modified

### Backend Changes
1. `azure_advisor_reports/apps/reports/generators/base.py` - Fixed path storage
2. `azure_advisor_reports/apps/reports/views.py` - Fixed download endpoint

### New Files Created
3. `azure_advisor_reports/apps/reports/management/__init__.py` - Package init
4. `azure_advisor_reports/apps/reports/management/commands/__init__.py` - Commands package
5. `azure_advisor_reports/apps/reports/management/commands/fix_report_paths.py` - Migration command

### Documentation
6. `FILE_GENERATION_BUG_INVESTIGATION_REPORT.md` - This report

---

## Deployment Notes

### Required Actions
1. ✓ Deploy backend code changes (base.py, views.py)
2. ✓ Restart backend service
3. ✓ Restart celery-worker service
4. ✓ Run migration command to fix existing reports
5. No frontend changes required
6. No database schema changes required

### Verification Steps
```bash
# 1. Check service status
docker-compose ps

# 2. Test file generation
curl -X POST http://localhost:8000/api/v1/reports/{id}/generate/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"format": "both"}'

# 3. Verify database paths
docker-compose exec backend python manage.py shell -c \
  "from apps.reports.models import Report; \
   r = Report.objects.first(); \
   print(f'HTML: {r.html_file}\\nPDF: {r.pdf_file}')"

# 4. Test download endpoints
curl -v http://localhost:8000/api/v1/reports/{id}/download/html/ \
  -H "Authorization: Bearer {token}"

curl -v http://localhost:8000/api/v1/reports/{id}/download/pdf/ \
  -H "Authorization: Bearer {token}"
```

---

## Support Information

### Common Issues

**Issue**: Files not appearing after generation
**Solution**: Check Celery worker logs for errors

**Issue**: 404 when downloading files
**Solution**: Verify file exists on disk at MEDIA_ROOT location

**Issue**: HTML downloads instead of displaying
**Solution**: Verify `as_attachment` parameter in download endpoint

### Monitoring
- Check Celery worker logs: `docker-compose logs celery-worker`
- Check backend logs: `docker-compose logs backend`
- Monitor file generation duration in task logs
- Track file storage usage in /app/media/reports/

---

## Status: RESOLVED ✓

All bugs have been fixed and tested successfully. The file generation feature now works as expected:
- Files generate correctly with relative paths
- Database stores paths in correct format
- Frontend buttons enable/disable correctly
- HTML displays in browser
- PDF downloads as file

**Date Fixed**: 2025-10-13
**Fixed By**: Claude Code (Senior Backend Architect)
**Verified**: Yes - All tests passing
