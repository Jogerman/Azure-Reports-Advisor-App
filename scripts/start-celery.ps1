# ================================
# Start Celery Worker on Windows
# Azure Advisor Reports Platform
# ================================

<#
.SYNOPSIS
    Starts Celery worker for the Azure Advisor Reports Platform on Windows.

.DESCRIPTION
    This script starts a Celery worker using the 'solo' pool which is compatible
    with Windows. It includes proper error handling and logging.

.PARAMETER Pool
    The execution pool to use. Options: 'solo' (default), 'gevent'
    Note: 'prefork' doesn't work on Windows

.PARAMETER LogLevel
    Logging level for Celery. Options: debug, info, warning, error, critical
    Default: info

.PARAMETER Concurrency
    Number of concurrent worker processes. For 'solo' pool, this is always 1.
    For 'gevent' pool, you can increase this value.
    Default: 1

.PARAMETER Queues
    Comma-separated list of queues to consume from.
    Default: default,reports,priority

.EXAMPLE
    .\start-celery.ps1
    Starts Celery worker with default settings (solo pool)

.EXAMPLE
    .\start-celery.ps1 -Pool gevent -Concurrency 4 -LogLevel debug
    Starts Celery worker with gevent pool, 4 concurrent workers, and debug logging

.NOTES
    Requirements:
    - Python virtual environment must be activated
    - Redis must be running (via Docker or locally)
    - Django project must be properly configured
#>

param(
    [ValidateSet('solo', 'gevent')]
    [string]$Pool = 'solo',

    [ValidateSet('debug', 'info', 'warning', 'error', 'critical')]
    [string]$LogLevel = 'info',

    [int]$Concurrency = 1,

    [string]$Queues = 'default,reports,priority'
)

# Script configuration
$ErrorActionPreference = "Stop"
$ProjectRoot = "D:\Code\Azure Reports"
$BackendDir = Join-Path $ProjectRoot "azure_advisor_reports"
$LogDir = Join-Path $BackendDir "logs"

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = 'White'
    )
    Write-Host $Message -ForegroundColor $Color
}

# Banner
Write-Host "`n" -NoNewline
Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "  Azure Advisor Reports - Celery Worker" "Cyan"
Write-ColorOutput "========================================" "Cyan"
Write-Host ""

# Check if we're in the correct directory
if (-not (Test-Path $BackendDir)) {
    Write-ColorOutput "ERROR: Backend directory not found at $BackendDir" "Red"
    exit 1
}

# Change to backend directory
Set-Location $BackendDir
Write-ColorOutput "Working directory: $BackendDir" "Gray"

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-ColorOutput "WARNING: Virtual environment not detected!" "Yellow"
    Write-ColorOutput "Attempting to activate virtual environment..." "Yellow"

    $VenvPath = Join-Path $BackendDir "venv"
    $ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"

    if (Test-Path $ActivateScript) {
        & $ActivateScript
        Write-ColorOutput "Virtual environment activated!" "Green"
    } else {
        Write-ColorOutput "ERROR: Virtual environment not found at $VenvPath" "Red"
        Write-ColorOutput "Please create it first: python -m venv venv" "Yellow"
        exit 1
    }
}

# Check if Redis is running
Write-ColorOutput "`nChecking Redis connection..." "Yellow"
try {
    $redisCheck = docker ps --filter "name=azure-advisor-redis" --format "{{.Status}}"
    if ($redisCheck -like "*Up*") {
        Write-ColorOutput "✓ Redis is running" "Green"
    } else {
        Write-ColorOutput "WARNING: Redis container exists but may not be running" "Yellow"
        Write-ColorOutput "Starting Redis..." "Yellow"
        docker-compose up -d redis
        Start-Sleep -Seconds 3
    }
} catch {
    Write-ColorOutput "ERROR: Cannot connect to Docker or Redis" "Red"
    Write-ColorOutput "Please ensure Docker Desktop is running and Redis container is started:" "Yellow"
    Write-ColorOutput "  docker-compose up -d redis" "Gray"
    exit 1
}

# Check if Django can be imported
Write-ColorOutput "`nValidating Django configuration..." "Yellow"
try {
    $djangoCheck = python manage.py check --deploy 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "✓ Django configuration valid" "Green"
    } else {
        Write-ColorOutput "WARNING: Django configuration has warnings" "Yellow"
        Write-ColorOutput $djangoCheck "Gray"
    }
} catch {
    Write-ColorOutput "ERROR: Django configuration check failed" "Red"
    exit 1
}

# Create logs directory if it doesn't exist
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    Write-ColorOutput "Created logs directory: $LogDir" "Gray"
}

# Display configuration
Write-ColorOutput "`nCelery Worker Configuration:" "Cyan"
Write-ColorOutput "  Pool Type:      $Pool" "Gray"
Write-ColorOutput "  Log Level:      $LogLevel" "Gray"
Write-ColorOutput "  Concurrency:    $Concurrency" "Gray"
Write-ColorOutput "  Queues:         $Queues" "Gray"
Write-ColorOutput "  Log Directory:  $LogDir" "Gray"
Write-Host ""

# Warning for gevent pool
if ($Pool -eq 'gevent') {
    Write-ColorOutput "NOTE: Using gevent pool. Ensure 'gevent' is installed:" "Yellow"
    Write-ColorOutput "  pip install gevent" "Gray"
    Write-Host ""
}

# Build Celery command
$CeleryCommand = "celery -A azure_advisor_reports worker"
$CeleryCommand += " -l $LogLevel"
$CeleryCommand += " -P $Pool"

if ($Pool -eq 'solo') {
    # Solo pool doesn't support concurrency
    $CeleryCommand += " --concurrency=1"
} else {
    $CeleryCommand += " --concurrency=$Concurrency"
}

$CeleryCommand += " -Q $Queues"
$CeleryCommand += " --logfile=$LogDir\celery_worker.log"
$CeleryCommand += " --pidfile=$LogDir\celery_worker.pid"

# Display the command
Write-ColorOutput "Starting Celery worker with command:" "Cyan"
Write-ColorOutput "  $CeleryCommand" "Gray"
Write-Host ""

# Start Celery worker
Write-ColorOutput "========================================" "Green"
Write-ColorOutput "  Celery Worker Starting..." "Green"
Write-ColorOutput "========================================" "Green"
Write-ColorOutput "`nPress Ctrl+C to stop the worker`n" "Yellow"

try {
    # Execute the command
    Invoke-Expression $CeleryCommand
} catch {
    Write-ColorOutput "`nERROR: Celery worker failed to start" "Red"
    Write-ColorOutput $_.Exception.Message "Red"
    exit 1
}

# Cleanup on exit
Write-ColorOutput "`nCelery worker stopped" "Yellow"