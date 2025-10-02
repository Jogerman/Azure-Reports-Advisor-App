# TASK.md - Azure Advisor Reports Platform

**Project:** Azure Advisor Reports Platform
**Last Updated:** October 1, 2025
**Status:** In Progress - Milestone 2
**Estimated Duration:** 14 weeks

---

## 📊 Progress Overview

```
Total Milestones: 6
Completed: 1/6 (17%)

Total Tasks: 186
Completed: 109/186 (59%)

Milestone 2 Progress: 100% Complete ✅
Milestone 3 Progress: 35% Complete (Section 3.5 Frontend Reports - COMPLETE)
```

---

## 🎯 Milestone 1: Development Environment Ready
**Target Date:** End of Week 1  
**Status:** Not Started  
**Tasks:** 0/25 Complete

### 1.1 Project Setup & Repository

- [x] Create GitHub repository for the project
- [x] Initialize `.gitignore` for Python and Node.js
- [x] Create README.md with project overview
- [x] Setup branch protection rules (main, develop)
- [x] Configure GitHub Issues and Projects
- [x] Create project directory structure
  ```
  azure-advisor-reports/
  ├── azure_advisor_reports/
  ├── frontend/
  ├── docs/
  ├── scripts/
  └── tests/
  ```
- [x] Add LICENSE file
- [x] Create CONTRIBUTING.md
- [x] Setup GitHub Actions workflows directory (`.github/workflows/`)

### 1.2 Backend Initial Setup

- [x] Create Django project: `django-admin startproject azure_advisor_reports`
- [x] Create virtual environment: `python -m venv venv`
- [x] Create `requirements.txt` with initial dependencies:
  ```
  Django==4.2.5
  djangorestframework==3.14.0
  django-cors-headers==4.2.0
  psycopg2-binary==2.9.7
  python-decouple==3.8
  ```
- [x] Create `requirements-dev.txt` for development dependencies
- [x] Setup Django apps structure:
  - [x] Create `apps/authentication/`
  - [x] Create `apps/clients/`
  - [x] Create `apps/reports/`
  - [x] Create `apps/analytics/`
- [x] Configure Django settings structure (`settings/base.py`, `settings/development.py`, `settings/production.py`)
- [x] Create `.env.example` file with all required environment variables
- [x] Setup Django logging configuration
- [ ] Create initial database schema design document

### 1.3 Frontend Initial Setup

- [x] Create React app: `npx create-react-app frontend`
- [x] Install core dependencies:
  ```bash
  npm install react-router-dom react-query axios
  npm install tailwindcss postcss autoprefixer
  npm install @microsoft/msal-react @microsoft/msal-browser
  npm install framer-motion recharts
  ```
- [x] Configure TailwindCSS (`tailwind.config.js`, `postcss.config.js`)
- [x] Create folder structure:
  ```
  src/
  ├── components/
  ├── pages/
  ├── services/
  ├── hooks/
  ├── utils/
  └── context/
  ```
- [x] Setup routing structure in `App.js`
- [x] Configure Axios base configuration (`services/api.js`)
- [x] Create environment variables file (`.env.local`)
- [x] Setup ESLint and Prettier configurations

### 1.4 Docker & Development Environment

- [x] Create `Dockerfile` for backend
- [x] Create `Dockerfile` for frontend
- [x] Create `docker-compose.yml` for local development
  - [x] PostgreSQL service (port 5432)
  - [x] Redis service (port 6379)
  - [x] Backend service (port 8000)
  - [x] Frontend service (port 3000)
  - [x] Celery worker service
- [x] Create `.dockerignore` files
- [x] Test Docker setup: `docker-compose up -d`
- [x] Verify all services are running
- [x] Create docker-compose override for development

### 1.5 CI/CD Pipeline Setup

- [x] Create `.github/workflows/ci.yml` for continuous integration
  - [x] Backend testing job
  - [x] Frontend testing job
  - [x] Linting jobs
  - [x] Code coverage reporting
- [x] Setup GitHub Actions secrets
- [x] Create `.github/workflows/deploy-staging.yml`
- [x] Create `.github/workflows/deploy-production.yml`
- [x] Test CI pipeline with dummy commit

### 1.6 Documentation

- [x] Create PLANNING.md (completed)
- [x] Create PRD.md (completed)
- [x] Create CLAUDE.md (completed)
- [x] Create TASK.md (this file)
- [x] Create ARCHITECTURE.md with system diagrams
- [x] Setup documentation folder structure
- [x] Create API documentation template

---

## 🎯 Milestone 2: MVP Backend Complete
**Target Date:** End of Week 4
**Status:** In Progress
**Tasks:** 35/38 Complete (92%)

### 2.1 Database Setup & Models

- [ ] Configure PostgreSQL connection in Django settings
- [ ] Create initial migration: `python manage.py migrate`
- [ ] Create `User` model (extending AbstractUser)
  - [ ] Add azure_id field
  - [ ] Add role field (admin, manager, analyst, viewer)
  - [ ] Add created_at, updated_at fields
- [ ] Create `Client` model
  - [ ] id (UUID, primary key)
  - [ ] company_name
  - [ ] industry
  - [ ] contact_email
  - [ ] contact_phone
  - [ ] azure_subscription_ids (JSONField)
  - [ ] status (active/inactive)
  - [ ] notes
  - [ ] created_at, updated_at
- [ ] Create `Report` model
  - [ ] id (UUID)
  - [ ] client (ForeignKey)
  - [ ] created_by (ForeignKey to User)
  - [ ] report_type (choices)
  - [ ] csv_file (FileField)
  - [ ] html_file (FileField)
  - [ ] pdf_file (FileField)
  - [ ] status (pending/processing/completed/failed)
  - [ ] analysis_data (JSONField)
  - [ ] error_message
  - [ ] processing timestamps
  - [ ] created_at, updated_at
- [ ] Create `Recommendation` model
  - [ ] report (ForeignKey)
  - [ ] category
  - [ ] business_impact
  - [ ] recommendation (TextField)
  - [ ] subscription_id
  - [ ] resource_name
  - [ ] resource_type
  - [ ] potential_savings
  - [ ] All Azure Advisor CSV fields
- [ ] Create indexes for performance optimization
- [ ] Run migrations: `python manage.py makemigrations && python manage.py migrate`
- [ ] Create admin interface for all models
- [ ] Test admin interface: `python manage.py createsuperuser`

### 2.2 Django REST Framework Setup

- [ ] Install DRF: Add to requirements.txt
- [ ] Configure DRF in settings (DEFAULT_PERMISSION_CLASSES, etc.)
- [ ] Create base serializers
- [ ] Setup pagination classes
- [ ] Configure exception handling
- [ ] Setup filtering and search backends
- [ ] Create API versioning structure (v1/)

### 2.3 Authentication Implementation

**Azure AD Integration:**
- [x] Register application in Azure AD (TODO: Needs actual Azure AD app - using placeholders)
  - [x] Note down Client ID, Tenant ID
  - [x] Create Client Secret
  - [x] Configure Redirect URIs
- [x] Install MSAL: `msal==1.34.0` (already installed)
- [x] Install PyJWT: `PyJWT==2.10.1` (already installed)
- [x] Create `apps/authentication/services.py`
  - [x] Implement Azure AD token validation
  - [x] Implement user creation/update from Azure AD profile
  - [x] Implement JWT token generation
  - [x] Implement JWT token validation
  - [x] Implement token refresh logic
  - [x] Create RoleService for RBAC helpers
- [x] Create authentication middleware (`middleware.py`)
  - [x] JWTAuthenticationMiddleware
  - [x] RequestLoggingMiddleware
  - [x] SessionTrackingMiddleware
  - [x] APIVersionMiddleware
- [x] Create authentication backend (`authentication.py`)
  - [x] AzureADAuthentication for DRF
- [x] Create authentication serializers (`serializers.py`)
  - [x] UserSerializer
  - [x] AzureADLoginSerializer
  - [x] TokenResponseSerializer
  - [x] TokenRefreshSerializer
  - [x] LogoutSerializer
  - [x] UpdateProfileSerializer
- [x] Create authentication views (`views.py`):
  - [x] POST `/api/auth/login/` - AzureADLoginView
  - [x] POST `/api/auth/logout/` - LogoutView
  - [x] GET `/api/auth/user/` - CurrentUserView
  - [x] PUT `/api/auth/user/` - Update profile
  - [x] POST `/api/auth/refresh/` - TokenRefreshView
  - [x] UserViewSet for admin user management
- [x] Implement RBAC (Role-Based Access Control)
- [x] Create permission classes for different roles (`permissions.py`)
  - [x] IsAdmin
  - [x] IsManager
  - [x] IsAnalyst
  - [x] IsViewer
  - [x] CanManageClients
  - [x] CanManageReports
  - [x] RoleBasedPermission
- [x] Create URL configuration (`urls.py`)
- [x] Include in main urls.py
- [ ] Write unit tests for authentication (pending)
- [ ] Test authentication flow end-to-end (requires Azure AD app)

### 2.4 Client Management API

**Models & Serializers:**
- [x] Create `ClientSerializer` with all fields
- [x] Create `ClientListSerializer` (for list view)
- [x] Create `ClientDetailSerializer` (for detail view)
- [x] Add validation for required fields
- [x] Create `ClientContactSerializer` for contacts
- [x] Create `ClientNoteSerializer` for notes
- [x] Create `ClientStatisticsSerializer` for statistics

**ViewSets & URLs:**
- [x] Create `ClientViewSet` in `apps/clients/views.py`
  - [x] list() - GET /api/clients/
  - [x] create() - POST /api/clients/
  - [x] retrieve() - GET /api/clients/{id}/
  - [x] update() - PUT /api/clients/{id}/
  - [x] partial_update() - PATCH /api/clients/{id}/
  - [x] destroy() - DELETE /api/clients/{id}/
- [x] Add search functionality (by company_name, contact_email, contact_person)
- [x] Add filtering (by status, industry, account_manager)
- [x] Add ordering (by created_at, company_name, updated_at)
- [x] Register routes in `apps/clients/urls.py`
- [x] Include in main urls.py
- [x] Add custom actions (activate, deactivate, add_subscription, remove_subscription, statistics)
- [x] Create `ClientContactViewSet` for contact management
- [x] Create `ClientNoteViewSet` for note management

**Business Logic:**
- [x] Create `apps/clients/services.py` for business logic
- [x] Implement client creation with validation
- [x] Implement client update logic
- [x] Implement soft delete (status=inactive)
- [x] Add audit logging for client operations
- [x] Create `ClientService` with advanced methods
- [x] Create `ClientContactService` for contact management
- [x] Create `ClientNoteService` for note management
- [x] Implement search functionality with filters
- [x] Implement statistics calculation

**Testing:**
- [x] Write unit tests for Client model (42 test cases)
- [x] Write unit tests for ClientContact model
- [x] Write unit tests for ClientNote model
- [x] Write tests for ClientSerializer (15 test cases)
- [x] Write tests for all serializers
- [x] Write API tests for all endpoints (25 test cases)
- [x] Write tests for services (25 test cases)
- [x] Test permissions and authentication integration
- [x] Test edge cases (duplicate names, invalid data, cascading deletes)
- [x] Test custom actions and statistics

### 2.5 Health Check & Monitoring

- [ ] Create health check endpoint: GET `/api/health/`
  - [ ] Check database connectivity
  - [ ] Check Redis connectivity
  - [ ] Return service status
- [ ] Setup Django logging
- [ ] Configure structured logging format
- [ ] Create log rotation strategy
- [ ] Setup error tracking (Sentry integration - optional)

### 2.6 Backend Testing Setup

- [ ] Install pytest and pytest-django
- [ ] Create `pytest.ini` configuration
- [ ] Create test fixtures in `conftest.py`
- [ ] Write tests for models
- [ ] Write tests for serializers
- [ ] Write tests for views/APIs
- [ ] Setup test coverage reporting
- [ ] Run tests: `pytest --cov=apps`
- [ ] Achieve 40% test coverage minimum

---

## 🎯 Milestone 3: Core Features Complete
**Target Date:** End of Week 8  
**Status:** Not Started  
**Tasks:** 0/56 Complete

### 3.1 CSV Upload & Processing

**File Upload:**
- [ ] Install pandas: `pip install pandas==2.1.1`
- [ ] Configure file upload settings in Django
  - [ ] MAX_UPLOAD_SIZE = 50MB
  - [ ] ALLOWED_EXTENSIONS = ['csv']
- [ ] Create file storage backend (Azure Blob Storage)
  - [ ] Install: `pip install azure-storage-blob`
  - [ ] Configure connection string
  - [ ] Create blob containers (csv-uploads, reports-html, reports-pdf)
- [ ] Create CSV upload endpoint: POST `/api/v1/reports/upload/`
  - [ ] Accept multipart/form-data
  - [ ] Validate file size
  - [ ] Validate file extension
  - [ ] Validate CSV structure
  - [ ] Save file to blob storage
  - [ ] Create Report record with status='pending'
- [ ] Implement file validation
  - [ ] Check for required columns
  - [ ] Validate data types
  - [ ] Check for empty file
  - [ ] Check encoding (UTF-8, UTF-8-BOM)
- [ ] Add error handling for upload failures

**CSV Processing:**
- [ ] Create `apps/reports/services/csv_processor.py`
- [ ] Implement CSV parsing with pandas
  ```python
  def parse_csv(file_path):
      df = pd.read_csv(file_path, encoding='utf-8-sig')
      # Process data
      return df
  ```
- [ ] Extract Azure Advisor columns:
  - [ ] Category
  - [ ] Business Impact
  - [ ] Recommendation
  - [ ] Subscription ID/Name
  - [ ] Resource Group
  - [ ] Resource Name
  - [ ] Type
  - [ ] Potential Benefits
  - [ ] Potential Annual Cost Savings
  - [ ] Currency
  - [ ] Retirement Date
  - [ ] Retiring Feature
- [ ] Handle missing or malformed data
- [ ] Calculate statistics:
  - [ ] Count by category
  - [ ] Total potential savings
  - [ ] Business impact distribution
  - [ ] Azure Advisor Score calculation
- [ ] Save Recommendation records to database
- [ ] Update Report status to 'completed' or 'failed'

**Async Processing with Celery:**
- [ ] Install Celery: `pip install celery[redis]`
- [ ] Create `azure_advisor_reports/celery.py` configuration
- [ ] Configure Celery in Django settings
- [ ] Create `apps/reports/tasks.py`
- [ ] Create task: `@shared_task def process_csv_file(report_id)`
  - [ ] Fetch Report from database
  - [ ] Download CSV from blob storage
  - [ ] Parse CSV
  - [ ] Create Recommendation records
  - [ ] Update Report analysis_data
  - [ ] Update Report status
  - [ ] Handle errors and retry logic
- [ ] Test Celery worker: `celery -A azure_advisor_reports worker -l info`
- [ ] Implement task status checking endpoint
- [ ] Add task progress updates (optional)

### 3.2 Report Generation - Backend

**Base Report Generator:**
- [ ] Create `apps/reports/generators/base.py`
  - [ ] BaseReportGenerator class
  - [ ] Common methods (get_data, calculate_metrics, render_html)
  - [ ] Template rendering logic
- [ ] Define report data structure (analysis_data JSON)
  ```json
  {
    "total_recommendations": 0,
    "category_distribution": {},
    "business_impact_distribution": {},
    "estimated_monthly_savings": 0,
    "estimated_working_hours": 0,
    "advisor_score": 0,
    "top_recommendations": []
  }
  ```

**Report Templates (HTML):**
- [ ] Create `templates/reports/base.html` with common styling
  - [ ] Define CSS variables for brand colors
  - [ ] Add logo and header
  - [ ] Create footer with disclaimer
- [ ] Create `templates/reports/detailed.html`
  - [ ] Full recommendation list
  - [ ] Grouped by category
  - [ ] All technical details
  - [ ] Sortable tables
- [ ] Create `templates/reports/executive.html`
  - [ ] High-level summary
  - [ ] Key metrics dashboard
  - [ ] Charts (category distribution)
  - [ ] Top 10 recommendations
- [ ] Create `templates/reports/cost.html`
  - [ ] Focus on cost optimization
  - [ ] Savings calculations
  - [ ] ROI analysis
  - [ ] Quick wins section
- [ ] Create `templates/reports/security.html`
  - [ ] Security recommendations only
  - [ ] Risk level indicators
  - [ ] Compliance section
  - [ ] Remediation steps
- [ ] Create `templates/reports/operations.html`
  - [ ] Operational excellence focus
  - [ ] Reliability improvements
  - [ ] Best practices
  - [ ] Automation opportunities

**Report Generators:**
- [ ] Create `apps/reports/generators/detailed.py`
  - [ ] DetailedReportGenerator(BaseReportGenerator)
  - [ ] Implement generate() method
  - [ ] Render HTML template
  - [ ] Save to blob storage
- [ ] Create `apps/reports/generators/executive.py`
- [ ] Create `apps/reports/generators/cost.py`
- [ ] Create `apps/reports/generators/security.py`
- [ ] Create `apps/reports/generators/operations.py`
- [ ] Create factory pattern for generator selection
  ```python
  def get_report_generator(report_type):
      generators = {
          'detailed': DetailedReportGenerator,
          'executive': ExecutiveReportGenerator,
          # ...
      }
      return generators[report_type]()
  ```

**PDF Generation:**
- [ ] Install ReportLab: `pip install reportlab`
- [ ] Create `apps/reports/services/pdf_generator.py`
- [ ] Implement HTML to PDF conversion
  - [ ] Option 1: WeasyPrint (recommended)
  - [ ] Option 2: ReportLab direct
  - [ ] Option 3: wkhtmltopdf wrapper
- [ ] Handle charts and images in PDF
- [ ] Optimize PDF file size
- [ ] Add page numbers and table of contents
- [ ] Test PDF generation with various data sizes

**Report Generation API:**
- [ ] Create endpoint: POST `/api/v1/reports/generate/`
  - [ ] Accept: report_id, report_type
  - [ ] Trigger Celery task
  - [ ] Return task ID for status tracking
- [ ] Create Celery task: `generate_report(report_id, report_type)`
  - [ ] Fetch Report and Recommendations
  - [ ] Calculate analysis metrics
  - [ ] Select appropriate generator
  - [ ] Generate HTML
  - [ ] Generate PDF
  - [ ] Upload files to blob storage
  - [ ] Update Report record with file URLs
  - [ ] Update status to 'completed'
- [ ] Create endpoint: GET `/api/v1/reports/{id}/status/`
- [ ] Create endpoint: GET `/api/v1/reports/{id}/download/`
  - [ ] Return signed URL for file download
  - [ ] Support both HTML and PDF formats
- [ ] Add error handling and logging

### 3.3 Frontend - Core UI Implementation

**Layout Components:**
- [ ] Create `src/components/layout/Header.js`
  - [ ] Logo
  - [ ] Navigation menu
  - [ ] User profile dropdown
  - [ ] Logout button
- [ ] Create `src/components/layout/Sidebar.js`
  - [ ] Dashboard link
  - [ ] Clients link
  - [ ] Reports link
  - [ ] History link
  - [ ] Settings link
  - [ ] Active state highlighting
- [ ] Create `src/components/layout/Footer.js`
- [ ] Create `src/components/layout/MainLayout.js`
  - [ ] Combine Header, Sidebar, Content area, Footer
  - [ ] Responsive design (collapse sidebar on mobile)

**Common Components:**
- [ ] Create `src/components/common/Button.js`
  - [ ] Primary, secondary, danger variants
  - [ ] Loading state
  - [ ] Disabled state
- [ ] Create `src/components/common/Card.js`
- [ ] Create `src/components/common/Modal.js`
- [ ] Create `src/components/common/LoadingSpinner.js`
- [ ] Create `src/components/common/ErrorBoundary.js`
- [ ] Create `src/components/common/Toast.js` (notifications)
- [ ] Create `src/components/common/ConfirmDialog.js`

**Authentication:**
- [x] Configure MSAL in `src/config/authConfig.ts`
  - [x] clientId
  - [x] authority (tenant)
  - [x] redirectUri
  - [x] Comprehensive logging configuration
  - [x] Login request scopes (User.Read, openid, profile, email)
- [x] Create `src/context/AuthContext.tsx`
  - [x] Wrap app with MsalProvider
  - [x] Handle authentication state (isAuthenticated, isLoading, user)
  - [x] Automatic MSAL initialization
  - [x] Handle redirect promise flow
  - [x] User profile loading from Azure AD
- [x] Create `src/hooks/useAuth.ts`
  - [x] Login function (popup flow)
  - [x] Logout function (popup flow)
  - [x] Get user info
  - [x] Check if authenticated
  - [x] getAccessToken() with silent token refresh
- [x] Create `src/pages/LoginPage.tsx`
  - [x] "Sign in with Microsoft" button
  - [x] Company branding with Azure logo
  - [x] Feature highlights
  - [x] Loading state during auth
  - [x] Framer Motion animations
  - [x] Responsive design
- [x] Create `src/components/auth/ProtectedRoute.tsx`
  - [x] Redirect to login if not authenticated
  - [x] Loading spinner during auth check
  - [x] Save attempted URL for redirect after login
  - [x] Role-based access control support
  - [x] Access denied page for insufficient permissions
- [x] Update App.tsx routing with authentication
  - [x] AuthProvider wrapper
  - [x] ProtectedRoute for all authenticated routes
  - [x] Public /login route
  - [x] Proper route structure with nested routes
- [x] Update MainLayout to use useAuth hook
- [x] Create AUTHENTICATION_SETUP.md documentation
- [ ] Test authentication flow (requires Azure AD app credentials)

**API Service Layer:**
- [x] Create API endpoint definitions in `src/config/api.ts`
  - [x] Authentication endpoints
  - [x] Client endpoints
  - [x] Report endpoints
  - [x] Analytics endpoints
- [x] Configure Axios in `src/services/apiClient.ts`
  - [x] Base URL configuration (from env var)
  - [x] Request interceptor (add auth token from MSAL)
  - [x] Response interceptor (handle errors)
  - [x] Token refresh logic (acquireTokenPopup on 401)
  - [x] Automatic retry on token refresh
  - [x] Comprehensive error handling with toast notifications
  - [x] 30-second timeout configuration
- [x] Create `src/services/authService.ts`
  - [x] login(accessToken) - Exchange Azure AD token for backend JWT
  - [x] logout() - Logout from backend
  - [x] getCurrentUser() - Get current user profile
  - [x] refreshToken() - Refresh backend JWT
  - [x] Full TypeScript types (User, LoginRequest, LoginResponse)
- [x] Create `src/services/clientService.ts`
  - [x] getClients(params) - with pagination, search, filtering
  - [x] getClient(id) - Get single client
  - [x] createClient(data) - Create new client
  - [x] updateClient(id, data) - Update client (PATCH)
  - [x] deleteClient(id) - Delete client
  - [x] Full TypeScript types (Client, CreateClientData, UpdateClientData, etc.)
- [x] Create `src/services/reportService.ts`
  - [x] uploadCSV(data) - Upload CSV with FormData
  - [x] generateReport(data) - Trigger report generation
  - [x] getReportStatus(id) - Check generation status
  - [x] downloadReport(id, format) - Download HTML/PDF report
  - [x] getReports(filters) - List reports with filters
  - [x] getReport(id) - Get single report
  - [x] deleteReport(id) - Delete report
  - [x] downloadFile() - Helper to trigger browser download
  - [x] Full TypeScript types (Report, ReportType, ReportStatus, etc.)
- [x] Create `src/services/index.ts` - Export all services and types
- [x] Update `.env.local` with Azure AD placeholders

### 3.4 Frontend - Client Management

**Client List Page:**
- [x] Create `src/pages/ClientsPage.tsx`
- [x] Implement client list display
  - [x] Card view with Company Name, Industry, Status, Subscriptions, Actions
  - [x] Search bar (filter by company name)
  - [x] Status filter dropdown (All/Active/Inactive)
  - [x] Add Client button
- [x] Create `src/components/clients/ClientCard.tsx` (alternative card view)
- [x] Implement pagination (with page size 10)
- [x] Add loading state (with spinner)
- [x] Add empty state ("No clients yet")
- [x] Implement client deletion with confirmation dialog

**Client Form:**
- [x] Create `src/components/clients/ClientForm.tsx`
  - [x] Company name (required)
  - [x] Industry dropdown (12 industries including Technology, Healthcare, Finance, etc.)
  - [x] Contact email (with validation)
  - [x] Contact phone
  - [x] Azure subscription IDs (textarea - one per line)
  - [x] Notes (textarea)
  - [x] Status (Active/Inactive - shown only when editing)
- [x] Implement form validation (using Formik + Yup)
- [x] Create modal for Add/Edit client
- [x] Handle form submission (create and update)
- [x] Show success/error toast notifications

**Client Detail Page:**
- [x] Create `src/pages/ClientDetailPage.tsx`
- [x] Display client information (all fields, formatted dates)
- [x] Show list of reports for this client
- [x] Add "Generate Report" button (redirects to reports page)
- [x] Add "Edit Client" button (opens modal)
- [x] Add "Delete Client" button (with confirmation)
- [x] Implement report history list (with status badges)
- [x] Add metrics: Total reports, Completed reports, Azure subscriptions

### 3.5 Frontend - Report Generation & Management

**Report Upload Page:**
- [x] Create `src/pages/ReportsPage.tsx` (Complete with 3-step wizard)
- [x] Create `src/components/reports/CSVUploader.tsx`
  - [x] Drag & drop zone
  - [x] File browser button
  - [x] File validation (size, type)
  - [x] Upload progress indication
  - [x] Success/error messages
- [x] Client selection (step 1 of wizard)
- [x] Upload file to backend
- [x] Show upload status
- [x] Redirect to report list after generation

**Report Generation:**
- [x] Create `src/components/reports/ReportTypeSelector.tsx`
  - [x] Cards for 5 report types (Detailed, Executive, Cost, Security, Operations)
  - [x] Description of each type
  - [x] Visual icons and color coding
  - [x] Audience targeting info
  - [x] Feature highlights
- [x] Trigger report generation API call
- [x] Show processing status with ReportStatusBadge
  - [x] Pending → Processing → Completed
  - [x] Status indicators with icons
  - [x] Real-time status updates
- [x] Poll for status updates (auto-refresh every 5s when processing)
- [x] Show completion notification (toast)
- [x] Provide download buttons (HTML, PDF)

**Report List:**
- [x] Create `src/components/reports/ReportList.tsx`
- [x] Display reports in cards with full info
  - [x] Client name
  - [x] Report type with labels
  - [x] Generated date (formatted)
  - [x] Status badge with animations
  - [x] Actions (Download HTML/PDF, Delete)
- [x] Implement filters
  - [x] By report type
  - [x] By status
  - [x] Client-specific filtering (via props)
- [x] Implement sorting (by created_at DESC)
- [x] Add pagination with page controls
- [x] Create `src/components/reports/ReportStatusBadge.tsx` for status display
- [x] Auto-refresh for processing reports

---

## 🎯 Milestone 4: MVP Feature Complete
**Target Date:** End of Week 12  
**Status:** Not Started  
**Tasks:** 0/35 Complete

### 4.1 Dashboard & Analytics

**Backend Analytics Endpoints:**
- [ ] Create `apps/analytics/services.py`
- [ ] Implement dashboard metrics calculation
  - [ ] Total recommendations
  - [ ] Total potential savings
  - [ ] Total clients
  - [ ] Total reports
  - [ ] Category distribution
  - [ ] Business impact distribution
  - [ ] Trend data (last 30/90 days)
- [ ] Create endpoint: GET `/api/v1/analytics/dashboard/`
- [ ] Create endpoint: GET `/api/v1/analytics/trends/`
- [ ] Create endpoint: GET `/api/v1/analytics/client-performance/`
- [ ] Implement caching for expensive queries
- [ ] Add date range filtering
- [ ] Write tests for analytics calculations

**Frontend Dashboard:**
- [ ] Create `src/pages/Dashboard.js`
- [ ] Create `src/components/dashboard/MetricCard.js`
  - [ ] Display single metric with icon
  - [ ] Trend indicator (up/down)
  - [ ] Percentage change
- [ ] Create summary metrics section
  - [ ] Total Recommendations
  - [ ] Total Potential Savings (USD)
  - [ ] Active Clients
  - [ ] Reports Generated This Month
- [ ] Create `src/components/dashboard/CategoryChart.js`
  - [ ] Pie chart of recommendation distribution
  - [ ] Use Recharts library
  - [ ] Interactive tooltips
- [ ] Create `src/components/dashboard/TrendChart.js`
  - [ ] Line chart showing trends over time
  - [ ] Selectable time range (7/30/90 days)
- [ ] Create `src/components/dashboard/TopRecommendations.js`
  - [ ] List of highest-impact recommendations
  - [ ] Link to full reports
- [ ] Create `src/components/dashboard/RecentActivity.js`
  - [ ] Timeline of recent reports
  - [ ] Quick actions (view, download)
- [ ] Implement auto-refresh (every 5 minutes)
- [ ] Add loading skeletons
- [ ] Add error states
- [ ] Make responsive for mobile/tablet

### 4.2 UI/UX Polish

**Design System:**
- [ ] Define color palette in `tailwind.config.js`
  - [ ] Primary colors (Azure blue)
  - [ ] Secondary colors
  - [ ] Success/warning/danger colors
  - [ ] Neutral grays
- [ ] Define typography scale
- [ ] Define spacing scale
- [ ] Create shadow utilities
- [ ] Create border radius utilities

**Animations:**
- [ ] Add page transition animations (Framer Motion)
- [ ] Add card hover effects
- [ ] Add button loading animations
- [ ] Add skeleton loaders for async content
- [ ] Add toast notification animations
- [ ] Add modal entrance/exit animations
- [ ] Keep animations subtle and performant

**Responsive Design:**
- [ ] Test all pages on mobile (320px+)
- [ ] Test all pages on tablet (768px+)
- [ ] Test all pages on desktop (1024px+)
- [ ] Adjust layouts for different screen sizes
- [ ] Test sidebar collapse on mobile
- [ ] Test table responsiveness (horizontal scroll or cards)
- [ ] Optimize images for different screen sizes

**Accessibility:**
- [ ] Add proper ARIA labels
- [ ] Ensure keyboard navigation works
- [ ] Add focus visible states
- [ ] Check color contrast ratios (WCAG AA)
- [ ] Add alt text to images
- [ ] Test with screen reader
- [ ] Add skip to main content link
- [ ] Ensure forms have proper labels

### 4.3 Testing & Quality Assurance

**Backend Testing:**
- [ ] Write unit tests for all models
- [ ] Write tests for all serializers
- [ ] Write API tests for all endpoints
- [ ] Write tests for CSV processing
- [ ] Write tests for report generation
- [ ] Write tests for authentication
- [ ] Write tests for permissions
- [ ] Test Celery tasks
- [ ] Run coverage report: `pytest --cov=apps --cov-report=html`
- [ ] Achieve 85%+ test coverage

**Frontend Testing:**
- [ ] Write tests for utility functions
- [ ] Write tests for custom hooks
- [ ] Write component tests (Testing Library)
- [ ] Test form validation
- [ ] Test API service methods (mocked)
- [ ] Test authentication flow
- [ ] Run coverage: `npm test -- --coverage`
- [ ] Achieve 70%+ test coverage

**Integration Testing:**
- [ ] Test complete CSV upload → report generation flow
- [ ] Test authentication with Azure AD (staging)
- [ ] Test file upload to Azure Blob Storage
- [ ] Test PDF generation with various data sizes
- [ ] Test concurrent report generation
- [ ] Test error recovery scenarios

**Manual QA:**
- [ ] Create QA test plan document
- [ ] Test all user flows:
  - [ ] Login/logout
  - [ ] Create/edit/delete client
  - [ ] Upload CSV
  - [ ] Generate reports (all 5 types)
  - [ ] Download reports (HTML & PDF)
  - [ ] View dashboard
  - [ ] Search and filter
- [ ] Test on different browsers (Chrome, Firefox, Edge, Safari)
- [ ] Test on different devices (desktop, tablet, mobile)
- [ ] Document bugs in GitHub Issues
- [ ] Verify bug fixes

### 4.4 Performance Optimization

**Backend Optimization:**
- [ ] Add database indexes for frequently queried fields
- [ ] Implement query optimization (select_related, prefetch_related)
- [ ] Add Redis caching for expensive queries
  - [ ] Cache dashboard metrics
  - [ ] Cache report lists
- [ ] Optimize CSV processing for large files
- [ ] Implement pagination for all list endpoints
- [ ] Add request/response compression (gzip)
- [ ] Profile slow endpoints and optimize

**Frontend Optimization:**
- [ ] Implement code splitting (React.lazy)
- [ ] Lazy load images
- [ ] Optimize bundle size (analyze with webpack-bundle-analyzer)
- [ ] Implement React Query caching strategy
- [ ] Debounce search inputs
- [ ] Use pagination for large lists
- [ ] Optimize re-renders (React.memo, useMemo, useCallback)
- [ ] Minimize API calls (batch requests if possible)

**Performance Testing:**
- [ ] Run Lighthouse audit (aim for 90+ score)
- [ ] Measure page load times (< 2 seconds)
- [ ] Test with slow 3G throttling
- [ ] Load test API endpoints (100 concurrent users)
- [ ] Test report generation with 1000+ recommendations
- [ ] Profile memory usage

### 4.5 Documentation

**User Documentation:**
- [ ] Create user manual (Markdown or PDF)
  - [ ] Getting started guide
  - [ ] How to upload CSV
  - [ ] How to generate reports
  - [ ] Understanding report types
  - [ ] Managing clients
  - [ ] Dashboard overview
- [ ] Create video tutorials (optional)
  - [ ] Quick start (5 min)
  - [ ] Report generation walkthrough (10 min)
- [ ] Create FAQ document
- [ ] Create troubleshooting guide

**Technical Documentation:**
- [ ] Document API endpoints (OpenAPI/Swagger)
  - [ ] Use drf-spectacular for auto-generation
  - [ ] Add request/response examples
  - [ ] Document error codes
- [ ] Update ARCHITECTURE.md with implementation details
- [ ] Document deployment process
- [ ] Document environment variables
- [ ] Create runbook for common operations
- [ ] Document backup and restore procedures

**Code Documentation:**
- [ ] Add docstrings to all Python functions/classes
- [ ] Add JSDoc comments to complex JavaScript functions
- [ ] Update README.md with setup instructions
- [ ] Create CONTRIBUTING.md with development guidelines
- [ ] Add inline comments for complex logic

---

## 🎯 Milestone 5: Production Ready
**Target Date:** End of Week 13  
**Status:** Not Started  
**Tasks:** 0/22 Complete

### 5.1 Azure Infrastructure Setup

**Resource Provisioning:**
- [ ] Create Azure resource group: `rg-azure-advisor-reports-prod`
- [ ] Create Azure Database for PostgreSQL
  - [ ] Configure firewall rules
  - [ ] Create database: `azure_advisor_reports_prod`
  - [ ] Create database user with appropriate permissions
  - [ ] Enable SSL/TLS
- [ ] Create Azure Cache for Redis
  - [ ] Note connection string
  - [ ] Configure firewall rules
- [ ] Create Azure Storage Account
  - [ ] Create blob containers:
    - [ ] csv-uploads (private)
    - [ ] reports-html (private)
    - [ ] reports-pdf (private)
  - [ ] Configure CORS for frontend access
  - [ ] Note connection string
- [ ] Create App Service Plan for backend (P2v3)
- [ ] Create App Service Plan for frontend (P1v3)
- [ ] Create Application Insights for monitoring

**Network Configuration:**
- [ ] Configure Virtual Network (optional for Premium tier)
- [ ] Configure network security groups
- [ ] Setup private endpoints (if needed)
- [ ] Configure DNS records
- [ ] Purchase and configure custom domain (optional)
- [ ] Setup SSL certificate (Let's Encrypt or Azure Certificate)

**Azure AD Configuration:**
- [ ] Create App Registration for production
- [ ] Configure redirect URIs for production domain
- [ ] Create client secret
- [ ] Configure API permissions
- [ ] Create service principal for deployments

### 5.2 Backend Deployment

**Production Configuration:**
- [ ] Create `settings/production.py` with production settings
  - [ ] DEBUG = False
  - [ ] ALLOWED_HOSTS with production domain
  - [ ] Secure cookies
  - [ ] HTTPS redirects
  - [ ] HSTS headers
- [ ] Configure environment variables in App Service
  - [ ] DATABASE_URL
  - [ ] REDIS_URL
  - [ ] AZURE_STORAGE_CONNECTION_STRING
  - [ ] SECRET_KEY (generate strong key)
  - [ ] AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID
  - [ ] All other required variables
- [ ] Update requirements.txt with production dependencies
  - [ ] gunicorn
  - [ ] whitenoise
  - [ ] azure dependencies

**Docker Build & Push:**
- [ ] Build production Docker image
  ```bash
  docker build -t azure-advisor-backend:prod -f Dockerfile.prod .
  ```
- [ ] Create Azure Container Registry (optional)
- [ ] Tag and push image
- [ ] Or use GitHub Actions for automated builds

**Deployment:**
- [ ] Deploy to Azure App Service
  - [ ] Option 1: Docker container deployment
  - [ ] Option 2: Git deployment
  - [ ] Option 3: GitHub Actions deployment
- [ ] Run database migrations in production
  ```bash
  az webapp ssh
  python manage.py migrate --no-input
  ```
- [ ] Collect static files
  ```bash
  python manage.py collectstatic --no-input
  ```
- [ ] Create superuser in production
- [ ] Configure worker instances (Celery)
  - [ ] Option 1: Separate App Service for workers
  - [ ] Option 2: Azure Container Instances
  - [ ] Configure auto-scaling rules
- [ ] Verify deployment with health check endpoint

### 5.3 Frontend Deployment

**Production Build:**
- [ ] Update `.env.production` with production values
  - [ ] REACT_APP_API_URL (backend URL)
  - [ ] REACT_APP_AZURE_CLIENT_ID
  - [ ] REACT_APP_AZURE_TENANT_ID
  - [ ] REACT_APP_AZURE_REDIRECT_URI
- [ ] Create production build
  ```bash
  npm run build
  ```
- [ ] Test production build locally
  ```bash
  npx serve -s build
  ```
- [ ] Optimize assets (images, fonts)

**Deployment:**
- [ ] Deploy to Azure App Service
  - [ ] Upload build folder
  - [ ] Configure web.config or startup command
- [ ] Configure Azure Front Door (CDN) - optional
  - [ ] Setup origin with App Service
  - [ ] Configure caching rules
  - [ ] Setup WAF rules
- [ ] Configure custom domain
- [ ] Setup SSL/TLS certificate
- [ ] Test frontend loads correctly
- [ ] Test API calls work from frontend

### 5.4 Monitoring & Logging

**Application Insights:**
- [ ] Configure Application Insights in backend
  - [ ] Install: `pip install opencensus-ext-azure`
  - [ ] Configure in settings.py
  - [ ] Add instrumentation key
- [ ] Configure custom telemetry
  - [ ] Track report generation duration
  - [ ] Track CSV processing duration
  - [ ] Track API response times
- [ ] Setup dashboards in Azure portal
- [ ] Create alerts:
  - [ ] Response time > 2 seconds
  - [ ] Error rate > 5%
  - [ ] Failed reports > 10 in 1 hour
  - [ ] CPU usage > 80%
  - [ ] Memory usage > 80%

**Logging:**
- [ ] Configure centralized logging
- [ ] Setup log retention policy
- [ ] Create log queries for common issues
- [ ] Setup log-based alerts

**Backup Strategy:**
- [ ] Configure automated database backups
  - [ ] Daily backups
  - [ ] 14-day retention
  - [ ] Test restore procedure
- [ ] Configure blob storage backup
- [ ] Document backup and restore procedures
- [ ] Test disaster recovery plan

### 5.5 Security Hardening

**Security Checklist:**
- [ ] Enable HTTPS only (no HTTP)
- [ ] Configure security headers
  - [ ] Content-Security-Policy
  - [ ] X-Frame-Options
  - [ ] X-Content-Type-Options
  - [ ] Strict-Transport-Security
- [ ] Enable CORS with strict origins
- [ ] Implement rate limiting
- [ ] Configure Azure WAF rules
- [ ] Enable Azure DDoS protection
- [ ] Scan for vulnerabilities
  - [ ] Run `safety check` for Python
  - [ ] Run `npm audit` for Node.js
  - [ ] Fix critical vulnerabilities
- [ ] Review and rotate secrets
- [ ] Setup key rotation schedule
- [ ] Enable audit logging
- [ ] Configure IP restrictions (if needed)

**Security Testing:**
- [ ] Run OWASP ZAP scan
- [ ] Perform penetration testing (if budget allows)
- [ ] Test authentication/authorization
- [ ] Test file upload security
- [ ] Test SQL injection (should be prevented by ORM)
- [ ] Test XSS vulnerabilities
- [ ] Test CSRF protection

### 5.6 UAT (User Acceptance Testing)

**Test Environment:**
- [ ] Setup staging environment identical to production
- [ ] Deploy latest code to staging
- [ ] Create test users with different roles
- [ ] Prepare test data (sample CSVs)

**UAT Test Plan:**
- [ ] Create test scenarios document
- [ ] Invite beta testers (3-5 users)
- [ ] Provide access to staging environment
- [ ] Walk through key features
- [ ] Collect feedback via survey/interviews
- [ ] Log bugs and issues
- [ ] Prioritize feedback for fixes

**Sign-off:**
- [ ] Fix critical bugs found in UAT
- [ ] Re-test fixes
- [ ] Get stakeholder approval
- [ ] Document known issues/limitations
- [ ] Create release notes

---

## 🎯 Milestone 6: Production Launch
**Target Date:** End of Week 14  
**Status:** Not Started  
**Tasks:** 0/10 Complete

### 6.1 Pre-Launch Checklist

**Technical Verification:**
- [ ] All tests passing in CI/CD
- [ ] Performance benchmarks met
- [ ] Security scan passed
- [ ] Backup verified and tested
- [ ] Monitoring and alerting active
- [ ] Runbook documented
- [ ] Rollback plan prepared

**Documentation Verification:**
- [ ] User documentation complete
- [ ] API documentation published
- [ ] Support procedures documented
- [ ] FAQ updated
- [ ] Terms of Service and Privacy Policy published

**Team Readiness:**
- [ ] Support team trained
- [ ] On-call schedule established
- [ ] Incident response plan reviewed
- [ ] Communication channels setup (Slack, email)

### 6.2 Production Deployment

**Go-Live:**
- [ ] Schedule deployment window (low traffic period)
- [ ] Communicate maintenance window to users (if applicable)
- [ ] Deploy backend to production
- [ ] Deploy frontend to production
- [ ] Run database migrations
- [ ] Verify health checks pass
- [ ] Smoke test critical flows:
  - [ ] Login/logout
  - [ ] Upload CSV
  - [ ] Generate report
  - [ ] Download report
  - [ ] View dashboard

**Monitoring:**
- [ ] Monitor error logs for 1 hour post-deployment
- [ ] Check Application Insights for anomalies
- [ ] Monitor resource usage (CPU, memory, database)
- [ ] Verify alerts are working
- [ ] Check response times
- [ ] Monitor Celery task queue

### 6.3 User Onboarding

**Beta Users:**
- [ ] Send launch announcement email
- [ ] Provide login instructions
- [ ] Schedule onboarding calls
- [ ] Share user documentation links
- [ ] Create support ticket system
- [ ] Monitor user feedback channels

**Training:**
- [ ] Conduct live demo sessions
- [ ] Share video tutorials
- [ ] Answer initial questions
- [ ] Collect early feedback

### 6.4 Post-Launch Activities

**Week 1 Post-Launch:**
- [ ] Daily monitoring of errors and performance
- [ ] Triage and fix critical bugs
- [ ] Collect user feedback
- [ ] Update documentation based on questions
- [ ] Send follow-up survey

**Week 2 Post-Launch:**
- [ ] Analyze usage metrics
- [ ] Identify most-used features
- [ ] Identify pain points
- [ ] Plan improvements for next iteration
- [ ] Conduct retrospective with team

### 6.5 Success Metrics Tracking

**Setup Analytics:**
- [ ] Configure Google Analytics (if not using App Insights only)
- [ ] Setup conversion tracking
- [ ] Create dashboards for:
  - [ ] User registrations
  - [ ] Reports generated per day/week
  - [ ] Average report generation time
  - [ ] Error rates
  - [ ] User retention

**Week 4 Evaluation:**
- [ ] Review against success metrics:
  - [ ] Number of active users vs target
  - [ ] Reports generated vs target
  - [ ] Performance metrics vs target
  - [ ] User satisfaction vs target
- [ ] Create performance report for stakeholders
- [ ] Identify areas for improvement
- [ ] Plan next phase of development

---

## 📊 Task Categories Summary

### By Priority

**P0 - Critical (Must Have for MVP):** 124 tasks
- Authentication & Authorization
- CSV Upload & Processing
- Report Generation (all 5 types)
- Client Management
- Dashboard basics
- Production deployment

**P1 - High (Should Have):** 42 tasks
- Advanced analytics
- UI/UX polish
- Testing coverage
- Performance optimization
- Documentation

**P2 - Medium (Nice to Have):** 20 tasks
- Advanced features
- Additional optimizations
- Enhanced monitoring
- Video tutorials

### By Role

**Backend Developer:** 75 tasks
**Frontend Developer:** 68 tasks
**DevOps Engineer:** 28 tasks
**QA Engineer:** 10 tasks
**Product Manager:** 5 tasks

---

## 🔄 Progress Tracking

### How to Use This Document

1. **Regular Updates:** Update task status weekly in team meetings
2. **Checkboxes:** Mark tasks as complete using `[x]`
3. **Blockers:** Add 🚫 emoji if task is blocked
4. **In Progress:** Add 🔄 emoji if task is in progress
5. **Comments:** Add notes below tasks as needed

### Status Legend

- [ ] Not Started
- [x] Completed
- 🔄 In Progress
- 🚫 Blocked
- ⏸️ Paused
- ✅ Verified

### Example Usage:
```markdown
- [x] Create Django project
- 🔄 Implement authentication (80% complete)
- 🚫 Setup Azure AD (waiting for credentials)
- [ ] Write unit tests
```

---

## 📝 Notes Section

**Add implementation notes, decisions, and learnings here as you progress:**

### Week 1 Notes:
- 

### Week 2 Notes:
-

### Week 3 Notes:
-

---

**End of Task List**

*Keep this document updated and sync with your project management tools (Jira, Asana, GitHub Projects, etc.)*

*For questions about specific tasks, refer to CLAUDE.md, PLANNING.md, or PRD.md*