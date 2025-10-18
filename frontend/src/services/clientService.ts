import apiClient from './apiClient';
import { API_ENDPOINTS } from '../config/api';

export interface Client {
  id: string;
  company_name: string;
  industry?: string;
  contact_email?: string;
  contact_phone?: string;
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