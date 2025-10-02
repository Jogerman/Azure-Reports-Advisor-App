# ================================
# Docker Services Health Check
# Azure Advisor Reports Platform
# ================================

<#
.SYNOPSIS
    Performs comprehensive health checks on all Docker services.

.DESCRIPTION
    This script checks the health and connectivity of:
    - Docker Engine
    - PostgreSQL container and database
    - Redis container and connectivity
    - Network connectivity between services

.PARAMETER Fix
    Attempt to fix issues automatically (restart containers, etc.)

.PARAMETER Detailed
    Show detailed diagnostic information

.EXAMPLE
    .\docker-health-check.ps1
    Runs basic health checks

.EXAMPLE
    .\docker-health-check.ps1 -Fix
    Runs health checks and attempts to fix issues

.EXAMPLE
    .\docker-health-check.ps1 -Detailed
    Shows detailed diagnostic information
#>

[CmdletBinding()]
param(
    [Parameter()]
    [switch]$Fix,

    [Parameter()]
    [switch]$Detailed
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Color output functions
function Write-ColorOutput {
    param([string]$Message, [string]$Color = 'White')
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success { param([string]$Message) Write-ColorOutput "✓ $Message" -Color Green }
function Write-Info { param([string]$Message) Write-ColorOutput "ℹ $Message" -Color Cyan }
function Write-Warning-Custom { param([string]$Message) Write-ColorOutput "⚠ $Message" -Color Yellow }
function Write-Error-Custom { param([string]$Message) Write-ColorOutput "✗ $Message" -Color Red }

# Banner
Clear-Host
Write-Host ""
Write-ColorOutput "╔═══════════════════════════════════════════════════╗" -Color Cyan
Write-ColorOutput "║   Docker Services Health Check                    ║" -Color Cyan
Write-ColorOutput "╚═══════════════════════════════════════════════════╝" -Color Cyan
Write-Host ""

$allHealthy = $true

# ================================
# 1. Check Docker Engine
# ================================
Write-Info "Checking Docker Engine..."
try {
    $dockerVersion = docker version --format '{{.Server.Version}}' 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker Engine running (version $dockerVersion)"
    } else {
        Write-Error-Custom "Docker Engine is not running"
        Write-Info "Please start Docker Desktop"
        $allHealthy = $false

        if ($Fix) {
            Write-Info "Attempting to start Docker Desktop..."
            Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
            Write-Info "Waiting for Docker to start (30 seconds)..."
            Start-Sleep -Seconds 30
        } else {
            exit 1
        }
    }
} catch {
    Write-Error-Custom "Docker is not installed or not accessible"
    Write-Info "Install from: https://www.docker.com/products/docker-desktop"
    exit 1
}

# ================================
# 2. Check Docker Compose
# ================================
Write-Info "Checking Docker Compose..."
try {
    $composeVersion = docker-compose version --short 2>&1
    Write-Success "Docker Compose available (version $composeVersion)"
} catch {
    Write-Error-Custom "Docker Compose not found"
    $allHealthy = $false
}

# ================================
# 3. Check PostgreSQL Container
# ================================
Write-Host ""
Write-Info "Checking PostgreSQL container..."

$postgresStatus = docker ps -a --filter "name=azure-advisor-postgres" --format "{{.Status}}" 2>&1

if ($postgresStatus -like "*Up*") {
    Write-Success "PostgreSQL container is running"

    # Check if healthy
    $healthStatus = docker inspect azure-advisor-postgres --format='{{.State.Health.Status}}' 2>&1
    if ($healthStatus -eq "healthy") {
        Write-Success "PostgreSQL health check: healthy"
    } else {
        Write-Warning-Custom "PostgreSQL health check: $healthStatus"
        $allHealthy = $false
    }

    # Test database connection
    Write-Info "Testing database connectivity..."
    $dbTest = docker exec azure-advisor-postgres pg_isready -U postgres -d azure_advisor_reports 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Database connection: OK"

        # Count tables
        $tableCount = docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -t -c "SELECT count(*) FROM pg_tables WHERE schemaname = 'public';" 2>&1
        Write-Success "Database tables: $($tableCount.Trim())"
    } else {
        Write-Error-Custom "Database connection failed"
        $allHealthy = $false
    }

    # Show detailed info
    if ($Detailed) {
        Write-Info "PostgreSQL Details:"
        docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "\dt" 2>&1 | Write-Host
    }

} elseif ($postgresStatus -like "*Exited*") {
    Write-Warning-Custom "PostgreSQL container exists but is stopped"
    $allHealthy = $false

    if ($Fix) {
        Write-Info "Starting PostgreSQL container..."
        docker-compose up -d postgres
        Start-Sleep -Seconds 5
        Write-Success "PostgreSQL started"
    }
} else {
    Write-Error-Custom "PostgreSQL container not found"
    $allHealthy = $false

    if ($Fix) {
        Write-Info "Creating and starting PostgreSQL container..."
        docker-compose up -d postgres
        Start-Sleep -Seconds 10
        Write-Success "PostgreSQL created and started"
    } else {
        Write-Info "Run: docker-compose up -d postgres"
    }
}

# ================================
# 4. Check Redis Container
# ================================
Write-Host ""
Write-Info "Checking Redis container..."

$redisStatus = docker ps -a --filter "name=azure-advisor-redis" --format "{{.Status}}" 2>&1

if ($redisStatus -like "*Up*") {
    Write-Success "Redis container is running"

    # Check if healthy
    $healthStatus = docker inspect azure-advisor-redis --format='{{.State.Health.Status}}' 2>&1
    if ($healthStatus -eq "healthy") {
        Write-Success "Redis health check: healthy"
    } else {
        Write-Warning-Custom "Redis health check: $healthStatus"
        $allHealthy = $false
    }

    # Test Redis connection
    Write-Info "Testing Redis connectivity..."
    $redisTest = docker exec azure-advisor-redis redis-cli ping 2>&1
    if ($redisTest -eq "PONG") {
        Write-Success "Redis connection: OK"

        # Get Redis info
        $redisInfo = docker exec azure-advisor-redis redis-cli info server 2>&1
        if ($redisInfo -match "redis_version:([^\r\n]+)") {
            Write-Success "Redis version: $($matches[1])"
        }
    } else {
        Write-Error-Custom "Redis connection failed"
        $allHealthy = $false
    }

    # Show detailed info
    if ($Detailed) {
        Write-Info "Redis Details:"
        docker exec azure-advisor-redis redis-cli info 2>&1 | Write-Host
    }

} elseif ($redisStatus -like "*Exited*") {
    Write-Warning-Custom "Redis container exists but is stopped"
    $allHealthy = $false

    if ($Fix) {
        Write-Info "Starting Redis container..."
        docker-compose up -d redis
        Start-Sleep -Seconds 3
        Write-Success "Redis started"
    }
} else {
    Write-Error-Custom "Redis container not found"
    $allHealthy = $false

    if ($Fix) {
        Write-Info "Creating and starting Redis container..."
        docker-compose up -d redis
        Start-Sleep -Seconds 5
        Write-Success "Redis created and started"
    } else {
        Write-Info "Run: docker-compose up -d redis"
    }
}

# ================================
# 5. Check Network
# ================================
Write-Host ""
Write-Info "Checking Docker network..."

$networkExists = docker network inspect azure-advisor-network 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Success "Docker network 'azure-advisor-network' exists"

    if ($Detailed) {
        Write-Info "Network Details:"
        docker network inspect azure-advisor-network --format='{{json .}}' | ConvertFrom-Json | ConvertTo-Json -Depth 2 | Write-Host
    }
} else {
    Write-Warning-Custom "Docker network 'azure-advisor-network' not found"
    Write-Info "It will be created when you run docker-compose up"
}

# ================================
# 6. Check Volumes
# ================================
Write-Host ""
Write-Info "Checking Docker volumes..."

$volumes = @("postgres_data", "redis_data", "media_data", "static_data")
foreach ($vol in $volumes) {
    $volName = "azure-advisor-reports_$vol"
    $volExists = docker volume inspect $volName 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Volume '$vol' exists"
    } else {
        Write-Warning-Custom "Volume '$vol' not found"
    }
}

# ================================
# Summary
# ================================
Write-Host ""
Write-ColorOutput "═══════════════════════════════════════════════════" -Color Blue
Write-ColorOutput "  Health Check Summary" -Color Blue
Write-ColorOutput "═══════════════════════════════════════════════════" -Color Blue
Write-Host ""

if ($allHealthy) {
    Write-Success "All services are healthy!"
    Write-Host ""
    Write-Info "Service URLs:"
    Write-ColorOutput "  PostgreSQL: localhost:5432" -Color Gray
    Write-ColorOutput "  Redis:      localhost:6379" -Color Gray
    Write-Host ""
    exit 0
} else {
    Write-Error-Custom "Some services have issues"
    Write-Host ""
    Write-Info "Common fixes:"
    Write-ColorOutput "  1. Restart services: docker-compose restart" -Color Gray
    Write-ColorOutput "  2. Rebuild services: docker-compose up -d --build" -Color Gray
    Write-ColorOutput "  3. Clean restart: docker-compose down && docker-compose up -d" -Color Gray
    Write-Host ""
    exit 1
}
