# ================================
# Run Tests for Azure Advisor Reports Platform
# Comprehensive Test Runner for Windows
# ================================

<#
.SYNOPSIS
    Runs tests for both backend (Django) and frontend (React) applications.

.DESCRIPTION
    This script provides a comprehensive test runner that:
    - Runs backend tests with pytest and coverage
    - Runs frontend tests with Jest
    - Generates coverage reports
    - Can run specific test suites

.PARAMETER Backend
    Run only backend tests

.PARAMETER Frontend
    Run only frontend tests

.PARAMETER Coverage
    Generate coverage reports (HTML format)

.PARAMETER Verbose
    Enable verbose test output

.PARAMETER Pattern
    Test pattern to match (for pytest)

.EXAMPLE
    .\run-tests.ps1
    Runs all tests (backend and frontend)

.EXAMPLE
    .\run-tests.ps1 -Backend -Coverage
    Runs only backend tests with coverage report

.EXAMPLE
    .\run-tests.ps1 -Pattern "test_client*"
    Runs backend tests matching pattern
#>

[CmdletBinding()]
param(
    [Parameter()]
    [switch]$Backend,

    [Parameter()]
    [switch]$Frontend,

    [Parameter()]
    [switch]$Coverage,

    [Parameter()]
    [switch]$Verbose,

    [Parameter()]
    [string]$Pattern = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "azure_advisor_reports"
$FrontendDir = Join-Path $ProjectRoot "frontend"

# Color output functions
function Write-ColorOutput {
    param([string]$Message, [string]$Color = 'White')
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success { param([string]$Message) Write-ColorOutput "✓ $Message" -Color Green }
function Write-Info { param([string]$Message) Write-ColorOutput "ℹ $Message" -Color Cyan }
function Write-Error-Custom { param([string]$Message) Write-ColorOutput "✗ $Message" -Color Red }
function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-ColorOutput "═══════════════════════════════════════" -Color Blue
    Write-ColorOutput "  $Message" -Color Blue
    Write-ColorOutput "═══════════════════════════════════════" -Color Blue
    Write-Host ""
}

# Banner
Clear-Host
Write-Host ""
Write-ColorOutput "╔═══════════════════════════════════════╗" -Color Magenta
Write-ColorOutput "║   Azure Advisor Reports - Tests      ║" -Color Magenta
Write-ColorOutput "╚═══════════════════════════════════════╝" -Color Magenta
Write-Host ""

# Determine what to run
$runBackend = $Backend -or (-not $Frontend)
$runFrontend = $Frontend -or (-not $Backend)

$testsPassed = $true

# ================================
# Backend Tests
# ================================
if ($runBackend) {
    Write-Step "Running Backend Tests (Django/Pytest)"

    Set-Location $BackendDir

    # Check if virtual environment exists
    $venvPath = Join-Path $BackendDir "venv"
    if (Test-Path $venvPath) {
        Write-Info "Activating virtual environment..."
        $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
        & $activateScript
        Write-Success "Virtual environment activated"
    } else {
        Write-Error-Custom "Virtual environment not found at: $venvPath"
        Write-Info "Please run: .\scripts\start-dev.ps1 first"
        exit 1
    }

    # Check if services are running
    Write-Info "Checking Docker services..."
    $postgresStatus = docker ps --filter "name=azure-advisor-postgres" --format "{{.Status}}" 2>&1
    $redisStatus = docker ps --filter "name=azure-advisor-redis" --format "{{.Status}}" 2>&1

    if ($postgresStatus -notlike "*Up*") {
        Write-Error-Custom "PostgreSQL is not running"
        Write-Info "Starting PostgreSQL..."
        docker-compose up -d postgres
        Start-Sleep -Seconds 5
    }

    if ($redisStatus -notlike "*Up*") {
        Write-Error-Custom "Redis is not running"
        Write-Info "Starting Redis..."
        docker-compose up -d redis
        Start-Sleep -Seconds 3
    }

    Write-Success "Docker services are ready"

    # Build pytest command
    $pytestCmd = "pytest"

    if ($Coverage) {
        $pytestCmd += " --cov=apps --cov-report=html --cov-report=term-missing"
    }

    if ($Verbose) {
        $pytestCmd += " -vv"
    } else {
        $pytestCmd += " -v"
    }

    if ($Pattern) {
        $pytestCmd += " -k `"$Pattern`""
    }

    # Add markers and settings
    $pytestCmd += " --tb=short --maxfail=5"

    Write-Info "Running: $pytestCmd"
    Write-Host ""

    # Run tests
    try {
        Invoke-Expression $pytestCmd
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Success "Backend tests passed!"
        } else {
            Write-Host ""
            Write-Error-Custom "Backend tests failed!"
            $testsPassed = $false
        }
    } catch {
        Write-Error-Custom "Failed to run backend tests: $_"
        $testsPassed = $false
    }

    # Show coverage report location
    if ($Coverage -and (Test-Path "htmlcov\index.html")) {
        Write-Host ""
        Write-Info "Coverage report generated at:"
        Write-ColorOutput "  file:///$((Get-Item 'htmlcov\index.html').FullName.Replace('\', '/'))" -Color Gray
    }
}

# ================================
# Frontend Tests
# ================================
if ($runFrontend) {
    Write-Step "Running Frontend Tests (React/Jest)"

    Set-Location $FrontendDir

    # Check if node_modules exists
    if (-not (Test-Path "node_modules")) {
        Write-Info "Installing npm dependencies..."
        npm install
    }

    # Build npm test command
    $npmCmd = "npm test -- --watchAll=false"

    if ($Coverage) {
        $npmCmd += " --coverage"
    }

    if ($Verbose) {
        $npmCmd += " --verbose"
    }

    Write-Info "Running: $npmCmd"
    Write-Host ""

    # Run tests
    try {
        Invoke-Expression $npmCmd
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Success "Frontend tests passed!"
        } else {
            Write-Host ""
            Write-Error-Custom "Frontend tests failed!"
            $testsPassed = $false
        }
    } catch {
        Write-Error-Custom "Failed to run frontend tests: $_"
        $testsPassed = $false
    }

    # Show coverage report location
    if ($Coverage -and (Test-Path "coverage\lcov-report\index.html")) {
        Write-Host ""
        Write-Info "Coverage report generated at:"
        Write-ColorOutput "  file:///$((Get-Item 'coverage\lcov-report\index.html').FullName.Replace('\', '/'))" -Color Gray
    }
}

# ================================
# Summary
# ================================
Write-Host ""
Write-ColorOutput "═══════════════════════════════════════" -Color Blue
Write-ColorOutput "  Test Summary" -Color Blue
Write-ColorOutput "═══════════════════════════════════════" -Color Blue
Write-Host ""

if ($testsPassed) {
    Write-Success "All tests passed successfully!"
    Write-Host ""
    exit 0
} else {
    Write-Error-Custom "Some tests failed. Please review the output above."
    Write-Host ""
    exit 1
}
