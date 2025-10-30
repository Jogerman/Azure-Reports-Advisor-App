import { Configuration, PopupRequest } from '@azure/msal-browser';

/**
 * Validate required environment variables for Azure AD authentication
 */
const validateEnvVars = () => {
  const requiredVars = {
    REACT_APP_AZURE_CLIENT_ID: process.env.REACT_APP_AZURE_CLIENT_ID,
    REACT_APP_AZURE_TENANT_ID: process.env.REACT_APP_AZURE_TENANT_ID,
  };

  const missingVars = Object.entries(requiredVars)
    .filter(([_, value]) => !value)
    .map(([key, _]) => key);

  if (missingVars.length > 0) {
    console.error('❌ Missing required Azure AD environment variables:', missingVars);
    console.error('Please check your .env.local or .env.production file');
    throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`);
  }

  // Log configuration for debugging (without sensitive data)
  console.log('✅ Azure AD Configuration initialized:');
  console.log('  - Client ID:', requiredVars.REACT_APP_AZURE_CLIENT_ID?.substring(0, 8) + '...');
  console.log('  - Tenant ID:', requiredVars.REACT_APP_AZURE_TENANT_ID?.substring(0, 8) + '...');
  console.log('  - Redirect URI:', process.env.REACT_APP_AZURE_REDIRECT_URI || window.location.origin);
};

// Validate environment variables on module load
validateEnvVars();

/**
 * Configuration object to be passed to MSAL instance on creation.
 * For a full list of MSAL.js configuration parameters, visit:
 * https://github.com/AzureAD/microsoft-authentication-library-for-js/blob/dev/lib/msal-browser/docs/configuration.md
 */
export const msalConfig: Configuration = {
  auth: {
    clientId: process.env.REACT_APP_AZURE_CLIENT_ID!,
    authority: `https://login.microsoftonline.com/${process.env.REACT_APP_AZURE_TENANT_ID}`,
    redirectUri: process.env.REACT_APP_AZURE_REDIRECT_URI || window.location.origin,
    postLogoutRedirectUri: process.env.REACT_APP_AZURE_POST_LOGOUT_REDIRECT_URI || window.location.origin,
    navigateToLoginRequestUrl: false, // Let React Router handle navigation
  },
  cache: {
    cacheLocation: 'localStorage', // Use localStorage for persistence
    storeAuthStateInCookie: true, // Store state in cookie to ensure persistence across redirects
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) {
          return;
        }
        switch (level) {
          case 0: // LogLevel.Error
            console.error(message);
            return;
          case 1: // LogLevel.Warning
            console.warn(message);
            return;
          case 2: // LogLevel.Info
            console.info(message);
            return;
          case 3: // LogLevel.Verbose
            console.debug(message);
            return;
        }
      },
      logLevel: process.env.NODE_ENV === 'development' ? 3 : 1,
    },
  },
};

/**
 * Scopes you add here will be prompted for user consent during sign-in.
 */
export const loginRequest: PopupRequest = {
  scopes: ['User.Read', 'openid', 'profile', 'email'],
};

/**
 * Add here the scopes to request when obtaining an access token for API calls.
 */
export const tokenRequest = {
  scopes: ['User.Read'],
};

export const graphConfig = {
  graphMeEndpoint: 'https://graph.microsoft.com/v1.0/me',
};