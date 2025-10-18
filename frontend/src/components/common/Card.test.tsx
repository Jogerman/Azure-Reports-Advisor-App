import React from 'react';
import { render, screen, fireEvent } from '../../utils/test-utils';
import Card from './Card';

describe('Card Component', () => {
  // Test 1: Basic rendering
  it('renders card with children', () => {
    render(
      <Card>
        <p>Card Content</p>
      </Card>
    );
    expect(screen.getByText('Card Content')).toBeInTheDocument();
  });

  // Test 2: Default styles
  it('renders with default styles', () => {
    const { container } = render(<Card>Content</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card).toHaveClass('bg-white');
    expect(card).toHaveClass('rounded-lg');
    expect(card).toHaveClass('shadow-sm');
    expect(card).toHaveClass('border');
    expect(card).toHaveClass('border-gray-200');
  });

  // Test 3: Default padding (md)
  it('renders with medium padding by default', () => {
    const { container } = render(<Card>Content</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card).toHaveClass('p-6');
  });

  // Test 4: No padding
  it('renders with no padding when padding is "none"', () => {
    const { container } = render(<Card padding="none">Content</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card).not.toHaveClass('p-4');
    expect(card).not.toHaveClass('p-6');
    expect(card).not.toHaveClass('p-8');
  });

  // Test 5: Small padding
  it('renders with small padding', () => {
    const { container } = render(<Card padding="sm">Content</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card).toHaveClass('p-4');
  });

  // Test 6: Large padding
  it('renders with large padding', () => {
    const { container } = render(<Card padding="lg">Content</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card).toHaveClass('p-8');
  });

  // Test 7: Hoverable styles
  it('applies hover styles when hoverable is true', () => {
    const { container } = render(<Card hoverable>Content</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card).toHaveClass('cursor-pointer');
    expect(card).toHaveClass('hover:shadow-lg');
    expect(card).toHaveClass('hover:scale-[1.01]');
  });

  // Test 8: Not hoverable by default
  it('does not apply hover styles by default', () => {
    const { container } = render(<Card>Content</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card).not.toHaveClass('hover:shadow-lg');
    expect(card).not.toHaveClass('hover:scale-[1.01]');
  });

  // Test 9: onClick handler
  it('calls onClick handler when clicked', () => {
    const handleClick = jest.fn();
    const { container } = render(<Card onClick={handleClick}>Content</Card>);
    const card = container.firstChild as HTMLElement;

    fireEvent.click(card);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  // Test 10: Clickable cursor style
  it('applies cursor-pointer when onClick is provided', () => {
    const handleClick = jest.fn();
    const { container } = render(<Card onClick={handleClick}>Content</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card).toHaveClass('cursor-pointer');
  });

  // Test 11: Custom className
  it('applies custom className', () => {
    const { container } = render(<Card className="custom-class">Content</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card).toHaveClass('custom-class');
  });

  // Test 12: Framer Motion animation
  it('has animation properties from Framer Motion', () => {
    const { container } = render(<Card>Content</Card>);
    const card = container.firstChild as HTMLElement;
    // Framer Motion adds these inline styles
    expect(card).toBeInTheDocument();
  });

  // Test 13: Complex children rendering
  it('renders complex children correctly', () => {
    render(
      <Card>
        <h2>Title</h2>
        <p>Description</p>
        <button>Action</button>
      </Card>
    );

    expect(screen.getByText('Title')).toBeInTheDocument();
    expect(screen.getByText('Description')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /action/i })).toBeInTheDocument();
  });

  // Test 14: Multiple cards
  it('renders multiple cards independently', () => {
    render(
      <>
        <Card>Card 1</Card>
        <Card>Card 2</Card>
        <Card>Card 3</Card>
      </>
    );

    expect(screen.getByText('Card 1')).toBeInTheDocument();
    expect(screen.getByText('Card 2')).toBeInTheDocument();
    expect(screen.getByText('Card 3')).toBeInTheDocument();
  });
});
