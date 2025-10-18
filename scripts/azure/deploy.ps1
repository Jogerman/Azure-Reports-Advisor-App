<#
.SYNOPSIS
    Azure Advisor Reports Platform - Production Deployment Script

.DESCRIPTION
    Comprehensive deployment automation for Azure infrastructure using Bicep templates.
    Handles parameter validation, resource provisioning, and output management.

.PARAMETER Environment
    Target environment: dev, staging, or prod

.PARAMETER Location
    Azure region for deployment (default: eastus2)

.PARAMETER ResourceGroupPrefix
    Resource group name prefix (default: rg-azure-advisor)

.PARAMETER SkipValidation
    Skip pre-deployment validation checks

.PARAMETER WhatIf
    Preview changes without deploying

.PARAMETER Force
    Skip confirmation prompts

.EXAMPLE
    .\deploy.ps1 -Environment prod -Location eastus2

.EXAMPLE
    .\deploy.ps1 -Environment dev -WhatIf

.NOTES
    Version: 1.0
    Author: Azure Advisor Reports Team
    Last Updated: October 3, 2025
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment,

    [Parameter(Mandatory = $false)]
    [string]$Location = 'eastus2',

    [Parameter(Mandatory = $false)]
    [string]$ResourceGroupPrefix = 'rg-azure-advisor',

    [Parameter(Mandatory = $false)]
    [string]$AppNamePrefix = 'azure-advisor',

    [Parameter(Mandatory = $false)]
    [switch]$SkipValidation,

    [Parameter(Mandatory = $false)]
    [switch]$WhatIf,

    [Parameter(Mandatory = $false)]
    [switch]$Force
)

# ============================================================================
# SCRIPT CONFIGURATION
# ============================================================================

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

# Script paths
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BicepRoot = Join-Path $ScriptRoot "bicep"
$MainBicepFile = Join-Path $BicepRoot "main.bicep"
$OutputDir = Join-Path $ScriptRoot "outputs"
$LogDir = Join-Path $ScriptRoot "logs"

# Deployment configuration
$DeploymentName = "azure-advisor-$Environment-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$ResourceGroupName = "$ResourceGroupPrefix-$Environment"

# Create output directories
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# Setup logging
$LogFile = Join-Path $LogDir "deployment-$Environment-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

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
        'Success' { Write-Host $Message -ForegroundColor Green }
        'Warning' { Write-Host $Message -ForegroundColor Yellow }
        'Error'   { Write-Host $Message -ForegroundColor Red }
        default   { Write-Host $Message -ForegroundColor Cyan }
    }
}

function Write-Section {
    param([string]$Title)
    Write-Host "`n============================================================================" -ForegroundColor Magenta
    Write-Host " $Title" -ForegroundColor Magenta
    Write-Host "============================================================================`n" -ForegroundColor Magenta
}

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

function Test-Prerequisites {
    Write-Section "Checking Prerequisites"

    $errors = @()

    # Check Azure CLI
    Write-Log "Checking Azure CLI installation..."
    try {
        $azVersion = az version --query '\"azure-cli\"' -o tsv 2>$null
        if ($azVersion) {
            Write-Log "✓ Azure CLI version: $azVersion" -Level Success
        } else {
            $errors += "Azure CLI is not installed or not in PATH"
        }
    } catch {
        $errors += "Azure CLI check failed: $_"
    }

    # Check Bicep
    Write-Log "Checking Bicep installation..."
    try {
        $bicepVersion = az bicep version 2>$null
        if ($bicepVersion) {
            Write-Log "✓ Bicep version: $bicepVersion" -Level Success
        } else {
            $errors += "Bicep is not installed"
        }
    } catch {
        $errors += "Bicep check failed: $_"
    }

    # Check Azure login
    Write-Log "Checking Azure authentication..."
    try {
        $account = az account show 2>$null | ConvertFrom-Json
        if ($account) {
            Write-Log "✓ Logged in as: $($account.user.name)" -Level Success
            Write-Log "✓ Subscription: $($account.name) ($($account.id))" -Level Success
        } else {
            $errors += "Not logged in to Azure. Run 'az login' first."
        }
    } catch {
        $errors += "Azure authentication check failed: $_"
    }

    # Check Bicep files exist
    Write-Log "Checking Bicep template files..."
    if (-not (Test-Path $MainBicepFile)) {
        $errors += "Main Bicep file not found: $MainBicepFile"
    } else {
        Write-Log "✓ Main Bicep template found" -Level Success
    }

    $moduleFiles = @(
        "modules/infrastructure.bicep",
        "modules/security.bicep",
        "modules/networking.bicep"
    )

    foreach ($module in $moduleFiles) {
        $modulePath = Join-Path $BicepRoot $module
        if (-not (Test-Path $modulePath)) {
            $errors += "Module not found: $modulePath"
        } else {
            Write-Log "✓ Module found: $module" -Level Success
        }
    }

    if ($errors.Count -gt 0) {
        Write-Log "Prerequisites check failed:" -Level Error
        $errors | ForEach-Object { Write-Log "  - $_" -Level Error }
        throw "Prerequisites not met. Please fix the errors above."
    }

    Write-Log "✓ All prerequisites met" -Level Success
}

function Get-DeploymentParameters {
    Write-Section "Gathering Deployment Parameters"

    # Check for parameter file
    $parameterFile = Join-Path $BicepRoot "parameters.$Environment.json"

    if (Test-Path $parameterFile) {
        Write-Log "Found parameter file: $parameterFile" -Level Success
        return @{
            ParameterFile = $parameterFile
        }
    }

    # Interactive parameter collection
    Write-Log "Parameter file not found. Collecting parameters interactively..." -Level Warning

    $params = @{}

    # Azure AD parameters
    Write-Host "`nAzure AD Configuration:" -ForegroundColor Yellow

    $azureAdClientId = Read-Host "Enter Azure AD Client ID (App Registration)"
    if ([string]::IsNullOrWhiteSpace($azureAdClientId)) {
        throw "Azure AD Client ID is required"
    }
    $params['azureAdClientId'] = $azureAdClientId

    $azureAdTenantId = Read-Host "Enter Azure AD Tenant ID"
    if ([string]::IsNullOrWhiteSpace($azureAdTenantId)) {
        throw "Azure AD Tenant ID is required"
    }
    $params['azureAdTenantId'] = $azureAdTenantId

    $azureAdClientSecret = Read-Host "Enter Azure AD Client Secret" -AsSecureString
    $params['azureAdClientSecret'] = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($azureAdClientSecret)
    )

    # Optional parameters
    Write-Host "`nOptional Configuration:" -ForegroundColor Yellow

    $customDomain = Read-Host "Enter custom domain (leave empty to skip)"
    if (-not [string]::IsNullOrWhiteSpace($customDomain)) {
        $params['customDomain'] = $customDomain
    }

    $enableFrontDoor = Read-Host "Enable Azure Front Door? (y/n, default: y)"
    $params['enableFrontDoor'] = ($enableFrontDoor -ne 'n')

    $enableAppInsights = Read-Host "Enable Application Insights? (y/n, default: y)"
    $params['enableAppInsights'] = ($enableAppInsights -ne 'n')

    return @{
        Parameters = $params
    }
}

# ============================================================================
# DEPLOYMENT FUNCTIONS
# ============================================================================

function Invoke-BicepValidation {
    Write-Section "Validating Bicep Templates"

    Write-Log "Building Bicep template..."
    try {
        az bicep build --file $MainBicepFile 2>&1 | Out-Null
        Write-Log "✓ Bicep template is valid" -Level Success
    } catch {
        Write-Log "Bicep validation failed: $_" -Level Error
        throw
    }
}

function Invoke-WhatIfAnalysis {
    param($Parameters)

    Write-Section "Running What-If Analysis"

    Write-Log "Analyzing deployment changes..."

    try {
        $whatIfArgs = @(
            "deployment", "sub", "what-if",
            "--location", $Location,
            "--template-file", $MainBicepFile,
            "--parameters", "environment=$Environment",
            "--parameters", "location=$Location",
            "--parameters", "resourceGroupPrefix=$ResourceGroupPrefix",
            "--parameters", "appNamePrefix=$AppNamePrefix"
        )

        if ($Parameters.ParameterFile) {
            $whatIfArgs += @("--parameters", $Parameters.ParameterFile)
        } elseif ($Parameters.Parameters) {
            foreach ($key in $Parameters.Parameters.Keys) {
                $value = $Parameters.Parameters[$key]
                if ($key -eq 'azureAdClientSecret') {
                    $whatIfArgs += @("--parameters", "$key=$value")
                } else {
                    $whatIfArgs += @("--parameters", "$key=$value")
                }
            }
        }

        $whatIfOutput = & az @whatIfArgs

        Write-Host $whatIfOutput

        Write-Log "What-If analysis completed" -Level Success
    } catch {
        Write-Log "What-If analysis failed: $_" -Level Error
        throw
    }
}

function Invoke-Deployment {
    param($Parameters)

    Write-Section "Deploying Infrastructure"

    # Confirmation prompt
    if (-not $Force -and -not $WhatIf) {
        Write-Host "`nDeployment Configuration:" -ForegroundColor Yellow
        Write-Host "  Environment:      $Environment"
        Write-Host "  Location:         $Location"
        Write-Host "  Resource Group:   $ResourceGroupName"
        Write-Host "  Deployment Name:  $DeploymentName"
        Write-Host ""

        $confirm = Read-Host "Proceed with deployment? (yes/no)"
        if ($confirm -ne 'yes') {
            Write-Log "Deployment cancelled by user" -Level Warning
            return $null
        }
    }

    if ($WhatIf) {
        Write-Log "What-If mode enabled. Skipping actual deployment." -Level Warning
        return $null
    }

    Write-Log "Starting deployment..."

    try {
        $deployArgs = @(
            "deployment", "sub", "create",
            "--location", $Location,
            "--name", $DeploymentName,
            "--template-file", $MainBicepFile,
            "--parameters", "environment=$Environment",
            "--parameters", "location=$Location",
            "--parameters", "resourceGroupPrefix=$ResourceGroupPrefix",
            "--parameters", "appNamePrefix=$AppNamePrefix"
        )

        if ($Parameters.ParameterFile) {
            $deployArgs += @("--parameters", $Parameters.ParameterFile)
        } elseif ($Parameters.Parameters) {
            foreach ($key in $Parameters.Parameters.Keys) {
                $value = $Parameters.Parameters[$key]
                $deployArgs += @("--parameters", "$key=$value")
            }
        }

        Write-Log "Executing deployment command..."
        Write-Log "Deployment name: $DeploymentName"

        $deploymentOutput = & az @deployArgs | ConvertFrom-Json

        if ($deploymentOutput.properties.provisioningState -eq 'Succeeded') {
            Write-Log "✓ Deployment completed successfully" -Level Success
            return $deploymentOutput
        } else {
            throw "Deployment failed with state: $($deploymentOutput.properties.provisioningState)"
        }

    } catch {
        Write-Log "Deployment failed: $_" -Level Error

        # Get deployment error details
        Write-Log "Fetching deployment error details..." -Level Warning
        try {
            $errorDetails = az deployment sub show `
                --name $DeploymentName `
                --query 'properties.error' 2>$null | ConvertFrom-Json

            if ($errorDetails) {
                Write-Log "Error Details:" -Level Error
                Write-Log "  Code: $($errorDetails.code)" -Level Error
                Write-Log "  Message: $($errorDetails.message)" -Level Error
            }
        } catch {
            # Ignore errors in error retrieval
        }

        throw
    }
}

function Get-DeploymentOutputs {
    param($DeploymentName)

    Write-Section "Retrieving Deployment Outputs"

    try {
        Write-Log "Fetching deployment outputs..."

        $outputs = az deployment sub show `
            --name $DeploymentName `
            --query 'properties.outputs' | ConvertFrom-Json

        if ($outputs) {
            Write-Log "✓ Deployment outputs retrieved" -Level Success

            # Save outputs to file
            $outputFile = Join-Path $OutputDir "deployment-outputs-$Environment-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
            $outputs | ConvertTo-Json -Depth 10 | Set-Content -Path $outputFile
            Write-Log "✓ Outputs saved to: $outputFile" -Level Success

            # Display key outputs
            Write-Host "`nDeployment Outputs:" -ForegroundColor Green
            Write-Host "===================" -ForegroundColor Green

            if ($outputs.resourceGroupName) {
                Write-Host "Resource Group:        $($outputs.resourceGroupName.value)"
            }
            if ($outputs.appServiceBackendUrl) {
                Write-Host "Backend URL:           $($outputs.appServiceBackendUrl.value)"
            }
            if ($outputs.appServiceFrontendUrl) {
                Write-Host "Frontend URL:          $($outputs.appServiceFrontendUrl.value)"
            }
            if ($outputs.frontDoorEndpoint) {
                Write-Host "Front Door Endpoint:   $($outputs.frontDoorEndpoint.value)"
            }
            if ($outputs.keyVaultName) {
                Write-Host "Key Vault:             $($outputs.keyVaultName.value)"
            }
            if ($outputs.postgreSqlServerName) {
                Write-Host "PostgreSQL Server:     $($outputs.postgreSqlServerName.value)"
            }
            if ($outputs.redisName) {
                Write-Host "Redis Cache:           $($outputs.redisName.value)"
            }
            if ($outputs.storageAccountName) {
                Write-Host "Storage Account:       $($outputs.storageAccountName.value)"
            }

            Write-Host ""

            return $outputs
        } else {
            Write-Log "No outputs found" -Level Warning
            return $null
        }

    } catch {
        Write-Log "Failed to retrieve outputs: $_" -Level Error
        return $null
    }
}

function Save-ConnectionStrings {
    param($Outputs)

    Write-Section "Saving Connection Strings"

    if (-not $Outputs) {
        Write-Log "No outputs available to save" -Level Warning
        return
    }

    try {
        $connectionStrings = @{}

        if ($Outputs.postgreSqlConnectionString) {
            $connectionStrings['DATABASE_URL'] = $Outputs.postgreSqlConnectionString.value
        }
        if ($Outputs.redisConnectionString) {
            $connectionStrings['REDIS_URL'] = $Outputs.redisConnectionString.value
        }
        if ($Outputs.storageAccountConnectionString) {
            $connectionStrings['AZURE_STORAGE_CONNECTION_STRING'] = $Outputs.storageAccountConnectionString.value
        }
        if ($Outputs.appInsightsConnectionString) {
            $connectionStrings['APPLICATIONINSIGHTS_CONNECTION_STRING'] = $Outputs.appInsightsConnectionString.value
        }

        if ($connectionStrings.Count -gt 0) {
            $envFile = Join-Path $OutputDir ".env.$Environment"

            $envContent = @"
# Azure Advisor Reports Platform
# Environment: $Environment
# Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

# Database
DATABASE_URL=$($connectionStrings['DATABASE_URL'])

# Cache
REDIS_URL=$($connectionStrings['REDIS_URL'])

# Storage
AZURE_STORAGE_CONNECTION_STRING=$($connectionStrings['AZURE_STORAGE_CONNECTION_STRING'])

# Monitoring
APPLICATIONINSIGHTS_CONNECTION_STRING=$($connectionStrings['APPLICATIONINSIGHTS_CONNECTION_STRING'])

# Azure AD (Add your values)
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_TENANT_ID=

# Django Settings
SECRET_KEY=<GENERATE_STRONG_SECRET_KEY>
DEBUG=False
ALLOWED_HOSTS=$($Outputs.appServiceBackendUrl.value -replace 'https://', '')

# CORS
CORS_ALLOWED_ORIGINS=$($Outputs.appServiceFrontendUrl.value)

# Frontend Settings (for React)
REACT_APP_API_URL=$($Outputs.appServiceBackendUrl.value)
REACT_APP_AZURE_CLIENT_ID=
REACT_APP_AZURE_TENANT_ID=
REACT_APP_AZURE_REDIRECT_URI=$($Outputs.appServiceFrontendUrl.value)
"@

            $envContent | Set-Content -Path $envFile
            Write-Log "✓ Environment file saved to: $envFile" -Level Success
            Write-Log "⚠️  IMPORTANT: Update Azure AD credentials in the .env file" -Level Warning
        }

    } catch {
        Write-Log "Failed to save connection strings: $_" -Level Error
    }
}

# ============================================================================
# POST-DEPLOYMENT CONFIGURATION
# ============================================================================

function Invoke-PostDeploymentConfig {
    param($Outputs)

    Write-Section "Post-Deployment Configuration"

    if (-not $Outputs) {
        Write-Log "Skipping post-deployment configuration (no outputs)" -Level Warning
        return
    }

    # Configure App Service settings
    if ($Outputs.appServiceBackendName -and $Outputs.postgreSqlConnectionString) {
        Write-Log "Configuring backend App Service settings..."

        try {
            $backendName = $Outputs.appServiceBackendName.value
            $rgName = $Outputs.resourceGroupName.value

            az webapp config appsettings set `
                --name $backendName `
                --resource-group $rgName `
                --settings "DATABASE_URL=$($Outputs.postgreSqlConnectionString.value)" `
                            "REDIS_URL=$($Outputs.redisConnectionString.value)" `
                            "AZURE_STORAGE_CONNECTION_STRING=$($Outputs.storageAccountConnectionString.value)" `
                            "APPLICATIONINSIGHTS_CONNECTION_STRING=$($Outputs.appInsightsConnectionString.value)" `
                            "PYTHON_VERSION=3.11" `
                            "SCM_DO_BUILD_DURING_DEPLOYMENT=true" | Out-Null

            Write-Log "✓ Backend App Service configured" -Level Success
        } catch {
            Write-Log "Failed to configure backend App Service: $_" -Level Error
        }
    }

    # Configure CORS for storage account
    if ($Outputs.storageAccountName -and $Outputs.appServiceFrontendUrl) {
        Write-Log "Configuring Storage Account CORS..."

        try {
            $storageName = $Outputs.storageAccountName.value
            $frontendUrl = $Outputs.appServiceFrontendUrl.value

            az storage cors add `
                --account-name $storageName `
                --services b `
                --methods GET POST PUT `
                --origins $frontendUrl `
                --allowed-headers '*' `
                --max-age 3600 2>$null | Out-Null

            Write-Log "✓ Storage Account CORS configured" -Level Success
        } catch {
            Write-Log "Failed to configure Storage CORS: $_" -Level Warning
        }
    }
}

# ============================================================================
# ROLLBACK FUNCTIONS
# ============================================================================

function Invoke-Rollback {
    param($DeploymentName)

    Write-Section "Deployment Rollback"

    Write-Log "Initiating rollback for deployment: $DeploymentName" -Level Warning

    try {
        # Delete the resource group if it was created
        $confirm = Read-Host "Delete resource group '$ResourceGroupName'? (yes/no)"

        if ($confirm -eq 'yes') {
            Write-Log "Deleting resource group..."

            az group delete `
                --name $ResourceGroupName `
                --yes `
                --no-wait

            Write-Log "✓ Resource group deletion initiated" -Level Success
            Write-Log "Deletion is running in the background. Check Azure Portal for status." -Level Warning
        } else {
            Write-Log "Rollback cancelled" -Level Warning
        }

    } catch {
        Write-Log "Rollback failed: $_" -Level Error
    }
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

function Main {
    try {
        Write-Host @"

╔══════════════════════════════════════════════════════════════════╗
║     Azure Advisor Reports Platform - Deployment Script          ║
║                                                                  ║
║     Environment: $Environment                                    ║
║     Location:    $Location                                       ║
╚══════════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

        Write-Log "Deployment started at $(Get-Date)"
        Write-Log "Environment: $Environment"
        Write-Log "Location: $Location"
        Write-Log "Log file: $LogFile"

        # Step 1: Prerequisites check
        if (-not $SkipValidation) {
            Test-Prerequisites
        } else {
            Write-Log "Skipping prerequisites validation (as requested)" -Level Warning
        }

        # Step 2: Bicep validation
        if (-not $SkipValidation) {
            Invoke-BicepValidation
        }

        # Step 3: Gather parameters
        $parameters = Get-DeploymentParameters

        # Step 4: What-If analysis
        if (-not $SkipValidation -or $WhatIf) {
            Invoke-WhatIfAnalysis -Parameters $parameters
        }

        if ($WhatIf) {
            Write-Log "What-If mode completed. Exiting." -Level Warning
            return
        }

        # Step 5: Deploy
        $deployment = Invoke-Deployment -Parameters $parameters

        if (-not $deployment) {
            Write-Log "Deployment was cancelled or failed" -Level Warning
            return
        }

        # Step 6: Get outputs
        $outputs = Get-DeploymentOutputs -DeploymentName $DeploymentName

        # Step 7: Save connection strings
        Save-ConnectionStrings -Outputs $outputs

        # Step 8: Post-deployment configuration
        Invoke-PostDeploymentConfig -Outputs $outputs

        # Success summary
        Write-Section "Deployment Complete"

        Write-Log @"
✓ Deployment completed successfully!

Next Steps:
1. Review the deployment outputs above
2. Update .env.$Environment file with Azure AD credentials
3. Configure GitHub Secrets for CI/CD
4. Run database migrations: az webapp ssh --resource-group $ResourceGroupName --name <backend-app> -c 'python manage.py migrate'
5. Create superuser: az webapp ssh --resource-group $ResourceGroupName --name <backend-app> -c 'python manage.py createsuperuser'
6. Verify application health checks

For detailed post-deployment steps, see DEPLOYMENT_RUNBOOK.md
"@ -Level Success

        Write-Log "Deployment completed at $(Get-Date)" -Level Success

    } catch {
        Write-Log "Deployment failed: $_" -Level Error
        Write-Log "Check log file for details: $LogFile" -Level Error

        # Offer rollback
        $rollback = Read-Host "`nWould you like to rollback this deployment? (yes/no)"
        if ($rollback -eq 'yes') {
            Invoke-Rollback -DeploymentName $DeploymentName
        }

        exit 1
    }
}

# Execute main function
Main
