# Dashboard Visualization Guide
**Azure Advisor Reports Platform**

Quick reference for frontend developers implementing the analytics dashboard.

---

## 1. Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Header (Logo, Navigation, User Profile)                     │
├────┬────────────────────────────────────────────────────────┤
│    │  DASHBOARD                                              │
│    │                                                         │
│ S  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐              │
│ I  │  │  📊  │  │  💰  │  │  👥  │  │  📈  │              │
│ D  │  │ 1,234│  │$50.2K│  │  45  │  │  89  │  Metric Cards│
│ E  │  │Recomm│  │Saving│  │Client│  │Report│              │
│ B  │  └──────┘  └──────┘  └──────┘  └──────┘              │
│ A  │                                                         │
│ R  │  ┌────────────────┐  ┌────────────────┐               │
│    │  │                │  │                │               │
│    │  │  Category Pie  │  │ Impact Bar     │ Charts Row 1 │
│    │  │     Chart      │  │    Chart       │               │
│    │  │                │  │                │               │
│    │  └────────────────┘  └────────────────┘               │
│    │                                                         │
│    │  ┌─────────────────────────────────────┐               │
│    │  │                                     │               │
│    │  │     Savings Trend Line Chart        │ Charts Row 2 │
│    │  │                                     │               │
│    │  └─────────────────────────────────────┘               │
│    │                                                         │
│    │  ┌─────────────────────────────────────┐               │
│    │  │  Top 10 Recommendations Table       │               │
│    │  │  (sortable, expandable)             │ Data Table   │
│    │  └─────────────────────────────────────┘               │
└────┴─────────────────────────────────────────────────────────┘
```

---

## 2. Metric Cards

### Component Structure

```typescript
interface MetricCardProps {
  title: string;
  value: number | string;
  change?: number;  // percentage change
  trend?: 'up' | 'down' | 'neutral';
  sparkline?: number[];  // 7-day data
  icon: string;  // icon name
  color: string;  // theme color
  loading?: boolean;
}
```

### Visual Design

```
┌──────────────────────────┐
│  📊  Total Recommendations│
│                          │
│      1,234              │ ← Large value (48px)
│      ▲ 15.3%           │ ← Trend (green if up)
│      ▬▬▬▬▬▬▬          │ ← Sparkline
└──────────────────────────┘
```

### Color Scheme

```javascript
const metricColors = {
  recommendations: {
    icon: 'FileText',
    color: 'blue',
    background: 'bg-blue-50',
    text: 'text-blue-600',
    border: 'border-blue-200'
  },
  savings: {
    icon: 'DollarSign',
    color: 'green',
    background: 'bg-green-50',
    text: 'text-green-600',
    border: 'border-green-200'
  },
  clients: {
    icon: 'Users',
    color: 'purple',
    background: 'bg-purple-50',
    text: 'text-purple-600',
    border: 'border-purple-200'
  },
  reports: {
    icon: 'TrendingUp',
    color: 'orange',
    background: 'bg-orange-50',
    text: 'text-orange-600',
    border: 'border-orange-200'
  }
};
```

### Implementation Example

```tsx
import { FileText, TrendingUp, TrendingDown, Minus } from 'lucide-react';

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  trend,
  icon,
  color
}) => {
  const IconComponent = iconMap[icon];
  const TrendIcon = trend === 'up' ? TrendingUp :
                    trend === 'down' ? TrendingDown : Minus;

  return (
    <div className={`p-6 bg-white rounded-lg shadow-sm border border-${color}-200`}>
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-gray-600">{title}</span>
        <IconComponent className={`w-5 h-5 text-${color}-600`} />
      </div>

      <div className="text-3xl font-bold text-gray-900 mb-2">
        {value.toLocaleString()}
      </div>

      {change !== undefined && (
        <div className={`flex items-center text-sm ${
          trend === 'up' ? 'text-green-600' :
          trend === 'down' ? 'text-red-600' :
          'text-gray-600'
        }`}>
          <TrendIcon className="w-4 h-4 mr-1" />
          <span>{Math.abs(change)}%</span>
          <span className="ml-2 text-gray-500">vs last period</span>
        </div>
      )}
    </div>
  );
};
```

---

## 3. Category Pie Chart

### Data Format

```javascript
const categoryData = {
  data: [
    {
      name: 'Cost',
      value: 45,
      color: '#10b981',  // green-500
      savings: 12500,
      percentage: 35
    },
    {
      name: 'Security',
      value: 30,
      color: '#ef4444',  // red-500
      savings: 0,
      percentage: 25
    },
    {
      name: 'Reliability',
      value: 20,
      color: '#3b82f6',  // blue-500
      savings: 0,
      percentage: 20
    },
    {
      name: 'Performance',
      value: 12,
      color: '#8b5cf6',  // purple-500
      savings: 0,
      percentage: 12
    },
    {
      name: 'Ops Excellence',
      value: 8,
      color: '#f59e0b',  // amber-500
      savings: 0,
      percentage: 8
    }
  ]
};
```

### Color Mapping

```javascript
const CATEGORY_COLORS = {
  'cost': '#10b981',              // Green - money/savings
  'security': '#ef4444',          // Red - alerts/danger
  'reliability': '#3b82f6',       // Blue - trust/stability
  'performance': '#8b5cf6',       // Purple - optimization
  'operational_excellence': '#f59e0b'  // Amber - quality
};
```

### Implementation

```tsx
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const CategoryPieChart: React.FC<{ data: CategoryData[] }> = ({ data }) => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <h3 className="text-lg font-semibold mb-4">
        Recommendations by Category
      </h3>

      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={100}
            label={({ name, percentage }) => `${name}: ${percentage}%`}
          >
            {data.map((entry, index) => (
              <Cell key={index} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload[0]) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-3 shadow-lg rounded border">
                    <p className="font-semibold">{data.name}</p>
                    <p className="text-sm">Count: {data.value}</p>
                    <p className="text-sm">Percentage: {data.percentage}%</p>
                    {data.savings > 0 && (
                      <p className="text-sm text-green-600">
                        Savings: ${data.savings.toLocaleString()}
                      </p>
                    )}
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
```

---

## 4. Savings Trend Chart

### Data Format

```javascript
const trendData = {
  period: '30d',  // 7d, 30d, 90d
  data: [
    {
      date: '2025-09-01',
      savings: 5000,
      recommendations: 12
    },
    {
      date: '2025-09-02',
      savings: 7500,
      recommendations: 18
    },
    // ... 30 days of data
  ]
};
```

### Implementation

```tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
         Legend, ResponsiveContainer } from 'recharts';

const SavingsTrendChart: React.FC<{ data: TrendData[] }> = ({ data }) => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Savings Trend</h3>

        {/* Period selector */}
        <div className="flex gap-2">
          <button className="px-3 py-1 text-sm rounded bg-blue-100 text-blue-700">
            7D
          </button>
          <button className="px-3 py-1 text-sm rounded hover:bg-gray-100">
            30D
          </button>
          <button className="px-3 py-1 text-sm rounded hover:bg-gray-100">
            90D
          </button>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric'
            })}
          />
          <YAxis
            yAxisId="left"
            label={{ value: 'Savings ($)', angle: -90, position: 'insideLeft' }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            label={{ value: 'Recommendations', angle: 90, position: 'insideRight' }}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                return (
                  <div className="bg-white p-3 shadow-lg rounded border">
                    <p className="font-semibold">
                      {new Date(payload[0].payload.date).toLocaleDateString()}
                    </p>
                    <p className="text-sm text-green-600">
                      Savings: ${payload[0].value?.toLocaleString()}
                    </p>
                    <p className="text-sm text-blue-600">
                      Recommendations: {payload[1].value}
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="savings"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="recommendations"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
```

---

## 5. Impact Bar Chart

### Data Format

```javascript
const impactData = [
  {
    impact: 'High',
    count: 25,
    percentage: 35,
    avgSavings: 1800,
    color: '#ef4444'  // red
  },
  {
    impact: 'Medium',
    count: 35,
    percentage: 45,
    avgSavings: 850,
    color: '#f59e0b'  // amber
  },
  {
    impact: 'Low',
    count: 15,
    percentage: 20,
    avgSavings: 200,
    color: '#10b981'  // green
  }
];
```

### Implementation

```tsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
         Legend, ResponsiveContainer, Cell } from 'recharts';

const ImpactBarChart: React.FC<{ data: ImpactData[] }> = ({ data }) => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <h3 className="text-lg font-semibold mb-4">
        Recommendations by Impact Level
      </h3>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="impact" />
          <YAxis label={{ value: 'Count', angle: -90, position: 'insideLeft' }} />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload[0]) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-3 shadow-lg rounded border">
                    <p className="font-semibold">{data.impact} Impact</p>
                    <p className="text-sm">Count: {data.count}</p>
                    <p className="text-sm">Percentage: {data.percentage}%</p>
                    <p className="text-sm text-green-600">
                      Avg Savings: ${data.avgSavings.toLocaleString()}
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Bar dataKey="count" radius={[8, 8, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={index} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
```

---

## 6. Advisor Score Gauge

### Data Format

```javascript
const advisorScoreData = {
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
};
```

### Implementation

```tsx
import { RadialBarChart, RadialBar, Legend, ResponsiveContainer } from 'recharts';

const AdvisorScoreGauge: React.FC<{ data: AdvisorScoreData }> = ({ data }) => {
  const gaugeData = [
    {
      name: 'Current Score',
      score: data.currentScore,
      fill: '#3b82f6'
    },
    {
      name: 'Potential Score',
      score: data.potentialScore,
      fill: '#10b981'
    }
  ];

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-blue-600';
    if (score >= 60) return 'text-amber-600';
    return 'text-red-600';
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <h3 className="text-lg font-semibold mb-4">Azure Advisor Score</h3>

      <div className="relative">
        <ResponsiveContainer width="100%" height={250}>
          <RadialBarChart
            innerRadius="60%"
            outerRadius="90%"
            data={gaugeData}
            startAngle={180}
            endAngle={0}
          >
            <RadialBar
              background
              dataKey="score"
              cornerRadius={10}
            />
          </RadialBarChart>
        </ResponsiveContainer>

        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className={`text-4xl font-bold ${getScoreColor(data.currentScore)}`}>
            {data.currentScore.toFixed(1)}
          </div>
          <div className="text-sm text-gray-500">out of 100</div>
          <div className="text-sm text-green-600 mt-1">
            +{data.improvement.toFixed(1)} potential
          </div>
        </div>
      </div>

      {/* Category breakdown */}
      <div className="mt-4 space-y-2">
        {Object.entries(data.categoryScores).map(([category, score]) => (
          <div key={category} className="flex items-center justify-between">
            <span className="text-sm capitalize">{category}</span>
            <div className="flex items-center gap-2">
              <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 transition-all"
                  style={{ width: `${score}%` }}
                />
              </div>
              <span className="text-sm font-medium w-10 text-right">
                {score}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

## 7. Filters Panel

### Component Structure

```tsx
interface FiltersProps {
  dateRange: [Date, Date];
  onDateRangeChange: (range: [Date, Date]) => void;
  selectedClients: string[];
  onClientChange: (clients: string[]) => void;
  selectedCategories: string[];
  onCategoryChange: (categories: string[]) => void;
  selectedImpacts: string[];
  onImpactChange: (impacts: string[]) => void;
}
```

### Implementation

```tsx
const DashboardFilters: React.FC<FiltersProps> = ({
  dateRange,
  onDateRangeChange,
  selectedCategories,
  onCategoryChange
}) => {
  const presetRanges = [
    { label: '7 Days', days: 7 },
    { label: '30 Days', days: 30 },
    { label: '90 Days', days: 90 },
    { label: 'YTD', days: 'ytd' }
  ];

  const categories = [
    { value: 'cost', label: 'Cost', color: 'green' },
    { value: 'security', label: 'Security', color: 'red' },
    { value: 'reliability', label: 'Reliability', color: 'blue' },
    { value: 'performance', label: 'Performance', color: 'purple' },
    { value: 'operational_excellence', label: 'Ops Excellence', color: 'amber' }
  ];

  return (
    <div className="bg-white p-4 rounded-lg shadow-sm mb-6">
      <div className="flex flex-wrap gap-4 items-center">
        {/* Date range preset buttons */}
        <div className="flex gap-2">
          {presetRanges.map(range => (
            <button
              key={range.label}
              className="px-3 py-1.5 text-sm rounded-md border hover:bg-gray-50"
              onClick={() => {/* Set date range */}}
            >
              {range.label}
            </button>
          ))}
        </div>

        {/* Category checkboxes */}
        <div className="flex gap-3">
          {categories.map(cat => (
            <label key={cat.value} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedCategories.includes(cat.value)}
                onChange={(e) => {
                  if (e.target.checked) {
                    onCategoryChange([...selectedCategories, cat.value]);
                  } else {
                    onCategoryChange(
                      selectedCategories.filter(c => c !== cat.value)
                    );
                  }
                }}
                className="rounded"
              />
              <span className={`text-sm text-${cat.color}-600`}>
                {cat.label}
              </span>
            </label>
          ))}
        </div>

        {/* Export button */}
        <button className="ml-auto px-4 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700">
          Export CSV
        </button>
      </div>
    </div>
  );
};
```

---

## 8. Responsive Breakpoints

```javascript
// Tailwind breakpoints
const breakpoints = {
  sm: '640px',   // Mobile landscape
  md: '768px',   // Tablet
  lg: '1024px',  // Desktop
  xl: '1280px',  // Large desktop
  '2xl': '1536px' // Extra large
};

// Layout adjustments per breakpoint
const layoutConfig = {
  // Mobile (< 640px)
  mobile: {
    metricCards: 'grid-cols-1',  // Stack vertically
    charts: 'grid-cols-1',
    sidebar: 'hidden'  // Collapsible menu
  },

  // Tablet (640px - 1024px)
  tablet: {
    metricCards: 'grid-cols-2',  // 2 columns
    charts: 'grid-cols-1',
    sidebar: 'hidden'  // Hamburger menu
  },

  // Desktop (> 1024px)
  desktop: {
    metricCards: 'grid-cols-4',  // 4 columns
    charts: 'grid-cols-2',       // 2 columns
    sidebar: 'block'             // Always visible
  }
};
```

---

## 9. Loading States

### Skeleton Loaders

```tsx
const MetricCardSkeleton = () => (
  <div className="p-6 bg-white rounded-lg shadow-sm border animate-pulse">
    <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
    <div className="h-8 bg-gray-200 rounded w-3/4 mb-2"></div>
    <div className="h-3 bg-gray-200 rounded w-1/3"></div>
  </div>
);

const ChartSkeleton = () => (
  <div className="p-6 bg-white rounded-lg shadow-sm animate-pulse">
    <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
    <div className="h-64 bg-gray-100 rounded"></div>
  </div>
);
```

### Loading Component

```tsx
const DashboardLoading = () => (
  <div className="space-y-6">
    {/* Metric cards */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {[1, 2, 3, 4].map(i => <MetricCardSkeleton key={i} />)}
    </div>

    {/* Charts */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {[1, 2].map(i => <ChartSkeleton key={i} />)}
    </div>
  </div>
);
```

---

## 10. Error States

```tsx
const ErrorDisplay: React.FC<{ error: Error, retry: () => void }> = ({
  error,
  retry
}) => (
  <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
    <div className="text-red-600 mb-4">
      <AlertCircle className="w-12 h-12 mx-auto mb-2" />
      <h3 className="text-lg font-semibold">Failed to Load Dashboard</h3>
      <p className="text-sm mt-2">{error.message}</p>
    </div>
    <button
      onClick={retry}
      className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
    >
      Try Again
    </button>
  </div>
);
```

---

## Quick Reference: Chart Library Installation

```bash
npm install recharts
npm install lucide-react  # For icons
npm install date-fns      # For date formatting
```

---

**End of Dashboard Visualization Guide**
