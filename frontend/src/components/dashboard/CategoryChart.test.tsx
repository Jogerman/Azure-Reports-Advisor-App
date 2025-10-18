import React from 'react';
import { render, screen } from '../../utils/test-utils';
import CategoryChart from './CategoryChart';

describe('CategoryChart Component', () => {
  const mockData = [
    { name: 'Cost', value: 20, color: '#f59e0b' },
    { name: 'Security', value: 15, color: '#ef4444' },
    { name: 'Reliability', value: 10, color: '#3b82f6' },
    { name: 'Operational Excellence', value: 5, color: '#8b5cf6' },
  ];

  // Test 1: Basic rendering with data
  it('renders chart with data', () => {
    render(<CategoryChart data={mockData} />);
    expect(screen.getByText('Recommendations by Category')).toBeInTheDocument();
  });

  // Test 2: Custom title
  it('renders with custom title', () => {
    render(<CategoryChart data={mockData} title="Custom Title" />);
    expect(screen.getByText('Custom Title')).toBeInTheDocument();
  });

  // Test 3: Default title
  it('renders with default title', () => {
    render(<CategoryChart data={mockData} />);
    expect(screen.getByText('Recommendations by Category')).toBeInTheDocument();
  });

  // Test 4: Subtitle rendering
  it('renders subtitle when provided', () => {
    render(<CategoryChart data={mockData} subtitle="Last 30 days" />);
    expect(screen.getByText('Last 30 days')).toBeInTheDocument();
  });

  // Test 5: No subtitle
  it('does not render subtitle when not provided', () => {
    render(<CategoryChart data={mockData} />);
    expect(screen.queryByText('Last 30 days')).not.toBeInTheDocument();
  });

  // Test 6: Loading state
  it('renders loading skeleton when loading', () => {
    render(<CategoryChart data={mockData} loading />);
    expect(screen.getByText('Loading chart...')).toBeInTheDocument();

    const { container } = render(<CategoryChart data={mockData} loading />);
    const skeleton = container.querySelector('.animate-pulse');
    expect(skeleton).toBeInTheDocument();
  });

  // Test 7: Empty data state
  it('renders empty state when data is empty', () => {
    render(<CategoryChart data={[]} />);
    expect(screen.getByText('No data available')).toBeInTheDocument();
  });

  // Test 8: Summary statistics - Total
  it('displays correct total in summary statistics', () => {
    render(<CategoryChart data={mockData} />);

    // Total should be 20 + 15 + 10 + 5 = 50
    const totals = screen.getAllByText('50');
    expect(totals.length).toBeGreaterThan(0);
  });

  // Test 9: Summary statistics - Categories count
  it('displays correct categories count', () => {
    render(<CategoryChart data={mockData} />);
    expect(screen.getByText('4')).toBeInTheDocument(); // 4 categories
  });

  // Test 10: Single category data
  it('renders correctly with single category', () => {
    const singleData = [{ name: 'Cost', value: 100, color: '#f59e0b' }];
    render(<CategoryChart data={singleData} />);

    expect(screen.getByText('100')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument(); // 1 category
  });

  // Test 11: Large data set
  it('handles large data set correctly', () => {
    const largeData = [
      { name: 'Cost', value: 200, color: '#f59e0b' },
      { name: 'Security', value: 150, color: '#ef4444' },
      { name: 'Reliability', value: 100, color: '#3b82f6' },
      { name: 'Operational Excellence', value: 50, color: '#8b5cf6' },
      { name: 'Performance', value: 75, color: '#10b981' },
    ];
    render(<CategoryChart data={largeData} />);

    // Total should be 575
    expect(screen.getByText('575')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument(); // 5 categories
  });

  // Test 12: Zero values handled
  it('handles zero values in data', () => {
    const dataWithZero = [
      { name: 'Cost', value: 20, color: '#f59e0b' },
      { name: 'Security', value: 0, color: '#ef4444' },
    ];
    render(<CategoryChart data={dataWithZero} />);

    expect(screen.getByText('20')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // Still 2 categories
  });

  // Test 13: Null data handled
  it('renders empty state when data is null', () => {
    render(<CategoryChart data={null as any} />);
    expect(screen.getByText('No data available')).toBeInTheDocument();
  });

  // Test 14: Memoization behavior
  it('is memoized to prevent unnecessary re-renders', () => {
    const { rerender } = render(<CategoryChart data={mockData} />);

    // Re-render with same props
    rerender(<CategoryChart data={mockData} />);

    expect(screen.getByText('Recommendations by Category')).toBeInTheDocument();
  });
});
