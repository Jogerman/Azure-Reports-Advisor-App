# Windows 11 Development Setup Guide
## Azure Advisor Reports Platform

**Last Updated:** September 30, 2025
**Platform:** Windows 11 Pro (64-bit)
**Target Audience:** Developers setting up local development environment

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Starting Development Environment](#starting-development-environment)
4. [Service Management](#service-management)
5. [Troubleshooting](#troubleshooting)
6. [Windows-Specific Considerations](#windows-specific-considerations)
7. [PowerShell Scripts](#powershell-scripts)
8. [Performance Tips](#performance-tips)

---

## Prerequisites

### Required Software

| Software | Version | Installation Method | Verification Command |
|----------|---------|---------------------|---------------------|
| **Python** | 3.11+ | [python.org](https://python.org) or Microsoft Store | `python --version` |
| **Node.js** | 18+ LTS | [nodejs.org](https://nodejs.org) | `node --version` |
| **Docker Desktop** | Latest | [docker.com](https://docker.com) | `docker --version` |
| **Git** | 2.40+ | [git-scm.com](https://git-scm.com) | `git --version` |
| **PowerShell** | 7.x | [Microsoft Docs](https://docs.microsoft.com/powershell) | `$PSVersionTable.PSVersion` |

### Optional But Recommended

- **Windows Terminal**: Modern terminal with tabs and theming
- **Visual Studio Code**: Primary code editor with extensions
- **Azure CLI**: For cloud resource management
- **PostgreSQL Client**: For database debugging (psql, pgAdmin, Azure Data Studio)
- **Redis CLI** or **RedisInsight**: For cache debugging

### Docker Desktop Configuration

**IMPORTANT**: Docker Desktop must use WSL2 backend for optimal performance.

1. Open Docker Desktop Settings
2. Go to **General**
3. Enable: **Use the WSL 2 based engine**
4. Go to **Resources** → **WSL Integration**
5. Enable integration with your WSL distro (if using WSL)
6. Apply & Restart

**Resource Allocation (Recommended):**
- **Memory**: 4 GB minimum, 8 GB recommended
- **CPUs**: 2 minimum, 4 recommended
- **Disk**: 20 GB minimum

---

## Initial Setup

### Step 1: Clone Repository

```powershell
# Open PowerShell or Windows Terminal
cd D:\Code  # Or your preferred development directory
git clone <repository-url> "Azure Reports"
cd "Azure Reports"
```

### Step 2: Backend Setup

```powershell
# Navigate to backend directory
cd azure_advisor_reports

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Frontend Setup

```powershell
# Open NEW terminal/tab (keep backend terminal open)
cd "D:\Code\Azure Reports\frontend"

# Install dependencies
npm install

# This may take 5-10 minutes
```

### Step 4: Environment Configuration

```powershell
# Return to project root
cd "D:\Code\Azure Reports"

# Copy environment template
Copy-Item .env.example .env

# Edit .env file with your settings
notepad .env  # or code .env (VS Code)
```

**Minimum Required Configuration:**
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/azure_advisor_reports
REDIS_URL=redis://localhost:6379/0
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

**Generate Strong Secret Key:**
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Step 5: Start Docker Services

```powershell
# From project root
docker-compose up -d postgres redis

# Verify containers are running
docker-compose ps

# Expected output:
# NAME                      STATUS
# azure-advisor-postgres    Up (healthy)
# azure-advisor-redis       Up (healthy)
```

### Step 6: Run Database Migrations

```powershell
cd azure_advisor_reports
.\venv\Scripts\Activate.ps1
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser
```

### Step 7: Verify Installation

```powershell
# Test Django configuration
python manage.py check

# Test health endpoint (in another terminal after starting server)
curl http://localhost:8000/api/health/
```

---

## Starting Development Environment

### Quick Start (All Services)

Create a PowerShell script `start-dev.ps1`:

```powershell
# Start Docker services
Write-Host "Starting Docker services..." -ForegroundColor Cyan
docker-compose up -d postgres redis

# Wait for services to be healthy
Start-Sleep -Seconds 5

# Start backend in background
Write-Host "Starting Django backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'D:\Code\Azure Reports\azure_advisor_reports'; .\venv\Scripts\Activate.ps1; python manage.py runserver"

# Start frontend in background
Write-Host "Starting React frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'D:\Code\Azure Reports\frontend'; npm start"

# Start Celery worker
Write-Host "Starting Celery worker..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'D:\Code\Azure Reports'; .\scripts\start-celery.ps1"

Write-Host "`nAll services starting..." -ForegroundColor Green
Write-Host "Frontend:  http://localhost:3000" -ForegroundColor Yellow
Write-Host "Backend:   http://localhost:8000" -ForegroundColor Yellow
Write-Host "Admin:     http://localhost:8000/admin" -ForegroundColor Yellow
Write-Host "Health:    http://localhost:8000/api/health/" -ForegroundColor Yellow
```

### Manual Start (Individual Services)

#### Terminal 1: Docker Services
```powershell
docker-compose up -d postgres redis
docker-compose logs -f postgres redis  # View logs
```

#### Terminal 2: Django Backend
```powershell
cd "D:\Code\Azure Reports\azure_advisor_reports"
.\venv\Scripts\Activate.ps1
python manage.py runserver

# Server runs on: http://localhost:8000
```

#### Terminal 3: React Frontend
```powershell
cd "D:\Code\Azure Reports\frontend"
npm start

# Server runs on: http://localhost:3000
```

#### Terminal 4: Celery Worker
```powershell
cd "D:\Code\Azure Reports"
.\scripts\start-celery.ps1

# Or manually:
cd azure_advisor_reports
.\venv\Scripts\Activate.ps1
celery -A azure_advisor_reports worker -l info -P solo
```

---

## Service Management

### Docker Services

```powershell
# View running containers
docker-compose ps

# View logs
docker-compose logs postgres    # PostgreSQL logs
docker-compose logs redis       # Redis logs
docker-compose logs -f          # Follow all logs

# Stop services
docker-compose stop

# Start services
docker-compose start

# Restart services
docker-compose restart

# Stop and remove containers
docker-compose down

# Stop and remove with volumes (DELETES DATA)
docker-compose down -v
```

### Django Management

```powershell
# Always activate virtual environment first!
cd azure_advisor_reports
.\venv\Scripts\Activate.ps1

# Run server
python manage.py runserver

# Run migrations
python manage.py migrate

# Create migrations
python manage.py makemigrations

# Create superuser
python manage.py createsuperuser

# Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic

# Check for issues
python manage.py check

# Production deployment check
python manage.py check --deploy
```

### Celery Management

```powershell
# Start worker (Windows-compatible)
celery -A azure_advisor_reports worker -l info -P solo

# Start worker with gevent pool (requires: pip install gevent)
celery -A azure_advisor_reports worker -l info -P gevent --concurrency=4

# Check worker status
celery -A azure_advisor_reports inspect active
celery -A azure_advisor_reports inspect stats

# Purge all tasks
celery -A azure_advisor_reports purge

# Start flower (monitoring UI)
celery -A azure_advisor_reports flower
# Access at: http://localhost:5555
```

### Frontend Management

```powershell
cd frontend

# Start development server
npm start

# Build production bundle
npm run build

# Run tests
npm test

# Run tests with coverage
npm test -- --coverage

# Lint code
npm run lint

# Format code
npm run format
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Port Already in Use

**Symptom:** Error starting service - port 8000/3000/5432/6379 already in use

**Solution:**
```powershell
# Find process using port
netstat -ano | findstr :8000

# Kill process
taskkill /PID <PID> /F

# Or use Task Manager to end the process
```

#### 2. Docker Container Won't Start

**Symptom:** Container exits immediately or shows unhealthy status

**Solution:**
```powershell
# Check Docker Desktop is running
docker version

# Check container logs
docker-compose logs postgres

# Restart Docker Desktop
# Right-click Docker icon → Restart

# Check WSL2
wsl --list --verbose

# Restart WSL
wsl --shutdown
```

#### 3. Database Connection Refused

**Symptom:** `django.db.utils.OperationalError: could not connect to server`

**Solution:**
```powershell
# Check PostgreSQL container is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres

# Verify connection
docker exec -it azure-advisor-postgres psql -U postgres -d azure_advisor_reports
```

#### 4. Redis Connection Refused

**Symptom:** `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379`

**Solution:**
```powershell
# Check Redis container
docker-compose ps redis

# Test Redis connection
docker exec -it azure-advisor-redis redis-cli ping
# Expected: PONG

# Restart Redis
docker-compose restart redis
```

#### 5. Celery Worker Crashes on Windows

**Symptom:** `AttributeError` or worker immediately exits

**Solution:**
```powershell
# Use 'solo' pool (not 'prefork')
celery -A azure_advisor_reports worker -l info -P solo

# Or use gevent pool
pip install gevent
celery -A azure_advisor_reports worker -l info -P gevent
```

#### 6. PowerShell Execution Policy Error

**Symptom:** `cannot be loaded because running scripts is disabled`

**Solution:**
```powershell
# Run as Administrator or set policy for current user
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# Verify
Get-ExecutionPolicy -List
```

#### 7. Virtual Environment Activation Issues

**Symptom:** `venv\Scripts\Activate.ps1` not found or fails

**Solution:**
```powershell
# Recreate virtual environment
Remove-Item -Recurse -Force venv
python -m venv venv

# Use absolute path
& "D:\Code\Azure Reports\azure_advisor_reports\venv\Scripts\Activate.ps1"

# Alternative: Use CMD activate script
.\venv\Scripts\activate.bat
```

#### 8. Frontend Compilation Errors

**Symptom:** ESLint errors, missing dependencies

**Solution:**
```powershell
# Clear cache and reinstall
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm cache clean --force
npm install

# Ignore ESLint errors temporarily
# Create .env.local in frontend directory:
echo "ESLINT_NO_DEV_ERRORS=true" > .env.local
```

#### 9. Health Check Endpoint Returns Errors

**Symptom:** `/api/health/` shows services as unhealthy

**Solution:**
```powershell
# Check each service individually:

# 1. Test database
docker exec -it azure-advisor-postgres psql -U postgres -c "SELECT 1"

# 2. Test Redis
docker exec -it azure-advisor-redis redis-cli ping

# 3. Check Django can connect
cd azure_advisor_reports
python manage.py shell
>>> from django.db import connection
>>> connection.ensure_connection()
>>> from django.core.cache import cache
>>> cache.set('test', 'value')
>>> cache.get('test')
```

---

## Windows-Specific Considerations

### Path Handling

Windows uses backslashes (`\`) but Python/Django prefers forward slashes (`/`).

**Recommended:**
```python
# Use forward slashes in paths
MEDIA_ROOT = "D:/Code/Azure Reports/media"

# Or use Path objects (cross-platform)
from pathlib import Path
MEDIA_ROOT = Path("D:/Code/Azure Reports/media")
```

### File System Case Sensitivity

Windows file system is case-insensitive, but Linux (Docker containers) is case-sensitive.

**Best Practice:**
- Use consistent casing in all file/folder names
- Prefer lowercase with underscores or hyphens
- Test imports carefully when deploying to Linux

### Line Endings

Windows uses CRLF (`\r\n`), Linux uses LF (`\n`).

**Git Configuration:**
```powershell
# Configure Git to handle line endings
git config --global core.autocrlf true
```

**VS Code Configuration:**
```json
{
    "files.eol": "\n"
}
```

### Celery Limitations on Windows

- **prefork pool doesn't work** (Unix-only feature)
- Use **solo** pool for single-process execution
- Use **gevent** pool for concurrent execution (requires `pip install gevent`)
- Performance may be lower than Linux/Mac

### Docker Desktop Performance

- Use **WSL2 backend** (not Hyper-V)
- Store project files in WSL2 filesystem for better performance
- Or keep in Windows but expect slower file I/O

### Firewall Considerations

Windows Firewall may block Docker or Python:
1. Allow Docker Desktop through firewall
2. Allow Python through firewall when prompted
3. Check: Control Panel → Windows Defender Firewall → Allow an app

---

## PowerShell Scripts

### Available Scripts

| Script | Location | Purpose |
|--------|----------|---------|
| `start-celery.ps1` | `scripts/` | Start Celery worker with Windows compatibility |
| `start-dev.ps1` | Project root (create it) | Start all development services |

### Creating Custom Scripts

Example: `stop-all.ps1`
```powershell
Write-Host "Stopping all services..." -ForegroundColor Yellow

# Stop Django (find and kill process)
$djangoProcess = Get-Process | Where-Object { $_.ProcessName -eq "python" -and $_.CommandLine -like "*manage.py*" }
if ($djangoProcess) {
    Stop-Process -Id $djangoProcess.Id -Force
    Write-Host "Django stopped" -ForegroundColor Green
}

# Stop Docker services
docker-compose stop

Write-Host "All services stopped" -ForegroundColor Green
```

---

## Performance Tips

### 1. Use WSL2 for Better Performance

Store and run your project in WSL2 filesystem:
```powershell
# Access WSL2 from Windows
cd \\wsl$\Ubuntu\home\username\projects\azure-reports
```

### 2. Disable Windows Defender Real-Time Scanning for Dev Folders

Add exclusions for:
- Your project directory
- Python installation directory
- Node.js installation directory
- Docker data directory

**Path:** Settings → Windows Security → Virus & threat protection → Exclusions

### 3. Use SSD for Docker Storage

Configure Docker to use SSD:
1. Docker Desktop Settings
2. Resources → Advanced
3. Change "Disk image location"

### 4. Optimize PostgreSQL for Development

Add to `docker-compose.yml`:
```yaml
postgres:
  command: postgres -c shared_buffers=256MB -c max_connections=200
```

### 5. Use RAM Disk for Temporary Files (Advanced)

Install ImDisk Toolkit and create RAM disk for logs/cache.

---

## Additional Resources

### Documentation
- [Django Documentation](https://docs.djangoproject.com/)
- [React Documentation](https://react.dev/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Docker Documentation](https://docs.docker.com/)

### Project-Specific Docs
- `CLAUDE.md` - Comprehensive project guide
- `PLANNING.md` - Architecture and planning
- `TASK.md` - Development tasks
- `README.md` - User-facing documentation

### Support
- GitHub Issues: Report bugs and request features
- Team Chat: Internal communication
- Documentation: Check project docs first

---

## Quick Reference Commands

```powershell
# Start everything
docker-compose up -d
cd azure_advisor_reports && .\venv\Scripts\Activate.ps1 && python manage.py runserver

# Health check
curl http://localhost:8000/api/health/

# View logs
docker-compose logs -f

# Stop everything
docker-compose down
Get-Process python | Stop-Process
Get-Process node | Stop-Process

# Reset database (DELETES ALL DATA)
docker-compose down -v
docker-compose up -d postgres
python manage.py migrate
python manage.py createsuperuser
```

---

**Last Updated:** September 30, 2025
**Maintainer:** DevOps-Cloud-Specialist
**Questions?** Check CLAUDE.md or open a GitHub issue