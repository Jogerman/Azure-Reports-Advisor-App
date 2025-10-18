import React, { useMemo, useCallback } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import Card from '../common/Card';
import SkeletonLoader from '../common/SkeletonLoader';
import { CATEGORY_COLORS, getCategoryColor } from '../../constants/chartColors';

export interface CategoryData {
  name: string;
  value: number;
  color: string;
}

export interface CategoryChartProps {
  data: CategoryData[];
  title?: string;
  subtitle?: string;
  loading?: boolean;
}

// Use theme-aware colors for categories (now imported from constants)
const COLORS = CATEGORY_COLORS;

// Memoized custom tooltip component
const CustomTooltip = React.memo(({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0];
    return (
      <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
        <p className="text-sm font-semibold text-gray-900">{data.name}</p>
        <p className="text-sm text-gray-600">
          Count: <span className="font-medium">{data.value}</span>
        </p>
      </div>
    );
  }
  return null;
});

CustomTooltip.displayName = 'CustomTooltip';

const CategoryChart: React.FC<CategoryChartProps> = ({
  data,
  title = 'Recommendations by Category',
  subtitle,
  loading = false,
}) => {
  // Memoize total calculation
  const total = useMemo(() => {
    if (!data || data.length === 0) return 0;
    return data.reduce((sum, item) => sum + item.value, 0);
  }, [data]);

  // Memoize label renderer to prevent recreation on every render
  const renderCustomizedLabel = useCallback((entry: any) => {
    const percent = ((entry.value / total) * 100).toFixed(0);
    return `${percent}%`;
  }, [total]);

  if (loading) {
    return (
      <Card>
        <div className="p-6" role="status" aria-busy="true" aria-label="Loading recommendations by category chart">
          <div className="mb-4">
            <SkeletonLoader variant="text" width="60%" height="24px" className="mb-2" />
            {subtitle && <SkeletonLoader variant="text" width="80%" height="16px" />}
          </div>
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
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
          {subtitle && <p className="text-sm text-gray-600 mb-4">{subtitle}</p>}
          <div className="w-full h-64 bg-gray-50 rounded-lg flex items-center justify-center">
            <p className="text-gray-500">No data available</p>
          </div>
        </div>
      </Card>
    );
  }

  // Calculate total for percentages
  const dataWithTotal = data.map((item) => ({
    ...item,
    total: data.reduce((sum, d) => sum + d.value, 0),
  }));

  return (
    <Card>
      <div className="p-6">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">{title}</h3>
          {subtitle && <p className="text-sm text-gray-600">{subtitle}</p>}
        </div>

        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={dataWithTotal}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={renderCustomizedLabel}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
            >
              {dataWithTotal.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.color || getCategoryColor(entry.name)}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="circle"
              formatter={(value) => (
                <span className="text-sm text-gray-700">{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>

        {/* Summary Statistics */}
        <div className="mt-4 grid grid-cols-2 gap-4">
          <div className="text-center">
            <p className="text-sm text-gray-500">Total</p>
            <p className="text-2xl font-bold text-gray-900">
              {data.reduce((sum, item) => sum + item.value, 0)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">Categories</p>
            <p className="text-2xl font-bold text-gray-900">{data.length}</p>
          </div>
        </div>
      </div>
    </Card>
  );
};

// Memoize component to prevent unnecessary re-renders
export default React.memo(CategoryChart);
