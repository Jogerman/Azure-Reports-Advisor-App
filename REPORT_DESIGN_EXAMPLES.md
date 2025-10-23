# Azure Advisor Reports - Design Examples & Visual Reference

## Quick Visual Reference Guide

This document provides visual examples and code snippets for all design components in the Azure Advisor Reports redesign.

---

## 1. Cover Page

### Visual Layout

```
┌────────────────────────────────────────────────────────┐
│  ┌──┐                                                  │
│  │ ☁│  [Logo Icon]                                     │
│  └──┘  Company Name                                    │
│                                                         │
│                                                         │
│              Azure Advisor                             │
│           Analysis Report                              │
│         [Detailed Report]                              │
│                                                         │
│              ┌─────┐                                   │
│              │  📊 │  [Large Icon]                     │
│              └─────┘                                   │
│                                                         │
│  ─────────────────────────────────────────────────    │
│  Report Date     Total Findings    Potential Savings  │
│  Jan 15, 2025         47              $125,000        │
└────────────────────────────────────────────────────────┘
Background: Gradient (cyan → blue → purple)
```

### Code Example

```html
<div class="cover-page">
    <div class="cover-header">
        <div class="cover-logo">[Logo/Icon]</div>
        <div class="cover-company">CONTOSO</div>
    </div>

    <div class="cover-main">
        <h1 class="cover-title">Azure Advisor<br>Analysis Report</h1>
        <p class="cover-subtitle">Detailed Report</p>
        <div class="cover-icon-container">
            <div class="cover-icon">📊</div>
        </div>
    </div>

    <div class="cover-footer">
        <div class="cover-footer-grid">
            <div class="cover-footer-item">
                <div class="cover-footer-label">Report Date</div>
                <div class="cover-footer-value">January 15, 2025</div>
            </div>
            <!-- More footer items... -->
        </div>
    </div>
</div>
```

---

## 2. Metric Cards

### Visual Layout

```
┌─────────────────────────────┐
│ ─── [Gradient Top Border]   │
│                              │
│  💰 [Icon]                   │
│                              │
│  POTENTIAL ANNUAL SAVINGS    │
│  $125,000                    │
│  $10,417 per month          │
└─────────────────────────────┘
```

### Variations

**Default (Blue)**
```html
<div class="metric-card">
    <div class="metric-icon">📊</div>
    <div class="metric-label">Total Recommendations</div>
    <div class="metric-value">47</div>
    <div class="metric-subtitle">Across all categories</div>
</div>
```

**Cost (Green)**
```html
<div class="metric-card metric-cost">
    <div class="metric-icon">💰</div>
    <div class="metric-label">Potential Annual Savings</div>
    <div class="metric-value">$125,000</div>
    <div class="metric-subtitle">$10,417 per month</div>
</div>
```

**Security (Orange)**
```html
<div class="metric-card metric-security">
    <div class="metric-icon">🔒</div>
    <div class="metric-label">Security Issues</div>
    <div class="metric-value">12</div>
    <div class="metric-subtitle">Require attention</div>
</div>
```

**Critical (Red)**
```html
<div class="metric-card metric-critical">
    <div class="metric-icon">⚠️</div>
    <div class="metric-label">High Priority Items</div>
    <div class="metric-value">8</div>
    <div class="metric-subtitle">Immediate action required</div>
</div>
```

---

## 3. Section Headers

### Visual Layout

```
┌──────────────────────────────────────────────────┐
│  ┌─────┐                                         │
│  │ 💰  │  Cost Optimization         12 items    │
│  └─────┘                                         │
│  ─────────────────────────────────────────────── │
└──────────────────────────────────────────────────┘
```

### Code Examples

**Cost Optimization**
```html
<div class="section-header">
    <div class="section-icon icon-cost">💰</div>
    <h2 class="section-title">Cost Optimization</h2>
    <span class="section-count">12 items</span>
</div>
```

**Security**
```html
<div class="section-header">
    <div class="section-icon icon-security">🔒</div>
    <h2 class="section-title">Security Assessment</h2>
    <span class="section-count">8 items</span>
</div>
```

**Reliability**
```html
<div class="section-header">
    <div class="section-icon icon-reliability">🛡️</div>
    <h2 class="section-title">Reliability</h2>
    <span class="section-count">15 items</span>
</div>
```

**Operations**
```html
<div class="section-header">
    <div class="section-icon icon-operations">⚙️</div>
    <h2 class="section-title">Operational Excellence</h2>
    <span class="section-count">10 items</span>
</div>
```

---

## 4. Data Tables

### Visual Layout

```
┌────────────────────────────────────────────────────┐
│  Priority │ Recommendation      │ Resource │ Savings │
│  ═════════════════════════════════════════════════ │
│  [HIGH]   │ Reduce VM size      │ vm-001   │ $5,000  │
│  [MEDIUM] │ Delete unused disk  │ disk-02  │ $1,200  │
│  [LOW]    │ Enable monitoring   │ web-app  │   —     │
└────────────────────────────────────────────────────┘
```

### Code Example

```html
<div class="table-container">
    <table class="data-table">
        <thead>
            <tr>
                <th>Priority</th>
                <th>Recommendation</th>
                <th>Resource</th>
                <th style="text-align: right;">Savings</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>
                    <span class="badge badge-high">HIGH</span>
                </td>
                <td>
                    <div class="font-bold">Right-size underutilized VMs</div>
                    <div class="text-sm text-muted">Reduce costs by 40%</div>
                </td>
                <td>
                    <strong>vm-production-001</strong><br>
                    <small class="text-muted">Standard_D4s_v3</small>
                </td>
                <td style="text-align: right;">
                    <strong class="text-success">$5,000</strong><br>
                    <small class="text-muted">$417/mo</small>
                </td>
            </tr>
            <!-- More rows... -->
        </tbody>
    </table>
</div>
```

---

## 5. Badges

### Priority Badges

**High Priority**
```html
<span class="badge badge-high">HIGH</span>
```
Visual: 🔴 Red gradient background, white text, rounded

**Medium Priority**
```html
<span class="badge badge-medium">MEDIUM</span>
```
Visual: 🟠 Orange gradient background, white text, rounded

**Low Priority**
```html
<span class="badge badge-low">LOW</span>
```
Visual: 🟢 Green gradient background, white text, rounded

### Category Badges

**Cost**
```html
<span class="badge badge-cost">Cost</span>
```
Visual: Green flat color

**Security**
```html
<span class="badge badge-security">Security</span>
```
Visual: Orange flat color

**Reliability**
```html
<span class="badge badge-reliability">Reliability</span>
```
Visual: Cyan flat color

**Operational Excellence**
```html
<span class="badge badge-operational_excellence">Ops Excellence</span>
```
Visual: Purple flat color

**Performance**
```html
<span class="badge badge-performance">Performance</span>
```
Visual: Violet flat color

---

## 6. Charts

### Donut Chart (Category Distribution)

```
        ┌─────────────────┐
        │                 │
        │    ╭───────╮    │
        │   ╱    47   ╲   │
        │  │  Total   │   │
        │   ╲         ╱   │
        │    ╰───────╯    │
        │                 │
        │ ■ Cost (12)     │
        │ ■ Security (8)  │
        │ ■ Other (27)    │
        └─────────────────┘
```

**Code:**
```html
<div class="chart-container">
    <div class="chart-header">
        <h3 class="chart-title">Recommendations by Category</h3>
        <p class="chart-subtitle">Distribution across pillars</p>
    </div>
    <div class="chart-wrapper">
        <canvas id="categoryChart"></canvas>
    </div>
</div>

<script>
new Chart(document.getElementById('categoryChart'), {
    type: 'doughnut',
    data: {
        labels: ['Cost', 'Security', 'Reliability', 'Operations', 'Performance'],
        datasets: [{
            data: [12, 8, 15, 10, 2],
            backgroundColor: ['#107C10', '#FF8C00', '#00BCF2', '#8661C5', '#9966FF']
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { position: 'bottom' }
        }
    }
});
</script>
```

### Horizontal Bar Chart (Savings by Category)

```
        ┌─────────────────────────┐
        │                         │
        │ Cost    ████████ $75K   │
        │ Security ████ $25K      │
        │ Reliability ██ $15K     │
        │ Operations █ $10K       │
        └─────────────────────────┘
```

**Code:**
```html
<div class="chart-container">
    <div class="chart-header">
        <h3 class="chart-title">Potential Savings by Category</h3>
        <p class="chart-subtitle">Annual cost reduction</p>
    </div>
    <div class="chart-wrapper chart-large">
        <canvas id="savingsChart"></canvas>
    </div>
</div>

<script>
new Chart(document.getElementById('savingsChart'), {
    type: 'bar',
    data: {
        labels: ['Cost', 'Security', 'Reliability', 'Operations'],
        datasets: [{
            data: [75000, 25000, 15000, 10000],
            backgroundColor: ['#107C10', '#FF8C00', '#00BCF2', '#8661C5'],
            borderRadius: 6
        }]
    },
    options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: {
                ticks: {
                    callback: (value) => '$' + value.toLocaleString()
                }
            }
        }
    }
});
</script>
```

### Vertical Bar Chart (Subscriptions)

```
        ┌─────────────────────────┐
        │     ║                    │
        │  15 ║                    │
        │     ║                    │
        │  10 ║  ███  ██           │
        │     ║  ███  ██    █      │
        │   5 ║  ███  ██    █      │
        │     └──────────────────  │
        │      Sub1  Sub2  Sub3    │
        └─────────────────────────┘
```

**Code:**
```html
<div class="chart-container">
    <div class="chart-wrapper chart-large">
        <canvas id="subscriptionChart"></canvas>
    </div>
</div>

<script>
new Chart(document.getElementById('subscriptionChart'), {
    type: 'bar',
    data: {
        labels: ['Production', 'Development', 'Testing'],
        datasets: [{
            label: 'Recommendations',
            data: [12, 8, 3],
            backgroundColor: '#0078D4',
            borderRadius: 6
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: { beginAtZero: true }
        }
    }
});
</script>
```

---

## 7. Info Boxes

### Visual Layout

```
┌────────────────────────────────────────┐
│ ├─── [Colored Left Border]             │
│                                         │
│  💡 [Icon]                              │
│                                         │
│  Heading Text                           │
│  Body content goes here with           │
│  multiple lines of text...             │
└────────────────────────────────────────┘
```

### Variations

**Info Box (Blue)**
```html
<div class="info-box">
    <div class="info-box-icon">💡</div>
    <h3>Key Information</h3>
    <p>Important details about the recommendations...</p>
</div>
```

**Success Box (Green)**
```html
<div class="success-box">
    <h3>Implementation Success</h3>
    <p>These recommendations have been successfully implemented.</p>
</div>
```

**Warning Box (Orange)**
```html
<div class="warning-box">
    <h3>Attention Required</h3>
    <p>Review these items carefully before implementation.</p>
</div>
```

**Danger Box (Red)**
```html
<div class="danger-box">
    <div class="info-box-icon">⚠️</div>
    <h3>Critical Alert</h3>
    <p>Immediate action required to address security vulnerabilities.</p>
</div>
```

---

## 8. Complete Layout Examples

### Executive Summary Section

```html
<div class="executive-summary">
    <div class="summary-header">
        <h2 class="summary-title">Executive Summary</h2>
        <p class="summary-subtitle">Key findings from Azure Advisor</p>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-icon">📊</div>
            <div class="metric-label">Total Recommendations</div>
            <div class="metric-value">47</div>
            <div class="metric-subtitle">Across all categories</div>
        </div>

        <div class="metric-card metric-cost">
            <div class="metric-icon">💰</div>
            <div class="metric-label">Potential Annual Savings</div>
            <div class="metric-value">$125,000</div>
            <div class="metric-subtitle">$10,417 per month</div>
        </div>

        <div class="metric-card metric-critical">
            <div class="metric-icon">⚠️</div>
            <div class="metric-label">High Priority Items</div>
            <div class="metric-value">8</div>
            <div class="metric-subtitle">Immediate attention</div>
        </div>

        <div class="metric-card">
            <div class="metric-icon">🎯</div>
            <div class="metric-label">Categories Affected</div>
            <div class="metric-value">5</div>
            <div class="metric-subtitle">Azure Advisor pillars</div>
        </div>
    </div>
</div>
```

### Category Detail Section

```html
<div class="section">
    <div class="section-header">
        <div class="section-icon icon-cost">💰</div>
        <h2 class="section-title">Cost Optimization</h2>
        <span class="section-count">12 items</span>
    </div>

    <div class="table-container">
        <table class="data-table">
            <thead>
                <tr>
                    <th>Priority</th>
                    <th>Recommendation</th>
                    <th>Resource</th>
                    <th style="text-align: right;">Savings</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><span class="badge badge-high">HIGH</span></td>
                    <td>
                        <div class="font-bold">Right-size underutilized VMs</div>
                        <div class="text-sm text-muted">Benefits: Reduce costs by 40%</div>
                    </td>
                    <td>
                        <div class="font-semibold">vm-production-001</div>
                        <div class="text-xs text-muted">Type: Standard_D4s_v3</div>
                    </td>
                    <td style="text-align: right;">
                        <div class="font-bold text-success text-lg">$5,000</div>
                        <div class="text-xs text-muted">$417/month</div>
                    </td>
                </tr>
                <!-- More rows... -->
            </tbody>
        </table>
    </div>
</div>
```

### Chart Section with Multiple Charts

```html
<div class="section">
    <div class="section-header">
        <div class="section-icon">📈</div>
        <h2 class="section-title">Distribution Analysis</h2>
    </div>

    <div class="charts-grid">
        <!-- Chart 1 -->
        <div class="chart-container">
            <div class="chart-header">
                <h3 class="chart-title">By Category</h3>
                <p class="chart-subtitle">Recommendation distribution</p>
            </div>
            <div class="chart-wrapper">
                <canvas id="chart1"></canvas>
            </div>
        </div>

        <!-- Chart 2 -->
        <div class="chart-container">
            <div class="chart-header">
                <h3 class="chart-title">By Priority</h3>
                <p class="chart-subtitle">Impact level breakdown</p>
            </div>
            <div class="chart-wrapper">
                <canvas id="chart2"></canvas>
            </div>
        </div>
    </div>
</div>
```

---

## 9. Color Examples in Context

### Category Color Coding

**In Tables:**
```
Priority Column:
  HIGH    → Red badge (#D13438)
  MEDIUM  → Orange badge (#FF8C00)
  LOW     → Green badge (#107C10)

Category Column:
  Cost                    → Green (#107C10)
  Security                → Orange (#FF8C00)
  Reliability             → Cyan (#00BCF2)
  Operational Excellence  → Purple (#8661C5)
  Performance             → Violet (#9966FF)
```

**In Section Headers:**
```
Cost Section            → Green gradient icon
Security Section        → Orange gradient icon
Reliability Section     → Cyan gradient icon
Operations Section      → Purple gradient icon
Performance Section     → Violet gradient icon
```

**In Metric Cards:**
```
Default Card           → Blue top border & icon
Cost Card              → Green top border & icon
Security Card          → Orange top border & icon
Critical Card          → Red top border & icon
```

---

## 10. Typography Examples

### Heading Hierarchy

```html
<!-- Page Title (36px, Bold) -->
<h1 class="text-4xl font-bold text-primary">Azure Advisor Report</h1>

<!-- Section Title (30px, Bold) -->
<h2 class="text-3xl font-bold">Cost Optimization</h2>

<!-- Subsection Title (24px, Semibold) -->
<h3 class="text-2xl font-semibold">High Priority Items</h3>

<!-- Body Text (16px, Normal) -->
<p class="text-base">This section contains recommendations...</p>

<!-- Small Text (14px, Normal) -->
<p class="text-sm text-muted">Additional context or metadata</p>

<!-- Extra Small (12px, Uppercase, Bold) -->
<span class="text-xs font-bold" style="text-transform: uppercase;">Label</span>
```

### Metric Display

```html
<!-- Large Metric (48px, Bold) -->
<div class="metric-value">$125,000</div>

<!-- Medium Metric (24px, Semibold) -->
<div class="text-2xl font-semibold">47 Recommendations</div>

<!-- Small Metric (18px, Bold) -->
<div class="text-lg font-bold">High Priority: 8</div>
```

---

## 11. Spacing Examples

### Card Spacing

```css
/* Compact Card */
.metric-card {
    padding: 20px;  /* spacing-5 */
    gap: 12px;      /* spacing-3 */
}

/* Standard Card */
.chart-container {
    padding: 32px;  /* spacing-8 */
    margin: 24px 0; /* spacing-6 */
}

/* Section Spacing */
.section {
    margin: 48px 0; /* spacing-12 */
}
```

### Grid Spacing

```css
/* Metrics Grid */
.metrics-grid {
    gap: 24px;      /* spacing-6 */
}

/* Charts Grid */
.charts-grid {
    gap: 24px;      /* spacing-6 */
}

/* Table Cell Spacing */
.data-table td {
    padding: 16px;  /* spacing-4 */
}
```

---

## 12. Responsive Examples

### Desktop (1024px+)

```
┌──────────────────────────────────────────────────────┐
│  [Card 1]  [Card 2]  [Card 3]  [Card 4]             │
│  [Chart 1]           [Chart 2]                       │
│  [Table spanning full width]                         │
└──────────────────────────────────────────────────────┘
4-column grid, side-by-side charts, full tables
```

### Tablet (768px - 1023px)

```
┌────────────────────────────┐
│  [Card 1]    [Card 2]      │
│  [Card 3]    [Card 4]      │
│  [Chart 1]                 │
│  [Chart 2]                 │
│  [Scrollable Table]        │
└────────────────────────────┘
2-column grid, stacked charts
```

### Mobile (< 768px)

```
┌─────────────────┐
│    [Card 1]     │
│    [Card 2]     │
│    [Card 3]     │
│    [Card 4]     │
│    [Chart 1]    │
│    [Chart 2]    │
│  [Compact Table]│
└─────────────────┘
1-column layout, smaller text
```

---

## 13. Print Layout

### Page 1 (Cover)

```
╔════════════════════════════════════╗
║     [Gradient Background]          ║
║                                    ║
║     Company Logo                   ║
║                                    ║
║   Azure Advisor                    ║
║   Analysis Report                  ║
║                                    ║
║        [Icon]                      ║
║                                    ║
║  ─────────────────────────         ║
║  Date | Count | Savings            ║
╚════════════════════════════════════╝
[Page Break]
```

### Page 2+ (Content)

```
╔════════════════════════════════════╗
║  [Header with logo]                ║
║  ────────────────────────────      ║
║                                    ║
║  Executive Summary                 ║
║  [Metrics Grid]                    ║
║                                    ║
║  ────────────────────────────      ║
║  Category Summary                  ║
║  [Table]                           ║
║                                    ║
║  [Footer - Page 2 of 10]          ║
╚════════════════════════════════════╝
```

---

## 14. Animation Examples

### Hover Effects

```css
/* Card Hover */
.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
}

/* Table Row Hover */
.data-table tbody tr:hover {
    background-color: #F3F2F1;
    transition: background-color 0.2s ease;
}

/* Button Hover */
.button:hover {
    opacity: 0.8;
    transform: scale(1.05);
    transition: all 0.2s ease;
}
```

---

## 15. Quick Reference Chart

### Component Sizes

| Component | Width | Height | Padding | Radius |
|-----------|-------|--------|---------|--------|
| Metric Card | Auto | Auto | 24px | 12px |
| Chart Container | Auto | 300px | 32px | 12px |
| Section Icon | 40px | 40px | — | 8px |
| Badge | Auto | 24px | 4px 12px | Full |
| Table Cell | Auto | Auto | 16px | — |

### Color Quick Reference

| Element | Color | Hex |
|---------|-------|-----|
| Primary Text | Gray 900 | #201F1E |
| Secondary Text | Gray 600 | #605E5C |
| Links | Azure Blue | #0078D4 |
| Success | Green | #107C10 |
| Warning | Orange | #FF8C00 |
| Danger | Red | #D13438 |

### Typography Quick Reference

| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| Cover Title | 60px | 700 | 1.1 |
| Page Title | 36px | 700 | 1.2 |
| Section Title | 30px | 700 | 1.2 |
| Body Text | 16px | 400 | 1.6 |
| Small Text | 14px | 400 | 1.6 |
| Labels | 12px | 700 | 1.4 |

---

## 16. Common Patterns

### Pattern: Metric Dashboard

```html
<div class="metrics-grid">
    <!-- 4 metric cards showing KPIs -->
    <div class="metric-card">...</div>
    <div class="metric-card metric-cost">...</div>
    <div class="metric-card metric-security">...</div>
    <div class="metric-card metric-critical">...</div>
</div>
```

### Pattern: Data Section

```html
<div class="section">
    <div class="section-header">...</div>
    <div class="chart-container">...</div>
    <div class="table-container">...</div>
</div>
```

### Pattern: Call to Action

```html
<div class="info-box">
    <div class="info-box-icon">💡</div>
    <h3>Next Steps</h3>
    <ol>
        <li>Review recommendations</li>
        <li>Prioritize actions</li>
        <li>Implement changes</li>
    </ol>
</div>
```

---

## Conclusion

This visual reference guide provides all the building blocks needed to create consistent, professional Azure Advisor reports. Use these examples as templates for your own implementations.

For full code examples, see:
- `templates/reports/base_redesigned.html`
- `templates/reports/detailed_redesigned.html`
- `REPORT_DESIGN_SYSTEM.md`
- `REPORT_REDESIGN_IMPLEMENTATION_GUIDE.md`
