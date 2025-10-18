import React, { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { motion } from 'framer-motion';
import Card from '../common/Card';
import SkeletonLoader from '../common/SkeletonLoader';

export interface TrendDataPoint {
  date: string;
  value: number;
  label?: string;
}

export interface TrendChartProps {
  data: TrendDataPoint[];
  title?: string;
  subtitle?: string;
  valueLabel?: string;
  loading?: boolean;
  showTimeRangeSelector?: boolean;
}

type TimeRange = '7d' | '30d' | '90d';

const TrendChart: React.FC<TrendChartProps> = ({
  data,
  title = 'Report Generation Trend',
  subtitle,
  valueLabel = 'Reports',
  loading = false,
  showTimeRangeSelector = true,
}) => {
  const [timeRange, setTimeRange] = useState<TimeRange>('30d');

  // Filter data based on selected time range
  const getFilteredData = () => {
    const days = {
      '7d': 7,
      '30d': 30,
      '90d': 90,
    };

    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days[timeRange]);

    return data.filter((item) => new Date(item.date) >= cutoffDate);
  };

  const filteredData = getFilteredData();

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
          <p className="text-sm font-semibold text-gray-900">{data.payload.label || data.payload.date}</p>
          <p className="text-sm text-gray-600">
            {valueLabel}: <span className="font-medium text-azure-600">{data.value}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <Card>
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
              <div key={i} className="flex items-end space-x-2" style={{ height: '16.67%' }}>
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
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
          {subtitle && <p className="text-sm text-gray-600 mb-4">{subtitle}</p>}
          <div className="w-full h-80 bg-gray-50 rounded-lg flex items-center justify-center">
            <p className="text-gray-500">No data available</p>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">{title}</h3>
            {subtitle && <p className="text-sm text-gray-600">{subtitle}</p>}
          </div>

          {showTimeRangeSelector && (
            <div className="flex space-x-2">
              {(['7d', '30d', '90d'] as TimeRange[]).map((range) => (
                <motion.button
                  key={range}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setTimeRange(range)}
                  className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                    timeRange === range
                      ? 'bg-azure-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {range === '7d' && '7 Days'}
                  {range === '30d' && '30 Days'}
                  {range === '90d' && '90 Days'}
                </motion.button>
              ))}
            </div>
          )}
        </div>

        <ResponsiveContainer width="100%" height={320}>
          <LineChart
            data={filteredData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              stroke="#9ca3af"
              style={{ fontSize: '12px' }}
              tickFormatter={(value) => {
                const date = new Date(value);
                return `${date.getMonth() + 1}/${date.getDate()}`;
              }}
            />
            <YAxis
              stroke="#9ca3af"
              style={{ fontSize: '12px' }}
              allowDecimals={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: '14px' }}
              iconType="line"
            />
            <Line
              type="monotone"
              dataKey="value"
              name={valueLabel}
              stroke="#0078D4"
              strokeWidth={3}
              dot={{ fill: '#0078D4', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>

        {/* Summary Statistics */}
        <div className="mt-6 grid grid-cols-3 gap-4 pt-4 border-t border-gray-200">
          <div className="text-center">
            <p className="text-sm text-gray-500">Total</p>
            <p className="text-xl font-bold text-gray-900">
              {filteredData.reduce((sum, item) => sum + item.value, 0)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">Average</p>
            <p className="text-xl font-bold text-gray-900">
              {filteredData.length > 0
                ? (filteredData.reduce((sum, item) => sum + item.value, 0) / filteredData.length).toFixed(1)
                : '0'}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">Peak</p>
            <p className="text-xl font-bold text-gray-900">
              {Math.max(...filteredData.map((item) => item.value), 0)}
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default TrendChart;
