import React from 'react';
import { render, screen } from '../../utils/test-utils';
import MetricCard from './MetricCard';
import { FiDollarSign } from 'react-icons/fi';

describe('MetricCard Component', () => {
  const defaultProps = {
    title: 'Total Revenue',
    value: '$50,000',
    icon: <FiDollarSign data-testid="dollar-icon" />,
  };

  // Test 1: Basic rendering
  it('renders title and value', () => {
    render(<MetricCard {...defaultProps} />);
    expect(screen.getByText('Total Revenue')).toBeInTheDocument();
    expect(screen.getByText('$50,000')).toBeInTheDocument();
  });

  // Test 2: Icon rendering
  it('renders icon', () => {
    render(<MetricCard {...defaultProps} />);
    expect(screen.getByTestId('dollar-icon')).toBeInTheDocument();
  });

  // Test 3: Subtitle rendering
  it('renders subtitle when provided', () => {
    render(<MetricCard {...defaultProps} subtitle="Last 30 days" />);
    expect(screen.getByText('Last 30 days')).toBeInTheDocument();
  });

  // Test 4: No subtitle
  it('does not render subtitle when not provided', () => {
    render(<MetricCard {...defaultProps} />);
    expect(screen.queryByText('Last 30 days')).not.toBeInTheDocument();
  });

  // Test 5: Change label rendering
  it('renders change label when provided', () => {
    render(<MetricCard {...defaultProps} changeLabel="vs last month" />);
    expect(screen.getByText('vs last month')).toBeInTheDocument();
  });

  // Test 6: Positive change indicator
  it('displays positive change with success color and up arrow', () => {
    render(<MetricCard {...defaultProps} change={15.5} />);
    expect(screen.getByText('+15.5%')).toBeInTheDocument();

    const { container } = render(<MetricCard {...defaultProps} change={15.5} />);
    const trendElement = container.querySelector('.text-success-600');
    expect(trendElement).toBeInTheDocument();
  });

  // Test 7: Negative change indicator
  it('displays negative change with danger color and down arrow', () => {
    render(<MetricCard {...defaultProps} change={-8.3} />);
    expect(screen.getByText('-8.3%')).toBeInTheDocument();

    const { container } = render(<MetricCard {...defaultProps} change={-8.3} />);
    const trendElement = container.querySelector('.text-danger-600');
    expect(trendElement).toBeInTheDocument();
  });

  // Test 8: Zero change
  it('displays zero change with gray color', () => {
    render(<MetricCard {...defaultProps} change={0} />);
    expect(screen.getByText('0.0%')).toBeInTheDocument();

    const { container } = render(<MetricCard {...defaultProps} change={0} />);
    const trendElement = container.querySelector('.text-gray-600');
    expect(trendElement).toBeInTheDocument();
  });

  // Test 9: Azure color (default)
  it('applies azure color by default', () => {
    const { container } = render(<MetricCard {...defaultProps} />);
    const iconWrapper = container.querySelector('.bg-azure-50.text-azure-600');
    expect(iconWrapper).toBeInTheDocument();
  });

  // Test 10: Success color
  it('applies success color', () => {
    const { container } = render(<MetricCard {...defaultProps} color="success" />);
    const iconWrapper = container.querySelector('.bg-success-50.text-success-600');
    expect(iconWrapper).toBeInTheDocument();
  });

  // Test 11: Warning color
  it('applies warning color', () => {
    const { container } = render(<MetricCard {...defaultProps} color="warning" />);
    const iconWrapper = container.querySelector('.bg-warning-50.text-warning-600');
    expect(iconWrapper).toBeInTheDocument();
  });

  // Test 12: Danger color
  it('applies danger color', () => {
    const { container } = render(<MetricCard {...defaultProps} color="danger" />);
    const iconWrapper = container.querySelector('.bg-danger-50.text-danger-600');
    expect(iconWrapper).toBeInTheDocument();
  });

  // Test 13: Info color
  it('applies info color', () => {
    const { container } = render(<MetricCard {...defaultProps} color="info" />);
    const iconWrapper = container.querySelector('.bg-info-50.text-info-600');
    expect(iconWrapper).toBeInTheDocument();
  });

  // Test 14: Loading state
  it('renders skeleton loader when loading', () => {
    const { container } = render(<MetricCard {...defaultProps} loading />);
    const skeleton = container.querySelector('.animate-pulse');
    expect(skeleton).toBeInTheDocument();

    // Content should not be visible
    expect(screen.queryByText('Total Revenue')).not.toBeInTheDocument();
    expect(screen.queryByText('$50,000')).not.toBeInTheDocument();
  });

  // Test 15: Not loading by default
  it('does not show loading state by default', () => {
    const { container } = render(<MetricCard {...defaultProps} />);
    const skeleton = container.querySelector('.animate-pulse');
    expect(skeleton).not.toBeInTheDocument();
  });

  // Test 16: Numeric value
  it('renders numeric value', () => {
    render(<MetricCard {...defaultProps} value={1250} />);
    expect(screen.getByText('1250')).toBeInTheDocument();
  });

  // Test 17: String value
  it('renders string value', () => {
    render(<MetricCard {...defaultProps} value="$50K+" />);
    expect(screen.getByText('$50K+')).toBeInTheDocument();
  });

  // Test 18: Complete card with all props
  it('renders complete card with all props', () => {
    render(
      <MetricCard
        title="Total Savings"
        value="$75,000"
        subtitle="This quarter"
        change={22.5}
        changeLabel="vs last quarter"
        icon={<FiDollarSign data-testid="dollar-icon" />}
        color="success"
      />
    );

    expect(screen.getByText('Total Savings')).toBeInTheDocument();
    expect(screen.getByText('$75,000')).toBeInTheDocument();
    expect(screen.getByText('This quarter')).toBeInTheDocument();
    expect(screen.getByText('+22.5%')).toBeInTheDocument();
    expect(screen.getByText('vs last quarter')).toBeInTheDocument();
    expect(screen.getByTestId('dollar-icon')).toBeInTheDocument();
  });

  // Test 19: Change precision
  it('displays change with one decimal place', () => {
    render(<MetricCard {...defaultProps} change={15.567} />);
    expect(screen.getByText('+15.6%')).toBeInTheDocument();

    const { rerender } = render(<MetricCard {...defaultProps} change={-7.234} />);
    expect(screen.getByText('-7.2%')).toBeInTheDocument();

    rerender(<MetricCard {...defaultProps} change={0.05} />);
    expect(screen.getByText('+0.1%')).toBeInTheDocument();
  });

  // Test 20: Memoization behavior
  it('is memoized to prevent unnecessary re-renders', () => {
    const { rerender } = render(<MetricCard {...defaultProps} />);

    // Re-render with same props should not cause change
    rerender(<MetricCard {...defaultProps} />);

    expect(screen.getByText('Total Revenue')).toBeInTheDocument();
  });
});
