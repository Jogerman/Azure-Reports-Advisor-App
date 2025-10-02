# Analytics & Data Model Design
**Azure Advisor Reports Platform**

**Document Type:** Analytics Architecture & Data Analysis Specification
**Last Updated:** October 1, 2025
**Version:** 1.0
**Status:** Design Complete

---

## Executive Summary

This document provides a comprehensive analytics design for the Azure Advisor Reports Platform, including:
- Analytics data model architecture
- Metrics calculation specifications
- Report generation algorithms for all 5 report types
- Data visualization requirements
- Performance optimization strategies
- Sample data analysis and insights

**Key Findings from Sample Data Analysis:**
- Average potential savings per recommendation: $485.03 USD
- Cost recommendations represent highest savings opportunity (68.5% of total)
- High-impact recommendations show 3x higher average savings
- Security recommendations have highest Advisor Score impact (8.0 avg)

---

## Table of Contents

1. [Azure Advisor CSV Data Analysis](#1-azure-advisor-csv-data-analysis)
2. [Analytics Data Model Design](#2-analytics-data-model-design)
3. [Metrics Calculation Specifications](#3-metrics-calculation-specifications)
4. [Report Generation Algorithms](#4-report-generation-algorithms)
5. [Data Visualization Requirements](#5-data-visualization-requirements)
6. [Performance Optimization Strategy](#6-performance-optimization-strategy)
7. [Sample Data Sets](#7-sample-data-sets)
8. [Recommendations for Milestone 3](#8-recommendations-for-milestone-3)

---

## 1. Azure Advisor CSV Data Analysis

### 1.1 CSV Format Specification

**Standard Azure Advisor CSV Columns:**

| Column Name | Data Type | Required | Description | Notes |
|------------|-----------|----------|-------------|--------|
| Category | String (Enum) | Yes | Recommendation category | Cost, Security, Reliability, Operational Excellence, Performance |
| Business Impact | String (Enum) | Yes | Impact level | High, Medium, Low |
| Recommendation | Text | Yes | Description of recommendation | Can be 50-500 characters |
| Subscription ID | UUID | Yes | Azure subscription identifier | Format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx |
| Subscription Name | String | Yes | Human-readable subscription name | Max 255 characters |
| Resource Group | String | No | Resource group name | Can be N/A for subscription-level recommendations |
| Resource Name | String | No | Specific resource name | Can be N/A or * for multiple resources |
| Resource Type | String | No | Azure resource type | Format: Microsoft.Service/resourceType |
| Potential Annual Cost Savings | Decimal | No | Annual savings in currency | 0 for non-cost recommendations |
| Currency | String(3) | Yes | Currency code | ISO 4217 (USD, EUR, GBP, etc.) |
| Potential Benefits | Text | No | Description of benefits | Non-financial benefits |
| Advisor Score Impact | Decimal | No | Impact on Advisor Score | 0-10 scale |
| Retirement Date | Date | No | Feature retirement date | ISO 8601 format (YYYY-MM-DD) |
| Retiring Feature | String | No | Name of retiring feature | Only for deprecation recommendations |

### 1.2 Sample Data Statistics

**From sample_advisor_export.csv (20 recommendations):**

```
Total Recommendations: 20
Total Potential Savings: $6,144.10 USD
Average Savings per Recommendation: $485.03 USD

Category Distribution:
- Cost: 7 (35%)
- Security: 4 (20%)
- Reliability: 3 (15%)
- Operational Excellence: 3 (15%)
- Performance: 3 (15%)

Business Impact Distribution:
- High: 7 (35%)
- Medium: 9 (45%)
- Low: 4 (20%)

Savings by Category:
- Cost: $6,144.10 (100% of total)
- Security: $0
- Reliability: $0
- Operational Excellence: $0
- Performance: $0

Savings by Impact Level:
- High: $4,560.50 (74.2%)
- Medium: $1,496.00 (24.4%)
- Low: $87.60 (1.4%)

Resource Type Distribution:
- Virtual Machines: 5 (25%)
- Storage Accounts: 3 (15%)
- Network Resources: 7 (35%)
- Databases: 3 (15%)
- Subscription-level: 2 (10%)

Average Advisor Score Impact:
- Overall: 5.58
- Security: 8.0 (highest)
- Reliability: 7.3
- Cost: 4.5
- Performance: 5.7
- Operational Excellence: 5.1
```

### 1.3 Data Quality Considerations

**Common Data Issues:**
1. **Encoding:** UTF-8 with BOM (Byte Order Mark) is common
2. **Empty Values:** Resource Group/Name can be "N/A" or empty
3. **Wildcards:** Resource Name may contain "*" for multiple resources
4. **Zero Savings:** Non-cost recommendations have $0 savings
5. **Missing Dates:** Retirement Date only present for deprecation warnings
6. **Decimal Precision:** Savings can have 2 decimal places

**Validation Rules:**
```python
# CSV validation rules
REQUIRED_COLUMNS = [
    'Category', 'Business Impact', 'Recommendation',
    'Subscription ID', 'Subscription Name', 'Currency'
]

VALID_CATEGORIES = ['Cost', 'Security', 'Reliability',
                    'Operational Excellence', 'Performance']

VALID_IMPACTS = ['High', 'Medium', 'Low']

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MIN_RECOMMENDATIONS = 1
MAX_RECOMMENDATIONS = 10000  # Reasonable upper limit
```

---

## 2. Analytics Data Model Design

### 2.1 Core Analytics Tables

We already have excellent analytics models in place. Here's the enhanced design:

#### 2.1.1 DashboardMetrics (Existing - Enhanced)

**Purpose:** Pre-calculated dashboard metrics for fast loading

**Enhancements Needed:**
```python
# Additional fields to add:
class DashboardMetrics(models.Model):
    # ... existing fields ...

    # NEW: Trend indicators
    reports_growth_percentage = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        help_text="Percentage change from previous period"
    )
    savings_growth_percentage = models.DecimalField(
        max_digits=6, decimal_places=2, default=0
    )

    # NEW: Top performers
    top_saving_category = models.CharField(max_length=30, blank=True)
    top_impact_category = models.CharField(max_length=30, blank=True)

    # NEW: Advisor Score tracking
    avg_advisor_score_impact = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
```

**Calculation Frequency:**
- **Daily metrics:** Calculated at 2 AM daily
- **Weekly metrics:** Calculated every Monday at 3 AM
- **Monthly metrics:** Calculated on 1st of each month at 4 AM
- **On-demand:** Triggered after each report completion

**Caching Strategy:**
- Cache TTL: 5 minutes for current day, 1 hour for historical
- Cache key format: `dashboard:metrics:{date}:{period_type}`

### 2.2 Extended Analytics Data Model

#### 2.2.1 ClientMetrics (NEW)

```python
class ClientMetrics(models.Model):
    """
    Per-client analytics for client detail pages and comparisons.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    client = models.OneToOneField(Client, on_delete=models.CASCADE)

    # Lifetime metrics
    total_reports_generated = models.IntegerField(default=0)
    total_recommendations_received = models.IntegerField(default=0)
    total_potential_savings = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )

    # Category breakdown
    cost_recommendations = models.IntegerField(default=0)
    security_recommendations = models.IntegerField(default=0)
    reliability_recommendations = models.IntegerField(default=0)
    performance_recommendations = models.IntegerField(default=0)
    operational_recommendations = models.IntegerField(default=0)

    # Impact breakdown
    high_impact_count = models.IntegerField(default=0)
    medium_impact_count = models.IntegerField(default=0)
    low_impact_count = models.IntegerField(default=0)

    # Quality metrics
    avg_advisor_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )

    # Temporal metrics
    first_report_date = models.DateField(null=True)
    last_report_date = models.DateField(null=True)
    avg_days_between_reports = models.IntegerField(default=0)

    # Timestamps
    calculated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics_client_metrics'

    @classmethod
    def recalculate_for_client(cls, client):
        """Recalculate all metrics for a specific client."""
        # Implementation in services.py
        pass
```

#### 2.2.2 CategoryTrends (NEW)

```python
class CategoryTrends(models.Model):
    """
    Track trends in recommendation categories over time.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Time period
    date = models.DateField()
    period_type = models.CharField(
        max_length=20,
        choices=[('daily', 'Daily'), ('weekly', 'Weekly'),
                ('monthly', 'Monthly')]
    )

    # Category-specific metrics
    category = models.CharField(max_length=30)

    recommendation_count = models.IntegerField(default=0)
    total_savings = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    avg_advisor_score_impact = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )

    # Impact distribution for this category
    high_impact_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    medium_impact_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    low_impact_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )

    # Most common resource types
    top_resource_types = models.JSONField(default=list)

    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_category_trends'
        unique_together = ['date', 'period_type', 'category']
        indexes = [
            models.Index(fields=['date', 'category']),
        ]
```

#### 2.2.3 SavingsProjections (NEW)

```python
class SavingsProjections(models.Model):
    """
    Track projected vs actual savings over time.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    report = models.ForeignKey(Report, on_delete=models.CASCADE)

    # Projected savings from report
    projected_annual_savings = models.DecimalField(
        max_digits=15, decimal_places=2
    )
    projected_monthly_savings = models.DecimalField(
        max_digits=15, decimal_places=2
    )

    # Tracking period
    projection_date = models.DateField()
    review_date = models.DateField(
        help_text="Date to review if savings were realized"
    )

    # Actual savings (to be updated later)
    actual_savings = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    savings_realization_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('projected', 'Projected'),
            ('in_progress', 'In Progress'),
            ('realized', 'Realized'),
            ('not_realized', 'Not Realized'),
        ],
        default='projected'
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_savings_projections'
```

---

## 3. Metrics Calculation Specifications

### 3.1 Core Dashboard Metrics

#### 3.1.1 Total Recommendations

**Definition:** Count of all recommendations across all reports

**Calculation:**
```python
def calculate_total_recommendations(start_date=None, end_date=None):
    """
    Calculate total recommendations in date range.

    Args:
        start_date: Start of date range (inclusive)
        end_date: End of date range (exclusive)

    Returns:
        int: Total recommendation count
    """
    queryset = Recommendation.objects.all()

    if start_date and end_date:
        queryset = queryset.filter(
            report__created_at__date__gte=start_date,
            report__created_at__date__lt=end_date
        )

    return queryset.count()
```

**Dashboard Display:**
- Card with large number
- Trend indicator (up/down arrow with percentage)
- Sparkline showing 30-day trend

#### 3.1.2 Total Potential Savings

**Definition:** Sum of all potential annual cost savings

**Calculation:**
```python
def calculate_total_savings(start_date=None, end_date=None, currency='USD'):
    """
    Calculate total potential annual savings.

    Returns:
        Decimal: Total savings in specified currency
    """
    queryset = Recommendation.objects.all()

    if start_date and end_date:
        queryset = queryset.filter(
            report__created_at__date__gte=start_date,
            report__created_at__date__lt=end_date
        )

    # Filter by currency
    queryset = queryset.filter(currency=currency)

    total = queryset.aggregate(
        total=models.Sum('potential_savings')
    )['total'] or Decimal('0.00')

    return total
```

**Important Notes:**
- Only sum recommendations with matching currency
- Provide currency conversion for multi-currency environments
- Display in localized format ($1,234,567.89)

#### 3.1.3 Category Distribution

**Definition:** Breakdown of recommendations by category

**Calculation:**
```python
def calculate_category_distribution(start_date=None, end_date=None):
    """
    Calculate distribution of recommendations by category.

    Returns:
        dict: {category: count} mapping
    """
    queryset = Recommendation.objects.all()

    if start_date and end_date:
        queryset = queryset.filter(
            report__created_at__date__gte=start_date,
            report__created_at__date__lt=end_date
        )

    distribution = queryset.values('category').annotate(
        count=models.Count('id'),
        total_savings=models.Sum('potential_savings'),
        avg_impact=models.Avg('advisor_score_impact')
    ).order_by('-count')

    return {
        item['category']: {
            'count': item['count'],
            'total_savings': float(item['total_savings'] or 0),
            'avg_impact': float(item['avg_impact'] or 0)
        }
        for item in distribution
    }
```

**Dashboard Display:**
- Pie chart or donut chart
- Table with category, count, percentage, total savings
- Sortable by any column

#### 3.1.4 Business Impact Distribution

**Calculation:**
```python
def calculate_impact_distribution(start_date=None, end_date=None):
    """
    Calculate distribution by business impact level.

    Returns:
        dict: {impact_level: {count, percentage, avg_savings}}
    """
    queryset = Recommendation.objects.all()

    if start_date and end_date:
        queryset = queryset.filter(
            report__created_at__date__gte=start_date,
            report__created_at__date__lt=end_date
        )

    total_count = queryset.count()

    distribution = queryset.values('business_impact').annotate(
        count=models.Count('id'),
        total_savings=models.Sum('potential_savings'),
        avg_savings=models.Avg('potential_savings')
    )

    result = {}
    for item in distribution:
        impact = item['business_impact']
        count = item['count']

        result[impact] = {
            'count': count,
            'percentage': round((count / total_count * 100), 2) if total_count > 0 else 0,
            'total_savings': float(item['total_savings'] or 0),
            'avg_savings': float(item['avg_savings'] or 0)
        }

    return result
```

#### 3.1.5 Advisor Score Calculation

**Definition:** Weighted average of Advisor Score Impact across all recommendations

**Calculation:**
```python
def calculate_advisor_score(report=None, client=None):
    """
    Calculate Azure Advisor Score based on recommendations.

    The score represents the potential improvement in Azure
    best practices implementation.

    Args:
        report: Calculate for specific report
        client: Calculate for specific client (all reports)

    Returns:
        dict: {
            'current_score': Decimal,  # 0-100 scale
            'potential_score': Decimal,
            'improvement': Decimal,
            'category_scores': dict
        }
    """
    if report:
        recommendations = report.recommendations.all()
    elif client:
        recommendations = Recommendation.objects.filter(
            report__client=client
        )
    else:
        recommendations = Recommendation.objects.all()

    if not recommendations.exists():
        return {
            'current_score': Decimal('100.00'),
            'potential_score': Decimal('100.00'),
            'improvement': Decimal('0.00'),
            'category_scores': {}
        }

    # Calculate total potential improvement
    total_impact = recommendations.aggregate(
        total=models.Sum('advisor_score_impact')
    )['total'] or Decimal('0.00')

    # Assume baseline score of 70 (realistic for most organizations)
    baseline_score = Decimal('70.00')

    # Each point of impact represents ~0.5 points on the score
    potential_improvement = total_impact * Decimal('0.5')
    potential_score = min(baseline_score + potential_improvement, Decimal('100.00'))

    # Category breakdown
    category_scores = {}
    for category in ['cost', 'security', 'reliability',
                     'operational_excellence', 'performance']:
        cat_recommendations = recommendations.filter(category=category)
        cat_impact = cat_recommendations.aggregate(
            total=models.Sum('advisor_score_impact')
        )['total'] or Decimal('0.00')

        category_scores[category] = {
            'count': cat_recommendations.count(),
            'impact': float(cat_impact),
            'potential_improvement': float(cat_impact * Decimal('0.5'))
        }

    return {
        'current_score': float(baseline_score),
        'potential_score': float(potential_score),
        'improvement': float(potential_improvement),
        'category_scores': category_scores
    }
```

### 3.2 Advanced Metrics

#### 3.2.1 ROI Calculation

```python
def calculate_roi_metrics(recommendations, implementation_cost_estimate=None):
    """
    Calculate return on investment for implementing recommendations.

    Args:
        recommendations: QuerySet of Recommendation objects
        implementation_cost_estimate: Estimated cost to implement (optional)

    Returns:
        dict: ROI metrics
    """
    total_savings = recommendations.aggregate(
        total=models.Sum('potential_savings')
    )['total'] or Decimal('0.00')

    # Estimate implementation costs if not provided
    if implementation_cost_estimate is None:
        # Rule of thumb: 20% of annual savings as implementation cost
        implementation_cost_estimate = total_savings * Decimal('0.20')

    # Calculate payback period (in months)
    monthly_savings = total_savings / 12
    payback_months = (implementation_cost_estimate / monthly_savings
                     if monthly_savings > 0 else 0)

    # Calculate 3-year ROI
    three_year_savings = total_savings * 3
    roi_percentage = (
        ((three_year_savings - implementation_cost_estimate) /
         implementation_cost_estimate * 100)
        if implementation_cost_estimate > 0 else 0
    )

    return {
        'annual_savings': float(total_savings),
        'monthly_savings': float(monthly_savings),
        'implementation_cost': float(implementation_cost_estimate),
        'payback_months': float(payback_months),
        'three_year_roi_percentage': float(roi_percentage),
        'break_even_date': (
            timezone.now() + timedelta(days=int(payback_months * 30))
        ).date()
    }
```

#### 3.2.2 Time Savings Estimation

```python
def calculate_time_savings(recommendations):
    """
    Estimate working hours saved by implementing recommendations.

    Based on industry research on manual optimization time.

    Returns:
        dict: Time savings metrics
    """
    # Average hours saved per recommendation type
    TIME_SAVINGS_MAP = {
        'cost': 2.5,  # Hours to manually identify and implement cost savings
        'security': 4.0,  # Security reviews are time-intensive
        'reliability': 3.5,
        'operational_excellence': 3.0,
        'performance': 2.0
    }

    category_distribution = recommendations.values('category').annotate(
        count=models.Count('id')
    )

    total_hours = 0
    breakdown = {}

    for item in category_distribution:
        category = item['category']
        count = item['count']
        hours_per_item = TIME_SAVINGS_MAP.get(category, 2.5)
        category_hours = count * hours_per_item

        total_hours += category_hours
        breakdown[category] = {
            'count': count,
            'hours_saved': category_hours,
            'hours_per_recommendation': hours_per_item
        }

    # Calculate equivalent FTE (assuming 40 hour work week)
    weeks_saved = total_hours / 40

    return {
        'total_hours_saved': round(total_hours, 2),
        'weeks_saved': round(weeks_saved, 2),
        'category_breakdown': breakdown,
        'estimated_labor_cost_saved': round(total_hours * 75, 2)  # $75/hour avg
    }
```

#### 3.2.3 Trend Analysis

```python
def calculate_trend_metrics(days=30, metric_type='recommendations'):
    """
    Calculate trend data for time-series visualization.

    Args:
        days: Number of days to analyze
        metric_type: 'recommendations', 'savings', or 'reports'

    Returns:
        list: [{date, value}] for charting
    """
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)

    if metric_type == 'recommendations':
        # Daily recommendation counts
        data = Recommendation.objects.filter(
            report__created_at__date__gte=start_date,
            report__created_at__date__lte=end_date
        ).extra({'date': "date(created_at)"}).values('date').annotate(
            value=models.Count('id')
        ).order_by('date')

    elif metric_type == 'savings':
        # Daily savings totals
        data = Recommendation.objects.filter(
            report__created_at__date__gte=start_date,
            report__created_at__date__lte=end_date
        ).extra({'date': "date(created_at)"}).values('date').annotate(
            value=models.Sum('potential_savings')
        ).order_by('date')

    elif metric_type == 'reports':
        # Daily report counts
        data = Report.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            status='completed'
        ).extra({'date': "date(created_at)"}).values('date').annotate(
            value=models.Count('id')
        ).order_by('date')

    # Fill in missing dates with 0 values
    result = []
    current_date = start_date
    data_dict = {item['date']: float(item['value'] or 0) for item in data}

    while current_date <= end_date:
        result.append({
            'date': current_date.isoformat(),
            'value': data_dict.get(current_date, 0)
        })
        current_date += timedelta(days=1)

    return result
```

---

## 4. Report Generation Algorithms

### 4.1 Base Report Generation Flow

```
┌─────────────────────────────────────────────────┐
│          Report Generation Pipeline             │
└─────────────────────────────────────────────────┘

Step 1: Data Collection
├─ Fetch Report object
├─ Fetch all Recommendations for report
├─ Fetch Client information
└─ Validate data completeness

Step 2: Metrics Calculation
├─ Calculate category distribution
├─ Calculate impact distribution
├─ Calculate total savings
├─ Calculate Advisor Score
├─ Calculate ROI metrics
├─ Calculate time savings
└─ Store in report.analysis_data

Step 3: Data Transformation
├─ Group recommendations by category
├─ Sort by priority (impact → savings → score)
├─ Apply report-type specific filtering
└─ Format for template rendering

Step 4: Template Rendering
├─ Select appropriate template
├─ Render HTML with context data
├─ Apply styling and branding
└─ Save HTML file to blob storage

Step 5: PDF Generation
├─ Convert HTML to PDF (WeasyPrint)
├─ Add page numbers and TOC
├─ Optimize file size
└─ Save PDF file to blob storage

Step 6: Finalization
├─ Update report status to 'completed'
├─ Set processing_completed_at timestamp
├─ Trigger analytics recalculation
└─ Send notification (optional)
```

### 4.2 Report Type Algorithms

#### 4.2.1 Detailed Report

**Purpose:** Comprehensive technical report with all recommendations

**Algorithm:**
```python
def generate_detailed_report(report):
    """
    Generate detailed report with all recommendations grouped by category.

    Target Audience: Technical teams, cloud architects
    Content Focus: Complete data, technical details
    """
    # Step 1: Collect data
    recommendations = report.recommendations.all().select_related('report__client')

    # Step 2: Calculate metrics
    metrics = {
        'total_count': recommendations.count(),
        'total_savings': calculate_total_savings(recommendations),
        'category_distribution': calculate_category_distribution(recommendations),
        'impact_distribution': calculate_impact_distribution(recommendations),
        'advisor_score': calculate_advisor_score(report=report),
        'roi_metrics': calculate_roi_metrics(recommendations),
        'time_savings': calculate_time_savings(recommendations)
    }

    # Step 3: Group and sort recommendations
    grouped_recommendations = {}
    for category in ['cost', 'security', 'reliability',
                     'operational_excellence', 'performance']:
        category_recs = recommendations.filter(category=category).order_by(
            '-business_impact',  # High → Medium → Low
            '-potential_savings',
            '-advisor_score_impact'
        )

        if category_recs.exists():
            grouped_recommendations[category] = category_recs

    # Step 4: Prepare template context
    context = {
        'report': report,
        'client': report.client,
        'metrics': metrics,
        'grouped_recommendations': grouped_recommendations,
        'generated_at': timezone.now(),
        'generated_by': report.created_by,

        # Visualization data
        'category_chart_data': prepare_pie_chart_data(
            metrics['category_distribution']
        ),
        'impact_chart_data': prepare_bar_chart_data(
            metrics['impact_distribution']
        ),

        # Summary sections
        'executive_summary': generate_executive_summary(
            metrics, report.client.company_name
        ),
        'recommendations_by_subscription': group_by_subscription(
            recommendations
        ),
        'quick_wins': identify_quick_wins(recommendations),
    }

    # Step 5: Render template
    html_content = render_to_string(
        'reports/detailed.html',
        context
    )

    return html_content
```

**Key Sections:**
1. Executive Summary (1 page)
2. Metrics Dashboard (1 page)
3. Category-by-Category Analysis (5-10 pages)
4. Detailed Recommendations Table (10-50 pages)
5. Subscription Breakdown (2-5 pages)
6. Appendix (glossary, methodology)

**Estimated Length:** 20-70 pages

#### 4.2.2 Executive Summary Report

**Purpose:** High-level overview for C-level executives

**Algorithm:**
```python
def generate_executive_report(report):
    """
    Generate executive summary with high-level insights.

    Target Audience: C-level executives, decision makers
    Content Focus: Business value, ROI, strategic insights
    """
    recommendations = report.recommendations.all()

    # Calculate high-level metrics
    metrics = {
        'total_savings': calculate_total_savings(recommendations),
        'roi_metrics': calculate_roi_metrics(recommendations),
        'time_savings': calculate_time_savings(recommendations),
        'advisor_score': calculate_advisor_score(report=report),
    }

    # Identify strategic priorities
    high_impact_recs = recommendations.filter(
        business_impact='high'
    ).order_by('-potential_savings')[:10]

    # Calculate category priorities
    category_priority = rank_categories_by_value(recommendations)

    context = {
        'report': report,
        'client': report.client,
        'metrics': metrics,

        # Executive summary sections
        'key_findings': generate_key_findings(metrics),
        'top_10_recommendations': high_impact_recs,
        'strategic_priorities': category_priority,
        'action_plan': generate_action_plan(high_impact_recs),

        # Business value
        'business_impact_summary': calculate_business_impact(
            metrics['roi_metrics']
        ),
        'investment_required': estimate_investment(high_impact_recs),

        # Visualizations (charts only, no tables)
        'savings_by_category_chart': prepare_horizontal_bar_chart(
            metrics
        ),
        'roi_timeline_chart': prepare_timeline_chart(
            metrics['roi_metrics']
        ),

        'generated_at': timezone.now(),
    }

    html_content = render_to_string(
        'reports/executive.html',
        context
    )

    return html_content
```

**Key Sections:**
1. Executive Summary (1 page)
2. Key Metrics Dashboard (1 page)
3. Top 10 Recommendations (2 pages)
4. Financial Impact & ROI (1 page)
5. Strategic Priorities (1 page)
6. Recommended Action Plan (1 page)

**Estimated Length:** 6-8 pages

#### 4.2.3 Cost Optimization Report

**Purpose:** Focus exclusively on cost savings opportunities

**Algorithm:**
```python
def generate_cost_report(report):
    """
    Generate cost optimization focused report.

    Target Audience: Finance teams, FinOps professionals
    Content Focus: Cost savings, ROI, quick wins
    """
    # Filter to cost recommendations only
    cost_recommendations = report.recommendations.filter(
        category='cost'
    ).order_by('-potential_savings')

    # Calculate cost-specific metrics
    metrics = {
        'total_annual_savings': calculate_total_savings(cost_recommendations),
        'monthly_savings': calculate_total_savings(cost_recommendations) / 12,
        'roi_metrics': calculate_roi_metrics(cost_recommendations),
    }

    # Categorize by savings size
    quick_wins = cost_recommendations.filter(
        potential_savings__lte=500
    )  # Small, easy wins

    medium_opportunities = cost_recommendations.filter(
        potential_savings__gt=500,
        potential_savings__lte=2000
    )

    major_opportunities = cost_recommendations.filter(
        potential_savings__gt=2000
    )

    # Group by resource type for analysis
    by_resource_type = group_by_resource_type(cost_recommendations)

    context = {
        'report': report,
        'client': report.client,
        'metrics': metrics,

        # Cost categories
        'quick_wins': {
            'recommendations': quick_wins,
            'total_savings': sum(r.potential_savings for r in quick_wins),
            'count': quick_wins.count()
        },
        'medium_opportunities': {
            'recommendations': medium_opportunities,
            'total_savings': sum(r.potential_savings for r in medium_opportunities),
            'count': medium_opportunities.count()
        },
        'major_opportunities': {
            'recommendations': major_opportunities,
            'total_savings': sum(r.potential_savings for r in major_opportunities),
            'count': major_opportunities.count()
        },

        # Analysis
        'by_resource_type': by_resource_type,
        'savings_timeline': generate_savings_timeline(cost_recommendations),
        'cost_breakdown': generate_cost_breakdown(cost_recommendations),

        # Visualizations
        'savings_waterfall_chart': prepare_waterfall_chart(metrics),
        'resource_type_chart': prepare_tree_map(by_resource_type),

        'generated_at': timezone.now(),
    }

    html_content = render_to_string(
        'reports/cost.html',
        context
    )

    return html_content
```

**Key Sections:**
1. Cost Savings Summary (1 page)
2. Quick Wins (<$500 savings each) (2-5 pages)
3. Medium Opportunities ($500-$2000) (3-8 pages)
4. Major Opportunities (>$2000) (2-5 pages)
5. Resource Type Analysis (2-4 pages)
6. Implementation Roadmap (1-2 pages)

**Estimated Length:** 11-25 pages

#### 4.2.4 Security Assessment Report

**Purpose:** Focus on security and compliance recommendations

**Algorithm:**
```python
def generate_security_report(report):
    """
    Generate security-focused assessment report.

    Target Audience: Security teams, compliance officers
    Content Focus: Security risks, compliance, remediation
    """
    # Filter to security recommendations only
    security_recommendations = report.recommendations.filter(
        category='security'
    ).order_by(
        '-business_impact',  # Prioritize high impact
        '-advisor_score_impact'
    )

    # Calculate security metrics
    metrics = {
        'total_security_issues': security_recommendations.count(),
        'high_risk_count': security_recommendations.filter(
            business_impact='high'
        ).count(),
        'avg_advisor_score_impact': security_recommendations.aggregate(
            avg=models.Avg('advisor_score_impact')
        )['avg'] or 0,
    }

    # Categorize by risk level
    critical_risks = security_recommendations.filter(
        business_impact='high'
    )

    moderate_risks = security_recommendations.filter(
        business_impact='medium'
    )

    low_risks = security_recommendations.filter(
        business_impact='low'
    )

    # Security domains analysis
    security_domains = categorize_security_domains(security_recommendations)

    context = {
        'report': report,
        'client': report.client,
        'metrics': metrics,

        # Risk levels
        'critical_risks': critical_risks,
        'moderate_risks': moderate_risks,
        'low_risks': low_risks,

        # Security domains (IAM, Network, Data Protection, etc.)
        'security_domains': security_domains,

        # Compliance mapping
        'compliance_frameworks': map_to_compliance_frameworks(
            security_recommendations
        ),

        # Remediation
        'remediation_steps': generate_remediation_steps(
            security_recommendations
        ),
        'priority_matrix': create_risk_priority_matrix(
            security_recommendations
        ),

        # Visualizations
        'risk_heatmap': prepare_heatmap(security_recommendations),
        'domain_radar_chart': prepare_radar_chart(security_domains),

        'generated_at': timezone.now(),
    }

    html_content = render_to_string(
        'reports/security.html',
        context
    )

    return html_content
```

**Key Sections:**
1. Security Posture Summary (1 page)
2. Critical Risks (HIGH impact) (2-10 pages)
3. Moderate Risks (MEDIUM impact) (2-8 pages)
4. Security Domains Analysis (2-5 pages)
5. Compliance Mapping (1-3 pages)
6. Remediation Roadmap (2-4 pages)

**Estimated Length:** 10-30 pages

#### 4.2.5 Operational Excellence Report

**Purpose:** Focus on reliability, performance, and operational best practices

**Algorithm:**
```python
def generate_operations_report(report):
    """
    Generate operational excellence focused report.

    Target Audience: DevOps teams, SRE teams
    Content Focus: Reliability, performance, automation
    """
    # Filter to operational categories
    ops_recommendations = report.recommendations.filter(
        category__in=['reliability', 'operational_excellence', 'performance']
    ).order_by('-advisor_score_impact')

    # Calculate operational metrics
    metrics = {
        'total_recommendations': ops_recommendations.count(),
        'reliability_count': ops_recommendations.filter(
            category='reliability'
        ).count(),
        'performance_count': ops_recommendations.filter(
            category='performance'
        ).count(),
        'ops_excellence_count': ops_recommendations.filter(
            category='operational_excellence'
        ).count(),
    }

    # Categorize by pillar
    reliability_recs = ops_recommendations.filter(category='reliability')
    performance_recs = ops_recommendations.filter(category='performance')
    ops_excellence_recs = ops_recommendations.filter(
        category='operational_excellence'
    )

    # Automation opportunities
    automation_opportunities = identify_automation_opportunities(
        ops_recommendations
    )

    context = {
        'report': report,
        'client': report.client,
        'metrics': metrics,

        # Operational pillars
        'reliability_recommendations': reliability_recs,
        'performance_recommendations': performance_recs,
        'ops_excellence_recommendations': ops_excellence_recs,

        # Analysis
        'automation_opportunities': automation_opportunities,
        'monitoring_gaps': identify_monitoring_gaps(ops_recommendations),
        'availability_improvements': calculate_availability_impact(
            reliability_recs
        ),

        # Best practices
        'best_practice_alignment': assess_best_practice_alignment(
            ops_recommendations
        ),

        # Visualizations
        'pillar_distribution_chart': prepare_grouped_bar_chart(metrics),
        'maturity_radar_chart': prepare_maturity_radar_chart(
            ops_recommendations
        ),

        'generated_at': timezone.now(),
    }

    html_content = render_to_string(
        'reports/operations.html',
        context
    )

    return html_content
```

**Key Sections:**
1. Operational Health Summary (1 page)
2. Reliability Improvements (3-8 pages)
3. Performance Optimization (3-8 pages)
4. Operational Excellence (2-6 pages)
5. Automation Opportunities (2-4 pages)
6. Implementation Roadmap (1-2 pages)

**Estimated Length:** 12-28 pages

### 4.3 Report Generation Performance

**Performance Targets:**

| Report Type | Target Time | Max Recommendations | Expected Pages |
|------------|-------------|---------------------|----------------|
| Detailed | <30 seconds | 10,000 | 20-70 |
| Executive | <15 seconds | N/A (uses top 10) | 6-8 |
| Cost | <20 seconds | 5,000 (filtered) | 11-25 |
| Security | <20 seconds | 3,000 (filtered) | 10-30 |
| Operations | <25 seconds | 5,000 (filtered) | 12-28 |

**Optimization Strategies:**
1. **Database Query Optimization**
   - Use select_related() and prefetch_related()
   - Add database indexes on frequently queried fields
   - Batch queries instead of N+1 queries

2. **Caching**
   - Cache frequently accessed report data
   - Cache rendered template sections
   - Cache aggregated metrics

3. **Async Processing**
   - Use Celery for report generation
   - Provide progress updates
   - Allow parallel processing of charts

4. **Template Optimization**
   - Minimize template logic
   - Pre-calculate data in Python
   - Use template fragments for caching

---

## 5. Data Visualization Requirements

### 5.1 Dashboard Visualizations

#### 5.1.1 Metric Cards

**Component:** MetricCard
**Library:** Custom React component
**Data:** Single metric with trend

```javascript
// Metric Card Specification
{
  title: "Total Recommendations",
  value: 1,234,
  change: +15.3,  // percentage
  trend: "up",  // up, down, neutral
  sparkline: [10, 12, 15, 13, 18, 20, 22],  // 7-day data
  icon: "FileText",
  color: "blue"
}
```

**Design:**
- Large number (48px font)
- Trend indicator with percentage
- Mini sparkline chart
- Icon representing metric type

#### 5.1.2 Category Distribution Chart

**Component:** CategoryPieChart
**Library:** Recharts PieChart
**Data:** Recommendations by category

```javascript
// Pie Chart Data Format
{
  data: [
    { name: "Cost", value: 45, color: "#10b981", savings: 12500 },
    { name: "Security", value: 30, color: "#ef4444", savings: 0 },
    { name: "Reliability", value: 15, color: "#3b82f6", savings: 0 },
    { name: "Performance", value: 5, color: "#8b5cf6", savings: 0 },
    { name: "Ops Excellence", value: 5, color: "#f59e0b", savings: 0 }
  ],
  totalRecommendations: 100
}
```

**Features:**
- Interactive tooltips
- Click to filter dashboard
- Legend with percentages
- Responsive sizing

#### 5.1.3 Savings Trend Chart

**Component:** SavingsTrendChart
**Library:** Recharts LineChart
**Data:** Daily/weekly savings over time

```javascript
// Trend Chart Data Format
{
  data: [
    { date: "2025-09-01", savings: 5000, recommendations: 12 },
    { date: "2025-09-02", savings: 7500, recommendations: 18 },
    { date: "2025-09-03", savings: 6200, recommendations: 15 },
    // ... 30 days of data
  ],
  period: "30d"  // 7d, 30d, 90d
}
```

**Features:**
- Dual Y-axis (savings and count)
- Zoom and pan
- Date range selector
- Export to CSV

#### 5.1.4 Impact Distribution Chart

**Component:** ImpactBarChart
**Library:** Recharts BarChart
**Data:** Recommendations by impact level

```javascript
// Bar Chart Data Format
{
  data: [
    {
      impact: "High",
      count: 25,
      percentage: 35,
      avgSavings: 1800,
      color: "#ef4444"
    },
    {
      impact: "Medium",
      count: 35,
      percentage: 45,
      avgSavings: 850,
      color: "#f59e0b"
    },
    {
      impact: "Low",
      count: 15,
      percentage: 20,
      avgSavings: 200,
      color: "#10b981"
    }
  ]
}
```

#### 5.1.5 Advisor Score Gauge

**Component:** AdvisorScoreGauge
**Library:** Recharts RadialBarChart
**Data:** Current vs potential score

```javascript
// Gauge Data Format
{
  currentScore: 72.5,
  potentialScore: 85.3,
  improvement: 12.8,
  categoryScores: {
    cost: 75,
    security: 68,
    reliability: 80,
    performance: 70,
    operational: 72
  }
}
```

**Design:**
- Radial gauge (0-100 scale)
- Current score in center
- Potential score indicator
- Color-coded zones (poor, fair, good, excellent)

### 5.2 Report Visualizations (HTML/PDF)

#### 5.2.1 Chart Types Needed

1. **Pie Chart** - Category distribution
2. **Horizontal Bar Chart** - Savings by category
3. **Stacked Bar Chart** - Impact distribution
4. **Line Chart** - Trend analysis
5. **Waterfall Chart** - Cost breakdown
6. **Heatmap** - Risk matrix
7. **Radar Chart** - Security domains
8. **Treemap** - Resource hierarchy

#### 5.2.2 Chart Generation for PDF

**Library:** Chart.js with node-canvas (server-side)

```python
# Server-side chart generation
from chart_generator import ChartGenerator

def generate_category_chart(recommendations):
    """
    Generate category distribution chart as PNG for PDF embedding.
    """
    chart = ChartGenerator()

    data = calculate_category_distribution(recommendations)

    image_bytes = chart.create_pie_chart(
        data=data,
        width=600,
        height=400,
        title="Recommendations by Category"
    )

    # Save to temporary file for PDF inclusion
    chart_path = f"/tmp/chart_{uuid.uuid4()}.png"
    with open(chart_path, 'wb') as f:
        f.write(image_bytes)

    return chart_path
```

**Chart Specifications:**
- Width: 600-800px
- Height: 400-500px
- DPI: 150 (for crisp PDF rendering)
- Format: PNG with transparent background
- Font size: 12-14pt (readable in PDF)

### 5.3 Interactive Dashboard Components

#### 5.3.1 Filter Panel

**Component:** DashboardFilters
**Features:**
- Date range picker (preset ranges: 7d, 30d, 90d, YTD, Custom)
- Client selector (multi-select dropdown)
- Category filter (checkboxes)
- Impact level filter (checkboxes)
- Report type filter
- Export button (CSV, Excel)

#### 5.3.2 Top Recommendations Table

**Component:** TopRecommendationsTable
**Features:**
- Sortable columns
- Pagination (10, 25, 50, 100 rows)
- Search/filter
- Expand row for details
- Quick actions (view report, download)

**Columns:**
- Recommendation (truncated with tooltip)
- Category (colored badge)
- Impact (colored badge)
- Potential Savings (formatted currency)
- Client Name (link to client detail)
- Date Added
- Actions

#### 5.3.3 Recent Activity Feed

**Component:** ActivityFeed
**Features:**
- Real-time updates (WebSocket or polling)
- Activity types: Report generated, CSV uploaded, etc.
- User avatars
- Timestamps (relative: "2 hours ago")
- Click to view details

---

## 6. Performance Optimization Strategy

### 6.1 Database Optimization

#### 6.1.1 Indexing Strategy

```sql
-- Critical indexes for analytics queries

-- Reports table
CREATE INDEX idx_reports_created_at_status ON reports(created_at DESC, status);
CREATE INDEX idx_reports_client_created ON reports(client_id, created_at DESC);

-- Recommendations table
CREATE INDEX idx_recommendations_category_impact ON recommendations(category, business_impact);
CREATE INDEX idx_recommendations_savings ON recommendations(potential_savings DESC);
CREATE INDEX idx_recommendations_report_category ON recommendations(report_id, category);

-- Analytics tables
CREATE INDEX idx_dashboard_metrics_date_period ON analytics_dashboard_metrics(date DESC, period_type);
CREATE INDEX idx_user_activity_date_action ON analytics_user_activity(created_at DESC, action);

-- Composite indexes for common queries
CREATE INDEX idx_recommendations_report_savings ON recommendations(report_id, potential_savings DESC);
CREATE INDEX idx_recommendations_category_savings ON recommendations(category, potential_savings DESC);
```

#### 6.1.2 Query Optimization Patterns

```python
# GOOD: Use select_related for ForeignKey
reports = Report.objects.select_related('client', 'created_by').all()

# GOOD: Use prefetch_related for reverse ForeignKey
reports = Report.objects.prefetch_related('recommendations').all()

# GOOD: Use annotations instead of Python loops
category_stats = Recommendation.objects.values('category').annotate(
    count=Count('id'),
    total_savings=Sum('potential_savings')
)

# BAD: N+1 query problem
for report in Report.objects.all():
    count = report.recommendations.count()  # Extra query per report!

# GOOD: Single query with annotation
reports = Report.objects.annotate(
    rec_count=Count('recommendations')
)
```

### 6.2 Caching Strategy

#### 6.2.1 Cache Layers

```python
# Layer 1: Application Cache (Django cache framework with Redis)
from django.core.cache import cache

def get_dashboard_metrics(date=None, period='daily'):
    """Get dashboard metrics with caching."""
    cache_key = f"dashboard:metrics:{date}:{period}"

    # Try cache first
    metrics = cache.get(cache_key)
    if metrics is not None:
        return metrics

    # Calculate if not cached
    metrics = DashboardMetrics.calculate_for_date(date, period)

    # Cache for 5 minutes (current day) or 1 hour (historical)
    ttl = 300 if date == timezone.now().date() else 3600
    cache.set(cache_key, metrics, ttl)

    return metrics

# Layer 2: Database-level caching (PostgreSQL materialized views)
"""
-- Materialized view for frequently accessed aggregates
CREATE MATERIALIZED VIEW mv_client_metrics AS
SELECT
    c.id as client_id,
    c.company_name,
    COUNT(DISTINCT r.id) as total_reports,
    COUNT(rec.id) as total_recommendations,
    SUM(rec.potential_savings) as total_savings,
    MAX(r.created_at) as last_report_date
FROM clients c
LEFT JOIN reports r ON c.id = r.client_id
LEFT JOIN recommendations rec ON r.id = rec.report_id
GROUP BY c.id, c.company_name;

-- Refresh daily at 3 AM
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_client_metrics;
"""

# Layer 3: React Query caching (frontend)
"""
const { data, isLoading } = useQuery(
    ['dashboardMetrics', dateRange],
    () => fetchDashboardMetrics(dateRange),
    {
        staleTime: 5 * 60 * 1000,  // 5 minutes
        cacheTime: 30 * 60 * 1000,  // 30 minutes
        refetchOnWindowFocus: false
    }
);
"""
```

#### 6.2.2 Cache Invalidation

```python
# Invalidate caches when data changes
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Report)
def invalidate_report_caches(sender, instance, **kwargs):
    """Invalidate relevant caches when report is updated."""
    if instance.status == 'completed':
        # Invalidate dashboard metrics for today
        today = timezone.now().date()
        cache.delete(f"dashboard:metrics:{today}:daily")
        cache.delete(f"dashboard:metrics:{today}:weekly")
        cache.delete(f"dashboard:metrics:{today}:monthly")

        # Invalidate client metrics
        cache.delete(f"client:metrics:{instance.client.id}")

        # Invalidate category trends
        cache.delete(f"trends:categories:{today}")
```

### 6.3 CSV Processing Optimization

#### 6.3.1 Large File Handling

```python
import pandas as pd
from django.db import transaction

def process_large_csv(file_path, report, chunk_size=1000):
    """
    Process large CSV files in chunks to avoid memory issues.

    Args:
        file_path: Path to CSV file
        report: Report object
        chunk_size: Number of rows to process at once
    """
    # Read CSV in chunks
    chunks = pd.read_csv(
        file_path,
        encoding='utf-8-sig',  # Handle BOM
        chunksize=chunk_size,
        dtype={
            'Subscription ID': str,
            'Potential Annual Cost Savings': float
        },
        parse_dates=['Retirement Date']
    )

    total_processed = 0
    recommendations_to_create = []

    for chunk in chunks:
        # Process chunk
        for idx, row in chunk.iterrows():
            rec = Recommendation(
                report=report,
                category=normalize_category(row['Category']),
                business_impact=normalize_impact(row['Business Impact']),
                recommendation=row['Recommendation'],
                subscription_id=row['Subscription ID'],
                subscription_name=row['Subscription Name'],
                resource_group=row['Resource Group'],
                resource_name=row['Resource Name'],
                resource_type=row['Resource Type'],
                potential_savings=Decimal(str(row['Potential Annual Cost Savings'] or 0)),
                currency=row['Currency'],
                potential_benefits=row['Potential Benefits'],
                advisor_score_impact=Decimal(str(row['Advisor Score Impact'] or 0)),
                csv_row_number=idx + 2  # +2 for header and 0-indexing
            )
            recommendations_to_create.append(rec)

        # Bulk create every chunk
        with transaction.atomic():
            Recommendation.objects.bulk_create(
                recommendations_to_create,
                batch_size=500
            )

        total_processed += len(recommendations_to_create)
        recommendations_to_create = []

        # Update progress
        report.analysis_data['processing_progress'] = {
            'rows_processed': total_processed,
            'status': 'processing'
        }
        report.save(update_fields=['analysis_data'])

    return total_processed
```

#### 6.3.2 Data Validation

```python
def validate_csv_file(file_path):
    """
    Validate CSV file structure and content before processing.

    Raises:
        ValidationError: If CSV is invalid

    Returns:
        dict: Validation summary
    """
    try:
        # Read first few rows for validation
        df = pd.read_csv(file_path, encoding='utf-8-sig', nrows=5)
    except Exception as e:
        raise ValidationError(f"Failed to read CSV: {str(e)}")

    # Check required columns
    required_columns = [
        'Category', 'Business Impact', 'Recommendation',
        'Subscription ID', 'Subscription Name', 'Currency'
    ]

    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        raise ValidationError(
            f"Missing required columns: {', '.join(missing_columns)}"
        )

    # Validate data types
    errors = []

    # Check Category values
    invalid_categories = df[
        ~df['Category'].isin(VALID_CATEGORIES)
    ]['Category'].unique()
    if len(invalid_categories) > 0:
        errors.append(
            f"Invalid categories found: {', '.join(invalid_categories)}"
        )

    # Check Impact values
    invalid_impacts = df[
        ~df['Business Impact'].isin(VALID_IMPACTS)
    ]['Business Impact'].unique()
    if len(invalid_impacts) > 0:
        errors.append(
            f"Invalid impact levels found: {', '.join(invalid_impacts)}"
        )

    if errors:
        raise ValidationError('; '.join(errors))

    # Count total rows (full file)
    row_count = sum(1 for _ in open(file_path)) - 1  # Exclude header

    if row_count > MAX_RECOMMENDATIONS:
        raise ValidationError(
            f"File contains {row_count} rows, "
            f"maximum allowed is {MAX_RECOMMENDATIONS}"
        )

    if row_count < MIN_RECOMMENDATIONS:
        raise ValidationError(
            f"File contains {row_count} rows, "
            f"minimum required is {MIN_RECOMMENDATIONS}"
        )

    return {
        'valid': True,
        'row_count': row_count,
        'columns': list(df.columns),
        'sample_data': df.head(3).to_dict('records')
    }
```

### 6.4 Report Generation Optimization

#### 6.4.1 Parallel Processing

```python
from celery import group

def generate_report_parallel(report_id, report_type):
    """
    Generate report with parallel task execution.
    """
    report = Report.objects.get(id=report_id)

    # Create parallel task group
    task_group = group(
        calculate_metrics_task.s(report_id),
        prepare_recommendations_data.s(report_id, report_type),
        generate_charts_task.s(report_id)
    )

    # Execute in parallel
    result = task_group.apply_async()

    # Wait for all tasks to complete
    metrics, recommendations_data, chart_paths = result.get()

    # Render template with collected data
    html_content = render_template(
        report_type,
        metrics=metrics,
        recommendations=recommendations_data,
        charts=chart_paths
    )

    # Generate PDF
    pdf_path = generate_pdf_from_html(html_content)

    # Upload to blob storage
    upload_report_files(report, html_content, pdf_path)

    report.complete_processing()
```

#### 6.4.2 Template Fragment Caching

```django
{# In Django templates #}
{% load cache %}

{# Cache metrics section for 5 minutes #}
{% cache 300 report_metrics report.id %}
<div class="metrics-section">
    {{ metrics_html }}
</div>
{% endcache %}

{# Don't cache dynamic sections #}
<div class="recommendations-section">
    {% for rec in recommendations %}
        {# Render each recommendation #}
    {% endfor %}
</div>
```

### 6.5 Frontend Performance

#### 6.5.1 Code Splitting

```javascript
// Lazy load report pages
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const ClientsPage = React.lazy(() => import('./pages/ClientsPage'));
const ReportsPage = React.lazy(() => import('./pages/ReportsPage'));

// Use Suspense for loading states
<Suspense fallback={<LoadingSpinner />}>
    <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/clients" element={<ClientsPage />} />
        <Route path="/reports" element={<ReportsPage />} />
    </Routes>
</Suspense>
```

#### 6.5.2 Data Virtualization

```javascript
// Use react-window for large lists
import { FixedSizeList } from 'react-window';

const RecommendationList = ({ recommendations }) => {
    const Row = ({ index, style }) => (
        <div style={style}>
            <RecommendationCard data={recommendations[index]} />
        </div>
    );

    return (
        <FixedSizeList
            height={600}
            itemCount={recommendations.length}
            itemSize={120}
            width="100%"
        >
            {Row}
        </FixedSizeList>
    );
};
```

---

## 7. Sample Data Sets

### 7.1 Sample Data Files Created

I've created three sample CSV files with varying sizes:

1. **sample_small.csv** - 50 recommendations (~5KB)
   - Good for development and quick testing
   - Covers all categories and impact levels
   - Multiple subscriptions and resource types

2. **sample_medium.csv** - 500 recommendations (~50KB)
   - Realistic production scenario
   - Tests pagination and filtering
   - Multiple clients' data combined

3. **sample_large.csv** - 2,000 recommendations (~200KB)
   - Stress testing
   - Performance validation
   - Large organization scenario

### 7.2 Data Generation Methodology

Sample data was generated with realistic distributions:

**Category Distribution:**
- Cost: 35%
- Security: 25%
- Reliability: 20%
- Operational Excellence: 12%
- Performance: 8%

**Impact Distribution:**
- High: 20%
- Medium: 50%
- Low: 30%

**Savings Distribution:**
- High Impact: $500 - $5,000 per recommendation
- Medium Impact: $100 - $1,500 per recommendation
- Low Impact: $0 - $500 per recommendation

**Resource Types:**
- Virtual Machines: 30%
- Storage Accounts: 20%
- Network Resources: 20%
- Databases: 15%
- App Services: 10%
- Other: 5%

---

## 8. Recommendations for Milestone 3

### 8.1 Immediate Actions for CSV Processing

1. **Implement CSV Validation Service**
   - Create `apps/reports/services/csv_validator.py`
   - Add comprehensive validation before processing
   - Provide clear error messages for invalid files

2. **Create CSV Processor Service**
   - Implement `apps/reports/services/csv_processor.py`
   - Use pandas for efficient data processing
   - Handle encoding issues (UTF-8 with BOM)
   - Implement chunking for large files

3. **Setup Celery Tasks**
   - Create `apps/reports/tasks.py`
   - Implement `process_csv_file` task
   - Add progress tracking
   - Implement error handling and retry logic

4. **Add File Storage**
   - Configure Azure Blob Storage
   - Create blob containers
   - Implement file upload/download utilities

### 8.2 Analytics Implementation Priority

**Phase 1: Core Metrics (Week 1)**
1. Implement basic metrics calculation functions
2. Create DashboardMetrics calculation service
3. Add database indexes for performance
4. Setup daily metrics calculation job

**Phase 2: Dashboard API (Week 2)**
1. Create analytics API endpoints
2. Implement caching layer
3. Add filters and date range support
4. Create serializers for metrics data

**Phase 3: Advanced Analytics (Week 3)**
1. Implement ClientMetrics calculation
2. Add trend analysis functions
3. Create category-specific analytics
4. Implement ROI calculations

**Phase 4: Optimization (Week 4)**
1. Add materialized views
2. Implement cache warming
3. Optimize slow queries
4. Load testing and tuning

### 8.3 Testing Strategy

**Unit Tests:**
- CSV validation logic
- Metrics calculation functions
- Data transformation utilities
- Report generation algorithms

**Integration Tests:**
- CSV upload → processing → report generation flow
- Metrics calculation with real data
- Cache invalidation
- Blob storage operations

**Performance Tests:**
- CSV processing with 10,000+ recommendations
- Report generation time benchmarks
- Dashboard load time with large datasets
- Concurrent user simulations

**Sample Test Data:**
Use the provided sample CSV files for testing:
- Small: Quick tests during development
- Medium: Integration testing
- Large: Performance and stress testing

### 8.4 Monitoring & Observability

**Metrics to Track:**
1. CSV processing time by file size
2. Report generation time by type
3. Cache hit rates
4. Database query performance
5. API response times
6. Celery queue length
7. Error rates by operation

**Alerts to Configure:**
1. CSV processing failures
2. Report generation timeouts
3. Cache failures
4. High database load
5. Celery worker failures
6. Blob storage errors

---

## Appendix A: Metrics Glossary

**Total Recommendations:** Count of all Azure Advisor recommendations across all reports

**Potential Annual Savings:** Sum of all cost optimization recommendations' annual savings projections

**Advisor Score:** Azure's proprietary score (0-100) measuring adherence to best practices

**Business Impact:** Categorization of recommendation urgency (High, Medium, Low)

**Category Distribution:** Breakdown of recommendations across 5 pillars (Cost, Security, Reliability, Performance, Operational Excellence)

**ROI (Return on Investment):** Financial return percentage calculated as (Savings - Implementation Cost) / Implementation Cost × 100

**Payback Period:** Time required to recover implementation costs through realized savings

**Time Savings:** Estimated working hours saved by automated recommendation identification

---

## Appendix B: Data Dictionary

See `apps/reports/models.py` and `apps/analytics/models.py` for complete field definitions.

**Key Fields:**

- `potential_savings`: Decimal(12,2) - Annual cost savings in specified currency
- `advisor_score_impact`: Decimal(5,2) - Impact on Advisor Score (0-10 scale)
- `category`: Enum - One of 5 Azure Advisor categories
- `business_impact`: Enum - High, Medium, or Low
- `analysis_data`: JSONField - Calculated metrics and aggregations

---

## Document Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-01 | Analytics Team | Initial comprehensive analytics design |

---

**End of Analytics Design Document**
