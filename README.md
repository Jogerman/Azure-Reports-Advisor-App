# Azure Advisor Reports Platform

**Professional Azure Advisor report generation platform for cloud consultancies and MSPs**

[![Build Status](https://github.com/your-org/azure-advisor-reports/workflows/CI/badge.svg)](https://github.com/your-org/azure-advisor-reports/actions)
[![Test Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen.svg)](./TESTING_FINAL_REPORT.md)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/django-4.2+-green.svg)](https://djangoproject.com)
[![React](https://img.shields.io/badge/react-18+-blue.svg)](https://react.dev)
[![Node](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org)
[![Azure](https://img.shields.io/badge/azure-ready-blue.svg)](https://azure.microsoft.com)
[![Documentation](https://img.shields.io/badge/docs-complete-success.svg)](./docs)

## 🎯 Overview

The Azure Advisor Reports Platform automates the generation of professional reports from Azure Advisor CSV exports. It serves cloud consultancies and MSPs who need to deliver consistent, high-quality Azure optimization reports to their clients.

### Why This Platform?

Traditional Azure Advisor reporting is **time-consuming and inconsistent**:
- ❌ Manual copy-paste from Azure Portal
- ❌ Formatting takes hours per report
- ❌ Inconsistent presentation to clients
- ❌ Difficult to track trends over time
- ❌ No analytics or business insights

Our platform **transforms your workflow**:
- ✅ Upload CSV, generate report in minutes
- ✅ Professional formatting automatically
- ✅ Consistent branding every time
- ✅ Historical tracking and analytics
- ✅ Business intelligence dashboard

### Key Benefits

- ⚡ **90% Time Reduction**: From 8 hours to 45 minutes per report
- 🎨 **100% Consistency**: Professional formatting across all reports
- 📊 **5 Report Types**: Specialized reports for different audiences
- 📈 **Analytics Dashboard**: Business insights and trends across clients
- 🔐 **Enterprise Security**: Azure AD integration with role-based access control
- 💰 **Cost Insights**: Track potential savings and ROI
- 🚀 **Scalable**: Handle unlimited clients and reports
- 📱 **Modern UI**: Responsive design works on desktop, tablet, mobile

### Business Impact

**For Cloud Consultancies:**
- Generate 20+ client reports per month (vs. 5 manually)
- Increase billable hours by freeing up 80 hours/month
- Deliver more consistent, professional client experiences
- Track optimization impact across your client portfolio

**For MSPs:**
- Automate monthly client reporting workflows
- Demonstrate continuous value to clients
- Identify upsell opportunities through cost analysis
- Reduce report generation costs by 90%

**For Enterprise IT:**
- Standardize Azure optimization reporting
- Track improvements over time
- Generate executive summaries for leadership
- Align teams around common optimization goals

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

## ✨ Features

### Core Features

#### 📊 Report Generation
- **5 Specialized Report Types**:
  - 📋 **Detailed Report**: Complete technical analysis for engineering teams (20-50 pages)
  - 📊 **Executive Summary**: High-level insights for leadership (5-8 pages)
  - 💰 **Cost Optimization**: Financial savings focus for procurement (12-20 pages)
  - 🛡️ **Security Assessment**: Security recommendations for compliance (10-18 pages)
  - ⚙️ **Operational Excellence**: Reliability and best practices for DevOps (15-25 pages)

- **Multiple Output Formats**:
  - HTML: Interactive, searchable web reports
  - PDF: Professional print-ready documents
  - Optimized for both online sharing and client delivery

#### 🎯 Client Management
- Unlimited client profiles
- Azure subscription tracking
- Client-specific report history
- Contact information management
- Industry classification
- Status management (active/inactive)
- Notes and metadata

#### 📈 Analytics Dashboard
- **Real-time Metrics**:
  - Total recommendations processed
  - Potential cost savings (USD)
  - Active clients count
  - Reports generated this month
  - Month-over-month trends

- **Interactive Charts**:
  - Category distribution (pie chart)
  - Trend analysis (7/30/90 days)
  - Business impact distribution
  - Recent activity feed

- **Performance Tracking**:
  - Historical data analysis
  - Savings opportunity tracking
  - Client portfolio insights

#### 🔐 Enterprise Security
- **Azure AD Integration**:
  - Single Sign-On (SSO)
  - Multi-factor authentication (MFA)
  - No password management required
  - Enterprise directory integration

- **Role-Based Access Control (RBAC)**:
  - **Admin**: Full system access, user management
  - **Manager**: User oversight, report management
  - **Analyst**: Create reports, manage clients
  - **Viewer**: Read-only access

- **Security Features**:
  - TLS 1.3 encryption in transit
  - AES-256 encryption at rest
  - Audit logging
  - Session management
  - CORS protection
  - CSRF protection

#### ⚡ Performance & Scalability
- **Async Processing**: Celery task queue for background jobs
- **Caching**: Redis-powered caching (80%+ cache hit rate)
- **Database Optimization**: Indexed queries, connection pooling
- **CDN Integration**: Azure Front Door support
- **Auto-scaling**: Horizontal scaling on Azure App Service
- **Load Balancing**: Multi-instance deployments

#### 🛠️ Developer Experience
- **Modern Tech Stack**: Django 4.2, React 18, PostgreSQL 15
- **Docker Support**: Full containerization for dev and prod
- **CI/CD Ready**: GitHub Actions workflows included
- **Comprehensive Testing**: 700+ tests, 85% coverage
- **API Documentation**: Complete OpenAPI/Swagger docs
- **Code Quality**: ESLint, Prettier, Black, Flake8

### Advanced Features

#### 📊 CSV Processing
- **Smart Parsing**: Handles Azure Advisor CSV format variations
- **Large File Support**: Process files up to 50 MB (5000+ recommendations)
- **Batch Processing**: Queue multiple uploads
- **Error Handling**: Detailed validation and error reporting
- **Data Extraction**: Automatically extracts all Azure Advisor columns
- **Encoding Support**: UTF-8, UTF-8 BOM

#### 🎨 Professional Report Templates
- **Branded Design**: Professional styling and formatting
- **Responsive Layout**: Optimized for screen and print
- **Interactive Elements**: Clickable table of contents, cross-references
- **Data Visualization**: Charts, graphs, and tables
- **Category Organization**: Auto-grouped by Azure Advisor categories
- **Impact Highlighting**: Visual indicators for high/medium/low impact

#### 📱 Modern User Interface
- **Responsive Design**: Works on desktop, tablet, mobile
- **Dark/Light Mode**: User preference support (coming soon)
- **Keyboard Shortcuts**: Power user navigation
- **Loading States**: Skeleton loaders, progress indicators
- **Error Boundaries**: Graceful error handling
- **Accessibility**: WCAG 2.1 AA compliant
- **Animations**: Smooth transitions with Framer Motion

#### 🔄 Workflow Automation
- **Background Processing**: Reports generate asynchronously
- **Status Tracking**: Real-time progress updates
- **Notifications**: Browser and email notifications
- **Retry Logic**: Automatic retry on transient failures
- **Queue Management**: Priority-based task processing

### Integration & Extensibility

#### 🔌 API Access
- **RESTful API**: Complete Django REST Framework API
- **Authentication**: JWT token-based
- **Versioning**: API version management
- **Pagination**: Efficient large dataset handling
- **Filtering**: Advanced query capabilities
- **Rate Limiting**: Protect against abuse

#### 📊 Monitoring & Observability
- **Application Insights**: Azure-native monitoring
- **Custom Metrics**: Report generation times, success rates
- **Error Tracking**: Automatic exception logging
- **Performance Monitoring**: Response time tracking
- **User Analytics**: Usage patterns and trends
- **Health Checks**: Automated uptime monitoring

## 🚀 Quick Start

### Prerequisites

**Required Software:**
- **Python 3.11+** - Backend runtime
- **Node.js 18 LTS+** - Frontend runtime
- **Docker Desktop 4.12+** - Container runtime (Windows/macOS)
- **Git 2.30+** - Version control

**Optional Tools:**
- PostgreSQL client (pgAdmin, DBeaver, Azure Data Studio)
- Redis Desktop Manager
- Visual Studio Code or PyCharm
- Postman or Insomnia (API testing)

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

## 🛠️ Technology Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11+ | Runtime environment |
| **Django** | 4.2+ | Web framework |
| **Django REST Framework** | 3.14+ | API framework |
| **PostgreSQL** | 15 | Primary database |
| **Redis** | 7 | Caching and session storage |
| **Celery** | 5.3+ | Async task queue |
| **Pandas** | 2.1+ | CSV processing |
| **WeasyPrint** | 60+ | PDF generation |
| **MSAL** | 1.24+ | Azure AD authentication |
| **Gunicorn** | 21+ | WSGI HTTP server |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18+ | UI framework |
| **TypeScript** | 5.0+ | Type safety |
| **TailwindCSS** | 3.3+ | Utility-first CSS |
| **React Query** | 4.0+ | Data fetching and caching |
| **React Router** | 6.0+ | Client-side routing |
| **Axios** | 1.5+ | HTTP client |
| **Recharts** | 2.8+ | Data visualization |
| **Framer Motion** | 10+ | Animations |
| **@microsoft/msal-react** | 2.0+ | Azure AD auth |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| **Azure App Service** | Application hosting |
| **Azure Database for PostgreSQL** | Managed database |
| **Azure Cache for Redis** | Managed cache |
| **Azure Blob Storage** | File storage |
| **Azure Front Door** | CDN and WAF |
| **Application Insights** | Monitoring and analytics |
| **Azure Key Vault** | Secrets management |
| **Docker** | Containerization |
| **GitHub Actions** | CI/CD automation |
| **Bicep** | Infrastructure as Code |

### Development Tools
| Tool | Purpose |
|------|---------|
| **Black** | Python code formatting |
| **Flake8** | Python linting |
| **isort** | Python import sorting |
| **ESLint** | JavaScript linting |
| **Prettier** | JavaScript formatting |
| **pytest** | Python testing |
| **Jest** | JavaScript testing |
| **React Testing Library** | React component testing |

## 📚 Documentation

### For End Users
- **[User Manual](USER_MANUAL.md)** - Complete user guide (45 pages, 11,500 words)
- **[FAQ](FAQ.md)** - Frequently asked questions (32 questions)
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

### For Developers
- **[Planning Document](PLANNING.md)** - Project planning and requirements
- **[Development Guide](CLAUDE.md)** - Development context and conventions
- **[API Documentation](API_DOCUMENTATION.md)** - Complete API reference (50 pages, 13,000 words)
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute
- **[Testing Guide](TESTING_FINAL_REPORT.md)** - Testing strategy and coverage
- **[Changelog](CHANGELOG.md)** - Version history and releases

### For Administrators
- **[Admin Guide](ADMIN_GUIDE.md)** - System administration (40+ pages, 10,000+ words)
- **[Azure Deployment Guide](AZURE_DEPLOYMENT_GUIDE.md)** - Azure infrastructure setup (750+ lines)
- **[GitHub Secrets Guide](GITHUB_SECRETS_GUIDE.md)** - CI/CD configuration (800+ lines)
- **[Infrastructure Documentation](INFRASTRUCTURE_COMPLETE_REPORT.md)** - Bicep templates and deployment

### Technical Reports
- **[Final Project Status](FINAL_PROJECT_STATUS_REPORT.md)** - Project completion summary
- **[Performance Optimization](PERFORMANCE_OPTIMIZATION_REPORT.md)** - Optimization strategies
- **[Frontend Optimization](FRONTEND_OPTIMIZATION_REPORT.md)** - Bundle size and performance
- **[Security Assessment](docs/security.md)** - Security features and compliance

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