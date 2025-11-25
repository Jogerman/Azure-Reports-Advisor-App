import React from 'react';
import { FiEdit2, FiTrash2, FiEye } from 'react-icons/fi';
import { Client } from '../../services';

interface ClientCardProps {
  client: Client;
  onView: (client: Client) => void;
  onEdit: (client: Client) => void;
  onDelete: (client: Client) => void;
}

/**
 * ClientCard Component - Card view for client display
 * Alternative to table view, optimized for mobile and tablet
 */
const ClientCard: React.FC<ClientCardProps> = ({
  client,
  onView,
  onEdit,
  onDelete,
}) => {
  return (
    <div
      className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow duration-200 cursor-pointer"
      onClick={() => onView(client)}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-start space-x-3 flex-1">
          {client.logo && (
            <div className="flex-shrink-0">
              <img
                src={client.logo}
                alt={`${client.company_name} logo`}
                className="h-12 w-12 object-contain border border-gray-200 rounded-lg p-1 bg-white"
              />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 mb-1 truncate">
              {client.company_name}
            </h3>
            <p className="text-sm text-gray-600">
              {client.industry || 'No industry specified'}
            </p>
          </div>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-xs font-medium flex-shrink-0 ml-2 ${
            client.status === 'active'
              ? 'bg-green-100 text-green-800'
              : 'bg-gray-100 text-gray-800'
          }`}
        >
          {client.status}
        </span>
      </div>

      {/* Contact Information */}
      <div className="space-y-2 mb-4">
        {client.contact_email && (
          <div className="flex items-center text-sm text-gray-600">
            <span className="font-medium mr-2">Email:</span>
            <span className="truncate">{client.contact_email}</span>
          </div>
        )}
        {client.contact_phone && (
          <div className="flex items-center text-sm text-gray-600">
            <span className="font-medium mr-2">Phone:</span>
            <span>{client.contact_phone}</span>
          </div>
        )}
      </div>

      {/* Azure Subscriptions */}
      <div className="mb-4 pb-4 border-b border-gray-200">
        <div className="flex items-center text-sm text-gray-600">
          <span className="font-medium mr-2">Azure Subscriptions:</span>
          <span className="text-azure-600 font-semibold">
            {client.azure_subscription_ids?.length || 0}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onView(client);
          }}
          className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-azure-600 hover:text-azure-700 hover:bg-azure-50 rounded-lg transition-colors"
          aria-label="View client details"
        >
          <FiEye className="w-4 h-4 mr-1" />
          View
        </button>

        <div className="flex items-center space-x-1">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onEdit(client);
            }}
            className="p-2 text-gray-600 hover:text-azure-600 hover:bg-azure-50 rounded-lg transition-colors"
            aria-label="Edit client"
          >
            <FiEdit2 className="w-4 h-4" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(client);
            }}
            className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            aria-label="Delete client"
          >
            <FiTrash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Notes Preview (if available) */}
      {client.notes && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500 font-medium mb-1">Notes:</p>
          <p className="text-sm text-gray-600 line-clamp-2">{client.notes}</p>
        </div>
      )}
    </div>
  );
};

export default ClientCard;
