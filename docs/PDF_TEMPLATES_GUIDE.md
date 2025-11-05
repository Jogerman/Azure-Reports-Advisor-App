# Azure Advisor PDF-Optimized Templates Guide

## Overview

Three new PDF-optimized templates have been created specifically for WeasyPrint PDF generation. These templates replace modern CSS features with WeasyPrint-compatible alternatives while maintaining professional Azure branding.

## Created Templates

1. **`executive_pdf.html`** - Executive Summary Report (PDF-optimized)
2. **`cost_pdf.html`** - Cost Optimization Report (PDF-optimized)
3. **`security_pdf.html`** - Security Assessment Report (PDF-optimized)

**Location:** `D:\Code\Azure Reports\azure_advisor_reports\templates\reports\`

---

## Key Changes for WeasyPrint Compatibility

### 1. CSS Grid → Table Layouts
**Problem:** WeasyPrint doesn't support CSS Grid (`display: grid`, `grid-template-columns`)

**Solution:**
- Used HTML `<table>` elements with `border-collapse: separate` and `border-spacing` for metric card layouts
- Replaced grid-based charts with table-based layouts
- Example:
```html
<!-- OLD: CSS Grid -->
<div class="metrics-grid">
  <div class="metric-card">...</div>
</div>

<!-- NEW: Table Layout -->
<table class="metrics-table">
  <tr>
    <td><div class="metric-card">...</div></td>
  </tr>
</table>
```

### 2. CSS Variables → Hardcoded Values
**Problem:** WeasyPrint has limited support for CSS variables (`var(--color-primary)`)

**Solution:**
- Replaced all CSS variables with hardcoded color values
- Azure Blue: `#0078D4`
- Success Green: `#107C10`
- Warning Orange: `#FF8C00`
- Danger Red: `#D13438`
- Gray scales: `#FAFAFA`, `#E1DFDD`, `#605E5C`, `#201F1E`

### 3. Modern CSS Properties → Basic Alternatives
**Problem:** WeasyPrint doesn't support:
- `backdrop-filter: blur(10px)`
- `gap: 20px` (in flexbox/grid)
- Complex `box-shadow` with multiple layers
- Media queries with `max-width`

**Solution:**
- Removed `backdrop-filter` entirely (used solid backgrounds)
- Replaced `gap` with `border-spacing` in tables or margins
- Simplified box shadows to: `box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);`
- Removed responsive media queries (PDF has fixed dimensions)

### 4. Chart.js → HTML/CSS Visualizations
**Problem:** JavaScript doesn't execute in PDFs (Chart.js won't render)

**Solution:** Created pure HTML/CSS alternatives:

#### Doughnut Charts → Horizontal Bar Charts
```html
<div class="bar-chart-item">
  <div class="bar-chart-label">Category Name (Count)</div>
  <div class="bar-chart-bar">
    <div class="bar-chart-fill" style="width: 75%; background-color: #0078D4;"></div>
    <div class="bar-chart-value">75%</div>
  </div>
</div>
```

#### Progress Circles → Simple Bordered Circles
```html
<div class="security-score-circle excellent">
  <div class="security-score-value excellent">85</div>
</div>
```

#### Distribution Bars → Segmented Divs
```html
<div class="risk-distribution-bar">
  <div class="risk-segment critical" style="width: 30%;"></div>
  <div class="risk-segment high" style="width: 50%;"></div>
  <div class="risk-segment medium" style="width: 20%;"></div>
</div>
```

---

## WeasyPrint Page Setup

Each template includes proper `@page` rules for PDF generation:

```css
@page {
    size: A4;
    margin: 2cm 1.5cm;

    @top-center {
        content: "Azure Advisor Report - {{ client.company_name }}";
        font-size: 9pt;
        color: #605E5C;
    }

    @bottom-right {
        content: "Page " counter(page) " of " counter(pages);
        font-size: 9pt;
        color: #605E5C;
    }
}
```

**Features:**
- A4 page size
- Automatic page headers and footers
- Page numbers with "Page X of Y" format
- `page-break-after: always` for cover pages
- `page-break-inside: avoid` for sections

---

## Template Structure

### Executive PDF Template (`executive_pdf.html`)

**Cover Page:**
- Azure gradient background (Blue → Purple)
- Company name, report title, date
- Key metrics: Total recommendations, potential savings

**Content Sections:**
1. Key Metrics (4 metric cards)
2. Key Insights (strategic overview)
3. Recommendations Distribution (bar charts + table)
4. Quick Wins table
5. Top 10 Recommendations by Value
6. Strategic Implementation Roadmap (3 phases)
7. Executive Action Items

**Color Scheme:** Azure Blue (`#0078D4`)

---

### Cost PDF Template (`cost_pdf.html`)

**Cover Page:**
- Green gradient background (Success theme)
- Annual savings prominently displayed

**Content Sections:**
1. Financial Impact Metrics (4 cards)
2. ROI Analysis (implementation cost, net benefit, ROI %, 3-year savings)
3. Savings Distribution (bar chart by resource type)
4. Top Cost-Saving Opportunities table
5. Quick Wins table
6. Savings Breakdown by Resource Type
7. Implementation Roadmap (3 phases)
8. Next Steps & Governance

**Color Scheme:** Success Green (`#107C10`)

---

### Security PDF Template (`security_pdf.html`)

**Cover Page:**
- Orange/Red gradient background (Security theme)
- Security score prominently displayed

**Content Sections:**
1. Security Score Gauge (visual circle indicator)
2. Remediation Timeline (Immediate, Short-term, Medium-term)
3. Threat Landscape Overview (bar charts)
4. Critical Security Issues table (if any)
5. High Priority Security Issues table
6. Security by Subscription table
7. Compliance & Regulatory Frameworks (badges)
8. Security Remediation Roadmap (3 phases)
9. Immediate Action Items

**Color Scheme:** Warning Orange (`#FF8C00`) and Danger Red (`#D13438`)

---

## Data Variables Used

All templates use the same Django template variables as the enhanced versions:

### Executive Template
- `client.company_name`
- `generated_date`
- `summary_metrics.total_recommendations`
- `summary_metrics.total_savings`
- `summary_metrics.monthly_savings`
- `summary_metrics.high_priority_count`
- `summary_metrics.categories_affected`
- `category_chart_data` (list with: category, count, percentage, color)
- `high_impact_count`, `medium_impact_count`, `low_impact_count`
- `quick_wins` (queryset)
- `top_10_recommendations` (queryset)

### Cost Template
- `total_annual_savings`
- `total_monthly_savings`
- `cost_recommendations` (queryset)
- `quick_wins` (queryset)
- `quick_wins_total`, `quick_wins_monthly`
- `roi_analysis.payback_months`
- `roi_analysis.estimated_implementation_cost`
- `roi_analysis.net_benefit`
- `roi_analysis.roi_percentage`
- `top_cost_savers` (queryset)
- `top_cost_savers_total`
- `cost_by_resource_type` (list with: resource_type, count, total_savings, monthly_savings, percentage)
- `long_term_opportunities` (queryset)
- `long_term_total`

### Security Template
- `security_score` (0-100)
- `total_security_findings`
- `critical_count`, `high_count`, `medium_count`
- `critical_issues` (queryset)
- `high_priority_issues` (queryset)
- `security_by_subscription` (list with: subscription_name, critical_count, high_count, medium_count, total_count)
- `security_by_resource_type` (list with: resource_type, count)

---

## How to Use These Templates

### Option 1: Update Views to Use PDF Templates

In your Django views (`views.py`), add logic to select the PDF template when generating PDFs:

```python
from django.shortcuts import render
from weasyprint import HTML

def generate_executive_pdf(request, report_id):
    report = get_object_or_404(Report, pk=report_id)

    # Use the PDF-optimized template
    html_string = render_to_string('reports/executive_pdf.html', {
        'report': report,
        'client': report.client,
        'generated_date': timezone.now(),
        'summary_metrics': get_summary_metrics(report),
        # ... other context
    })

    # Generate PDF with WeasyPrint
    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="executive_report_{report.id}.pdf"'
    return response
```

### Option 2: Add URL Parameter for PDF Format

Add a URL parameter to switch between HTML and PDF templates:

```python
def executive_report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    format_type = request.GET.get('format', 'html')  # 'html' or 'pdf'

    template = 'reports/executive_pdf.html' if format_type == 'pdf' else 'reports/executive_enhanced.html'

    context = {
        'report': report,
        # ... context data
    }

    if format_type == 'pdf':
        # Generate PDF
        html_string = render_to_string(template, context)
        pdf = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="report_{report_id}.pdf"'
        return response
    else:
        # Render HTML
        return render(request, template, context)
```

---

## Testing with WeasyPrint

### Install WeasyPrint

```bash
pip install weasyprint
```

### Test PDF Generation

```python
from weasyprint import HTML

# Test executive report
HTML('D:/Code/Azure Reports/azure_advisor_reports/templates/reports/executive_pdf.html').write_pdf('test_executive.pdf')

# Test cost report
HTML('D:/Code/Azure Reports/azure_advisor_reports/templates/reports/cost_pdf.html').write_pdf('test_cost.pdf')

# Test security report
HTML('D:/Code/Azure Reports/azure_advisor_reports/templates/reports/security_pdf.html').write_pdf('test_security.pdf')
```

---

## Design Features Preserved

✅ **Professional Azure branding** (colors, gradients, typography)
✅ **Cover pages** with gradient backgrounds
✅ **Metric cards** with color-coded borders
✅ **Data tables** with proper styling
✅ **Info boxes** (success, warning, danger, info)
✅ **Badges** for categories and priorities
✅ **Visual data representations** (bars, progress indicators)
✅ **Page headers and footers** with page numbers
✅ **Section headers** with icons
✅ **Proper page breaks** (cover pages, sections)
✅ **Professional typography** (Segoe UI font stack)

---

## WeasyPrint CSS Support Reference

### ✅ Supported
- Basic selectors (class, id, element, descendant)
- `display: block`, `inline`, `inline-block`, `table`, `table-cell`
- `float: left/right`
- `position: relative/absolute`
- Basic `flexbox` (limited support)
- `border`, `padding`, `margin`
- `background`, `background-color`, `background: linear-gradient()`
- Simple `box-shadow` (single shadow only)
- `border-radius`
- `@page` rules with margins and content
- `page-break-before`, `page-break-after`, `page-break-inside`
- Web fonts (via `@font-face`)

### ❌ Not Supported
- CSS Grid (`display: grid`)
- CSS Variables (`var(--name)`)
- `backdrop-filter`
- `gap` property
- Complex multi-layer `box-shadow`
- `transform: rotate/scale/skew` (limited support)
- `@media` queries
- JavaScript execution
- Interactive elements (hover states won't work in PDF)

---

## Troubleshooting Common Issues

### Issue: Fonts not rendering correctly
**Solution:** Install the Segoe UI font on the server, or use web fonts:
```css
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;600;700&display=swap');
body { font-family: 'Roboto', Arial, sans-serif; }
```

### Issue: Images not loading
**Solution:** Use absolute paths or base64-encoded images:
```html
<img src="file:///absolute/path/to/image.png" />
<!-- OR -->
<img src="data:image/png;base64,iVBORw0KGgoAAAANS..." />
```

### Issue: Colors look washed out
**Solution:** Add print color adjustment:
```css
* {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}
```

### Issue: Page breaks in wrong places
**Solution:** Use `page-break-inside: avoid` on containers:
```css
.section, .metric-card, .table-container {
    page-break-inside: avoid;
}
```

---

## File Locations

```
D:\Code\Azure Reports\azure_advisor_reports\templates\reports\
├── executive_pdf.html     (NEW - PDF-optimized Executive Report)
├── cost_pdf.html          (NEW - PDF-optimized Cost Report)
├── security_pdf.html      (NEW - PDF-optimized Security Report)
├── executive_enhanced.html (Original - Browser version)
├── cost_enhanced.html      (Original - Browser version)
└── security_enhanced.html  (Original - Browser version)
```

---

## Next Steps

1. **Update Views:** Modify your Django views to use the PDF templates when generating PDFs
2. **Test PDF Generation:** Use WeasyPrint to generate test PDFs and verify formatting
3. **Add Download Buttons:** Add "Download PDF" buttons to your HTML reports that trigger PDF generation
4. **Configure WeasyPrint:** Ensure WeasyPrint is properly installed and configured in production
5. **Performance Optimization:** Consider caching generated PDFs for frequently accessed reports

---

## Additional Resources

- **WeasyPrint Documentation:** https://doc.courtbouillon.org/weasyprint/
- **CSS Print Documentation:** https://developer.mozilla.org/en-US/docs/Web/CSS/@page
- **Azure Design Guidelines:** https://learn.microsoft.com/en-us/azure/architecture/guide/design-principles/

---

**Created:** {{ generated_date|date:"F d, Y" }}
**Author:** Claude Code
**Version:** 1.0
