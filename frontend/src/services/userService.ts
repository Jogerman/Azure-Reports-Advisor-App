/**
 * User Management Service
 * Handles all user management API calls including listing, creating, updating roles, and activating/deactivating users.
 */

import apiClient from './apiClient';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: 'admin' | 'manager' | 'analyst' | 'viewer';
  role_display: string;
  job_title?: string;
  department?: string;
  phone_number?: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  last_login?: string;
  created_at: string;
  avatar_url?: string;
}

export interface UserListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: User[];
}

export interface UserStatistics {
  total_users: number;
  active_users: number;
  inactive_users: number;
  users_by_role: Record<string, number>;
}

export interface CreateUserRequest {
  email: string;
  username?: string;
  first_name: string;
  last_name: string;
  password: string;
  role: string;
  job_title?: string;
  department?: string;
  phone_number?: string;
  is_staff?: boolean;
}

export interface UpdateUserRequest {
  first_name?: string;
  last_name?: string;
  job_title?: string;
  department?: string;
  phone_number?: string;
  role?: string;
  is_active?: boolean;
}

class UserService {
  private basePath = '/users';

  /**
   * Get list of all users (paginated)
   */
  async getUsers(params?: {
    page?: number;
    page_size?: number;
    role?: string;
    is_active?: boolean;
    search?: string;
  }): Promise<UserListResponse> {
    const response = await apiClient.get<UserListResponse>(this.basePath, { params });
    return response.data;
  }

  /**
   * Get a specific user by ID
   */
  async getUser(userId: number): Promise<User> {
    const response = await apiClient.get<User>(`${this.basePath}/${userId}/`);
    return response.data;
  }

  /**
   * Create a new user
   */
  async createUser(userData: CreateUserRequest): Promise<User> {
    const response = await apiClient.post<User>(this.basePath + '/', userData);
    return response.data;
  }

  /**
   * Update an existing user
   */
  async updateUser(userId: number, userData: UpdateUserRequest): Promise<User> {
    const response = await apiClient.patch<User>(`${this.basePath}/${userId}/`, userData);
    return response.data;
  }

  /**
   * Delete a user
   */
  async deleteUser(userId: number): Promise<void> {
    await apiClient.delete(`${this.basePath}/${userId}/`);
  }

  /**
   * Activate a user account
   */
  async activateUser(userId: number): Promise<User> {
    const response = await apiClient.post<User>(`${this.basePath}/${userId}/activate/`);
    return response.data;
  }

  /**
   * Deactivate a user account
   */
  async deactivateUser(userId: number): Promise<User> {
    const response = await apiClient.post<User>(`${this.basePath}/${userId}/deactivate/`);
    return response.data;
  }

  /**
   * Change user role
   */
  async changeUserRole(userId: number, role: string): Promise<User> {
    const response = await apiClient.post<User>(
      `${this.basePath}/${userId}/change-role/`,
      { role }
    );
    return response.data;
  }

  /**
   * Get user statistics
   */
  async getUserStatistics(): Promise<UserStatistics> {
    const response = await apiClient.get<UserStatistics>(`${this.basePath}/statistics/`);
    return response.data;
  }
}

export const userService = new UserService();
export default userService;
