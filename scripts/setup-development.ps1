# ================================
# Azure Advisor Reports Platform
# Development Environment Setup Script (Windows PowerShell)
# ================================

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Azure Advisor Reports Platform" -ForegroundColor Cyan
Write-Host "Development Environment Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

$ErrorActionPreference = "Continue"

function Write-Step {
    param([string]$Message)
    Write-Host "`n🔄 $Message..." -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Cyan
}

# Ensure we're in the project root
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Info "Project root: $projectRoot"

# Step 1: Copy environment file
Write-Step "Setting up environment configuration"
if (!(Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Success "Copied .env.example to .env"
        Write-Info "Please edit .env file with your Azure AD and database credentials"
    } else {
        Write-Error ".env.example file not found"
    }
} else {
    Write-Info ".env file already exists"
}

# Step 2: Backend setup
Write-Step "Setting up Django backend"
try {
    Set-Location "azure_advisor_reports"

    # Create virtual environment
    if (!(Test-Path "venv")) {
        Write-Info "Creating Python virtual environment..."
        python -m venv venv
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Virtual environment created"
        } else {
            Write-Error "Failed to create virtual environment"
        }
    } else {
        Write-Info "Virtual environment already exists"
    }

    # Activate virtual environment and install dependencies
    Write-Info "Installing Python dependencies..."
    if (Test-Path "venv\Scripts\Activate.ps1") {
        & ".\venv\Scripts\Activate.ps1"
        pip install --upgrade pip
        pip install -r requirements.txt
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Python dependencies installed"
        } else {
            Write-Error "Failed to install Python dependencies"
        }
    } else {
        Write-Error "Cannot activate virtual environment"
    }

    Set-Location $projectRoot
} catch {
    Write-Error "Backend setup failed: $_"
    Set-Location $projectRoot
}

# Step 3: Frontend setup
Write-Step "Setting up React frontend"
try {
    Set-Location "frontend"

    # Install Node.js dependencies
    if (Test-Path "package.json") {
        Write-Info "Installing Node.js dependencies..."
        npm install
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Node.js dependencies installed"
        } else {
            Write-Error "Failed to install Node.js dependencies"
        }
    } else {
        Write-Error "package.json not found in frontend directory"
    }

    Set-Location $projectRoot
} catch {
    Write-Error "Frontend setup failed: $_"
    Set-Location $projectRoot
}

# Step 4: Database setup (if Docker is available)
Write-Step "Checking Docker availability"
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker is available: $dockerVersion"

        # Test Docker connectivity
        try {
            docker ps | Out-Null
            Write-Success "Docker daemon is running"

            Write-Step "Starting database services"
            Write-Info "Starting PostgreSQL and Redis with Docker..."
            docker-compose up -d postgres redis

            if ($LASTEXITCODE -eq 0) {
                Write-Success "Database services started"

                # Wait for databases to be ready
                Write-Info "Waiting for databases to be ready (30 seconds)..."
                Start-Sleep -Seconds 30

                # Run Django migrations
                Write-Step "Running Django database migrations"
                Set-Location "azure_advisor_reports"
                try {
                    if (Test-Path "venv\Scripts\Activate.ps1") {
                        & ".\venv\Scripts\Activate.ps1"
                        python manage.py migrate
                        if ($LASTEXITCODE -eq 0) {
                            Write-Success "Database migrations completed"
                        } else {
                            Write-Error "Database migrations failed"
                        }
                    }
                } catch {
                    Write-Error "Could not run migrations: $_"
                }
                Set-Location $projectRoot

            } else {
                Write-Error "Failed to start database services"
            }
        } catch {
            Write-Error "Docker daemon is not running"
            Write-Info "Please start Docker Desktop and try again"
        }
    } else {
        Write-Error "Docker is not available"
        Write-Info "Please install Docker Desktop for Windows"
    }
} catch {
    Write-Error "Could not check Docker availability"
}

# Step 5: Create startup scripts
Write-Step "Creating development startup scripts"

# Backend startup script
$backendScript = @"
# Start Django Development Server
cd azure_advisor_reports
.\venv\Scripts\Activate.ps1
python manage.py runserver
"@

Set-Content -Path "start-backend.ps1" -Value $backendScript
Write-Success "Created start-backend.ps1"

# Frontend startup script
$frontendScript = @"
# Start React Development Server
cd frontend
npm start
"@

Set-Content -Path "start-frontend.ps1" -Value $frontendScript
Write-Success "Created start-frontend.ps1"

# Celery worker script
$celeryScript = @"
# Start Celery Worker
cd azure_advisor_reports
.\venv\Scripts\Activate.ps1
celery -A azure_advisor_reports worker -l info
"@

Set-Content -Path "start-celery.ps1" -Value $celeryScript
Write-Success "Created start-celery.ps1"

# Full stack startup script
$fullStackScript = @"
# Start Full Development Stack
Write-Host "Starting Azure Advisor Reports Development Stack..." -ForegroundColor Cyan

# Start Docker services
docker-compose up -d postgres redis

# Wait for services to be ready
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Start backend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; .\start-backend.ps1"

# Start frontend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; .\start-frontend.ps1"

# Start Celery in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; .\start-celery.ps1"

Write-Host "Development stack started!" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Admin Panel: http://localhost:8000/admin" -ForegroundColor Cyan
"@

Set-Content -Path "start-dev-stack.ps1" -Value $fullStackScript
Write-Success "Created start-dev-stack.ps1"

Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "Development Setup Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file with your Azure AD credentials" -ForegroundColor Gray
Write-Host "2. Start Docker Desktop (if using Docker)" -ForegroundColor Gray
Write-Host "3. Run .\start-dev-stack.ps1 to start all services" -ForegroundColor Gray
Write-Host "4. Access the application at http://localhost:3000" -ForegroundColor Gray

Write-Host "`nAlternatively, start services individually:" -ForegroundColor Yellow
Write-Host "- Backend: .\start-backend.ps1" -ForegroundColor Gray
Write-Host "- Frontend: .\start-frontend.ps1" -ForegroundColor Gray
Write-Host "- Celery: .\start-celery.ps1" -ForegroundColor Gray

Write-Host "`nFor validation, run:" -ForegroundColor Yellow
Write-Host ".\scripts\validate-environment.ps1" -ForegroundColor Gray

Write-Host ""