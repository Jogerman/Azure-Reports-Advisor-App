import apiClient from './apiClient';
import { API_ENDPOINTS } from '../config/api';

export interface User {
  id: string;
  name: string;
  email: string;
  roles: string[];
}

export interface LoginRequest {
  accessToken: string;
}

export interface LoginResponse {
  user: User;
  token: string;
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
      { accessToken }
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