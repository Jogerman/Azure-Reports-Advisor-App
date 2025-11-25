import apiClient from './apiClient';
import { API_ENDPOINTS } from '../config/api';

export interface Client {
  id: string;
  company_name: string;
  industry?: string;
  contact_email?: string;
  contact_phone?: string;
  logo?: string | null;
  azure_subscription_ids: string[];
  status: 'active' | 'inactive';
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateClientData {
  company_name: string;
  industry?: string;
  contact_email?: string;
  contact_phone?: string;
  logo?: File | null;
  azure_subscription_ids?: string[];
  notes?: string;
}

export interface UpdateClientData extends Partial<CreateClientData> {
  status?: 'active' | 'inactive';
}

export interface ClientListParams {
  page?: number;
  page_size?: number;
  search?: string;
  status?: 'active' | 'inactive';
  industry?: string;
  ordering?: string;
}

export interface ClientListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Client[];
}

/**
 * Client management service
 */
class ClientService {
  /**
   * Get list of clients with optional filters
   */
  async getClients(params?: ClientListParams): Promise<ClientListResponse> {
    const response = await apiClient.get<ClientListResponse>(
      API_ENDPOINTS.CLIENTS.LIST,
      { params }
    );
    return response.data;
  }

  /**
   * Get single client by ID
   */
  async getClient(id: string): Promise<Client> {
    const response = await apiClient.get<Client>(
      API_ENDPOINTS.CLIENTS.DETAIL(id)
    );
    return response.data;
  }

  /**
   * Create new client
   */
  async createClient(data: CreateClientData): Promise<Client> {
    // If logo is provided, use FormData for file upload
    if (data.logo) {
      const formData = new FormData();

      // Add all fields to FormData
      Object.entries(data).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (key === 'azure_subscription_ids' && Array.isArray(value)) {
            // Send array as JSON string
            formData.append(key, JSON.stringify(value));
          } else if (key === 'logo' && value instanceof File) {
            formData.append(key, value);
          } else {
            formData.append(key, String(value));
          }
        }
      });

      const response = await apiClient.post<Client>(
        API_ENDPOINTS.CLIENTS.CREATE,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      return response.data;
    }

    // If no logo, send as regular JSON
    const response = await apiClient.post<Client>(
      API_ENDPOINTS.CLIENTS.CREATE,
      data
    );
    return response.data;
  }

  /**
   * Update existing client
   */
  async updateClient(id: string, data: UpdateClientData): Promise<Client> {
    // If logo is provided, use FormData for file upload
    if (data.logo) {
      const formData = new FormData();

      // Add all fields to FormData
      Object.entries(data).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (key === 'azure_subscription_ids' && Array.isArray(value)) {
            // Send array as JSON string
            formData.append(key, JSON.stringify(value));
          } else if (key === 'logo' && value instanceof File) {
            formData.append(key, value);
          } else {
            formData.append(key, String(value));
          }
        }
      });

      const response = await apiClient.patch<Client>(
        API_ENDPOINTS.CLIENTS.UPDATE(id),
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      return response.data;
    }

    // If no logo, send as regular JSON
    const response = await apiClient.patch<Client>(
      API_ENDPOINTS.CLIENTS.UPDATE(id),
      data
    );
    return response.data;
  }

  /**
   * Delete client (soft delete)
   */
  async deleteClient(id: string): Promise<void> {
    await apiClient.delete(API_ENDPOINTS.CLIENTS.DELETE(id));
  }
}

const clientService = new ClientService();
export default clientService;