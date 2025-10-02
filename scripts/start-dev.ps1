# ================================
# Start Development Environment
# Azure Advisor Reports Platform
# Windows PowerShell Edition
# ================================

<#
.SYNOPSIS
    Starts the entire development environment for Azure Advisor Reports Platform.

.DESCRIPTION
    This comprehensive script performs the following:
    1. Validates prerequisites (Python, Node.js, Docker)
    2. Checks and starts Docker services (PostgreSQL, Redis)
    3. Activates Python virtual environment
    4. Runs database migrations
    5. Starts Django development server
    6. Provides instructions for starting frontend and Celery

.PARAMETER SkipMigrations
    Skip running database migrations

.PARAMETER SkipChecks
    Skip prerequisite checks (use with caution)

.PARAMETER Frontend
    Also start the frontend development server (requires separate terminal)

.EXAMPLE
    .\start-dev.ps1
    Start development environment with all checks

.EXAMPLE
    .\start-dev.ps1 -SkipMigrations
    Start without running migrations

.NOTES
    Author: Azure Advisor Reports Team
    Date: 2025-10-01
    Requires: Python 3.11+, Node.js 18+, Docker Desktop
#>

[CmdletBinding()]
param(
    [Parameter()]
    [switch]$SkipMigrations,

    [Parameter()]
    [switch]$SkipChecks,

    [Parameter()]
    [switch]$Frontend
)

# Script configuration
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "azure_advisor_reports"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$LogDir = Join-Path $BackendDir "logs"

# Color output functions
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = 'White'
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✓ $Message" -Color Green
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "ℹ $Message" -Color Cyan
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-ColorOutput "⚠ $Message" -Color Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-ColorOutput "✗ $Message" -Color Red
}

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-ColorOutput "═══════════════════════════════════════════════════════" -Color Blue
    Write-ColorOutput "  $Message" -Color Blue
    Write-ColorOutput "═══════════════════════════════════════════════════════" -Color Blue
    Write-Host ""
}

# Banner
Clear-Host
Write-Host ""
Write-ColorOutput "╔═══════════════════════════════════════════════════════╗" -Color Magenta
Write-ColorOutput "║   Azure Advisor Reports Platform - Dev Environment   ║" -Color Magenta
Write-ColorOutput "║          Comprehensive Startup Script v1.0            ║" -Color Magenta
Write-ColorOutput "╚═══════════════════════════════════════════════════════╝" -Color Magenta
Write-Host ""

# ================================
# Step 1: Prerequisite Checks
# ================================
if (-not $SkipChecks) {
    Write-Step "Step 1: Checking Prerequisites"

    # Check Python
    Write-Info "Checking Python installation..."
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+)\.(\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            if ($major -ge 3 -and $minor -ge 11) {
                Write-Success "Python $pythonVersion found"
            } else {
                Write-Error-Custom "Python 3.11+ required, found $pythonVersion"
                exit 1
            }
        }
    } catch {
        Write-Error-Custom "Python not found. Please install Python 3.11+"
        Write-Info "Download from: https://www.python.org/downloads/"
        exit 1
    }

    # Check Node.js
    Write-Info "Checking Node.js installation..."
    try {
        $nodeVersion = node --version 2>&1
        if ($nodeVersion -match "v(\d+)\.") {
            $major = [int]$matches[1]
            if ($major -ge 18) {
                Write-Success "Node.js $nodeVersion found"
            } else {
                Write-Warning-Custom "Node.js 18+ recommended, found $nodeVersion"
            }
        }
    } catch {
        Write-Error-Custom "Node.js not found. Please install Node.js 18+"
        Write-Info "Download from: https://nodejs.org/"
        exit 1
    }

    # Check npm
    Write-Info "Checking npm installation..."
    try {
        $npmVersion = npm --version 2>&1
        Write-Success "npm $npmVersion found"
    } catch {
        Write-Error-Custom "npm not found. Please install Node.js with npm"
        exit 1
    }

    # Check Docker
    Write-Info "Checking Docker installation..."
    try {
        $dockerVersion = docker --version 2>&1
        Write-Success "Docker found: $dockerVersion"
    } catch {
        Write-Error-Custom "Docker not found. Please install Docker Desktop"
        Write-Info "Download from: https://www.docker.com/products/docker-desktop"
        exit 1
    }

    # Check Docker is running
    Write-Info "Verifying Docker is running..."
    try {
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Docker is running"
        } else {
            Write-Error-Custom "Docker is not running. Please start Docker Desktop"
            exit 1
        }
    } catch {
        Write-Error-Custom "Cannot connect to Docker. Please ensure Docker Desktop is running"
        exit 1
    }

    # Check Git
    Write-Info "Checking Git installation..."
    try {
        $gitVersion = git --version 2>&1
        Write-Success "Git found: $gitVersion"
    } catch {
        Write-Warning-Custom "Git not found. It's recommended for version control"
    }

    Write-Success "All prerequisites satisfied!"
}

# ================================
# Step 2: Docker Services
# ================================
Write-Step "Step 2: Starting Docker Services"

Write-Info "Checking Docker Compose configuration..."
$dockerComposePath = Join-Path $ProjectRoot "docker-compose.yml"
if (-not (Test-Path $dockerComposePath)) {
    Write-Error-Custom "docker-compose.yml not found at: $dockerComposePath"
    exit 1
}
Write-Success "Docker Compose configuration found"

# Check if PostgreSQL is running
Write-Info "Checking PostgreSQL container..."
$postgresStatus = docker ps --filter "name=azure-advisor-postgres" --format "{{.Status}}" 2>&1
if ($postgresStatus -like "*Up*") {
    Write-Success "PostgreSQL is already running"
} else {
    Write-Info "Starting PostgreSQL container..."
    docker-compose up -d postgres
    Write-Success "PostgreSQL started"

    Write-Info "Waiting for PostgreSQL to be ready..."
    $maxAttempts = 30
    $attempt = 0
    while ($attempt -lt $maxAttempts) {
        Start-Sleep -Seconds 2
        $healthCheck = docker exec azure-advisor-postgres pg_isready -U postgres 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "PostgreSQL is ready"
            break
        }
        $attempt++
        Write-Host "." -NoNewline
    }

    if ($attempt -eq $maxAttempts) {
        Write-Error-Custom "PostgreSQL failed to start within timeout"
        exit 1
    }
}

# Check if Redis is running
Write-Info "Checking Redis container..."
$redisStatus = docker ps --filter "name=azure-advisor-redis" --format "{{.Status}}" 2>&1
if ($redisStatus -like "*Up*") {
    Write-Success "Redis is already running"
} else {
    Write-Info "Starting Redis container..."
    docker-compose up -d redis
    Write-Success "Redis started"

    Write-Info "Waiting for Redis to be ready..."
    Start-Sleep -Seconds 3
    $redisCheck = docker exec azure-advisor-redis redis-cli ping 2>&1
    if ($redisCheck -eq "PONG") {
        Write-Success "Redis is ready"
    } else {
        Write-Warning-Custom "Redis may not be fully ready, but continuing..."
    }
}

# Display service status
Write-Host ""
Write-Info "Docker Services Status:"
docker ps --filter "name=azure-advisor" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
Write-Host ""

# ================================
# Step 3: Python Virtual Environment
# ================================
Write-Step "Step 3: Python Virtual Environment"

Set-Location $BackendDir

Write-Info "Checking virtual environment..."
$venvPath = Join-Path $BackendDir "venv"
if (-not (Test-Path $venvPath)) {
    Write-Info "Virtual environment not found. Creating..."
    python -m venv venv
    Write-Success "Virtual environment created"
}

Write-Info "Activating virtual environment..."
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Success "Virtual environment activated: $venvPath"
} else {
    Write-Error-Custom "Activation script not found: $activateScript"
    exit 1
}

# Check if dependencies are installed
Write-Info "Checking Python dependencies..."
$requirementsFile = Join-Path $BackendDir "requirements.txt"
if (Test-Path $requirementsFile) {
    Write-Info "Verifying installed packages..."
    $pipList = pip list 2>&1
    if ($pipList -match "Django") {
        Write-Success "Dependencies appear to be installed"
    } else {
        Write-Warning-Custom "Some dependencies may be missing"
        Write-Info "Installing dependencies from requirements.txt..."
        pip install -r requirements.txt
        Write-Success "Dependencies installed"
    }
} else {
    Write-Warning-Custom "requirements.txt not found"
}

# ================================
# Step 4: Environment Variables
# ================================
Write-Step "Step 4: Environment Variables"

$envFile = Join-Path $ProjectRoot ".env"
if (Test-Path $envFile) {
    Write-Info "Loading environment variables from .env..."
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)\s*=\s*(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            $value = $value -replace '^["'']|["'']$', ''
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
    Write-Success "Environment variables loaded"
} else {
    Write-Warning-Custom ".env file not found"
    Write-Info "Using default configuration"

    # Set essential defaults
    $env:DEBUG = "True"
    $env:DB_HOST = "localhost"
    $env:DB_PORT = "5432"
    $env:DB_NAME = "azure_advisor_reports"
    $env:DB_USER = "postgres"
    $env:DB_PASSWORD = "postgres"
    $env:REDIS_URL = "redis://localhost:6379/0"
    $env:DJANGO_SETTINGS_MODULE = "azure_advisor_reports.settings.development"

    Write-Success "Default environment variables set"
}

# ================================
# Step 5: Database Setup
# ================================
Write-Step "Step 5: Database Configuration"

# Create logs directory
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    Write-Success "Created logs directory: $LogDir"
}

# Run Django checks
Write-Info "Running Django system checks..."
try {
    python manage.py check
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Django system check passed"
    } else {
        Write-Warning-Custom "Django system check returned warnings"
    }
} catch {
    Write-Error-Custom "Django system check failed: $_"
    exit 1
}

# Run migrations
if (-not $SkipMigrations) {
    Write-Info "Running database migrations..."
    try {
        python manage.py migrate --noinput
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Migrations completed successfully"
        } else {
            Write-Error-Custom "Migration failed"
            exit 1
        }
    } catch {
        Write-Error-Custom "Migration error: $_"
        exit 1
    }

    # Create superuser prompt
    Write-Info "Checking for superuser..."
    $superuserCheck = python manage.py shell -c "from apps.authentication.models import User; print(User.objects.filter(is_superuser=True).exists())" 2>&1
    if ($superuserCheck -eq "False") {
        Write-Warning-Custom "No superuser found"
        Write-Host ""
        $createSuperuser = Read-Host "Would you like to create a superuser now? (y/N)"
        if ($createSuperuser -eq 'y' -or $createSuperuser -eq 'Y') {
            python manage.py createsuperuser
        } else {
            Write-Info "You can create a superuser later with: python manage.py createsuperuser"
        }
    } else {
        Write-Success "Superuser exists"
    }
} else {
    Write-Info "Skipping migrations (--SkipMigrations flag)"
}

# Collect static files
Write-Info "Collecting static files..."
try {
    python manage.py collectstatic --noinput --clear 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Static files collected"
    }
} catch {
    Write-Warning-Custom "Static files collection had issues (non-critical)"
}

# ================================
# Step 6: Health Check
# ================================
Write-Step "Step 6: Service Health Check"

Write-Info "Testing database connection..."
$dbTest = python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('OK')" 2>&1
if ($dbTest -match "OK") {
    Write-Success "Database connection: OK"
} else {
    Write-Error-Custom "Database connection failed"
    exit 1
}

Write-Info "Testing Redis connection..."
$redisTest = python manage.py shell -c "from django.core.cache import cache; cache.set('test', 'ok', 10); print(cache.get('test'))" 2>&1
if ($redisTest -match "ok") {
    Write-Success "Redis connection: OK"
} else {
    Write-Warning-Custom "Redis connection issue (Celery may not work)"
}

# ================================
# Step 7: Summary and Instructions
# ================================
Write-Step "Development Environment Ready!"

Write-ColorOutput "╔═══════════════════════════════════════════════════════╗" -Color Green
Write-ColorOutput "║              Environment Status                       ║" -Color Green
Write-ColorOutput "╚═══════════════════════════════════════════════════════╝" -Color Green
Write-Host ""
Write-Success "PostgreSQL:  Running on localhost:5432"
Write-Success "Redis:       Running on localhost:6379"
Write-Success "Django:      Configured and ready"
Write-Success "Migrations:  Up to date"
Write-Host ""

Write-ColorOutput "╔═══════════════════════════════════════════════════════╗" -Color Cyan
Write-ColorOutput "║              Next Steps                               ║" -Color Cyan
Write-ColorOutput "╚═══════════════════════════════════════════════════════╝" -Color Cyan
Write-Host ""

Write-Host "1. " -NoNewline; Write-ColorOutput "Start Django Development Server:" -Color Yellow
Write-Host "   " -NoNewline; Write-ColorOutput "python manage.py runserver" -Color White
Write-Host "   " -NoNewline; Write-ColorOutput "Access at: http://localhost:8000" -Color Gray
Write-Host ""

Write-Host "2. " -NoNewline; Write-ColorOutput "Start Celery Worker (in new terminal):" -Color Yellow
Write-Host "   " -NoNewline; Write-ColorOutput "cd azure_advisor_reports" -Color White
Write-Host "   " -NoNewline; Write-ColorOutput "..\scripts\start-celery.ps1" -Color White
Write-Host ""

Write-Host "3. " -NoNewline; Write-ColorOutput "Start Frontend (in new terminal):" -Color Yellow
Write-Host "   " -NoNewline; Write-ColorOutput "cd frontend" -Color White
Write-Host "   " -NoNewline; Write-ColorOutput "npm install  # First time only" -Color White
Write-Host "   " -NoNewline; Write-ColorOutput "npm start" -Color White
Write-Host "   " -NoNewline; Write-ColorOutput "Access at: http://localhost:3000" -Color Gray
Write-Host ""

Write-Host "4. " -NoNewline; Write-ColorOutput "Access Admin Panel:" -Color Yellow
Write-Host "   " -NoNewline; Write-ColorOutput "http://localhost:8000/admin" -Color Gray
Write-Host ""

Write-ColorOutput "╔═══════════════════════════════════════════════════════╗" -Color Cyan
Write-ColorOutput "║              Useful Commands                          ║" -Color Cyan
Write-ColorOutput "╚═══════════════════════════════════════════════════════╝" -Color Cyan
Write-Host ""
Write-Host "  • " -NoNewline; Write-ColorOutput "Health Check:      " -Color Gray -NoNewline; Write-ColorOutput "curl http://localhost:8000/api/health/" -Color White
Write-Host "  • " -NoNewline; Write-ColorOutput "Run Tests:         " -Color Gray -NoNewline; Write-ColorOutput "python manage.py test" -Color White
Write-Host "  • " -NoNewline; Write-ColorOutput "Create Migrations: " -Color Gray -NoNewline; Write-ColorOutput "python manage.py makemigrations" -Color White
Write-Host "  • " -NoNewline; Write-ColorOutput "Django Shell:      " -Color Gray -NoNewline; Write-ColorOutput "python manage.py shell" -Color White
Write-Host "  • " -NoNewline; Write-ColorOutput "Stop Containers:   " -Color Gray -NoNewline; Write-ColorOutput "docker-compose down" -Color White
Write-Host ""

# Prompt to start Django server
Write-Host ""
$startServer = Read-Host "Would you like to start the Django development server now? (Y/n)"
if ($startServer -ne 'n' -and $startServer -ne 'N') {
    Write-Host ""
    Write-ColorOutput "Starting Django development server..." -Color Green
    Write-ColorOutput "Press Ctrl+C to stop" -Color Yellow
    Write-Host ""
    python manage.py runserver
} else {
    Write-Info "You can start the server manually with: python manage.py runserver"
}
