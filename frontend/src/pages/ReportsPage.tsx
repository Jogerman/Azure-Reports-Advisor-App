import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { FiArrowRight, FiChevronRight, FiList, FiUploadCloud, FiCloud, FiPlus, FiTrash2, FiEdit3, FiCheck } from 'react-icons/fi';
import { clientService, reportService, ReportType, ManualRecommendation, RecommendationCategory, BusinessImpact } from '../services';
import { Button, Card, LoadingSpinner, showToast } from '../components/common';
import { CSVUploader, ReportTypeSelector, ReportList } from '../components/reports';
import { azureSubscriptionApi, createReportFromAzureAPI } from '../services/azureIntegrationApi';
import { DataSource, AzureReportFilters } from '../types/azureIntegration';

type Step = 'select-client' | 'select-data-source' | 'upload-csv' | 'select-azure-subscription' | 'manual-input' | 'select-type' | 'view-reports';

// Constants for form options
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

// ManualInputStep Component
interface ManualInputStepProps {
  selectedClient: any;
  dataSource: DataSource;
  selectedFile: File | null;
  wantsManualInput: boolean | null;
  manualRecommendations: ManualRecommendation[];
  onWantsManualInputChange: (wants: boolean | null) => void;
  onRecommendationsChange: (recs: ManualRecommendation[]) => void;
  onBack: () => void;
  onContinue: () => void;
}

const ManualInputStep: React.FC<ManualInputStepProps> = ({
  selectedClient,
  dataSource,
  selectedFile,
  wantsManualInput,
  manualRecommendations,
  onWantsManualInputChange,
  onRecommendationsChange,
  onBack,
  onContinue,
}) => {
  const handleAddRecommendation = () => {
    onRecommendationsChange([...manualRecommendations, emptyRecommendation()]);
  };

  const handleRemoveRecommendation = (index: number) => {
    if (manualRecommendations.length === 1) return;
    onRecommendationsChange(manualRecommendations.filter((_, i) => i !== index));
  };

  const handleRecommendationChange = (
    index: number,
    field: keyof ManualRecommendation,
    value: any
  ) => {
    const updated = [...manualRecommendations];
    updated[index] = { ...updated[index], [field]: value };
    onRecommendationsChange(updated);
  };

  const canContinue = wantsManualInput === false ||
    (wantsManualInput === true && manualRecommendations.length > 0 &&
     manualRecommendations.every(rec => rec.category && rec.business_impact && rec.recommendation.trim()));

  return (
    <Card>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">
            Step 4: Manual Recommendations (Optional)
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Client: <span className="font-medium">{selectedClient?.company_name}</span> •
            Data Source: <span className="font-medium">{dataSource === 'csv' ? 'CSV Upload' : 'Azure API'}</span>
            {dataSource === 'csv' && selectedFile && (
              <> • File: <span className="font-medium">{selectedFile.name}</span></>
            )}
          </p>
        </div>
        <Button variant="ghost" onClick={onBack}>
          Back
        </Button>
      </div>

      {/* Question Card */}
      {wantsManualInput === null && (
        <div className="space-y-6">
          <div className="bg-azure-50 border border-azure-200 rounded-lg p-6">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <FiEdit3 className="h-6 w-6 text-azure-600" />
              </div>
              <div className="ml-3 flex-1">
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  ¿Deseas agregar recomendaciones manuales?
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Puedes añadir recomendaciones personalizadas que se incluirán en el reporte junto con las recomendaciones de Azure Advisor.
                </p>
                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    onClick={() => onWantsManualInputChange(false)}
                  >
                    No, continuar sin recomendaciones
                  </Button>
                  <Button
                    variant="primary"
                    onClick={() => {
                      onWantsManualInputChange(true);
                      if (manualRecommendations.length === 0) {
                        onRecommendationsChange([emptyRecommendation()]);
                      }
                    }}
                  >
                    Sí, agregar recomendaciones
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Form Area */}
      {wantsManualInput === true && (
        <div className="space-y-6">
          {/* Summary Badge */}
          <div className="flex items-center justify-between bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center">
              <FiCheck className="h-5 w-5 text-green-600 mr-2" />
              <span className="text-sm font-medium text-green-900">
                {manualRecommendations.length} recomendación(es) agregada(s)
              </span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                onWantsManualInputChange(null);
                onRecommendationsChange([]);
              }}
            >
              Cancelar
            </Button>
          </div>

          {/* Recommendations Forms */}
          <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
            {manualRecommendations.map((rec, index) => (
              <div
                key={index}
                className="border border-gray-200 rounded-lg p-4 bg-gray-50 space-y-4"
              >
                {/* Header with remove button */}
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-medium text-gray-700">
                    Recomendación #{index + 1}
                  </h4>
                  {manualRecommendations.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveRecommendation(index)}
                      className="text-red-600 hover:text-red-800 flex items-center text-sm"
                    >
                      <FiTrash2 className="mr-1" size={16} />
                      Eliminar
                    </button>
                  )}
                </div>

                {/* Required fields */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Categoría <span className="text-red-500">*</span>
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
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-azure-500 focus:border-azure-500"
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
                      Impacto de Negocio <span className="text-red-500">*</span>
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
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-azure-500 focus:border-azure-500"
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
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Recomendación <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={rec.recommendation}
                    onChange={(e) =>
                      handleRecommendationChange(index, 'recommendation', e.target.value)
                    }
                    rows={3}
                    maxLength={5000}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-azure-500 focus:border-azure-500"
                    placeholder="Describe la recomendación en detalle..."
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {rec.recommendation.length}/5000 caracteres
                  </p>
                </div>

                {/* Optional fields - Azure Resource Information */}
                <details className="group">
                  <summary className="text-sm font-medium text-azure-600 cursor-pointer hover:text-azure-700 flex items-center">
                    <FiChevronRight className="mr-1 transition-transform group-open:rotate-90" />
                    Detalles de Recursos Azure (Opcional)
                  </summary>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3 pl-6">
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        ID de Suscripción
                      </label>
                      <input
                        type="text"
                        value={rec.subscription_id || ''}
                        onChange={(e) =>
                          handleRecommendationChange(index, 'subscription_id', e.target.value)
                        }
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:ring-azure-500 focus:border-azure-500"
                        placeholder="ej., sub-123"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Nombre de Suscripción
                      </label>
                      <input
                        type="text"
                        value={rec.subscription_name || ''}
                        onChange={(e) =>
                          handleRecommendationChange(index, 'subscription_name', e.target.value)
                        }
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:ring-azure-500 focus:border-azure-500"
                        placeholder="ej., Producción"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Grupo de Recursos
                      </label>
                      <input
                        type="text"
                        value={rec.resource_group || ''}
                        onChange={(e) =>
                          handleRecommendationChange(index, 'resource_group', e.target.value)
                        }
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:ring-azure-500 focus:border-azure-500"
                        placeholder="ej., rg-produccion"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Nombre de Recurso
                      </label>
                      <input
                        type="text"
                        value={rec.resource_name || ''}
                        onChange={(e) =>
                          handleRecommendationChange(index, 'resource_name', e.target.value)
                        }
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:ring-azure-500 focus:border-azure-500"
                        placeholder="ej., vm-web-01"
                      />
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Tipo de Recurso
                      </label>
                      <input
                        type="text"
                        value={rec.resource_type || ''}
                        onChange={(e) =>
                          handleRecommendationChange(index, 'resource_type', e.target.value)
                        }
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:ring-azure-500 focus:border-azure-500"
                        placeholder="ej., Microsoft.Compute/virtualMachines"
                      />
                    </div>
                  </div>
                </details>

                {/* Optional fields - Cost Information */}
                <details className="group">
                  <summary className="text-sm font-medium text-azure-600 cursor-pointer hover:text-azure-700 flex items-center">
                    <FiChevronRight className="mr-1 transition-transform group-open:rotate-90" />
                    Detalles de Costo e Impacto (Opcional)
                  </summary>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-3 pl-6">
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Ahorro Potencial
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
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:ring-azure-500 focus:border-azure-500"
                        placeholder="ej., 1200.00"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Moneda
                      </label>
                      <select
                        value={rec.currency || 'USD'}
                        onChange={(e) =>
                          handleRecommendationChange(index, 'currency', e.target.value)
                        }
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:ring-azure-500 focus:border-azure-500"
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
                        Impacto en Advisor Score (0-100)
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
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:ring-azure-500 focus:border-azure-500"
                        placeholder="ej., 5.0"
                      />
                    </div>
                    <div className="md:col-span-3">
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Beneficios Potenciales
                      </label>
                      <textarea
                        value={rec.potential_benefits || ''}
                        onChange={(e) =>
                          handleRecommendationChange(index, 'potential_benefits', e.target.value)
                        }
                        rows={2}
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:ring-azure-500 focus:border-azure-500"
                        placeholder="Describe los beneficios esperados..."
                      />
                    </div>
                  </div>
                </details>
              </div>
            ))}
          </div>

          {/* Add recommendation button */}
          <div>
            <button
              type="button"
              onClick={handleAddRecommendation}
              className="flex items-center text-azure-600 hover:text-azure-800 text-sm font-medium"
            >
              <FiPlus className="mr-1" size={16} />
              Agregar otra recomendación
            </button>
          </div>
        </div>
      )}

      {/* Continue button */}
      {(wantsManualInput === false || (wantsManualInput === true && canContinue)) && (
        <div className="flex justify-end mt-6 pt-4 border-t border-gray-200">
          <Button
            variant="primary"
            icon={<FiArrowRight />}
            onClick={onContinue}
          >
            Continuar al Tipo de Reporte
          </Button>
        </div>
      )}
    </Card>
  );
};

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
  const [manualRecommendations, setManualRecommendations] = useState<ManualRecommendation[]>([]);
  const [wantsManualInput, setWantsManualInput] = useState<boolean | null>(null);

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
    onSuccess: async (report) => {
      showToast.success('CSV uploaded successfully! Report is being processed...');
      queryClient.invalidateQueries({ queryKey: ['reports'] });

      // If there are manual recommendations, add them to the report
      if (manualRecommendations.length > 0) {
        try {
          await reportService.addManualRecommendations(report.id, manualRecommendations);
          showToast.success(`Added ${manualRecommendations.length} manual recommendation(s) to the report`);
        } catch (error) {
          showToast.error('Report created, but failed to add manual recommendations');
        }
      }

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
    onSuccess: async (report) => {
      showToast.success('Report creation initiated from Azure API!');
      queryClient.invalidateQueries({ queryKey: ['reports'] });

      // If there are manual recommendations, add them to the report
      if (manualRecommendations.length > 0) {
        try {
          await reportService.addManualRecommendations(report.id, manualRecommendations);
          showToast.success(`Added ${manualRecommendations.length} manual recommendation(s) to the report`);
        } catch (error) {
          showToast.error('Report created, but failed to add manual recommendations');
        }
      }

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

  const handleContinueToManualInput = () => {
    if ((dataSource === 'csv' && selectedFile) || (dataSource === 'azure_api' && selectedAzureSubscription)) {
      setCurrentStep('manual-input');
      setWantsManualInput(null); // Reset manual input choice
    }
  };

  const handleContinueToReportType = () => {
    setCurrentStep('select-type');
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

  const handleGenerateReport = async () => {
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
    setManualRecommendations([]);
    setWantsManualInput(null);
    setCurrentStep('select-client');
  };

  const renderStepIndicator = () => {
    const steps = [
      { id: 'select-client', label: 'Select Client' },
      { id: 'select-data-source', label: 'Data Source' },
      { id: dataSource === 'csv' ? 'upload-csv' : 'select-azure-subscription', label: dataSource === 'csv' ? 'Upload CSV' : 'Azure Subscription' },
      { id: 'manual-input', label: 'Manual Input' },
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
              onClick={handleContinueToManualInput}
              disabled={!selectedFile}
            >
              Continue to Manual Input
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
              onClick={handleContinueToManualInput}
              disabled={!selectedAzureSubscription}
            >
              Continue to Manual Input
            </Button>
          </div>
        </Card>
      )}

      {/* Step 4: Manual Input */}
      {currentStep === 'manual-input' && (
        <ManualInputStep
          selectedClient={selectedClient}
          dataSource={dataSource}
          selectedFile={selectedFile}
          wantsManualInput={wantsManualInput}
          manualRecommendations={manualRecommendations}
          onWantsManualInputChange={setWantsManualInput}
          onRecommendationsChange={setManualRecommendations}
          onBack={() => setCurrentStep(dataSource === 'csv' ? 'upload-csv' : 'select-azure-subscription')}
          onContinue={handleContinueToReportType}
        />
      )}

      {/* Step 5: Select Report Type */}
      {currentStep === 'select-type' && (
        <Card>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Step 5: Select Report Type
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
              onClick={() => setCurrentStep('manual-input')}
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
