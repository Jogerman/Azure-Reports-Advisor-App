# ================================
# Django Backend Dockerfile
# ================================

# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies (including WeasyPrint and Playwright dependencies)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        git \
        wget \
        # WeasyPrint dependencies for PDF generation
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf-2.0-0 \
        libffi-dev \
        shared-mime-info \
        libcairo2 \
        libglib2.0-0 \
        # Playwright/Chromium dependencies
        libnss3 \
        libnspr4 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libdbus-1-3 \
        libxkbcommon0 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libasound2 \
        libatspi2.0-0 \
        # Fonts for PDF rendering
        fonts-liberation \
        fonts-noto-color-emoji \
        fonts-dejavu-core \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy project files
COPY . .

# Create directories for media and static files
RUN mkdir -p /app/media /app/staticfiles

# Collect static files (will run during container startup)
# RUN python manage.py collectstatic --noinput

# Create non-root user for security
RUN adduser --disabled-password --gecos '' django \
    && chown -R django:django /app

# Switch to django user BEFORE installing Playwright
USER django

# Install Playwright browsers (Chromium for PDF generation) as django user
# Skip deps since we already installed all required dependencies manually above
RUN python -m playwright install chromium

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]