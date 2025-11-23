import React, { useState } from 'react';
import { FiX, FiPlus, FiTrash2, FiAlertCircle } from 'react-icons/fi';
import {
  ManualRecommendation,
  RecommendationCategory,
  BusinessImpact,
} from '../../services/reportService';

interface ManualRecommendationFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (recommendations: ManualRecommendation[]) => Promise<void>;
  reportId: string;
}

const CATEGORY_OPTIONS: { value: RecommendationCategory; label: string }[] = [
  { value: 'cost', label: 'Cost Optimization' },
  { value: 'security', label: 'Security' },
  { value: 'reliability', label: 'Reliability' },
  { value: 'operational_excellence', label: 'Operational Excellence' },
  { value: 'performance', label: 'Performance' },
];

const IMPACT_OPTIONS: { value: BusinessImpact; label: string }[] = [
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
];

const CURRENCY_OPTIONS = ['USD', 'EUR', 'GBP', 'MXN'];

const emptyRecommendation = (): ManualRecommendation => ({
  category: 'cost',
  business_impact: 'medium',
  recommendation: '',
  subscription_id: '',
  subscription_name: '',
  resource_group: '',
  resource_name: '',
  resource_type: '',
  potential_savings: undefined,
  currency: 'USD',
  potential_benefits: '',
  advisor_score_impact: undefined,
});

const ManualRecommendationForm: React.FC<ManualRecommendationFormProps> = ({
  isOpen,
  onClose,
  onSubmit,
  reportId,
}) => {
  const [recommendations, setRecommendations] = useState<ManualRecommendation[]>([
    emptyRecommendation(),
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleAddRecommendation = () => {
    setRecommendations([...recommendations, emptyRecommendation()]);
  };

  const handleRemoveRecommendation = (index: number) => {
    if (recommendations.length === 1) return;
    setRecommendations(recommendations.filter((_, i) => i !== index));
  };

  const handleRecommendationChange = (
    index: number,
    field: keyof ManualRecommendation,
    value: any
  ) => {
    const updated = [...recommendations];
    updated[index] = { ...updated[index], [field]: value };
    setRecommendations(updated);
  };

  const validateRecommendations = (): boolean => {
    for (const rec of recommendations) {
      if (!rec.category || !rec.business_impact || !rec.recommendation.trim()) {
        setError('Category, Business Impact, and Recommendation text are required fields.');
        return false;
      }
      if (rec.recommendation.length > 5000) {
        setError('Recommendation text must be less than 5000 characters.');
        return false;
      }
      if (rec.potential_savings !== undefined && rec.potential_savings < 0) {
        setError('Potential savings must be a non-negative number.');
        return false;
      }
      if (
        rec.advisor_score_impact !== undefined &&
        (rec.advisor_score_impact < 0 || rec.advisor_score_impact > 100)
      ) {
        setError('Advisor score impact must be between 0 and 100.');
        return false;
      }
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateRecommendations()) {
      return;
    }

    setIsSubmitting(true);
    try {
      // Filter out empty optional fields
      const cleanedRecommendations = recommendations.map((rec) => {
        const cleaned: any = {
          category: rec.category,
          business_impact: rec.business_impact,
          recommendation: rec.recommendation,
        };

        if (rec.subscription_id?.trim()) cleaned.subscription_id = rec.subscription_id;
        if (rec.subscription_name?.trim()) cleaned.subscription_name = rec.subscription_name;
        if (rec.resource_group?.trim()) cleaned.resource_group = rec.resource_group;
        if (rec.resource_name?.trim()) cleaned.resource_name = rec.resource_name;
        if (rec.resource_type?.trim()) cleaned.resource_type = rec.resource_type;
        if (rec.potential_savings !== undefined) cleaned.potential_savings = rec.potential_savings;
        if (rec.currency?.trim()) cleaned.currency = rec.currency;
        if (rec.potential_benefits?.trim()) cleaned.potential_benefits = rec.potential_benefits;
        if (rec.retirement_date?.trim()) cleaned.retirement_date = rec.retirement_date;
        if (rec.retiring_feature?.trim()) cleaned.retiring_feature = rec.retiring_feature;
        if (rec.advisor_score_impact !== undefined)
          cleaned.advisor_score_impact = rec.advisor_score_impact;

        return cleaned;
      });

      await onSubmit(cleanedRecommendations);
      handleClose();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to add manual recommendations');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setRecommendations([emptyRecommendation()]);
    setError(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-start justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={handleClose}
        ></div>

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full sm:p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Add Manual Recommendations</h3>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-500 focus:outline-none"
            >
              <FiX size={24} />
            </button>
          </div>

          {/* Error message */}
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-3 flex items-start">
              <FiAlertCircle className="text-red-500 mr-2 mt-0.5" size={20} />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit}>
            <div className="max-h-[60vh] overflow-y-auto mb-4">
              {recommendations.map((rec, index) => (
                <div
                  key={index}
                  className="border border-gray-200 rounded-lg p-4 mb-4 bg-gray-50"
                >
                  {/* Header with remove button */}
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-medium text-gray-700">
                      Recommendation #{index + 1}
                    </h4>
                    {recommendations.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveRecommendation(index)}
                        className="text-red-600 hover:text-red-800 flex items-center text-sm"
                      >
                        <FiTrash2 className="mr-1" size={16} />
                        Remove
                      </button>
                    )}
                  </div>

                  {/* Required fields */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Category <span className="text-red-500">*</span>
                      </label>
                      <select
                        value={rec.category}
                        onChange={(e) =>
                          handleRecommendationChange(
                            index,
                            'category',
                            e.target.value as RecommendationCategory
                          )
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                        required
                      >
                        {CATEGORY_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Business Impact <span className="text-red-500">*</span>
                      </label>
                      <select
                        value={rec.business_impact}
                        onChange={(e) =>
                          handleRecommendationChange(
                            index,
                            'business_impact',
                            e.target.value as BusinessImpact
                          )
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                        required
                      >
                        {IMPACT_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Recommendation text */}
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Recommendation <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      value={rec.recommendation}
                      onChange={(e) =>
                        handleRecommendationChange(index, 'recommendation', e.target.value)
                      }
                      rows={3}
                      maxLength={5000}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Describe the recommendation in detail..."
                      required
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {rec.recommendation.length}/5000 characters
                    </p>
                  </div>

                  {/* Optional fields - Azure Resource Information */}
                  <details className="mb-4">
                    <summary className="text-sm font-medium text-gray-700 cursor-pointer mb-2">
                      Azure Resource Details (Optional)
                    </summary>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pl-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Subscription ID
                        </label>
                        <input
                          type="text"
                          value={rec.subscription_id || ''}
                          onChange={(e) =>
                            handleRecommendationChange(index, 'subscription_id', e.target.value)
                          }
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md"
                          placeholder="e.g., sub-123"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Subscription Name
                        </label>
                        <input
                          type="text"
                          value={rec.subscription_name || ''}
                          onChange={(e) =>
                            handleRecommendationChange(index, 'subscription_name', e.target.value)
                          }
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md"
                          placeholder="e.g., Production"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Resource Group
                        </label>
                        <input
                          type="text"
                          value={rec.resource_group || ''}
                          onChange={(e) =>
                            handleRecommendationChange(index, 'resource_group', e.target.value)
                          }
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md"
                          placeholder="e.g., rg-production"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Resource Name
                        </label>
                        <input
                          type="text"
                          value={rec.resource_name || ''}
                          onChange={(e) =>
                            handleRecommendationChange(index, 'resource_name', e.target.value)
                          }
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md"
                          placeholder="e.g., vm-web-01"
                        />
                      </div>
                      <div className="md:col-span-2">
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Resource Type
                        </label>
                        <input
                          type="text"
                          value={rec.resource_type || ''}
                          onChange={(e) =>
                            handleRecommendationChange(index, 'resource_type', e.target.value)
                          }
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md"
                          placeholder="e.g., Microsoft.Compute/virtualMachines"
                        />
                      </div>
                    </div>
                  </details>

                  {/* Optional fields - Cost Information */}
                  <details>
                    <summary className="text-sm font-medium text-gray-700 cursor-pointer mb-2">
                      Cost & Impact Details (Optional)
                    </summary>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pl-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Potential Savings
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          value={rec.potential_savings || ''}
                          onChange={(e) =>
                            handleRecommendationChange(
                              index,
                              'potential_savings',
                              e.target.value ? parseFloat(e.target.value) : undefined
                            )
                          }
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md"
                          placeholder="e.g., 1200.00"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Currency
                        </label>
                        <select
                          value={rec.currency || 'USD'}
                          onChange={(e) =>
                            handleRecommendationChange(index, 'currency', e.target.value)
                          }
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md"
                        >
                          {CURRENCY_OPTIONS.map((curr) => (
                            <option key={curr} value={curr}>
                              {curr}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Advisor Score Impact (0-100)
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          max="100"
                          value={rec.advisor_score_impact || ''}
                          onChange={(e) =>
                            handleRecommendationChange(
                              index,
                              'advisor_score_impact',
                              e.target.value ? parseFloat(e.target.value) : undefined
                            )
                          }
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md"
                          placeholder="e.g., 5.0"
                        />
                      </div>
                      <div className="md:col-span-3">
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Potential Benefits
                        </label>
                        <textarea
                          value={rec.potential_benefits || ''}
                          onChange={(e) =>
                            handleRecommendationChange(index, 'potential_benefits', e.target.value)
                          }
                          rows={2}
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md"
                          placeholder="Describe the expected benefits..."
                        />
                      </div>
                    </div>
                  </details>
                </div>
              ))}
            </div>

            {/* Add recommendation button */}
            <div className="mb-4">
              <button
                type="button"
                onClick={handleAddRecommendation}
                className="flex items-center text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                <FiPlus className="mr-1" size={16} />
                Add Another Recommendation
              </button>
            </div>

            {/* Footer buttons */}
            <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 font-medium"
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Adding...' : `Add ${recommendations.length} Recommendation${recommendations.length > 1 ? 's' : ''}`}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ManualRecommendationForm;
