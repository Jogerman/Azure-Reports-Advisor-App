/**
 * Runtime Environment Configuration
 *
 * This module provides access to environment variables that can be set at runtime
 * (not just at build time). This is essential for Docker containers where
 * environment variables are injected when the container starts.
 */

// Extend the Window interface to include our runtime environment
declare global {
  interface Window {
    _env_?: {
      REACT_APP_API_URL?: string;
      REACT_APP_AZURE_CLIENT_ID?: string;
      REACT_APP_AZURE_TENANT_ID?: string;
      REACT_APP_AZURE_REDIRECT_URI?: string;
      REACT_APP_ENVIRONMENT?: string;
    };
  }
}

/**
 * Get environment variable value
 * Tries runtime environment first (window._env_), then falls back to build-time (process.env)
 */
export const getEnv = (key: string): string | undefined => {
  // Try runtime environment first (injected by env.sh)
  if (window._env_ && key in window._env_) {
    const value = window._env_[key as keyof typeof window._env_];
    if (value) return value;
  }

  // Fall back to build-time environment
  return process.env[key];
};

/**
 * Get required environment variable (throws if not found)
 */
export const getRequiredEnv = (key: string): string => {
  const value = getEnv(key);
  if (!value) {
    throw new Error(`Required environment variable ${key} is not set`);
  }
  return value;
};

/**
 * Environment configuration object
 */
export const env = {
  // API Configuration
  apiUrl: getEnv('REACT_APP_API_URL') || window.location.origin,

  // Azure AD Configuration
  azureClientId: getEnv('REACT_APP_AZURE_CLIENT_ID') || '',
  azureTenantId: getEnv('REACT_APP_AZURE_TENANT_ID') || '',
  azureRedirectUri: getEnv('REACT_APP_AZURE_REDIRECT_URI') || window.location.origin,

  // Environment
  environment: getEnv('REACT_APP_ENVIRONMENT') || 'production',

  // Computed values
  isDevelopment: getEnv('REACT_APP_ENVIRONMENT') === 'development',
  isProduction: getEnv('REACT_APP_ENVIRONMENT') === 'production',
};

/**
 * Validate that all required environment variables are set
 */
export const validateEnvironment = (): void => {
  const requiredVars = [
    'REACT_APP_AZURE_CLIENT_ID',
    'REACT_APP_AZURE_TENANT_ID',
  ];

  const missingVars = requiredVars.filter(key => !getEnv(key));

  if (missingVars.length > 0) {
    console.error('❌ Missing required environment variables:', missingVars);
    console.error('Runtime env (_env_):', window._env_);
    console.error('Build-time env (process.env):', {
      REACT_APP_AZURE_CLIENT_ID: process.env.REACT_APP_AZURE_CLIENT_ID,
      REACT_APP_AZURE_TENANT_ID: process.env.REACT_APP_AZURE_TENANT_ID,
    });
    throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`);
  }

  // Log configuration for debugging (without sensitive data)
  console.log('✅ Environment Configuration:');
  console.log('  - Source:', window._env_ ? 'Runtime (window._env_)' : 'Build-time (process.env)');
  console.log('  - Client ID:', env.azureClientId?.substring(0, 8) + '...');
  console.log('  - Tenant ID:', env.azureTenantId?.substring(0, 8) + '...');
  console.log('  - Redirect URI:', env.azureRedirectUri);
  console.log('  - Environment:', env.environment);
};
