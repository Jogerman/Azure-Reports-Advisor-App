import React from 'react';
import { Link } from 'react-router-dom';
import { Budget } from '../../types/costMonitoring';

interface BudgetWidgetProps {
  budget: Budget;
  onUpdate?: (id: string) => void;
}

const BudgetWidget: React.FC<BudgetWidgetProps> = ({ budget, onUpdate }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ok':
        return 'bg-green-500';
      case 'warning':
        return 'bg-yellow-500';
      case 'exceeded':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'ok':
        return 'bg-green-100 text-green-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'exceeded':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'ok':
        return 'On Track';
      case 'warning':
        return 'Warning';
      case 'exceeded':
        return 'Exceeded';
      default:
        return status;
    }
  };

  const percentage = parseFloat(budget.percentage_used);
  const currentSpend = parseFloat(budget.current_spend);
  const amount = parseFloat(budget.amount);
  const remaining = parseFloat(budget.amount_remaining);

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <Link
            to={`/cost-monitoring/budgets/${budget.id}`}
            className="text-lg font-semibold text-gray-900 hover:text-blue-600"
          >
            {budget.name}
          </Link>
          {budget.description && (
            <p className="text-sm text-gray-500 mt-1">{budget.description}</p>
          )}
        </div>
        <span
          className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusBadgeColor(
            budget.status
          )}`}
        >
          {getStatusLabel(budget.status)}
        </span>
      </div>

      {/* Amount Info */}
      <div className="mb-4">
        <div className="flex justify-between items-baseline mb-2">
          <span className="text-2xl font-bold text-gray-900">
            {budget.currency} {currentSpend.toLocaleString()}
          </span>
          <span className="text-sm text-gray-500">
            of {budget.currency} {amount.toLocaleString()}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className={`h-3 rounded-full transition-all duration-300 ${getStatusColor(
              budget.status
            )}`}
            style={{ width: `${Math.min(percentage, 100)}%` }}
          />
        </div>

        <div className="flex justify-between items-center mt-2">
          <span className="text-sm font-medium text-gray-700">
            {percentage.toFixed(1)}% used
          </span>
          <span className="text-sm text-gray-500">
            {budget.currency} {remaining.toLocaleString()} remaining
          </span>
        </div>
      </div>

      {/* Period Info */}
      <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
        <div>
          <span className="text-gray-600">Period:</span>
          <p className="font-medium text-gray-900 capitalize">{budget.period}</p>
        </div>
        <div>
          <span className="text-gray-600">Subscription:</span>
          <p className="font-medium text-gray-900">{budget.subscription_name}</p>
        </div>
        <div>
          <span className="text-gray-600">Start Date:</span>
          <p className="font-medium text-gray-900">
            {new Date(budget.start_date).toLocaleDateString()}
          </p>
        </div>
        <div>
          <span className="text-gray-600">End Date:</span>
          <p className="font-medium text-gray-900">
            {new Date(budget.end_date).toLocaleDateString()}
          </p>
        </div>
      </div>

      {/* Thresholds */}
      {budget.thresholds && budget.thresholds.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-gray-600 mb-2">Alert Thresholds:</p>
          <div className="flex flex-wrap gap-2">
            {budget.thresholds
              .filter((t) => t.is_active)
              .sort((a, b) => a.threshold_percentage - b.threshold_percentage)
              .map((threshold) => (
                <span
                  key={threshold.id}
                  className={`px-2 py-1 text-xs rounded ${
                    percentage >= threshold.threshold_percentage
                      ? 'bg-red-100 text-red-800'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {threshold.threshold_percentage}%
                  {threshold.last_triggered && ' (triggered)'}
                </span>
              ))}
          </div>
        </div>
      )}

      {/* Actions */}
      {onUpdate && (
        <button
          onClick={() => onUpdate(budget.id)}
          className="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Update Spending
        </button>
      )}
    </div>
  );
};

export default BudgetWidget;
