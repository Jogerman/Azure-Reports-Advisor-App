# Windows Development Setup Guide

**Azure Advisor Reports Platform**
**Last Updated:** September 29, 2025

---

## 🏁 Quick Start (TL;DR)

```powershell
# 1. Run setup script
.\scripts\setup-development.ps1

# 2. Configure environment
# Edit .env file with your Azure AD credentials

# 3. Start Docker Desktop

# 4. Start development stack
.\start-dev-stack.ps1

# 5. Access application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000/admin
```

---

## 📋 Prerequisites

### Required Software

| Software | Version | Download Link |
|----------|---------|---------------|
| **Python** | 3.8+ (3.11+ recommended) | https://python.org/downloads |
| **Node.js** | 18+ (LTS recommended) | https://nodejs.org |
| **Git** | Latest | https://git-scm.com/download/win |
| **Docker Desktop** | Latest | https://docker.com/products/docker-desktop |
| **Visual Studio Code** | Latest (optional) | https://code.visualstudio.com |

### Verify Installation

```powershell
# Check versions
python --version    # Should be 3.8+
node --version      # Should be v18+
npm --version       # Should be 8+
docker --version    # Should be 20+
git --version       # Any recent version
```

---

## 🛠️ Manual Setup Steps

### 1. Clone Repository

```powershell
git clone <repository-url>
cd azure-advisor-reports
```

### 2. Backend Setup (Django)

```powershell
# Navigate to backend directory
cd azure_advisor_reports

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Return to project root
cd ..
```

### 3. Frontend Setup (React)

```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Return to project root
cd ..
```

### 4. Environment Configuration

```powershell
# Copy environment template
Copy-Item .env.example .env

# Edit .env file with your values
notepad .env
```

**Required Environment Variables:**

```bash
# Django
SECRET_KEY=your-super-secret-django-key-here
DEBUG=True

# Database (using Docker)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/azure_advisor_reports

# Redis (using Docker)
REDIS_URL=redis://localhost:6379/0

# Azure AD (get from Azure portal)
AZURE_CLIENT_ID=your-azure-ad-client-id
AZURE_CLIENT_SECRET=your-azure-ad-client-secret
AZURE_TENANT_ID=your-azure-tenant-id
AZURE_REDIRECT_URI=http://localhost:3000

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### 5. Start Docker Services

```powershell
# Start Docker Desktop first, then:
docker-compose up -d postgres redis

# Wait for services to start
Start-Sleep -Seconds 15
```

### 6. Initialize Database

```powershell
cd azure_advisor_reports
.\venv\Scripts\Activate.ps1

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

cd ..
```

---

## 🚀 Running the Application

### Option 1: Individual Services

**Terminal 1 - Backend:**
```powershell
cd azure_advisor_reports
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm start
```

**Terminal 3 - Celery Worker:**
```powershell
cd azure_advisor_reports
.\venv\Scripts\Activate.ps1
celery -A azure_advisor_reports worker -l info
```

### Option 2: Full Stack Script

```powershell
# Run the setup script first (one time)
.\scripts\setup-development.ps1

# Then start the full development stack
.\start-dev-stack.ps1
```

### Access Points

- **Frontend Application:** http://localhost:3000
- **Backend API:** http://localhost:8000/api/v1
- **Django Admin:** http://localhost:8000/admin
- **API Documentation:** http://localhost:8000/api/docs (when available)

---

## 🐛 Troubleshooting

### Common Issues

#### 1. PowerShell Execution Policy

**Error:** "cannot be loaded because running scripts is disabled"

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 2. Python Not Found

**Error:** "'python' is not recognized as an internal or external command"

**Solutions:**
- Ensure Python is in PATH during installation
- Use `py` instead of `python`
- Restart terminal after installation

#### 3. Docker Issues

**Error:** "error during connect: Get"

**Solutions:**
- Start Docker Desktop
- Ensure Docker is running in Windows containers mode (or Linux mode)
- Check Docker Desktop settings

#### 4. Port Already in Use

**Error:** "Port 3000 is already in use"

**Solutions:**
```powershell
# Find and kill process using port
netstat -ano | findstr :3000
taskkill /PID <process-id> /F

# Or use different port
$env:PORT = "3001"
npm start
```

#### 5. Django Database Connection

**Error:** "django.db.utils.OperationalError: connection to server"

**Solutions:**
```powershell
# Ensure PostgreSQL is running
docker-compose ps postgres

# Check database connection
docker-compose exec postgres psql -U postgres -d azure_advisor_reports -c "\dt"

# Restart database service
docker-compose restart postgres
```

#### 6. NPM Install Issues

**Error:** Various npm errors

**Solutions:**
```powershell
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
Remove-Item node_modules -Recurse -Force
Remove-Item package-lock.json -Force
npm install

# Use yarn as alternative
yarn install
```

---

## 🧪 Testing Setup

### Run Validation Script

```powershell
.\scripts\validate-environment.ps1
```

This script checks:
- ✅ All required software is installed
- ✅ Project structure is correct
- ✅ Environment variables are configured
- ✅ Dependencies are installed
- ✅ Services can connect

### Manual Testing

**Backend Health Check:**
```powershell
# Test Django
curl http://localhost:8000/api/health/

# Test admin access
curl http://localhost:8000/admin/
```

**Frontend Health Check:**
```powershell
# Test React app
curl http://localhost:3000
```

**Database Connection:**
```powershell
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d azure_advisor_reports

# List tables
\dt

# Exit PostgreSQL
\q
```

---

## 🔧 Development Tools

### Recommended VS Code Extensions

```json
{
    "recommendations": [
        "ms-python.python",
        "ms-python.flake8",
        "ms-python.black-formatter",
        "bradlc.vscode-tailwindcss",
        "esbenp.prettier-vscode",
        "ms-vscode.vscode-typescript-next",
        "ms-vscode-remote.remote-containers"
    ]
}
```

### PowerShell Profile Setup

Add to your PowerShell profile (`$PROFILE`):

```powershell
# Azure Advisor Reports shortcuts
function Start-AzureAdvisor {
    Set-Location "C:\path\to\azure-advisor-reports"
    .\start-dev-stack.ps1
}

function Stop-AzureAdvisor {
    docker-compose down
}

# Aliases
Set-Alias -Name azstart -Value Start-AzureAdvisor
Set-Alias -Name azstop -Value Stop-AzureAdvisor
```

### Git Configuration

```powershell
# Configure Git for Windows
git config --global core.autocrlf true
git config --global core.editor "code --wait"
git config --global user.name "Your Name"
git config --global user.email "your.email@company.com"
```

---

## 🔐 Azure AD Setup

### 1. Register Application

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to "Azure Active Directory" > "App registrations"
3. Click "New registration"
4. Configure:
   - **Name:** Azure Advisor Reports Platform
   - **Supported account types:** Single tenant
   - **Redirect URI:** Web - `http://localhost:3000`

### 2. Configure Authentication

1. In your app registration, go to "Authentication"
2. Add redirect URIs:
   - `http://localhost:3000`
   - `http://localhost:3000/login`
3. Enable "ID tokens" under implicit grant
4. Set logout URL: `http://localhost:3000/logout`

### 3. Create Client Secret

1. Go to "Certificates & secrets"
2. Click "New client secret"
3. Set description and expiry
4. **Copy the secret value immediately** (you can't see it again)

### 4. API Permissions

1. Go to "API permissions"
2. Add permissions:
   - Microsoft Graph > Delegated > User.Read
   - Microsoft Graph > Delegated > email
   - Microsoft Graph > Delegated > openid
   - Microsoft Graph > Delegated > profile

### 5. Update Environment

```bash
AZURE_CLIENT_ID=your-app-registration-client-id
AZURE_CLIENT_SECRET=your-client-secret-value
AZURE_TENANT_ID=your-tenant-id
```

---

## 📊 Performance Optimization

### Windows-Specific Optimizations

**Docker Performance:**
```yaml
# In docker-compose.yml, add for better Windows performance
volumes:
  - type: bind
    source: ./azure_advisor_reports
    target: /app
    consistency: delegated
```

**Node.js Performance:**
```bash
# In .env.local (frontend)
CHOKIDAR_USEPOLLING=false  # Better file watching
FAST_REFRESH=true          # Faster hot reloading
```

**Python Performance:**
```bash
# In .env
PYTHONUNBUFFERED=1         # Better console output
PYTHONDONTWRITEBYTECODE=1  # Faster imports
```

---

## 🚨 Security Considerations

### Development Security

```powershell
# Ensure .env is not committed
git update-index --assume-unchanged .env

# Check for secrets in code
git secrets --register-aws
git secrets --install
git secrets --scan
```

### Windows Firewall

Docker and the development servers might trigger Windows Firewall prompts:
- ✅ Allow Docker Desktop
- ✅ Allow Python (Django development server)
- ✅ Allow Node.js (React development server)

---

## 🆘 Getting Help

### Log Files

**Django Logs:**
```
azure_advisor_reports/logs/django.log
```

**Docker Logs:**
```powershell
docker-compose logs postgres
docker-compose logs redis
docker-compose logs backend
```

**NPM Logs:**
```
frontend/npm-debug.log
```

### Support Channels

1. **Team Chat:** #azure-advisor-reports
2. **Email:** development-team@company.com
3. **Issues:** GitHub Issues in the repository

### Useful Commands

```powershell
# Check all services status
docker-compose ps

# View logs
docker-compose logs -f backend

# Restart specific service
docker-compose restart postgres

# Clean restart
docker-compose down
docker-compose up -d

# Django shell
cd azure_advisor_reports
.\venv\Scripts\Activate.ps1
python manage.py shell

# Database shell
python manage.py dbshell
```

---

## 📝 Next Steps

After successful setup:

1. **Development Workflow:**
   - Create feature branch: `git checkout -b feature/your-feature`
   - Make changes
   - Test locally
   - Create pull request

2. **Testing:**
   - Run backend tests: `pytest`
   - Run frontend tests: `npm test`
   - Run integration tests: `npm run test:e2e`

3. **Deployment:**
   - See `DEPLOYMENT.md` for production deployment
   - Use staging environment for testing

---

**Need help?** Contact the development team or check the troubleshooting section above.

**Found a bug?** Please create an issue in the GitHub repository with detailed steps to reproduce.