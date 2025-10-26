# Azure Advisor Reports - Template System Guide

## Overview

This guide documents the enhanced template system for the Azure Advisor Reports Platform. The templates have been redesigned to provide enterprise-level, visually appealing reports with real data visualizations using Chart.js.

**Version:** 2.0 Enhanced
**Last Updated:** October 2025
**Author:** Azure Advisor Reports Team

---

## Table of Contents

1. [Template Architecture](#template-architecture)
2. [Available Templates](#available-templates)
3. [Design System](#design-system)
4. [Data Requirements](#data-requirements)
5. [Visualization Components](#visualization-components)
6. [Customization Guide](#customization-guide)
7. [Best Practices](#best-practices)

---

## Template Architecture

### Base Template System

All report templates extend from `base.html`, which provides:

- **Professional Azure branding** - Microsoft Azure color scheme and design language
- **Responsive layout** - Adapts to different screen sizes and PDF generation
- **Common components** - Headers, footers, metric cards, tables
- **Chart.js integration** - Data visualization library loaded via CDN
- **Print-friendly styles** - Optimized for PDF generation with WeasyPrint

### Template Hierarchy

```
base.html (Base template with Azure design system)
├── executive_enhanced.html (Executive summary for leadership)
├── cost_enhanced.html (Cost optimization analysis)
├── security_enhanced.html (Security assessment)
├── operations.html (Operational excellence - existing)
└── detailed.html (Detailed technical report - existing)
```

---

## Available Templates

### 1. Base Template (`base.html`)

**Location:** `azure_advisor_reports/templates/reports/base.html`

**Purpose:** Foundation template with Azure design system

**Features:**
- Azure-branded color palette with CSS variables
- Professional cover page
- Report header with client metadata
- Responsive metrics grid
- Data tables with hover effects
- Chart containers
- Info boxes (success, warning, danger, info)
- Print-optimized styles
- Footer with disclaimers

**CSS Variables:**
```css
--azure-blue: #0078D4
--success-green: #107C10
--warning-orange: #FF8C00
--danger-red: #D13438
--gray-* (50-900 scale)
--gradient-azure, --gradient-success, etc.
```

---

### 2. Executive Report Enhanced (`executive_enhanced.html`)

**Target Audience:** C-Suite, Board Members, Senior Leadership

**Generator:** `ExecutiveReportGenerator` → `reports/executive_enhanced.html`

**Sections:**

1. **Executive Summary Dashboard**
   - Total recommendations
   - Annual savings potential
   - High priority items
   - Categories impacted

2. **Key Insights**
   - Strategic overview in business language
   - Financial impact summary

3. **Recommendations Distribution**
   - Category distribution chart (doughnut)
   - Impact distribution chart (doughnut)
   - Category summary table with percentages

4. **Quick Wins**
   - Top 5-10 high-value opportunities
   - Impact and savings for each
   - Total quick wins potential

5. **Top 10 Recommendations**
   - Sorted by business value
   - Category and impact indicators
   - Potential savings displayed

6. **Strategic Implementation Roadmap**
   - Phase 1: Immediate (Week 1-2)
   - Phase 2: Short-term (Month 1)
   - Phase 3: Long-term (Quarter 1)

7. **Financial Impact Analysis**
   - Total annual savings
   - Implementation time estimates
   - ROI projections
   - Business value breakdown

8. **Executive Action Items**
   - Clear next steps for leadership
   - Governance recommendations

**Data Requirements:**
```python
{
    'summary_metrics': {
        'total_recommendations': int,
        'total_savings': Decimal,
        'monthly_savings': Decimal,
        'high_priority_count': int,
        'categories_affected': int,
    },
    'quick_wins': QuerySet,  # High impact + high savings
    'category_chart_data': [
        {
            'category': str,
            'count': int,
            'percentage': float,
            'color': str  # Hex color
        },
        ...
    ],
    'top_10_recommendations': QuerySet,
    'high_impact_count': int,
    'medium_impact_count': int,
    'low_impact_count': int,
}
```

**Visualizations:**
- Category Distribution Doughnut Chart
- Impact Distribution Doughnut Chart

**Page Length:** 5-7 pages (PDF)

---

### 3. Cost Optimization Report Enhanced (`cost_enhanced.html`)

**Target Audience:** CFO, Finance Teams, Cost Managers, Procurement

**Generator:** `CostOptimizationReportGenerator` → `reports/cost_enhanced.html`

**Sections:**

1. **Cost Optimization Executive Summary**
   - Total annual/monthly savings
   - Number of cost recommendations
   - High-value opportunities count
   - Payback period

2. **Financial Impact Summary**
   - Detailed ROI analysis
   - Implementation cost estimates
   - Net benefit calculations
   - 3-year projection

3. **Savings Distribution Analysis**
   - Savings by resource type (bar chart)
   - Savings by subscription (doughnut chart)

4. **Top Cost-Saving Opportunities**
   - Top 10 recommendations by savings
   - Resource details
   - Impact level
   - Annual and monthly savings

5. **Quick Wins**
   - Low effort, high impact optimizations
   - Immediate implementation candidates

6. **Savings Breakdown by Resource Type**
   - Detailed table with counts
   - Annual and monthly savings
   - Percentage of total

7. **Long-term Strategic Opportunities**
   - Complex optimizations
   - Architectural changes
   - Higher effort but substantial value

8. **Implementation Roadmap**
   - Phase 1: Immediate (Week 1-2) - Quick wins
   - Phase 2: Short-term (Week 3-4) - Reserved instances, storage
   - Phase 3: Long-term (Month 2-3) - Architecture changes

9. **Next Steps & Governance**
   - Action plan
   - Cost governance best practices
   - FinOps recommendations

**Data Requirements:**
```python
{
    'total_annual_savings': Decimal,
    'total_monthly_savings': Decimal,
    'cost_recommendations': QuerySet,
    'quick_wins': QuerySet,
    'quick_wins_total': Decimal,
    'quick_wins_monthly': Decimal,
    'long_term_opportunities': QuerySet,
    'long_term_total': Decimal,
    'cost_by_resource_type': [
        {
            'resource_type': str,
            'count': int,
            'total_savings': Decimal,
            'monthly_savings': Decimal,
            'percentage': float
        },
        ...
    ],
    'cost_by_subscription': QuerySet,
    'top_cost_savers': QuerySet,
    'top_cost_savers_total': Decimal,
    'roi_analysis': {
        'estimated_implementation_cost': Decimal,
        'estimated_annual_savings': Decimal,
        'net_benefit': Decimal,
        'roi_percentage': float,
        'payback_months': float,
    },
}
```

**Visualizations:**
- Savings by Resource Type Bar Chart
- Savings by Subscription Doughnut Chart

**Page Length:** 8-12 pages (PDF)

---

### 4. Security Assessment Report Enhanced (`security_enhanced.html`)

**Target Audience:** CISO, Security Teams, Compliance Officers

**Generator:** `SecurityReportGenerator` → `reports/security_enhanced.html`

**Sections:**

1. **Security Posture Overview**
   - Security score gauge (0-100)
   - Visual score indicator
   - Remediation timeline metrics

2. **Security Metrics Dashboard**
   - Critical issues count
   - High priority count
   - Medium priority count
   - Total security findings
   - Severity indicators (visual bars)

3. **Threat Landscape Overview**
   - Security posture summary
   - Severity distribution chart
   - Findings by resource type chart

4. **Critical Security Issues**
   - Immediate action required (24 hours)
   - Detailed table with risk levels
   - Executive escalation recommended

5. **High Priority Security Issues**
   - Address within 1 week
   - Risk level indicators

6. **Security Findings by Subscription**
   - Critical/High/Medium breakdown
   - Visual risk distribution bars

7. **Compliance & Regulatory Framework**
   - ISO 27001, NIST CSF, CIS Controls
   - SOC 2, HIPAA, PCI DSS alignment
   - Compliance badges

8. **Security Remediation Roadmap**
   - Phase 1: Critical Response (24 hours)
   - Phase 2: Short-term Hardening (Week 1)
   - Phase 3: Continuous Improvement (Month 1+)

9. **Security Best Practices**
   - Continuous monitoring
   - Defense in depth
   - Zero trust model
   - Security culture

10. **Immediate Action Items**
    - Leadership actions
    - Emergency response procedures

**Data Requirements:**
```python
{
    'security_score': int,  # 0-100
    'total_security_findings': int,
    'critical_count': int,
    'high_count': int,
    'medium_count': int,
    'critical_issues': QuerySet,
    'high_priority_issues': QuerySet,
    'medium_priority': QuerySet,
    'security_recommendations': QuerySet,
    'security_by_subscription': [
        {
            'subscription_name': str,
            'critical_count': int,
            'high_count': int,
            'medium_count': int,
            'total_count': int,
        },
        ...
    ],
    'security_by_resource_type': [
        {
            'resource_type': str,
            'count': int,
            'critical_count': int,
        },
        ...
    ],
}
```

**Visualizations:**
- Security Score Gauge (CSS-based)
- Severity Distribution Doughnut Chart
- Findings by Resource Type Bar Chart
- Risk Distribution Bars (inline CSS)

**Special Features:**
- CSS-based security score gauge
- Risk indicator badges
- Compliance framework badges
- Severity visualization bars

**Page Length:** 10-15 pages (PDF)

---

## Design System

### Color Palette

**Primary Azure Colors:**
```css
--azure-blue: #0078D4        /* Primary brand color */
--azure-blue-dark: #005A9E   /* Darker variant */
--azure-cyan: #00BCF2        /* Secondary accent */
--azure-purple: #8661C5      /* Tertiary accent */
```

**Semantic Colors:**
```css
--success-green: #107C10     /* Positive outcomes */
--warning-orange: #FF8C00    /* Caution required */
--danger-red: #D13438        /* Critical issues */
```

**Impact Colors:**
```css
High Impact: #D13438 (Red)
Medium Impact: #FFB900 (Yellow)
Low Impact: #107C10 (Green)
```

**Category Colors:**
```css
Cost: #107C10 (Green)
Security: #FF8C00 (Orange)
Reliability: #00BCF2 (Cyan)
Operational Excellence: #8661C5 (Purple)
Performance: #9966FF (Light Purple)
```

### Typography

**Font Family:**
```css
--font-family-base: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', 'Helvetica Neue', sans-serif;
--font-family-mono: 'Consolas', 'Monaco', 'Courier New', monospace;
```

**Font Scale:**
```css
--text-xs: 0.75rem    /* 12px */
--text-sm: 0.875rem   /* 14px */
--text-base: 1rem     /* 16px */
--text-lg: 1.125rem   /* 18px */
--text-xl: 1.25rem    /* 20px */
--text-2xl: 1.5rem    /* 24px */
--text-3xl: 1.875rem  /* 30px */
--text-4xl: 2.25rem   /* 36px */
--text-5xl: 3rem      /* 48px */
--text-6xl: 3.75rem   /* 60px */
```

### Component Classes

**Metric Cards:**
```html
<div class="metric-card [metric-cost|metric-security|metric-critical]">
    <div class="metric-icon">💰</div>
    <div class="metric-label">Label Text</div>
    <div class="metric-value">$1,234</div>
    <div class="metric-subtitle">Subtitle text</div>
</div>
```

**Info Boxes:**
```html
<div class="[info-box|success-box|warning-box|danger-box]">
    <div class="info-box-icon">🎯</div>
    <h3>Box Title</h3>
    <p>Box content...</p>
</div>
```

**Badges:**
```html
<span class="badge badge-[high|medium|low]">HIGH</span>
<span class="badge badge-[cost|security|reliability|operational_excellence|performance]">Cost</span>
```

**Data Tables:**
```html
<div class="table-container">
    <table class="data-table">
        <thead>
            <tr>
                <th>Column 1</th>
                <th>Column 2</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Data 1</td>
                <td>Data 2</td>
            </tr>
        </tbody>
    </table>
</div>
```

---

## Data Requirements

### Common Data (All Templates)

All templates receive base context from `BaseReportGenerator.get_base_context()`:

```python
{
    'report': Report,  # Report model instance
    'client': Client,  # Client model instance
    'recommendations': QuerySet,  # All recommendations
    'generated_date': datetime,
    'total_recommendations': int,
    'report_type_display': str,
    'category_distribution': list,
    'impact_distribution': dict,
    'total_savings': Decimal,
    'monthly_savings': Decimal,
    'top_recommendations': QuerySet,
    'subscriptions': list,
    'high_impact_count': int,
    'medium_impact_count': int,
    'low_impact_count': int,
}
```

### Template-Specific Data

Each generator adds specific data via `get_context_data()`. See individual template sections above for details.

---

## Visualization Components

### Chart.js Integration

**Library Version:** Chart.js 4.4.0 (loaded via CDN in base template)

**Chart Types Used:**

1. **Doughnut Charts** - Category distribution, severity distribution
2. **Bar Charts** - Savings by resource type, findings by resource
3. **Horizontal Bar Charts** - Resource-based comparisons

**Chart Configuration:**

```javascript
// Standard Azure color palette
const azureColors = {
    cost: '#107C10',
    security: '#FF8C00',
    reliability: '#00BCF2',
    operational_excellence: '#8661C5',
    performance: '#9966FF',
    high: '#D13438',
    medium: '#FFB900',
    low: '#107C10'
};

// Chart defaults
Chart.defaults.font.family = "'Segoe UI', sans-serif";
Chart.defaults.font.size = 12;

// Example: Category distribution doughnut chart
new Chart(ctx, {
    type: 'doughnut',
    data: {
        labels: ['Cost', 'Security', 'Reliability', 'OpEx', 'Performance'],
        datasets: [{
            data: [10, 15, 5, 8, 12],
            backgroundColor: [
                azureColors.cost,
                azureColors.security,
                azureColors.reliability,
                azureColors.operational_excellence,
                azureColors.performance
            ],
            borderWidth: 2,
            borderColor: '#ffffff'
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    padding: 15,
                    font: { size: 13, weight: '600' },
                    usePointStyle: true
                }
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                padding: 12,
                callbacks: {
                    label: function(context) {
                        return context.label + ': ' + context.parsed + ' items';
                    }
                }
            }
        }
    }
});
```

**Chart Container:**
```html
<div class="chart-container">
    <div class="chart-header">
        <h3 class="chart-title">Chart Title</h3>
        <p class="chart-subtitle">Chart subtitle</p>
    </div>
    <div class="chart-wrapper [chart-large|chart-small]">
        <canvas id="myChart"></canvas>
    </div>
</div>
```

---

## Customization Guide

### Adding a New Template

1. **Create HTML Template:**
   ```html
   {% extends 'reports/base.html' %}

   {% block title %}My Custom Report - {{ client.company_name }}{% endblock %}

   {% block content %}
       <!-- Your custom content here -->
   {% endblock %}
   ```

2. **Create Generator:**
   ```python
   from .base import BaseReportGenerator

   class CustomReportGenerator(BaseReportGenerator):
       def get_template_name(self):
           return 'reports/custom_report.html'

       def get_context_data(self):
           return {
               'custom_data': self.calculate_custom_metrics(),
           }
   ```

3. **Register Generator:**
   ```python
   # In generators/__init__.py
   from .custom import CustomReportGenerator

   REPORT_GENERATORS = {
       'custom': CustomReportGenerator,
   }
   ```

### Customizing Colors

Override CSS variables in template:

```html
{% block extra_css %}
<style>
    :root {
        --azure-blue: #YOUR_COLOR;
        --success-green: #YOUR_COLOR;
    }
</style>
{% endblock %}
```

### Adding Custom Charts

```html
{% block content %}
    <div class="chart-container">
        <div class="chart-wrapper">
            <canvas id="customChart"></canvas>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const ctx = document.getElementById('customChart');
            new Chart(ctx, {
                // Your chart configuration
            });
        });
    </script>
{% endblock %}
```

### Custom Metric Cards

```html
<div class="metrics-grid">
    <div class="metric-card" style="border-top-color: #YOUR_COLOR;">
        <div class="metric-icon">🎯</div>
        <div class="metric-label">Custom Metric</div>
        <div class="metric-value">{{ custom_value }}</div>
        <div class="metric-subtitle">Description</div>
    </div>
</div>
```

---

## Best Practices

### Template Development

1. **Always extend base.html** - Maintains consistent branding and structure
2. **Use semantic HTML** - Improves accessibility and PDF generation
3. **Leverage CSS variables** - Easy theming and maintenance
4. **Include descriptive titles** - Helps with navigation and PDF bookmarks
5. **Add print styles** - Consider page breaks and margins

### Data Handling

1. **Use real data only** - No hardcoded values or mock data
2. **Handle empty states** - Use `{% empty %}` blocks in loops
3. **Format numbers consistently** - Use `|floatformat:0` for currencies
4. **Provide context** - Include subtitles and descriptions for all metrics
5. **Validate data in generator** - Ensure data types and calculations are correct

### Performance

1. **Limit chart data points** - Use top 10/15 items for readability
2. **Optimize queries** - Use `select_related()` and `prefetch_related()`
3. **Lazy load charts** - Initialize on `DOMContentLoaded`
4. **Minimize inline styles** - Use CSS classes instead
5. **Test PDF generation** - Ensure all elements render correctly

### Accessibility

1. **Use semantic HTML tags** - `<header>`, `<section>`, `<table>`
2. **Provide alt text** - For any images or icons
3. **Ensure color contrast** - WCAG AA minimum (4.5:1)
4. **Use ARIA labels** - For interactive elements
5. **Test with screen readers** - Validate accessibility

### PDF Generation

1. **Use page-break-after** - Control pagination
2. **Avoid page-break-inside** - Keep sections together
3. **Set appropriate margins** - Consider @page rules
4. **Test font rendering** - Ensure fonts are embedded
5. **Optimize file size** - Compress images, minimize inline styles

---

## Troubleshooting

### Charts Not Rendering

**Problem:** Charts appear blank or don't render

**Solutions:**
- Verify Chart.js CDN is loading (check browser console)
- Ensure canvas element has proper ID
- Check JavaScript console for errors
- Verify data format (arrays, not querysets in JSON context)
- Use `|safe` filter for JSON data in templates

### PDF Generation Issues

**Problem:** PDF looks different from HTML

**Solutions:**
- Check WeasyPrint logs for rendering errors
- Ensure all fonts are available
- Use print media query styles
- Avoid `position: fixed` elements
- Test with `print-color-adjust: exact`

### Data Not Displaying

**Problem:** Template variables show as empty

**Solutions:**
- Verify generator returns data in `get_context_data()`
- Check variable names match template usage
- Use Django template debug mode
- Print context in generator for debugging
- Ensure QuerySets are evaluated properly

### Styling Issues

**Problem:** CSS not applying correctly

**Solutions:**
- Check CSS specificity
- Verify class names match
- Inspect element in browser DevTools
- Clear browser cache
- Check for CSS variable browser support

---

## Migration from Old Templates

### Steps to Migrate

1. **Backup existing templates**
   ```bash
   cp -r templates/reports templates/reports_backup
   ```

2. **Update generator template names**
   ```python
   # Old
   return 'reports/executive.html'

   # New
   return 'reports/executive_enhanced.html'
   ```

3. **Test each report type**
   - Generate reports with real data
   - Compare HTML and PDF output
   - Verify all sections render correctly

4. **Update documentation**
   - Document any custom changes
   - Update user guides
   - Train support team

### Compatibility Notes

- Old templates remain functional (backward compatible)
- New templates use same data structures
- Enhanced templates are opt-in (update generator to use)
- Can run old and new templates simultaneously

---

## Support & Resources

### Documentation

- **Django Templates:** https://docs.djangoproject.com/en/stable/topics/templates/
- **Chart.js:** https://www.chartjs.org/docs/latest/
- **WeasyPrint:** https://doc.courtbouillon.org/weasyprint/stable/
- **Azure Design System:** https://developer.microsoft.com/en-us/fluentui

### Getting Help

For issues or questions:

1. Check this guide first
2. Review generator code comments
3. Check browser console for JavaScript errors
4. Contact development team
5. Submit GitHub issue with details

---

## Changelog

### Version 2.0 Enhanced (October 2025)

**Added:**
- Professional executive summary template with strategic roadmap
- Enhanced cost report with ROI analysis and savings breakdown
- Security assessment with compliance framework alignment
- Chart.js visualizations (doughnut, bar, horizontal bar)
- Security score gauge (CSS-based)
- Compliance framework badges
- Enhanced metric cards with icons
- Professional color coding system
- Print-optimized styles

**Improved:**
- Base template design system
- Typography and spacing
- Table styling with hover effects
- Info box components
- Data visualization standards
- PDF generation compatibility

**Fixed:**
- Responsive layout issues
- Print page breaks
- Color contrast for accessibility
- Chart rendering in PDF

---

## Appendix

### Template File Locations

```
azure_advisor_reports/
├── templates/
│   └── reports/
│       ├── base.html (v2.0)
│       ├── executive_enhanced.html (NEW)
│       ├── cost_enhanced.html (NEW)
│       ├── security_enhanced.html (NEW)
│       ├── executive.html (legacy)
│       ├── cost.html (legacy)
│       ├── security.html (legacy)
│       ├── operations.html
│       └── detailed.html
└── apps/
    └── reports/
        └── generators/
            ├── base.py
            ├── executive.py (updated)
            ├── cost.py (updated)
            ├── security.py (updated)
            ├── operations.py
            └── detailed.py
```

### Sample Context Data

**Executive Report:**
```python
{
    'summary_metrics': {
        'total_recommendations': 42,
        'total_savings': Decimal('125000.00'),
        'monthly_savings': Decimal('10416.67'),
        'high_priority_count': 8,
        'categories_affected': 4,
    },
    'quick_wins': <QuerySet [<Recommendation: ...>, ...]>,  # 5 items
    'category_chart_data': [
        {'category': 'Cost', 'count': 15, 'percentage': 35.7, 'color': '#107C10'},
        {'category': 'Security', 'count': 12, 'percentage': 28.6, 'color': '#FF8C00'},
        {'category': 'Reliability', 'count': 10, 'percentage': 23.8, 'color': '#00BCF2'},
        {'category': 'Operational Excellence', 'count': 5, 'percentage': 11.9, 'color': '#8661C5'},
    ],
    'top_10_recommendations': <QuerySet [...]>,
    'high_impact_count': 8,
    'medium_impact_count': 20,
    'low_impact_count': 14,
}
```

---

**End of Guide**

For the latest version of this guide, visit the project repository or contact the development team.
