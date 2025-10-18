# CLAUDE.md - Azure Advisor Reports Platform

**Last Updated:** September 29, 2025  
**Version:** 1.0  
**Project Status:** Active Development

## Notes
- always read PLANNING.md at the start of every new conversation
- check TASK.md before starting your work
- mark completed task immediately
- add newly discovered tasks

---

## 📖 Document Purpose

This document provides context and guidance for Claude Code sessions working on the Azure Advisor Reports Platform. It contains essential information about the project's architecture, conventions, and development practices to ensure consistent and informed development.

---

## 🎯 Project Overview

### What This Project Does

Azure Advisor Reports Platform is an enterprise SaaS application that automates the generation of professional reports from Azure Advisor CSV exports. It serves cloud consultancies and MSPs who need to deliver consistent, high-quality Azure optimization reports to their clients.

**Core Value Proposition:**
- Reduces report generation time from 8 hours to 45 minutes (90% reduction)
- Ensures 100% consistency in report formatting
- Provides 5 specialized report types with professional HTML/PDF output
- Includes analytics dashboard for business insights

### Key Business Context

- **Target Users:** Cloud engineers, service delivery managers, IT consultants
- **Primary Use Case:** Upload Azure Advisor CSV → Generate professional reports → Deliver to clients
- **Critical Success Factor:** Speed and quality of report generation
- **Revenue Impact:** Saves 80 hours/month of manual work per company

---

## 🏗️ Technical Architecture

### Technology Stack

**Backend:**
```
- Framework: Django 4.2+
- API: Django REST Framework (DRF)
- Database: PostgreSQL 15
- Cache: Redis 7
- Task Queue: Celery (for async processing)
- Authentication: Azure AD via MSAL
- PDF Generation: ReportLab
- Data Processing: Pandas
```

**Frontend:**
```
- Framework: React 18+
- Routing: React Router v6
- State Management: React Query (TanStack Query)
- Styling: TailwindCSS (utility-first)
- Charts: Recharts
- Authentication: @microsoft/msal-react
- HTTP Client: Axios
- Animations: Framer Motion
```

**Infrastructure:**
```
- Cloud: Microsoft Azure
- Compute: Azure App Service (Linux)
- Database: Azure Database for PostgreSQL
- Cache: Azure Cache for Redis
- Storage: Azure Blob Storage
- Monitoring: Application Insights
- CI/CD: GitHub Actions
- Containers: Docker + Docker Compose
```

### Project Structure

```
azure-advisor-reports/
├── azure_advisor_reports/          # Django backend
│   ├── apps/
│   │   ├── authentication/         # Azure AD auth
│   │   ├── clients/                # Client management
│   │   ├── reports/                # Report generation
│   │   └── analytics/              # Dashboard analytics
│   ├── azure_advisor_reports/      # Django settings
│   ├── manage.py
│   └── requirements.txt
├── frontend/                       # React frontend
│   ├── src/
│   │   ├── components/            # Reusable components
│   │   ├── pages/                 # Page components
│   │   ├── services/              # API services
│   │   ├── hooks/                 # Custom React hooks
│   │   ├── utils/                 # Utility functions
│   │   └── App.js
│   └── package.json
├── docker-compose.yml             # Local development
├── .env.example                   # Environment template
├── CLAUDE.md                      # This file
└── README.md                      # User-facing docs
```

### System Architecture Diagram

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

---

## 🔑 Key Design Decisions

### 1. Async Processing with Celery

**Decision:** Use Celery for CSV processing and report generation  
**Rationale:** 
- Large CSV files (up to 50MB) can take 30+ seconds to process
- PDF generation can take 20-40 seconds
- Prevents timeout issues and improves UX with progress indicators

**Implementation Pattern:**
```python
# In reports/tasks.py
@shared_task
def process_csv_and_generate_report(report_id, report_type):
    report = Report.objects.get(id=report_id)
    # Process CSV
    # Generate report
    # Save to blob storage
    return report_id
```

### 2. Separation of Report Types

**Decision:** Five distinct report types instead of one customizable report  
**Rationale:**
- Each report serves a specific audience (technical vs executive)
- Easier to maintain and test individual templates
- Allows for specialized formatting and content per type

**Report Types:**
1. **Detailed Report** → Technical teams (full data)
2. **Executive Summary** → Leadership (high-level)
3. **Cost Optimization** → Finance/procurement (savings focus)
4. **Security Assessment** → Security teams (risk focus)
5. **Operational Excellence** → DevOps (reliability focus)

### 3. Client-Centric Data Model

**Decision:** All reports must be associated with a client  
**Rationale:**
- Enables historical tracking per client
- Supports multi-tenant usage patterns
- Facilitates billing and reporting at client level

**Key Relationship:**
```
Client (1) ──── (Many) Reports ──── (Many) Recommendations
```

### 4. Azure AD as Single Auth Provider

**Decision:** Only support Azure AD authentication (no email/password)  
**Rationale:**
- Target users already have Azure subscriptions
- Enterprise security requirements (MFA, conditional access)
- Simplifies security model and reduces attack surface
- Aligns with Microsoft ecosystem

### 5. PostgreSQL Over NoSQL

**Decision:** Use PostgreSQL despite some semi-structured data  
**Rationale:**
- CSV data has consistent schema (Azure Advisor format)
- Need for ACID transactions
- Complex queries for analytics dashboard
- Team familiarity with SQL
- JSONField available for flexible data storage

---

## 💻 Development Environment Setup

### Prerequisites

```bash
# Required software
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git
- PostgreSQL client tools (optional, for debugging)
```

### Initial Setup (Windows PowerShell)

```powershell
# 1. Clone repository
git clone <repository-url>
cd azure-advisor-reports

# 2. Setup backend
cd azure_advisor_reports
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Setup frontend
cd ..\frontend
npm install

# 4. Configure environment
cd ..
Copy-Item .env.example .env
# Edit .env with your Azure AD credentials

# 5. Start services with Docker
docker-compose up -d postgres redis

# 6. Run migrations
cd azure_advisor_reports
python manage.py migrate
python manage.py createsuperuser

# 7. Start development servers
# Terminal 1 - Backend
python manage.py runserver

# Terminal 2 - Celery worker
celery -A azure_advisor_reports worker -l info

# Terminal 3 - Frontend
cd ..\frontend
npm start
```

### Environment Variables

**Critical Variables (required):**
```bash
SECRET_KEY=<django-secret-key>
DATABASE_URL=postgres://user:pass@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0
AZURE_CLIENT_ID=<your-azure-ad-app-id>
AZURE_CLIENT_SECRET=<your-azure-ad-secret>
AZURE_TENANT_ID=<your-azure-tenant-id>
AZURE_REDIRECT_URI=http://localhost:3000
```

**Optional Variables:**
```bash
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
AZURE_STORAGE_CONNECTION_STRING=<for-blob-storage>
```

---

## 📝 Coding Conventions

### Backend (Django/Python)

**Style Guide:**
- Follow PEP 8
- Use Black for formatting (`black .`)
- Use isort for imports (`isort .`)
- Maximum line length: 100 characters

**Naming Conventions:**
```python
# Models: PascalCase
class ClientProfile(models.Model):
    pass

# Views/ViewSets: PascalCase with descriptor
class ReportViewSet(viewsets.ModelViewSet):
    pass

# Functions/methods: snake_case
def process_csv_file(file_path):
    pass

# Constants: UPPER_SNAKE_CASE
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
```

**Django App Structure:**
```
app_name/
├── __init__.py
├── models.py           # Database models
├── serializers.py      # DRF serializers
├── views.py            # API views/viewsets
├── urls.py             # URL routing
├── tasks.py            # Celery tasks
├── services.py         # Business logic
├── utils.py            # Helper functions
└── tests/
    ├── test_models.py
    ├── test_views.py
    └── test_services.py
```

**API Response Format:**
```python
# Success response
{
    "status": "success",
    "data": { ... },
    "message": "Operation completed successfully"
}

# Error response
{
    "status": "error",
    "errors": { ... },
    "message": "Operation failed"
}
```

### Frontend (React/JavaScript)

**Style Guide:**
- Follow Airbnb JavaScript Style Guide
- Use ESLint + Prettier
- Functional components with hooks (no class components)
- Use arrow functions for component definition

**Naming Conventions:**
```javascript
// Components: PascalCase
const ReportCard = () => { ... }

// Hooks: camelCase with 'use' prefix
const useReportData = () => { ... }

// Functions: camelCase
const fetchReportData = async () => { ... }

// Constants: UPPER_SNAKE_CASE
const MAX_FILE_SIZE = 50 * 1024 * 1024;

// Props destructuring
const ReportCard = ({ title, data, onDownload }) => { ... }
```

**Component Structure:**
```javascript
// 1. Imports
import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';

// 2. Component definition
const ComponentName = ({ prop1, prop2 }) => {
  // 3. Hooks
  const [state, setState] = useState(null);
  const { data } = useQuery(...)
  
  // 4. Event handlers
  const handleClick = () => { ... }
  
  // 5. Effects
  useEffect(() => { ... }, [dependencies]);
  
  // 6. Render
  return ( ... )
}

// 7. Export
export default ComponentName;
```

**File Organization:**
```
components/
├── common/          # Shared components
│   ├── Button.js
│   ├── Card.js
│   └── Modal.js
├── reports/         # Feature-specific components
│   ├── ReportCard.js
│   ├── ReportList.js
│   └── ReportUpload.js
└── layout/          # Layout components
    ├── Header.js
    ├── Sidebar.js
    └── Footer.js
```

---

## 🔄 Common Development Tasks

### Creating a New Django App

```powershell
cd azure_advisor_reports
python manage.py startapp new_app_name
# Then add to INSTALLED_APPS in settings.py
```

### Adding a New API Endpoint

```python
# 1. Create serializer (serializers.py)
class NewModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewModel
        fields = '__all__'

# 2. Create viewset (views.py)
class NewModelViewSet(viewsets.ModelViewSet):
    queryset = NewModel.objects.all()
    serializer_class = NewModelSerializer
    permission_classes = [IsAuthenticated]

# 3. Register URL (urls.py)
router.register(r'new-endpoint', NewModelViewSet, basename='new-endpoint')
```

### Creating a New React Component

```javascript
// src/components/NewComponent.js
import React from 'react';

const NewComponent = ({ prop1, prop2 }) => {
  return (
    <div className="container mx-auto p-4">
      {/* Component content */}
    </div>
  );
};

export default NewComponent;
```

### Adding a New Celery Task

```python
# In app/tasks.py
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def new_background_task(self, arg1, arg2):
    try:
        # Task logic here
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

### Running Tests

```powershell
# Backend tests
cd azure_advisor_reports
python manage.py test

# With coverage
pytest --cov=apps --cov-report=html

# Frontend tests
cd frontend
npm test

# With coverage
npm test -- --coverage
```

---

## 📊 Data Models Reference

### Core Models

**Client Model:**
```python
class Client(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    company_name = models.CharField(max_length=255)
    industry = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField()
    azure_subscription_ids = models.JSONField(default=list)
    status = models.CharField(
        max_length=20,
        choices=[('active', 'Active'), ('inactive', 'Inactive')]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Report Model:**
```python
class Report(models.Model):
    REPORT_TYPES = [
        ('detailed', 'Detailed Report'),
        ('executive', 'Executive Summary'),
        ('cost', 'Cost Optimization'),
        ('security', 'Security Assessment'),
        ('operations', 'Operational Excellence'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    csv_file = models.FileField(upload_to='csv_uploads/')
    html_file = models.FileField(upload_to='reports/html/', blank=True)
    pdf_file = models.FileField(upload_to='reports/pdf/', blank=True)
    status = models.CharField(max_length=20, default='pending')
    analysis_data = models.JSONField(default=dict)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Recommendation Model:**
```python
class Recommendation(models.Model):
    CATEGORIES = [
        ('cost', 'Cost'),
        ('security', 'Security'),
        ('reliability', 'Reliability'),
        ('operational_excellence', 'Operational Excellence'),
    ]
    
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    category = models.CharField(max_length=30, choices=CATEGORIES)
    business_impact = models.CharField(max_length=10)
    recommendation = models.TextField()
    resource_name = models.CharField(max_length=255)
    potential_savings = models.DecimalField(max_digits=10, decimal_places=2)
    # ... other fields
```

---

## 🔐 Security Considerations

### Authentication Flow

```
1. User clicks "Login with Microsoft"
2. Frontend redirects to Azure AD login page
3. User authenticates with Azure credentials
4. Azure AD redirects back with authorization code
5. Frontend exchanges code for access token
6. Frontend stores token and makes API requests with token
7. Backend validates token with Azure AD on each request
```

### API Security Checklist

- ✅ All endpoints require authentication (except health check)
- ✅ Use HTTPS in production (TLS 1.3)
- ✅ Implement CSRF protection (Django default)
- ✅ Validate all user input
- ✅ Use parameterized queries (ORM prevents SQL injection)
- ✅ Rate limiting on API endpoints
- ✅ File upload validation (size, type, content)
- ✅ Sanitize file names before storage
- ✅ Don't expose sensitive data in error messages
- ✅ Use secure headers (HSTS, CSP, X-Frame-Options)

### Sensitive Data Handling

**Never commit to Git:**
- `.env` file with real credentials
- `*.pem`, `*.key` files
- Database dumps with real data
- Azure storage connection strings
- API keys or secrets

**File Upload Security:**
```python
# Always validate uploaded files
ALLOWED_EXTENSIONS = ['csv']
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def validate_csv_file(file):
    # Check extension
    if not file.name.endswith('.csv'):
        raise ValidationError("Only CSV files allowed")
    
    # Check size
    if file.size > MAX_FILE_SIZE:
        raise ValidationError("File too large")
    
    # Scan content (basic check)
    # Add virus scanning in production
```

---

## 🧪 Testing Strategy

### Backend Testing

**Test Coverage Goals:**
- Models: 90%+
- Views/APIs: 85%+
- Services/Utils: 80%+
- Overall: 85%+

**Test Structure:**
```python
# tests/test_models.py
class ClientModelTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(...)
    
    def test_client_creation(self):
        self.assertEqual(self.client.company_name, "Test Company")
    
    def test_client_str_representation(self):
        self.assertEqual(str(self.client), "Test Company")

# tests/test_views.py
class ReportAPITest(APITestCase):
    def setUp(self):
        self.client.force_authenticate(user=self.user)
    
    def test_list_reports(self):
        response = self.client.get('/api/reports/')
        self.assertEqual(response.status_code, 200)
```

### Frontend Testing

**Test Coverage Goals:**
- Components: 70%+
- Hooks: 80%+
- Utils: 85%+

**Test Structure:**
```javascript
// __tests__/ReportCard.test.js
import { render, screen, fireEvent } from '@testing-library/react';
import ReportCard from '../ReportCard';

describe('ReportCard', () => {
  const mockReport = {
    id: '123',
    title: 'Test Report',
    status: 'completed'
  };
  
  it('renders report title', () => {
    render(<ReportCard report={mockReport} />);
    expect(screen.getByText('Test Report')).toBeInTheDocument();
  });
  
  it('calls onDownload when download button clicked', () => {
    const mockDownload = jest.fn();
    render(<ReportCard report={mockReport} onDownload={mockDownload} />);
    fireEvent.click(screen.getByText('Download'));
    expect(mockDownload).toHaveBeenCalledWith('123');
  });
});
```

### Integration Testing

```python
# Test full workflow
class ReportGenerationIntegrationTest(TestCase):
    def test_csv_upload_to_report_generation(self):
        # 1. Upload CSV
        # 2. Process CSV
        # 3. Generate report
        # 4. Verify report content
        # 5. Download report
        pass
```

---

## 🚀 Deployment

### Production Environment Variables

```bash
# Set these in Azure App Service Configuration
DEBUG=False
SECRET_KEY=<strong-random-key>
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=<azure-postgres-connection-string>
REDIS_URL=<azure-redis-connection-string>
AZURE_STORAGE_CONNECTION_STRING=<blob-storage-connection>
```

### Docker Deployment

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Push to Azure Container Registry
docker tag backend:latest <registry>.azurecr.io/backend:latest
docker push <registry>.azurecr.io/backend:latest

# Deploy to Azure App Service
az webapp create --resource-group <rg> --plan <plan> --name <app-name>
```

### Database Migrations in Production

```bash
# Always backup before migrations
az postgres db backup ...

# Run migrations
python manage.py migrate --no-input

# Verify
python manage.py showmigrations
```

---

## ⚠️ Known Issues & Gotchas

### 1. CSV Encoding Issues

**Problem:** Some Azure Advisor exports use UTF-8 with BOM  
**Solution:** Always specify encoding when reading CSVs
```python
df = pd.read_csv(file_path, encoding='utf-8-sig')
```

### 2. Large File Upload Timeouts

**Problem:** Files >20MB can timeout on slow connections  
**Solution:** Implemented chunked uploads and celery processing  
**Status:** Resolved, but monitor for issues

### 3. PDF Generation Memory Issues

**Problem:** Generating PDFs for reports with 500+ recommendations can use 500MB+ RAM  
**Solution:** Use streaming and pagination in PDF generation  
**Status:** Monitoring, may need optimization

### 4. Azure AD Token Expiration

**Problem:** Tokens expire after 1 hour by default  
**Solution:** Frontend implements token refresh automatically  
**Note:** Always handle 401 responses and re-authenticate

### 5. React Query Cache Invalidation

**Problem:** Dashboard doesn't update after report generation  
**Solution:** Invalidate queries after mutations
```javascript
const mutation = useMutation(generateReport, {
  onSuccess: () => {
    queryClient.invalidateQueries('reports');
  }
});
```

---

## 📚 External Resources

### Documentation
- **Django Docs:** https://docs.djangoproject.com/
- **DRF Docs:** https://www.django-rest-framework.org/
- **React Docs:** https://react.dev/
- **React Query:** https://tanstack.com/query/latest
- **Azure AD Auth:** https://docs.microsoft.com/azure/active-directory/

### Azure Services
- **Azure Advisor:** https://docs.microsoft.com/azure/advisor/
- **App Service:** https://docs.microsoft.com/azure/app-service/
- **Blob Storage:** https://docs.microsoft.com/azure/storage/blobs/

### Tools
- **Celery:** https://docs.celeryproject.org/
- **ReportLab:** https://www.reportlab.com/docs/
- **Pandas:** https://pandas.pydata.org/docs/

---

## 🤝 Contributing Guidelines

### Git Workflow

```bash
# 1. Create feature branch
git checkout -b feature/new-feature-name

# 2. Make changes and commit
git add .
git commit -m "feat: add new feature"

# 3. Push to remote
git push origin feature/new-feature-name

# 4. Create Pull Request
# 5. After approval, merge to main
```

### Commit Message Format

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Examples:**
```
feat(reports): add cost optimization report type
fix(auth): resolve token refresh issue
docs(readme): update setup instructions
```

### Code Review Checklist

- [ ] Code follows project conventions
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No sensitive data in commits
- [ ] Performance impact considered
- [ ] Security implications reviewed
- [ ] Error handling implemented
- [ ] Logging added where appropriate

---

## 🐛 Debugging Tips

### Backend Debugging

```python
# Use Django shell for testing
python manage.py shell

# Import and test models
from apps.reports.models import Report
Report.objects.all()

# Test serializers
from apps.reports.serializers import ReportSerializer
serializer = ReportSerializer(report)
serializer.data

# Check SQL queries
from django.db import connection
print(connection.queries)
```

### Frontend Debugging

```javascript
// React Query DevTools
import { ReactQueryDevtools } from 'react-query/devtools';

// Add to App.js
<ReactQueryDevtools initialIsOpen={false} />

// Log API responses
axios.interceptors.response.use(
  response => {
    console.log('API Response:', response);
    return response;
  }
);
```

### Common Commands

```powershell
# View Django logs
python manage.py runserver --verbosity 2

# View Celery task status
celery -A azure_advisor_reports inspect active

# Check Redis
redis-cli
> KEYS *

# Database queries
psql -U postgres -d azure_advisor
\dt  # List tables
\d+ reports_report  # Describe table
```

---

## 📞 Getting Help

### Internal Resources
- **Product Manager:** For feature clarification and priorities
- **Tech Lead:** For architecture decisions
- **DevOps:** For deployment and infrastructure issues
- **QA Team:** For testing strategies and bug reproduction

### When Stuck
1. Check this CLAUDE.md file
2. Review existing similar code in the project
3. Check project documentation in `/docs`
4. Search GitHub issues
5. Ask team in chat/email

### Useful Debugging Queries

```sql
-- Check recent reports
SELECT id, client_id, report_type, status, created_at 
FROM reports_report 
ORDER BY created_at DESC LIMIT 10;

-- Count reports by status
SELECT status, COUNT(*) 
FROM reports_report 
GROUP BY status;

-- Find large files
SELECT id, csv_file, 
       pg_size_pretty(pg_column_size(csv_file)) as size
FROM reports_report 
ORDER BY pg_column_size(csv_file) DESC 
LIMIT 10;
```

---

## 🎯 Quick Reference

### Essential Commands

```powershell
# Start all services
docker-compose up -d

# Backend
python manage.py runserver
python manage.py migrate
python manage.py createsuperuser
python manage.py test

# Celery
celery -A azure_advisor_reports worker -l info

# Frontend
npm start
npm test
npm run build

# Stop all
docker-compose down
```

### Key URLs (Development)

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api
- Admin Panel: http://localhost:8000/admin
- API Docs: http://localhost:8000/api/docs

### Important File Paths

```
Config files:
- .env                                    # Environment variables
- azure_advisor_reports/settings.py       # Django settings
- frontend/src/config.js                  # Frontend config

Templates:
- azure_advisor_reports/templates/        # Django templates
- frontend/src/components/                # React components

Tests:
- azure_advisor_reports/apps/*/tests/     # Backend tests
- frontend/src/__tests__/                 # Frontend tests
```

---

## ✅ Pre-Deployment Checklist

Before deploying to production:

- [ ] All tests passing (backend + frontend)
- [ ] Environment variables configured in Azure
- [ ] Database migrations run successfully
- [ ] Static files collected and uploaded to CDN
- [ ] Azure AD app registration completed
- [ ] SSL certificate installed
- [ ] Monitoring and logging configured
- [ ] Backup strategy implemented
- [ ] Load testing completed
- [ ] Security scan passed
- [ ] Documentation updated
- [ ] Rollback plan prepared

---

## 📝 Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-09-29 | Initial CLAUDE.md creation | Product Team |

---



**End of Document**

*This CLAUDE.md file should be kept updated as the project evolves. All developers are encouraged to contribute improvements and clarifications.*

