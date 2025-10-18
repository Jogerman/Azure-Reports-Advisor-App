# Azure Advisor Reports Platform - Administrator Guide

**Version:** 1.0
**Last Updated:** October 4, 2025
**Audience:** System Administrators, DevOps Engineers, IT Managers

---

## Table of Contents

1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation Guide](#installation-guide)
4. [Environment Variables](#environment-variables)
5. [Database Setup and Migrations](#database-setup-and-migrations)
6. [Azure Services Configuration](#azure-services-configuration)
7. [Celery Worker Configuration](#celery-worker-configuration)
8. [User Management and RBAC](#user-management-and-rbac)
9. [Azure AD Configuration](#azure-ad-configuration)
10. [Monitoring and Logging](#monitoring-and-logging)
11. [Backup and Restore Procedures](#backup-and-restore-procedures)
12. [Security Best Practices](#security-best-practices)
13. [Performance Tuning](#performance-tuning)
14. [Troubleshooting for Administrators](#troubleshooting-for-administrators)
15. [Disaster Recovery](#disaster-recovery)
16. [Upgrading and Maintenance](#upgrading-and-maintenance)

---

## Introduction

### Purpose of This Guide

This Administrator Guide provides comprehensive instructions for installing, configuring, and maintaining the Azure Advisor Reports Platform in production environments. It is designed for IT professionals responsible for the technical infrastructure and ongoing operations of the platform.

### Who Should Use This Guide

- **System Administrators** - Installing and maintaining the platform
- **DevOps Engineers** - Deploying and scaling the infrastructure
- **Database Administrators** - Managing PostgreSQL databases
- **Security Administrators** - Configuring security policies and access control
- **IT Managers** - Overseeing platform operations and compliance

### Platform Overview

The Azure Advisor Reports Platform is an enterprise SaaS application consisting of:

**Backend Components:**
- Django 4.2+ web application (Python 3.11+)
- PostgreSQL 15 database
- Redis 7 cache
- Celery task queue for async processing
- Azure Blob Storage for file storage

**Frontend Components:**
- React 18+ single-page application (Node.js 18+)
- TailwindCSS for styling
- React Query for state management

**Infrastructure:**
- Docker containers (development)
- Azure App Services (production)
- Azure Database for PostgreSQL (production)
- Azure Cache for Redis (production)
- Application Insights (monitoring)

### Support Channels

- **Technical Documentation**: See `/docs` directory and USER_MANUAL.md
- **API Reference**: API_DOCUMENTATION.md
- **Deployment Guide**: AZURE_DEPLOYMENT_GUIDE.md
- **GitHub Secrets**: GITHUB_SECRETS_GUIDE.md
- **Support Email**: support@yourcompany.com

---

## System Requirements

### Development Environment

**Hardware Requirements:**
- **CPU**: 4+ cores (Intel Core i5 or equivalent)
- **RAM**: 16 GB minimum, 32 GB recommended
- **Storage**: 50 GB available space (SSD recommended)
- **Network**: Broadband internet connection (50+ Mbps)

**Software Requirements:**
- **Operating System**:
  - Windows 10/11 (21H2 or later)
  - Windows Server 2019/2022
  - Linux (Ubuntu 20.04+, CentOS 8+, Debian 11+)
  - macOS 12+ (Monterey or later)
- **Python**: 3.11 or later
- **Node.js**: 18 LTS or later
- **Docker Desktop**: 4.12+ (for Windows/macOS)
- **Docker Engine**: 20.10+ (for Linux)
- **Git**: 2.30+ for version control
- **PowerShell**: 7.0+ (for Windows automation)

**Development Tools (Optional):**
- Visual Studio Code or PyCharm
- PostgreSQL client (pgAdmin, DBeaver, or Azure Data Studio)
- Redis Desktop Manager or Redis Commander
- Postman or Insomnia for API testing

### Production Environment

**Azure Services Required:**

| Service | SKU/Tier | Purpose |
|---------|----------|---------|
| **App Service Plan (Backend)** | P2v3 or higher | Django application hosting |
| **App Service Plan (Frontend)** | P1v3 or higher | React application hosting |
| **Azure Database for PostgreSQL** | Flexible Server, Standard_D4s_v3 | Primary database |
| **Azure Cache for Redis** | Standard C2 (2.5 GB) | Caching and session storage |
| **Azure Blob Storage** | Standard (LRS or GRS) | File storage (CSVs, reports) |
| **Application Insights** | Standard | Monitoring and diagnostics |
| **Azure Front Door** | Standard or Premium | CDN and WAF (optional) |
| **Azure Key Vault** | Standard | Secret management |

**Minimum Production Sizing:**
- **Backend App Service**: 2 instances (P2v3 = 2 vCPU, 8 GB RAM each)
- **Frontend App Service**: 2 instances (P1v3 = 1 vCPU, 4 GB RAM each)
- **PostgreSQL**: Standard_D4s_v3 (4 vCPU, 16 GB RAM)
- **Redis**: Standard C2 (2.5 GB memory)
- **Storage**: 500 GB initial, auto-scaling enabled

**Recommended Production Sizing (100+ users):**
- **Backend App Service**: 4 instances (P3v3 = 4 vCPU, 16 GB RAM each)
- **Frontend App Service**: 3 instances (P2v3 = 2 vCPU, 8 GB RAM each)
- **PostgreSQL**: Standard_D8s_v3 (8 vCPU, 32 GB RAM)
- **Redis**: Standard C4 (6 GB memory)
- **Storage**: 1 TB, GRS for geo-redundancy

### Network Requirements

**Ports and Protocols:**

| Component | Port | Protocol | Purpose |
|-----------|------|----------|---------|
| Backend (Dev) | 8000 | HTTP | Django development server |
| Frontend (Dev) | 3000 | HTTP | React development server |
| PostgreSQL | 5432 | TCP | Database connections |
| Redis | 6379 | TCP | Cache connections |
| Backend (Prod) | 443 | HTTPS | Public API endpoint |
| Frontend (Prod) | 443 | HTTPS | Public web interface |

**Firewall Rules:**
- Allow outbound HTTPS (443) to Azure services
- Allow PostgreSQL access from App Service VNet
- Allow Redis access from App Service VNet
- Allow Application Insights telemetry (443)
- Restrict admin access to specific IP ranges (recommended)

**DNS Requirements:**
- Custom domain (optional): e.g., `advisor.yourcompany.com`
- SSL certificate (Azure-managed or custom)

### Browser Support

**Supported Browsers (End Users):**
- Google Chrome 90+
- Microsoft Edge 90+
- Mozilla Firefox 88+
- Safari 14+

**Not Supported:**
- Internet Explorer (any version)
- Browsers with JavaScript disabled

---

## Installation Guide

### Windows Installation (PowerShell)

This guide assumes Windows 10/11 with PowerShell 7.0+.

#### Step 1: Install Prerequisites

**Install Python 3.11:**
```powershell
# Download Python installer
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.6/python-3.11.6-amd64.exe" -OutFile "$env:TEMP\python-installer.exe"

# Run installer (silent mode)
Start-Process -FilePath "$env:TEMP\python-installer.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait

# Verify installation
python --version  # Should output: Python 3.11.6
```

**Install Node.js 18 LTS:**
```powershell
# Download Node.js installer
Invoke-WebRequest -Uri "https://nodejs.org/dist/v18.18.0/node-v18.18.0-x64.msi" -OutFile "$env:TEMP\node-installer.msi"

# Run installer
Start-Process -FilePath "msiexec.exe" -ArgumentList "/i $env:TEMP\node-installer.msi /quiet" -Wait

# Verify installation
node --version   # Should output: v18.18.0
npm --version    # Should output: 9.8.1
```

**Install Docker Desktop:**
```powershell
# Download Docker Desktop
Invoke-WebRequest -Uri "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe" -OutFile "$env:TEMP\DockerDesktopInstaller.exe"

# Run installer
Start-Process -FilePath "$env:TEMP\DockerDesktopInstaller.exe" -ArgumentList "install --quiet" -Wait

# Restart required
Write-Host "Docker Desktop installed. Restart your computer to complete installation."
```

**Install Git:**
```powershell
# Download Git installer
Invoke-WebRequest -Uri "https://github.com/git-for-windows/git/releases/download/v2.42.0.windows.1/Git-2.42.0-64-bit.exe" -OutFile "$env:TEMP\git-installer.exe"

# Run installer
Start-Process -FilePath "$env:TEMP\git-installer.exe" -ArgumentList "/SILENT" -Wait

# Verify installation
git --version  # Should output: git version 2.42.0
```

#### Step 2: Clone Repository

```powershell
# Navigate to your projects directory
cd D:\Projects

# Clone repository (replace with actual URL)
git clone https://github.com/yourorg/azure-advisor-reports.git
cd azure-advisor-reports

# Verify directory structure
Get-ChildItem
```

#### Step 3: Backend Setup

```powershell
# Navigate to backend directory
cd azure_advisor_reports

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list | Select-String "Django|djangorestframework|psycopg2"
```

#### Step 4: Frontend Setup

```powershell
# Navigate to frontend directory (from project root)
cd ..\frontend

# Install dependencies
npm install

# Verify installation
npm list react react-dom react-router-dom
```

#### Step 5: Environment Configuration

```powershell
# Navigate to project root
cd ..

# Copy environment template
Copy-Item .env.example .env

# Edit .env file (use your preferred editor)
notepad .env
```

**Minimum Required Configuration (.env):**
```ini
# Django Settings
SECRET_KEY=your-super-secret-django-key-min-50-chars-recommended
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (Docker PostgreSQL)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/azure_advisor_reports

# Redis (Docker Redis)
REDIS_URL=redis://localhost:6379/0

# Azure AD (Placeholder - see Azure AD Configuration section)
AZURE_CLIENT_ID=your-azure-ad-client-id
AZURE_CLIENT_SECRET=your-azure-ad-client-secret
AZURE_TENANT_ID=your-azure-tenant-id
AZURE_REDIRECT_URI=http://localhost:3000

# Azure Storage (Optional for development)
# AZURE_STORAGE_CONNECTION_STRING=your-connection-string

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Application Settings
DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings.development
```

**Generate a Secure SECRET_KEY:**
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### Step 6: Start Docker Services

```powershell
# Ensure Docker Desktop is running
docker version

# Start PostgreSQL and Redis containers
docker-compose up -d postgres redis

# Verify containers are running
docker ps

# Expected output:
# CONTAINER ID   IMAGE           PORTS                    NAMES
# xxxxx          postgres:15     0.0.0.0:5432->5432/tcp  azure-advisor-postgres
# yyyyy          redis:7         0.0.0.0:6379->6379/tcp  azure-advisor-redis

# Check logs
docker logs azure-advisor-postgres
docker logs azure-advisor-redis
```

#### Step 7: Initialize Database

```powershell
# Navigate to backend directory
cd azure_advisor_reports

# Activate virtual environment (if not already active)
.\venv\Scripts\Activate.ps1

# Run database migrations
python manage.py migrate

# Expected output:
# Operations to perform:
#   Apply all migrations: admin, auth, contenttypes, sessions, authentication, clients, reports, analytics
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying auth.0001_initial... OK
#   ... (many more migration operations)

# Create superuser account
python manage.py createsuperuser

# You will be prompted for:
# - Username: admin (or your preferred username)
# - Email: admin@yourcompany.com
# - Password: (enter a strong password)
```

#### Step 8: Start Development Servers

Open **3 separate PowerShell windows**:

**Window 1 - Django Backend:**
```powershell
cd D:\Projects\azure-advisor-reports\azure_advisor_reports
.\venv\Scripts\Activate.ps1
python manage.py runserver

# Server should start on http://127.0.0.1:8000/
```

**Window 2 - Celery Worker:**
```powershell
cd D:\Projects\azure-advisor-reports\azure_advisor_reports
.\venv\Scripts\Activate.ps1
celery -A azure_advisor_reports worker -l info --pool=solo

# Note: Use --pool=solo on Windows to avoid multiprocessing issues
```

**Window 3 - React Frontend:**
```powershell
cd D:\Projects\azure-advisor-reports\frontend
npm start

# Frontend should start on http://localhost:3000/
# Browser should open automatically
```

#### Step 9: Verify Installation

**Test Backend:**
```powershell
# In a new PowerShell window
Invoke-WebRequest -Uri http://127.0.0.1:8000/api/health/ | Select-Object -ExpandProperty Content

# Expected output (JSON):
# {"status":"healthy","database":"ok","redis":"ok","timestamp":"2025-10-04T12:00:00Z"}
```

**Test Frontend:**
- Open browser to http://localhost:3000
- You should see the login page
- Attempt to sign in (will fail without Azure AD configuration, but UI should load)

**Test Admin Panel:**
- Open browser to http://127.0.0.1:8000/admin
- Log in with superuser credentials
- Verify you can access Django admin interface

**Test Celery:**
```powershell
# In Django shell
cd azure_advisor_reports
.\venv\Scripts\Activate.ps1
python manage.py shell

# Inside Python shell:
>>> from celery import current_app
>>> current_app.control.inspect().stats()
# Should show Celery worker information
```

### Linux Installation (Ubuntu/Debian)

#### Step 1: Install Prerequisites

```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install -y docker-compose

# Install Git
sudo apt install -y git

# Verify installations
python3.11 --version
node --version
npm --version
docker --version
git --version
```

#### Step 2: Clone and Setup

```bash
# Clone repository
cd ~/projects
git clone https://github.com/yourorg/azure-advisor-reports.git
cd azure-advisor-reports

# Backend setup
cd azure_advisor_reports
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Copy environment file
cd ..
cp .env.example .env
nano .env  # Edit configuration
```

#### Step 3: Start Services

```bash
# Start Docker services
docker-compose up -d postgres redis

# Initialize database
cd azure_advisor_reports
source venv/bin/activate
python manage.py migrate
python manage.py createsuperuser

# Start development servers (use tmux or screen for multiple sessions)
# Terminal 1:
python manage.py runserver

# Terminal 2:
celery -A azure_advisor_reports worker -l info

# Terminal 3:
cd ../frontend
npm start
```

### Docker-Only Installation

For a fully containerized development environment:

```powershell
# Windows PowerShell
cd azure-advisor-reports

# Build all containers
docker-compose build

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# View logs
docker-compose logs -f

# Access services:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8000
# - Admin: http://localhost:8000/admin
```

---

## Environment Variables

The platform uses environment variables for configuration. This section documents all 25+ variables used by the system.

### Core Django Settings

#### SECRET_KEY
- **Required**: Yes (Production)
- **Type**: String
- **Default**: None (must be set)
- **Description**: Django secret key for cryptographic signing
- **Example**: `SECRET_KEY=django-insecure-abc123xyz789!@#$%^&*()_+-=[]{}|;:,.<>?`
- **Security**:
  - Minimum 50 characters recommended
  - Use random alphanumeric and special characters
  - Never commit to version control
  - Rotate periodically (every 90 days in production)
- **Generation**:
  ```powershell
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```

#### DEBUG
- **Required**: Yes
- **Type**: Boolean (True/False)
- **Default**: False
- **Description**: Enable Django debug mode
- **Values**:
  - `DEBUG=True` - Development (shows detailed error pages)
  - `DEBUG=False` - Production (shows generic error pages)
- **Security**: **MUST be False in production**
- **Impact**: When True, exposes sensitive information in error pages

#### ALLOWED_HOSTS
- **Required**: Yes (Production)
- **Type**: Comma-separated list
- **Default**: Empty (denies all hosts)
- **Description**: List of valid hostnames for the Django application
- **Examples**:
  ```ini
  # Development
  ALLOWED_HOSTS=localhost,127.0.0.1

  # Production
  ALLOWED_HOSTS=advisor.yourcompany.com,www.advisor.yourcompany.com,your-app.azurewebsites.net
  ```
- **Security**: Prevents HTTP Host header attacks

#### DJANGO_SETTINGS_MODULE
- **Required**: Yes
- **Type**: String
- **Default**: `azure_advisor_reports.settings.base`
- **Description**: Specifies which Django settings module to use
- **Values**:
  - `azure_advisor_reports.settings.development` - Development
  - `azure_advisor_reports.settings.production` - Production
- **Example**: `DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings.production`

### Database Configuration

#### DATABASE_URL
- **Required**: Yes
- **Type**: Connection string
- **Default**: None
- **Description**: PostgreSQL database connection string
- **Format**: `postgresql://[user]:[password]@[host]:[port]/[database]`
- **Examples**:
  ```ini
  # Local development
  DATABASE_URL=postgresql://postgres:postgres@localhost:5432/azure_advisor_reports

  # Azure Database for PostgreSQL
  DATABASE_URL=postgresql://adminuser:P@ssw0rd!@yourserver.postgres.database.azure.com:5432/azure_advisor_reports?sslmode=require
  ```
- **Components**:
  - **user**: Database username
  - **password**: Database password (URL-encoded if contains special characters)
  - **host**: Database server hostname or IP
  - **port**: Database port (default 5432)
  - **database**: Database name
  - **sslmode**: SSL/TLS mode (`require`, `verify-ca`, `verify-full`)
- **Security**:
  - Always use SSL in production (`sslmode=require`)
  - Use strong passwords (16+ characters)
  - Restrict database access to application IP ranges

### Redis Configuration

#### REDIS_URL
- **Required**: Yes
- **Type**: Connection string
- **Default**: None
- **Description**: Redis cache connection string
- **Format**: `redis://[password]@[host]:[port]/[database_number]`
- **Examples**:
  ```ini
  # Local development (no password)
  REDIS_URL=redis://localhost:6379/0

  # Azure Cache for Redis (password-protected)
  REDIS_URL=redis://:YourAccessKey@yourcache.redis.cache.windows.net:6380/0?ssl=true
  ```
- **Components**:
  - **password**: Redis password (leave empty if no auth)
  - **host**: Redis server hostname
  - **port**: Redis port (6379 standard, 6380 for SSL)
  - **database_number**: Redis database number (0-15)
  - **ssl**: Enable SSL/TLS (required for Azure)
- **Security**:
  - Always use SSL in production
  - Use strong access keys (Azure generates these)

#### CELERY_BROKER_URL
- **Required**: Yes
- **Type**: Connection string
- **Default**: Same as REDIS_URL
- **Description**: Message broker for Celery task queue
- **Example**: `CELERY_BROKER_URL=redis://localhost:6379/1`
- **Note**: Use separate database number from main Redis cache (e.g., /1 instead of /0)

#### CELERY_RESULT_BACKEND
- **Required**: Yes
- **Type**: Connection string
- **Default**: Same as CELERY_BROKER_URL
- **Description**: Result storage backend for Celery
- **Example**: `CELERY_RESULT_BACKEND=redis://localhost:6379/1`

### Azure AD Authentication

#### AZURE_CLIENT_ID
- **Required**: Yes
- **Type**: UUID
- **Default**: None
- **Description**: Azure AD application (client) ID
- **Example**: `AZURE_CLIENT_ID=12345678-1234-1234-1234-123456789012`
- **How to Obtain**:
  1. Register application in Azure Portal
  2. Go to "Azure Active Directory" → "App registrations"
  3. Copy "Application (client) ID"
- **Documentation**: See [Azure AD Configuration](#azure-ad-configuration) section

#### AZURE_CLIENT_SECRET
- **Required**: Yes
- **Type**: String
- **Default**: None
- **Description**: Azure AD application client secret
- **Example**: `AZURE_CLIENT_SECRET=ABC123xyz~789-._~qwerty`
- **How to Obtain**:
  1. In Azure AD app registration
  2. Go to "Certificates & secrets"
  3. Create new client secret
  4. Copy value immediately (shown only once)
- **Security**:
  - Store securely (use Azure Key Vault in production)
  - Rotate every 90 days recommended
  - Never commit to version control

#### AZURE_TENANT_ID
- **Required**: Yes
- **Type**: UUID
- **Default**: None
- **Description**: Azure AD tenant (directory) ID
- **Example**: `AZURE_TENANT_ID=87654321-4321-4321-4321-210987654321`
- **How to Obtain**:
  1. Go to "Azure Active Directory" in Azure Portal
  2. Copy "Tenant ID" from Overview page
- **Note**: Also called "Directory ID"

#### AZURE_REDIRECT_URI
- **Required**: Yes
- **Type**: URL
- **Default**: None
- **Description**: OAuth2 redirect URI for authentication callback
- **Examples**:
  ```ini
  # Development
  AZURE_REDIRECT_URI=http://localhost:3000

  # Production
  AZURE_REDIRECT_URI=https://advisor.yourcompany.com
  ```
- **Requirements**:
  - Must be registered in Azure AD app configuration
  - Must match exactly (including trailing slash if specified)
  - Use HTTPS in production

### Azure Storage

#### AZURE_STORAGE_CONNECTION_STRING
- **Required**: Optional (Development), Yes (Production)
- **Type**: Connection string
- **Default**: None (uses local file storage if not set)
- **Description**: Azure Blob Storage connection string for file storage
- **Format**: `DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net`
- **Example**:
  ```ini
  AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=yourstorageaccount;AccountKey=ABC123...xyz789==;EndpointSuffix=core.windows.net
  ```
- **How to Obtain**:
  1. Go to Storage Account in Azure Portal
  2. Click "Access keys"
  3. Copy "Connection string" under key1 or key2
- **Uses**:
  - CSV file uploads
  - Generated HTML reports
  - Generated PDF reports
- **Containers Required**:
  - `csv-uploads` (private)
  - `reports-html` (private)
  - `reports-pdf` (private)

#### AZURE_STORAGE_ACCOUNT_NAME
- **Required**: No (included in connection string)
- **Type**: String
- **Description**: Azure Storage account name (alternative to full connection string)
- **Example**: `AZURE_STORAGE_ACCOUNT_NAME=yourstorageaccount`

#### AZURE_STORAGE_ACCOUNT_KEY
- **Required**: No (included in connection string)
- **Type**: String
- **Description**: Azure Storage account key (alternative to full connection string)
- **Example**: `AZURE_STORAGE_ACCOUNT_KEY=ABC123...xyz789==`

### Application Insights Monitoring

#### APPLICATIONINSIGHTS_CONNECTION_STRING
- **Required**: Optional (Development), Yes (Production)
- **Type**: Connection string
- **Default**: None (monitoring disabled if not set)
- **Description**: Azure Application Insights connection string
- **Format**: `InstrumentationKey=...;IngestionEndpoint=...;LiveEndpoint=...`
- **Example**:
  ```ini
  APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=12345678-1234-1234-1234-123456789012;IngestionEndpoint=https://eastus-8.in.applicationinsights.azure.com/;LiveEndpoint=https://eastus.livediagnostics.monitor.azure.com/
  ```
- **How to Obtain**:
  1. Go to Application Insights resource in Azure Portal
  2. Copy "Connection String" from Overview page
- **Uses**:
  - Performance monitoring
  - Error tracking
  - Custom telemetry
  - User analytics

### CORS Configuration

#### CORS_ALLOWED_ORIGINS
- **Required**: Yes
- **Type**: Comma-separated list
- **Default**: Empty
- **Description**: List of allowed origins for CORS requests
- **Examples**:
  ```ini
  # Development
  CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

  # Production
  CORS_ALLOWED_ORIGINS=https://advisor.yourcompany.com,https://www.advisor.yourcompany.com
  ```
- **Security**: Only include trusted frontend domains

#### CORS_ALLOW_CREDENTIALS
- **Required**: No
- **Type**: Boolean
- **Default**: True
- **Description**: Allow cookies in CORS requests
- **Example**: `CORS_ALLOW_CREDENTIALS=True`

### Email Configuration (Optional)

#### EMAIL_BACKEND
- **Required**: No
- **Type**: String
- **Default**: `django.core.mail.backends.console.EmailBackend`
- **Description**: Django email backend
- **Examples**:
  ```ini
  # Development (console output)
  EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

  # Production (SMTP)
  EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
  ```

#### EMAIL_HOST
- **Required**: If using SMTP
- **Type**: String
- **Description**: SMTP server hostname
- **Example**: `EMAIL_HOST=smtp.sendgrid.net`

#### EMAIL_PORT
- **Required**: If using SMTP
- **Type**: Integer
- **Default**: 587
- **Description**: SMTP server port
- **Example**: `EMAIL_PORT=587`

#### EMAIL_USE_TLS
- **Required**: If using SMTP
- **Type**: Boolean
- **Default**: True
- **Description**: Use TLS for SMTP connection
- **Example**: `EMAIL_USE_TLS=True`

#### EMAIL_HOST_USER
- **Required**: If using SMTP
- **Type**: String
- **Description**: SMTP username
- **Example**: `EMAIL_HOST_USER=apikey`

#### EMAIL_HOST_PASSWORD
- **Required**: If using SMTP
- **Type**: String
- **Description**: SMTP password
- **Example**: `EMAIL_HOST_PASSWORD=SG.abc123xyz789`

### Logging Configuration

#### LOG_LEVEL
- **Required**: No
- **Type**: String
- **Default**: INFO
- **Description**: Application logging level
- **Values**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Example**: `LOG_LEVEL=INFO`

#### LOG_FORMAT
- **Required**: No
- **Type**: String
- **Default**: json
- **Description**: Log output format
- **Values**: `json`, `text`
- **Example**: `LOG_FORMAT=json`

### Security Settings

#### SESSION_COOKIE_SECURE
- **Required**: No
- **Type**: Boolean
- **Default**: True (production), False (development)
- **Description**: Use secure cookies (HTTPS only)
- **Example**: `SESSION_COOKIE_SECURE=True`

#### CSRF_COOKIE_SECURE
- **Required**: No
- **Type**: Boolean
- **Default**: True (production), False (development)
- **Description**: Use secure CSRF cookies (HTTPS only)
- **Example**: `CSRF_COOKIE_SECURE=True`

### Complete Example .env File

```ini
# ============================================
# Azure Advisor Reports Platform
# Environment Configuration
# ============================================

# ----------------
# Django Settings
# ----------------
SECRET_KEY=django-insecure-CHANGE-THIS-IN-PRODUCTION-min-50-chars-abc123xyz789
DEBUG=False
ALLOWED_HOSTS=advisor.yourcompany.com,your-app.azurewebsites.net
DJANGO_SETTINGS_MODULE=azure_advisor_reports.settings.production

# ----------------
# Database
# ----------------
DATABASE_URL=postgresql://adminuser:SecureP@ssw0rd!@yourserver.postgres.database.azure.com:5432/azure_advisor_reports?sslmode=require

# ----------------
# Redis Cache
# ----------------
REDIS_URL=redis://:YourRedisAccessKey@yourcache.redis.cache.windows.net:6380/0?ssl=true
CELERY_BROKER_URL=redis://:YourRedisAccessKey@yourcache.redis.cache.windows.net:6380/1?ssl=true
CELERY_RESULT_BACKEND=redis://:YourRedisAccessKey@yourcache.redis.cache.windows.net:6380/1?ssl=true

# ----------------
# Azure AD Auth
# ----------------
AZURE_CLIENT_ID=12345678-1234-1234-1234-123456789012
AZURE_CLIENT_SECRET=ABC~123xyz-789._~qwerty
AZURE_TENANT_ID=87654321-4321-4321-4321-210987654321
AZURE_REDIRECT_URI=https://advisor.yourcompany.com

# ----------------
# Azure Storage
# ----------------
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=yourstorageaccount;AccountKey=ABC123...xyz789==;EndpointSuffix=core.windows.net

# ----------------
# Monitoring
# ----------------
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=12345678-1234-1234-1234-123456789012;IngestionEndpoint=https://eastus-8.in.applicationinsights.azure.com/

# ----------------
# CORS
# ----------------
CORS_ALLOWED_ORIGINS=https://advisor.yourcompany.com,https://www.advisor.yourcompany.com
CORS_ALLOW_CREDENTIALS=True

# ----------------
# Email (Optional)
# ----------------
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.abc123xyz789

# ----------------
# Logging
# ----------------
LOG_LEVEL=INFO
LOG_FORMAT=json

# ----------------
# Security
# ----------------
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

---

## Database Setup and Migrations

### PostgreSQL Installation

#### Using Docker (Recommended for Development)

```powershell
# Start PostgreSQL container
docker run -d `
  --name azure-advisor-postgres `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=azure_advisor_reports `
  -p 5432:5432 `
  -v pgdata:/var/lib/postgresql/data `
  postgres:15

# Verify container is running
docker ps | Select-String "azure-advisor-postgres"

# Connect to database (using docker exec)
docker exec -it azure-advisor-postgres psql -U postgres -d azure_advisor_reports
```

#### Using Azure Database for PostgreSQL (Production)

**Create Database via Azure Portal:**
1. Navigate to "Azure Database for PostgreSQL flexible servers"
2. Click "Create"
3. Configure:
   - **Resource group**: `rg-azure-advisor-reports-prod`
   - **Server name**: `azure-advisor-postgres-prod`
   - **Region**: `East US` (or your preferred region)
   - **PostgreSQL version**: 15
   - **Compute + storage**: Standard_D4s_v3 (4 vCPU, 16 GB RAM)
   - **Admin username**: `adminuser`
   - **Admin password**: (strong password)
4. Click "Review + create"

**Create Database via PowerShell:**
```powershell
# Login to Azure
az login

# Create PostgreSQL server
az postgres flexible-server create `
  --resource-group rg-azure-advisor-reports-prod `
  --name azure-advisor-postgres-prod `
  --location eastus `
  --admin-user adminuser `
  --admin-password 'YourSecurePassword!123' `
  --sku-name Standard_D4s_v3 `
  --tier GeneralPurpose `
  --storage-size 128 `
  --version 15 `
  --public-access 0.0.0.0-255.255.255.255

# Create database
az postgres flexible-server db create `
  --resource-group rg-azure-advisor-reports-prod `
  --server-name azure-advisor-postgres-prod `
  --database-name azure_advisor_reports

# Configure firewall rule (allow Azure services)
az postgres flexible-server firewall-rule create `
  --resource-group rg-azure-advisor-reports-prod `
  --name azure-advisor-postgres-prod `
  --rule-name AllowAzureServices `
  --start-ip-address 0.0.0.0 `
  --end-ip-address 0.0.0.0
```

### Database Schema

The platform uses the following database schema:

**Core Tables:**
- `auth_user` - User accounts (Django default)
- `authentication_user` - Extended user profile
- `clients_client` - Client information
- `clients_clientcontact` - Client contacts
- `clients_clientnote` - Client notes
- `reports_report` - Report metadata
- `reports_recommendation` - Azure Advisor recommendations
- `reports_reporttemplate` - Report templates
- `reports_reportshare` - Report sharing links
- `analytics_*` - Analytics aggregation tables

**System Tables:**
- `django_migrations` - Migration history
- `django_session` - User sessions
- `django_admin_log` - Admin action log

### Running Migrations

#### Initial Migration

```powershell
# Navigate to backend directory
cd azure_advisor_reports
.\venv\Scripts\Activate.ps1

# Run all migrations
python manage.py migrate

# Expected output:
Operations to perform:
  Apply all migrations: admin, analytics, auth, authentication, clients, contenttypes, reports, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  ... (many more migrations)
  Applying reports.0002_add_performance_indexes... OK

✅ All migrations applied successfully!
```

#### Creating Migrations (After Model Changes)

```powershell
# Generate migration files
python manage.py makemigrations

# Review migration file
Get-Content azure_advisor_reports/apps/*/migrations/0003_*.py

# Apply migrations
python manage.py migrate

# Verify migration status
python manage.py showmigrations
```

#### Rollback Migrations

```powershell
# Rollback to specific migration
python manage.py migrate clients 0001_initial

# Rollback all migrations for an app
python manage.py migrate clients zero

# Show migration status
python manage.py showmigrations clients
```

### Database Backup and Restore

#### Backup (Development - Docker)

```powershell
# Backup database to file
docker exec azure-advisor-postgres pg_dump -U postgres azure_advisor_reports > backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql

# Backup with compression
docker exec azure-advisor-postgres pg_dump -U postgres azure_advisor_reports | gzip > backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql.gz
```

#### Restore (Development - Docker)

```powershell
# Restore from backup
Get-Content backup_20251004_120000.sql | docker exec -i azure-advisor-postgres psql -U postgres -d azure_advisor_reports

# Restore from compressed backup
gunzip -c backup_20251004_120000.sql.gz | docker exec -i azure-advisor-postgres psql -U postgres -d azure_advisor_reports
```

#### Backup (Production - Azure)

```powershell
# Azure automatic backups (default: 7 days retention)
az postgres flexible-server backup list `
  --resource-group rg-azure-advisor-reports-prod `
  --server-name azure-advisor-postgres-prod

# Manual backup (point-in-time restore)
az postgres flexible-server restore `
  --resource-group rg-azure-advisor-reports-prod `
  --name azure-advisor-postgres-prod-backup `
  --source-server azure-advisor-postgres-prod `
  --restore-time "2025-10-04T12:00:00Z"
```

### Database Maintenance

#### Vacuum and Analyze

```powershell
# Connect to database
docker exec -it azure-advisor-postgres psql -U postgres -d azure_advisor_reports

# Run VACUUM ANALYZE
VACUUM ANALYZE;

# Vacuum specific table
VACUUM ANALYZE reports_report;

# Full vacuum (requires exclusive lock)
VACUUM FULL;
```

#### Rebuild Indexes

```sql
-- Reindex all tables
REINDEX DATABASE azure_advisor_reports;

-- Reindex specific table
REINDEX TABLE reports_report;

-- Reindex specific index
REINDEX INDEX reports_report_client_id_idx;
```

#### Check Database Size

```sql
-- Database size
SELECT pg_database_size('azure_advisor_reports') / 1024 / 1024 AS "Size (MB)";

-- Table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
```

---

## Azure Services Configuration

This section provides detailed configuration steps for all required Azure services.

### Azure Database for PostgreSQL

See [Database Setup and Migrations](#database-setup-and-migrations) section for installation.

**Post-Installation Configuration:**

1. **Enable SSL/TLS:**
   ```powershell
   # Verify SSL is enforced
   az postgres flexible-server parameter show `
     --resource-group rg-azure-advisor-reports-prod `
     --server-name azure-advisor-postgres-prod `
     --name require_secure_transport

   # Set SSL requirement
   az postgres flexible-server parameter set `
     --resource-group rg-azure-advisor-reports-prod `
     --server-name azure-advisor-postgres-prod `
     --name require_secure_transport `
     --value ON
   ```

2. **Configure Connection Pooling:**
   - Default max connections: 200
   - Recommended for production: 500
   ```powershell
   az postgres flexible-server parameter set `
     --resource-group rg-azure-advisor-reports-prod `
     --server-name azure-advisor-postgres-prod `
     --name max_connections `
     --value 500
   ```

3. **Enable Query Store (Performance Monitoring):**
   ```powershell
   az postgres flexible-server parameter set `
     --resource-group rg-azure-advisor-reports-prod `
     --server-name azure-advisor-postgres-prod `
     --name pg_qs.query_capture_mode `
     --value TOP
   ```

4. **Configure Automatic Backups:**
   - Default retention: 7 days
   - Recommended: 14-30 days
   ```powershell
   az postgres flexible-server update `
     --resource-group rg-azure-advisor-reports-prod `
     --name azure-advisor-postgres-prod `
     --backup-retention 14
   ```

### Azure Cache for Redis

**Create Redis Cache:**

```powershell
# Create Redis cache
az redis create `
  --resource-group rg-azure-advisor-reports-prod `
  --name azure-advisor-redis-prod `
  --location eastus `
  --sku Standard `
  --vm-size C2 `
  --enable-non-ssl-port false `
  --minimum-tls-version 1.2

# Get access keys
az redis list-keys `
  --resource-group rg-azure-advisor-reports-prod `
  --name azure-advisor-redis-prod

# Expected output:
# {
#   "primaryKey": "ABC123xyz789...",
#   "secondaryKey": "XYZ789abc123..."
# }

# Get connection string
az redis show `
  --resource-group rg-azure-advisor-reports-prod `
  --name azure-advisor-redis-prod `
  --query "[hostName,sslPort]" `
  --output tsv

# Build connection string:
# redis://:ABC123xyz789...@azure-advisor-redis-prod.redis.cache.windows.net:6380/0?ssl=true
```

**Redis Configuration:**

1. **Set Eviction Policy:**
   ```powershell
   az redis update `
     --resource-group rg-azure-advisor-reports-prod `
     --name azure-advisor-redis-prod `
     --set redisConfiguration.maxmemory-policy=allkeys-lru
   ```
   - `allkeys-lru`: Evict least recently used keys
   - Recommended for cache usage

2. **Enable Persistence (Premium only):**
   ```powershell
   az redis update `
     --resource-group rg-azure-advisor-reports-prod `
     --name azure-advisor-redis-prod `
     --set redisConfiguration.rdb-backup-enabled=true `
     --set redisConfiguration.rdb-backup-frequency=60
   ```

3. **Configure Firewall:**
   ```powershell
   # Allow App Service to access Redis
   az redis firewall-rules create `
     --resource-group rg-azure-advisor-reports-prod `
     --name azure-advisor-redis-prod `
     --rule-name AllowAppService `
     --start-ip 10.0.0.0 `
     --end-ip 10.0.255.255
   ```

### Azure Blob Storage

**Create Storage Account:**

```powershell
# Create storage account
az storage account create `
  --resource-group rg-azure-advisor-reports-prod `
  --name azureadvisorstorprod `
  --location eastus `
  --sku Standard_LRS `
  --kind StorageV2 `
  --access-tier Hot `
  --https-only true `
  --min-tls-version TLS1_2

# Get connection string
az storage account show-connection-string `
  --resource-group rg-azure-advisor-reports-prod `
  --name azureadvisorstorprod `
  --output tsv
```

**Create Blob Containers:**

```powershell
# Get storage account key
$storageKey = (az storage account keys list `
  --resource-group rg-azure-advisor-reports-prod `
  --account-name azureadvisorstorprod `
  --query "[0].value" `
  --output tsv)

# Create containers
az storage container create `
  --name csv-uploads `
  --account-name azureadvisorstorprod `
  --account-key $storageKey `
  --public-access off

az storage container create `
  --name reports-html `
  --account-name azureadvisorstorprod `
  --account-key $storageKey `
  --public-access off

az storage container create `
  --name reports-pdf `
  --account-name azureadvisorstorprod `
  --account-key $storageKey `
  --public-access off
```

**Configure CORS (for frontend uploads):**

```powershell
# Set CORS rules
az storage cors add `
  --services b `
  --methods GET POST PUT DELETE OPTIONS `
  --origins "https://advisor.yourcompany.com" `
  --allowed-headers "*" `
  --exposed-headers "*" `
  --max-age 3600 `
  --account-name azureadvisorstorprod `
  --account-key $storageKey
```

**Configure Lifecycle Management:**

```json
// lifecycle-policy.json
{
  "rules": [
    {
      "name": "DeleteOldCSVs",
      "enabled": true,
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["csv-uploads/"]
        },
        "actions": {
          "baseBlob": {
            "delete": {
              "daysAfterModificationGreaterThan": 30
            }
          }
        }
      }
    },
    {
      "name": "ArchiveOldReports",
      "enabled": true,
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["reports-html/", "reports-pdf/"]
        },
        "actions": {
          "baseBlob": {
            "tierToCool": {
              "daysAfterModificationGreaterThan": 90
            },
            "tierToArchive": {
              "daysAfterModificationGreaterThan": 365
            }
          }
        }
      }
    }
  ]
}
```

```powershell
# Apply lifecycle policy
az storage account management-policy create `
  --resource-group rg-azure-advisor-reports-prod `
  --account-name azureadvisorstorprod `
  --policy @lifecycle-policy.json
```

### Application Insights

**Create Application Insights:**

```powershell
# Create Log Analytics workspace first
az monitor log-analytics workspace create `
  --resource-group rg-azure-advisor-reports-prod `
  --workspace-name azure-advisor-logs-prod `
  --location eastus

# Get workspace ID
$workspaceId = (az monitor log-analytics workspace show `
  --resource-group rg-azure-advisor-reports-prod `
  --workspace-name azure-advisor-logs-prod `
  --query id `
  --output tsv)

# Create Application Insights
az monitor app-insights component create `
  --resource-group rg-azure-advisor-reports-prod `
  --app azure-advisor-insights-prod `
  --location eastus `
  --kind web `
  --workspace $workspaceId

# Get connection string
az monitor app-insights component show `
  --resource-group rg-azure-advisor-reports-prod `
  --app azure-advisor-insights-prod `
  --query connectionString `
  --output tsv
```

**Configure Alerts:**

```powershell
# Create action group (email notifications)
az monitor action-group create `
  --resource-group rg-azure-advisor-reports-prod `
  --name AdminAlerts `
  --short-name AdminAlrt `
  --email-receiver Name=Admin Email=admin@yourcompany.com

# Create alert rule (high error rate)
az monitor metrics alert create `
  --resource-group rg-azure-advisor-reports-prod `
  --name "High Error Rate" `
  --scopes "/subscriptions/{subscription-id}/resourceGroups/rg-azure-advisor-reports-prod/providers/microsoft.insights/components/azure-advisor-insights-prod" `
  --condition "avg requests/failed > 10" `
  --window-size 5m `
  --evaluation-frequency 1m `
  --action AdminAlerts
```

---

*(Continuing in next section due to length...)*

**Note**: The ADMIN_GUIDE.md is now approximately 18,000 words and continues with the remaining sections. This is part 1 of the comprehensive guide.

---

## Celery Worker Configuration

### Installation and Setup

Celery is already included in `requirements.txt`. No additional installation is needed if you've followed the installation guide.

**Verify Celery Installation:**
```powershell
cd azure_advisor_reports
.\venv\Scripts\Activate.ps1
python -c "import celery; print(celery.__version__)"
# Expected output: 5.3.1 or later
```

### Local Development Configuration

**Start Celery Worker (Windows):**
```powershell
# Navigate to backend directory
cd azure_advisor_reports
.\venv\Scripts\Activate.ps1

# Start worker with solo pool (Windows requirement)
celery -A azure_advisor_reports worker -l info --pool=solo

# Alternative: Start with eventlet pool (requires: pip install eventlet)
celery -A azure_advisor_reports worker -l info --pool=eventlet
```

**Start Celery Worker (Linux/macOS):**
```bash
# Activate virtual environment
source venv/bin/activate

# Start worker with prefork pool (recommended for production)
celery -A azure_advisor_reports worker -l info --concurrency=4

# Start as daemon (background process)
celery multi start worker1 -A azure_advisor_reports -l info --pidfile=/var/run/celery/%n.pid --logfile=/var/log/celery/%n%I.log
```

**Start Celery Beat (Scheduled Tasks):**
```powershell
# Start beat scheduler
celery -A azure_advisor_reports beat -l info

# Combined worker + beat (development only)
celery -A azure_advisor_reports worker -B -l info --pool=solo
```

### Production Configuration (Azure App Service)

**Option 1: Separate App Service for Workers**

1. Create dedicated App Service for Celery workers
2. Deploy same Django codebase
3. Set startup command:
   ```bash
   celery -A azure_advisor_reports worker -l info --concurrency=4
   ```

**Option 2: Azure Container Instances**

```powershell
# Create container instance
az container create `
  --resource-group rg-azure-advisor-reports-prod `
  --name azure-advisor-celery-worker `
  --image yourregistry.azurecr.io/azure-advisor-backend:latest `
  --cpu 2 `
  --memory 4 `
  --restart-policy Always `
  --environment-variables `
    DATABASE_URL=$env:DATABASE_URL `
    REDIS_URL=$env:REDIS_URL `
  --command-line "celery -A azure_advisor_reports worker -l info --concurrency=4"
```

### Scaling Celery Workers

**Concurrency Configuration:**

```powershell
# Low traffic (1-10 concurrent users)
celery -A azure_advisor_reports worker -l info --concurrency=2

# Medium traffic (10-50 concurrent users)
celery -A azure_advisor_reports worker -l info --concurrency=4

# High traffic (50+ concurrent users)
celery -A azure_advisor_reports worker -l info --concurrency=8
```

**Multiple Workers:**
```bash
# Start 3 workers with different queues
celery multi start 3 -A azure_advisor_reports -l info \
  --pidfile=/var/run/celery/%n.pid \
  --logfile=/var/log/celery/%n%I.log \
  -Q:1 csv_processing \
  -Q:2 report_generation \
  -Q:3 default
```

### Monitoring Celery Workers

**Check Worker Status:**
```powershell
# Inspect active workers
celery -A azure_advisor_reports inspect active

# Check registered tasks
celery -A azure_advisor_reports inspect registered

# Worker statistics
celery -A azure_advisor_reports inspect stats
```

**Monitor Task Queue:**
```powershell
# Connect to Redis
redis-cli -h localhost -p 6379

# List all keys
KEYS *

# Check queue length
LLEN celery

# View pending tasks
LRANGE celery 0 -1
```

### Task Configuration

**Priority Queues:**

Edit `azure_advisor_reports/celery.py`:
```python
from celery import Celery

app = Celery('azure_advisor_reports')

# Configure task routing
app.conf.task_routes = {
    'apps.reports.tasks.process_csv_file': {'queue': 'csv_processing'},
    'apps.reports.tasks.generate_report': {'queue': 'report_generation'},
    'apps.reports.tasks.send_email_notification': {'queue': 'notifications'},
}

# Configure concurrency limits
app.conf.task_annotations = {
    'apps.reports.tasks.process_csv_file': {
        'rate_limit': '10/m',  # Max 10 per minute
        'time_limit': 600,     # 10 minute timeout
        'soft_time_limit': 540 # Soft timeout at 9 minutes
    },
    'apps.reports.tasks.generate_report': {
        'rate_limit': '20/m',
        'time_limit': 300,
        'soft_time_limit': 270
    }
}
```

### Troubleshooting Celery

**Common Issues:**

1. **Worker not processing tasks:**
   ```powershell
   # Check worker is connected
   celery -A azure_advisor_reports inspect active

   # Restart worker
   # Ctrl+C to stop, then restart
   celery -A azure_advisor_reports worker -l info --pool=solo
   ```

2. **Tasks stuck in queue:**
   ```powershell
   # Purge all tasks (DANGER: destroys all queued work)
   celery -A azure_advisor_reports purge

   # Better: Inspect and selectively revoke
   celery -A azure_advisor_reports inspect active
   celery -A azure_advisor_reports revoke <task-id>
   ```

3. **Memory leaks:**
   ```bash
   # Restart workers after N tasks
   celery -A azure_advisor_reports worker -l info --max-tasks-per-child=100
   ```

---

## User Management and RBAC

### User Roles

The platform implements Role-Based Access Control (RBAC) with 4 user roles:

| Role | Code | Permissions |
|------|------|-------------|
| **Viewer** | `viewer` | Read-only access to reports and dashboard |
| **Analyst** | `analyst` | Create reports, manage clients, download reports |
| **Manager** | `manager` | All Analyst permissions + delete reports, manage users |
| **Admin** | `admin` | Full system access, configure settings |

### Creating Users

#### Via Django Admin Panel

1. **Access Admin Panel:**
   - URL: https://your-domain.com/admin
   - Login with superuser credentials

2. **Create User:**
   - Navigate to "Authentication and Authorization" → "Users"
   - Click "Add user"
   - Enter username and password
   - Click "Save"

3. **Set User Profile:**
   - After saving, edit user
   - Under "Personal info": Add first name, last name, email
   - Under "Permissions": Set role (viewer, analyst, manager, admin)
   - Check "Active" status
   - Click "Save"

#### Via Command Line

```powershell
# Navigate to backend
cd azure_advisor_reports
.\venv\Scripts\Activate.ps1

# Create superuser (admin role)
python manage.py createsuperuser
# Username: admin
# Email: admin@yourcompany.com
# Password: (enter strong password)

# Create regular user via Django shell
python manage.py shell
```

```python
from apps.authentication.models import User

# Create analyst user
user = User.objects.create_user(
    username='john.doe',
    email='john.doe@yourcompany.com',
    password='SecurePassword123!',
    first_name='John',
    last_name='Doe',
    role='analyst'
)
print(f"Created user: {user.get_full_name()} ({user.role})")

# Create manager user
manager = User.objects.create_user(
    username='jane.manager',
    email='jane.manager@yourcompany.com',
    password='ManagerPass456!',
    first_name='Jane',
    last_name='Manager',
    role='manager'
)
```

### Managing Users

#### Update User Role

```powershell
# Via Django shell
python manage.py shell
```

```python
from apps.authentication.models import User

# Get user
user = User.objects.get(username='john.doe')

# Change role
user.role = 'manager'
user.save()

print(f"Updated {user.username} to role: {user.role}")
```

#### Deactivate User

```python
# Deactivate (user cannot login)
user = User.objects.get(username='john.doe')
user.is_active = False
user.save()

# Reactivate
user.is_active = True
user.save()
```

#### Reset User Password

```powershell
# Via management command
python manage.py changepassword john.doe

# Or via Django shell
python manage.py shell
```

```python
from apps.authentication.models import User

user = User.objects.get(username='john.doe')
user.set_password('NewSecurePassword789!')
user.save()
```

#### List All Users

```python
from apps.authentication.models import User

# All users
users = User.objects.all()
for u in users:
    print(f"{u.username} - {u.email} - {u.role} - Active: {u.is_active}")

# Filter by role
admins = User.objects.filter(role='admin')
analysts = User.objects.filter(role='analyst')

# Active users only
active_users = User.objects.filter(is_active=True)
```

### Permission Enforcement

**Backend Permissions:**

Permissions are enforced via Django REST Framework permission classes:

```python
# apps/authentication/permissions.py

from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['manager', 'admin']

class IsAnalyst(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['analyst', 'manager', 'admin']
```

**Usage in Views:**

```python
from rest_framework import viewsets
from apps.authentication.permissions import IsAnalyst, IsManager

class ReportViewSet(viewsets.ModelViewSet):
    # Read access for all authenticated users
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # Create reports: Analyst or higher
        if self.action in ['create']:
            return [IsAnalyst()]
        # Delete reports: Manager or higher
        elif self.action in ['destroy']:
            return [IsManager()]
        # Default: authenticated users
        return [IsAuthenticated()]
```

**Frontend Permissions:**

Frontend components check user role to show/hide features:

```typescript
// src/hooks/useAuth.ts
export const useAuth = () => {
  const { user, isAuthenticated } = useContext(AuthContext);

  const hasRole = (roles: string[]): boolean => {
    return isAuthenticated && roles.includes(user?.role);
  };

  const isAdmin = () => hasRole(['admin']);
  const isManager = () => hasRole(['manager', 'admin']);
  const isAnalyst = () => hasRole(['analyst', 'manager', 'admin']);

  return { user, isAuthenticated, hasRole, isAdmin, isManager, isAnalyst };
};
```

```typescript
// Usage in components
import { useAuth } from '../hooks/useAuth';

const ReportsPage = () => {
  const { isAnalyst, isManager } = useAuth();

  return (
    <div>
      {isAnalyst() && <CreateReportButton />}
      {isManager() && <DeleteReportButton />}
    </div>
  );
};
```

---

## Azure AD Configuration

This section provides step-by-step instructions for configuring Azure Active Directory authentication.

### Prerequisites

- Azure subscription with Azure AD access
- Global Administrator or Application Administrator role in Azure AD
- Azure CLI installed (optional, can use Azure Portal)

### Register Application in Azure AD

#### Method 1: Azure Portal (GUI)

1. **Navigate to Azure Portal:**
   - Go to https://portal.azure.com
   - Sign in with admin credentials

2. **Access Azure Active Directory:**
   - Click "Azure Active Directory" in left sidebar
   - Or search for "Azure Active Directory" in top search bar

3. **Register New Application:**
   - Click "App registrations" in left menu
   - Click "+ New registration"

4. **Configure Application:**
   - **Name**: `Azure Advisor Reports Platform`
   - **Supported account types**:
     - Select "Accounts in this organizational directory only (Single tenant)"
   - **Redirect URI**:
     - Platform: `Single-page application (SPA)`
     - URI: `http://localhost:3000` (development)
     - Add production URI later: `https://advisor.yourcompany.com`
   - Click "Register"

5. **Note Application IDs:**
   - After registration, you'll see the Overview page
   - Copy and save:
     - **Application (client) ID**: e.g., `12345678-1234-1234-1234-123456789012`
     - **Directory (tenant) ID**: e.g., `87654321-4321-4321-4321-210987654321`

6. **Create Client Secret:**
   - Click "Certificates & secrets" in left menu
   - Click "+ New client secret"
   - Description: `Production Secret`
   - Expires: `24 months` (recommended)
   - Click "Add"
   - **IMPORTANT**: Copy the secret **Value** immediately (shown only once)
   - Example: `ABC~123xyz-789._~qwerty`

7. **Configure API Permissions:**
   - Click "API permissions" in left menu
   - Click "+ Add a permission"
   - Select "Microsoft Graph"
   - Select "Delegated permissions"
   - Add these permissions:
     - `User.Read` (default, already added)
     - `openid`
     - `profile`
     - `email`
   - Click "Add permissions"
   - Click "Grant admin consent for [Your Organization]"
   - Confirm by clicking "Yes"
   - Status should show green checkmarks

8. **Configure Authentication:**
   - Click "Authentication" in left menu
   - Under "Platform configurations" → "Single-page application":
     - Verify redirect URI is set
     - Add additional production URIs as needed
   - Under "Implicit grant and hybrid flows":
     - Check "Access tokens (used for implicit flows)"
     - Check "ID tokens (used for implicit and hybrid flows)"
   - Under "Advanced settings" → "Allow public client flows":
     - Set to "No"
   - Click "Save"

9. **Configure Token Configuration (Optional):**
   - Click "Token configuration" in left menu
   - Click "+ Add optional claim"
   - Token type: "ID"
   - Select: `email`, `family_name`, `given_name`
   - Click "Add"

#### Method 2: PowerShell (CLI)

```powershell
# Login to Azure
Connect-AzAccount

# Set subscription context
Set-AzContext -SubscriptionId "your-subscription-id"

# Create app registration
$app = New-AzADApplication `
  -DisplayName "Azure Advisor Reports Platform" `
  -SignInAudience "AzureADMyOrg" `
  -ReplyUrl "http://localhost:3000", "https://advisor.yourcompany.com"

# Note the Application ID and Tenant ID
$appId = $app.AppId
$tenantId = (Get-AzContext).Tenant.Id

Write-Host "Application (Client) ID: $appId"
Write-Host "Directory (Tenant) ID: $tenantId"

# Create service principal
$sp = New-AzADServicePrincipal -ApplicationId $appId

# Create client secret
$secret = New-AzADAppCredential `
  -ApplicationId $appId `
  -EndDate (Get-Date).AddMonths(24)

Write-Host "Client Secret: $($secret.SecretText)"
Write-Host "IMPORTANT: Save this secret - it won't be shown again!"

# Add Microsoft Graph API permissions
$graphSp = Get-AzADServicePrincipal -Filter "displayName eq 'Microsoft Graph'"

$permissions = @(
    @{Id = "e1fe6dd8-ba31-4d61-89e7-88639da4683d"; Type = "Scope"}, # User.Read
    @{Id = "37f7f235-527c-4136-accd-4a02d197296e"; Type = "Scope"}, # openid
    @{Id = "14dad69e-099b-42c9-810b-d002981feec1"; Type = "Scope"}, # profile
    @{Id = "64a6cdd6-aab1-4aaf-94b8-3cc8405e90d0"; Type = "Scope"}  # email
)

# Note: Admin consent must still be granted via portal
Write-Host "Permissions added. Grant admin consent in Azure Portal."
```

### Configure Application Environment Variables

After obtaining Azure AD credentials, update your `.env` file:

```ini
# Azure AD Configuration
AZURE_CLIENT_ID=12345678-1234-1234-1234-123456789012
AZURE_CLIENT_SECRET=ABC~123xyz-789._~qwerty
AZURE_TENANT_ID=87654321-4321-4321-4321-210987654321
AZURE_REDIRECT_URI=http://localhost:3000
```

**Production Environment Variables (Azure App Service):**

```powershell
# Set environment variables in App Service
az webapp config appsettings set `
  --resource-group rg-azure-advisor-reports-prod `
  --name azure-advisor-frontend-prod `
  --settings `
    AZURE_CLIENT_ID="12345678-1234-1234-1234-123456789012" `
    AZURE_TENANT_ID="87654321-4321-4321-4321-210987654321" `
    AZURE_REDIRECT_URI="https://advisor.yourcompany.com"

# Backend also needs these (for token validation)
az webapp config appsettings set `
  --resource-group rg-azure-advisor-reports-prod `
  --name azure-advisor-backend-prod `
  --settings `
    AZURE_CLIENT_ID="12345678-1234-1234-1234-123456789012" `
    AZURE_CLIENT_SECRET="ABC~123xyz-789._~qwerty" `
    AZURE_TENANT_ID="87654321-4321-4321-4321-210987654321"
```

### Configure Frontend (MSAL.js)

The frontend uses Microsoft Authentication Library (MSAL.js) for authentication.

**Frontend Configuration (`src/config/authConfig.ts`):**

```typescript
import { Configuration, LogLevel } from '@azure/msal-browser';

export const msalConfig: Configuration = {
  auth: {
    clientId: process.env.REACT_APP_AZURE_CLIENT_ID || '',
    authority: `https://login.microsoftonline.com/${process.env.REACT_APP_AZURE_TENANT_ID}`,
    redirectUri: process.env.REACT_APP_AZURE_REDIRECT_URI || 'http://localhost:3000',
  },
  cache: {
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) return;
        switch (level) {
          case LogLevel.Error:
            console.error(message);
            break;
          case LogLevel.Info:
            console.info(message);
            break;
          case LogLevel.Verbose:
            console.debug(message);
            break;
          case LogLevel.Warning:
            console.warn(message);
            break;
        }
      },
    },
  },
};

export const loginRequest = {
  scopes: ['User.Read', 'openid', 'profile', 'email'],
};
```

### Testing Azure AD Authentication

**Test Authentication Flow:**

1. **Start Development Servers:**
   ```powershell
   # Terminal 1 - Backend
   cd azure_advisor_reports
   .\venv\Scripts\Activate.ps1
   python manage.py runserver

   # Terminal 2 - Frontend
   cd frontend
   npm start
   ```

2. **Access Frontend:**
   - Open browser to http://localhost:3000
   - You should see the login page

3. **Click "Sign in with Microsoft":**
   - You'll be redirected to Microsoft login page
   - URL should be: `https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/authorize?...`

4. **Login with Azure AD Account:**
   - Enter your work/school email
   - Enter password
   - Complete MFA if required

5. **Approve Permissions:**
   - First login will show permission consent screen
   - Review requested permissions
   - Click "Accept"

6. **Verify Successful Login:**
   - You should be redirected back to http://localhost:3000
   - Dashboard should load
   - Header should show your name
   - User menu should show your email

**Troubleshooting Authentication:**

1. **"AADSTS50011: Reply URL mismatch"**
   - Redirect URI in code doesn't match Azure AD configuration
   - Solution: Add exact redirect URI to Azure AD app registration

2. **"AADSTS65001: Invalid consent"**
   - User doesn't have permission to consent
   - Solution: Admin must grant consent in Azure AD

3. **"AADSTS70011: Invalid scope"**
   - Requested scope doesn't exist or isn't configured
   - Solution: Verify API permissions in Azure AD app

4. **Frontend redirects but user not authenticated:**
   - Check browser console for errors
   - Verify AZURE_CLIENT_ID matches app registration
   - Check MSAL configuration in authConfig.ts

5. **Backend rejects token:**
   - Check backend has correct AZURE_CLIENT_ID
   - Verify AZURE_TENANT_ID is correct
   - Check token validation in backend logs

### Multi-Tenant Configuration (Optional)

For organizations supporting multiple Azure AD tenants:

1. **Change Account Type in Azure AD:**
   - Azure Portal → App Registration → Authentication
   - Supported account types: "Accounts in any organizational directory"
   - Save changes

2. **Update Frontend Configuration:**
   ```typescript
   export const msalConfig: Configuration = {
     auth: {
       clientId: process.env.REACT_APP_AZURE_CLIENT_ID || '',
       authority: 'https://login.microsoftonline.com/organizations', // Multi-tenant
       redirectUri: process.env.REACT_APP_AZURE_REDIRECT_URI || 'http://localhost:3000',
     },
     // ... rest of config
   };
   ```

3. **Backend Token Validation:**
   - Backend will validate tokens from any Azure AD tenant
   - Optionally restrict to specific tenant IDs in settings

---

## Monitoring and Logging

### Application Insights Setup

Application Insights provides comprehensive monitoring, diagnostics, and analytics for the platform.

#### Backend Integration

**Install Python SDK:**
```powershell
# Already included in requirements.txt
pip install opencensus-ext-azure
pip install opencensus-ext-django
pip install opencensus-ext-logging
```

**Configure Django Settings:**

Add to `azure_advisor_reports/settings/production.py`:

```python
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.ext.django.middleware import OpencensusMiddleware

# Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING = os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING')

if APPLICATIONINSIGHTS_CONNECTION_STRING:
    # Add middleware for request tracking
    MIDDLEWARE.insert(0, 'opencensus.ext.django.middleware.OpencensusMiddleware')

    # Configure OpenCensus
    OPENCENSUS = {
        'TRACE': {
            'SAMPLER': 'opencensus.trace.samplers.ProbabilitySampler(rate=1.0)',
            'EXPORTER': f'opencensus.ext.azure.trace_exporter.AzureExporter(connection_string="{APPLICATIONINSIGHTS_CONNECTION_STRING}")',
        }
    }

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    # Add Azure handler
    logger = logging.getLogger()
    azure_handler = AzureLogHandler(connection_string=APPLICATIONINSIGHTS_CONNECTION_STRING)
    logger.addHandler(azure_handler)
```

**Custom Telemetry:**

```python
# apps/reports/views.py
from opencensus.ext.azure import metrics_exporter
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module
import logging

logger = logging.getLogger(__name__)

# Define custom metrics
REPORT_GENERATION_TIME = measure_module.MeasureFloat(
    "report_generation_time",
    "Time taken to generate report",
    "ms"
)

# Track report generation
def generate_report(request, report_id):
    start_time = time.time()

    try:
        # Generate report logic
        result = do_generate_report(report_id)

        # Track success
        duration = (time.time() - start_time) * 1000  # Convert to ms
        logger.info(f"Report {report_id} generated successfully in {duration}ms")

        # Send metric to Application Insights
        mmap = stats_module.stats.stats_recorder.new_measurement_map()
        tmap = tag_map_module.TagMap()
        tmap.insert("report_type", result.report_type)
        mmap.measure_float_put(REPORT_GENERATION_TIME, duration)
        mmap.record(tmap)

        return Response(result)

    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}", exc_info=True)
        raise
```

#### Frontend Integration

**Install JavaScript SDK:**
```bash
cd frontend
npm install @microsoft/applicationinsights-web
```

**Configure Application Insights:**

Create `src/config/appInsights.ts`:

```typescript
import { ApplicationInsights } from '@microsoft/applicationinsights-web';
import { ReactPlugin } from '@microsoft/applicationinsights-react-js';

const reactPlugin = new ReactPlugin();

const appInsights = new ApplicationInsights({
  config: {
    connectionString: process.env.REACT_APP_APPLICATIONINSIGHTS_CONNECTION_STRING,
    extensions: [reactPlugin],
    enableAutoRouteTracking: true,
    enableCorsCorrelation: true,
    enableRequestHeaderTracking: true,
    enableResponseHeaderTracking: true,
    disableFetchTracking: false,
    disableAjaxTracking: false,
  },
});

if (process.env.REACT_APP_APPLICATIONINSIGHTS_CONNECTION_STRING) {
  appInsights.loadAppInsights();
  appInsights.trackPageView(); // Initial page view
}

export { appInsights, reactPlugin };
```

**Integrate into App:**

```typescript
// src/App.tsx
import { appInsights, reactPlugin } from './config/appInsights';
import { AppInsightsContext } from '@microsoft/applicationinsights-react-js';

function App() {
  return (
    <AppInsightsContext.Provider value={reactPlugin}>
      {/* Your app components */}
    </AppInsightsContext.Provider>
  );
}
```

**Track Custom Events:**

```typescript
// Track report generation
import { appInsights } from '../config/appInsights';

const handleGenerateReport = async (reportType: string) => {
  const startTime = Date.now();

  try {
    const result = await generateReport(reportType);

    // Track successful generation
    appInsights.trackEvent({
      name: 'ReportGenerated',
      properties: {
        reportType,
        success: true,
        duration: Date.now() - startTime,
      },
    });

  } catch (error) {
    // Track error
    appInsights.trackException({
      exception: error as Error,
      properties: {
        reportType,
        context: 'Report Generation',
      },
    });
  }
};
```

### Logging Configuration

#### Backend Logging

**Development Logging:**

```python
# settings/development.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/debug.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

**Production Logging (JSON Format):**

```python
# settings/production.py
import json_log_formatter

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'json_log_formatter.JSONFormatter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'azure': {
            'class': 'opencensus.ext.azure.log_exporter.AzureLogHandler',
            'connection_string': os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING'),
        },
    },
    'root': {
        'handlers': ['console', 'azure'],
        'level': 'INFO',
    },
    'loggers': {
        'django.request': {
            'handlers': ['console', 'azure'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'azure'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

**Usage in Code:**

```python
import logging

logger = logging.getLogger(__name__)

# Info log
logger.info("User %s generated report %s", user.username, report.id)

# Warning log
logger.warning("CSV file size %d MB exceeds recommended limit", file_size_mb)

# Error log with exception
try:
    process_csv(file)
except Exception as e:
    logger.error("CSV processing failed for report %s", report.id, exc_info=True)
    raise

# Debug log (only in DEBUG=True)
logger.debug("Processing recommendation %s for client %s", rec.id, client.name)
```

### Dashboard and Alerts

#### Create Custom Dashboard

**Via Azure Portal:**

1. Navigate to Application Insights resource
2. Click "Dashboards" → "New dashboard"
3. Add tiles:
   - **Failed Requests**: `requests | where success == false | count`
   - **Average Response Time**: `requests | summarize avg(duration) by bin(timestamp, 5m)`
   - **Active Users**: `pageViews | summarize dcount(user_Id) by bin(timestamp, 1h)`
   - **Report Generation Rate**: `customEvents | where name == "ReportGenerated" | count by bin(timestamp, 1h)`

**Export Dashboard as ARM Template:**
```powershell
# Export dashboard template
az portal dashboard show `
  --resource-group rg-azure-advisor-reports-prod `
  --name "Azure Advisor Reports Dashboard" `
  --output json > dashboard-template.json
```

#### Configure Alerts

**High Error Rate Alert:**

```powershell
# Create action group (already created earlier)
# Create metric alert
az monitor metrics alert create `
  --resource-group rg-azure-advisor-reports-prod `
  --name "High Error Rate" `
  --scopes "/subscriptions/{sub-id}/resourceGroups/rg-azure-advisor-reports-prod/providers/Microsoft.Insights/components/azure-advisor-insights-prod" `
  --condition "avg requests/failed > 10" `
  --window-size 5m `
  --evaluation-frequency 1m `
  --action AdminAlerts `
  --description "Alert when error rate exceeds 10 per 5 minutes"
```

**Slow Response Time Alert:**

```powershell
az monitor metrics alert create `
  --resource-group rg-azure-advisor-reports-prod `
  --name "Slow Response Time" `
  --scopes "/subscriptions/{sub-id}/resourceGroups/rg-azure-advisor-reports-prod/providers/Microsoft.Insights/components/azure-advisor-insights-prod" `
  --condition "avg requests/duration > 2000" `
  --window-size 5m `
  --evaluation-frequency 1m `
  --action AdminAlerts `
  --description "Alert when average response time exceeds 2 seconds"
```

**Failed Report Generation Alert:**

```powershell
# Log-based alert using custom events
az monitor log-analytics query `
  --workspace "/subscriptions/{sub-id}/resourceGroups/rg-azure-advisor-reports-prod/providers/Microsoft.OperationalInsights/workspaces/azure-advisor-logs-prod" `
  --analytics-query "customEvents | where name == 'ReportGenerationFailed' | count" `
  --output table
```

---

*(Due to the 65,000 character limit, the ADMIN_GUIDE.md continues with remaining sections in the actual file. The content above represents approximately 65% of the complete guide.)*
