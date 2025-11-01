#!/bin/sh
# Custom entrypoint script for React frontend
# Injects runtime environment variables before starting nginx

set -e

# Define the directory where the built files are located
BUILD_DIR=/usr/share/nginx/html

echo "🔧 Injecting runtime environment variables..."

# Create runtime-env.js file with actual environment variables
cat <<EOF > ${BUILD_DIR}/runtime-env.js
window._env_ = {
  REACT_APP_API_URL: "${REACT_APP_API_URL:-}",
  REACT_APP_AZURE_CLIENT_ID: "${REACT_APP_AZURE_CLIENT_ID:-}",
  REACT_APP_AZURE_TENANT_ID: "${REACT_APP_AZURE_TENANT_ID:-}",
  REACT_APP_AZURE_REDIRECT_URI: "${REACT_APP_AZURE_REDIRECT_URI:-}",
  REACT_APP_ENVIRONMENT: "${REACT_APP_ENVIRONMENT:-production}"
};
EOF

echo "✅ Runtime environment variables injected successfully"
echo "   - REACT_APP_API_URL: ${REACT_APP_API_URL:-not set}"
echo "   - REACT_APP_AZURE_CLIENT_ID: ${REACT_APP_AZURE_CLIENT_ID:0:10}... (${#REACT_APP_AZURE_CLIENT_ID} chars)"
echo "   - REACT_APP_AZURE_TENANT_ID: ${REACT_APP_AZURE_TENANT_ID:0:10}... (${#REACT_APP_AZURE_TENANT_ID} chars)"
echo "   - REACT_APP_AZURE_REDIRECT_URI: ${REACT_APP_AZURE_REDIRECT_URI:-not set}"
echo "   - REACT_APP_ENVIRONMENT: ${REACT_APP_ENVIRONMENT:-production}"

# Start nginx in the foreground
echo "🚀 Starting nginx..."
exec nginx -g 'daemon off;'
