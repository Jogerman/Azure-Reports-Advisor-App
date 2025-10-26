# Analytics Dashboard - Detailed Wireframes
**Visual Design Specifications**

---

## Table of Contents
1. [Desktop Layout (1920x1080)](#desktop-layout)
2. [Tablet Layout (768x1024)](#tablet-layout)
3. [Mobile Layout (375x812)](#mobile-layout)
4. [Component States](#component-states)
5. [Interaction Patterns](#interaction-patterns)
6. [Animation Specifications](#animation-specifications)

---

## Desktop Layout (1920x1080)

### Full Page View

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ SIDEBAR (240px)     │  MAIN CONTENT AREA (1680px)                                │
│ ═══════════════════ │ ════════════════════════════════════════════════════════   │
│                     │                                                             │
│ 🏠 Dashboard        │  ┌─────────────────────────────────────────────────────┐   │
│ 👥 Clients          │  │ HEADER (80px)                                       │   │
│ 📊 Reports          │  │ Analytics Dashboard                  [Filters] [⟳] │   │
│ 📈 Analytics ◄      │  │ [Date: Last 30 days ▼]          [Export ▼]         │   │
│ ⚙️  Settings        │  └─────────────────────────────────────────────────────┘   │
│                     │                                                             │
│                     │  ┌─────────────────────────────────────────────────────┐   │
│                     │  │ KPI SECTION (200px height)                          │   │
│                     │  │                                                     │   │
│                     │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │   │
│                     │  │  │ 📄       │  │ 👥       │  │ ✅       │         │   │
│                     │  │  │          │  │          │  │          │         │   │
│                     │  │  │ Reports  │  │ Clients  │  │ Recomm.  │         │   │
│                     │  │  │ 1,247    │  │ 24       │  │ 3,456    │         │   │
│                     │  │  │ ↑ +12.5% │  │ ↑ +4.2%  │  │ ↑ +8.3%  │         │   │
│                     │  │  │ ▁▂▃▅█    │  │ ▁▁▂▄█    │  │ ▂▄▆█▅    │         │   │
│                     │  │  └──────────┘  └──────────┘  └──────────┘         │   │
│                     │  │                                                     │   │
│                     │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │   │
│                     │  │  │ 💰       │  │ ⏱️       │  │ 💾       │         │   │
│                     │  │  │          │  │          │  │          │         │   │
│                     │  │  │ Savings  │  │ Avg Time │  │ Storage  │         │   │
│                     │  │  │ $45.8K   │  │ 23.4s    │  │ 2.3 GB   │         │   │
│                     │  │  │ ↑ +15.7% │  │ ↓ -8.1%  │  │ ↑ +12%   │         │   │
│                     │  │  │ ▁▃▅█▆    │  │ ▆█▅▃▁    │  │ ▂▃▅▆█    │         │   │
│                     │  │  └──────────┘  └──────────┘  └──────────┘         │   │
│                     │  └─────────────────────────────────────────────────────┘   │
│                     │                                                             │
│                     │  ┌──────────────────────────────────────────────────────┐  │
│                     │  │ CHARTS SECTION - ROW 1 (450px height)                │  │
│                     │  │                                                      │  │
│                     │  │  ┌───────────────────────┐  ┌─────────────────────┐ │  │
│                     │  │  │ Reports Over Time     │  │ Reports by Type     │ │  │
│                     │  │  │ [7d][30d][90d] ◄      │  │                     │ │  │
│                     │  │  │ ┌─────────────────┐   │  │       ╱─────╲      │ │  │
│                     │  │  │ │            ╱╲   │   │  │     ╱         ╲    │ │  │
│                     │  │  │ │        ╱───  ╲  │   │  │    │  1,247   │   │ │  │
│                     │  │  │ │    ╱───       ╲ │   │  │    │ reports  │   │ │  │
│                     │  │  │ │╱───             │   │  │     ╲         ╱    │ │  │
│                     │  │  │ └─────────────────┘   │  │       ╲─────╱      │ │  │
│                     │  │  │ ■Cost ■Security      │  │ ●Cost (27%)        │ │  │
│                     │  │  │ ■Perf ■Operations    │  │ ●Security (15%)    │ │  │
│                     │  │  └───────────────────────┘  └─────────────────────┘ │  │
│                     │  └──────────────────────────────────────────────────────┘  │
│                     │                                                             │
│                     │  ┌──────────────────────────────────────────────────────┐  │
│                     │  │ CHARTS SECTION - ROW 2 (350px height)                │  │
│                     │  │                                                      │  │
│                     │  │  ┌───────────────────────┐  ┌─────────────────────┐ │  │
│                     │  │  │ Reports by Status     │  │ Top Active Users    │ │  │
│                     │  │  │                       │  │              [View→]│ │  │
│                     │  │  │ Completed ████ 1,156  │  │ User      Rpts Last│ │  │
│                     │  │  │ Processing█      12   │  │ ◉ John      42  2h │ │  │
│                     │  │  │ Failed   ███     79   │  │ ◉ Jane      38  5h │ │  │
│                     │  │  │                       │  │ ◉ Bob       35  1d │ │  │
│                     │  │  │                       │  │ ◉ Alice     28  1d │ │  │
│                     │  │  │                       │  │ ◉ Charlie   24  2d │ │  │
│                     │  │  └───────────────────────┘  └─────────────────────┘ │  │
│                     │  └──────────────────────────────────────────────────────┘  │
│                     │                                                             │
│                     │  ┌──────────────────────────────────────────────────────┐  │
│                     │  │ COST INSIGHTS SECTION (400px height)                 │  │
│                     │  │                                                      │  │
│                     │  │  ┌───────────────────────┐  ┌─────────────────────┐ │  │
│                     │  │  │ Cost Trends           │  │ Top Cost Categories │ │  │
│                     │  │  │ ┌─────────────────┐   │  │ Compute   ████ 45% │ │  │
│                     │  │  │ │        ╱▔▔▔╲    │   │  │ Storage   ███  28% │ │  │
│                     │  │  │ │      ╱▁▁▁▁▁▁╲   │   │  │ Network   ██   15% │ │  │
│                     │  │  │ │   ╱▁▁▁▁▁▁▁▁▁▁▁  │   │  │ Database  █    8%  │ │  │
│                     │  │  │ │ ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁ │   │  │ Other     ▌    4%  │ │  │
│                     │  │  │ └─────────────────┘   │  │                     │ │  │
│                     │  │  │ Total: $845,230       │  │ Total: $845,230     │ │  │
│                     │  │  │ Savings: $127,450     │  │                     │ │  │
│                     │  │  └───────────────────────┘  └─────────────────────┘ │  │
│                     │  └──────────────────────────────────────────────────────┘  │
│                     │                                                             │
│                     │  ┌──────────────────────────────────────────────────────┐  │
│                     │  │ SYSTEM HEALTH (Admin Only) (280px height)            │  │
│                     │  │ 🔒 Admin Only                                        │  │
│                     │  │                                                      │  │
│                     │  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌────────────────┐  │  │
│                     │  │  │ CPU  │  │ RAM  │  │ API  │  │ Performance    │  │  │
│                     │  │  │ 45%  │  │ 62%  │  │125ms │  │ • Gen: 23.4s   │  │  │
│                     │  │  │  ◐   │  │  ◓   │  │  ◑   │  │ • DB: 2.3GB    │  │  │
│                     │  │  └──────┘  └──────┘  └──────┘  │ • Cache: 87.5% │  │  │
│                     │  │                                │ • Sessions: 24 │  │  │
│                     │  │                                └────────────────┘  │  │
│                     │  └──────────────────────────────────────────────────────┘  │
│                     │                                                             │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Dimensions & Spacing (Desktop)

**Container**:
- Max Width: 1680px (with sidebar) or 1920px (full screen)
- Padding: 32px (left/right), 24px (top/bottom)
- Section Spacing: 32px between major sections

**KPI Cards Grid**:
- Grid: 3 columns
- Gap: 24px
- Card Dimensions: 360px x 180px
- Padding: 24px

**Charts**:
- Two-column Grid: 50% / 50%
- Gap: 24px
- Height: 400px (line charts), 350px (tables), 300px (bar charts)

---

## Tablet Layout (768x1024)

```
┌──────────────────────────────────────────────────┐
│ HEADER (60px)                                    │
│ Analytics Dashboard            [☰]  [⟳] [Share] │
└──────────────────────────────────────────────────┘
│                                                  │
│ ┌────────────────────────────────────────────┐  │
│ │ FILTERS (collapsed)                        │  │
│ │ [Date: Last 30d ▼]  [Type: All ▼]  [More] │  │
│ └────────────────────────────────────────────┘  │
│                                                  │
│ ┌────────────────────────────────────────────┐  │
│ │ KPI CARDS (2 columns)                      │  │
│ │                                            │  │
│ │  ┌───────────┐    ┌───────────┐           │  │
│ │  │ Reports   │    │ Clients   │           │  │
│ │  │ 1,247     │    │ 24        │           │  │
│ │  │ ↑ +12.5%  │    │ ↑ +4.2%   │           │  │
│ │  └───────────┘    └───────────┘           │  │
│ │                                            │  │
│ │  ┌───────────┐    ┌───────────┐           │  │
│ │  │ Recomm.   │    │ Savings   │           │  │
│ │  │ 3,456     │    │ $45.8K    │           │  │
│ │  │ ↑ +8.3%   │    │ ↑ +15.7%  │           │  │
│ │  └───────────┘    └───────────┘           │  │
│ │                                            │  │
│ │  ┌───────────┐    ┌───────────┐           │  │
│ │  │ Avg Time  │    │ Storage   │           │  │
│ │  │ 23.4s     │    │ 2.3 GB    │           │  │
│ │  │ ↓ -8.1%   │    │ ↑ +12%    │           │  │
│ │  └───────────┘    └───────────┘           │  │
│ └────────────────────────────────────────────┘  │
│                                                  │
│ ┌────────────────────────────────────────────┐  │
│ │ Reports Over Time (full width)             │  │
│ │ [7d] [30d] [90d]                           │  │
│ │ ┌────────────────────────────────────────┐ │  │
│ │ │            Chart (350px height)        │ │  │
│ │ └────────────────────────────────────────┘ │  │
│ └────────────────────────────────────────────┘  │
│                                                  │
│ ┌────────────────────────────────────────────┐  │
│ │ Reports by Type (full width)               │  │
│ │ ┌────────────────────────────────────────┐ │  │
│ │ │      Donut Chart (300px height)        │ │  │
│ │ └────────────────────────────────────────┘ │  │
│ └────────────────────────────────────────────┘  │
│                                                  │
│ ┌────────────────────────────────────────────┐  │
│ │ Reports by Status (full width)             │  │
│ │ ┌────────────────────────────────────────┐ │  │
│ │ │    Horizontal Bar (250px height)       │ │  │
│ │ └────────────────────────────────────────┘ │  │
│ └────────────────────────────────────────────┘  │
│                                                  │
│ ┌────────────────────────────────────────────┐  │
│ │ Top Active Users (full width)              │  │
│ │ [View All →]                               │  │
│ │ ◉ John Smith     42    2h ago    Admin    │  │
│ │ ◉ Jane Doe       38    5h ago    Manager  │  │
│ │ ◉ Bob Johnson    35    1d ago    Analyst  │  │
│ └────────────────────────────────────────────┘  │
│                                                  │
│ [Scroll down for more...]                       │
│                                                  │
└──────────────────────────────────────────────────┘
```

### Tablet-Specific Adaptations

**Layout Changes**:
- Single column for charts (stacked)
- 2-column grid for KPI cards
- Filters collapse into dropdowns
- Sidebar converts to hamburger menu

**Touch Optimizations**:
- Minimum touch target: 48x48px
- Increased spacing between interactive elements: 16px
- Larger buttons and controls
- Swipeable charts for time period selection

**Chart Adjustments**:
- Reduced height: 300-350px
- Larger touch points on charts
- Simplified tooltips (tap instead of hover)

---

## Mobile Layout (375x812)

```
┌─────────────────────────────────┐
│ ☰  Analytics Dashboard    ⋮ [⟳] │  ← Header 56px
├─────────────────────────────────┤
│                                 │
│ ┌─────────────────────────────┐ │
│ │ Filters                  ▼  │ │  ← Collapsible
│ └─────────────────────────────┘ │
│                                 │
│ ┌─── Horizontal Scroll ───────→│
│ │┌──────────┐ ┌──────────┐    │ │
│ ││ Reports  │ │ Clients  │    │ │
│ ││ 1,247    │ │ 24       │    │ │
│ ││ ↑ +12.5% │ │ ↑ +4.2%  │    │ │
│ │└──────────┘ └──────────┘    │ │
│ └────────────────────────────── │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ Reports Over Time           │ │
│ │ ← Swipe for period →        │ │
│ │ 30d                          │ │
│ │ ┌─────────────────────────┐ │ │
│ │ │                         │ │ │
│ │ │   Chart (250px)         │ │ │
│ │ │                         │ │ │
│ │ └─────────────────────────┘ │ │
│ └─────────────────────────────┘ │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ Reports by Type             │ │
│ │ ┌─────────────────────────┐ │ │
│ │ │                         │ │ │
│ │ │   Donut (250px)         │ │ │
│ │ │                         │ │ │
│ │ └─────────────────────────┘ │ │
│ │ ● Cost (27%)                │ │
│ │ ● Security (15%)            │ │
│ │ [Show More ▼]               │ │
│ └─────────────────────────────┘ │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ Reports by Status           │ │
│ │ Completed  ████████  1,156  │ │
│ │ Processing ▌            12  │ │
│ │ Failed     ████          79 │ │
│ └─────────────────────────────┘ │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ Top Users         [View →]  │ │
│ │ ┌───────────────────────────┤ │
│ │ │ ◉ John Smith              │ │
│ │ │   42 reports • 2h ago     │ │
│ │ │   Admin                   │ │
│ │ ├───────────────────────────┤ │
│ │ │ ◉ Jane Doe                │ │
│ │ │   38 reports • 5h ago     │ │
│ │ │   Manager                 │ │
│ │ └───────────────────────────│ │
│ │ [Expand for more ▼]         │ │
│ └─────────────────────────────┘ │
│                                 │
│ [Pull to refresh]               │
│                                 │
└─────────────────────────────────┘
```

### Mobile-Specific Features

**Navigation**:
- Hamburger menu for sidebar
- Bottom navigation bar (optional)
- Pull-to-refresh for data reload
- Swipe gestures for chart periods

**KPI Cards**:
- Horizontal scroll container
- Snap to card edges
- Indicators showing position (dots)
- Card size: 280px x 160px

**Charts**:
- Full width (minus padding)
- Reduced height: 250px
- Simplified legends (collapsible)
- Tap-based interactions
- Horizontal scroll for overflow data

**Tables**:
- Card-based layout instead of table
- Stack information vertically
- Expandable rows for details

---

## Component States

### KPI Card States

**1. Loading State**:
```
┌─────────────────────────┐
│ ▄▄▄▄       ▄▄▄▄▄▄      │  ← Shimmer animation
│                         │
│ ▄▄▄▄▄▄▄▄▄▄▄▄           │
│ ▄▄▄▄▄▄▄▄               │
│ ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄    │
│ ▄▄▄▄▄▄▄                │
└─────────────────────────┘
```

**2. Default State**:
```
┌─────────────────────────┐
│ 📄          ↑ +12.5%    │
│                         │
│ Total Reports           │
│ 1,247                   │
│ ▁▂▃▅▄▆▇█               │
│ vs last month           │
└─────────────────────────┘
```

**3. Hover State** (Desktop):
```
┌─────────────────────────┐  ↑ Lifted 4px
│ 📄 ✨       ↑ +12.5%    │  Subtle glow
│                         │  Icon rotates 5°
│ Total Reports           │  Shadow increases
│ 1,247                   │
│ ▁▂▃▅▄▆▇█               │
│ vs last month           │
└─────────────────────────┘
```

**4. Error State**:
```
┌─────────────────────────┐
│          ⚠️             │  Red border
│                         │
│ Unable to load data     │
│                         │
│ [Retry]                 │
│                         │
└─────────────────────────┘
```

**5. Empty State**:
```
┌─────────────────────────┐
│ 📄          --          │
│                         │
│ Total Reports           │
│ 0                       │
│                         │
│ No data available       │
└─────────────────────────┘
```

---

### Chart States

**1. Loading State**:
```
┌───────────────────────────────┐
│ Reports Over Time             │
│ ┌───────────────────────────┐ │
│ │                           │ │
│ │      ⟳ Loading...         │ │
│ │                           │ │
│ │                           │ │
│ └───────────────────────────┘ │
└───────────────────────────────┘
```

**2. Empty State**:
```
┌───────────────────────────────┐
│ Reports Over Time             │
│ ┌───────────────────────────┐ │
│ │         📊                │ │
│ │   No data available       │ │
│ │   for selected period     │ │
│ │   [Change Filters]        │ │
│ └───────────────────────────┘ │
└───────────────────────────────┘
```

**3. Interactive State** (Hover):
```
┌───────────────────────────────┐
│ Reports Over Time             │
│ ┌───────────────────────────┐ │
│ │     •╭──────────────╮    │ │  Tooltip appears
│ │    ╱ │ Jan 15, 2025  │    │ │  Point enlarges
│ │   ╱  │ Total: 45     │    │ │  Crosshair lines
│ │  ╱   │ Cost: 12      │ ⊕  │ │
│ │ ╱    │ Security: 18  │    │ │
│ │      ╰──────────────╯     │ │
│ └───────────────────────────┘ │
└───────────────────────────────┘
```

**4. Zoomed State** (Line Chart):
```
┌───────────────────────────────┐
│ Reports Over Time  [Reset ✕]  │
│ ┌───────────────────────────┐ │
│ │     Zoomed: Jan 15-22     │ │
│ │    ╱╲     ╱╲              │ │
│ │   ╱  ╲   ╱  ╲             │ │
│ │  ╱    ╲ ╱    ╲            │ │
│ │ ╱      ▼      ╲           │ │
│ │ [=================]        │ │  Brush selector
│ └───────────────────────────┘ │
└───────────────────────────────┘
```

---

### Filter Panel States

**1. Collapsed (Desktop)**:
```
┌──────────────────────────────────────┐
│ [Date: Last 30d ▼]  [Type: All ▼]   │
│                      [More Filters]  │
└──────────────────────────────────────┘
```

**2. Expanded (Desktop)**:
```
┌──────────────────────────────────────┐
│ Filters                      [✕]     │
├──────────────────────────────────────┤
│ Date Range                           │
│ ● Last 7 days                        │
│ ◯ Last 30 days                       │
│ ◯ Last 90 days                       │
│ ◯ Custom range                       │
│                                      │
│ Report Type                          │
│ ☑ Cost Optimization                  │
│ ☑ Security                           │
│ ☑ Performance                        │
│ ☑ Operational Excellence             │
│                                      │
│ Status                               │
│ ● All                                │
│ ◯ Completed Only                     │
│ ◯ Exclude Failed                     │
│                                      │
│ [Reset]           [Apply Filters]   │
└──────────────────────────────────────┘
```

**3. Mobile Filters (Modal)**:
```
┌───────────────────────────────┐
│ ✕  Filters          [Apply]   │  ← Full screen
├───────────────────────────────┤
│                               │
│ Date Range                    │
│ [Last 30 days ▼]              │
│                               │
│ Report Type                   │
│ ☑ Cost Optimization           │
│ ☑ Security                    │
│ ☑ Performance                 │
│ ☑ Operational Excellence      │
│                               │
│ Status                        │
│ ● All                         │
│ ◯ Completed Only              │
│ ◯ Exclude Failed              │
│                               │
│                               │
│ ┌───────────────────────────┐ │
│ │ Reset     Apply Filters   │ │  ← Sticky footer
│ └───────────────────────────┘ │
└───────────────────────────────┘
```

---

## Interaction Patterns

### 1. Chart Interactions

**Line Chart Click Behavior**:
```
User Action: Click on data point
┌─────────────────────────────────┐
│ Click point → Show tooltip      │
│ ├─ Display detailed metrics     │
│ ├─ Highlight corresponding bar  │
│ └─ Option to drill down         │
└─────────────────────────────────┘

User Action: Click legend item
┌─────────────────────────────────┐
│ Click legend → Toggle series    │
│ ├─ Hide/show line               │
│ ├─ Update chart scale           │
│ └─ Persist selection            │
└─────────────────────────────────┘

User Action: Drag on chart
┌─────────────────────────────────┐
│ Drag → Create zoom selection    │
│ ├─ Show brush overlay           │
│ ├─ Zoom to selection on release │
│ └─ Show reset button            │
└─────────────────────────────────┘
```

**Donut Chart Click Behavior**:
```
User Action: Click segment
┌─────────────────────────────────┐
│ Click segment → Filter data     │
│ ├─ Highlight segment            │
│ ├─ Apply filter globally        │
│ ├─ Update other charts          │
│ └─ Show "Filtered by X" badge   │
└─────────────────────────────────┘

User Action: Hover segment
┌─────────────────────────────────┐
│ Hover → Expand segment          │
│ ├─ Increase outer radius +10px  │
│ ├─ Show detailed tooltip        │
│ └─ Highlight legend entry       │
└─────────────────────────────────┘
```

---

### 2. Filter Application Flow

```
Step 1: User opens filters
┌──────────────────┐
│ [Open Filters]   │ ──→ Panel slides in (300ms)
└──────────────────┘

Step 2: User selects options
┌──────────────────┐
│ ☑ Change options │ ──→ Update preview count
└──────────────────┘     "~450 results"

Step 3: User applies filters
┌──────────────────┐
│ [Apply Filters]  │ ──→ API call initiated
└──────────────────┘     Show loading overlay

Step 4: Data loads
┌──────────────────┐
│ Loading...       │ ──→ Skeleton loaders
└──────────────────┘     for all sections

Step 5: Charts update
┌──────────────────┐
│ ✓ Applied        │ ──→ Animated transitions
└──────────────────┘     Toast notification
                         "Filters applied"
```

---

### 3. Export Flow

```
User clicks Export button
         ↓
┌──────────────────────┐
│ Export Menu Opens    │
│ ├─ Export as PDF     │ ──→ Generate PDF (3-5s)
│ ├─ Export Data (CSV) │ ──→ Download CSV (instant)
│ ├─ Screenshot        │ ──→ Capture & download (2s)
│ ├─ Email Report      │ ──→ Open email client
│ └─ Share Link        │ ──→ Copy to clipboard
└──────────────────────┘
         ↓
   Toast notification
   "Exported successfully"
         ↓
   File downloads
```

---

## Animation Specifications

### Entry Animations

**Page Load Sequence**:
```
1. Header fades in (0ms, 200ms duration)
   opacity: 0 → 1

2. KPI Cards stagger in (200ms start, 100ms offset each)
   opacity: 0 → 1
   transform: translateY(20px) → translateY(0)

3. Charts fade & slide in (600ms start, 150ms offset each)
   opacity: 0 → 1
   transform: translateY(30px) → translateY(0)

4. Tables fade in (1200ms start)
   opacity: 0 → 1
```

**CSS Implementation**:
```css
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.kpi-card {
  animation: fadeInUp 400ms ease-out forwards;
  animation-delay: calc(var(--index) * 100ms + 200ms);
}

.chart-container {
  animation: fadeInUp 500ms ease-out forwards;
  animation-delay: calc(var(--index) * 150ms + 600ms);
}
```

---

### Hover Animations

**KPI Card Hover**:
```css
.kpi-card {
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

.kpi-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.12);
}

.kpi-card-icon {
  transition: transform 200ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

.kpi-card:hover .kpi-card-icon {
  transform: rotate(5deg) scale(1.1);
}
```

**Chart Line Hover**:
```css
.recharts-line {
  transition: stroke-width 150ms ease-in-out;
}

.recharts-line:hover {
  stroke-width: 4px; /* from 2.5px */
}

.recharts-dot:hover {
  r: 8; /* from 4 */
  transition: r 150ms ease-in-out;
}
```

---

### Transition Animations

**Filter Panel Slide**:
```css
@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.filter-panel {
  animation: slideInRight 300ms cubic-bezier(0.4, 0, 0.2, 1);
}
```

**Chart Data Update**:
```javascript
// Recharts configuration
<LineChart
  data={data}
  isAnimationActive={true}
  animationDuration={800}
  animationEasing="ease-in-out"
>
```

**Loading Shimmer**:
```css
@keyframes shimmer {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
}

.skeleton-loader {
  background: linear-gradient(
    90deg,
    #f0f0f0 0%,
    #f8f8f8 50%,
    #f0f0f0 100%
  );
  background-size: 1000px 100%;
  animation: shimmer 2s infinite linear;
}
```

---

## Summary

This wireframe specification provides:

1. **Detailed Layouts** for Desktop, Tablet, and Mobile
2. **Component State Diagrams** for all major elements
3. **Interaction Flow Diagrams** showing user journey
4. **Animation Specifications** with CSS implementations
5. **Pixel-Perfect Dimensions** for all breakpoints
6. **Touch Optimization** guidelines for mobile/tablet

**Key Features**:
- Responsive design with 3 breakpoints
- Progressive enhancement approach
- Touch-optimized interactions
- Smooth, performant animations
- Consistent spacing and alignment
- Accessible by design

**Usage**:
- Use as reference during implementation
- Share with stakeholders for approval
- Guide for QA testing
- Documentation for future maintenance

---

**Document Version**: 1.0
**Last Updated**: 2025-10-25
**Status**: Ready for Development
