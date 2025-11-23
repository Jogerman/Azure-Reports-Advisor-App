/**
 * ManualRecommendationForm Component (v1.7.0)
 *
 * Modal form for manually adding recommendations to a report.
 * Allows users to input custom recommendations not captured by Azure Advisor.
 */

import React, { useState } from 'react';

interface ManualRecommendation {
  category: 'cost' | 'security' | 'reliability' | 'operational_excellence' | 'performance';
  business_impact: 'high' | 'medium' | 'low';
  recommendation: string;
  subscription_id?: string;
  subscription_name?: string;
  resource_group?: string;
  resource_name?: string;
  resource_type?: string;
  potential_savings?: number;
  currency?: string;
  potential_benefits?: string;
  retirement_date?: string;
  retiring_feature?: string;
  advisor_score_impact?: number;
}

interface ManualRecommendationFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (recommendations: ManualRecommendation[]) => Promise<void>;
  reportId?: string;
}

const CATEGORY_OPTIONS = [
  { value: 'cost', label: 'Cost' },
  { value: 'security', label: 'Security' },
  { value: 'reliability', label: 'Reliability' },
  { value: 'operational_excellence', label: 'Operational Excellence' },
  { value: 'performance', label: 'Performance' },
];

const IMPACT_OPTIONS = [
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
];

const EMPTY_RECOMMENDATION: ManualRecommendation = {
  category: 'cost',
  business_impact: 'medium',
  recommendation: '',
  subscription_id: '',
  subscription_name: '',
  resource_group: '',
  resource_name: '',
  resource_type: '',
  potential_savings: 0,
  currency: 'USD',
  potential_benefits: '',
  retirement_date: '',
  retiring_feature: '',
  advisor_score_impact: 0,
};

export const ManualRecommendationForm: React.FC<ManualRecommendationFormProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [recommendations, setRecommendations] = useState<ManualRecommendation[]>([
    { ...EMPTY_RECOMMENDATION },
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState<boolean[]>([false]);

  const addRecommendation = () => {
    setRecommendations([...recommendations, { ...EMPTY_RECOMMENDATION }]);
    setShowAdvanced([...showAdvanced, false]);
  };

  const removeRecommendation = (index: number) => {
    const newRecommendations = recommendations.filter((_, i) => i !== index);
    const newShowAdvanced = showAdvanced.filter((_, i) => i !== index);
    setRecommendations(newRecommendations.length > 0 ? newRecommendations : [{ ...EMPTY_RECOMMENDATION }]);
    setShowAdvanced(newShowAdvanced.length > 0 ? newShowAdvanced : [false]);
  };

  const updateRecommendation = (index: number, field: keyof ManualRecommendation, value: any) => {
    const newRecommendations = [...recommendations];
    newRecommendations[index] = { ...newRecommendations[index], [field]: value };
    setRecommendations(newRecommendations);
  };

  const toggleAdvanced = (index: number) => {
    const newShowAdvanced = [...showAdvanced];
    newShowAdvanced[index] = !newShowAdvanced[index];
    setShowAdvanced(newShowAdvanced);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      // Filter out empty recommendations
      const validRecommendations = recommendations.filter(
        (rec) => rec.recommendation.trim() !== ''
      );

      if (validRecommendations.length === 0) {
        alert('Please add at least one recommendation');
        return;
      }

      await onSubmit(validRecommendations);

      // Reset form
      setRecommendations([{ ...EMPTY_RECOMMENDATION }]);
      setShowAdvanced([false]);
      onClose();
    } catch (error) {
      console.error('Failed to submit manual recommendations:', error);
      alert('Failed to add recommendations. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setRecommendations([{ ...EMPTY_RECOMMENDATION }]);
      setShowAdvanced([false]);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-blue-600 text-white px-6 py-4 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">Add Manual Recommendations</h2>
            <p className="text-sm text-blue-100 mt-1">
              Add custom recommendations not captured by Azure Advisor
            </p>
          </div>
          <button
            onClick={handleClose}
            disabled={isSubmitting}
            className="text-white hover:text-gray-200 text-2xl leading-none disabled:opacity-50"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {/* Form Content */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto">
          <div className="p-6 space-y-6">
            {recommendations.map((rec, index) => (
              <div
                key={index}
                className="border border-gray-300 rounded-lg p-4 bg-gray-50"
              >
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold text-gray-800">
                    Recommendation {index + 1}
                  </h3>
                  {recommendations.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeRecommendation(index)}
                      className="text-red-600 hover:text-red-800 text-sm font-medium"
                    >
                      Remove
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Category */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Category <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={rec.category}
                      onChange={(e) =>
                        updateRecommendation(index, 'category', e.target.value)
                      }
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    >
                      {CATEGORY_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Business Impact */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Business Impact <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={rec.business_impact}
                      onChange={(e) =>
                        updateRecommendation(index, 'business_impact', e.target.value)
                      }
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    >
                      {IMPACT_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Recommendation Text */}
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Recommendation <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      value={rec.recommendation}
                      onChange={(e) =>
                        updateRecommendation(index, 'recommendation', e.target.value)
                      }
                      required
                      rows={3}
                      placeholder="Describe the recommendation..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  {/* Potential Savings */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Potential Annual Savings
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={rec.potential_savings || ''}
                      onChange={(e) =>
                        updateRecommendation(
                          index,
                          'potential_savings',
                          parseFloat(e.target.value) || 0
                        )
                      }
                      placeholder="0.00"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  {/* Currency */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Currency
                    </label>
                    <input
                      type="text"
                      value={rec.currency}
                      onChange={(e) =>
                        updateRecommendation(index, 'currency', e.target.value)
                      }
                      placeholder="USD"
                      maxLength={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>

                {/* Advanced Options Toggle */}
                <button
                  type="button"
                  onClick={() => toggleAdvanced(index)}
                  className="mt-4 text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center"
                >
                  {showAdvanced[index] ? '▼' : '▶'} Advanced Options
                </button>

                {/* Advanced Options */}
                {showAdvanced[index] && (
                  <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-200">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Subscription ID
                      </label>
                      <input
                        type="text"
                        value={rec.subscription_id}
                        onChange={(e) =>
                          updateRecommendation(index, 'subscription_id', e.target.value)
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Subscription Name
                      </label>
                      <input
                        type="text"
                        value={rec.subscription_name}
                        onChange={(e) =>
                          updateRecommendation(index, 'subscription_name', e.target.value)
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Resource Group
                      </label>
                      <input
                        type="text"
                        value={rec.resource_group}
                        onChange={(e) =>
                          updateRecommendation(index, 'resource_group', e.target.value)
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Resource Name
                      </label>
                      <input
                        type="text"
                        value={rec.resource_name}
                        onChange={(e) =>
                          updateRecommendation(index, 'resource_name', e.target.value)
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Resource Type
                      </label>
                      <input
                        type="text"
                        value={rec.resource_type}
                        onChange={(e) =>
                          updateRecommendation(index, 'resource_type', e.target.value)
                        }
                        placeholder="e.g., Microsoft.Compute/virtualMachines"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Potential Benefits
                      </label>
                      <textarea
                        value={rec.potential_benefits}
                        onChange={(e) =>
                          updateRecommendation(index, 'potential_benefits', e.target.value)
                        }
                        rows={2}
                        placeholder="Describe the potential benefits..."
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Advisor Score Impact (0-100)
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max="100"
                        value={rec.advisor_score_impact || ''}
                        onChange={(e) =>
                          updateRecommendation(
                            index,
                            'advisor_score_impact',
                            parseFloat(e.target.value) || 0
                          )
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Add Another Button */}
            <button
              type="button"
              onClick={addRecommendation}
              disabled={recommendations.length >= 100}
              className="w-full py-2 px-4 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-500 hover:text-blue-600 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              + Add Another Recommendation
            </button>
          </div>

          {/* Footer */}
          <div className="bg-gray-100 px-6 py-4 flex justify-between items-center border-t border-gray-300">
            <p className="text-sm text-gray-600">
              {recommendations.length} recommendation{recommendations.length !== 1 ? 's' : ''}
            </p>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleClose}
                disabled={isSubmitting}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 font-medium disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Adding...' : 'Add Recommendations'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ManualRecommendationForm;
