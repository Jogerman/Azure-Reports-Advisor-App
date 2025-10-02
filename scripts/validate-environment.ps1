# ================================
# Azure Advisor Reports Platform
# Environment Validation Script (Windows PowerShell)
# ================================

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Azure Advisor Reports Platform" -ForegroundColor Cyan
Write-Host "Environment Validation Script" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

$ErrorCount = 0

# Function to check if a command exists
function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Function to report status
function Report-Status {
    param(
        [string]$Component,
        [bool]$Status,
        [string]$Message = ""
    )

    if ($Status) {
        Write-Host "✅ $Component" -ForegroundColor Green
        if ($Message) { Write-Host "   $Message" -ForegroundColor Gray }
    } else {
        Write-Host "❌ $Component" -ForegroundColor Red
        if ($Message) { Write-Host "   $Message" -ForegroundColor Gray }
        $script:ErrorCount++
    }
}

Write-Host "`n1. Checking System Prerequisites..." -ForegroundColor Yellow

# Check Python
if (Test-Command "python") {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python 3\.([8-9]|\d{2,})") {
        Report-Status "Python" $true $pythonVersion
    } else {
        Report-Status "Python" $false "Version 3.8+ required, found: $pythonVersion"
    }
} else {
    Report-Status "Python" $false "Python not found in PATH"
}

# Check Node.js
if (Test-Command "node") {
    $nodeVersion = node --version 2>&1
    if ($nodeVersion -match "v(1[8-9]|\d{2,})") {
        Report-Status "Node.js" $true $nodeVersion
    } else {
        Report-Status "Node.js" $false "Version 18+ required, found: $nodeVersion"
    }
} else {
    Report-Status "Node.js" $false "Node.js not found in PATH"
}

# Check npm
if (Test-Command "npm") {
    $npmVersion = npm --version 2>&1
    Report-Status "npm" $true "v$npmVersion"
} else {
    Report-Status "npm" $false "npm not found in PATH"
}

# Check Docker
if (Test-Command "docker") {
    $dockerVersion = docker --version 2>&1
    if ($dockerVersion -match "Docker version") {
        Report-Status "Docker" $true $dockerVersion

        # Test Docker connectivity
        try {
            docker ps | Out-Null
            Report-Status "Docker Engine" $true "Docker daemon is running"
        } catch {
            Report-Status "Docker Engine" $false "Docker daemon not running or not accessible"
        }
    } else {
        Report-Status "Docker" $false "Docker version check failed"
    }
} else {
    Report-Status "Docker" $false "Docker not found in PATH"
}

# Check Git
if (Test-Command "git") {
    $gitVersion = git --version 2>&1
    Report-Status "Git" $true $gitVersion
} else {
    Report-Status "Git" $false "Git not found in PATH"
}

Write-Host "`n2. Checking Project Structure..." -ForegroundColor Yellow

# Check main directories
$projectDirs = @(
    "azure_advisor_reports",
    "frontend",
    "scripts",
    "docs",
    "tests"
)

foreach ($dir in $projectDirs) {
    $path = Join-Path $PWD $dir
    Report-Status "Directory: $dir" (Test-Path $path)
}

# Check key files
$keyFiles = @(
    "docker-compose.yml",
    ".env.example",
    "CLAUDE.md",
    "TASK.md",
    "README.md"
)

foreach ($file in $keyFiles) {
    $path = Join-Path $PWD $file
    Report-Status "File: $file" (Test-Path $path)
}

Write-Host "`n3. Checking Backend Configuration..." -ForegroundColor Yellow

# Check Django backend structure
$backendDirs = @(
    "azure_advisor_reports\apps\authentication",
    "azure_advisor_reports\apps\clients",
    "azure_advisor_reports\apps\reports",
    "azure_advisor_reports\apps\analytics"
)

foreach ($dir in $backendDirs) {
    $path = Join-Path $PWD $dir
    Report-Status "Django App: $($dir.Split('\')[-1])" (Test-Path $path)
}

# Check Django files
$djangoFiles = @(
    "azure_advisor_reports\manage.py",
    "azure_advisor_reports\requirements.txt",
    "azure_advisor_reports\azure_advisor_reports\settings.py",
    "azure_advisor_reports\azure_advisor_reports\celery.py"
)

foreach ($file in $djangoFiles) {
    $path = Join-Path $PWD $file
    Report-Status "Django: $($file.Split('\')[-1])" (Test-Path $path)
}

Write-Host "`n4. Checking Frontend Configuration..." -ForegroundColor Yellow

# Check React frontend
$frontendFiles = @(
    "frontend\package.json",
    "frontend\tailwind.config.js",
    "frontend\tsconfig.json",
    "frontend\src\App.tsx"
)

foreach ($file in $frontendFiles) {
    $path = Join-Path $PWD $file
    Report-Status "React: $($file.Split('\')[-1])" (Test-Path $path)
}

# Check if node_modules exists
$nodeModulesPath = Join-Path $PWD "frontend\node_modules"
Report-Status "Frontend Dependencies" (Test-Path $nodeModulesPath) "Run 'npm install' in frontend directory if missing"

Write-Host "`n5. Checking Environment Configuration..." -ForegroundColor Yellow

# Check .env file
$envPath = Join-Path $PWD ".env"
if (Test-Path $envPath) {
    Report-Status "Environment File" $true "Found .env file"

    # Check for critical environment variables
    $envContent = Get-Content $envPath -Raw
    $criticalVars = @(
        "SECRET_KEY",
        "DATABASE_URL",
        "REDIS_URL",
        "AZURE_CLIENT_ID"
    )

    foreach ($var in $criticalVars) {
        if ($envContent -match "^$var=.+") {
            Report-Status "Env Var: $var" $true "Configured"
        } else {
            Report-Status "Env Var: $var" $false "Missing or empty"
        }
    }
} else {
    Report-Status "Environment File" $false "Copy .env.example to .env and configure"
}

Write-Host "`n6. Testing Backend Setup..." -ForegroundColor Yellow

# Test Django configuration
try {
    Set-Location "azure_advisor_reports"

    # Check if virtual environment exists
    if (Test-Path "venv") {
        Report-Status "Python Virtual Environment" $true "Found venv directory"
    } else {
        Report-Status "Python Virtual Environment" $false "Run 'python -m venv venv' to create"
    }

    # Try Django check (if venv is activated)
    try {
        $djangoCheck = python manage.py check --deploy 2>&1
        if ($LASTEXITCODE -eq 0) {
            Report-Status "Django Configuration" $true "Django check passed"
        } else {
            Report-Status "Django Configuration" $false "Django check failed: $djangoCheck"
        }
    } catch {
        Report-Status "Django Configuration" $false "Could not run Django check (activate venv first)"
    }

    Set-Location ".."
} catch {
    Report-Status "Backend Test" $false "Could not access backend directory"
}

Write-Host "`n7. Testing Frontend Setup..." -ForegroundColor Yellow

try {
    Set-Location "frontend"

    # Check package.json
    if (Test-Path "package.json") {
        $packageJson = Get-Content "package.json" | ConvertFrom-Json
        Report-Status "Frontend Package" $true "Version: $($packageJson.version)"
    }

    # Test npm/build setup (if node_modules exists)
    if (Test-Path "node_modules") {
        try {
            $npmTest = npm run build 2>&1
            if ($LASTEXITCODE -eq 0) {
                Report-Status "Frontend Build" $true "Build successful"
            } else {
                Report-Status "Frontend Build" $false "Build failed"
            }
        } catch {
            Report-Status "Frontend Build" $false "Could not test build"
        }
    } else {
        Report-Status "Frontend Dependencies" $false "Run 'npm install' first"
    }

    Set-Location ".."
} catch {
    Report-Status "Frontend Test" $false "Could not access frontend directory"
}

Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "Environment Validation Complete" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

if ($ErrorCount -eq 0) {
    Write-Host "✅ All checks passed! Environment is ready." -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "1. Start Docker Desktop (if using Docker)" -ForegroundColor Gray
    Write-Host "2. Run 'docker-compose up -d' to start services" -ForegroundColor Gray
    Write-Host "3. Access the application at http://localhost:3000" -ForegroundColor Gray
} else {
    Write-Host "❌ $ErrorCount issues found. Please resolve them before continuing." -ForegroundColor Red
    Write-Host "`nCommon solutions:" -ForegroundColor Yellow
    Write-Host "1. Install missing dependencies" -ForegroundColor Gray
    Write-Host "2. Copy .env.example to .env and configure" -ForegroundColor Gray
    Write-Host "3. Run 'python -m venv venv' in backend directory" -ForegroundColor Gray
    Write-Host "4. Run 'npm install' in frontend directory" -ForegroundColor Gray
    Write-Host "5. Start Docker Desktop" -ForegroundColor Gray
}

Write-Host ""
exit $ErrorCount