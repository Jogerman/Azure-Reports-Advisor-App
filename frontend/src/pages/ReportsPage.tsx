import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { FiArrowRight, FiChevronRight, FiList, FiUploadCloud, FiCloud } from 'react-icons/fi';
import { clientService, reportService, ReportType } from '../services';
import { Button, Card, LoadingSpinner, showToast } from '../components/common';
import { CSVUploader, ReportTypeSelector, ReportList } from '../components/reports';
import { azureSubscriptionApi, createReportFromAzureAPI } from '../services/azureIntegrationApi';
import { DataSource, AzureReportFilters } from '../types/azureIntegration';

type Step = 'select-client' | 'select-data-source' | 'upload-csv' | 'select-azure-subscription' | 'select-type' | 'view-reports';

const ReportsPage: React.FC = () => {
  const queryClient = useQueryClient();

  // State
  const [currentStep, setCurrentStep] = useState<Step>('select-client');
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null);
  const [dataSource, setDataSource] = useState<DataSource>('csv');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedAzureSubscription, setSelectedAzureSubscription] = useState<string | null>(null);
  const [azureFilters, setAzureFilters] = useState<AzureReportFilters>({});
  const [selectedReportType, setSelectedReportType] = useState<ReportType | null>(null);

  // Fetch clients
  const { data: clientsData, isLoading: loadingClients } = useQuery({
    queryKey: ['clients', { page: 1, page_size: 100, status: 'active' }],
    queryFn: () => clientService.getClients({ page: 1, page_size: 100, status: 'active' }),
  });

  // Fetch active Azure subscriptions for the selected client
  const { data: azureSubscriptionsData, isLoading: loadingAzureSubscriptions } = useQuery({
    queryKey: ['azure-subscriptions', { client: selectedClientId, is_active: true }],
    queryFn: () => azureSubscriptionApi.list({ client: selectedClientId!, is_active: true }),
    enabled: !!selectedClientId && dataSource === 'azure_api',
  });

  // Upload CSV mutation
  const uploadMutation = useMutation({
    mutationFn: (data: { client_id: string; csv_file: File; report_type?: ReportType }) =>
      reportService.uploadCSV(data),
    onSuccess: (report) => {
      showToast.success('CSV uploaded successfully! Report is being processed...');
      queryClient.invalidateQueries({ queryKey: ['reports'] });

      // Reset and go to view reports
      setTimeout(() => {
        resetWorkflow();
        setCurrentStep('view-reports');
      }, 1500);
    },
    onError: () => {
      showToast.error('Failed to upload CSV file');
    },
  });

  // Create report from Azure API mutation
  const createFromAzureMutation = useMutation({
    mutationFn: (data: {
      client_id: string;
      report_type: string;
      azure_subscription: string;
      filters?: AzureReportFilters;
    }) => createReportFromAzureAPI(data),
    onSuccess: () => {
      showToast.success('Report creation initiated from Azure API!');
      queryClient.invalidateQueries({ queryKey: ['reports'] });

      // Reset and go to view reports
      setTimeout(() => {
        resetWorkflow();
        setCurrentStep('view-reports');
      }, 1500);
    },
    onError: (error: any) => {
      showToast.error(error.response?.data?.detail || 'Failed to create report from Azure API');
    },
  });

  const clients = clientsData?.results || [];
  const azureSubscriptions = azureSubscriptionsData?.results || [];
  const selectedClient = clients.find((c) => c.id === selectedClientId);

  const handleClientSelect = (clientId: string) => {
    setSelectedClientId(clientId);
    setCurrentStep('select-data-source');
  };

  const handleDataSourceSelect = (source: DataSource) => {
    setDataSource(source);
    if (source === 'csv') {
      setCurrentStep('upload-csv');
    } else {
      setCurrentStep('select-azure-subscription');
    }
  };

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
  };

  const handleFileRemove = () => {
    setSelectedFile(null);
  };

  const handleContinueToReportType = () => {
    if ((dataSource === 'csv' && selectedFile) || (dataSource === 'azure_api' && selectedAzureSubscription)) {
      setCurrentStep('select-type');
    }
  };

  const handleReportTypeSelect = (type: ReportType) => {
    setSelectedReportType(type);
  };

  const handleAzureFilterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setAzureFilters(prev => ({
      ...prev,
      [name]: value || undefined,
    }));
  };

  const handleGenerateReport = () => {
    if (!selectedClientId || !selectedReportType) return;

    if (dataSource === 'csv' && selectedFile) {
      uploadMutation.mutate({
        client_id: selectedClientId,
        csv_file: selectedFile,
        report_type: selectedReportType,
      });
    } else if (dataSource === 'azure_api' && selectedAzureSubscription) {
      createFromAzureMutation.mutate({
        client_id: selectedClientId,
        report_type: selectedReportType,
        azure_subscription: selectedAzureSubscription,
        filters: Object.keys(azureFilters).length > 0 ? azureFilters : undefined,
      });
    }
  };

  const resetWorkflow = () => {
    setSelectedClientId(null);
    setDataSource('csv');
    setSelectedFile(null);
    setSelectedAzureSubscription(null);
    setAzureFilters({});
    setSelectedReportType(null);
    setCurrentStep('select-client');
  };

  const renderStepIndicator = () => {
    const steps = [
      { id: 'select-client', label: 'Select Client' },
      { id: 'select-data-source', label: 'Data Source' },
      { id: dataSource === 'csv' ? 'upload-csv' : 'select-azure-subscription', label: dataSource === 'csv' ? 'Upload CSV' : 'Azure Subscription' },
      { id: 'select-type', label: 'Select Type' },
    ];

    const currentIndex = steps.findIndex((s) => s.id === currentStep);

    return (
      <div className="flex items-center justify-center mb-8">
        {steps.map((step, index) => (
          <React.Fragment key={step.id}>
            <div
              className={`flex items-center space-x-2 ${
                index <= currentIndex ? 'text-azure-600' : 'text-gray-400'
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold ${
                  index < currentIndex
                    ? 'bg-azure-600 text-white'
                    : index === currentIndex
                    ? 'bg-azure-100 text-azure-600 border-2 border-azure-600'
                    : 'bg-gray-100 text-gray-400'
                }`}
              >
                {index + 1}
              </div>
              <span className="text-sm font-medium hidden sm:inline">{step.label}</span>
            </div>
            {index < steps.length - 1 && (
              <FiChevronRight className="mx-2 sm:mx-4 text-gray-400" />
            )}
          </React.Fragment>
        ))}
      </div>
    );
  };

  const isGenerating = uploadMutation.isPending || createFromAzureMutation.isPending;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* Page Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Reports</h1>
          <p className="text-gray-600">
            Upload Azure Advisor CSV files or connect to Azure API to generate professional reports.
          </p>
        </div>

        {currentStep !== 'view-reports' && (
          <Button
            variant="outline"
            icon={<FiList />}
            onClick={() => setCurrentStep('view-reports')}
          >
            View All Reports
          </Button>
        )}

        {currentStep === 'view-reports' && (
          <Button
            variant="primary"
            onClick={resetWorkflow}
          >
            Generate New Report
          </Button>
        )}
      </div>

      {/* Step Indicator (only show when not viewing reports) */}
      {currentStep !== 'view-reports' && renderStepIndicator()}

      {/* Step 1: Select Client */}
      {currentStep === 'select-client' && (
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Step 1: Select Client
          </h2>
          <p className="text-gray-600 mb-6">
            Choose the client for which you want to generate a report
          </p>

          {loadingClients ? (
            <div className="flex justify-center py-12">
              <LoadingSpinner size="lg" text="Loading clients..." />
            </div>
          ) : clients.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600 mb-4">
                No active clients found. Please add a client first.
              </p>
              <Button variant="primary" onClick={() => window.location.href = '/clients'}>
                Go to Clients
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {clients.map((client) => (
                <button
                  key={client.id}
                  onClick={() => handleClientSelect(client.id)}
                  className="p-4 border-2 border-gray-200 rounded-lg text-left hover:border-azure-500 hover:bg-azure-50 transition-all"
                >
                  <h3 className="font-semibold text-gray-900">{client.company_name}</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {client.industry || 'No industry'}
                  </p>
                  <p className="text-xs text-gray-500 mt-2">
                    {client.azure_subscription_ids?.length || 0} subscriptions
                  </p>
                </button>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Step 2: Select Data Source */}
      {currentStep === 'select-data-source' && selectedClient && (
        <Card>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 2: Select Data Source
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Client: <span className="font-medium">{selectedClient.company_name}</span>
              </p>
            </div>
            <Button variant="ghost" onClick={() => setCurrentStep('select-client')}>
              Change Client
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* CSV Upload Option */}
            <button
              onClick={() => handleDataSourceSelect('csv')}
              className={`p-6 border-2 rounded-lg text-left transition-all ${
                dataSource === 'csv'
                  ? 'border-azure-500 bg-azure-50'
                  : 'border-gray-200 hover:border-azure-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-center w-16 h-16 bg-blue-100 rounded-lg mb-4">
                <FiUploadCloud className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">CSV Upload</h3>
              <p className="text-sm text-gray-600">
                Upload an exported CSV file from Azure Advisor to generate your report.
              </p>
              <ul className="mt-3 text-xs text-gray-500 space-y-1">
                <li>• Works offline</li>
                <li>• No Azure credentials needed</li>
                <li>• Manual export required</li>
              </ul>
            </button>

            {/* Azure API Option */}
            <button
              onClick={() => handleDataSourceSelect('azure_api')}
              className={`p-6 border-2 rounded-lg text-left transition-all ${
                dataSource === 'azure_api'
                  ? 'border-azure-500 bg-azure-50'
                  : 'border-gray-200 hover:border-azure-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-center w-16 h-16 bg-green-100 rounded-lg mb-4">
                <FiCloud className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Azure API</h3>
              <p className="text-sm text-gray-600">
                Connect directly to Azure API to fetch the latest recommendations automatically.
              </p>
              <ul className="mt-3 text-xs text-gray-500 space-y-1">
                <li>• Real-time data</li>
                <li>• Automated sync</li>
                <li>• Requires Azure credentials</li>
              </ul>
            </button>
          </div>
        </Card>
      )}

      {/* Step 3a: Upload CSV */}
      {currentStep === 'upload-csv' && selectedClient && (
        <Card>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 3: Upload Azure Advisor CSV
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Client: <span className="font-medium">{selectedClient.company_name}</span> •
                Data Source: <span className="font-medium">CSV Upload</span>
              </p>
            </div>
            <Button variant="ghost" onClick={() => setCurrentStep('select-data-source')}>
              Change Data Source
            </Button>
          </div>

          <CSVUploader
            selectedFile={selectedFile}
            onFileSelect={handleFileSelect}
            onFileRemove={handleFileRemove}
          />

          <div className="flex justify-end mt-6">
            <Button
              variant="primary"
              icon={<FiArrowRight />}
              onClick={handleContinueToReportType}
              disabled={!selectedFile}
            >
              Continue to Report Type
            </Button>
          </div>
        </Card>
      )}

      {/* Step 3b: Select Azure Subscription */}
      {currentStep === 'select-azure-subscription' && selectedClient && (
        <Card>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 3: Select Azure Subscription
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Client: <span className="font-medium">{selectedClient.company_name}</span> •
                Data Source: <span className="font-medium">Azure API</span>
              </p>
            </div>
            <Button variant="ghost" onClick={() => setCurrentStep('select-data-source')}>
              Change Data Source
            </Button>
          </div>

          {loadingAzureSubscriptions ? (
            <div className="flex justify-center py-12">
              <LoadingSpinner size="lg" text="Loading subscriptions..." />
            </div>
          ) : azureSubscriptions.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600 mb-4">
                No active Azure subscriptions configured for <span className="font-medium">{selectedClient?.company_name}</span>.
              </p>
              <p className="text-sm text-gray-500 mb-4">
                Add Azure API credentials from the client details page to enable automated reports.
              </p>
              <Button variant="primary" onClick={() => window.location.href = `/clients/${selectedClientId}`}>
                Go to Client Details
              </Button>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Subscription Selector */}
              <div>
                <label htmlFor="azure-subscription" className="block text-sm font-medium text-gray-700 mb-2">
                  Azure Subscription <span className="text-red-500">*</span>
                </label>
                <select
                  id="azure-subscription"
                  value={selectedAzureSubscription || ''}
                  onChange={(e) => setSelectedAzureSubscription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-azure-500"
                >
                  <option value="">Select a subscription...</option>
                  {azureSubscriptions.map((sub) => (
                    <option key={sub.id} value={sub.id}>
                      {sub.name} ({sub.subscription_id})
                    </option>
                  ))}
                </select>
              </div>

              {/* Optional Filters */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3">
                  Filters (Optional)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label htmlFor="category" className="block text-sm text-gray-600 mb-1">
                      Category
                    </label>
                    <select
                      id="category"
                      name="category"
                      value={azureFilters.category || ''}
                      onChange={handleAzureFilterChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-azure-500"
                    >
                      <option value="">All Categories</option>
                      <option value="Cost">Cost</option>
                      <option value="HighAvailability">High Availability</option>
                      <option value="Performance">Performance</option>
                      <option value="Security">Security</option>
                      <option value="OperationalExcellence">Operational Excellence</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="impact" className="block text-sm text-gray-600 mb-1">
                      Impact Level
                    </label>
                    <select
                      id="impact"
                      name="impact"
                      value={azureFilters.impact || ''}
                      onChange={handleAzureFilterChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-azure-500"
                    >
                      <option value="">All Impact Levels</option>
                      <option value="High">High</option>
                      <option value="Medium">Medium</option>
                      <option value="Low">Low</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="resource_group" className="block text-sm text-gray-600 mb-1">
                      Resource Group
                    </label>
                    <input
                      type="text"
                      id="resource_group"
                      name="resource_group"
                      value={azureFilters.resource_group || ''}
                      onChange={handleAzureFilterChange}
                      placeholder="e.g., rg-production"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-azure-500"
                    />
                  </div>
                </div>
                <p className="mt-2 text-xs text-gray-500">
                  Apply filters to narrow down recommendations included in the report
                </p>
              </div>
            </div>
          )}

          <div className="flex justify-end mt-6">
            <Button
              variant="primary"
              icon={<FiArrowRight />}
              onClick={handleContinueToReportType}
              disabled={!selectedAzureSubscription}
            >
              Continue to Report Type
            </Button>
          </div>
        </Card>
      )}

      {/* Step 4: Select Report Type */}
      {currentStep === 'select-type' && (
        <Card>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 4: Select Report Type
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Client: <span className="font-medium">{selectedClient?.company_name}</span> •
                Data Source: <span className="font-medium">{dataSource === 'csv' ? 'CSV Upload' : 'Azure API'}</span>
                {dataSource === 'csv' && selectedFile && (
                  <> • File: <span className="font-medium">{selectedFile.name}</span></>
                )}
              </p>
            </div>
            <Button
              variant="ghost"
              onClick={() => setCurrentStep(dataSource === 'csv' ? 'upload-csv' : 'select-azure-subscription')}
            >
              Back
            </Button>
          </div>

          <ReportTypeSelector
            selectedType={selectedReportType}
            onSelect={handleReportTypeSelect}
            disabled={isGenerating}
          />

          <div className="flex justify-end mt-6">
            <Button
              variant="primary"
              onClick={handleGenerateReport}
              disabled={!selectedReportType || isGenerating}
              loading={isGenerating}
            >
              {isGenerating ? 'Generating Report...' : 'Generate Report'}
            </Button>
          </div>
        </Card>
      )}

      {/* View All Reports */}
      {currentStep === 'view-reports' && (
        <div className="space-y-6">
          <Card>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              All Reports
            </h2>
            <p className="text-gray-600">
              View, download, and manage all generated reports from both CSV uploads and Azure API
            </p>
          </Card>

          <ReportList showClientName={true} />
        </div>
      )}
    </motion.div>
  );
};

export default ReportsPage;
