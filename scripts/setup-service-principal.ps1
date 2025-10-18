# Service Principal Creation Script for GitHub Actions
# Azure Advisor Reports Platform - CI/CD Prerequisites
#
# Purpose: Creates Service Principal with proper RBAC for GitHub Actions
# Version: 1.0
# Last Updated: October 5, 2025
# Platform: Windows PowerShell 7+
# Prerequisites: Azure CLI, Owner or User Access Administrator role

#Requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [ValidateSet('dev', 'staging', 'prod', 'all')]
    [string]$Environment = 'all',

    [Parameter(Mandatory = $false)]
    [string]$ServicePrincipalName = 'azure-advisor-github-actions',

    [Parameter(Mandatory = $false)]
    [string]$SubscriptionId = '',

    [Parameter(Mandatory = $false)]
    [string]$ResourceGroupName = '',

    [Parameter(Mandatory = $false)]
    [ValidateSet('Contributor', 'Owner')]
    [string]$Role = 'Contributor',

    [Parameter(Mandatory = $false)]
    [switch]$GrantUserAccessAdministrator,

    [Parameter(Mandatory = $false)]
    [string]$OutputDirectory = 'github-credentials'
)

# Script configuration
$ErrorActionPreference = 'Stop'
$InformationPreference = 'Continue'

# Color helper functions
function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Warning-Custom { param($Message) Write-Host $Message -ForegroundColor Yellow }
function Write-ErrorMessage { param($Message) Write-Host $Message -ForegroundColor Red }
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }
function Write-Step { param($Message) Write-Host "`n=== $Message ===" -ForegroundColor Magenta }

# Main script start
Write-Host "`n" -NoNewline
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Service Principal Creation for GitHub Actions               ║" -ForegroundColor Cyan
Write-Host "║   Azure Advisor Reports Platform                              ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "`n"

# Validate prerequisites
Write-Step "Validating Prerequisites"

# Check Azure CLI
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Success "Azure CLI installed: $($azVersion.'azure-cli')"
} catch {
    Write-ErrorMessage "Azure CLI is not installed or not in PATH"
    Write-Info "Install from: https://aka.ms/installazurecliwindows"
    exit 1
}

# Check Azure login
Write-Info "Checking Azure login status..."
try {
    $account = az account show --output json 2>$null | ConvertFrom-Json
    if (-not $account) {
        Write-Warning-Custom "Not logged in to Azure. Initiating login..."
        az login --output none
        $account = az account show --output json | ConvertFrom-Json
    }
    Write-Success "Logged in as: $($account.user.name)"
    Write-Success "Subscription: $($account.name)"
} catch {
    Write-ErrorMessage "Azure login failed. Please run 'az login' manually."
    exit 1
}

# Get or validate subscription ID
if (-not $SubscriptionId) {
    $SubscriptionId = $account.id
    Write-Info "Using current subscription: $SubscriptionId"
} else {
    Write-Info "Setting subscription to: $SubscriptionId"
    az account set --subscription $SubscriptionId
}

# Check permissions
Write-Info "Checking RBAC permissions..."
try {
    $currentUserId = az ad signed-in-user show --query id -o tsv
    $roleAssignments = az role assignment list --assignee $currentUserId --subscription $SubscriptionId --output json | ConvertFrom-Json

    $hasOwner = $roleAssignments | Where-Object { $_.roleDefinitionName -eq 'Owner' }
    $hasUserAccessAdmin = $roleAssignments | Where-Object { $_.roleDefinitionName -eq 'User Access Administrator' }
    $hasContributor = $roleAssignments | Where-Object { $_.roleDefinitionName -eq 'Contributor' }

    if ($hasOwner) {
        Write-Success "You have Owner role - can create Service Principal and assign roles"
    } elseif ($hasUserAccessAdmin -and $hasContributor) {
        Write-Success "You have User Access Administrator + Contributor - can create Service Principal"
    } else {
        Write-Warning-Custom "You may not have sufficient permissions to create Service Principal"
        Write-Warning-Custom "Required: Owner OR (User Access Administrator + Contributor)"
        Write-Info "Your roles: $($roleAssignments.roleDefinitionName -join ', ')"

        $continue = Read-Host "Do you want to try anyway? (y/N)"
        if ($continue -ne 'y' -and $continue -ne 'Y') {
            exit 0
        }
    }
} catch {
    Write-Warning-Custom "Could not verify permissions. Proceeding anyway..."
}

# Determine scope
if ($ResourceGroupName) {
    $scope = "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroupName"
    Write-Info "Scope: Resource Group ($ResourceGroupName)"
} else {
    $scope = "/subscriptions/$SubscriptionId"
    Write-Info "Scope: Subscription (all resource groups)"
}

# Display configuration
Write-Step "Configuration"
Write-Info "Service Principal Name: $ServicePrincipalName"
Write-Info "Subscription ID: $SubscriptionId"
Write-Info "Subscription Name: $($account.name)"
Write-Info "Scope: $scope"
Write-Info "Primary Role: $Role"
if ($GrantUserAccessAdministrator) {
    Write-Info "Additional Role: User Access Administrator (for RBAC assignments)"
}
Write-Info "Output Directory: $OutputDirectory"
Write-Info "`n"

# Confirm before proceeding
Write-Warning-Custom "This script will create a Service Principal with $Role permissions."
if ($ResourceGroupName) {
    Write-Warning-Custom "Scope: Resource Group '$ResourceGroupName' only"
} else {
    Write-Warning-Custom "Scope: ENTIRE SUBSCRIPTION (all resource groups)"
}

$confirm = Read-Host "Do you want to proceed? (y/N)"
if ($confirm -ne 'y' -and $confirm -ne 'Y') {
    Write-Info "Operation cancelled by user."
    exit 0
}

# Create Service Principal
Write-Step "Creating Service Principal"

try {
    Write-Info "Creating Service Principal: $ServicePrincipalName"

    # Create Service Principal with specified role and scope
    $spJson = az ad sp create-for-rbac `
        --name $ServicePrincipalName `
        --role $Role `
        --scopes $scope `
        --sdk-auth `
        --output json

    if (-not $spJson) {
        throw "Service Principal creation returned empty result"
    }

    $spCredentials = $spJson | ConvertFrom-Json

    Write-Success "Service Principal created successfully!"
    Write-Success "App ID (Client ID): $($spCredentials.clientId)"
    Write-Success "Object ID: $($spCredentials.objectId)"
    Write-Success "Tenant ID: $($spCredentials.tenantId)"

} catch {
    Write-ErrorMessage "Failed to create Service Principal"
    Write-ErrorMessage $_.Exception.Message

    # Check if SP already exists
    if ($_.Exception.Message -match "already exists") {
        Write-Warning-Custom "Service Principal may already exist"

        # Try to find existing SP
        $existingSp = az ad sp list --display-name $ServicePrincipalName --output json | ConvertFrom-Json

        if ($existingSp -and $existingSp.Count -gt 0) {
            Write-Info "Found existing Service Principal:"
            Write-Info "  App ID: $($existingSp[0].appId)"
            Write-Info "  Object ID: $($existingSp[0].id)"

            $useExisting = Read-Host "Do you want to reset credentials for existing SP? (y/N)"
            if ($useExisting -eq 'y' -or $useExisting -eq 'Y') {
                Write-Info "Resetting credentials..."

                # Get app ID
                $appId = $existingSp[0].appId

                # Reset credentials
                $spJson = az ad sp credential reset `
                    --id $appId `
                    --append `
                    --output json

                # Need to manually construct sdk-auth format
                $resetCreds = $spJson | ConvertFrom-Json
                $spCredentials = @{
                    clientId       = $appId
                    clientSecret   = $resetCreds.password
                    subscriptionId = $SubscriptionId
                    tenantId       = $resetCreds.tenant
                    objectId       = $existingSp[0].id
                } | ConvertTo-Json

                $spCredentials = $spCredentials | ConvertFrom-Json
                Write-Success "Credentials reset successfully"
            } else {
                Write-Info "Operation cancelled"
                exit 1
            }
        } else {
            exit 1
        }
    } else {
        exit 1
    }
}

# Add User Access Administrator role if requested
if ($GrantUserAccessAdministrator) {
    Write-Step "Granting User Access Administrator Role"

    try {
        Write-Info "Adding User Access Administrator role for RBAC assignments..."

        az role assignment create `
            --assignee $spCredentials.clientId `
            --role "User Access Administrator" `
            --scope $scope `
            --output none

        Write-Success "User Access Administrator role granted"
        Write-Info "This allows the Service Principal to create role assignments (needed for Bicep deployment)"

    } catch {
        Write-Warning-Custom "Could not grant User Access Administrator role"
        Write-Warning-Custom "You may need to add this role manually if deployment fails"
        Write-Info "Command: az role assignment create --assignee $($spCredentials.clientId) --role 'User Access Administrator' --scope $scope"
    }
}

# Verify role assignments
Write-Step "Verifying Role Assignments"

try {
    Start-Sleep -Seconds 5  # Wait for role propagation

    Write-Info "Checking assigned roles..."
    $assignments = az role assignment list --assignee $spCredentials.clientId --output json | ConvertFrom-Json

    if ($assignments.Count -gt 0) {
        Write-Success "Role assignments verified:"
        foreach ($assignment in $assignments) {
            Write-Info "  - $($assignment.roleDefinitionName) on $($assignment.scope)"
        }
    } else {
        Write-Warning-Custom "No role assignments found (may take a few minutes to propagate)"
    }
} catch {
    Write-Warning-Custom "Could not verify role assignments"
}

# Create output directory
if (-not (Test-Path $OutputDirectory)) {
    New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
    Write-Success "Created output directory: $OutputDirectory"
}

# Save credentials for GitHub Actions
Write-Step "Saving Credentials"

# Format for GitHub Actions (sdk-auth format)
$githubCredentials = @{
    clientId                = $spCredentials.clientId
    clientSecret            = $spCredentials.clientSecret
    subscriptionId          = $SubscriptionId
    tenantId                = $spCredentials.tenantId
    activeDirectoryEndpointUrl = "https://login.microsoftonline.com"
    resourceManagerEndpointUrl = "https://management.azure.com/"
    activeDirectoryGraphResourceId = "https://graph.windows.net/"
    sqlManagementEndpointUrl = "https://management.core.windows.net:8443/"
    galleryEndpointUrl      = "https://gallery.azure.com/"
    managementEndpointUrl   = "https://management.core.windows.net/"
}

# Save environment-specific files
$environments = if ($Environment -eq 'all') { @('dev', 'staging', 'prod') } else { @($Environment) }

foreach ($env in $environments) {
    $filename = "$OutputDirectory/azure-credentials-$env.json"

    $githubCredentials | ConvertTo-Json -Depth 10 | Out-File -FilePath $filename -Encoding UTF8

    Write-Success "Saved credentials for $env environment: $filename"
}

# Create summary file
$summaryFile = "$OutputDirectory/service-principal-summary.txt"
@"
SERVICE PRINCIPAL SUMMARY
==========================
Created: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Created By: $($account.user.name)

SERVICE PRINCIPAL DETAILS
-------------------------
Name: $ServicePrincipalName
App ID (Client ID): $($spCredentials.clientId)
Object ID: $($spCredentials.objectId)
Tenant ID: $($spCredentials.tenantId)
Subscription ID: $SubscriptionId
Subscription Name: $($account.name)

CLIENT SECRET
-------------
IMPORTANT: This is shown only once!
$($spCredentials.clientSecret)

ROLE ASSIGNMENTS
----------------
Primary Role: $Role
Scope: $scope
$(if ($GrantUserAccessAdministrator) { "Additional: User Access Administrator" })

GITHUB SECRETS CONFIGURATION
-----------------------------
Use the following files for GitHub Secrets:

For Development:
  Secret Name: AZURE_CREDENTIALS_DEV
  File: $OutputDirectory/azure-credentials-dev.json

For Staging:
  Secret Name: AZURE_CREDENTIALS_STAGING
  File: $OutputDirectory/azure-credentials-staging.json

For Production:
  Secret Name: AZURE_CREDENTIALS_PROD
  File: $OutputDirectory/azure-credentials-prod.json

SETUP INSTRUCTIONS
------------------
1. Navigate to GitHub repository > Settings > Secrets and variables > Actions
2. Click "New repository secret"
3. Name: AZURE_CREDENTIALS_DEV (or _STAGING, _PROD)
4. Value: Copy entire content of the corresponding JSON file
5. Click "Add secret"
6. Repeat for each environment

SECURITY NOTES
--------------
- Store these credentials securely
- Delete these files after adding to GitHub Secrets
- Never commit these files to Git
- Rotate credentials periodically (every 6-12 months)
- Monitor Service Principal activity in Azure Portal

VERIFICATION
------------
Test the Service Principal:
  az login --service-principal -u $($spCredentials.clientId) -p <client-secret> --tenant $($spCredentials.tenantId)
  az account show

NEXT STEPS
----------
1. Add credentials to GitHub Secrets (see instructions above)
2. Update GitHub Actions workflows to use these secrets
3. Test deployment pipeline
4. Delete these credential files
5. Document Service Principal details in password manager

"@ | Out-File -FilePath $summaryFile -Encoding UTF8

Write-Success "Summary saved to: $summaryFile"

# Display next steps
Write-Step "GitHub Secrets Setup"

Write-Info @"

To configure GitHub Secrets:

1. Open your GitHub repository in a browser
2. Go to Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. For each environment, create a secret:

   DEV ENVIRONMENT:
   ----------------
   Name: AZURE_CREDENTIALS_DEV
   Value: Copy content from: $OutputDirectory/azure-credentials-dev.json

   STAGING ENVIRONMENT:
   --------------------
   Name: AZURE_CREDENTIALS_STAGING
   Value: Copy content from: $OutputDirectory/azure-credentials-staging.json

   PRODUCTION ENVIRONMENT:
   -----------------------
   Name: AZURE_CREDENTIALS_PROD
   Value: Copy content from: $OutputDirectory/azure-credentials-prod.json

5. Alternatively, use GitHub CLI:

   gh secret set AZURE_CREDENTIALS_DEV < $OutputDirectory/azure-credentials-dev.json
   gh secret set AZURE_CREDENTIALS_STAGING < $OutputDirectory/azure-credentials-staging.json
   gh secret set AZURE_CREDENTIALS_PROD < $OutputDirectory/azure-credentials-prod.json

"@

Write-Step "Security Recommendations"

Write-Warning-Custom @"

IMPORTANT SECURITY STEPS:

1. Store credentials in password manager
2. DELETE credential files after GitHub setup:
   - $OutputDirectory/azure-credentials-*.json
   - $summaryFile

3. Add to .gitignore:
   echo "$OutputDirectory/" >> .gitignore

4. Verify credentials are not committed:
   git status

5. Set credential rotation reminder (6-12 months)

6. Monitor Service Principal activity:
   Azure Portal > Azure Active Directory > Enterprise Applications

7. Test Service Principal (optional):
   az login --service-principal \
     -u $($spCredentials.clientId) \
     -p $($spCredentials.clientSecret) \
     --tenant $($spCredentials.tenantId)

"@

Write-Success "`nService Principal creation completed successfully!"
Write-Warning-Custom "Remember to secure and delete credential files after GitHub setup!"

# Return credentials object (for scripting scenarios)
return @{
    ClientId       = $spCredentials.clientId
    TenantId       = $spCredentials.tenantId
    SubscriptionId = $SubscriptionId
    OutputDirectory = $OutputDirectory
    Environments   = $environments
}
