import React, { useMemo } from 'react';
import { FiTrendingUp } from 'react-icons/fi';
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
import { format, parseISO } from 'date-fns';
import Card from '../common/Card';
import Button from '../common/Button';
import { TrendDataPoint } from '../../types/history';

interface HistoryChartProps {
  data: TrendDataPoint[];
  granularity: 'day' | 'week' | 'month';
  onGranularityChange: (g: 'day' | 'week' | 'month') => void;
  loading: boolean;
}

// Consistent colors for report types
const CHART_COLORS = {
  cost: '#0078D4',
  security: '#D13438',
  operations: '#107C10',
  detailed: '#8B5CF6',
  executive: '#F59E0B',
};

const HistoryChart: React.FC<HistoryChartProps> = ({
  data,
  granularity,
  onGranularityChange,
  loading,
}) => {
  // Transform data for Recharts
  const chartData = useMemo(() => {
    return data.map((point) => ({
      date: point.date,
      formattedDate: formatDate(point.date, granularity),
      Cost: point.by_type.cost,
      Security: point.by_type.security,
      Operations: point.by_type.operations,
      Detailed: point.by_type.detailed,
      Executive: point.by_type.executive,
      Total: point.total,
    }));
  }, [data, granularity]);

  // Format date based on granularity
  function formatDate(dateStr: string, gran: 'day' | 'week' | 'month'): string {
    try {
      const date = parseISO(dateStr);
      switch (gran) {
        case 'day':
          return format(date, 'MMM dd');
        case 'week':
          return format(date, 'MMM dd');
        case 'month':
          return format(date, 'MMM yyyy');
        default:
          return format(date, 'MMM dd');
      }
    } catch {
      return dateStr;
    }
  }

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || payload.length === 0) return null;

    const total = payload.reduce((sum: number, item: any) => {
      if (item.dataKey !== 'Total') {
        return sum + (item.value || 0);
      }
      return sum;
    }, 0);

    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
        <p className="text-sm font-semibold text-gray-900 mb-2">{label}</p>
        <div className="space-y-1">
          {payload.map((item: any) => {
            if (item.dataKey === 'Total') return null;
            return (
              <div key={item.dataKey} className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-xs text-gray-700">{item.dataKey}</span>
                </div>
                <span className="text-xs font-semibold text-gray-900">{item.value}</span>
              </div>
            );
          })}
          <div className="pt-1 mt-1 border-t border-gray-200">
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs font-semibold text-gray-900">Total</span>
              <span className="text-xs font-bold text-azure-600">{total}</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <Card>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-info-50 text-info-600 flex items-center justify-center">
            <FiTrendingUp className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Report Trends</h2>
            <p className="text-sm text-gray-600">Reports generated over time</p>
          </div>
        </div>

        {/* Granularity Toggle */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600 mr-1">View by:</span>
          <Button
            size="sm"
            variant={granularity === 'day' ? 'primary' : 'outline'}
            onClick={() => onGranularityChange('day')}
          >
            Day
          </Button>
          <Button
            size="sm"
            variant={granularity === 'week' ? 'primary' : 'outline'}
            onClick={() => onGranularityChange('week')}
          >
            Week
          </Button>
          <Button
            size="sm"
            variant={granularity === 'month' ? 'primary' : 'outline'}
            onClick={() => onGranularityChange('month')}
          >
            Month
          </Button>
        </div>
      </div>

      {/* Chart */}
      {loading ? (
        <div className="h-80 flex items-center justify-center">
          <div className="space-y-4 w-full">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-16 bg-gray-200 rounded animate-pulse" />
            ))}
          </div>
        </div>
      ) : data.length === 0 ? (
        <div className="h-80 flex flex-col items-center justify-center text-gray-400">
          <FiTrendingUp className="w-12 h-12 mb-3" />
          <p className="text-sm">No trend data available</p>
          <p className="text-xs mt-1">Generate some reports to see trends</p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={chartData} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis
              dataKey="formattedDate"
              stroke="#6B7280"
              fontSize={12}
              tickLine={false}
            />
            <YAxis
              stroke="#6B7280"
              fontSize={12}
              tickLine={false}
              allowDecimals={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: '12px' }}
              iconType="circle"
              formatter={(value) => {
                const names: Record<string, string> = {
                  Cost: 'Cost Optimization',
                  Security: 'Security',
                  Operations: 'Operations',
                  Detailed: 'Detailed',
                  Executive: 'Executive',
                };
                return names[value] || value;
              }}
            />
            <Line
              type="monotone"
              dataKey="Cost"
              stroke={CHART_COLORS.cost}
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
            <Line
              type="monotone"
              dataKey="Security"
              stroke={CHART_COLORS.security}
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
            <Line
              type="monotone"
              dataKey="Operations"
              stroke={CHART_COLORS.operations}
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
            <Line
              type="monotone"
              dataKey="Detailed"
              stroke={CHART_COLORS.detailed}
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
            <Line
              type="monotone"
              dataKey="Executive"
              stroke={CHART_COLORS.executive}
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
};

export default React.memo(HistoryChart);
