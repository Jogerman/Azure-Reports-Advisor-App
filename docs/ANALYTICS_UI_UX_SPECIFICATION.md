# Analytics Dashboard - UI/UX Design Specification
**Azure Advisor Reports Platform**

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Design Philosophy](#design-philosophy)
3. [Visual Design System](#visual-design-system)
4. [Layout Architecture](#layout-architecture)
5. [Component Specifications](#component-specifications)
6. [Data Flow & API Integration](#data-flow--api-integration)
7. [User Experience Patterns](#user-experience-patterns)
8. [Responsive Design Strategy](#responsive-design-strategy)
9. [Implementation Roadmap](#implementation-roadmap)
10. [Technical Stack](#technical-stack)

---

## 1. Executive Summary

The Analytics Dashboard is a premium, data-rich interface designed to provide comprehensive insights into Azure Advisor report generation, user activity, cost analysis, and system performance. This specification delivers an enterprise-grade solution that rivals platforms like Power BI and Tableau.

### Key Objectives
- **Visual Impact**: Create a "wow factor" professional interface
- **Data Clarity**: Present complex analytics in digestible formats
- **Performance**: Ensure sub-second load times with lazy loading
- **Accessibility**: WCAG 2.1 AA compliance minimum
- **Mobile-First**: Exceptional experience on tablets and mobile devices

### Success Metrics
- Page load time < 2 seconds
- Time to Interactive (TTI) < 3 seconds
- Chart render time < 500ms per chart
- Mobile responsiveness: Full feature parity on tablet/mobile

---

## 2. Design Philosophy

### Core Principles

**1. Progressive Disclosure**
- Start with high-level KPIs
- Allow drill-down into detailed metrics
- Use expandable sections for advanced analytics

**2. Data Hierarchy**
- Primary metrics: Large, prominent, immediately visible
- Secondary metrics: Contextual, supporting primary data
- Tertiary metrics: Available on-demand or hover

**3. Cognitive Load Management**
- Maximum 6 KPI cards in primary view
- Group related metrics together
- Use whitespace generously
- Limit colors to meaningful distinctions

**4. Action-Oriented Design**
- Every metric should suggest an action or insight
- Provide clear export and sharing capabilities
- Enable quick filtering without page reload

---

## 3. Visual Design System

### 3.1 Color Palette

**Primary Colors (Azure Brand)**
```css
--azure-primary: #0078D4;      /* Main brand color */
--azure-secondary: #50E6FF;     /* Accent/highlights */
--azure-dark: #004578;          /* Headers, emphasis */
--azure-light: #E6F4FF;         /* Backgrounds, subtle */
```

**Semantic Colors**
```css
--success: #107C10;             /* Positive trends, completed */
--success-light: #F0FDF4;       /* Success backgrounds */
--warning: #FFB900;             /* Warnings, pending */
--warning-light: #FFFBEB;       /* Warning backgrounds */
--error: #D13438;               /* Errors, failures */
--error-light: #FEF2F2;         /* Error backgrounds */
--info: #3B82F6;                /* Informational */
--info-light: #EFF6FF;          /* Info backgrounds */
```

**Chart Colors (8-color palette)**
```css
--chart-1: #0078D4;  /* Azure Blue */
--chart-2: #107C10;  /* Green */
--chart-3: #FFB900;  /* Yellow */
--chart-4: #D13438;  /* Red */
--chart-5: #8B5CF6;  /* Purple */
--chart-6: #50E6FF;  /* Cyan */
--chart-7: #F59E0B;  /* Orange */
--chart-8: #EC4899;  /* Pink */
```

**Neutral Scale**
```css
--gray-50: #F9FAFB;
--gray-100: #F3F4F6;
--gray-200: #E5E7EB;
--gray-300: #D1D5DB;
--gray-500: #6B7280;
--gray-700: #374151;
--gray-900: #111827;
```

### 3.2 Typography

**Font Family**
- Primary: 'Inter', system-ui, sans-serif
- Monospace: 'JetBrains Mono', 'Fira Code', monospace (for numbers)

**Type Scale**
```css
--text-xs: 0.75rem;    /* 12px - Labels, captions */
--text-sm: 0.875rem;   /* 14px - Body text, descriptions */
--text-base: 1rem;     /* 16px - Default text */
--text-lg: 1.125rem;   /* 18px - Card titles */
--text-xl: 1.25rem;    /* 20px - Section headers */
--text-2xl: 1.5rem;    /* 24px - Page title */
--text-3xl: 1.875rem;  /* 30px - KPI numbers */
--text-4xl: 2.25rem;   /* 36px - Hero metrics */
```

**Font Weights**
```css
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### 3.3 Spacing System

**8px Grid System**
```css
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
```

### 3.4 Shadows & Elevation

```css
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
--shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
```

### 3.5 Border Radius

```css
--radius-sm: 0.25rem;   /* 4px - Badges, tags */
--radius-md: 0.5rem;    /* 8px - Buttons, inputs */
--radius-lg: 0.75rem;   /* 12px - Cards */
--radius-xl: 1rem;      /* 16px - Modals */
--radius-2xl: 1.5rem;   /* 24px - Hero elements */
--radius-full: 9999px;  /* Full circle */
```

---

## 4. Layout Architecture

### 4.1 Page Structure

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER (60px fixed)                                         │
│ Analytics Dashboard    [Date Range] [Filters] [Export] [⟳] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ CONTENT AREA (scrollable)                                   │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ SECTION 1: KEY PERFORMANCE INDICATORS                   │ │
│ │ Grid: 3 columns (desktop) / 2 (tablet) / 1 (mobile)    │ │
│ │                                                         │ │
│ │ [KPI Card]  [KPI Card]  [KPI Card]                     │ │
│ │ [KPI Card]  [KPI Card]  [KPI Card]                     │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ SECTION 2: REPORTS ANALYTICS                            │ │
│ │ Grid: 2 columns (desktop) / 1 (tablet/mobile)          │ │
│ │                                                         │ │
│ │ ┌───────────────────────┐  ┌──────────────────────────┐│ │
│ │ │ Reports Over Time     │  │ Reports by Type          ││ │
│ │ │ (Multi-line Chart)    │  │ (Donut Chart)           ││ │
│ │ │                       │  │                          ││ │
│ │ │ Height: 400px         │  │ Height: 400px            ││ │
│ │ └───────────────────────┘  └──────────────────────────┘│ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ SECTION 3: REPORTS STATUS & TOP USERS                   │ │
│ │                                                         │ │
│ │ ┌───────────────────────┐  ┌──────────────────────────┐│ │
│ │ │ Reports by Status     │  │ Top Active Users         ││ │
│ │ │ (Horizontal Bar)      │  │ (Table with avatars)     ││ │
│ │ │ Height: 300px         │  │ Height: 300px            ││ │
│ │ └───────────────────────┘  └──────────────────────────┘│ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ SECTION 4: COST INSIGHTS (for Cost reports)             │ │
│ │                                                         │ │
│ │ ┌───────────────────────┐  ┌──────────────────────────┐│ │
│ │ │ Cost Trends           │  │ Top Cost Categories      ││ │
│ │ │ (Area Chart)          │  │ (Horizontal Bar)         ││ │
│ │ │ Height: 350px         │  │ Height: 350px            ││ │
│ │ └───────────────────────┘  └──────────────────────────┘│ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ SECTION 5: SYSTEM HEALTH (Admin only)                   │ │
│ │                                                         │ │
│ │ [Gauge] [Gauge] [Gauge]   [Performance Metrics Table]  │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Grid System

**Desktop (≥1280px)**
- Container max-width: 1400px
- Gutter: 24px
- Columns: 12-column grid
- KPI Cards: 3 columns (4-column span each)
- Charts: 2 columns (6-column span each)

**Tablet (768px - 1279px)**
- Container: fluid width with 24px padding
- Gutter: 20px
- KPI Cards: 2 columns
- Charts: 1 column (stacked)

**Mobile (<768px)**
- Container: fluid width with 16px padding
- Gutter: 16px
- All elements: 1 column (stacked)
- KPI Cards: horizontal scroll option

---

## 5. Component Specifications

### 5.1 KPI Card Component

**Purpose**: Display key metric with trend indicator and sparkline

**Visual Design**:
```
┌─────────────────────────────────────┐
│ ┌──────┐               ↑ +12.5%    │
│ │ ICON │                            │
│ └──────┘                            │
│                                     │
│ Total Reports Generated             │ ← Text-sm, gray-600
│ 1,247                               │ ← Text-3xl, bold, gray-900
│ ▁▂▃▅▄▆▇█                           │ ← Sparkline
│ vs last month                       │ ← Text-xs, gray-500
└─────────────────────────────────────┘
```

**Component Props**:
```typescript
interface KPICardProps {
  title: string;
  value: number | string;
  icon: ReactNode;
  trend?: {
    value: number;        // Percentage change
    label?: string;       // e.g., "vs last month"
  };
  sparklineData?: number[];
  color?: 'azure' | 'success' | 'warning' | 'danger' | 'info';
  loading?: boolean;
  className?: string;
  onClick?: () => void;
}
```

**Interactions**:
- Hover: Lift effect (translateY: -4px) + shadow increase
- Click: Optional drill-down navigation
- Icon container: Slight rotation on hover (5deg)

**States**:
- **Loading**: Skeleton placeholder with shimmer animation
- **Default**: Full content display
- **Error**: Red border + error icon + "Unable to load" message

**Accessibility**:
- `role="article"`
- `aria-label="{title} metric"`
- Trend indicator with `aria-label="Trend: {direction} {percentage}"`
- Keyboard navigable if clickable

**Responsive Behavior**:
- Desktop: 33% width (3 per row)
- Tablet: 50% width (2 per row)
- Mobile: 100% width (stacked) OR horizontal scroll container

---

### 5.2 Reports Over Time Chart

**Chart Type**: Multi-line Chart (Recharts)

**Data Structure**:
```typescript
interface ReportTrendPoint {
  date: string;           // ISO date
  cost: number;
  security: number;
  performance: number;
  operational: number;
  total: number;
}
```

**Visual Design**:
```
┌─────────────────────────────────────────────┐
│ Reports Over Time           [7d][30d][90d]  │
├─────────────────────────────────────────────┤
│    ┌─────────────────────────────────────┐  │
│  50│                              ╱╲     │  │
│    │                          ╱───  ╲    │  │
│  40│                      ╱───       ╲   │  │
│    │                  ╱───             ╲ │  │
│  30│              ╱───                   │  │
│    │          ╱───                       │  │
│  20│      ╱───                           │  │
│    │  ╱───                               │  │
│  10│─                                    │  │
│    └─────────────────────────────────────┘  │
│     Jan 1   Jan 8   Jan 15  Jan 22  Jan 29  │
│                                             │
│ Legend:                                     │
│ ■ Cost  ■ Security  ■ Performance  ■ All   │
└─────────────────────────────────────────────┘
```

**Configuration**:
```typescript
const chartConfig = {
  height: 400,
  margin: { top: 20, right: 30, left: 20, bottom: 20 },
  strokeWidth: 2.5,
  dotRadius: 4,
  activeDotRadius: 6,
  animationDuration: 800,
  animationEasing: 'ease-in-out'
}
```

**Features**:
- **Time Period Toggle**: 7/30/90 days (buttons in top-right)
- **Series Toggle**: Click legend to show/hide specific report types
- **Tooltips**: Detailed on hover showing all values for that date
- **Zoom**: Brush component for date range selection
- **Responsive**: Adjust height and margins on mobile

**Interactions**:
- Hover over line: Highlight with increased stroke width
- Click legend item: Toggle series visibility
- Drag on chart: Create zoom selection
- Click point: Show detailed breakdown modal

**Empty State**:
```
┌─────────────────────────────────────────┐
│    📊                                   │
│    No report data available             │
│    Generate your first report to see    │
│    analytics here.                      │
│                                         │
│    [Generate Report]                    │
└─────────────────────────────────────────┘
```

---

### 5.3 Reports by Type Chart

**Chart Type**: Donut Chart with Center Label

**Visual Design**:
```
┌─────────────────────────────────┐
│ Reports by Type                 │
├─────────────────────────────────┤
│                                 │
│         ╱────────╲              │
│       ╱            ╲            │
│      │    1,247    │           │
│      │   reports   │           │
│       ╲            ╱            │
│         ╲────────╱              │
│                                 │
│ Legend:                         │
│ ● Cost (342 - 27.4%)           │
│ ● Security (189 - 15.2%)       │
│ ● Performance (456 - 36.6%)    │
│ ● Operational (178 - 14.3%)    │
│ ● Other (82 - 6.5%)            │
└─────────────────────────────────┘
```

**Configuration**:
```typescript
const donutConfig = {
  innerRadius: '60%',
  outerRadius: '80%',
  paddingAngle: 2,
  cornerRadius: 4,
  animationDuration: 1000,
  animationBegin: 0
}
```

**Features**:
- **Center Label**: Total count + label
- **Active Segment**: Expand on hover (outerRadius + 10)
- **Interactive Legend**: Click to highlight segment
- **Tooltips**: Percentage + count on hover

**Interactions**:
- Hover segment: Expand + show detailed tooltip
- Click segment: Filter main data by that type
- Click legend: Isolate that segment

---

### 5.4 Reports by Status Chart

**Chart Type**: Horizontal Bar Chart

**Visual Design**:
```
┌─────────────────────────────────────────┐
│ Reports by Status                       │
├─────────────────────────────────────────┤
│                                         │
│ Completed  ████████████████████  1,156  │
│ Processing █                        12  │
│ Failed     ████                     79  │
│                                         │
└─────────────────────────────────────────┘
```

**Configuration**:
```typescript
const barConfig = {
  layout: 'horizontal',
  barHeight: 48,
  barGap: 16,
  colors: {
    completed: '#107C10',
    processing: '#FFB900',
    failed: '#D13438'
  },
  showValues: true,
  animationDuration: 1000
}
```

**Features**:
- **Color Coding**: Green (completed), Yellow (processing), Red (failed)
- **Value Labels**: Display count on right side of bar
- **Percentage Display**: Show % of total in tooltip

---

### 5.5 Top Active Users Table

**Visual Design**:
```
┌──────────────────────────────────────────────────────────┐
│ Top Active Users                          [View All →]   │
├──────────────────────────────────────────────────────────┤
│ User              Reports   Last Activity      Role      │
├──────────────────────────────────────────────────────────┤
│ ◉ John Smith        42      2 hours ago       Admin     │
│ ◉ Jane Doe          38      5 hours ago       Manager   │
│ ◉ Bob Johnson       35      1 day ago         Analyst   │
│ ◉ Alice Williams    28      1 day ago         Manager   │
│ ◉ Charlie Brown     24      2 days ago        Analyst   │
└──────────────────────────────────────────────────────────┘
```

**Component Props**:
```typescript
interface TopUsersTableProps {
  users: Array<{
    id: string;
    name: string;
    avatar?: string;
    reportsGenerated: number;
    lastActivity: Date;
    role: 'admin' | 'manager' | 'analyst' | 'viewer';
  }>;
  limit?: number;
  onViewAll?: () => void;
  loading?: boolean;
}
```

**Features**:
- **Avatar Display**: User initials or photo (40px circular)
- **Sortable Columns**: Click header to sort
- **Role Badges**: Color-coded (Admin: blue, Manager: purple, etc.)
- **Relative Time**: "2 hours ago" format
- **Hover Row**: Subtle background color change

**Interactions**:
- Click row: Navigate to user profile/activity
- Click "View All": Open full users analytics page
- Hover avatar: Show user details tooltip

---

### 5.6 Cost Insights Section

**Components**:
1. **Cost Insights Summary Card**
2. **Cost Trends Area Chart**
3. **Top Cost Categories Bar Chart**

**5.6.1 Cost Insights Summary Card**
```
┌─────────────────────────────────────────┐
│ 💰 Cost Insights                        │
├─────────────────────────────────────────┤
│                                         │
│ Total Cost Analyzed                     │
│ $845,230                                │
│ ↑ +8.3% from last month                │
│                                         │
│ Potential Savings Identified            │
│ $127,450                                │
│ 15.1% optimization opportunity          │
│                                         │
│ Top Saving Category: Compute (45%)      │
└─────────────────────────────────────────┘
```

**5.6.2 Cost Trends Area Chart**
```typescript
const areChartConfig = {
  type: 'area',
  height: 350,
  gradientFill: true,
  gradientColors: ['rgba(0, 120, 212, 0.4)', 'rgba(0, 120, 212, 0.0)'],
  strokeColor: '#0078D4',
  strokeWidth: 3
}
```

---

### 5.7 System Health Dashboard (Admin Only)

**Visual Design**:
```
┌─────────────────────────────────────────────────────────┐
│ System Health Metrics                    🔒 Admin Only  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │   CPU    │  │  Memory  │  │   API    │             │
│  │   45%    │  │   62%    │  │  125ms   │             │
│  │  ◐       │  │  ◓       │  │  ◑       │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│                                                         │
│  Performance Metrics:                                   │
│  • Avg Report Generation: 23.4s                        │
│  • Database Size: 2.3 GB / 10 GB                       │
│  • Active Sessions: 24                                 │
│  • Cache Hit Rate: 87.5%                               │
└─────────────────────────────────────────────────────────┘
```

**Gauge Component**:
```typescript
interface GaugeProps {
  value: number;        // 0-100
  max?: number;
  title: string;
  unit?: string;
  thresholds?: {
    warning: number;   // e.g., 70
    danger: number;    // e.g., 90
  };
  color?: string;
}
```

**Color Coding**:
- Green: 0-70%
- Yellow: 71-90%
- Red: 91-100%

---

### 5.8 Global Filters Panel

**Visual Design**:
```
┌─────────────────────────────────────────┐
│ Filters                          [Apply]│
├─────────────────────────────────────────┤
│                                         │
│ Date Range                              │
│ [Last 30 days ▼]                       │
│                                         │
│ Report Type                             │
│ ☑ Cost                                  │
│ ☑ Security                              │
│ ☑ Performance                           │
│ ☑ Operational Excellence                │
│                                         │
│ Status                                  │
│ ● All                                   │
│ ○ Completed Only                        │
│ ○ Exclude Failed                        │
│                                         │
│ User Role (Admin)                       │
│ [All Roles ▼]                          │
│                                         │
│ [Reset Filters]      [Apply Filters]   │
└─────────────────────────────────────────┘
```

**Component Props**:
```typescript
interface AnalyticsFilters {
  dateRange: {
    start: Date;
    end: Date;
    preset?: '7d' | '30d' | '90d' | '6m' | '1y' | 'custom';
  };
  reportTypes: string[];
  status: 'all' | 'completed' | 'exclude_failed';
  userRole?: 'admin' | 'manager' | 'analyst' | 'viewer' | null;
}

interface FiltersPanelProps {
  filters: AnalyticsFilters;
  onChange: (filters: AnalyticsFilters) => void;
  onApply: () => void;
  onReset: () => void;
  isAdmin: boolean;
}
```

**Behavior**:
- Filters apply on "Apply Filters" button click (not real-time)
- "Reset Filters" restores to defaults
- Filter state persists in URL params
- Show filter count badge: "Filters (3 active)"

---

### 5.9 Export Menu

**Visual Design**:
```
┌─────────────────────────┐
│ Export Dashboard        │
├─────────────────────────┤
│ 📄 Export as PDF        │
│ 📊 Export Data (CSV)    │
│ 📷 Export Screenshot    │
│ 📧 Email Report         │
│ 🔗 Share Link           │
└─────────────────────────┘
```

**Features**:
- **PDF Export**: Full dashboard snapshot with all visible charts
- **CSV Export**: Raw data with current filters applied
- **Screenshot**: Use html2canvas for image capture
- **Email**: Pre-fill email with dashboard link
- **Share Link**: Generate shareable URL with filters

---

## 6. Data Flow & API Integration

### 6.1 API Endpoints Mapping

**Page Load (Parallel Requests)**:
```typescript
const loadAnalyticsDashboard = async () => {
  const [
    dashboardMetrics,
    trendData,
    categoryDistribution,
    recentActivity,
    costInsights,
    systemHealth
  ] = await Promise.all([
    analyticsApi.getDashboardMetrics(),
    analyticsApi.getTrendData(filters.dateRange),
    analyticsApi.getCategoryDistribution(),
    analyticsApi.getRecentActivity(10),
    analyticsApi.getCostInsights(),      // If has cost reports
    analyticsApi.getSystemHealth()       // If admin
  ]);
}
```

**Endpoint Details**:

| Endpoint | Method | Purpose | Cache |
|----------|--------|---------|-------|
| `/api/v1/analytics/dashboard/` | GET | Complete dashboard data | 5 min |
| `/api/v1/analytics/metrics/` | GET | KPI metrics only | 5 min |
| `/api/v1/analytics/trends/?days=30` | GET | Trend data | 10 min |
| `/api/v1/analytics/categories/` | GET | Category distribution | 10 min |
| `/api/v1/analytics/recent-activity/?limit=10` | GET | Recent activity | 2 min |
| `/api/v1/analytics/client-performance/` | GET | Client metrics | 10 min |
| `/api/v1/analytics/business-impact/` | GET | Impact distribution | 10 min |
| `/api/v1/analytics/cost-insights/` | GET | Cost analytics | 10 min |
| `/api/v1/analytics/system-health/` | GET | System metrics (admin) | 1 min |

### 6.2 Data Transformation Layer

**Example: KPI Metrics Transformation**:
```typescript
// API Response
interface ApiMetricsResponse {
  totalRecommendations: number;
  totalPotentialSavings: number;
  activeClients: number;
  reportsGeneratedThisMonth: number;
  trends: {
    recommendations: number;
    savings: number;
    clients: number;
    reports: number;
  };
}

// Transform to KPI Cards
const transformToKPICards = (data: ApiMetricsResponse): KPICardProps[] => [
  {
    title: 'Total Reports Generated',
    value: data.reportsGeneratedThisMonth.toLocaleString(),
    icon: <FiFileText />,
    trend: {
      value: data.trends.reports,
      label: 'vs last month'
    },
    color: 'azure'
  },
  {
    title: 'Active Clients',
    value: data.activeClients.toLocaleString(),
    icon: <FiUsers />,
    trend: {
      value: data.trends.clients,
      label: 'vs last month'
    },
    color: 'info'
  },
  {
    title: 'Total Recommendations',
    value: data.totalRecommendations.toLocaleString(),
    icon: <FiCheckCircle />,
    trend: {
      value: data.trends.recommendations,
      label: 'vs last month'
    },
    color: 'success'
  },
  {
    title: 'Potential Savings',
    value: `$${(data.totalPotentialSavings / 1000).toFixed(1)}k`,
    icon: <FiDollarSign />,
    trend: {
      value: data.trends.savings,
      label: 'vs last month'
    },
    color: 'warning'
  }
];
```

### 6.3 Caching Strategy

**Client-Side Cache**:
```typescript
import { useQuery, UseQueryOptions } from '@tanstack/react-query';

const useAnalyticsDashboard = (filters: AnalyticsFilters) => {
  return useQuery({
    queryKey: ['analytics', 'dashboard', filters],
    queryFn: () => analyticsApi.getDashboardMetrics(filters),
    staleTime: 5 * 60 * 1000,        // 5 minutes
    cacheTime: 10 * 60 * 1000,       // 10 minutes
    refetchOnWindowFocus: false,
    refetchInterval: 5 * 60 * 1000   // Auto-refetch every 5 min
  });
};
```

**Backend Cache**:
- Redis cache with 5-10 minute TTL
- Cache invalidation on new report generation
- Manual cache refresh button for admins

---

## 7. User Experience Patterns

### 7.1 Loading States

**Page Load Sequence**:
1. Show skeleton loaders for all sections (200ms)
2. Load KPI cards first (critical content)
3. Load charts progressively (top to bottom)
4. Fade in content as it loads

**Skeleton Design**:
```
┌─────────────────────────────────────┐
│ ┌────┐               ▄▄▄▄▄▄        │
│ │ ▄▄ │                              │
│ └────┘                              │
│                                     │
│ ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄                   │
│ ▄▄▄▄▄▄▄▄▄▄▄▄                       │
│ ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄        │
│ ▄▄▄▄▄▄▄▄▄▄▄                        │
└─────────────────────────────────────┘
```

### 7.2 Empty States

**No Data Available**:
```
┌─────────────────────────────────────┐
│                                     │
│              📊                     │
│                                     │
│      No analytics data yet          │
│                                     │
│   Generate your first report to     │
│   start seeing insights here.       │
│                                     │
│      [Generate Report]              │
│                                     │
└─────────────────────────────────────┘
```

**No Results for Filter**:
```
┌─────────────────────────────────────┐
│              🔍                     │
│                                     │
│   No data matches your filters      │
│                                     │
│   Try adjusting your date range or  │
│   report type selection.            │
│                                     │
│      [Reset Filters]                │
└─────────────────────────────────────┘
```

### 7.3 Error States

**API Error**:
```
┌─────────────────────────────────────┐
│              ⚠️                     │
│                                     │
│   Unable to load analytics data     │
│                                     │
│   Please try again or contact       │
│   support if the issue persists.    │
│                                     │
│   [Retry]     [Contact Support]     │
└─────────────────────────────────────┘
```

**Partial Load Error**:
- Show successfully loaded sections
- Display error banner at top
- Allow retry for failed sections only

### 7.4 Success Feedback

**Filter Applied**:
- Toast notification: "Filters applied successfully"
- Smooth transition of chart updates
- Loading spinner during data fetch

**Export Completed**:
- Toast notification: "Dashboard exported as PDF"
- Download starts automatically
- Option to view in new tab

### 7.5 Micro-interactions

**Hover Effects**:
- KPI Cards: Lift + shadow increase (transform: translateY(-4px))
- Chart points: Scale up + show detailed tooltip
- Buttons: Background color darken + scale(1.02)
- Links: Underline animation from left to right

**Click Feedback**:
- Button press: Scale down (scale: 0.98) for 100ms
- Card click: Ripple effect from click point
- Toggle switches: Smooth slide animation (200ms)

**Transitions**:
- Chart data updates: 800ms ease-in-out
- Filter panel open/close: 300ms slide
- Modal open: 250ms fade + scale from 0.95 to 1.0

---

## 8. Responsive Design Strategy

### 8.1 Breakpoints

```css
/* Mobile First Approach */
--mobile: 0px;        /* Default */
--tablet: 768px;      /* @media (min-width: 768px) */
--desktop: 1024px;    /* @media (min-width: 1024px) */
--wide: 1280px;       /* @media (min-width: 1280px) */
--ultra: 1536px;      /* @media (min-width: 1536px) */
```

### 8.2 Component Adaptations

**KPI Cards**:
- Mobile: Full width, stacked vertically
- Tablet: 2 per row (50% width)
- Desktop: 3 per row (33.33% width)
- Ultra: 4 per row (25% width) if more than 6 cards

**Charts**:
- Mobile: Full width, reduced height (300px)
- Tablet: Full width, standard height (400px)
- Desktop: 50% width, standard height (side by side)

**Tables**:
- Mobile: Card layout (vertical stack per row)
- Tablet: Horizontal scroll if needed
- Desktop: Full table display

**Filters Panel**:
- Mobile: Full-screen overlay modal
- Tablet: Slide-in panel from right (300px width)
- Desktop: Inline sidebar or dropdown

### 8.3 Touch Optimization

**Mobile Interactions**:
- Minimum touch target: 44x44px
- Increased spacing between interactive elements
- Swipe gestures for chart time periods
- Pull-to-refresh for data reload

**Chart Interactions**:
- Touch-optimized tooltips (larger hit area)
- Pinch-to-zoom for detailed view
- Swipe to navigate time periods

---

## 9. Implementation Roadmap

### Phase 1: Foundation (Week 1)
**Priority: CRITICAL**

**Tasks**:
1. Set up page structure and routing
2. Create base layout components
3. Implement global filters context
4. Set up React Query for data fetching
5. Create skeleton loaders for all sections

**Deliverables**:
- ✅ Analytics page route (`/analytics`)
- ✅ Layout grid system
- ✅ Filter context and state management
- ✅ Loading states for all components

---

### Phase 2: KPI Cards (Week 1-2)
**Priority: CRITICAL**

**Tasks**:
1. Create KPICard component
2. Integrate with dashboard metrics API
3. Implement trend indicators
4. Add sparkline charts (mini trend visualization)
5. Create responsive grid layout

**Components**:
- `KPICard.tsx`
- `TrendIndicator.tsx`
- `Sparkline.tsx`

**API Integration**:
- `/api/v1/analytics/metrics/`

---

### Phase 3: Main Charts (Week 2-3)
**Priority: HIGH**

**Tasks**:
1. Set up Recharts library
2. Create ReportsOverTimeChart (line chart)
3. Create ReportsByTypeChart (donut chart)
4. Create ReportsByStatusChart (horizontal bar)
5. Implement chart interactions and tooltips
6. Add export to image functionality

**Components**:
- `ReportsOverTimeChart.tsx`
- `ReportsByTypeChart.tsx`
- `ReportsByStatusChart.tsx`
- `ChartTooltip.tsx`
- `ChartLegend.tsx`

**API Integration**:
- `/api/v1/analytics/trends/?days=30`
- `/api/v1/analytics/categories/`

---

### Phase 4: User Analytics (Week 3)
**Priority: HIGH**

**Tasks**:
1. Create TopUsersTable component
2. Implement user activity heatmap (optional)
3. Add sorting and filtering
4. Create user detail modal

**Components**:
- `TopUsersTable.tsx`
- `UserActivityHeatmap.tsx` (optional)
- `UserDetailModal.tsx`

**API Integration**:
- `/api/v1/analytics/recent-activity/`
- `/api/v1/analytics/client-performance/`

---

### Phase 5: Cost Analytics (Week 4)
**Priority: MEDIUM**

**Tasks**:
1. Create CostInsightsCard component
2. Implement CostTrendsChart (area chart)
3. Create TopCostCategoriesChart (horizontal bar)
4. Add cost-specific filters

**Components**:
- `CostInsightsCard.tsx`
- `CostTrendsChart.tsx`
- `TopCostCategoriesChart.tsx`

**API Integration**:
- Create new endpoint: `/api/v1/analytics/cost-insights/`

---

### Phase 6: System Health (Week 4)
**Priority: MEDIUM (Admin only)**

**Tasks**:
1. Create SystemHealthDashboard component
2. Implement GaugeChart component
3. Add performance metrics table
4. Implement role-based visibility

**Components**:
- `SystemHealthDashboard.tsx`
- `GaugeChart.tsx`
- `PerformanceMetricsTable.tsx`

**API Integration**:
- Create new endpoint: `/api/v1/analytics/system-health/`

---

### Phase 7: Filters & Export (Week 5)
**Priority: HIGH**

**Tasks**:
1. Create comprehensive filters panel
2. Implement date range picker
3. Add export to PDF functionality
4. Add export to CSV functionality
5. Implement URL state persistence

**Components**:
- `AnalyticsFilters.tsx`
- `DateRangePicker.tsx`
- `ExportMenu.tsx`

**Libraries**:
- `react-datepicker` or `date-fns`
- `jspdf` + `html2canvas` for PDF export
- `papaparse` for CSV export

---

### Phase 8: Polish & Optimization (Week 5-6)
**Priority: MEDIUM**

**Tasks**:
1. Add animations and transitions
2. Implement error boundaries
3. Add accessibility features (ARIA labels, keyboard nav)
4. Optimize chart rendering performance
5. Add data refresh mechanisms
6. Create comprehensive loading states
7. Add empty states for all sections
8. Implement responsive design refinements

**Testing**:
- Cross-browser testing
- Mobile device testing
- Performance testing (Lighthouse)
- Accessibility audit (axe DevTools)

---

### Phase 9: Advanced Features (Week 6+)
**Priority: LOW (Nice to have)**

**Tasks**:
1. Add drill-down capabilities (click chart to filter)
2. Implement dashboard customization (drag & drop)
3. Add scheduled report emails
4. Create dashboard templates
5. Add comparison mode (period over period)
6. Implement real-time updates (WebSockets)

---

## 10. Technical Stack

### 10.1 Core Technologies

**Frontend Framework**:
- React 18+ with TypeScript
- React Router v6 for routing

**State Management**:
- React Query (TanStack Query) for server state
- Zustand or Context API for client state

**UI Components**:
- shadcn/ui components (Button, Card, Select, etc.)
- Custom components built on Radix UI primitives

**Styling**:
- TailwindCSS 3.x
- CSS Modules for component-specific styles
- Framer Motion for animations

**Charts & Data Visualization**:
```json
{
  "recharts": "^2.10.0",
  "react-chartjs-2": "^5.2.0" // Alternative
}
```

**Date & Time**:
```json
{
  "date-fns": "^3.0.0",
  "react-datepicker": "^4.21.0"
}
```

**Export Functionality**:
```json
{
  "jspdf": "^2.5.1",
  "html2canvas": "^1.4.1",
  "papaparse": "^5.4.1"
}
```

**Icons**:
```json
{
  "react-icons": "^5.0.0"
}
```

**HTTP Client**:
```json
{
  "axios": "^1.6.0"
}
```

### 10.2 Development Tools

**Code Quality**:
- ESLint + Prettier
- TypeScript strict mode
- Husky for pre-commit hooks

**Testing**:
- Jest + React Testing Library
- Cypress for E2E testing
- Storybook for component development

**Performance Monitoring**:
- React DevTools Profiler
- Chrome Lighthouse
- Bundle analyzer

---

## 11. Accessibility Standards

### 11.1 WCAG 2.1 AA Compliance

**Color Contrast**:
- Text: Minimum 4.5:1 contrast ratio
- Large text (18pt+): Minimum 3.0:1 contrast ratio
- UI components: Minimum 3.0:1 contrast ratio

**Keyboard Navigation**:
- All interactive elements keyboard accessible
- Visible focus indicators (2px outline)
- Logical tab order
- Skip links for main content

**Screen Reader Support**:
- Semantic HTML elements
- ARIA labels for complex widgets
- ARIA live regions for dynamic content
- Alt text for icons and images

**Responsive & Zoom**:
- Support up to 200% zoom without loss of functionality
- No horizontal scrolling at standard zoom levels
- Touch targets minimum 44x44px

### 11.2 Component-Level Accessibility

**KPI Cards**:
```tsx
<div
  role="article"
  aria-labelledby="kpi-title-1"
  aria-describedby="kpi-value-1"
>
  <h3 id="kpi-title-1">Total Reports Generated</h3>
  <p id="kpi-value-1">1,247</p>
  <span aria-label="Trend: up 12.5% compared to last month">
    ↑ 12.5%
  </span>
</div>
```

**Charts**:
```tsx
<div role="img" aria-label="Line chart showing reports generated over time">
  <ResponsiveContainer>
    <LineChart data={data} accessibilityLayer>
      {/* Chart content */}
    </LineChart>
  </ResponsiveContainer>
  <table className="sr-only">
    {/* Data table for screen readers */}
  </table>
</div>
```

**Filters**:
```tsx
<form
  role="search"
  aria-label="Filter analytics data"
  onSubmit={handleApplyFilters}
>
  <label htmlFor="date-range">Date Range</label>
  <select id="date-range" aria-describedby="date-range-help">
    <option value="7d">Last 7 days</option>
  </select>
  <span id="date-range-help" className="sr-only">
    Select a time period to filter the analytics data
  </span>
</form>
```

---

## 12. Performance Optimization

### 12.1 Loading Performance

**Code Splitting**:
```typescript
// Lazy load analytics page
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'));

// Lazy load chart components
const ReportsOverTimeChart = lazy(() =>
  import('./components/charts/ReportsOverTimeChart')
);
```

**Data Fetching Optimization**:
```typescript
// Parallel requests on page load
const useAnalyticsData = () => {
  const metricsQuery = useQuery(['metrics'], fetchMetrics);
  const trendsQuery = useQuery(['trends'], fetchTrends);
  const categoriesQuery = useQuery(['categories'], fetchCategories);

  return {
    isLoading: metricsQuery.isLoading || trendsQuery.isLoading,
    data: {
      metrics: metricsQuery.data,
      trends: trendsQuery.data,
      categories: categoriesQuery.data
    }
  };
};
```

**Image Optimization**:
- Use WebP format for images
- Lazy load images below the fold
- Implement blur-up placeholder technique

### 12.2 Runtime Performance

**React Optimization**:
```typescript
// Memoize expensive calculations
const chartData = useMemo(() =>
  transformDataForChart(rawData),
  [rawData]
);

// Memoize callback functions
const handleChartClick = useCallback((data) => {
  setSelectedData(data);
}, []);

// Memoize components
export default React.memo(KPICard);
```

**Virtual Scrolling**:
```typescript
// For large tables (100+ rows)
import { useVirtualizer } from '@tanstack/react-virtual';

const TableWithVirtualization = ({ data }) => {
  const rowVirtualizer = useVirtualizer({
    count: data.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
  });

  // Render only visible rows
};
```

**Debouncing & Throttling**:
```typescript
// Debounce filter changes
const debouncedFilter = useMemo(
  () => debounce(applyFilters, 300),
  []
);

// Throttle chart hover events
const throttledHover = useMemo(
  () => throttle(handleChartHover, 100),
  []
);
```

### 12.3 Bundle Size

**Target Metrics**:
- Initial bundle: < 200KB gzipped
- Analytics page chunk: < 150KB gzipped
- Chart library: < 100KB gzipped

**Optimization Strategies**:
- Tree-shaking unused code
- Dynamic imports for charts
- Use lightweight alternatives when possible
- Analyze bundle with webpack-bundle-analyzer

---

## 13. Testing Strategy

### 13.1 Unit Tests

**Test Coverage Target: 80%+**

**Example Tests**:
```typescript
describe('KPICard', () => {
  it('displays metric value correctly', () => {
    render(<KPICard title="Total Reports" value="1,247" icon={<Icon />} />);
    expect(screen.getByText('1,247')).toBeInTheDocument();
  });

  it('shows positive trend indicator', () => {
    render(<KPICard {...props} trend={{ value: 12.5 }} />);
    expect(screen.getByText(/↑.*12\.5%/)).toBeInTheDocument();
  });

  it('renders loading state', () => {
    render(<KPICard {...props} loading={true} />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});
```

### 13.2 Integration Tests

**Example: Filter Application**:
```typescript
describe('Analytics Filters', () => {
  it('updates charts when filters are applied', async () => {
    render(<AnalyticsPage />);

    // Change date range
    await userEvent.selectOptions(
      screen.getByLabelText('Date Range'),
      '7d'
    );

    // Apply filters
    await userEvent.click(screen.getByText('Apply Filters'));

    // Verify API called with correct params
    await waitFor(() => {
      expect(mockApi.getTrends).toHaveBeenCalledWith({ days: 7 });
    });

    // Verify chart updated
    expect(screen.getByRole('img', { name: /line chart/i }))
      .toBeInTheDocument();
  });
});
```

### 13.3 E2E Tests (Cypress)

**Example: Complete User Flow**:
```typescript
describe('Analytics Dashboard', () => {
  it('loads and displays all sections', () => {
    cy.visit('/analytics');

    // Verify KPI cards loaded
    cy.findByText('Total Reports Generated').should('be.visible');
    cy.findByText(/\d+/).should('be.visible');

    // Verify charts rendered
    cy.get('[data-testid="reports-over-time-chart"]').should('exist');
    cy.get('[data-testid="reports-by-type-chart"]').should('exist');

    // Test interaction
    cy.findByText('30d').click();
    cy.findByText('Apply Filters').click();

    // Verify data updated
    cy.wait('@analyticsRequest');
    cy.get('[data-testid="reports-over-time-chart"]')
      .should('contain', 'Last 30 days');
  });

  it('exports dashboard as PDF', () => {
    cy.visit('/analytics');

    cy.findByText('Export').click();
    cy.findByText('Export as PDF').click();

    // Verify download started
    cy.readFile('cypress/downloads/analytics-dashboard.pdf')
      .should('exist');
  });
});
```

---

## 14. Design Specifications Summary

### 14.1 Quick Reference

**Component Count**: 15+ new components
**API Endpoints**: 8 endpoints (7 existing + 1 new)
**Charts**: 6 different chart types
**Responsive Breakpoints**: 5 (mobile, tablet, desktop, wide, ultra)
**Color Palette**: 40+ colors (including shades)
**Animations**: 10+ micro-interactions

### 14.2 File Structure

```
frontend/src/
├── pages/
│   └── AnalyticsPage.tsx                 // Main page (500 lines)
├── components/
│   ├── analytics/
│   │   ├── KPICard.tsx                   // (150 lines)
│   │   ├── KPIGrid.tsx                   // (80 lines)
│   │   ├── AnalyticsFilters.tsx          // (250 lines)
│   │   ├── ExportMenu.tsx                // (150 lines)
│   │   ├── EmptyState.tsx                // (80 lines)
│   │   └── ErrorState.tsx                // (80 lines)
│   ├── charts/
│   │   ├── ReportsOverTimeChart.tsx      // (300 lines)
│   │   ├── ReportsByTypeChart.tsx        // (200 lines)
│   │   ├── ReportsByStatusChart.tsx      // (150 lines)
│   │   ├── CostTrendsChart.tsx           // (250 lines)
│   │   ├── TopCostCategoriesChart.tsx    // (180 lines)
│   │   ├── GaugeChart.tsx                // (200 lines)
│   │   ├── ChartTooltip.tsx              // (100 lines)
│   │   └── ChartLegend.tsx               // (100 lines)
│   ├── tables/
│   │   ├── TopUsersTable.tsx             // (250 lines)
│   │   └── PerformanceMetricsTable.tsx   // (150 lines)
│   └── cards/
│       ├── CostInsightsCard.tsx          // (200 lines)
│       └── SystemHealthCard.tsx          // (180 lines)
├── hooks/
│   ├── useAnalytics.ts                   // (150 lines)
│   ├── useAnalyticsFilters.ts            // (100 lines)
│   └── useChartData.ts                   // (120 lines)
├── services/
│   └── analyticsService.ts               // (Existing - extend)
├── types/
│   └── analytics.types.ts                // (200 lines)
└── utils/
    ├── chartHelpers.ts                   // (150 lines)
    ├── dateHelpers.ts                    // (100 lines)
    └── exportHelpers.ts                  // (200 lines)
```

**Total Estimated Lines of Code**: ~4,500 lines

---

## 15. Success Criteria

### 15.1 Functional Requirements

✅ **Must Have**:
- [ ] Display 6 KPI cards with real-time data
- [ ] Show 3+ interactive charts
- [ ] Implement comprehensive filtering system
- [ ] Export to PDF and CSV
- [ ] Mobile responsive (full feature parity)
- [ ] Loading states for all async operations
- [ ] Error handling with retry mechanisms
- [ ] WCAG 2.1 AA accessibility compliance

🎯 **Should Have**:
- [ ] Cost analytics section
- [ ] Top users table
- [ ] System health dashboard (admin)
- [ ] Chart interactions (click, hover, zoom)
- [ ] URL state persistence
- [ ] Auto-refresh capability

💡 **Nice to Have**:
- [ ] User activity heatmap
- [ ] Drill-down capabilities
- [ ] Dashboard customization
- [ ] Real-time updates (WebSockets)
- [ ] Scheduled email reports

### 15.2 Performance Requirements

| Metric | Target | Critical |
|--------|--------|----------|
| First Contentful Paint (FCP) | < 1.5s | < 2.5s |
| Time to Interactive (TTI) | < 3s | < 5s |
| Largest Contentful Paint (LCP) | < 2.5s | < 4s |
| Cumulative Layout Shift (CLS) | < 0.1 | < 0.25 |
| Chart Render Time | < 500ms | < 1s |
| Filter Apply Time | < 300ms | < 800ms |

### 15.3 Quality Requirements

**Code Quality**:
- TypeScript strict mode enabled
- ESLint: 0 errors
- Test coverage: > 80%
- Bundle size: < 200KB gzipped

**Design Quality**:
- Consistent spacing (8px grid)
- Color contrast ratios meet WCAG AA
- Responsive at all breakpoints
- Cross-browser compatible (Chrome, Firefox, Safari, Edge)

**User Experience**:
- No layout shift during load
- Smooth animations (60fps)
- Clear error messages
- Intuitive navigation

---

## Conclusion

This design specification provides a comprehensive blueprint for building a world-class Analytics Dashboard that rivals enterprise products like Power BI and Tableau. The design balances visual impact with usability, performance with features, and complexity with maintainability.

**Key Differentiators**:
1. **Azure-branded Design**: Consistent with Microsoft's design language
2. **Performance-First**: Sub-second load times with intelligent caching
3. **Mobile-Optimized**: Full feature parity on all devices
4. **Accessibility**: WCAG 2.1 AA compliant from day one
5. **Scalability**: Modular architecture for easy extension

**Next Steps**:
1. Review and approve this specification
2. Set up development environment
3. Begin Phase 1 implementation (Foundation)
4. Schedule regular design reviews
5. Conduct user testing after Phase 3

---

**Document Version**: 1.0
**Last Updated**: 2025-10-25
**Author**: Claude (Senior UX/UI Designer)
**Status**: Ready for Implementation
