import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FiArrowLeft, FiEdit2, FiTrash2, FiFileText, FiCalendar, FiDollarSign, FiTrendingUp } from 'react-icons/fi';
import { clientService, reportService } from '../services';
import { Button, Card, LoadingSpinner, Modal, ConfirmDialog, showToast } from '../components/common';
import ClientForm from '../components/clients/ClientForm';
import ClientAzureSubscriptions from '../components/clients/ClientAzureSubscriptions';
import ReportComparison from '../components/clients/ReportComparison';
import { format } from 'date-fns';

const ClientDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [activeTab, setActiveTab] = useState<'history' | 'comparison'>('history');

  // Fetch client details
  const { data: client, isLoading: clientLoading } = useQuery({
    queryKey: ['client', id],
    queryFn: () => clientService.getClient(id!),
    enabled: !!id,
  });

  // Fetch client's reports
  const { data: reportsData, isLoading: reportsLoading } = useQuery({
    queryKey: ['reports', { client: id }],
    queryFn: () => reportService.getReports({ client: id }),
    enabled: !!id,
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: () => clientService.deleteClient(id!),
    onSuccess: () => {
      showToast.success('Client deleted successfully');
      navigate('/clients');
    },
    onError: () => {
      showToast.error('Failed to delete client');
    },
  });

  const handleEditSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['client', id] });
    setShowEditModal(false);
  };

  if (clientLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <LoadingSpinner size="lg" text="Loading client details..." />
      </div>
    );
  }

  if (!client) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Client not found</p>
        <Button variant="primary" onClick={() => navigate('/clients')} className="mt-4">
          Back to Clients
        </Button>
      </div>
    );
  }

  const reports = reportsData?.results || [];
  const totalReports = reports.length;
  const completedReports = reports.filter((r) => r.status === 'completed').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            icon={<FiArrowLeft />}
            onClick={() => navigate('/clients')}
          >
            Back
          </Button>
          {client.logo && (
            <div className="flex-shrink-0">
              <img
                src={client.logo}
                alt={`${client.company_name} logo`}
                className="h-16 w-16 object-contain border border-gray-200 rounded-lg p-2 bg-white"
              />
            </div>
          )}
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{client.company_name}</h1>
            <p className="text-gray-600 mt-1">
              {client.industry || 'No industry specified'}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            icon={<FiEdit2 />}
            onClick={() => setShowEditModal(true)}
          >
            Edit
          </Button>
          <Button
            variant="danger"
            icon={<FiTrash2 />}
            onClick={() => setShowDeleteDialog(true)}
          >
            Delete
          </Button>
        </div>
      </div>

      {/* Status Badge */}
      <div>
        <span
          className={`px-4 py-2 rounded-full text-sm font-medium ${
            client.status === 'active'
              ? 'bg-green-100 text-green-800'
              : 'bg-gray-100 text-gray-800'
          }`}
        >
          {client.status}
        </span>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-azure-100 rounded-lg">
              <FiFileText className="w-6 h-6 text-azure-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Reports</p>
              <p className="text-2xl font-bold text-gray-900">{totalReports}</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <FiCalendar className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Completed</p>
              <p className="text-2xl font-bold text-gray-900">{completedReports}</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <FiDollarSign className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Subscriptions</p>
              <p className="text-2xl font-bold text-gray-900">
                {client.azure_subscription_ids?.length || 0}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Client Information */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Client Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <p className="text-sm font-medium text-gray-500">Contact Email</p>
            <p className="text-base text-gray-900 mt-1">
              {client.contact_email || 'Not specified'}
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Contact Phone</p>
            <p className="text-base text-gray-900 mt-1">
              {client.contact_phone || 'Not specified'}
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Created</p>
            <p className="text-base text-gray-900 mt-1">
              {format(new Date(client.created_at), 'MMMM d, yyyy')}
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Last Updated</p>
            <p className="text-base text-gray-900 mt-1">
              {format(new Date(client.updated_at), 'MMMM d, yyyy')}
            </p>
          </div>
        </div>

        {client.notes && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-sm font-medium text-gray-500 mb-2">Notes</p>
            <p className="text-base text-gray-900 whitespace-pre-wrap">{client.notes}</p>
          </div>
        )}
      </Card>

      {/* Azure Subscriptions - New integrated management */}
      <ClientAzureSubscriptions clientId={id!} clientName={client.company_name} />

      {/* Reports Section with Tabs */}
      <div>
        {/* Tab Navigation */}
        <div className="border-b border-gray-200 mb-6">
          <div className="flex items-center justify-between">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('history')}
                className={`${
                  activeTab === 'history'
                    ? 'border-azure-500 text-azure-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
              >
                <FiFileText className="w-4 h-4" />
                <span>Reports History</span>
              </button>
              <button
                onClick={() => setActiveTab('comparison')}
                className={`${
                  activeTab === 'comparison'
                    ? 'border-azure-500 text-azure-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
              >
                <FiTrendingUp className="w-4 h-4" />
                <span>Comparative Analysis</span>
              </button>
            </nav>
            {activeTab === 'history' && (
              <Button
                variant="primary"
                icon={<FiFileText />}
                onClick={() => navigate(`/reports?client=${id}`)}
              >
                Generate Report
              </Button>
            )}
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'history' && (
          <Card>
            {reportsLoading ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner text="Loading reports..." />
              </div>
            ) : reports.length === 0 ? (
              <div className="text-center py-8 text-gray-600">
                No reports generated yet for this client
              </div>
            ) : (
              <div className="space-y-3">
                {reports.map((report) => (
                  <div
                    key={report.id}
                    className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/reports/${report.id}`)}
                  >
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 capitalize">
                        {report.report_type.replace('_', ' ')} Report
                      </p>
                      <p className="text-sm text-gray-600 mt-1">
                        {format(new Date(report.created_at), 'MMMM d, yyyy • h:mm a')}
                      </p>
                    </div>
                    <div>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${
                          report.status === 'completed'
                            ? 'bg-green-100 text-green-800'
                            : report.status === 'failed'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        {report.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        )}

        {activeTab === 'comparison' && (
          <ReportComparison clientId={id!} reports={reports} />
        )}
      </div>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Client"
        size="lg"
      >
        <ClientForm
          client={client}
          onSuccess={handleEditSuccess}
          onCancel={() => setShowEditModal(false)}
        />
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={() => deleteMutation.mutate()}
        title="Delete Client"
        message={`Are you sure you want to delete "${client.company_name}"? This will also delete all associated reports. This action cannot be undone.`}
        confirmText="Delete"
        variant="danger"
        loading={deleteMutation.isPending}
      />
    </div>
  );
};

export default ClientDetailPage;