# Dark Mode Implementation Guide

## Overview

This document describes the dark mode implementation for the Azure Advisor Reports Platform frontend application. The dark mode feature provides users with a comfortable viewing experience in low-light environments and follows modern UX best practices.

## Implementation Details

### 1. Technology Stack

- **TailwindCSS**: Class-based dark mode using `dark:` prefix
- **React Context API**: Global state management for dark mode preference
- **localStorage**: Persistent storage of user preference
- **System Preference Detection**: Automatic dark mode based on OS settings

### 2. Key Components

#### DarkModeContext (`/src/context/DarkModeContext.tsx`)

Provides global dark mode state and controls:

```typescript
interface DarkModeContextType {
  isDarkMode: boolean;
  toggleDarkMode: () => void;
  setDarkMode: (value: boolean) => void;
}
```

**Features:**
- Initializes from localStorage or system preference
- Automatically applies `dark` class to document root
- Listens for system preference changes
- Persists user preference to localStorage

#### DarkModeToggle Component (`/src/components/common/DarkModeToggle.tsx`)

A toggle button with smooth icon transitions:
- Sun icon (visible in dark mode)
- Moon icon (visible in light mode)
- Accessible with proper ARIA labels
- Smooth rotation and scale animations

### 3. Configuration

#### Tailwind Config (`tailwind.config.js`)

```javascript
module.exports = {
  darkMode: 'class', // Enable class-based dark mode
  // ... rest of config
}
```

### 4. Usage

#### In Components

Use Tailwind's `dark:` prefix to specify dark mode styles:

```tsx
<div className="bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
  Content
</div>
```

#### Accessing Dark Mode State

```typescript
import { useDarkMode } from '../hooks/useDarkMode';

const MyComponent = () => {
  const { isDarkMode, toggleDarkMode, setDarkMode } = useDarkMode();

  return (
    <button onClick={toggleDarkMode}>
      Toggle Dark Mode
    </button>
  );
};
```

### 5. Components with Dark Mode Support

The following components have been updated with dark mode support:

**Layout Components:**
- `Header.tsx` - Navigation header
- `Sidebar.tsx` - Navigation sidebar
- `Footer.tsx` - Page footer
- `MainLayout.tsx` - Main application layout

**Common Components:**
- `Card.tsx` - Card container
- `Modal.tsx` - Modal dialog
- `DarkModeToggle.tsx` - Dark mode toggle button

### 6. Color Palette

#### Light Mode
- Background: `bg-white`, `bg-gray-50`, `bg-gray-100`
- Text: `text-gray-900`, `text-gray-700`, `text-gray-600`
- Borders: `border-gray-200`
- Hover: `hover:bg-gray-50`, `hover:bg-gray-100`

#### Dark Mode
- Background: `dark:bg-gray-900`, `dark:bg-gray-800`, `dark:bg-gray-700`
- Text: `dark:text-white`, `dark:text-gray-200`, `dark:text-gray-300`
- Borders: `dark:border-gray-700`
- Hover: `dark:hover:bg-gray-700`, `dark:hover:bg-gray-600`

#### Brand Colors (Azure Blue)
- Light: `bg-azure-50`, `text-azure-600`, `hover:text-azure-600`
- Dark: `dark:bg-azure-900/30`, `dark:text-azure-400`, `dark:hover:text-azure-300`

### 7. Best Practices

#### Adding Dark Mode to New Components

1. **Background Colors:**
   ```tsx
   className="bg-white dark:bg-gray-800"
   ```

2. **Text Colors:**
   ```tsx
   className="text-gray-900 dark:text-white"
   ```

3. **Borders:**
   ```tsx
   className="border-gray-200 dark:border-gray-700"
   ```

4. **Hover States:**
   ```tsx
   className="hover:bg-gray-100 dark:hover:bg-gray-700"
   ```

5. **Transitions:**
   ```tsx
   className="transition-colors duration-200"
   ```

#### Accessibility Considerations

- Always provide sufficient color contrast (WCAG AA minimum)
- Use semantic color names in context
- Test with screen readers
- Provide descriptive ARIA labels for toggle buttons
- Support keyboard navigation

### 8. Browser Support

- Modern browsers with CSS custom properties support
- Fallback to light mode for older browsers
- System preference detection via `prefers-color-scheme` media query

### 9. Performance Optimizations

- Class-based implementation (no runtime style calculations)
- Minimal re-renders with React Context
- CSS transitions for smooth visual updates
- localStorage caching to prevent flicker on page load

### 10. Testing

#### Manual Testing Checklist

- [ ] Toggle button appears in header
- [ ] Click toggle switches between light/dark mode
- [ ] Preference persists across page refreshes
- [ ] System preference is detected on first visit
- [ ] All pages render correctly in both modes
- [ ] Modals and overlays work in both modes
- [ ] Focus states are visible in both modes
- [ ] Color contrast meets WCAG AA standards

#### Component Testing

Test dark mode in key user flows:
1. Login page
2. Dashboard
3. Reports page
4. Client management
5. Settings
6. Modal dialogs
7. Forms and inputs

### 11. Future Enhancements

Potential improvements for future iterations:

1. **Auto-switching**: Automatically switch based on time of day
2. **Custom themes**: Allow users to create custom color schemes
3. **High contrast mode**: Additional accessibility mode
4. **Scheduled switching**: Switch at specified times
5. **Per-component preferences**: Remember dark mode per section

### 12. Troubleshooting

#### Dark mode not persisting
- Check localStorage is enabled in browser
- Verify `DarkModeProvider` wraps the entire application
- Check browser console for errors

#### Flicker on page load
- Ensure `dark` class is applied before first paint
- Check initialization logic in `DarkModeContext`

#### Icons not switching
- Verify `react-icons` package is installed
- Check icon import paths in `DarkModeToggle`

#### Styles not applying
- Ensure `darkMode: 'class'` is set in `tailwind.config.js`
- Verify `dark:` prefix is used correctly
- Check Tailwind is processing the files

### 13. File Structure

```
frontend/
├── src/
│   ├── context/
│   │   └── DarkModeContext.tsx          # Dark mode state management
│   ├── hooks/
│   │   └── useDarkMode.ts               # Convenience hook export
│   ├── components/
│   │   ├── common/
│   │   │   ├── DarkModeToggle.tsx       # Toggle button component
│   │   │   ├── Card.tsx                 # Updated with dark mode
│   │   │   └── Modal.tsx                # Updated with dark mode
│   │   └── layout/
│   │       ├── Header.tsx               # Updated with dark mode
│   │       ├── Sidebar.tsx              # Updated with dark mode
│   │       ├── Footer.tsx               # Updated with dark mode
│   │       └── MainLayout.tsx           # Updated with dark mode
│   └── App.tsx                          # DarkModeProvider integration
└── tailwind.config.js                   # Dark mode configuration
```

## Summary

The dark mode implementation provides:
- Seamless toggle between light and dark themes
- Persistent user preference storage
- Automatic system preference detection
- Comprehensive coverage of all layout components
- Accessible and keyboard-navigable interface
- Smooth transitions and animations
- Professional appearance in both modes

The implementation follows React and TailwindCSS best practices, ensuring maintainability and performance.
