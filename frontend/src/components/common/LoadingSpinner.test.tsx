import React from 'react';
import { render, screen } from '../../utils/test-utils';
import LoadingSpinner from './LoadingSpinner';

describe('LoadingSpinner Component', () => {
  // Test 1: Basic rendering
  it('renders spinner without text', () => {
    const { container } = render(<LoadingSpinner />);
    const spinner = container.querySelector('.rounded-full');
    expect(spinner).toBeInTheDocument();
  });

  // Test 2: Small size
  it('renders with small size', () => {
    const { container } = render(<LoadingSpinner size="sm" />);
    const spinner = container.querySelector('.w-4.h-4');
    expect(spinner).toBeInTheDocument();
  });

  // Test 3: Medium size (default)
  it('renders with medium size by default', () => {
    const { container } = render(<LoadingSpinner />);
    const spinner = container.querySelector('.w-8.h-8');
    expect(spinner).toBeInTheDocument();
  });

  // Test 4: Large size
  it('renders with large size', () => {
    const { container } = render(<LoadingSpinner size="lg" />);
    const spinner = container.querySelector('.w-12.h-12');
    expect(spinner).toBeInTheDocument();
  });

  // Test 5: Loading text
  it('renders with loading text when provided', () => {
    render(<LoadingSpinner text="Loading data..." />);
    expect(screen.getByText('Loading data...')).toBeInTheDocument();
  });

  // Test 6: No text by default
  it('does not render text when not provided', () => {
    const { container } = render(<LoadingSpinner />);
    const text = container.querySelector('.text-sm');
    expect(text).not.toBeInTheDocument();
  });

  // Test 7: Full screen mode
  it('renders in full screen mode when fullScreen is true', () => {
    const { container } = render(<LoadingSpinner fullScreen />);
    const fullScreenDiv = container.querySelector('.fixed.inset-0');
    expect(fullScreenDiv).toBeInTheDocument();
    expect(fullScreenDiv).toHaveClass('bg-white');
    expect(fullScreenDiv).toHaveClass('bg-opacity-90');
    expect(fullScreenDiv).toHaveClass('z-50');
  });

  // Test 8: Not full screen by default
  it('does not render in full screen mode by default', () => {
    const { container } = render(<LoadingSpinner />);
    const fullScreenDiv = container.querySelector('.fixed.inset-0');
    expect(fullScreenDiv).not.toBeInTheDocument();
  });

  // Test 9: Spinner styling
  it('has correct spinner styling', () => {
    const { container } = render(<LoadingSpinner />);
    const spinner = container.querySelector('.rounded-full');
    expect(spinner).toHaveClass('border-4');
    expect(spinner).toHaveClass('border-gray-200');
    expect(spinner).toHaveClass('border-t-azure-600');
  });

  // Test 10: Full screen with text
  it('renders full screen with text', () => {
    render(<LoadingSpinner fullScreen text="Please wait..." />);
    expect(screen.getByText('Please wait...')).toBeInTheDocument();
    const { container } = render(<LoadingSpinner fullScreen text="Please wait..." />);
    const fullScreenDiv = container.querySelector('.fixed.inset-0');
    expect(fullScreenDiv).toBeInTheDocument();
  });

  // Test 11: Text styling
  it('applies correct text styling', () => {
    render(<LoadingSpinner text="Loading..." />);
    const text = screen.getByText('Loading...');
    expect(text.tagName).toBe('P');
    expect(text).toHaveClass('text-sm');
    expect(text).toHaveClass('text-gray-600');
  });
});
