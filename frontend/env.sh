#!/bin/sh
# Generate runtime environment configuration for React app

# Create runtime-env.js with runtime environment variables
cat > /usr/share/nginx/html/runtime-env.js << EOF
window._env_ = {
  REACT_APP_API_URL: "${REACT_APP_API_URL}",
  REACT_APP_AZURE_CLIENT_ID: "${REACT_APP_AZURE_CLIENT_ID}",
  REACT_APP_AZURE_TENANT_ID: "${REACT_APP_AZURE_TENANT_ID}",
  REACT_APP_AZURE_REDIRECT_URI: "${REACT_APP_AZURE_REDIRECT_URI}",
  REACT_APP_ENVIRONMENT: "${REACT_APP_ENVIRONMENT}"
};
EOF

echo "✅ Runtime environment configuration generated"
echo "  - API URL: ${REACT_APP_API_URL}"
echo "  - Client ID: ${REACT_APP_AZURE_CLIENT_ID:0:8}..."
echo "  - Tenant ID: ${REACT_APP_AZURE_TENANT_ID:0:8}..."
echo "  - Redirect URI: ${REACT_APP_AZURE_REDIRECT_URI}"
echo "  - Environment: ${REACT_APP_ENVIRONMENT}"
