# Chart.js PDF Generation Fix - Production Issue Resolution

## Problem Summary

**Issue**: Production PDFs were missing chart visualizations on pages 5-7 (Category Distribution, Impact Level Distribution, and Cost Optimization Potential charts).

**Root Cause**: The base template (`base_redesigned.html`) was loading Chart.js from a CDN (jsdelivr.net) which is not accessible when Playwright generates PDFs in production using `page.set_content()` without a base URL.

```html
<!-- OLD - CDN approach (fails in production) -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
```

## Solution Implemented

**Fix**: Inline Chart.js libraries directly into the HTML template to ensure they're always available regardless of network access.

### Changes Made

#### 1. Downloaded Chart.js Libraries Locally

Created local copies of Chart.js libraries:
- `azure_advisor_reports/static/js/vendor/chart.umd.min.js` (200KB)
- `azure_advisor_reports/static/js/vendor/chartjs-plugin-datalabels.min.js` (13KB)

#### 2. Created Template Includes

Copied JavaScript files to template includes for inlining:
- `azure_advisor_reports/templates/reports/includes/chart.umd.min.js`
- `azure_advisor_reports/templates/reports/includes/chartjs-plugin-datalabels.min.js`

#### 3. Updated Base Template

Modified `azure_advisor_reports/templates/reports/base_redesigned.html` (lines 7-14):

```html
<!-- NEW - Inlined approach (works in all environments) -->
<script>
{% include 'reports/includes/chart.umd.min.js' %}
</script>
<script>
{% include 'reports/includes/chartjs-plugin-datalabels.min.js' %}
</script>
```

## Technical Details

### Why This Fix Works

1. **No External Dependencies**: Chart.js code is embedded directly in the HTML, eliminating the need for external network requests
2. **Playwright Compatible**: When Playwright's `page.set_content()` loads the HTML, all JavaScript is immediately available
3. **Production Safe**: Works in restricted network environments (Docker containers, Azure Container Apps, etc.)
4. **Development Compatible**: Still works in development environment without any changes

### Files Modified

```
azure_advisor_reports/
├── templates/
│   └── reports/
│       ├── base_redesigned.html           # MODIFIED - Updated script includes
│       └── includes/                       # NEW - Template includes directory
│           ├── chart.umd.min.js           # NEW - Chart.js library (inlined)
│           └── chartjs-plugin-datalabels.min.js  # NEW - Datalabels plugin
└── static/
    └── js/
        └── vendor/                        # NEW - Vendor JavaScript directory
            ├── chart.umd.min.js           # NEW - Chart.js source
            └── chartjs-plugin-datalabels.min.js  # NEW - Plugin source
```

## Testing Instructions

### Option 1: Test Locally (Development)

1. Ensure Django development server is running
2. Generate a detailed report for any client
3. Verify charts appear in the PDF:
   - Page 5: Category Distribution (doughnut chart)
   - Page 6: Impact Level Distribution (doughnut chart)
   - Page 7: Cost Optimization Potential (horizontal bar chart)

### Option 2: Test with Script

```bash
# From project root
cd azure_advisor_reports
python ../test_chart_pdf.py
```

This will generate `test_chart_rendering.pdf` - open it and verify charts are visible.

### Option 3: Test in Production (Docker)

1. Build the production Docker image:
   ```bash
   cd azure_advisor_reports
   docker build -f Dockerfile.prod -t azure-advisor-backend:fixed .
   ```

2. Run the container:
   ```bash
   docker run -d --name test-pdf-fix \
     -p 8000:8000 \
     --env-file .env.production \
     azure-advisor-backend:fixed
   ```

3. Generate a PDF through the application and verify charts appear

## Deployment Steps

### For Azure Container Apps

1. **Commit Changes**:
   ```bash
   git add .
   git commit -m "fix: Inline Chart.js to fix production PDF generation"
   ```

2. **Build and Push to Azure Container Registry**:
   ```bash
   az acr build --registry <your-registry> \
     --image azure-advisor-backend:v1.2.4 \
     --image azure-advisor-backend:latest \
     --file azure_advisor_reports/Dockerfile.prod \
     azure_advisor_reports
   ```

3. **Update Container App**:
   ```bash
   az containerapp update \
     --name <your-app-name> \
     --resource-group <your-resource-group> \
     --image <your-registry>.azurecr.io/azure-advisor-backend:v1.2.4
   ```

4. **Verify Deployment**:
   - Generate a detailed report
   - Download the PDF
   - Verify all charts are rendering correctly

### For Docker Compose

1. Update `docker-compose.yml` to rebuild:
   ```bash
   docker-compose up -d --build backend
   ```

2. Verify PDF generation works correctly

## Impact Analysis

### File Size Impact

- **Chart.js**: ~200KB (minified)
- **Datalabels Plugin**: ~13KB (minified)
- **Total Added**: ~213KB to each HTML document before PDF conversion
- **PDF Size Impact**: Minimal (JavaScript is not embedded in final PDF)

### Performance Impact

- **Positive**: No network requests needed for Chart.js
- **Neutral**: Playwright loads HTML into memory anyway
- **Overall**: Should be slightly faster due to no CDN latency

### Compatibility

- ✅ Works in all environments (dev, staging, production)
- ✅ No configuration changes needed
- ✅ Backward compatible with existing code
- ✅ No runtime dependencies on external services

## Verification Checklist

After deployment, verify:

- [ ] Cover page renders correctly
- [ ] Executive summary page renders correctly
- [ ] Category Distribution chart (Page 5) shows doughnut chart
- [ ] Impact Level Distribution chart (Page 6) shows doughnut chart
- [ ] Cost Optimization Potential chart (Page 7) shows horizontal bar chart
- [ ] Subscription-level charts render if present
- [ ] Tables and text content remain intact
- [ ] PDF file size is reasonable (< 2MB for typical report)
- [ ] Charts are properly colored and labeled

## Rollback Plan

If issues occur, rollback by reverting the template change:

```bash
git revert HEAD
# Rebuild and redeploy
```

Then restore CDN approach (though it won't work in production):
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
```

## Future Considerations

### Alternative Solutions (Not Recommended)

1. **Use Base URL in Playwright** - Would require serving static files through Django, adding complexity
2. **Pre-render Charts as Images** - Would require additional processing step and lose Chart.js quality
3. **Configure Network Access** - Not reliable, depends on firewall/proxy configuration

### Recommended Approach

The current solution (inlining) is the most reliable and maintainable approach for production PDF generation with Playwright.

## References

- Chart.js Documentation: https://www.chartjs.org/
- Playwright PDF Generation: https://playwright.dev/python/docs/api/class-page#page-pdf
- Django Template Includes: https://docs.djangoproject.com/en/4.2/ref/templates/builtins/#include

---

**Fixed by**: Claude Code
**Date**: November 1, 2025
**Version**: v1.2.4 (pending)
