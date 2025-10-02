# ================================
# React Frontend Dockerfile
# ================================

# Use Node.js 18 LTS Alpine image
FROM node:18-alpine

# Set environment variables
ENV NODE_ENV=development \
    CHOKIDAR_USEPOLLING=true

# Set work directory
WORKDIR /app

# Install system dependencies for better performance
RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy application code
COPY . .

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs \
    && adduser -S nextjs -u 1001 \
    && chown -R nextjs:nodejs /app
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Start the development server
CMD ["npm", "start"]