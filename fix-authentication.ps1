# Authentication Fix Script for Azure Advisor Reports Platform
# Version: 1.2.2
# Purpose: Clean cache and rebuild frontend to fix authentication issues

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Azure Advisor Reports - Authentication Fix" -ForegroundColor Cyan
Write-Host "Version 1.2.2" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the correct directory
if (-not (Test-Path "frontend\package.json")) {
    Write-Host "Error: Please run this script from the project root directory" -ForegroundColor Red
    Write-Host "Current directory: $PWD" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/6] Checking environment variables..." -ForegroundColor Yellow

# Check if .env.local exists
if (-not (Test-Path "frontend\.env.local")) {
    Write-Host "  Warning: frontend\.env.local not found!" -ForegroundColor Red
    Write-Host "  Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item "frontend\.env.example" "frontend\.env.local"
    Write-Host "  Please edit frontend\.env.local with your Azure AD credentials" -ForegroundColor Yellow
    notepad "frontend\.env.local"
    Read-Host "Press Enter after saving the file"
}

# Verify required variables
$envContent = Get-Content "frontend\.env.local" -Raw
$requiredVars = @(
    "REACT_APP_AZURE_CLIENT_ID",
    "REACT_APP_AZURE_TENANT_ID",
    "REACT_APP_AZURE_REDIRECT_URI"
)

$missingVars = @()
foreach ($var in $requiredVars) {
    if ($envContent -notmatch "$var=.+") {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "  Error: Missing required environment variables:" -ForegroundColor Red
    foreach ($var in $missingVars) {
        Write-Host "    - $var" -ForegroundColor Red
    }
    Write-Host "  Please update frontend\.env.local and run this script again" -ForegroundColor Yellow
    exit 1
}

Write-Host "  Environment variables configured" -ForegroundColor Green
Write-Host ""

Write-Host "[2/6] Stopping running processes..." -ForegroundColor Yellow

# Stop any running node processes on port 3000
$nodeProcesses = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique

if ($nodeProcesses) {
    foreach ($processId in $nodeProcesses) {
        Write-Host "  Stopping process on port 3000 (PID: $processId)" -ForegroundColor Gray
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
}

Write-Host "  Processes stopped" -ForegroundColor Green
Write-Host ""

Write-Host "[3/6] Cleaning frontend cache..." -ForegroundColor Yellow

# Clean frontend build directories
$dirsToClean = @(
    "frontend\build",
    "frontend\node_modules\.cache",
    "frontend\.cache"
)

foreach ($dir in $dirsToClean) {
    if (Test-Path $dir) {
        Write-Host "  Removing $dir" -ForegroundColor Gray
        Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
    }
}

Write-Host "  Frontend cache cleaned" -ForegroundColor Green
Write-Host ""

Write-Host "[4/6] Cleaning npm cache..." -ForegroundColor Yellow

Push-Location frontend
npm cache clean --force 2>&1 | Out-Null
Write-Host "  NPM cache cleaned" -ForegroundColor Green
Pop-Location
Write-Host ""

Write-Host "[5/6] Reinstalling dependencies..." -ForegroundColor Yellow

# Option to skip node_modules reinstall
$reinstall = Read-Host "Do you want to reinstall node_modules? This may take a few minutes. (y/N)"

if ($reinstall -eq "y" -or $reinstall -eq "Y") {
    Push-Location frontend

    if (Test-Path "node_modules") {
        Write-Host "  Removing node_modules..." -ForegroundColor Gray
        Remove-Item -Recurse -Force "node_modules" -ErrorAction SilentlyContinue
    }

    Write-Host "  Installing dependencies (this may take a while)..." -ForegroundColor Gray
    npm install

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Error: npm install failed" -ForegroundColor Red
        Pop-Location
        exit 1
    }

    Pop-Location
    Write-Host "  Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  Skipping node_modules reinstall" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "[6/6] Verifying configuration..." -ForegroundColor Yellow

# Read and display current configuration (obfuscated)
$envLines = Get-Content "frontend\.env.local"
foreach ($line in $envLines) {
    if ($line -match "^REACT_APP_AZURE_(CLIENT_ID|TENANT_ID)=(.+)") {
        $varName = $matches[1]
        $varValue = $matches[2]
        if ($varValue.Length -gt 8) {
            $obfuscated = $varValue.Substring(0, 8) + "..."
            Write-Host "  $varName = $obfuscated" -ForegroundColor Gray
        }
    }
}

Write-Host "  Configuration verified" -ForegroundColor Green
Write-Host ""

Write-Host "============================================" -ForegroundColor Green
Write-Host "Authentication fix completed successfully!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Start the backend server:" -ForegroundColor White
Write-Host "   cd azure_advisor_reports" -ForegroundColor Gray
Write-Host "   python manage.py runserver" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Start the frontend server:" -ForegroundColor White
Write-Host "   cd frontend" -ForegroundColor Gray
Write-Host "   npm start" -ForegroundColor Gray
Write-Host ""
Write-Host "3. If you still have authentication issues:" -ForegroundColor White
Write-Host "   - Open http://localhost:3000/clear-auth-cache.html" -ForegroundColor Gray
Write-Host "   - Click 'Clear All Authentication Cache'" -ForegroundColor Gray
Write-Host "   - Return to the app and try logging in again" -ForegroundColor Gray
Write-Host ""

$startNow = Read-Host "Do you want to start the frontend server now? (y/N)"

if ($startNow -eq "y" -or $startNow -eq "Y") {
    Write-Host ""
    Write-Host "Starting frontend server..." -ForegroundColor Cyan
    Write-Host "Note: Press Ctrl+C to stop the server" -ForegroundColor Yellow
    Write-Host ""

    Push-Location frontend
    npm start
    Pop-Location
} else {
    Write-Host ""
    Write-Host "You can start the servers manually when ready." -ForegroundColor White
    Write-Host ""
}
