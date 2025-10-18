# Loading States Standardization Guide

## Overview

This guide documents the standardized loading state patterns used across the Azure Advisor Reports Platform frontend. Consistent loading states improve user experience and accessibility.

## Design Principles

1. **Visual Consistency**: All loading states use the same animation timing (1.5s duration) and styling
2. **Accessibility First**: All loading states include proper ARIA attributes for screen readers
3. **Semantic Usage**: Different components for different use cases
4. **Performance**: Optimized animations using CSS transforms and GPU acceleration

## Component Types

### 1. SkeletonLoader (Content Placeholders)

**Use for**: Cards, lists, charts, tables, and content sections

**Location**: `frontend/src/components/common/SkeletonLoader.tsx`

**When to use**:
- Loading data in cards, tables, or lists
- Showing placeholders for charts and visualizations
- Maintaining page layout during data fetch

**Variants**:
- `text`: Single line text placeholder (height: 16px)
- `rectangular`: Rectangular content blocks (height: 128px default)
- `circular`: Circular avatars or icons (48px diameter)
- `card`: Full card skeleton (height: 192px)

**Props**:
```typescript
interface SkeletonLoaderProps {
  variant?: 'text' | 'circular' | 'rectangular' | 'card';
  width?: string;        // CSS width value (default: '100%')
  height?: string;       // CSS height value (varies by variant)
  className?: string;    // Additional Tailwind classes
}
```

**Accessibility Features**:
- `role="status"` - Announces loading state to screen readers
- `aria-busy="true"` - Indicates content is loading
- `aria-label="Loading"` - Descriptive label for screen readers

**Animation**:
- Gradient shimmer effect (gray-200 → gray-300 → gray-200)
- 1.5s duration, infinite loop, linear easing
- Hardware-accelerated using CSS transforms

### 2. LoadingSpinner (Full-Page/Modal Loading)

**Use for**: Full-page loading, modal dialogs, form submissions

**Location**: `frontend/src/components/common/LoadingSpinner.tsx`

**When to use**:
- Initial page load
- Modal/dialog loading states
- Form submission processing
- Action confirmations

**Props**:
```typescript
interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';  // sm: 16px, md: 32px, lg: 48px
  text?: string;               // Optional loading message
  fullScreen?: boolean;        // Cover entire viewport
}
```

**Sizes**:
- `sm`: 16px × 16px (inline use)
- `md`: 32px × 32px (default)
- `lg`: 48px × 48px (full-page)

**Accessibility Features**:
- `role="status"` - Loading state indicator
- `aria-busy="true"` - Content is loading
- `aria-label={text || "Loading"}` - Screen reader announcement
- `aria-live="polite"` - Non-intrusive updates on text prop
- `aria-hidden="true"` - Hide decorative spinner from screen readers

**Animation**:
- Rotating border animation
- 1s duration, infinite loop, linear easing
- Azure blue accent color (#0078D4)

## Composite Skeleton Components

### SkeletonCard
Pre-built card skeleton with title and content placeholders.

```tsx
<SkeletonCard className="mb-4" />
```

### SkeletonTable
Table skeleton with configurable row count.

```tsx
<SkeletonTable rows={5} />
```

### SkeletonList
List skeleton with avatar + text pattern.

```tsx
<SkeletonList items={10} />
```

## Usage Examples

### Example 1: Chart Loading State

**File**: `CategoryChart.tsx`, `TrendChart.tsx`

```tsx
if (loading) {
  return (
    <Card>
      <div className="p-6" role="status" aria-busy="true" aria-label="Loading chart">
        <SkeletonLoader variant="text" width="60%" height="24px" className="mb-2" />
        <SkeletonLoader variant="text" width="80%" height="16px" className="mb-4" />
        <SkeletonLoader variant="circular" width="256px" height="256px" />
      </div>
    </Card>
  );
}
```

**Why this pattern**:
- Uses `SkeletonLoader` for content placeholders
- Matches the chart's visual structure
- Includes proper ARIA attributes on container
- Maintains layout to prevent content shift

### Example 2: Metric Card Loading

**File**: `MetricCard.tsx`

```tsx
if (loading) {
  return (
    <Card>
      <div className="p-6" role="status" aria-busy="true" aria-label={`Loading ${title} metric`}>
        <div className="flex items-center justify-between mb-4">
          <SkeletonLoader variant="rectangular" width="48px" height="48px" />
          <SkeletonLoader variant="text" width="64px" height="20px" />
        </div>
        <SkeletonLoader variant="text" width="96px" height="16px" className="mb-2" />
        <SkeletonLoader variant="text" width="128px" height="32px" />
      </div>
    </Card>
  );
}
```

**Why this pattern**:
- Mimics the card's actual layout
- Dynamic aria-label uses the metric title
- Prevents layout shift when data loads

### Example 3: Full-Page Loading

**File**: `ReportList.tsx`, `ClientsPage.tsx`

```tsx
{isLoading ? (
  <div className="flex justify-center py-12">
    <LoadingSpinner size="lg" text="Loading reports..." />
  </div>
) : (
  // Content here
)}
```

**Why this pattern**:
- Uses `LoadingSpinner` for full-component loading
- Centers spinner in available space
- Includes descriptive text for context
- Built-in ARIA attributes for accessibility

### Example 4: List/Activity Loading

**File**: `RecentActivity.tsx`

```tsx
if (loading) {
  return (
    <Card>
      <div className="p-6" role="status" aria-busy="true" aria-label="Loading recent activity">
        <SkeletonLoader variant="text" width="30%" height="24px" className="mb-2" />
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
    </Card>
  );
}
```

**Why this pattern**:
- Creates realistic list item placeholders
- Uses array mapping for multiple items
- Circular skeleton for avatars/icons
- Varied widths create natural appearance

## Accessibility Checklist

When implementing loading states, ensure:

- [ ] Container has `role="status"` attribute
- [ ] Container has `aria-busy="true"` attribute
- [ ] Container has descriptive `aria-label`
- [ ] Decorative elements have `aria-hidden="true"`
- [ ] Dynamic text has `aria-live="polite"`
- [ ] Loading state maintains page layout (no content shift)
- [ ] Loading state is visually distinguishable from actual content
- [ ] Loading animations don't cause motion sickness (use `prefers-reduced-motion`)

## Animation Performance

All loading state animations use:

1. **CSS Transforms**: GPU-accelerated for smooth performance
2. **Will-change**: Hints to browser for optimization
3. **RequestAnimationFrame**: Syncs with browser repaint
4. **Framer Motion**: Optimized animation library

### Performance Best Practices

```tsx
// Good: Uses CSS transforms
<motion.div
  animate={{ backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'] }}
  transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
/>

// Good: Uses rotation transform
<motion.div
  animate={{ rotate: 360 }}
  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
/>
```

## Migration Guide

### From Custom Pulse to SkeletonLoader

**Before**:
```tsx
<div className="animate-pulse">
  <div className="h-6 w-48 bg-gray-200 rounded mb-2" />
  <div className="h-4 w-64 bg-gray-200 rounded" />
</div>
```

**After**:
```tsx
<div role="status" aria-busy="true" aria-label="Loading content">
  <SkeletonLoader variant="text" width="192px" height="24px" className="mb-2" />
  <SkeletonLoader variant="text" width="256px" height="16px" />
</div>
```

### From Text to LoadingSpinner

**Before**:
```tsx
{loading && <div>Loading...</div>}
```

**After**:
```tsx
{loading && <LoadingSpinner size="md" text="Loading..." />}
```

## Browser Compatibility

- **Modern browsers**: Full gradient shimmer animation
- **Reduced motion**: Respects `prefers-reduced-motion` setting
- **Screen readers**: Full ARIA support
- **Keyboard navigation**: Proper focus management during loading

## Testing

### Manual Testing

1. **Visual Regression**: Compare loading states across components
2. **Accessibility**: Test with screen reader (NVDA, JAWS, VoiceOver)
3. **Performance**: Monitor animation frame rate (should be 60fps)
4. **Responsive**: Test on mobile, tablet, desktop breakpoints

### Automated Testing

```typescript
// Example test for loading state
it('should render loading skeleton with proper ARIA attributes', () => {
  render(<MetricCard loading={true} title="Test" />);

  const loadingContainer = screen.getByRole('status');
  expect(loadingContainer).toHaveAttribute('aria-busy', 'true');
  expect(loadingContainer).toHaveAttribute('aria-label', 'Loading Test metric');
});
```

## Common Mistakes to Avoid

1. **Missing ARIA attributes**: Always include `role`, `aria-busy`, and `aria-label`
2. **Inconsistent animations**: Use standardized components, don't create custom ones
3. **Layout shift**: Skeleton should match actual content dimensions
4. **Wrong component choice**: Use SkeletonLoader for content, LoadingSpinner for pages/modals
5. **Overly complex skeletons**: Keep it simple - approximate shape is enough
6. **No loading state**: Every async operation should have visual feedback

## Resources

- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)
- [Web Content Accessibility Guidelines (WCAG) 2.1](https://www.w3.org/WAI/WCAG21/quickref/)
- [Framer Motion Documentation](https://www.framer.com/motion/)
- [TailwindCSS Animation Utilities](https://tailwindcss.com/docs/animation)

## Component File Locations

| Component | File Path |
|-----------|-----------|
| SkeletonLoader | `frontend/src/components/common/SkeletonLoader.tsx` |
| LoadingSpinner | `frontend/src/components/common/LoadingSpinner.tsx` |
| CategoryChart | `frontend/src/components/dashboard/CategoryChart.tsx` |
| TrendChart | `frontend/src/components/dashboard/TrendChart.tsx` |
| MetricCard | `frontend/src/components/dashboard/MetricCard.tsx` |
| RecentActivity | `frontend/src/components/dashboard/RecentActivity.tsx` |
| ReportList | `frontend/src/components/reports/ReportList.tsx` |
| ClientsPage | `frontend/src/pages/ClientsPage.tsx` |

## Summary

**Use SkeletonLoader for**:
- Content placeholders (cards, charts, tables, lists)
- Maintaining layout during data fetch
- Creating realistic content previews

**Use LoadingSpinner for**:
- Full-page loading states
- Modal/dialog loading
- Form submissions
- Initial app load

**Always include**:
- Proper ARIA attributes (`role`, `aria-busy`, `aria-label`)
- Consistent animation timing (1.5s for skeletons, 1s for spinners)
- Layout preservation (no content shift)
- Descriptive labels for screen readers

By following these patterns, we ensure a consistent, accessible, and performant loading experience across the entire application.
