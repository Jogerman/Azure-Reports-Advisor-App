# Azure Advisor Reports Platform

**Professional Azure Advisor report generation platform for cloud consultancies and MSPs**

[![Build Status](https://github.com/your-org/azure-advisor-reports/workflows/CI/badge.svg)](https://github.com/your-org/azure-advisor-reports/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Node](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org)

## 🎯 Overview

The Azure Advisor Reports Platform automates the generation of professional reports from Azure Advisor CSV exports. It serves cloud consultancies and MSPs who need to deliver consistent, high-quality Azure optimization reports to their clients.

**Key Benefits:**
- ⚡ **90% Time Reduction**: From 8 hours to 45 minutes per report
- 🎨 **100% Consistency**: Professional formatting across all reports
- 📊 **5 Report Types**: Specialized reports for different audiences
- 📈 **Analytics Dashboard**: Business insights and trends
- 🔐 **Enterprise Security**: Azure AD integration with RBAC

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│            Azure Active Directory                │
│          (Authentication Provider)               │
└──────────────────┬──────────────────────────────┘
                   │ OAuth 2.0
                   ▼
┌──────────────────────────────────────────────────┐
│          React Frontend (Port 3000)              │
│  • Client Management UI                          │
│  • Report Upload Interface                       │
│  • Dashboard & Analytics                         │
│  • Report Preview & Download                     │
└──────────────────┬───────────────────────────────┘
                   │ REST API
                   ▼
┌──────────────────────────────────────────────────┐
│         Django Backend (Port 8000)               │
│  • API Endpoints (DRF)                           │
│  • CSV Processing Logic                          │
│  • Report Generation Engine                      │
│  • Business Logic Layer                          │
└───────┬──────────┬──────────┬───────────────────┘
        │          │          │
        ▼          ▼          ▼
┌─────────┐  ┌─────────┐  ┌──────────┐
│PostgreSQL│  │  Redis  │  │  Celery  │
│   DB     │  │  Cache  │  │  Workers │
└─────────┘  └─────────┘  └──────────┘
        │          │          │
        └──────────┴──────────┘
                   │
                   ▼
        ┌────────────────────┐
        │  Azure Blob Storage│
        │  (Reports/Files)   │
        └────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose**
- **Git**

### Windows Setup

1. **Clone the repository:**
   ```powershell
   git clone <repository-url>
   cd azure-advisor-reports
   ```

2. **Setup environment variables:**
   ```powershell
   Copy-Item .env.example .env
   # Edit .env with your Azure AD credentials
   ```

3. **Start all services:**
   ```powershell
   docker-compose up -d
   ```

4. **Setup backend (optional for development):**
   ```powershell
   cd azure_advisor_reports
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api/v1
   - Admin Panel: http://localhost:8000/admin

### Linux/macOS Setup

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd azure-advisor-reports
   cp .env.example .env
   # Edit .env with your Azure AD credentials
   ```

2. **Start services:**
   ```bash
   docker-compose up -d
   ```

3. **Verify all services are running:**
   ```bash
   docker-compose ps
   ```

## 📁 Project Structure

```
azure-advisor-reports/
├── azure_advisor_reports/          # Django backend
│   ├── apps/
│   │   ├── authentication/         # Azure AD auth
│   │   ├── clients/                # Client management
│   │   ├── reports/                # Report generation
│   │   ├── analytics/              # Dashboard analytics
│   │   └── core/                   # Shared utilities
│   ├── azure_advisor_reports/      # Django settings
│   │   ├── settings/               # Environment-specific settings
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── celery.py
│   │   └── urls.py
│   ├── templates/                  # Report templates
│   ├── requirements.txt
│   └── manage.py
├── frontend/                       # React frontend
│   ├── src/
│   │   ├── components/            # Reusable components
│   │   ├── pages/                 # Page components
│   │   ├── services/              # API services
│   │   ├── hooks/                 # Custom React hooks
│   │   ├── utils/                 # Utility functions
│   │   └── config/                # App configuration
│   ├── package.json
│   └── tailwind.config.js
├── docs/                          # Documentation
├── scripts/                       # Utility scripts
├── tests/                         # Test files
├── docker-compose.yml             # Local development
├── .env.example                   # Environment template
└── README.md                      # This file
```

## 🔧 Configuration

### Required Environment Variables

```bash
# Django
SECRET_KEY=your-super-secret-django-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/azure_advisor_reports

# Redis
REDIS_URL=redis://localhost:6379/0

# Azure AD
AZURE_CLIENT_ID=your-azure-ad-client-id
AZURE_CLIENT_SECRET=your-azure-ad-client-secret
AZURE_TENANT_ID=your-azure-tenant-id

# Azure Storage (optional)
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
```

### Azure AD Setup

1. **Register an application** in Azure AD
2. **Configure redirect URIs**: `http://localhost:3000` (development)
3. **Generate client secret**
4. **Configure API permissions**: OpenID, Profile, Email
5. **Update .env file** with your credentials

## 🎨 Report Types

The platform generates 5 specialized report types:

1. **📋 Detailed Report** - Complete technical analysis for engineering teams
2. **📊 Executive Summary** - High-level insights for leadership
3. **💰 Cost Optimization** - Financial savings focus for procurement
4. **🛡️ Security Assessment** - Security recommendations for compliance
5. **⚙️ Operational Excellence** - Reliability and best practices for DevOps

## 🛠️ Development

### Backend Development

```powershell
cd azure_advisor_reports
.\venv\Scripts\Activate.ps1

# Run Django development server
python manage.py runserver

# Run Celery worker
celery -A azure_advisor_reports worker -l info

# Run tests
pytest --cov=apps

# Code formatting
black .
isort .
flake8 .
```

### Frontend Development

```powershell
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build
```

### Database Management

```powershell
# Create and run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data
python manage.py loaddata sample_data.json
```

## 🧪 Testing

### Run All Tests

```powershell
# Backend tests
cd azure_advisor_reports
pytest --cov=apps --cov-report=html

# Frontend tests
cd frontend
npm test -- --coverage
```

### Integration Testing

```powershell
# Test complete workflow
docker-compose up -d
python manage.py test tests.integration
```

## 📊 API Documentation

Once running, API documentation is available at:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/

### Key API Endpoints

```
# Authentication
POST /api/v1/auth/login/
POST /api/v1/auth/logout/
GET  /api/v1/auth/user/

# Clients
GET    /api/v1/clients/
POST   /api/v1/clients/
GET    /api/v1/clients/{id}/
PUT    /api/v1/clients/{id}/
DELETE /api/v1/clients/{id}/

# Reports
POST /api/v1/reports/upload/
POST /api/v1/reports/generate/
GET  /api/v1/reports/{id}/status/
GET  /api/v1/reports/{id}/download/

# Analytics
GET  /api/v1/analytics/dashboard/
GET  /api/v1/analytics/trends/
```

## 🚀 Deployment

### Production Deployment (Azure)

1. **Provision Azure resources:**
   ```bash
   # Create resource group
   az group create --name rg-azure-advisor-prod --location eastus

   # Create App Services, Database, Redis, Storage
   # (See deployment documentation)
   ```

2. **Deploy application:**
   ```bash
   # Using GitHub Actions (recommended)
   git push origin main

   # Or manual deployment
   docker build -t azure-advisor-backend .
   az webapp deployment container config
   ```

### Environment-Specific Settings

- **Development**: Uses `settings.development`
- **Staging**: Uses `settings.base` + environment overrides
- **Production**: Uses `settings.production`

## 📈 Monitoring

### Health Checks

- **Application**: http://localhost:8000/api/health/
- **Database**: Included in health check
- **Redis**: Included in health check
- **Celery**: Monitor task queues

### Logging

- **Development**: Console + file logging
- **Production**: Structured JSON logging + Azure Application Insights

## 🔐 Security

- **Authentication**: Azure AD OAuth 2.0
- **Authorization**: Role-based access control (RBAC)
- **API Security**: JWT tokens, CORS, rate limiting
- **Data Protection**: Encryption at rest and in transit
- **File Upload**: Validation and virus scanning
- **HTTPS**: Required in production

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 for Python code
- Use ESLint + Prettier for JavaScript
- Write tests for new features
- Update documentation
- Follow conventional commit messages

## 📚 Documentation

- **[Planning Document](PLANNING.md)** - Project planning and requirements
- **[Architecture Guide](ARCHITECTURE.md)** - System architecture details
- **[API Documentation](docs/api.md)** - Detailed API reference
- **[Deployment Guide](docs/deployment.md)** - Production deployment
- **[Development Guide](CLAUDE.md)** - Development context for AI assistants

## 📞 Support

- **Documentation**: Check the docs/ directory
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Email**: support@yourcompany.com

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Azure Advisor Team** - For the excellent cost optimization recommendations
- **Django Community** - For the robust web framework
- **React Community** - For the powerful frontend library
- **Microsoft** - For Azure services and authentication

---

**Built with ❤️ for the cloud optimization community**