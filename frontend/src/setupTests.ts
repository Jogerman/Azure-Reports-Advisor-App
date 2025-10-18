// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Mock Framer Motion to avoid animation issues in tests
jest.mock('framer-motion', () => {
  const React = require('react');
  return {
    ...jest.requireActual('framer-motion'),
    motion: new Proxy(
      {},
      {
        get: (target, prop) => {
          return React.forwardRef((props: any, ref: any) =>
            React.createElement(prop as string, { ...props, ref })
          );
        },
      }
    ),
    AnimatePresence: ({ children }: any) => children,
  };
});

// Mock ResizeObserver for Recharts
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock window.matchMedia (required for Framer Motion)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // Deprecated
    removeListener: jest.fn(), // Deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock window.getComputedStyle (required for Framer Motion animations)
Object.defineProperty(window, 'getComputedStyle', {
  value: () => ({
    getPropertyValue: () => '',
  }),
});

// Mock window.mediaQuery for Framer Motion's prefers-reduced-motion
const mockMediaQueryList = {
  matches: false,
  media: '(prefers-reduced-motion: reduce)',
  onchange: null,
  addListener: jest.fn(),
  removeListener: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  dispatchEvent: jest.fn(),
};

// Override matchMedia to ensure it always returns a valid MediaQueryList
window.matchMedia = jest.fn().mockImplementation((query) => ({
  ...mockMediaQueryList,
  media: query,
}));

// Suppress Framer Motion warnings in tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: any[]) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Not implemented: HTMLFormElement.prototype.submit') ||
       args[0].includes('Could not parse CSS stylesheet'))
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

// Mock URL.createObjectURL and URL.revokeObjectURL (required for file downloads)
if (typeof window.URL.createObjectURL === 'undefined') {
  Object.defineProperty(window.URL, 'createObjectURL', {
    writable: true,
    value: jest.fn((blob: Blob) => 'blob:mock-url'),
  });
}

if (typeof window.URL.revokeObjectURL === 'undefined') {
  Object.defineProperty(window.URL, 'revokeObjectURL', {
    writable: true,
    value: jest.fn(),
  });
}
