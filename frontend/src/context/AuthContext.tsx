import React, { createContext, useContext, useState, useEffect, ReactNode, useRef } from 'react';
import { PublicClientApplication, AccountInfo, AuthenticationResult } from '@azure/msal-browser';
import { msalConfig, loginRequest } from '../config/authConfig';
import { showToast } from '../components/common/Toast';
import authService from '../services/authService';

// Initialize MSAL instance
export const msalInstance = new PublicClientApplication(msalConfig);

interface User {
  id: string;
  name?: string;
  email: string;
  role?: string;
  roles?: string[];
}

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  getAccessToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);

  const loadUserProfile = async (account: AccountInfo, azureToken: string) => {
    try {
      console.log('Authenticating with backend using Azure AD token...');

      // Call backend login endpoint with Azure AD token
      const backendResponse = await authService.login(azureToken);

      console.log('Backend authentication successful:', backendResponse);

      // Store backend JWT tokens
      localStorage.setItem('access_token', backendResponse.access_token);
      localStorage.setItem('refresh_token', backendResponse.refresh_token);

      // Set user data from backend response
      const userData: User = {
        id: backendResponse.user.id,
        name: backendResponse.user.full_name || backendResponse.user.name,
        email: backendResponse.user.email,
        role: backendResponse.user.role,
        roles: backendResponse.user.role ? [backendResponse.user.role] : [],
      };

      setUser(userData);
      setIsAuthenticated(true);
    } catch (error: any) {
      console.error('Error loading user profile from backend:', error);
      showToast.error('Failed to authenticate with backend: ' + (error.response?.data?.error || error.message));
      // Clear any partial authentication state
      setUser(null);
      setIsAuthenticated(false);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      throw error;
    }
  };

  const handleAuthenticationResponse = async (response: AuthenticationResult) => {
    if (response.account) {
      msalInstance.setActiveAccount(response.account);
      // Use the Azure AD token to authenticate with backend
      const azureToken = response.idToken || response.accessToken;
      if (azureToken) {
        await loadUserProfile(response.account, azureToken);
      } else {
        console.error('No Azure AD token received');
        showToast.error('Authentication failed: No token received');
      }
    }
  };

  // Prevent double initialization in React.StrictMode
  const isInitializingRef = useRef(false);

  // Initialize MSAL and check for existing authentication
  useEffect(() => {
    // Prevent double initialization in React.StrictMode
    if (isInitializingRef.current) return;
    isInitializingRef.current = true;

    const initializeMsal = async () => {
      try {
        await msalInstance.initialize();

        // Handle redirect response
        const response = await msalInstance.handleRedirectPromise();
        if (response) {
          await handleAuthenticationResponse(response);
        } else {
          // Check if user is already signed in
          const accounts = msalInstance.getAllAccounts();
          const backendToken = localStorage.getItem('access_token');

          if (accounts.length > 0 && backendToken) {
            // User has both Azure AD session and backend token
            msalInstance.setActiveAccount(accounts[0]);

            // Try to load user profile from backend
            try {
              const userProfile = await authService.getCurrentUser();
              const userData: User = {
                id: userProfile.id,
                name: userProfile.full_name || userProfile.name,
                email: userProfile.email,
                role: userProfile.role,
                roles: userProfile.role ? [userProfile.role] : [],
              };
              setUser(userData);
              setIsAuthenticated(true);
            } catch (error) {
              // Backend token might be expired, get new token from Azure AD
              console.log('Backend token expired, re-authenticating...');
              try {
                const azureToken = await msalInstance.acquireTokenSilent({
                  ...loginRequest,
                  account: accounts[0],
                });
                await loadUserProfile(accounts[0], azureToken.idToken || azureToken.accessToken);
              } catch (silentError) {
                // Silent token acquisition failed, clear cache and require interactive login
                console.log('Silent token refresh failed, clearing cache');
                await msalInstance.clearCache();
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
              }
            }
          } else if (accounts.length > 0) {
            // User has Azure AD session but no backend token
            console.log('Azure AD session found, authenticating with backend...');
            try {
              const azureToken = await msalInstance.acquireTokenSilent({
                ...loginRequest,
                account: accounts[0],
              });
              msalInstance.setActiveAccount(accounts[0]);
              await loadUserProfile(accounts[0], azureToken.idToken || azureToken.accessToken);
            } catch (silentError: any) {
              // Silent token acquisition failed (iframe timeout, etc.)
              console.log('Silent token acquisition failed, will require interactive login:', silentError);
              // Clear the partial Azure AD session
              await msalInstance.clearCache();
              // User will need to click login button for interactive authentication
            }
          }
        }
      } catch (error) {
        console.error('MSAL initialization error:', error);
        showToast.error('Authentication initialization failed');
      } finally {
        setIsLoading(false);
      }
    };

    initializeMsal();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = async () => {
    try {
      setIsLoading(true);

      // Check if there's already an interaction in progress
      const interactionStatus = msalInstance.getActiveAccount();
      const inProgress = sessionStorage.getItem('msal.interaction.status');

      if (inProgress) {
        console.warn('Interaction already in progress, clearing stale state...');
        // Clear potentially stale interaction state (older than 60 seconds)
        const timestamp = sessionStorage.getItem('msal.interaction.timestamp');
        const now = Date.now();

        if (timestamp && (now - parseInt(timestamp)) > 60000) {
          // Interaction is stale (>60 seconds old), clear it
          sessionStorage.removeItem('msal.interaction.status');
          sessionStorage.removeItem('msal.interaction.timestamp');
          console.log('Cleared stale interaction state');
        } else {
          // Interaction is recent, show warning
          showToast.warning('A sign-in is already in progress. Please wait or refresh the page.');
          setIsLoading(false);
          return;
        }
      }

      // Mark interaction start
      sessionStorage.setItem('msal.interaction.timestamp', Date.now().toString());

      // Use redirect login instead of popup to avoid COOP issues
      await msalInstance.loginRedirect(loginRequest);

      // Note: After redirect, the page will reload and initialization will handle the response
    } catch (error: any) {
      console.error('Login error:', error);

      // Clear interaction tracking on error
      sessionStorage.removeItem('msal.interaction.timestamp');

      // Handle specific MSAL errors with user-friendly messages
      if (error.errorCode === 'user_cancelled') {
        showToast.info('Sign in was cancelled. You can try again anytime.');
      } else if (error.errorCode === 'interaction_in_progress') {
        showToast.warning('A sign-in is already in progress. Please complete it, wait a moment, or refresh the page to clear the state.');
        // Try to clear the interaction state after showing the warning
        setTimeout(() => {
          sessionStorage.removeItem('msal.interaction.status');
          sessionStorage.removeItem('msal.interaction.timestamp');
        }, 3000);
      } else if (error.errorCode === 'no_network') {
        showToast.error('No internet connection. Please check your network and try again.');
      } else if (error.errorCode === 'consent_required') {
        showToast.error('Additional consent is required. Please contact your administrator.');
      } else {
        showToast.error(
          'Sign in failed. ' + (error.errorMessage || 'Please try again or contact support.')
        );
      }
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      setIsLoading(true);

      // Clear backend session
      try {
        await authService.logout();
      } catch (error) {
        console.error('Backend logout error:', error);
      }

      // Clear local storage
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');

      // Clear local state
      setUser(null);
      setIsAuthenticated(false);

      // Logout from Azure AD
      const account = msalInstance.getActiveAccount();
      if (account) {
        await msalInstance.logoutRedirect({
          account,
          postLogoutRedirectUri: msalConfig.auth.postLogoutRedirectUri,
        });
      } else {
        await msalInstance.logoutRedirect();
      }

      // Note: After redirect, local state will be cleared on page reload
    } catch (error: any) {
      console.error('Logout error:', error);

      // Even if logout fails, clear local state
      setUser(null);
      setIsAuthenticated(false);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');

      if (error.errorCode === 'user_cancelled') {
        showToast.info('Sign out was cancelled.');
      } else {
        showToast.error('Sign out encountered an issue, but your session has been cleared.');
      }
      setIsLoading(false);
    }
  };

  const getAccessToken = async (): Promise<string | null> => {
    try {
      // Return backend JWT token
      const backendToken = localStorage.getItem('access_token');
      if (backendToken) {
        return backendToken;
      }

      // If no backend token, try to get one using Azure AD
      const account = msalInstance.getActiveAccount();
      if (!account) {
        return null;
      }

      const azureToken = await msalInstance.acquireTokenSilent({
        ...loginRequest,
        account,
      });

      // Authenticate with backend to get JWT
      const backendResponse = await authService.login(azureToken.idToken || azureToken.accessToken);

      // Store backend tokens
      localStorage.setItem('access_token', backendResponse.access_token);
      localStorage.setItem('refresh_token', backendResponse.refresh_token);

      return backendResponse.access_token;
    } catch (error) {
      console.error('Token acquisition error:', error);
      showToast.error('Failed to acquire authentication token');
      return null;
    }
  };

  const value: AuthContextType = {
    isAuthenticated,
    isLoading,
    user,
    login,
    logout,
    getAccessToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};