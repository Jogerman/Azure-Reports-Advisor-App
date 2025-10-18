# Loading States - Before & After Examples

## Quick Reference Guide

This document shows before/after comparisons for all updated loading states.

---

## 1. CategoryChart (Pie Chart)

### Before
```tsx
// Simple text with animate-pulse
<div className="w-full h-64 bg-gray-100 rounded-lg animate-pulse flex items-center justify-center">
  <div className="text-gray-400">Loading chart...</div>
</div>
```

**Issues**:
- No ARIA attributes
- Static gray box, not realistic
- No skeleton for summary stats
- Inconsistent with other loading states

### After
```tsx
// Realistic chart skeleton with proper accessibility
<div className="p-6" role="status" aria-busy="true" aria-label="Loading recommendations by category chart">
  <SkeletonLoader variant="text" width="60%" height="24px" className="mb-2" />
  <SkeletonLoader variant="text" width="80%" height="16px" />
  <div className="w-full h-64 flex items-center justify-center">
    <SkeletonLoader variant="circular" width="256px" height="256px" />
  </div>
  <div className="mt-4 grid grid-cols-2 gap-4">
    <div className="text-center space-y-2">
      <SkeletonLoader variant="text" width="40%" height="14px" className="mx-auto" />
      <SkeletonLoader variant="text" width="60%" height="32px" className="mx-auto" />
    </div>
    <div className="text-center space-y-2">
      <SkeletonLoader variant="text" width="40%" height="14px" className="mx-auto" />
      <SkeletonLoader variant="text" width="60%" height="32px" className="mx-auto" />
    </div>
  </div>
</div>
```

**Improvements**:
- ✓ Circular skeleton matches pie chart shape
- ✓ ARIA attributes for accessibility
- ✓ Includes summary statistics skeleton
- ✓ Gradient shimmer animation (1.5s)

---

## 2. TrendChart (Line Chart)

### Before
```tsx
// Simple text with animate-pulse
<div className="w-full h-80 bg-gray-100 rounded-lg animate-pulse flex items-center justify-center">
  <div className="text-gray-400">Loading chart...</div>
</div>
```

**Issues**:
- No skeleton for time range selector
- No ARIA attributes
- Static gray box
- No summary statistics skeleton

### After
```tsx
// Realistic line chart skeleton with controls
<div className="p-6" role="status" aria-busy="true" aria-label="Loading report generation trend chart">
  <div className="flex items-start justify-between mb-4">
    <div className="flex-1">
      <SkeletonLoader variant="text" width="60%" height="24px" className="mb-2" />
      {subtitle && <SkeletonLoader variant="text" width="80%" height="16px" />}
    </div>
    {showTimeRangeSelector && (
      <div className="flex space-x-2">
        <SkeletonLoader variant="rectangular" width="60px" height="32px" />
        <SkeletonLoader variant="rectangular" width="70px" height="32px" />
        <SkeletonLoader variant="rectangular" width="70px" height="32px" />
      </div>
    )}
  </div>
  <div className="w-full h-80 space-y-3">
    {[...Array(6)].map((_, i) => (
      <div key={i} className="flex items-end space-x-2">
        <SkeletonLoader variant="rectangular" width="100%" height={`${30 + Math.random() * 70}%`} />
      </div>
    ))}
  </div>
  <div className="mt-6 grid grid-cols-3 gap-4 pt-4 border-t border-gray-200">
    {[...Array(3)].map((_, i) => (
      <div key={i} className="text-center space-y-2">
        <SkeletonLoader variant="text" width="50%" height="14px" className="mx-auto" />
        <SkeletonLoader variant="text" width="60%" height="28px" className="mx-auto" />
      </div>
    ))}
  </div>
</div>
```

**Improvements**:
- ✓ Bar-like skeletons represent data points
- ✓ Time range selector skeleton (7d, 30d, 90d)
- ✓ Summary statistics skeleton (Total, Average, Peak)
- ✓ Full ARIA support

---

## 3. MetricCard

### Before
```tsx
// Custom animate-pulse implementation
<div className="p-6 animate-pulse">
  <div className="flex items-center justify-between mb-4">
    <div className="w-12 h-12 rounded-lg bg-gray-200" />
    <div className="w-16 h-5 bg-gray-200 rounded" />
  </div>
  <div className="w-24 h-4 bg-gray-200 rounded mb-2" />
  <div className="w-32 h-8 bg-gray-200 rounded" />
</div>
```

**Issues**:
- Using Tailwind's basic `animate-pulse` (simple opacity fade)
- No ARIA attributes
- Inconsistent with SkeletonLoader's gradient shimmer

### After
```tsx
// Standardized with SkeletonLoader
<div className="p-6" role="status" aria-busy="true" aria-label={`Loading ${title} metric`}>
  <div className="flex items-center justify-between mb-4">
    <SkeletonLoader variant="rectangular" width="48px" height="48px" />
    <SkeletonLoader variant="text" width="64px" height="20px" />
  </div>
  <SkeletonLoader variant="text" width="96px" height="16px" className="mb-2" />
  <SkeletonLoader variant="text" width="128px" height="32px" />
</div>
```

**Improvements**:
- ✓ Gradient shimmer animation (vs simple pulse)
- ✓ Dynamic ARIA label with metric title
- ✓ Consistent 1.5s animation timing
- ✓ Matches SkeletonLoader patterns

---

## 4. RecentActivity

### Before
```tsx
// Custom animate-pulse
<div className="space-y-4">
  {[...Array(5)].map((_, index) => (
    <div key={index} className="flex items-start space-x-3 animate-pulse">
      <div className="w-10 h-10 rounded-full bg-gray-200 flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-4 w-3/4 bg-gray-200 rounded" />
        <div className="h-3 w-1/2 bg-gray-200 rounded" />
      </div>
    </div>
  ))}
</div>
```

**Issues**:
- No title/subtitle skeleton
- Simple pulse animation
- No ARIA attributes
- Inconsistent with SkeletonLoader

### After
```tsx
// Standardized with SkeletonLoader
<div className="p-6" role="status" aria-busy="true" aria-label="Loading recent activity">
  <SkeletonLoader variant="text" width="30%" height="24px" className="mb-2" />
  {subtitle && <SkeletonLoader variant="text" width="50%" height="16px" />}
  <div className="space-y-4">
    {[...Array(5)].map((_, index) => (
      <div key={index} className="flex items-start space-x-3">
        <SkeletonLoader variant="circular" width="40px" height="40px" />
        <div className="flex-1 space-y-2">
          <SkeletonLoader variant="text" width="75%" height="16px" />
          <SkeletonLoader variant="text" width="50%" height="12px" />
        </div>
      </div>
    ))}
  </div>
</div>
```

**Improvements**:
- ✓ Title/subtitle skeleton included
- ✓ Gradient shimmer animation
- ✓ Proper ARIA attributes
- ✓ Matches actual activity item layout

---

## 5. LoadingSpinner

### Before
```tsx
// No accessibility attributes
<div className="flex flex-col items-center justify-center space-y-3">
  <motion.div
    animate={{ rotate: 360 }}
    className={`${sizeStyles[size]} border-4 border-gray-200 border-t-azure-600 rounded-full`}
  />
  {text && <p className="text-sm text-gray-600">{text}</p>}
</div>
```

**Issues**:
- No `role` or ARIA attributes
- Spinner not hidden from screen readers
- Text changes not announced

### After
```tsx
// Full accessibility support
<div
  className="flex flex-col items-center justify-center space-y-3"
  role="status"
  aria-busy="true"
  aria-label={text || "Loading"}
>
  <motion.div
    animate={{ rotate: 360 }}
    className={`${sizeStyles[size]} border-4 border-gray-200 border-t-azure-600 rounded-full`}
    aria-hidden="true"
  />
  {text && (
    <p className="text-sm text-gray-600" aria-live="polite">
      {text}
    </p>
  )}
</div>
```

**Improvements**:
- ✓ `role="status"` announces to screen readers
- ✓ `aria-busy="true"` indicates loading
- ✓ `aria-label` provides context
- ✓ `aria-hidden="true"` hides decorative spinner
- ✓ `aria-live="polite"` announces text updates

---

## Animation Comparison

### Tailwind's animate-pulse (OLD)
```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
/* Duration: 2s, cubic-bezier(0.4, 0, 0.6, 1) */
```

**Characteristics**:
- Simple opacity fade
- 2-second duration
- No directional movement
- Static appearance

### SkeletonLoader gradient shimmer (NEW)
```tsx
animate={{ backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'] }}
transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
```

**Characteristics**:
- Gradient moves left-to-right
- 1.5-second duration
- Creates "shimmer" effect
- More engaging visual feedback

---

## Accessibility Comparison

### Before (Inaccessible)
```tsx
<div className="animate-pulse">
  <div className="bg-gray-200 rounded" />
</div>
```

**Screen Reader Experience**:
- "Empty" (no announcement)
- No indication of loading state
- User left wondering what's happening

### After (Accessible)
```tsx
<div role="status" aria-busy="true" aria-label="Loading chart">
  <SkeletonLoader variant="circular" width="256px" height="256px" />
</div>
```

**Screen Reader Experience**:
- "Loading chart, busy" (announced immediately)
- Clear indication that content is loading
- User understands the current state

---

## Usage Decision Tree

```
Is the loading state for...

├─ Full page or modal?
│  └─ Use: LoadingSpinner
│     - Size: lg for pages, md for modals
│     - Include descriptive text prop
│
├─ Card or section content?
│  └─ Use: SkeletonLoader
│     - Match the content layout
│     - Use appropriate variants
│
├─ Chart or visualization?
│  └─ Use: SkeletonLoader
│     - circular for pie charts
│     - rectangular bars for line/bar charts
│
├─ List or table?
│  └─ Use: SkeletonList or SkeletonTable
│     - Pre-built composite components
│
└─ Form submission?
   └─ Use: LoadingSpinner
      - Size: sm inline, md in button
      - Include status text
```

---

## Common Patterns

### Pattern 1: Chart Loading
```tsx
if (loading) {
  return (
    <Card>
      <div className="p-6" role="status" aria-busy="true" aria-label="Loading chart">
        <SkeletonLoader variant="text" width="60%" height="24px" className="mb-2" />
        <SkeletonLoader variant="circular" width="256px" height="256px" />
      </div>
    </Card>
  );
}
```

### Pattern 2: Card Loading
```tsx
if (loading) {
  return (
    <Card>
      <div className="p-6" role="status" aria-busy="true" aria-label={`Loading ${title}`}>
        <SkeletonLoader variant="rectangular" width="48px" height="48px" />
        <SkeletonLoader variant="text" width="80%" height="16px" />
        <SkeletonLoader variant="text" width="60%" height="24px" />
      </div>
    </Card>
  );
}
```

### Pattern 3: List Loading
```tsx
if (loading) {
  return <SkeletonList items={5} />;
}
```

### Pattern 4: Full-Page Loading
```tsx
{isLoading ? (
  <div className="flex justify-center py-12">
    <LoadingSpinner size="lg" text="Loading data..." />
  </div>
) : (
  // Content
)}
```

---

## Testing Checklist

When implementing a new loading state:

- [ ] Visual: Does the skeleton match the content layout?
- [ ] Animation: 1.5s for skeleton, 1s for spinner?
- [ ] ARIA: Does it have `role="status"`?
- [ ] ARIA: Does it have `aria-busy="true"`?
- [ ] ARIA: Does it have a descriptive `aria-label`?
- [ ] Layout: Does it prevent content shift when loading completes?
- [ ] Component: Is it using SkeletonLoader (content) or LoadingSpinner (page/modal)?
- [ ] Responsive: Does it work on mobile, tablet, desktop?

---

## Summary

**Updated**: 6 components with SkeletonLoader patterns
**Verified**: 2 components already using correct patterns
**Created**: Comprehensive documentation and guides

All loading states now provide:
- ✓ Consistent visual appearance
- ✓ Smooth gradient animations
- ✓ Full accessibility support
- ✓ No layout shift
- ✓ Better user experience

**Next Steps**:
1. Review the [LOADING_STATES_GUIDE.md](./LOADING_STATES_GUIDE.md) for detailed usage
2. Read the [LOADING_STATES_STANDARDIZATION_REPORT.md](../LOADING_STATES_STANDARDIZATION_REPORT.md) for technical details
3. Follow the patterns shown in this document for future components
