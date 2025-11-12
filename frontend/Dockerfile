# ================================
# React Frontend Dockerfile - Production
# ================================

# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Build the application for production
# The REACT_APP_API_URL will be injected by Container App environment variables
# CI=false prevents treating warnings as errors during build
# TSC_COMPILE_ON_ERROR=true allows TypeScript compilation with type errors
ENV CI=false \
    TSC_COMPILE_ON_ERROR=true \
    DISABLE_ESLINT_PLUGIN=true
RUN npm run build

# Production stage - Use nginx to serve static files
FROM nginx:alpine

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Copy environment injection script
COPY env.sh /docker-entrypoint.d/40-generate-env.sh

# Create nginx user (if not exists)
RUN addgroup -g 101 -S nginx 2>/dev/null || true
RUN adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx 2>/dev/null || true

# Make env script executable
RUN chmod +x /docker-entrypoint.d/40-generate-env.sh

# Set proper permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Expose port (non-privileged port for non-root user)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# The entrypoint scripts run as root, which allows the env.sh script to write to /usr/share/nginx/html
# After entrypoint scripts complete, nginx will run as the nginx user (configured in nginx.conf)
CMD ["nginx", "-g", "daemon off;"]
