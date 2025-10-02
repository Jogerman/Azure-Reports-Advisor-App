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
 */
apiClient.interceptors.request.use(
  async (config) => {
    try {
      const account = msalInstance.getActiveAccount();

      if (account) {
        // Try to acquire token silently
        const response = await msalInstance.acquireTokenSilent({
          ...tokenRequest,
          account,
        });

        if (response.accessToken) {
          config.headers.Authorization = `Bearer ${response.accessToken}`;
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
        const account = msalInstance.getActiveAccount();

        if (account) {
          // Try to acquire token interactively
          const response = await msalInstance.acquireTokenPopup(tokenRequest);

          if (response.accessToken && originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${response.accessToken}`;
            return apiClient(originalRequest);
          }
        }
      } catch (tokenError) {
        console.error('Token refresh failed:', tokenError);
        showToast.error('Session expired. Please sign in again.');

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