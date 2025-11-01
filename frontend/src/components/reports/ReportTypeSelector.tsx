import React from 'react';
import {
  FiFileText,
  FiDollarSign,
  FiShield,
  FiSettings,
  FiBriefcase,
  FiCheck
} from 'react-icons/fi';
import { ReportType } from '../../services/reportService';

interface ReportTypeOption {
  type: ReportType;
  title: string;
  description: string;
  icon: React.ReactNode;
  audience: string;
  features: string[];
  color: string;
}

interface ReportTypeSelectorProps {
  selectedType: ReportType | null;
  onSelect: (type: ReportType) => void;
  disabled?: boolean;
}

const reportTypes: ReportTypeOption[] = [
  {
    type: 'detailed',
    title: 'Detailed Report',
    description: 'Comprehensive technical analysis with all recommendations',
    icon: <FiFileText className="w-6 h-6" />,
    audience: 'Technical Teams',
    features: [
      'All recommendations with full details',
      'Grouped by category',
      'Resource-level information',
      'Implementation steps',
    ],
    color: 'azure',
  },
  {
    type: 'executive',
    title: 'Executive Summary',
    description: 'High-level overview for leadership and stakeholders',
    icon: <FiBriefcase className="w-6 h-6" />,
    audience: 'Executives & Managers',
    features: [
      'Key metrics dashboard',
      'Top 10 recommendations',
      'Business impact analysis',
      'Visual charts and graphs',
    ],
    color: 'purple',
  },
  {
    type: 'cost',
    title: 'Cost Optimization',
    description: 'Focus on cost savings and resource optimization',
    icon: <FiDollarSign className="w-6 h-6" />,
    audience: 'Finance & Procurement',
    features: [
      'Potential savings breakdown',
      'ROI analysis',
      'Quick wins identification',
      'Cost-focused recommendations',
    ],
    color: 'green',
  },
  {
    type: 'security',
    title: 'Security Assessment',
    description: 'Security recommendations and compliance insights',
    icon: <FiShield className="w-6 h-6" />,
    audience: 'Security Teams',
    features: [
      'Security-focused recommendations',
      'Risk level indicators',
      'Compliance considerations',
      'Remediation priorities',
    ],
    color: 'red',
  },
  {
    type: 'operations',
    title: 'Operational Excellence',
    description: 'Reliability and operational best practices',
    icon: <FiSettings className="w-6 h-6" />,
    audience: 'DevOps & Operations',
    features: [
      'Reliability improvements',
      'Best practices alignment',
      'Automation opportunities',
      'Performance optimization',
    ],
    color: 'orange',
  },
];

const getColorClasses = (color: string, selected: boolean) => {
  const colorMap: Record<string, { border: string; bg: string; icon: string; text: string }> = {
    azure: {
      border: selected ? 'border-azure-500' : 'border-gray-200 hover:border-azure-300',
      bg: selected ? 'bg-azure-50' : 'bg-white hover:bg-azure-50',
      icon: 'bg-azure-100 text-azure-600',
      text: 'text-azure-600',
    },
    purple: {
      border: selected ? 'border-purple-500' : 'border-gray-200 hover:border-purple-300',
      bg: selected ? 'bg-purple-50' : 'bg-white hover:bg-purple-50',
      icon: 'bg-purple-100 text-purple-600',
      text: 'text-purple-600',
    },
    green: {
      border: selected ? 'border-green-500' : 'border-gray-200 hover:border-green-300',
      bg: selected ? 'bg-green-50' : 'bg-white hover:bg-green-50',
      icon: 'bg-green-100 text-green-600',
      text: 'text-green-600',
    },
    red: {
      border: selected ? 'border-red-500' : 'border-gray-200 hover:border-red-300',
      bg: selected ? 'bg-red-50' : 'bg-white hover:bg-red-50',
      icon: 'bg-red-100 text-red-600',
      text: 'text-red-600',
    },
    orange: {
      border: selected ? 'border-orange-500' : 'border-gray-200 hover:border-orange-300',
      bg: selected ? 'bg-orange-50' : 'bg-white hover:bg-orange-50',
      icon: 'bg-orange-100 text-orange-600',
      text: 'text-orange-600',
    },
  };

  return colorMap[color] || colorMap.azure;
};

const ReportTypeSelector: React.FC<ReportTypeSelectorProps> = ({
  selectedType,
  onSelect,
  disabled = false,
}) => {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Select Report Type
        </h3>
        <p className="text-sm text-gray-600">
          Choose the type of report that best fits your needs and audience
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {reportTypes.map((report) => {
          const isSelected = selectedType === report.type;
          const colors = getColorClasses(report.color, isSelected);

          return (
            <button
              key={report.type}
              onClick={() => onSelect(report.type)}
              disabled={disabled}
              className={`
                relative p-5 border-2 rounded-lg text-left transition-all
                ${colors.border}
                ${colors.bg}
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                ${isSelected ? 'ring-2 ring-offset-2 ring-' + report.color + '-500' : ''}
              `}
              aria-label={`Select ${report.title}`}
              aria-pressed={isSelected}
            >
              {/* Selected Indicator */}
              {isSelected && (
                <div className="absolute top-3 right-3">
                  <div className={`w-6 h-6 rounded-full ${colors.icon} flex items-center justify-center`}>
                    <FiCheck className="w-4 h-4" />
                  </div>
                </div>
              )}

              {/* Icon */}
              <div className={`w-12 h-12 rounded-lg ${colors.icon} flex items-center justify-center mb-4`}>
                {report.icon}
              </div>

              {/* Title and Description */}
              <h4 className="text-base font-semibold text-gray-900 mb-2">
                {report.title}
              </h4>
              <p className="text-sm text-gray-600 mb-3">
                {report.description}
              </p>

              {/* Audience */}
              <div className="mb-3">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors.text} bg-${report.color}-100`}>
                  {report.audience}
                </span>
              </div>

              {/* Features */}
              <ul className="space-y-1">
                {report.features.slice(0, 3).map((feature, index) => (
                  <li key={index} className="flex items-start text-xs text-gray-600">
                    <span className="mr-1.5 mt-0.5">•</span>
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </button>
          );
        })}
      </div>

      {/* Selected Report Info */}
      {selectedType && (
        <div className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="flex items-start space-x-3">
            <FiCheck className="w-5 h-5 text-green-600 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-gray-900">
                {reportTypes.find(r => r.type === selectedType)?.title} selected
              </p>
              <p className="text-sm text-gray-600 mt-1">
                This report will include all {reportTypes.find(r => r.type === selectedType)?.features.length} key features
                tailored for {reportTypes.find(r => r.type === selectedType)?.audience.toLowerCase()}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportTypeSelector;
