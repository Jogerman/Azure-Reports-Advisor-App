import React, { useState, useRef, useEffect } from 'react';
import { FiChevronDown, FiX, FiCheck } from 'react-icons/fi';
import { AnimatePresence, motion } from 'framer-motion';

export interface MultiSelectOption {
  value: string;
  label: string;
  count?: number;
}

interface MultiSelectProps {
  options: MultiSelectOption[];
  value: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
  searchable?: boolean;
  label?: string;
  disabled?: boolean;
  maxHeight?: string;
}

const MultiSelect: React.FC<MultiSelectProps> = ({
  options,
  value,
  onChange,
  placeholder = 'Select options...',
  searchable = true,
  label,
  disabled = false,
  maxHeight = '256px',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Handle ESC key to close
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
        setSearchQuery('');
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen]);

  // Filter options based on search query
  const filteredOptions = searchQuery
    ? options.filter((option) =>
        option.label.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : options;

  // Toggle option selection
  const toggleOption = (optionValue: string) => {
    if (value.includes(optionValue)) {
      onChange(value.filter((v) => v !== optionValue));
    } else {
      onChange([...value, optionValue]);
    }
  };

  // Select all options
  const selectAll = () => {
    onChange(filteredOptions.map((opt) => opt.value));
  };

  // Deselect all options
  const deselectAll = () => {
    onChange([]);
  };

  // Get selected labels for display
  const getSelectedLabels = () => {
    return options
      .filter((opt) => value.includes(opt.value))
      .map((opt) => opt.label);
  };

  const selectedLabels = getSelectedLabels();

  return (
    <div className="relative" ref={containerRef}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}

      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`
          w-full px-4 py-2 text-left bg-white border rounded-lg
          flex items-center justify-between transition-all duration-200
          ${disabled
            ? 'bg-gray-100 cursor-not-allowed opacity-60'
            : 'hover:border-azure-500 focus:outline-none focus:ring-2 focus:ring-azure-500 focus:ring-offset-1'
          }
          ${isOpen ? 'border-azure-500 ring-2 ring-azure-500 ring-offset-1' : 'border-gray-300'}
        `}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={label || 'Multi-select dropdown'}
      >
        <div className="flex-1 flex items-center gap-2 overflow-hidden">
          {selectedLabels.length === 0 ? (
            <span className="text-gray-400">{placeholder}</span>
          ) : (
            <div className="flex items-center gap-1 flex-wrap">
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-azure-100 text-azure-800">
                {selectedLabels.length} selected
              </span>
              {selectedLabels.length <= 2 && selectedLabels.map((label, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 truncate max-w-[150px]"
                  title={label}
                >
                  {label}
                </span>
              ))}
            </div>
          )}
        </div>

        <FiChevronDown
          className={`w-5 h-5 text-gray-400 transition-transform duration-200 ml-2 flex-shrink-0 ${
            isOpen ? 'transform rotate-180' : ''
          }`}
        />
      </button>

      {/* Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.15 }}
            className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg"
            style={{ maxHeight }}
          >
            {/* Search Input */}
            {searchable && (
              <div className="p-2 border-b border-gray-200">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search..."
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-azure-500 focus:border-transparent"
                  onClick={(e) => e.stopPropagation()}
                  aria-label="Search options"
                />
              </div>
            )}

            {/* Select/Deselect All */}
            <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200 bg-gray-50">
              <button
                type="button"
                onClick={selectAll}
                className="text-xs text-azure-600 hover:text-azure-700 font-medium transition-colors"
                aria-label="Select all options"
              >
                Select All
              </button>
              <button
                type="button"
                onClick={deselectAll}
                className="text-xs text-gray-600 hover:text-gray-700 font-medium transition-colors"
                aria-label="Deselect all options"
              >
                Clear
              </button>
            </div>

            {/* Options List */}
            <div
              className="overflow-y-auto"
              style={{ maxHeight: 'calc(' + maxHeight + ' - 100px)' }}
              role="listbox"
              aria-multiselectable="true"
            >
              {filteredOptions.length === 0 ? (
                <div className="px-4 py-3 text-sm text-gray-500 text-center">
                  No options found
                </div>
              ) : (
                filteredOptions.map((option) => {
                  const isSelected = value.includes(option.value);
                  return (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => toggleOption(option.value)}
                      className={`
                        w-full px-4 py-2 text-left flex items-center justify-between
                        transition-colors duration-150
                        ${isSelected
                          ? 'bg-azure-50 text-azure-900'
                          : 'text-gray-700 hover:bg-gray-50'
                        }
                      `}
                      role="option"
                      aria-selected={isSelected}
                    >
                      <div className="flex items-center gap-3">
                        {/* Checkbox */}
                        <div
                          className={`
                            w-4 h-4 rounded border flex items-center justify-center
                            transition-all duration-150
                            ${isSelected
                              ? 'bg-azure-600 border-azure-600'
                              : 'border-gray-300 bg-white'
                            }
                          `}
                        >
                          {isSelected && (
                            <FiCheck className="w-3 h-3 text-white" />
                          )}
                        </div>

                        <span className="text-sm">{option.label}</span>
                      </div>

                      {/* Count Badge */}
                      {option.count !== undefined && (
                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                          {option.count}
                        </span>
                      )}
                    </button>
                  );
                })
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default MultiSelect;
