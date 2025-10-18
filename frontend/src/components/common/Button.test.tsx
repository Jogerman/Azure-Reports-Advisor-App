import React from 'react';
import { render, screen, fireEvent } from '../../utils/test-utils';
import Button from './Button';

describe('Button Component', () => {
  // Test 1: Basic rendering
  it('renders button with children text', () => {
    render(<Button>Click Me</Button>);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  // Test 2: Primary variant (default)
  it('renders with primary variant by default', () => {
    render(<Button>Primary</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-azure-600');
    expect(button).toHaveClass('text-white');
  });

  // Test 3: Secondary variant
  it('renders with secondary variant', () => {
    render(<Button variant="secondary">Secondary</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-gray-600');
    expect(button).toHaveClass('text-white');
  });

  // Test 4: Danger variant
  it('renders with danger variant', () => {
    render(<Button variant="danger">Delete</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-red-600');
    expect(button).toHaveClass('text-white');
  });

  // Test 5: Outline variant
  it('renders with outline variant', () => {
    render(<Button variant="outline">Outline</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('border-2');
    expect(button).toHaveClass('border-azure-600');
    expect(button).toHaveClass('bg-transparent');
  });

  // Test 6: Ghost variant
  it('renders with ghost variant', () => {
    render(<Button variant="ghost">Ghost</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-transparent');
    expect(button).toHaveClass('text-gray-700');
  });

  // Test 7: Small size
  it('renders with small size', () => {
    render(<Button size="sm">Small</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('px-3');
    expect(button).toHaveClass('py-1.5');
    expect(button).toHaveClass('text-sm');
  });

  // Test 8: Medium size (default)
  it('renders with medium size by default', () => {
    render(<Button>Medium</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('px-4');
    expect(button).toHaveClass('py-2');
    expect(button).toHaveClass('text-base');
  });

  // Test 9: Large size
  it('renders with large size', () => {
    render(<Button size="lg">Large</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('px-6');
    expect(button).toHaveClass('py-3');
    expect(button).toHaveClass('text-lg');
  });

  // Test 10: Full width
  it('renders with full width when fullWidth is true', () => {
    render(<Button fullWidth>Full Width</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('w-full');
  });

  // Test 11: Disabled state
  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(button).toHaveClass('disabled:opacity-50');
    expect(button).toHaveClass('disabled:cursor-not-allowed');
  });

  // Test 12: Loading state
  it('shows loading spinner when loading is true', () => {
    render(<Button loading>Submit</Button>);
    expect(screen.getByText(/loading.../i)).toBeInTheDocument();
    expect(screen.queryByText('Submit')).not.toBeInTheDocument();

    // Check for spinner SVG
    const svg = document.querySelector('svg.animate-spin');
    expect(svg).toBeInTheDocument();
  });

  // Test 13: Loading state disables button
  it('is disabled when loading is true', () => {
    render(<Button loading>Submit</Button>);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  // Test 14: Click handler
  it('calls onClick handler when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click</Button>);

    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  // Test 15: Click handler not called when disabled
  it('does not call onClick when disabled', () => {
    const handleClick = jest.fn();
    render(<Button disabled onClick={handleClick}>Disabled</Button>);

    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(handleClick).not.toHaveBeenCalled();
  });

  // Test 16: Click handler not called when loading
  it('does not call onClick when loading', () => {
    const handleClick = jest.fn();
    render(<Button loading onClick={handleClick}>Loading</Button>);

    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(handleClick).not.toHaveBeenCalled();
  });

  // Test 17: Icon rendering
  it('renders with icon', () => {
    const icon = <span data-testid="test-icon">🔍</span>;
    render(<Button icon={icon}>Search</Button>);

    expect(screen.getByTestId('test-icon')).toBeInTheDocument();
    expect(screen.getByText('Search')).toBeInTheDocument();
  });

  // Test 18: Icon not shown when loading
  it('does not show icon when loading', () => {
    const icon = <span data-testid="test-icon">🔍</span>;
    render(<Button loading icon={icon}>Search</Button>);

    expect(screen.queryByTestId('test-icon')).not.toBeInTheDocument();
    expect(screen.getByText(/loading.../i)).toBeInTheDocument();
  });

  // Test 19: Custom className
  it('applies custom className', () => {
    render(<Button className="custom-class">Custom</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('custom-class');
  });

  // Test 20: HTML button attributes
  it('passes through HTML button attributes', () => {
    render(
      <Button type="submit" data-testid="custom-button" aria-label="Submit form">
        Submit
      </Button>
    );

    const button = screen.getByTestId('custom-button');
    expect(button).toHaveAttribute('type', 'submit');
    expect(button).toHaveAttribute('aria-label', 'Submit form');
  });

  // Test 21: Focus ring styles
  it('has focus ring styles', () => {
    render(<Button>Focus</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('focus:outline-none');
    expect(button).toHaveClass('focus:ring-2');
    expect(button).toHaveClass('focus:ring-offset-2');
  });

  // Test 22: Active scale animation
  it('has active scale animation', () => {
    render(<Button>Active</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('active:scale-95');
  });
});
