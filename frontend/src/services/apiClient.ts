import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { msalInstance } from '../context/AuthContext';
import { tokenRequest } from '../config/authConfig';
import { showToast } from '../components/common/Toast';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

/**
 * Create Axios instance with default configuration
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor to add authentication token
 *
 * Note: Using backend JWT tokens for authentication. These are obtained after
 * authenticating with Azure AD and calling the backend login endpoint.
 */
apiClient.interceptors.request.use(
  async (config) => {
    try {
      // First, try to use backend JWT token
      const backendToken = localStorage.getItem('access_token');

      if (backendToken) {
        config.headers.Authorization = `Bearer ${backendToken}`;
        console.log('Using backend JWT token for authentication');
        return config;
      }

      // Fallback: If no backend token, try Azure AD token
      // This can happen during initial authentication
      const account = msalInstance.getActiveAccount();

      if (account) {
        const response = await msalInstance.acquireTokenSilent({
          ...tokenRequest,
          account,
        });

        if (response.idToken) {
          config.headers.Authorization = `Bearer ${response.idToken}`;
          console.log('Using Azure AD idToken for authentication (fallback)');
        } else if (response.accessToken) {
          config.headers.Authorization = `Bearer ${response.accessToken}`;
          console.warn('Using Azure AD accessToken for authentication (fallback)');
        }
      }
    } catch (error) {
      console.error('Error acquiring token:', error);
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor to handle errors globally
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // Handle token expiration (401 errors)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        console.log('Received 401 error, attempting token refresh...');

        // Clear expired backend token
        localStorage.removeItem('access_token');

        // Try to get new token from Azure AD and re-authenticate with backend
        const account = msalInstance.getActiveAccount();

        if (account) {
          // Get fresh Azure AD token
          const azureResponse = await msalInstance.acquireTokenSilent({
            ...tokenRequest,
            account,
          });

          const azureToken = azureResponse.idToken || azureResponse.accessToken;

          // Re-authenticate with backend to get new JWT
          const authService = await import('./authService');
          const backendResponse = await authService.default.login(azureToken);

          // Store new backend tokens
          localStorage.setItem('access_token', backendResponse.access_token);
          localStorage.setItem('refresh_token', backendResponse.refresh_token);

          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${backendResponse.access_token}`;
            return apiClient(originalRequest);
          }
        }
      } catch (tokenError) {
        console.error('Token refresh failed:', tokenError);
        showToast.error('Session expired. Please sign in again.');

        // Clear all auth data
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');

        // Redirect to login
        window.location.href = '/login';
        return Promise.reject(tokenError);
      }
    }

    // Handle other errors
    handleApiError(error);
    return Promise.reject(error);
  }
);

/**
 * Handle API errors and show appropriate toast messages
 */
const handleApiError = (error: AxiosError) => {
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const data = error.response.data as any;

    switch (status) {
      case 400:
        showToast.error(data.message || 'Invalid request. Please check your input.');
        break;
      case 401:
        showToast.error('Unauthorized. Please sign in again.');
        break;
      case 403:
        showToast.error('You don\'t have permission to perform this action.');
        break;
      case 404:
        showToast.error('The requested resource was not found.');
        break;
      case 500:
        showToast.error('Server error. Please try again later.');
        break;
      default:
        showToast.error(data.message || 'An unexpected error occurred.');
    }
  } else if (error.request) {
    // Request made but no response received
    showToast.error('Network error. Please check your internet connection.');
  } else {
    // Something else happened
    showToast.error('An unexpected error occurred.');
  }
};

export default apiClient;