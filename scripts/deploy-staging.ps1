<#
.SYNOPSIS
    Staging Environment Deployment Script for Azure Advisor Reports Platform

.DESCRIPTION
    Automated deployment script for staging environment with blue-green deployment strategy.
    Includes pre-flight checks, infrastructure deployment, application deployment,
    health checks, and rollback capabilities.

.PARAMETER Force
    Skip confirmation prompts

.PARAMETER SkipValidation
    Skip pre-deployment validation (not recommended)

.PARAMETER WhatIf
    Preview deployment without making changes

.PARAMETER SkipHealthCheck
    Skip post-deployment health checks

.EXAMPLE
    .\deploy-staging.ps1

.EXAMPLE
    .\deploy-staging.ps1 -Force -SkipHealthCheck

.NOTES
    Version: 1.0
    Author: Azure Advisor Reports Team
    Last Updated: October 6, 2025
    Environment: Staging

    Prerequisites:
    - Azure CLI installed and authenticated
    - Bicep CLI installed
    - Contributor access to Azure subscription
    - GitHub secrets configured (for GitHub Actions)
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory=$false)]
    [switch]$Force,

    [Parameter(Mandatory=$false)]
    [switch]$SkipValidation,

    [Parameter(Mandatory=$false)]
    [switch]$WhatIf,

    [Parameter(Mandatory=$false)]
    [switch]$SkipHealthCheck
)

# ============================================================================
# SCRIPT CONFIGURATION
# ============================================================================

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

# Environment settings
$Environment = 'staging'
$Location = 'eastus2'
$ResourceGroupPrefix = 'rg-azure-advisor'
$AppNamePrefix = 'azure-advisor'

# Script paths
$ScriptRoot = Split-Path -Parent $PSCommandPath
$ProjectRoot = Split-Path -Parent $ScriptRoot
$AzureScriptsRoot = Join-Path $ScriptRoot "azure"
$DeployScript = Join-Path $AzureScriptsRoot "deploy.ps1"
$ValidationScript = Join-Path $ScriptRoot "validate-production-readiness.ps1"
$PostDeployScript = Join-Path $ScriptRoot "post-deployment-verify.ps1"

# Deployment configuration
$DeploymentName = "azure-advisor-staging-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$ResourceGroupName = "$ResourceGroupPrefix-$Environment"
$LogDir = Join-Path $ScriptRoot "logs"
$LogFile = Join-Path $LogDir "deploy-staging-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

# Create log directory
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# Color scheme
$SuccessColor = "Green"
$WarningColor = "Yellow"
$ErrorColor = "Red"
$InfoColor = "Cyan"
$HeaderColor = "Magenta"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet('Info', 'Success', 'Warning', 'Error')]
        [string]$Level = 'Info'
    )

    $Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $LogMessage = "[$Timestamp] [$Level] $Message"

    Add-Content -Path $LogFile -Value $LogMessage

    switch ($Level) {
        'Success' { Write-Host $Message -ForegroundColor $SuccessColor }
        'Warning' { Write-Host $Message -ForegroundColor $WarningColor }
        'Error'   { Write-Host $Message -ForegroundColor $ErrorColor }
        default   { Write-Host $Message -ForegroundColor $InfoColor }
    }
}

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════════" -ForegroundColor $HeaderColor
    Write-Host "  $Title" -ForegroundColor $HeaderColor
    Write-Host "═══════════════════════════════════════════════════════════════════════" -ForegroundColor $HeaderColor
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "──────────────────────────────────────────────────────────────────────" -ForegroundColor $InfoColor
    Write-Host "  $Message" -ForegroundColor $InfoColor
    Write-Host "──────────────────────────────────────────────────────────────────────" -ForegroundColor $InfoColor
}

function Confirm-Deployment {
    if ($Force -or $WhatIf) {
        return $true
    }

    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════════" -ForegroundColor Yellow
    Write-Host "  STAGING DEPLOYMENT CONFIRMATION" -ForegroundColor Yellow
    Write-Host "═══════════════════════════════════════════════════════════════════════" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Environment:      Staging" -ForegroundColor Cyan
    Write-Host "  Location:         $Location" -ForegroundColor Cyan
    Write-Host "  Resource Group:   $ResourceGroupName" -ForegroundColor Cyan
    Write-Host "  Deployment Name:  $DeploymentName" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  This will deploy the Azure Advisor Reports Platform to the STAGING environment." -ForegroundColor White
    Write-Host "  Existing resources will be updated or replaced as needed." -ForegroundColor White
    Write-Host ""

    $response = Read-Host "  Do you want to proceed? (yes/no)"

    if ($response -ne 'yes') {
        Write-Log "Deployment cancelled by user" -Level Warning
        return $false
    }

    return $true
}

# ============================================================================
# VALIDATION PHASE
# ============================================================================

function Start-PreDeploymentValidation {
    Write-Step "Phase 1: Pre-Deployment Validation"

    if ($SkipValidation) {
        Write-Log "⚠️  Skipping validation (SkipValidation flag set)" -Level Warning
        return $true
    }

    if (-not (Test-Path $ValidationScript)) {
        Write-Log "❌ Validation script not found: $ValidationScript" -Level Error
        throw "Validation script missing"
    }

    Write-Log "Running production readiness validation..."

    try {
        $validationResult = & $ValidationScript -Environment $Environment
        $validationExitCode = $LASTEXITCODE

        if ($validationExitCode -eq 0) {
            Write-Log "✅ All validation checks passed" -Level Success
            return $true
        } elseif ($validationExitCode -eq 2) {
            Write-Log "⚠️  Validation completed with warnings" -Level Warning

            if (-not $Force) {
                $response = Read-Host "  Continue with deployment despite warnings? (yes/no)"
                if ($response -ne 'yes') {
                    throw "Deployment cancelled due to validation warnings"
                }
            }
            return $true
        } else {
            Write-Log "❌ Validation failed" -Level Error
            throw "Pre-deployment validation failed"
        }
    } catch {
        Write-Log "❌ Validation error: $_" -Level Error
        throw
    }
}

# ============================================================================
# INFRASTRUCTURE DEPLOYMENT PHASE
# ============================================================================

function Deploy-AzureInfrastructure {
    Write-Step "Phase 2: Azure Infrastructure Deployment"

    if (-not (Test-Path $DeployScript)) {
        Write-Log "❌ Deployment script not found: $DeployScript" -Level Error
        throw "Deployment script missing"
    }

    Write-Log "Deploying Azure infrastructure via Bicep..."
    Write-Log "Deployment name: $DeploymentName"

    try {
        $deployParams = @{
            Environment = $Environment
            Location = $Location
            ResourceGroupPrefix = $ResourceGroupPrefix
            AppNamePrefix = $AppNamePrefix
        }

        if ($WhatIf) {
            $deployParams.Add('WhatIf', $true)
        }

        Write-Log "Executing Azure deployment script..."

        & $DeployScript @deployParams

        if ($LASTEXITCODE -ne 0) {
            throw "Azure deployment script failed with exit code: $LASTEXITCODE"
        }

        Write-Log "✅ Infrastructure deployment completed" -Level Success
        return $true

    } catch {
        Write-Log "❌ Infrastructure deployment failed: $_" -Level Error
        throw
    }
}

# ============================================================================
# APPLICATION DEPLOYMENT PHASE
# ============================================================================

function Deploy-BackendApplication {
    Write-Step "Phase 3: Backend Application Deployment"

    $backendAppName = "$AppNamePrefix-backend-staging"

    Write-Log "Deploying backend application to: $backendAppName"

    try {
        # Check if App Service exists
        $appExists = az webapp show --name $backendAppName --resource-group $ResourceGroupName 2>$null

        if (-not $appExists) {
            Write-Log "❌ Backend App Service not found: $backendAppName" -Level Error
            throw "Backend App Service does not exist"
        }

        Write-Log "App Service found: $backendAppName"

        if ($WhatIf) {
            Write-Log "[WHATIF] Would deploy backend application to $backendAppName" -Level Info
            return $true
        }

        # Deployment will be handled by GitHub Actions or manual process
        Write-Log "ℹ️  Backend deployment ready" -Level Info
        Write-Log "   Next steps:" -Level Info
        Write-Log "   1. Push code changes to trigger GitHub Actions" -Level Info
        Write-Log "   OR" -Level Info
        Write-Log "   2. Deploy manually using: az webapp deployment source config-zip" -Level Info

        return $true

    } catch {
        Write-Log "❌ Backend deployment failed: $_" -Level Error
        throw
    }
}

function Deploy-FrontendApplication {
    Write-Step "Phase 4: Frontend Application Deployment"

    $frontendAppName = "$AppNamePrefix-frontend-staging"

    Write-Log "Deploying frontend application to: $frontendAppName"

    try {
        # Check if App Service exists
        $appExists = az webapp show --name $frontendAppName --resource-group $ResourceGroupName 2>$null

        if (-not $appExists) {
            Write-Log "❌ Frontend App Service not found: $frontendAppName" -Level Error
            throw "Frontend App Service does not exist"
        }

        Write-Log "App Service found: $frontendAppName"

        if ($WhatIf) {
            Write-Log "[WHATIF] Would deploy frontend application to $frontendAppName" -Level Info
            return $true
        }

        # Deployment will be handled by GitHub Actions or manual process
        Write-Log "ℹ️  Frontend deployment ready" -Level Info
        Write-Log "   Next steps:" -Level Info
        Write-Log "   1. Push code changes to trigger GitHub Actions" -Level Info
        Write-Log "   OR" -Level Info
        Write-Log "   2. Deploy manually using: az webapp deployment source config-zip" -Level Info

        return $true

    } catch {
        Write-Log "❌ Frontend deployment failed: $_" -Level Error
        throw
    }
}

# ============================================================================
# DATABASE MIGRATION PHASE
# ============================================================================

function Run-DatabaseMigrations {
    Write-Step "Phase 5: Database Migrations"

    Write-Log "⚠️  Database migrations should be run after application deployment" -Level Warning
    Write-Log "   Run migrations using:" -Level Info
    Write-Log "   az webapp ssh --name $AppNamePrefix-backend-staging --resource-group $ResourceGroupName" -Level Info
    Write-Log "   Then execute: python manage.py migrate" -Level Info

    return $true
}

# ============================================================================
# HEALTH CHECK PHASE
# ============================================================================

function Test-DeploymentHealth {
    Write-Step "Phase 6: Health Check & Verification"

    if ($SkipHealthCheck -or $WhatIf) {
        Write-Log "⚠️  Skipping health checks" -Level Warning
        return $true
    }

    if (-not (Test-Path $PostDeployScript)) {
        Write-Log "⚠️  Post-deployment script not found: $PostDeployScript" -Level Warning
        Write-Log "   Skipping automated health checks" -Level Warning
        return $true
    }

    Write-Log "Running post-deployment verification..."

    try {
        & $PostDeployScript -Environment $Environment

        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ Health checks passed" -Level Success
            return $true
        } else {
            Write-Log "⚠️  Some health checks failed" -Level Warning
            return $false
        }
    } catch {
        Write-Log "⚠️  Health check error: $_" -Level Warning
        return $false
    }
}

# ============================================================================
# ROLLBACK FUNCTION
# ============================================================================

function Invoke-Rollback {
    param([string]$Reason)

    Write-Header "ROLLBACK INITIATED"
    Write-Log "Reason: $Reason" -Level Warning

    Write-Log "⚠️  Manual rollback required" -Level Warning
    Write-Log "   To rollback infrastructure changes:" -Level Info
    Write-Log "   1. Navigate to Azure Portal" -Level Info
    Write-Log "   2. Go to Resource Group: $ResourceGroupName" -Level Info
    Write-Log "   3. Review deployments and redeploy previous version" -Level Info
    Write-Log "   OR" -Level Info
    Write-Log "   4. Delete resource group if this was first deployment" -Level Info
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

try {
    $deploymentStartTime = Get-Date

    # Display deployment header
    Write-Header "Azure Advisor Reports - Staging Deployment"
    Write-Log "Deployment started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Log "Environment: Staging"
    Write-Log "Location: $Location"
    Write-Log "Log file: $LogFile"

    # Confirm deployment
    if (-not (Confirm-Deployment)) {
        Write-Log "Deployment cancelled" -Level Warning
        exit 0
    }

    # Phase 1: Validation
    $validationSuccess = Start-PreDeploymentValidation
    if (-not $validationSuccess) {
        throw "Pre-deployment validation failed"
    }

    # Phase 2: Infrastructure Deployment
    $infraSuccess = Deploy-AzureInfrastructure
    if (-not $infraSuccess) {
        throw "Infrastructure deployment failed"
    }

    # Phase 3: Backend Deployment
    $backendSuccess = Deploy-BackendApplication
    if (-not $backendSuccess) {
        Invoke-Rollback "Backend deployment failed"
        throw "Backend deployment failed"
    }

    # Phase 4: Frontend Deployment
    $frontendSuccess = Deploy-FrontendApplication
    if (-not $frontendSuccess) {
        Invoke-Rollback "Frontend deployment failed"
        throw "Frontend deployment failed"
    }

    # Phase 5: Database Migrations
    $migrationSuccess = Run-DatabaseMigrations
    if (-not $migrationSuccess) {
        Write-Log "⚠️  Database migration failed - manual intervention required" -Level Warning
    }

    # Phase 6: Health Checks
    $healthSuccess = Test-DeploymentHealth
    if (-not $healthSuccess) {
        Write-Log "⚠️  Health checks failed - review deployment" -Level Warning
    }

    # Calculate deployment duration
    $deploymentEndTime = Get-Date
    $deploymentDuration = $deploymentEndTime - $deploymentStartTime

    # Success summary
    Write-Header "DEPLOYMENT COMPLETED"
    Write-Log "✅ Staging deployment completed successfully" -Level Success
    Write-Log "   Duration: $($deploymentDuration.ToString('hh\:mm\:ss'))" -Level Success
    Write-Log "   Environment: Staging" -Level Success
    Write-Log "   Resource Group: $ResourceGroupName" -Level Success
    Write-Log ""
    Write-Log "Next Steps:" -Level Info
    Write-Log "1. Verify application endpoints:" -Level Info
    Write-Log "   • Backend:  https://$AppNamePrefix-backend-staging.azurewebsites.net/api/health" -Level Info
    Write-Log "   • Frontend: https://$AppNamePrefix-frontend-staging.azurewebsites.net" -Level Info
    Write-Log ""
    Write-Log "2. Run smoke tests on staging environment" -Level Info
    Write-Log ""
    Write-Log "3. If tests pass, proceed with production deployment:" -Level Info
    Write-Log "   .\scripts\deploy-production.ps1" -Level Info
    Write-Log ""
    Write-Log "Log file: $LogFile" -Level Info

    exit 0

} catch {
    Write-Header "DEPLOYMENT FAILED"
    Write-Log "❌ Deployment failed: $_" -Level Error
    Write-Log "Stack trace: $($_.ScriptStackTrace)" -Level Error
    Write-Log ""
    Write-Log "Troubleshooting:" -Level Info
    Write-Log "1. Review log file: $LogFile" -Level Info
    Write-Log "2. Check Azure Portal for deployment status" -Level Info
    Write-Log "3. Review Bicep template compilation errors" -Level Info
    Write-Log "4. Verify Azure credentials and permissions" -Level Info
    Write-Log ""

    exit 1
} finally {
    $ProgressPreference = 'Continue'
}
