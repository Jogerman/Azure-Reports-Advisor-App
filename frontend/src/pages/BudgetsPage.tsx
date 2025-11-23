import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import costMonitoringApi from '../services/costMonitoringApi';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { showToast } from '../components/common/Toast';
import BudgetWidget from '../components/cost-monitoring/BudgetWidget';

const BudgetsPage: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState<'ok' | 'warning' | 'exceeded' | ''>('');
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['budgets', statusFilter],
    queryFn: () =>
      costMonitoringApi.budgets.list({
        status: statusFilter || undefined,
        is_active: true,
      }),
  });

  const updateSpendMutation = useMutation({
    mutationFn: (id: string) => costMonitoringApi.budgets.updateSpend(id),
    onSuccess: () => {
      showToast.success('Budget spending updated successfully');
      queryClient.invalidateQueries({ queryKey: ['budgets'] });
    },
    onError: () => showToast.error('Failed to update budget spending'),
  });

  const handleUpdateSpend = (id: string) => {
    updateSpendMutation.mutate(id);
  };

  if (isLoading) {
    return <LoadingSpinner fullScreen text="Loading budgets..." />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Budgets</h1>
          <p className="mt-2 text-gray-600">
            Track and manage your Azure cost budgets
          </p>
        </div>
        <button className="px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700">
          + Create Budget
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex gap-2">
          <button
            onClick={() => setStatusFilter('')}
            className={`px-4 py-2 rounded-md font-medium ${
              statusFilter === ''
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setStatusFilter('ok')}
            className={`px-4 py-2 rounded-md font-medium ${
              statusFilter === 'ok'
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            On Track
          </button>
          <button
            onClick={() => setStatusFilter('warning')}
            className={`px-4 py-2 rounded-md font-medium ${
              statusFilter === 'warning'
                ? 'bg-yellow-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Warning
          </button>
          <button
            onClick={() => setStatusFilter('exceeded')}
            className={`px-4 py-2 rounded-md font-medium ${
              statusFilter === 'exceeded'
                ? 'bg-red-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Exceeded
          </button>
        </div>
      </div>

      {/* Budgets Grid */}
      {data && data.results.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data.results.map((budget) => (
            <BudgetWidget
              key={budget.id}
              budget={budget}
              onUpdate={handleUpdateSpend}
            />
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No budgets found
          </h3>
          <p className="text-gray-500 mb-6">
            {statusFilter
              ? `No budgets with status "${statusFilter}"`
              : 'Create your first budget to start tracking costs'}
          </p>
        </div>
      )}
    </div>
  );
};

export default BudgetsPage;
