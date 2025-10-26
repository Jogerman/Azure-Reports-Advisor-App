import React, { useState } from 'react';
import { FiCalendar, FiX } from 'react-icons/fi';
import { format, subDays, subMonths, startOfMonth, endOfMonth, startOfQuarter, endOfQuarter, startOfYear, endOfYear } from 'date-fns';

export interface DateRange {
  from: Date | null;
  to: Date | null;
}

interface DateRangePickerProps {
  value: DateRange;
  onChange: (range: DateRange) => void;
  label?: string;
  presets?: boolean;
  disabled?: boolean;
}

interface Preset {
  label: string;
  getValue: () => DateRange;
}

const PRESETS: Preset[] = [
  {
    label: 'Last 7 days',
    getValue: () => ({
      from: subDays(new Date(), 7),
      to: new Date(),
    }),
  },
  {
    label: 'Last 30 days',
    getValue: () => ({
      from: subDays(new Date(), 30),
      to: new Date(),
    }),
  },
  {
    label: 'This month',
    getValue: () => ({
      from: startOfMonth(new Date()),
      to: endOfMonth(new Date()),
    }),
  },
  {
    label: 'Last month',
    getValue: () => {
      const lastMonth = subMonths(new Date(), 1);
      return {
        from: startOfMonth(lastMonth),
        to: endOfMonth(lastMonth),
      };
    },
  },
  {
    label: 'This quarter',
    getValue: () => ({
      from: startOfQuarter(new Date()),
      to: endOfQuarter(new Date()),
    }),
  },
  {
    label: 'This year',
    getValue: () => ({
      from: startOfYear(new Date()),
      to: endOfYear(new Date()),
    }),
  },
];

const DateRangePicker: React.FC<DateRangePickerProps> = ({
  value,
  onChange,
  label,
  presets = true,
  disabled = false,
}) => {
  const [activePreset, setActivePreset] = useState<string | null>(null);

  const handlePresetClick = (preset: Preset) => {
    const range = preset.getValue();
    onChange(range);
    setActivePreset(preset.label);
  };

  const handleFromChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const date = e.target.value ? new Date(e.target.value) : null;
    onChange({ ...value, from: date });
    setActivePreset(null);
  };

  const handleToChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const date = e.target.value ? new Date(e.target.value) : null;
    onChange({ ...value, to: date });
    setActivePreset(null);
  };

  const handleClear = () => {
    onChange({ from: null, to: null });
    setActivePreset(null);
  };

  const hasValue = value.from !== null || value.to !== null;

  // Format dates for input value (YYYY-MM-DD)
  const formatDateForInput = (date: Date | null): string => {
    if (!date) return '';
    return format(date, 'yyyy-MM-dd');
  };

  return (
    <div className="space-y-3">
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
        </label>
      )}

      {/* Presets */}
      {presets && (
        <div className="flex flex-wrap gap-2">
          {PRESETS.map((preset) => (
            <button
              key={preset.label}
              type="button"
              onClick={() => handlePresetClick(preset)}
              disabled={disabled}
              className={`
                px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-200
                ${disabled
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : activePreset === preset.label
                  ? 'bg-azure-600 text-white shadow-sm'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }
              `}
              aria-label={`Select ${preset.label}`}
            >
              {preset.label}
            </button>
          ))}
        </div>
      )}

      {/* Date Inputs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* From Date */}
        <div>
          <label htmlFor="date-from" className="block text-xs font-medium text-gray-600 mb-1">
            From
          </label>
          <div className="relative">
            <input
              id="date-from"
              type="date"
              value={formatDateForInput(value.from)}
              onChange={handleFromChange}
              disabled={disabled}
              max={value.to ? formatDateForInput(value.to) : undefined}
              className={`
                w-full px-3 py-2 pl-10 border rounded-lg text-sm
                transition-all duration-200
                ${disabled
                  ? 'bg-gray-100 cursor-not-allowed opacity-60'
                  : 'bg-white hover:border-azure-500 focus:outline-none focus:ring-2 focus:ring-azure-500 focus:border-transparent'
                }
                ${value.from ? 'border-gray-300' : 'border-gray-300'}
              `}
              aria-label="From date"
            />
            <FiCalendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>
        </div>

        {/* To Date */}
        <div>
          <label htmlFor="date-to" className="block text-xs font-medium text-gray-600 mb-1">
            To
          </label>
          <div className="relative">
            <input
              id="date-to"
              type="date"
              value={formatDateForInput(value.to)}
              onChange={handleToChange}
              disabled={disabled}
              min={value.from ? formatDateForInput(value.from) : undefined}
              className={`
                w-full px-3 py-2 pl-10 border rounded-lg text-sm
                transition-all duration-200
                ${disabled
                  ? 'bg-gray-100 cursor-not-allowed opacity-60'
                  : 'bg-white hover:border-azure-500 focus:outline-none focus:ring-2 focus:ring-azure-500 focus:border-transparent'
                }
                ${value.to ? 'border-gray-300' : 'border-gray-300'}
              `}
              aria-label="To date"
            />
            <FiCalendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Clear Button */}
      {hasValue && !disabled && (
        <button
          type="button"
          onClick={handleClear}
          className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-800 transition-colors"
          aria-label="Clear date range"
        >
          <FiX className="w-3 h-3" />
          Clear dates
        </button>
      )}

      {/* Selected Range Display */}
      {hasValue && (
        <div className="text-xs text-gray-600 bg-gray-50 px-3 py-2 rounded-md">
          {value.from && value.to ? (
            <span>
              <strong>Selected:</strong> {format(value.from, 'MMM dd, yyyy')} - {format(value.to, 'MMM dd, yyyy')}
            </span>
          ) : value.from ? (
            <span>
              <strong>From:</strong> {format(value.from, 'MMM dd, yyyy')}
            </span>
          ) : value.to ? (
            <span>
              <strong>To:</strong> {format(value.to, 'MMM dd, yyyy')}
            </span>
          ) : null}
        </div>
      )}
    </div>
  );
};

export default DateRangePicker;
