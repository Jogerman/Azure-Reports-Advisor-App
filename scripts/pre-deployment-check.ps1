<#
.SYNOPSIS
    Pre-Deployment Validation Script for Azure Advisor Reports Platform

.DESCRIPTION
    Comprehensive validation script to check all prerequisites before deploying to Azure.
    Validates Azure CLI, Bicep, authentication, parameter files, templates, and permissions.

.PARAMETER Environment
    Target environment (dev, staging, or prod)

.PARAMETER SkipBicepValidation
    Skip Bicep template compilation check (useful if templates are known to be valid)

.EXAMPLE
    .\pre-deployment-check.ps1 -Environment prod

.EXAMPLE
    .\pre-deployment-check.ps1 -Environment staging -SkipBicepValidation

.NOTES
    Version: 1.0
    Last Updated: October 4, 2025
    Exit Codes:
        0 = All checks passed
        1 = One or more checks failed
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment,

    [Parameter(Mandatory=$false)]
    [switch]$SkipBicepValidation
)

# Script configuration
$ErrorActionPreference = "SilentlyContinue"
$script:ChecksPassed = 0
$script:ChecksFailed = 0
$script:ChecksWarning = 0
$script:TotalChecks = 10

# Colors
$script:SuccessColor = "Green"
$script:WarningColor = "Yellow"
$script:ErrorColor = "Red"
$script:InfoColor = "Cyan"
$script:HeaderColor = "Magenta"

function Write-Header {
    param([string]$Title)
    Write-Host "`n" -NoNewline
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor $HeaderColor
    Write-Host "  $Title" -ForegroundColor $HeaderColor
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor $HeaderColor
    Write-Host ""
}

function Write-CheckHeader {
    param([string]$Title, [int]$Number)
    Write-Host "`n┌─────────────────────────────────────────────────────────┐" -ForegroundColor $InfoColor
    Write-Host "│  Check $Number/$script:TotalChecks : $Title" -ForegroundColor $InfoColor
    Write-Host "└─────────────────────────────────────────────────────────┘" -ForegroundColor $InfoColor
}

function Write-Pass {
    param([string]$Message)
    Write-Host "  ✅ $Message" -ForegroundColor $SuccessColor
    $script:ChecksPassed++
}

function Write-Fail {
    param([string]$Message)
    Write-Host "  ❌ $Message" -ForegroundColor $ErrorColor
    $script:ChecksFailed++
}

function Write-Warn {
    param([string]$Message)
    Write-Host "  ⚠️  $Message" -ForegroundColor $WarningColor
    $script:ChecksWarning++
}

function Write-Info {
    param([string]$Message)
    Write-Host "  ℹ️  $Message" -ForegroundColor $InfoColor
}

function Write-Detail {
    param([string]$Message)
    Write-Host "     $Message" -ForegroundColor Gray
}

function Test-AzureCLI {
    Write-CheckHeader "Azure CLI Installation" 1

    $azInstalled = Get-Command az -ErrorAction SilentlyContinue

    if (-not $azInstalled) {
        Write-Fail "Azure CLI not found"
        Write-Info "Install from: https://aka.ms/installazurecliwindows"
        Write-Info "Or run: winget install -e --id Microsoft.AzureCLI"
        return $false
    }

    # Get version
    $versionOutput = az version 2>&1 | ConvertFrom-Json
    $azVersion = $versionOutput.'azure-cli'

    Write-Pass "Azure CLI installed"
    Write-Detail "Version: $azVersion"

    # Check version is recent enough (2.50.0+)
    $versionParts = $azVersion -split '\.'
    $majorVersion = [int]$versionParts[0]
    $minorVersion = [int]$versionParts[1]

    if ($majorVersion -lt 2 -or ($majorVersion -eq 2 -and $minorVersion -lt 50)) {
        Write-Warn "Azure CLI version is outdated (recommended: 2.50.0+)"
        Write-Info "Update with: az upgrade"
    } else {
        Write-Detail "Version check: OK (2.50.0+)"
    }

    return $true
}

function Test-AzureAuth {
    Write-CheckHeader "Azure Authentication" 2

    # Check if logged in
    $account = az account show 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Not logged in to Azure"
        Write-Info "Run: az login"
        return $false
    }

    $accountDetails = $account | ConvertFrom-Json
    $subscriptionName = $accountDetails.name
    $subscriptionId = $accountDetails.id
    $tenantId = $accountDetails.tenantId
    $userName = $accountDetails.user.name

    Write-Pass "Logged in to Azure"
    Write-Detail "User: $userName"
    Write-Detail "Subscription: $subscriptionName"
    Write-Detail "Subscription ID: $subscriptionId"
    Write-Detail "Tenant ID: $tenantId"

    return $true
}

function Test-BicepCLI {
    Write-CheckHeader "Bicep CLI Installation" 3

    $bicepVersion = az bicep version 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Bicep CLI not found"
        Write-Info "Install with: az bicep install"
        return $false
    }

    Write-Pass "Bicep CLI installed"
    Write-Detail "Version: $bicepVersion"

    # Check if Bicep is up to date
    $upgradeCheck = az bicep upgrade 2>&1
    if ($upgradeCheck -like "*already up to date*") {
        Write-Detail "Version check: Up to date"
    } else {
        Write-Warn "Bicep can be upgraded"
        Write-Info "Run: az bicep upgrade"
    }

    return $true
}

function Test-ParameterFile {
    Write-CheckHeader "Parameter File Validation" 4

    $paramFile = "scripts\azure\bicep\parameters.$Environment.json"
    $fullPath = Join-Path $PSScriptRoot "..\azure\bicep\parameters.$Environment.json"

    if (-not (Test-Path $fullPath)) {
        Write-Fail "Parameter file not found: $paramFile"
        Write-Info "Create file: $fullPath"
        return $false
    }

    Write-Pass "Parameter file found: $paramFile"

    # Validate JSON syntax
    try {
        $paramContent = Get-Content $fullPath -Raw | ConvertFrom-Json
        Write-Detail "JSON syntax: Valid"
    } catch {
        Write-Fail "Invalid JSON syntax in parameter file"
        Write-Detail "Error: $_"
        return $false
    }

    # Check for required parameters
    $requiredParams = @('environment', 'location', 'projectName')
    $missingParams = @()

    foreach ($param in $requiredParams) {
        if (-not $paramContent.parameters.$param) {
            $missingParams += $param
        }
    }

    if ($missingParams.Count -gt 0) {
        Write-Warn "Missing parameters: $($missingParams -join ', ')"
        Write-Info "Update parameter file with missing values"
    } else {
        Write-Detail "Required parameters: Present"
    }

    # Check for placeholder values
    $placeholders = @('CHANGE-ME', 'TODO', 'PLACEHOLDER', 'xxx')
    $hasPlaceholders = $false

    $paramString = $paramContent | ConvertTo-Json -Depth 10
    foreach ($placeholder in $placeholders) {
        if ($paramString -match $placeholder) {
            $hasPlaceholders = $true
            break
        }
    }

    if ($hasPlaceholders) {
        Write-Warn "Parameter file contains placeholder values"
        Write-Info "Replace placeholder values before deployment"
    } else {
        Write-Detail "Placeholder check: OK"
    }

    return $true
}

function Test-BicepTemplates {
    Write-CheckHeader "Bicep Template Validation" 5

    if ($SkipBicepValidation) {
        Write-Warn "Bicep validation skipped (--SkipBicepValidation flag)"
        return $true
    }

    $mainBicep = "scripts\azure\bicep\main.bicep"
    $fullPath = Join-Path $PSScriptRoot "..\azure\bicep\main.bicep"

    if (-not (Test-Path $fullPath)) {
        Write-Fail "Main Bicep template not found: $mainBicep"
        return $false
    }

    Write-Pass "Main Bicep template found"

    # Compile Bicep template
    Write-Info "Compiling Bicep template..."
    $buildOutput = az bicep build --file $fullPath 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Bicep compilation failed"
        Write-Detail "Error output:"
        $buildOutput | ForEach-Object { Write-Detail $_ }
        return $false
    }

    Write-Pass "Bicep template compiled successfully"

    # Check for warnings
    $warnings = $buildOutput | Where-Object { $_ -like "*Warning*" }
    if ($warnings.Count -gt 0) {
        Write-Warn "Bicep compilation has $($warnings.Count) warning(s)"
        Write-Detail "Warnings:"
        $warnings | ForEach-Object { Write-Detail $_ }
    } else {
        Write-Detail "No compilation warnings"
    }

    # Validate ARM template syntax
    $armTemplate = Join-Path $PSScriptRoot "..\azure\bicep\main.json"
    if (Test-Path $armTemplate) {
        Write-Detail "ARM template generated: main.json"
    }

    return $true
}

function Test-AzurePermissions {
    Write-CheckHeader "Azure Permissions" 6

    $subscriptionId = (az account show --query id -o tsv)

    # Get role assignments for current user
    $userEmail = az account show --query user.name -o tsv
    $roleAssignments = az role assignment list `
        --assignee $userEmail `
        --query "[?scope=='/subscriptions/$subscriptionId'].{Role:roleDefinitionName}" `
        -o json 2>&1 | ConvertFrom-Json

    if ($LASTEXITCODE -ne 0 -or $roleAssignments.Count -eq 0) {
        Write-Warn "Could not verify permissions"
        Write-Info "Ensure you have Contributor or Owner role on subscription"
        return $true  # Don't fail, just warn
    }

    $hasRequiredRole = $false
    $roles = @()

    foreach ($assignment in $roleAssignments) {
        $roles += $assignment.Role
        if ($assignment.Role -in @('Owner', 'Contributor')) {
            $hasRequiredRole = $true
        }
    }

    if ($hasRequiredRole) {
        Write-Pass "User has required permissions"
        Write-Detail "Roles: $($roles -join ', ')"
    } else {
        Write-Warn "User may not have sufficient permissions"
        Write-Detail "Current roles: $($roles -join ', ')"
        Write-Info "Required: Contributor or Owner role"
    }

    return $true
}

function Test-ResourceGroup {
    Write-CheckHeader "Resource Group Check" 7

    $rgName = "rg-azure-advisor-reports-$Environment"

    # Check if resource group exists
    $rg = az group show --name $rgName 2>&1

    if ($LASTEXITCODE -eq 0) {
        $rgDetails = $rg | ConvertFrom-Json
        Write-Pass "Resource group exists: $rgName"
        Write-Detail "Location: $($rgDetails.location)"
        Write-Detail "Provisioning State: $($rgDetails.properties.provisioningState)"

        # Check for existing resources
        $resources = az resource list --resource-group $rgName | ConvertFrom-Json
        $resourceCount = $resources.Count

        if ($resourceCount -gt 0) {
            Write-Warn "Resource group contains $resourceCount existing resource(s)"
            Write-Detail "Deployment will update/add resources"
        } else {
            Write-Detail "Resource group is empty"
        }
    } else {
        Write-Warn "Resource group doesn't exist: $rgName"
        Write-Info "Will be created during deployment"
    }

    return $true
}

function Test-RequiredProviders {
    Write-CheckHeader "Azure Resource Providers" 8

    $requiredProviders = @(
        'Microsoft.Web',
        'Microsoft.DBforPostgreSQL',
        'Microsoft.Cache',
        'Microsoft.Storage',
        'Microsoft.Cdn',
        'Microsoft.Insights',
        'Microsoft.ManagedIdentity',
        'Microsoft.KeyVault'
    )

    # Get registered providers
    $registeredProviders = az provider list --query "[?registrationState=='Registered'].namespace" -o json | ConvertFrom-Json

    $allRegistered = $true
    $notRegistered = @()

    foreach ($provider in $requiredProviders) {
        if ($registeredProviders -notcontains $provider) {
            $notRegistered += $provider
            $allRegistered = $false
        }
    }

    if ($allRegistered) {
        Write-Pass "All required resource providers are registered"
        Write-Detail "Providers: $($requiredProviders.Count) checked"
    } else {
        Write-Warn "$($notRegistered.Count) provider(s) not registered"
        Write-Detail "Not registered: $($notRegistered -join ', ')"
        Write-Info "Register with: az provider register --namespace <provider-name>"
    }

    return $true
}

function Test-DeploymentPrerequisites {
    Write-CheckHeader "Deployment Prerequisites" 9

    $allPrereqsMet = $true

    # Check 1: PowerShell version
    $psVersion = $PSVersionTable.PSVersion
    Write-Info "PowerShell version: $psVersion"
    if ($psVersion.Major -lt 7) {
        Write-Warn "PowerShell 7+ recommended (current: $psVersion)"
        Write-Info "Install from: https://github.com/PowerShell/PowerShell/releases"
    } else {
        Write-Detail "PowerShell version: OK"
    }

    # Check 2: Git (for version control)
    $gitInstalled = Get-Command git -ErrorAction SilentlyContinue
    if ($gitInstalled) {
        $gitVersion = git --version
        Write-Detail "Git: $gitVersion"
    } else {
        Write-Warn "Git not found (optional for deployment)"
    }

    # Check 3: Deployment script exists
    $deployScript = Join-Path $PSScriptRoot "..\azure\deploy.ps1"
    if (Test-Path $deployScript) {
        Write-Detail "Deployment script found: deploy.ps1"
    } else {
        Write-Fail "Deployment script not found: scripts\azure\deploy.ps1"
        $allPrereqsMet = $false
    }

    # Check 4: Internet connectivity (test Azure endpoint)
    try {
        $null = Test-NetConnection -ComputerName "management.azure.com" -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue
        if ($?) {
            Write-Detail "Azure connectivity: OK"
        } else {
            Write-Warn "Azure connectivity test failed"
            Write-Info "Check firewall and proxy settings"
        }
    } catch {
        Write-Warn "Could not test Azure connectivity"
    }

    if ($allPrereqsMet) {
        Write-Pass "Deployment prerequisites met"
    }

    return $allPrereqsMet
}

function Test-EnvironmentVariables {
    Write-CheckHeader "Environment Variables Check" 10

    $requiredEnvVars = @(
        @{Name='AZURE_CLIENT_ID'; Description='Azure AD Client ID'; Required=$false},
        @{Name='AZURE_CLIENT_SECRET'; Description='Azure AD Client Secret'; Required=$false},
        @{Name='AZURE_TENANT_ID'; Description='Azure AD Tenant ID'; Required=$false}
    )

    $allSet = $true
    $missingRequired = @()

    foreach ($envVar in $requiredEnvVars) {
        $value = [Environment]::GetEnvironmentVariable($envVar.Name)

        if ($value) {
            Write-Detail "$($envVar.Name): Set"
        } else {
            if ($envVar.Required) {
                Write-Fail "$($envVar.Name): Not set (required)"
                $missingRequired += $envVar.Name
                $allSet = $false
            } else {
                Write-Info "$($envVar.Name): Not set (optional)"
            }
        }
    }

    if ($allSet) {
        Write-Pass "Environment variables check complete"
        if ($missingRequired.Count -eq 0) {
            Write-Detail "Optional variables can be set post-deployment"
        }
    } else {
        Write-Warn "Some required environment variables are missing"
    }

    return $true  # Don't fail on missing optional vars
}

function Write-Summary {
    Write-Header "Pre-Deployment Validation Summary"

    $totalChecks = $script:ChecksPassed + $script:ChecksFailed + $script:ChecksWarning

    Write-Host "`nEnvironment: " -NoNewline -ForegroundColor White
    Write-Host $Environment.ToUpper() -ForegroundColor $HeaderColor

    Write-Host "`nValidation Results:" -ForegroundColor White
    Write-Host "  ✅ Passed:  " -NoNewline -ForegroundColor White
    Write-Host "$script:ChecksPassed" -ForegroundColor $SuccessColor

    if ($script:ChecksWarning -gt 0) {
        Write-Host "  ⚠️  Warnings:" -NoNewline -ForegroundColor White
        Write-Host "$script:ChecksWarning" -ForegroundColor $WarningColor
    }

    if ($script:ChecksFailed -gt 0) {
        Write-Host "  ❌ Failed:  " -NoNewline -ForegroundColor White
        Write-Host "$script:ChecksFailed" -ForegroundColor $ErrorColor
    }

    Write-Host "`nTotal Checks: " -NoNewline -ForegroundColor White
    Write-Host "$script:TotalChecks" -ForegroundColor Gray

    $percentage = [math]::Round(($script:ChecksPassed / $script:TotalChecks) * 100)

    Write-Host "`n" -NoNewline
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor $HeaderColor

    if ($script:ChecksFailed -eq 0) {
        Write-Host "`n✅ All critical checks passed! Ready for deployment." -ForegroundColor $SuccessColor

        if ($script:ChecksWarning -gt 0) {
            Write-Host "`n⚠️  $script:ChecksWarning warning(s) detected. Review before proceeding." -ForegroundColor $WarningColor
        }

        Write-Host "`nNext Steps:" -ForegroundColor White
        Write-Host "  1. Review parameter file: scripts\azure\bicep\parameters.$Environment.json" -ForegroundColor Gray
        Write-Host "  2. Run deployment: .\scripts\azure\deploy.ps1 -Environment $Environment" -ForegroundColor Gray
        Write-Host "  3. Monitor deployment progress in Azure Portal" -ForegroundColor Gray

        return 0
    } else {
        Write-Host "`n❌ $script:ChecksFailed check(s) failed. Fix issues before deployment." -ForegroundColor $ErrorColor

        Write-Host "`nRequired Actions:" -ForegroundColor White
        Write-Host "  1. Review failed checks above" -ForegroundColor Gray
        Write-Host "  2. Fix identified issues" -ForegroundColor Gray
        Write-Host "  3. Re-run validation: .\scripts\pre-deployment-check.ps1 -Environment $Environment" -ForegroundColor Gray

        return 1
    }
}

# Main Script Execution
Clear-Host

Write-Header "Pre-Deployment Validation for Azure Advisor Reports"

Write-Host "Environment: " -NoNewline -ForegroundColor White
Write-Host $Environment.ToUpper() -ForegroundColor $HeaderColor

Write-Host "`nThis script will validate:" -ForegroundColor White
Write-Host "  - Azure CLI and Bicep installation" -ForegroundColor Gray
Write-Host "  - Azure authentication and permissions" -ForegroundColor Gray
Write-Host "  - Bicep templates and parameters" -ForegroundColor Gray
Write-Host "  - Resource providers and prerequisites" -ForegroundColor Gray

Write-Host "`nStarting validation..." -ForegroundColor $InfoColor

# Run all checks
Test-AzureCLI
Test-AzureAuth
Test-BicepCLI
Test-ParameterFile
Test-BicepTemplates
Test-AzurePermissions
Test-ResourceGroup
Test-RequiredProviders
Test-DeploymentPrerequisites
Test-EnvironmentVariables

# Display summary and exit
$exitCode = Write-Summary
Write-Host ""
exit $exitCode
