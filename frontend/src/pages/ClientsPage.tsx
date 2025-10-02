import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { FiPlus, FiSearch, FiFilter, FiEdit2, FiTrash2, FiFileText } from 'react-icons/fi';
import { clientService, Client, ClientListParams } from '../services';
import { Button, Card, LoadingSpinner, Modal, ConfirmDialog, showToast } from '../components/common';
import ClientForm from '../components/clients/ClientForm';

const ClientsPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // State
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingClient, setEditingClient] = useState<Client | null>(null);
  const [deletingClient, setDeletingClient] = useState<Client | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  // Build query params
  const queryParams: ClientListParams = {
    page: currentPage,
    page_size: pageSize,
    search: searchTerm || undefined,
    status: statusFilter !== 'all' ? statusFilter : undefined,
    ordering: '-created_at',
  };

  // Fetch clients
  const { data, isLoading, error } = useQuery({
    queryKey: ['clients', queryParams],
    queryFn: () => clientService.getClients(queryParams),
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => clientService.deleteClient(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      showToast.success('Client deleted successfully');
      setDeletingClient(null);
    },
    onError: () => {
      showToast.error('Failed to delete client');
    },
  });

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    setCurrentPage(1); // Reset to first page on search
  };

  const handleStatusFilter = (status: 'all' | 'active' | 'inactive') => {
    setStatusFilter(status);
    setCurrentPage(1);
  };

  const handleEdit = (client: Client) => {
    setEditingClient(client);
  };

  const handleDelete = (client: Client) => {
    setDeletingClient(client);
  };

  const handleViewDetails = (client: Client) => {
    navigate(`/clients/${client.id}`);
  };

  const handleFormSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['clients'] });
    setShowAddModal(false);
    setEditingClient(null);
  };

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Failed to load clients. Please try again.</p>
      </div>
    );
  }

  const clients = data?.results || [];
  const totalCount = data?.count || 0;
  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Clients</h1>
          <p className="text-gray-600 mt-1">
            Manage your client organizations and their Azure subscriptions
          </p>
        </div>
        <Button
          variant="primary"
          icon={<FiPlus />}
          onClick={() => setShowAddModal(true)}
        >
          Add Client
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search clients by name..."
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-azure-500 focus:border-transparent"
            />
          </div>

          {/* Status Filter */}
          <div className="flex items-center space-x-2">
            <FiFilter className="text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => handleStatusFilter(e.target.value as any)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-azure-500 focus:border-transparent"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
          <span>
            Showing {clients.length} of {totalCount} clients
          </span>
          {searchTerm && (
            <button
              onClick={() => handleSearch('')}
              className="text-azure-600 hover:text-azure-700 font-medium"
            >
              Clear search
            </button>
          )}
        </div>
      </Card>

      {/* Client List */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" text="Loading clients..." />
        </div>
      ) : clients.length === 0 ? (
        <Card className="text-center py-12">
          <p className="text-gray-600 mb-4">
            {searchTerm
              ? 'No clients found matching your search'
              : 'No clients yet. Add your first client to get started!'}
          </p>
          {!searchTerm && (
            <Button
              variant="primary"
              icon={<FiPlus />}
              onClick={() => setShowAddModal(true)}
            >
              Add First Client
            </Button>
          )}
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {clients.map((client) => (
            <Card
              key={client.id}
              hoverable
              onClick={() => handleViewDetails(client)}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    {client.company_name}
                  </h3>
                  <p className="text-sm text-gray-600 mb-2">
                    {client.industry || 'No industry specified'}
                  </p>
                  {client.contact_email && (
                    <p className="text-sm text-gray-500">{client.contact_email}</p>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      client.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {client.status}
                  </span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200 flex items-center justify-between">
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <span>
                    {client.azure_subscription_ids?.length || 0} subscriptions
                  </span>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEdit(client);
                    }}
                    className="p-2 text-gray-600 hover:text-azure-600 hover:bg-azure-50 rounded-lg transition-colors"
                    aria-label="Edit client"
                  >
                    <FiEdit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(client);
                    }}
                    className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    aria-label="Delete client"
                  >
                    <FiTrash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
          >
            Previous
          </Button>
          <span className="text-sm text-gray-600">
            Page {currentPage} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
          >
            Next
          </Button>
        </div>
      )}

      {/* Add/Edit Modal */}
      <Modal
        isOpen={showAddModal || !!editingClient}
        onClose={() => {
          setShowAddModal(false);
          setEditingClient(null);
        }}
        title={editingClient ? 'Edit Client' : 'Add New Client'}
        size="lg"
      >
        <ClientForm
          client={editingClient || undefined}
          onSuccess={handleFormSuccess}
          onCancel={() => {
            setShowAddModal(false);
            setEditingClient(null);
          }}
        />
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={!!deletingClient}
        onClose={() => setDeletingClient(null)}
        onConfirm={() => deletingClient && deleteMutation.mutate(deletingClient.id)}
        title="Delete Client"
        message={`Are you sure you want to delete "${deletingClient?.company_name}"? This action cannot be undone.`}
        confirmText="Delete"
        variant="danger"
        loading={deleteMutation.isPending}
      />
    </div>
  );
};

export default ClientsPage;