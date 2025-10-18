import clientService from './clientService';
import apiClient from './apiClient';
import { mockClient, mockApiResponse, mockApiError } from '../utils/test-utils';

// Mock the apiClient
jest.mock('./apiClient');
const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('ClientService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getClients', () => {
    // Test 1: Get clients without parameters
    it('fetches clients list without parameters', async () => {
      const mockResponse = {
        count: 1,
        next: null,
        previous: null,
        results: [mockClient],
      };

      mockedApiClient.get.mockResolvedValue({ data: mockResponse });

      const result = await clientService.getClients();

      expect(mockedApiClient.get).toHaveBeenCalledWith('/clients/', {
        params: undefined,
      });
      expect(result).toEqual(mockResponse);
      expect(result.results).toHaveLength(1);
      expect(result.count).toBe(1);
    });

    // Test 2: Get clients with pagination
    it('fetches clients with pagination parameters', async () => {
      const mockResponse = {
        count: 50,
        next: 'next-url',
        previous: null,
        results: [mockClient],
      };

      mockedApiClient.get.mockResolvedValue({ data: mockResponse });

      const params = { page: 2, page_size: 10 };
      const result = await clientService.getClients(params);

      expect(mockedApiClient.get).toHaveBeenCalledWith('/clients/', {
        params,
      });
      expect(result.count).toBe(50);
      expect(result.next).toBe('next-url');
    });

    // Test 3: Get clients with search
    it('fetches clients with search parameter', async () => {
      const mockResponse = {
        count: 1,
        next: null,
        previous: null,
        results: [mockClient],
      };

      mockedApiClient.get.mockResolvedValue({ data: mockResponse });

      const params = { search: 'Test Company' };
      await clientService.getClients(params);

      expect(mockedApiClient.get).toHaveBeenCalledWith('/clients/', {
        params,
      });
    });

    // Test 4: Get clients with status filter
    it('fetches clients filtered by status', async () => {
      const mockResponse = {
        count: 1,
        next: null,
        previous: null,
        results: [mockClient],
      };

      mockedApiClient.get.mockResolvedValue({ data: mockResponse });

      const params = { status: 'active' as const };
      await clientService.getClients(params);

      expect(mockedApiClient.get).toHaveBeenCalledWith('/clients/', {
        params,
      });
    });

    // Test 5: Get clients with industry filter
    it('fetches clients filtered by industry', async () => {
      const mockResponse = {
        count: 1,
        next: null,
        previous: null,
        results: [mockClient],
      };

      mockedApiClient.get.mockResolvedValue({ data: mockResponse });

      const params = { industry: 'Technology' };
      await clientService.getClients(params);

      expect(mockedApiClient.get).toHaveBeenCalledWith('/clients/', {
        params,
      });
    });

    // Test 6: Get clients with ordering
    it('fetches clients with ordering', async () => {
      const mockResponse = {
        count: 1,
        next: null,
        previous: null,
        results: [mockClient],
      };

      mockedApiClient.get.mockResolvedValue({ data: mockResponse });

      const params = { ordering: '-created_at' };
      await clientService.getClients(params);

      expect(mockedApiClient.get).toHaveBeenCalledWith('/clients/', {
        params,
      });
    });

    // Test 7: Handle API error
    it('throws error when API request fails', async () => {
      mockedApiClient.get.mockRejectedValue(new Error('Network error'));

      await expect(clientService.getClients()).rejects.toThrow('Network error');
    });
  });

  describe('getClient', () => {
    // Test 8: Get single client by ID
    it('fetches single client by ID', async () => {
      mockedApiClient.get.mockResolvedValue({ data: mockClient });

      const result = await clientService.getClient(mockClient.id);

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        `/clients/${mockClient.id}/`
      );
      expect(result).toEqual(mockClient);
      expect(result.id).toBe(mockClient.id);
      expect(result.company_name).toBe(mockClient.company_name);
    });

    // Test 9: Handle client not found
    it('throws error when client not found', async () => {
      mockedApiClient.get.mockRejectedValue({
        response: { status: 404, data: { message: 'Client not found' } },
      });

      await expect(clientService.getClient('invalid-id')).rejects.toMatchObject({
        response: { status: 404 },
      });
    });
  });

  describe('createClient', () => {
    // Test 10: Create new client with minimal data
    it('creates new client with minimal required data', async () => {
      const createData = {
        company_name: 'New Company',
      };

      const newClient = {
        ...mockClient,
        ...createData,
      };

      mockedApiClient.post.mockResolvedValue({ data: newClient });

      const result = await clientService.createClient(createData);

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        '/clients/',
        createData
      );
      expect(result.company_name).toBe('New Company');
    });

    // Test 11: Create new client with complete data
    it('creates new client with all fields', async () => {
      const createData = {
        company_name: 'Complete Company',
        industry: 'Healthcare',
        contact_email: 'info@complete.com',
        contact_phone: '+1-555-0200',
        azure_subscription_ids: ['sub-123', 'sub-456'],
        notes: 'Important client',
      };

      const newClient = {
        ...mockClient,
        ...createData,
      };

      mockedApiClient.post.mockResolvedValue({ data: newClient });

      const result = await clientService.createClient(createData);

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        '/clients/',
        createData
      );
      expect(result.company_name).toBe(createData.company_name);
      expect(result.industry).toBe(createData.industry);
      expect(result.contact_email).toBe(createData.contact_email);
      expect(result.azure_subscription_ids).toEqual(createData.azure_subscription_ids);
    });

    // Test 12: Handle validation error
    it('throws error when validation fails', async () => {
      mockedApiClient.post.mockRejectedValue({
        response: {
          status: 400,
          data: { company_name: ['This field is required.'] },
        },
      });

      await expect(
        clientService.createClient({ company_name: '' })
      ).rejects.toMatchObject({
        response: { status: 400 },
      });
    });
  });

  describe('updateClient', () => {
    // Test 13: Update client with partial data
    it('updates client with partial data', async () => {
      const updateData = {
        company_name: 'Updated Company',
      };

      const updatedClient = {
        ...mockClient,
        ...updateData,
      };

      mockedApiClient.patch.mockResolvedValue({ data: updatedClient });

      const result = await clientService.updateClient(mockClient.id, updateData);

      expect(mockedApiClient.patch).toHaveBeenCalledWith(
        `/clients/${mockClient.id}/`,
        updateData
      );
      expect(result.company_name).toBe('Updated Company');
    });

    // Test 14: Update client status
    it('updates client status', async () => {
      const updateData = {
        status: 'inactive' as const,
      };

      const updatedClient = {
        ...mockClient,
        status: 'inactive' as const,
      };

      mockedApiClient.patch.mockResolvedValue({ data: updatedClient });

      const result = await clientService.updateClient(mockClient.id, updateData);

      expect(result.status).toBe('inactive');
    });

    // Test 15: Update multiple client fields
    it('updates multiple client fields at once', async () => {
      const updateData = {
        company_name: 'Multi Updated',
        industry: 'Finance',
        contact_email: 'new@email.com',
      };

      const updatedClient = {
        ...mockClient,
        ...updateData,
      };

      mockedApiClient.patch.mockResolvedValue({ data: updatedClient });

      const result = await clientService.updateClient(mockClient.id, updateData);

      expect(result.company_name).toBe(updateData.company_name);
      expect(result.industry).toBe(updateData.industry);
      expect(result.contact_email).toBe(updateData.contact_email);
    });
  });

  describe('deleteClient', () => {
    // Test 16: Delete client successfully
    it('deletes client successfully', async () => {
      mockedApiClient.delete.mockResolvedValue({ data: null });

      await clientService.deleteClient(mockClient.id);

      expect(mockedApiClient.delete).toHaveBeenCalledWith(
        `/clients/${mockClient.id}/`
      );
    });

    // Test 17: Handle delete error
    it('throws error when delete fails', async () => {
      mockedApiClient.delete.mockRejectedValue({
        response: { status: 404, data: { message: 'Client not found' } },
      });

      await expect(clientService.deleteClient('invalid-id')).rejects.toMatchObject(
        {
          response: { status: 404 },
        }
      );
    });

    // Test 18: Delete non-existent client
    it('handles deletion of non-existent client', async () => {
      mockedApiClient.delete.mockRejectedValue({
        response: { status: 404 },
      });

      await expect(
        clientService.deleteClient('non-existent-id')
      ).rejects.toMatchObject({
        response: { status: 404 },
      });
    });
  });
});
