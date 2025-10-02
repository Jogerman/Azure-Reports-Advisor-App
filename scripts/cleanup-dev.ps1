# ================================
# Cleanup Development Environment
# Azure Advisor Reports Platform
# ================================

<#
.SYNOPSIS
    Cleans up development environment and Docker resources.

.DESCRIPTION
    This script helps clean up:
    - Docker containers
    - Docker volumes (optional)
    - Python cache files
    - Node modules (optional)
    - Log files
    - Test artifacts

.PARAMETER All
    Remove everything including volumes and dependencies

.PARAMETER Volumes
    Remove Docker volumes (WARNING: This deletes all data!)

.PARAMETER Cache
    Remove Python and Node cache files

.PARAMETER Dependencies
    Remove node_modules and Python venv

.PARAMETER Logs
    Remove log files

.EXAMPLE
    .\cleanup-dev.ps1 -Cache
    Remove only cache files

.EXAMPLE
    .\cleanup-dev.ps1 -All
    Complete cleanup (WARNING: Removes all data)

.NOTES
    Use with caution! The -All flag will remove all Docker volumes.
#>

[CmdletBinding()]
param(
    [Parameter()]
    [switch]$All,

    [Parameter()]
    [switch]$Volumes,

    [Parameter()]
    [switch]$Cache,

    [Parameter()]
    [switch]$Dependencies,

    [Parameter()]
    [switch]$Logs
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
function Write-Warning-Custom { param([string]$Message) Write-ColorOutput "⚠ $Message" -Color Yellow }

# Banner
Clear-Host
Write-Host ""
Write-ColorOutput "╔═══════════════════════════════════════════════════╗" -Color Red
Write-ColorOutput "║   Development Environment Cleanup                 ║" -Color Red
Write-ColorOutput "╚═══════════════════════════════════════════════════╝" -Color Red
Write-Host ""

# Determine what to clean
if ($All) {
    $Volumes = $true
    $Cache = $true
    $Dependencies = $false  # Don't remove by default
    $Logs = $true
}

# If nothing specified, just cache and logs
if (-not ($Volumes -or $Cache -or $Dependencies -or $Logs)) {
    $Cache = $true
    $Logs = $true
}

$cleanupItems = @()
if ($Volumes) { $cleanupItems += "Docker volumes (DATA LOSS!)" }
if ($Cache) { $cleanupItems += "Cache files" }
if ($Dependencies) { $cleanupItems += "Dependencies (node_modules, venv)" }
if ($Logs) { $cleanupItems += "Log files" }

Write-Warning-Custom "The following will be cleaned up:"
$cleanupItems | ForEach-Object { Write-ColorOutput "  • $_" -Color Yellow }
Write-Host ""

$confirm = Read-Host "Are you sure you want to continue? (yes/no)"
if ($confirm -ne "yes") {
    Write-Info "Cleanup cancelled"
    exit 0
}

Write-Host ""

# ================================
# 1. Stop Docker Containers
# ================================
Write-Info "Stopping Docker containers..."
try {
    Set-Location $ProjectRoot
    docker-compose down
    Write-Success "Docker containers stopped"
} catch {
    Write-Warning-Custom "Failed to stop containers: $_"
}

# ================================
# 2. Remove Docker Volumes
# ================================
if ($Volumes) {
    Write-Host ""
    Write-Warning-Custom "Removing Docker volumes (THIS WILL DELETE ALL DATA)..."

    $finalConfirm = Read-Host "Type 'DELETE' to confirm"
    if ($finalConfirm -eq "DELETE") {
        try {
            docker-compose down -v
            Write-Success "Docker volumes removed"
        } catch {
            Write-Warning-Custom "Failed to remove volumes: $_"
        }
    } else {
        Write-Info "Volume removal cancelled"
    }
}

# ================================
# 3. Clean Python Cache
# ================================
if ($Cache) {
    Write-Host ""
    Write-Info "Cleaning Python cache files..."

    try {
        # Remove __pycache__ directories
        $pycacheDirs = Get-ChildItem -Path $BackendDir -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
        $count = $pycacheDirs.Count
        $pycacheDirs | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        Write-Success "Removed $count __pycache__ directories"

        # Remove .pyc files
        $pycFiles = Get-ChildItem -Path $BackendDir -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue
        $count = $pycFiles.Count
        $pycFiles | Remove-Item -Force -ErrorAction SilentlyContinue
        Write-Success "Removed $count .pyc files"

        # Remove .pytest_cache
        $pytestCache = Join-Path $BackendDir ".pytest_cache"
        if (Test-Path $pytestCache) {
            Remove-Item $pytestCache -Recurse -Force
            Write-Success "Removed .pytest_cache"
        }

        # Remove coverage files
        $coverageFiles = @(
            (Join-Path $BackendDir ".coverage"),
            (Join-Path $BackendDir "htmlcov"),
            (Join-Path $BackendDir "coverage.xml")
        )
        foreach ($file in $coverageFiles) {
            if (Test-Path $file) {
                Remove-Item $file -Recurse -Force -ErrorAction SilentlyContinue
                Write-Success "Removed coverage files"
            }
        }

    } catch {
        Write-Warning-Custom "Error cleaning Python cache: $_"
    }

    # Clean Node cache
    Write-Info "Cleaning Node cache files..."
    try {
        $nodeCache = Join-Path $FrontendDir ".cache"
        if (Test-Path $nodeCache) {
            Remove-Item $nodeCache -Recurse -Force
            Write-Success "Removed Node .cache"
        }

        # Remove Jest cache
        $jestCache = Join-Path $FrontendDir ".jest_cache"
        if (Test-Path $jestCache) {
            Remove-Item $jestCache -Recurse -Force
            Write-Success "Removed Jest cache"
        }

    } catch {
        Write-Warning-Custom "Error cleaning Node cache: $_"
    }
}

# ================================
# 4. Remove Dependencies
# ================================
if ($Dependencies) {
    Write-Host ""
    Write-Warning-Custom "Removing dependencies..."

    # Remove node_modules
    $nodeModules = Join-Path $FrontendDir "node_modules"
    if (Test-Path $nodeModules) {
        Write-Info "Removing node_modules (this may take a while)..."
        Remove-Item $nodeModules -Recurse -Force
        Write-Success "Removed node_modules"
    }

    # Remove Python venv
    $venvPath = Join-Path $BackendDir "venv"
    if (Test-Path $venvPath) {
        Write-Info "Removing Python virtual environment..."
        Remove-Item $venvPath -Recurse -Force
        Write-Success "Removed venv"
    }

    # Remove package-lock.json
    $packageLock = Join-Path $FrontendDir "package-lock.json"
    if (Test-Path $packageLock) {
        Remove-Item $packageLock -Force
        Write-Success "Removed package-lock.json"
    }
}

# ================================
# 5. Clean Log Files
# ================================
if ($Logs) {
    Write-Host ""
    Write-Info "Cleaning log files..."

    try {
        $logDir = Join-Path $BackendDir "logs"
        if (Test-Path $logDir) {
            Get-ChildItem $logDir -Filter "*.log" | Remove-Item -Force
            Get-ChildItem $logDir -Filter "*.pid" | Remove-Item -Force
            Write-Success "Removed log files"
        }

        # Remove Django logs
        $djangoLogs = Get-ChildItem -Path $BackendDir -Filter "django*.log" -ErrorAction SilentlyContinue
        $djangoLogs | Remove-Item -Force -ErrorAction SilentlyContinue

    } catch {
        Write-Warning-Custom "Error cleaning logs: $_"
    }
}

# ================================
# 6. Clean Build Artifacts
# ================================
Write-Host ""
Write-Info "Cleaning build artifacts..."

# Frontend build
$frontendBuild = Join-Path $FrontendDir "build"
if (Test-Path $frontendBuild) {
    Remove-Item $frontendBuild -Recurse -Force
    Write-Success "Removed frontend build"
}

# Backend static files
$staticFiles = Join-Path $BackendDir "staticfiles"
if (Test-Path $staticFiles) {
    Remove-Item $staticFiles -Recurse -Force
    Write-Success "Removed static files"
}

# ================================
# Summary
# ================================
Write-Host ""
Write-ColorOutput "═══════════════════════════════════════════════════" -Color Green
Write-ColorOutput "  Cleanup Complete" -Color Green
Write-ColorOutput "═══════════════════════════════════════════════════" -Color Green
Write-Host ""

Write-Info "To restore your development environment, run:"
Write-ColorOutput "  .\scripts\start-dev.ps1" -Color Gray
Write-Host ""

Write-Info "To reinstall dependencies:"
Write-ColorOutput "  Backend:  pip install -r azure_advisor_reports\requirements.txt" -Color Gray
Write-ColorOutput "  Frontend: npm install --prefix frontend" -Color Gray
Write-Host ""
