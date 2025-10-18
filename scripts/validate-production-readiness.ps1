<#
.SYNOPSIS
    Production Readiness Validation Script for Azure Advisor Reports Platform

.DESCRIPTION
    Comprehensive validation script to ensure production readiness before deployment.
    Validates Azure environment, Bicep templates, GitHub secrets, environment variables,
    and all deployment prerequisites.

.PARAMETER Environment
    Target environment (dev, staging, or prod). Default: prod

.PARAMETER SkipAzureLogin
    Skip Azure CLI login check (useful for CI/CD)

.PARAMETER Verbose
    Show detailed validation information

.EXAMPLE
    .\validate-production-readiness.ps1 -Environment prod

.EXAMPLE
    .\validate-production-readiness.ps1 -Environment staging -Verbose

.NOTES
    Version: 1.0
    Author: Azure Advisor Reports Team
    Last Updated: October 6, 2025

    Exit Codes:
        0 = All validations passed - READY FOR DEPLOYMENT
        1 = Critical failures - NOT READY FOR DEPLOYMENT
        2 = Warnings present - MANUAL REVIEW REQUIRED
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment = 'prod',

    [Parameter(Mandatory=$false)]
    [switch]$SkipAzureLogin,

    [Parameter(Mandatory=$false)]
    [switch]$Verbose
)

# ============================================================================
# SCRIPT CONFIGURATION
# ============================================================================

$ErrorActionPreference = 'SilentlyContinue'
$script:ChecksPassed = 0
$script:ChecksFailed = 0
$script:ChecksWarning = 0
$script:CriticalFailed = $false

# Script paths
$ScriptRoot = Split-Path -Parent $PSCommandPath
$ProjectRoot = Split-Path -Parent $ScriptRoot
$BicepRoot = Join-Path $ScriptRoot "azure\bicep"
$MainBicepFile = Join-Path $BicepRoot "main.bicep"
$ParameterFile = Join-Path $BicepRoot "parameters.$Environment.json"

# Output configuration
$script:SuccessColor = "Green"
$script:WarningColor = "Yellow"
$script:ErrorColor = "Red"
$script:InfoColor = "Cyan"
$script:HeaderColor = "Magenta"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════════" -ForegroundColor $HeaderColor
    Write-Host "  $Title" -ForegroundColor $HeaderColor
    Write-Host "═══════════════════════════════════════════════════════════════════════" -ForegroundColor $HeaderColor
    Write-Host ""
}

function Write-SectionHeader {
    param([string]$Title, [int]$Number)
    Write-Host ""
    Write-Host "┌───────────────────────────────────────────────────────────────────┐" -ForegroundColor $InfoColor
    Write-Host "│  $Number. $Title" -ForegroundColor $InfoColor
    Write-Host "└───────────────────────────────────────────────────────────────────┘" -ForegroundColor $InfoColor
}

function Write-Pass {
    param([string]$Message)
    Write-Host "  ✅ PASS: $Message" -ForegroundColor $SuccessColor
    $script:ChecksPassed++
}

function Write-Fail {
    param([string]$Message, [switch]$Critical)
    Write-Host "  ❌ FAIL: $Message" -ForegroundColor $ErrorColor
    $script:ChecksFailed++
    if ($Critical) {
        $script:CriticalFailed = $true
    }
}

function Write-Warn {
    param([string]$Message)
    Write-Host "  ⚠️  WARN: $Message" -ForegroundColor $WarningColor
    $script:ChecksWarning++
}

function Write-Info {
    param([string]$Message)
    Write-Host "  ℹ️  INFO: $Message" -ForegroundColor $InfoColor
}

function Write-Detail {
    param([string]$Message)
    if ($Verbose) {
        Write-Host "     → $Message" -ForegroundColor Gray
    }
}

# ============================================================================
# VALIDATION CHECKS
# ============================================================================

function Test-AzureCLI {
    Write-SectionHeader "Azure CLI Installation" 1

    try {
        $azCommand = Get-Command az -ErrorAction Stop
        $azVersion = az version --query '\"azure-cli\"' -o tsv 2>$null

        if ($azVersion) {
            Write-Pass "Azure CLI installed (version: $azVersion)"
            Write-Detail "Installation path: $($azCommand.Source)"

            # Check version is recent enough (minimum 2.50.0)
            $versionParts = $azVersion.Split('.')
            if ([int]$versionParts[0] -ge 2 -and [int]$versionParts[1] -ge 50) {
                Write-Pass "Azure CLI version is recent enough (>= 2.50.0)"
            } else {
                Write-Warn "Azure CLI version is old. Recommended to upgrade to >= 2.50.0"
            }
        } else {
            Write-Fail "Azure CLI command found but version check failed" -Critical
        }
    } catch {
        Write-Fail "Azure CLI is not installed or not in PATH" -Critical
        Write-Info "Install from: https://aka.ms/installazurecliwindows"
    }
}

function Test-BicepCLI {
    Write-SectionHeader "Bicep CLI Installation" 2

    try {
        $bicepVersion = az bicep version 2>$null
        if ($bicepVersion) {
            Write-Pass "Bicep CLI installed (version: $bicepVersion)"
            Write-Detail "Bicep is installed via Azure CLI"

            # Check if upgrade is available
            $upgradeCheck = az bicep version 2>&1
            if ($upgradeCheck -match "new Bicep release") {
                Write-Warn "A new Bicep version is available. Consider running: az bicep upgrade"
            }
        } else {
            Write-Fail "Bicep CLI is not installed" -Critical
            Write-Info "Install with: az bicep install"
        }
    } catch {
        Write-Fail "Bicep CLI check failed: $_" -Critical
    }
}

function Test-AzureAuthentication {
    Write-SectionHeader "Azure Authentication" 3

    if ($SkipAzureLogin) {
        Write-Info "Skipping Azure login check (SkipAzureLogin flag set)"
        return
    }

    try {
        $account = az account show 2>$null | ConvertFrom-Json

        if ($account) {
            Write-Pass "Logged in to Azure"
            Write-Detail "Account: $($account.user.name)"
            Write-Detail "Subscription: $($account.name) ($($account.id))"
            Write-Detail "Tenant: $($account.tenantId)"

            # Check if subscription is active
            if ($account.state -eq "Enabled") {
                Write-Pass "Subscription is active"
            } else {
                Write-Fail "Subscription is not active (state: $($account.state))" -Critical
            }
        } else {
            Write-Fail "Not logged in to Azure" -Critical
            Write-Info "Login with: az login"
        }
    } catch {
        Write-Fail "Azure authentication check failed: $_" -Critical
    }
}

function Test-AzurePermissions {
    Write-SectionHeader "Azure Permissions" 4

    try {
        $account = az account show 2>$null | ConvertFrom-Json
        if (-not $account) {
            Write-Fail "Cannot check permissions - not logged in" -Critical
            return
        }

        # Check if user has required permissions at subscription level
        $subscriptionId = $account.id
        $roleAssignments = az role assignment list --scope "/subscriptions/$subscriptionId" --query "[?principalName=='$($account.user.name)']" 2>$null | ConvertFrom-Json

        if ($roleAssignments) {
            $hasContributor = $roleAssignments | Where-Object { $_.roleDefinitionName -in @('Owner', 'Contributor') }

            if ($hasContributor) {
                Write-Pass "User has sufficient permissions (Owner or Contributor)"
                Write-Detail "Role: $($hasContributor[0].roleDefinitionName)"
            } else {
                Write-Warn "User may not have sufficient permissions. Required: Owner or Contributor"
                Write-Detail "Current roles: $($roleAssignments.roleDefinitionName -join ', ')"
            }
        } else {
            Write-Warn "Unable to verify permissions at subscription level"
        }
    } catch {
        Write-Warn "Permission check failed (non-critical): $_"
    }
}

function Test-BicepTemplates {
    Write-SectionHeader "Bicep Template Validation" 5

    # Check if main.bicep exists
    if (-not (Test-Path $MainBicepFile)) {
        Write-Fail "Main Bicep template not found: $MainBicepFile" -Critical
        return
    }
    Write-Pass "Main Bicep template found"

    # Check if parameter file exists
    if (-not (Test-Path $ParameterFile)) {
        Write-Fail "Parameter file not found: $ParameterFile" -Critical
        return
    }
    Write-Pass "Parameter file found for environment: $Environment"

    # Compile Bicep template
    try {
        Write-Info "Compiling Bicep template..."
        $buildOutput = az bicep build --file $MainBicepFile 2>&1

        # Check for errors (warnings are acceptable)
        $errors = $buildOutput | Where-Object { $_ -match "Error" }

        if ($errors) {
            Write-Fail "Bicep compilation failed with errors" -Critical
            $errors | ForEach-Object { Write-Detail $_ }
        } else {
            Write-Pass "Bicep template compiled successfully"

            # Check for warnings
            $warnings = $buildOutput | Where-Object { $_ -match "Warning" }
            if ($warnings) {
                Write-Warn "Bicep compilation has $($warnings.Count) warnings"
                if ($Verbose) {
                    $warnings | ForEach-Object { Write-Detail $_ }
                }
            } else {
                Write-Pass "No compilation warnings"
            }
        }
    } catch {
        Write-Fail "Bicep compilation check failed: $_" -Critical
    }

    # Validate parameter file structure
    try {
        $params = Get-Content $ParameterFile -Raw | ConvertFrom-Json

        if ($params.parameters) {
            Write-Pass "Parameter file has valid structure"

            # Check for placeholder values
            $placeholders = @()
            foreach ($param in $params.parameters.PSObject.Properties) {
                $value = $param.Value.value
                if ($value -match "YOUR_|REPLACE_|CHANGE_|TODO") {
                    $placeholders += $param.Name
                }
            }

            if ($placeholders) {
                Write-Fail "Parameter file contains placeholder values: $($placeholders -join ', ')" -Critical
                Write-Info "Update $ParameterFile with actual values"
            } else {
                Write-Pass "No placeholder values detected in parameters"
            }
        } else {
            Write-Fail "Parameter file has invalid structure" -Critical
        }
    } catch {
        Write-Fail "Parameter file validation failed: $_" -Critical
    }
}

function Test-GitHubSecrets {
    Write-SectionHeader "GitHub Secrets Configuration" 6

    $requiredSecrets = @(
        'AZURE_CLIENT_ID',
        'AZURE_CLIENT_SECRET',
        'AZURE_TENANT_ID',
        'AZURE_SUBSCRIPTION_ID',
        'DJANGO_SECRET_KEY',
        'DATABASE_PASSWORD'
    )

    Write-Info "Required GitHub Secrets for deployment:"
    foreach ($secret in $requiredSecrets) {
        Write-Detail "• $secret"
    }

    # Check if GitHub CLI is available
    $ghCommand = Get-Command gh -ErrorAction SilentlyContinue
    if ($ghCommand) {
        Write-Pass "GitHub CLI is installed"

        try {
            # Try to check if we're in a repo and authenticated
            $repoCheck = gh repo view 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Pass "GitHub CLI is authenticated and in repository"

                # Try to list secrets (requires admin permissions)
                Write-Info "To verify secrets are configured, run: gh secret list"
            } else {
                Write-Warn "GitHub CLI not authenticated or not in repository"
                Write-Info "Authenticate with: gh auth login"
            }
        } catch {
            Write-Warn "Cannot verify GitHub secrets automatically"
        }
    } else {
        Write-Warn "GitHub CLI not installed - cannot verify secrets automatically"
        Write-Info "Install from: https://cli.github.com/"
        Write-Info "Verify secrets manually at: https://github.com/[your-repo]/settings/secrets/actions"
    }
}

function Test-EnvironmentVariables {
    Write-SectionHeader "Environment Variables" 7

    $envFile = Join-Path $ProjectRoot ".env.example"

    if (Test-Path $envFile) {
        Write-Pass ".env.example file found"

        try {
            $envContent = Get-Content $envFile
            $requiredVars = $envContent | Where-Object { $_ -match "^[A-Z_]+=.*$" } | ForEach-Object {
                ($_ -split '=')[0]
            }

            Write-Info "Required environment variables: $($requiredVars.Count)"
            if ($Verbose) {
                $requiredVars | ForEach-Object { Write-Detail $_ }
            }
        } catch {
            Write-Warn "Could not parse .env.example: $_"
        }
    } else {
        Write-Warn ".env.example file not found"
    }

    # Check for actual .env file (should not exist in repo)
    $prodEnvFile = Join-Path $ProjectRoot ".env"
    if (Test-Path $prodEnvFile) {
        Write-Warn ".env file exists in project root - ensure it's in .gitignore"
    } else {
        Write-Pass ".env file not in project root (good - values should be in Azure)"
    }
}

function Test-DockerSetup {
    Write-SectionHeader "Docker Configuration" 8

    # Check Docker installation
    $dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
    if ($dockerCommand) {
        Write-Pass "Docker is installed"

        try {
            $dockerVersion = docker --version
            Write-Detail $dockerVersion

            # Check if Docker is running
            $dockerRunning = docker ps 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Pass "Docker daemon is running"
            } else {
                Write-Warn "Docker daemon is not running - start Docker Desktop"
            }
        } catch {
            Write-Warn "Docker check failed: $_"
        }
    } else {
        Write-Warn "Docker is not installed - required for local testing"
        Write-Info "Install Docker Desktop from: https://www.docker.com/products/docker-desktop/"
    }

    # Check for Dockerfiles
    $backendDockerfile = Join-Path $ProjectRoot "Dockerfile.prod"
    $frontendDockerfile = Join-Path $ProjectRoot "frontend\Dockerfile.prod"

    if (Test-Path $backendDockerfile) {
        Write-Pass "Backend production Dockerfile found"
    } else {
        Write-Warn "Backend production Dockerfile not found: $backendDockerfile"
    }

    if (Test-Path $frontendDockerfile) {
        Write-Pass "Frontend production Dockerfile found"
    } else {
        Write-Warn "Frontend production Dockerfile not found: $frontendDockerfile"
    }
}

function Test-ProjectStructure {
    Write-SectionHeader "Project Structure" 9

    $criticalPaths = @{
        "Backend Directory" = "azure_advisor_reports"
        "Frontend Directory" = "frontend"
        "Scripts Directory" = "scripts"
        "Backend Requirements" = "azure_advisor_reports\requirements.txt"
        "Frontend Package.json" = "frontend\package.json"
        "Django Settings" = "azure_advisor_reports\azure_advisor_reports\settings"
    }

    foreach ($item in $criticalPaths.GetEnumerator()) {
        $path = Join-Path $ProjectRoot $item.Value
        if (Test-Path $path) {
            Write-Pass "$($item.Key) exists"
        } else {
            Write-Fail "$($item.Key) not found: $path" -Critical
        }
    }
}

function Test-DeploymentScripts {
    Write-SectionHeader "Deployment Scripts" 10

    $requiredScripts = @{
        "Azure Deployment Script" = "scripts\azure\deploy.ps1"
        "Pre-deployment Check" = "scripts\pre-deployment-check.ps1"
        "Post-deployment Verify" = "scripts\post-deployment-verify.ps1"
        "Service Principal Setup" = "scripts\setup-service-principal.ps1"
        "Azure AD Setup" = "scripts\setup-azure-ad.ps1"
    }

    foreach ($item in $requiredScripts.GetEnumerator()) {
        $path = Join-Path $ProjectRoot $item.Value
        if (Test-Path $path) {
            Write-Pass "$($item.Key) exists"
        } else {
            Write-Warn "$($item.Key) not found: $path"
        }
    }
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

function Show-Summary {
    Write-Header "VALIDATION SUMMARY"

    $totalChecks = $script:ChecksPassed + $script:ChecksFailed + $script:ChecksWarning

    Write-Host "  Total Checks Run:    $totalChecks" -ForegroundColor Cyan
    Write-Host "  ✅ Passed:           $script:ChecksPassed" -ForegroundColor Green
    Write-Host "  ⚠️  Warnings:         $script:ChecksWarning" -ForegroundColor Yellow
    Write-Host "  ❌ Failed:           $script:ChecksFailed" -ForegroundColor Red
    Write-Host ""

    if ($script:CriticalFailed) {
        Write-Host "═══════════════════════════════════════════════════════════════════════" -ForegroundColor Red
        Write-Host "  ❌ CRITICAL FAILURES DETECTED" -ForegroundColor Red
        Write-Host "  Status: NOT READY FOR DEPLOYMENT" -ForegroundColor Red
        Write-Host "═══════════════════════════════════════════════════════════════════════" -ForegroundColor Red
        Write-Host ""
        Write-Host "  Action Required:" -ForegroundColor Yellow
        Write-Host "  1. Review and fix all critical failures above" -ForegroundColor Yellow
        Write-Host "  2. Re-run this validation script" -ForegroundColor Yellow
        Write-Host "  3. Proceed with deployment only after all critical issues are resolved" -ForegroundColor Yellow
        Write-Host ""
        return 1
    } elseif ($script:ChecksFailed -gt 0) {
        Write-Host "═══════════════════════════════════════════════════════════════════════" -ForegroundColor Yellow
        Write-Host "  ⚠️  FAILURES DETECTED (Non-Critical)" -ForegroundColor Yellow
        Write-Host "  Status: MANUAL REVIEW REQUIRED" -ForegroundColor Yellow
        Write-Host "═══════════════════════════════════════════════════════════════════════" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Review all failed checks and determine if they can be safely ignored." -ForegroundColor Yellow
        Write-Host ""
        return 2
    } elseif ($script:ChecksWarning -gt 0) {
        Write-Host "═══════════════════════════════════════════════════════════════════════" -ForegroundColor Yellow
        Write-Host "  ⚠️  WARNINGS DETECTED" -ForegroundColor Yellow
        Write-Host "  Status: READY FOR DEPLOYMENT (with warnings)" -ForegroundColor Yellow
        Write-Host "═══════════════════════════════════════════════════════════════════════" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Review warnings and proceed with caution." -ForegroundColor Yellow
        Write-Host ""
        return 0
    } else {
        Write-Host "═══════════════════════════════════════════════════════════════════════" -ForegroundColor Green
        Write-Host "  ✅ ALL CHECKS PASSED" -ForegroundColor Green
        Write-Host "  Status: READY FOR DEPLOYMENT" -ForegroundColor Green
        Write-Host "═══════════════════════════════════════════════════════════════════════" -ForegroundColor Green
        Write-Host ""
        Write-Host "  Next Steps:" -ForegroundColor Cyan
        Write-Host "  1. Deploy to $Environment environment" -ForegroundColor Cyan
        Write-Host "     .\scripts\deploy-$Environment.ps1" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  2. Verify deployment" -ForegroundColor Cyan
        Write-Host "     .\scripts\post-deployment-verify.ps1 -Environment $Environment" -ForegroundColor Gray
        Write-Host ""
        return 0
    }
}

# Main script execution
try {
    $startTime = Get-Date

    Write-Header "Azure Advisor Reports - Production Readiness Validation"
    Write-Host "  Environment: $Environment" -ForegroundColor Cyan
    Write-Host "  Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
    Write-Host ""

    # Run all validation checks
    Test-AzureCLI
    Test-BicepCLI
    Test-AzureAuthentication
    Test-AzurePermissions
    Test-BicepTemplates
    Test-GitHubSecrets
    Test-EnvironmentVariables
    Test-DockerSetup
    Test-ProjectStructure
    Test-DeploymentScripts

    # Show summary and exit with appropriate code
    $endTime = Get-Date
    $duration = $endTime - $startTime

    Write-Host ""
    Write-Host "  Validation completed in $($duration.TotalSeconds.ToString('F2')) seconds" -ForegroundColor Cyan

    $exitCode = Show-Summary
    exit $exitCode

} catch {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host "  ❌ VALIDATION SCRIPT ERROR" -ForegroundColor Red
    Write-Host "═══════════════════════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Error: $_" -ForegroundColor Red
    Write-Host "  Stack Trace: $($_.ScriptStackTrace)" -ForegroundColor Gray
    Write-Host ""
    exit 1
}
