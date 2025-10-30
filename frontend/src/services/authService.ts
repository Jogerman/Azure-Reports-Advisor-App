import apiClient from './apiClient';
import { API_ENDPOINTS } from '../config/api';

export interface User {
  id: string;
  name?: string;
  full_name?: string;
  first_name?: string;
  last_name?: string;
  email: string;
  role?: string;
  roles?: string[];
  is_active?: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
}

export interface LoginRequest {
  access_token: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
  user: User;
}

/**
 * Authentication service for backend API calls
 */
class AuthService {
  /**
   * Login with Azure AD access token
   */
  async login(accessToken: string): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>(
      API_ENDPOINTS.AUTH.LOGIN,
      { access_token: accessToken }
    );
    return response.data;
  }

  /**
   * Logout from the backend
   */
  async logout(): Promise<void> {
    await apiClient.post(API_ENDPOINTS.AUTH.LOGOUT);
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>(API_ENDPOINTS.AUTH.USER);
    return response.data;
  }

  /**
   * Refresh authentication token
   */
  async refreshToken(): Promise<{ token: string }> {
    const response = await apiClient.post<{ token: string }>(
      API_ENDPOINTS.AUTH.REFRESH
    );
    return response.data;
  }
}

const authService = new AuthService();
export default authService;