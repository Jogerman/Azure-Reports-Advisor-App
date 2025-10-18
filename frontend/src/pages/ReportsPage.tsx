import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { FiArrowRight, FiChevronRight, FiList } from 'react-icons/fi';
import { clientService, reportService, ReportType } from '../services';
import { Button, Card, LoadingSpinner, showToast } from '../components/common';
import { CSVUploader, ReportTypeSelector, ReportList } from '../components/reports';

type Step = 'select-client' | 'upload-csv' | 'select-type' | 'view-reports';

const ReportsPage: React.FC = () => {
  const queryClient = useQueryClient();

  // State
  const [currentStep, setCurrentStep] = useState<Step>('select-client');
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedReportType, setSelectedReportType] = useState<ReportType | null>(null);

  // Fetch clients
  const { data: clientsData, isLoading: loadingClients } = useQuery({
    queryKey: ['clients', { page: 1, page_size: 100, status: 'active' }],
    queryFn: () => clientService.getClients({ page: 1, page_size: 100, status: 'active' }),
  });

  // Upload CSV mutation
  const uploadMutation = useMutation({
    mutationFn: (data: { client_id: string; csv_file: File; report_type?: ReportType }) =>
      reportService.uploadCSV(data),
    onSuccess: (report) => {
      showToast.success('CSV uploaded successfully! Report is being processed...');
      queryClient.invalidateQueries({ queryKey: ['reports'] });

      // CSV processing happens automatically in the backend via Celery
      // No need to trigger it manually anymore

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

  // This mutation is no longer needed since CSV processing is automatic
  // Keeping it here for backwards compatibility but it won't be called

  const clients = clientsData?.results || [];
  const selectedClient = clients.find((c) => c.id === selectedClientId);

  const handleClientSelect = (clientId: string) => {
    setSelectedClientId(clientId);
    setCurrentStep('upload-csv');
  };

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
  };

  const handleFileRemove = () => {
    setSelectedFile(null);
  };

  const handleContinueToReportType = () => {
    if (selectedFile) {
      setCurrentStep('select-type');
    }
  };

  const handleReportTypeSelect = (type: ReportType) => {
    setSelectedReportType(type);
  };

  const handleGenerateReport = () => {
    if (selectedClientId && selectedFile && selectedReportType) {
      uploadMutation.mutate({
        client_id: selectedClientId,
        csv_file: selectedFile,
        report_type: selectedReportType,
      });
    }
  };

  const resetWorkflow = () => {
    setSelectedClientId(null);
    setSelectedFile(null);
    setSelectedReportType(null);
    setCurrentStep('select-client');
  };

  const renderStepIndicator = () => {
    const steps = [
      { id: 'select-client', label: 'Select Client' },
      { id: 'upload-csv', label: 'Upload CSV' },
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
            Upload Azure Advisor CSV files and generate professional reports.
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

      {/* Step 2: Upload CSV */}
      {currentStep === 'upload-csv' && selectedClient && (
        <Card>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 2: Upload Azure Advisor CSV
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Client: <span className="font-medium">{selectedClient.company_name}</span>
              </p>
            </div>
            <Button variant="ghost" onClick={() => setCurrentStep('select-client')}>
              Change Client
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

      {/* Step 3: Select Report Type */}
      {currentStep === 'select-type' && (
        <Card>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 3: Select Report Type
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Client: <span className="font-medium">{selectedClient?.company_name}</span> •
                File: <span className="font-medium">{selectedFile?.name}</span>
              </p>
            </div>
            <Button variant="ghost" onClick={() => setCurrentStep('upload-csv')}>
              Back
            </Button>
          </div>

          <ReportTypeSelector
            selectedType={selectedReportType}
            onSelect={handleReportTypeSelect}
            disabled={uploadMutation.isPending}
          />

          <div className="flex justify-end mt-6">
            <Button
              variant="primary"
              onClick={handleGenerateReport}
              disabled={!selectedReportType || uploadMutation.isPending}
              loading={uploadMutation.isPending}
            >
              {uploadMutation.isPending ? 'Generating Report...' : 'Generate Report'}
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
              View, download, and manage all generated reports
            </p>
          </Card>

          <ReportList showClientName={true} />
        </div>
      )}
    </motion.div>
  );
};

export default ReportsPage;
