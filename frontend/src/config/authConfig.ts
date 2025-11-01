import { Configuration, PopupRequest } from '@azure/msal-browser';
import { env, validateEnvironment } from './env';

// Validate environment variables on module load
validateEnvironment();

/**
 * Configuration object to be passed to MSAL instance on creation.
 * For a full list of MSAL.js configuration parameters, visit:
 * https://github.com/AzureAD/microsoft-authentication-library-for-js/blob/dev/lib/msal-browser/docs/configuration.md
 */
export const msalConfig: Configuration = {
  auth: {
    clientId: env.azureClientId,
    authority: `https://login.microsoftonline.com/${env.azureTenantId}`,
    redirectUri: env.azureRedirectUri,
    postLogoutRedirectUri: env.azureRedirectUri,
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