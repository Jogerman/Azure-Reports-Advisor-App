import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { PublicClientApplication, AccountInfo, AuthenticationResult } from '@azure/msal-browser';
import { msalConfig, loginRequest } from '../config/authConfig';
import { showToast } from '../components/common/Toast';

// Initialize MSAL instance
export const msalInstance = new PublicClientApplication(msalConfig);

interface User {
  id: string;
  name: string;
  email: string;
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

  const loadUserProfile = async (account: AccountInfo) => {
    try {
      // Set basic user info from account
      const userData: User = {
        id: account.homeAccountId,
        name: account.name || account.username,
        email: account.username,
        roles: [], // Will be populated from backend
      };

      setUser(userData);
      setIsAuthenticated(true);
    } catch (error) {
      console.error('Error loading user profile:', error);
      showToast.error('Failed to load user profile');
    }
  };

  const handleAuthenticationResponse = async (response: AuthenticationResult) => {
    if (response.account) {
      msalInstance.setActiveAccount(response.account);
      await loadUserProfile(response.account);
    }
  };

  // Initialize MSAL and check for existing authentication
  useEffect(() => {
    const initializeMsal = async () => {
      try {
        await msalInstance.initialize();

        // Handle redirect response
        const response = await msalInstance.handleRedirectPromise();
        if (response) {
          handleAuthenticationResponse(response);
        } else {
          // Check if user is already signed in
          const accounts = msalInstance.getAllAccounts();
          if (accounts.length > 0) {
            msalInstance.setActiveAccount(accounts[0]);
            await loadUserProfile(accounts[0]);
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

      // Use redirect login instead of popup to avoid COOP issues
      await msalInstance.loginRedirect(loginRequest);

      // Note: After redirect, the page will reload and initialization will handle the response
    } catch (error: any) {
      console.error('Login error:', error);

      // Handle specific MSAL errors with user-friendly messages
      if (error.errorCode === 'user_cancelled') {
        showToast.info('Sign in was cancelled. You can try again anytime.');
      } else if (error.errorCode === 'interaction_in_progress') {
        showToast.warning('A sign-in is already in progress. Please complete it or try again.');
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
      const account = msalInstance.getActiveAccount();
      if (!account) {
        return null;
      }

      const response = await msalInstance.acquireTokenSilent({
        ...loginRequest,
        account,
      });

      // Return idToken for backend authentication (contains user identity)
      // For production, consider using custom API scopes and access tokens
      return response.idToken || response.accessToken;
    } catch (error) {
      console.error('Token acquisition error:', error);

      // Try to acquire token interactively
      try {
        const response = await msalInstance.acquireTokenPopup(loginRequest);
        return response.idToken || response.accessToken;
      } catch (popupError) {
        console.error('Interactive token acquisition failed:', popupError);
        showToast.error('Failed to acquire authentication token');
        return null;
      }
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