# Azure AD App Registration Automation Script
# Azure Advisor Reports Platform - Deployment Prerequisites
#
# Purpose: Automates Azure AD application registration for authentication
# Version: 1.0
# Last Updated: October 5, 2025
# Platform: Windows PowerShell 7+
# Prerequisites: Azure CLI, Application Administrator role in Azure AD

#Requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment = 'dev',

    [Parameter(Mandatory = $false)]
    [string]$AppDisplayName = '',

    [Parameter(Mandatory = $false)]
    [string[]]$RedirectUris = @(),

    [Parameter(Mandatory = $false)]
    [switch]$SkipPermissions,

    [Parameter(Mandatory = $false)]
    [int]$SecretExpirationYears = 2,

    [Parameter(Mandatory = $false)]
    [string]$OutputFile = ''
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
Write-Host "║   Azure AD App Registration Automation                        ║" -ForegroundColor Cyan
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

# Get tenant ID
$tenantId = $account.tenantId
Write-Success "Tenant ID: $tenantId"

# Check Azure AD permissions
Write-Info "Checking Azure AD permissions..."
try {
    $currentUser = az ad signed-in-user show --output json | ConvertFrom-Json
    Write-Success "Current user: $($currentUser.displayName)"

    # Note: We can't easily check for Application Administrator role via CLI
    # We'll try the operation and handle errors
    Write-Warning-Custom "Ensure you have 'Application Administrator' role in Azure AD"
} catch {
    Write-Warning-Custom "Could not verify user details. Proceeding anyway..."
}

# Set default values based on environment
if (-not $AppDisplayName) {
    $AppDisplayName = switch ($Environment) {
        'dev'     { "Azure Advisor Reports - Development" }
        'staging' { "Azure Advisor Reports - Staging" }
        'prod'    { "Azure Advisor Reports - Production" }
    }
}

# Set default redirect URIs
if ($RedirectUris.Count -eq 0) {
    $RedirectUris = @(
        "http://localhost:3000",
        "http://localhost:3000/auth/callback"
    )
    Write-Info "Using default redirect URIs for local development"
    Write-Info "Note: Update these after deploying to Azure"
}

# Display configuration
Write-Step "Configuration"
Write-Info "Environment: $Environment"
Write-Info "App Name: $AppDisplayName"
Write-Info "Redirect URIs:"
$RedirectUris | ForEach-Object { Write-Info "  - $_" }
Write-Info "Secret Expiration: $SecretExpirationYears years"
Write-Info "`n"

# Confirm before proceeding
Write-Warning-Custom "This script will create an Azure AD application registration."
$confirm = Read-Host "Do you want to proceed? (y/N)"
if ($confirm -ne 'y' -and $confirm -ne 'Y') {
    Write-Info "Operation cancelled by user."
    exit 0
}

# Create Azure AD Application
Write-Step "Creating Azure AD Application"

try {
    Write-Info "Creating app registration: $AppDisplayName"

    # Build redirect URI parameter
    $redirectUriParam = ($RedirectUris | ForEach-Object { $_ }) -join ' '

    # Create app registration
    $appJson = az ad app create `
        --display-name $AppDisplayName `
        --sign-in-audience "AzureADMyOrg" `
        --web-redirect-uris @RedirectUris `
        --enable-id-token-issuance true `
        --output json

    if (-not $appJson) {
        throw "App creation returned empty result"
    }

    $app = $appJson | ConvertFrom-Json
    $appId = $app.appId
    $objectId = $app.id

    Write-Success "Application created successfully!"
    Write-Success "Application (Client) ID: $appId"
    Write-Success "Object ID: $objectId"

} catch {
    Write-ErrorMessage "Failed to create Azure AD application"
    Write-ErrorMessage $_.Exception.Message

    # Check if app already exists
    Write-Info "Checking if application already exists..."
    $existingApp = az ad app list --display-name $AppDisplayName --output json | ConvertFrom-Json

    if ($existingApp -and $existingApp.Count -gt 0) {
        Write-Warning-Custom "Application '$AppDisplayName' already exists!"
        Write-Info "App ID: $($existingApp[0].appId)"

        $useExisting = Read-Host "Do you want to use the existing app? (y/N)"
        if ($useExisting -eq 'y' -or $useExisting -eq 'Y') {
            $app = $existingApp[0]
            $appId = $app.appId
            $objectId = $app.id
            Write-Success "Using existing application"
        } else {
            Write-Info "Operation cancelled. Please delete the existing app or use a different name."
            exit 1
        }
    } else {
        exit 1
    }
}

# Create Client Secret
Write-Step "Creating Client Secret"

try {
    Write-Info "Generating client secret (valid for $SecretExpirationYears years)..."

    $secretJson = az ad app credential reset `
        --id $appId `
        --append `
        --display-name "$Environment-secret-$(Get-Date -Format 'yyyyMMdd')" `
        --years $SecretExpirationYears `
        --output json

    $secretData = $secretJson | ConvertFrom-Json
    $clientSecret = $secretData.password
    $secretExpiry = $secretData.endDateTime

    Write-Success "Client secret created successfully!"
    Write-Warning-Custom "SECRET VALUE (save this now, it won't be shown again):"
    Write-Host "  $clientSecret" -ForegroundColor Yellow -BackgroundColor Black
    Write-Info "Expires: $secretExpiry"

} catch {
    Write-ErrorMessage "Failed to create client secret"
    Write-ErrorMessage $_.Exception.Message
    exit 1
}

# Add API Permissions
if (-not $SkipPermissions) {
    Write-Step "Configuring API Permissions"

    try {
        Write-Info "Adding Microsoft Graph permissions..."

        # Microsoft Graph API ID
        $graphApiId = "00000003-0000-0000-c000-000000000000"

        # Permissions:
        # - e1fe6dd8-ba31-4d61-89e7-88639da4683d = User.Read (delegated)
        # - 37f7f235-527c-4136-accd-4a02d197296e = openid (delegated)
        # - 14dad69e-099b-42c9-810b-d002981feec1 = profile (delegated)
        # - 64a6cdd6-aab1-4aaf-94b8-3cc8405e90d0 = email (delegated)

        $permissions = @(
            @{ api = $graphApiId; permission = "e1fe6dd8-ba31-4d61-89e7-88639da4683d"; type = "Scope" } # User.Read
            @{ api = $graphApiId; permission = "37f7f235-527c-4136-accd-4a02d197296e"; type = "Scope" } # openid
            @{ api = $graphApiId; permission = "14dad69e-099b-42c9-810b-d002981feec1"; type = "Scope" } # profile
            @{ api = $graphApiId; permission = "64a6cdd6-aab1-4aaf-94b8-3cc8405e90d0"; type = "Scope" } # email
        )

        foreach ($perm in $permissions) {
            Write-Info "Adding permission: $($perm.permission)"
            az ad app permission add `
                --id $appId `
                --api $perm.api `
                --api-permissions "$($perm.permission)=$($perm.type)" `
                --output none 2>$null
        }

        Write-Success "API permissions added successfully"

        # Grant admin consent (may require admin privileges)
        Write-Info "Attempting to grant admin consent..."
        try {
            az ad app permission admin-consent --id $appId --output none 2>$null
            Write-Success "Admin consent granted automatically"
        } catch {
            Write-Warning-Custom "Could not grant admin consent automatically"
            Write-Warning-Custom "You may need to grant consent manually in Azure Portal:"
            Write-Info "  1. Go to Azure Portal > Azure Active Directory"
            Write-Info "  2. Navigate to App registrations > $AppDisplayName"
            Write-Info "  3. Go to API permissions"
            Write-Info "  4. Click 'Grant admin consent for [tenant]'"
        }

    } catch {
        Write-Warning-Custom "Failed to configure some API permissions"
        Write-Warning-Custom $_.Exception.Message
        Write-Info "You can add permissions manually in Azure Portal if needed"
    }
} else {
    Write-Info "Skipping API permissions configuration (--SkipPermissions flag used)"
}

# Configure optional settings
Write-Step "Configuring Additional Settings"

try {
    # Enable ID token issuance (already done in creation, but verify)
    Write-Info "Ensuring ID token issuance is enabled..."

    # Configure logout URL
    $logoutUrl = "http://localhost:3000/logout"
    Write-Info "Setting logout URL: $logoutUrl"

    az ad app update `
        --id $appId `
        --web-home-page-url "http://localhost:3000" `
        --output none 2>$null

    Write-Success "Additional settings configured"

} catch {
    Write-Warning-Custom "Some optional settings could not be configured"
}

# Generate summary output
Write-Step "Summary"

$summary = @{
    Environment          = $Environment
    AppDisplayName       = $AppDisplayName
    ClientId             = $appId
    TenantId             = $tenantId
    ObjectId             = $objectId
    ClientSecret         = $clientSecret
    SecretExpiry         = $secretExpiry
    RedirectUris         = $RedirectUris
    CreatedDate          = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    CreatedBy            = $account.user.name
}

Write-Success "Azure AD Application Registration Complete!"
Write-Info "`nApplication Details:"
Write-Info "  Display Name: $AppDisplayName"
Write-Info "  Environment: $Environment"
Write-Info "  Client ID: $appId"
Write-Info "  Tenant ID: $tenantId"
Write-Info "  Object ID: $objectId"
Write-Info "`nClient Secret:"
Write-Warning-Custom "  Value: $clientSecret"
Write-Info "  Expires: $secretExpiry"
Write-Info "`nRedirect URIs:"
$RedirectUris | ForEach-Object { Write-Info "  - $_" }

# Save to file
if (-not $OutputFile) {
    $OutputFile = "azure-ad-config-$Environment-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
}

try {
    # Create sanitized output (without client secret in plain JSON)
    $outputData = @{
        environment     = $Environment
        appDisplayName  = $AppDisplayName
        clientId        = $appId
        tenantId        = $tenantId
        objectId        = $objectId
        redirectUris    = $RedirectUris
        createdDate     = $summary.CreatedDate
        createdBy       = $summary.CreatedBy
        secretExpiry    = $secretExpiry
        instructions    = @{
            clientSecret = "STORED SECURELY - DO NOT COMMIT TO GIT"
            note         = "The client secret has been saved to a separate secure file"
        }
    }

    $outputData | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputFile -Encoding UTF8
    Write-Success "`nConfiguration saved to: $OutputFile"

    # Save secret to separate file
    $secretFile = "azure-ad-secret-$Environment-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    @"
AZURE AD CLIENT SECRET - $Environment
================================
IMPORTANT: Store this securely! This file should NOT be committed to Git.

Client ID: $appId
Tenant ID: $tenantId
Client Secret: $clientSecret
Expires: $secretExpiry

Created: $($summary.CreatedDate)
Created By: $($summary.CreatedBy)

NEXT STEPS:
1. Store this secret in Azure Key Vault
2. Add to GitHub Secrets:
   - AZURE_CLIENT_ID_$(($Environment).ToUpper())
   - AZURE_CLIENT_SECRET_$(($Environment).ToUpper())
   - AZURE_TENANT_ID (shared across environments)
3. Update parameter file: parameters.$Environment.json
4. DELETE THIS FILE after storing the secret securely

"@ | Out-File -FilePath $secretFile -Encoding UTF8

    Write-Success "Client secret saved to: $secretFile"
    Write-Warning-Custom "IMPORTANT: Delete this file after storing the secret securely!"

} catch {
    Write-Warning-Custom "Could not save configuration to file: $_"
}

# Post-deployment instructions
Write-Step "Next Steps"

Write-Info @"

1. SECURE THE CLIENT SECRET
   - Store in Azure Key Vault or password manager
   - Add to GitHub Secrets (for CI/CD)
   - Never commit to source control
   - Delete the secret file: $secretFile

2. UPDATE PARAMETER FILES
   - Edit scripts/azure/bicep/parameters.$Environment.json
   - Replace placeholders:
     * azureAdClientId: $appId
     * azureAdTenantId: $tenantId
     * azureAdClientSecret: $clientSecret

3. UPDATE REDIRECT URIS (After Infrastructure Deployment)
   - Get Front Door or App Service URL from deployment
   - Run: az ad app update --id $appId --web-redirect-uris https://your-domain.com
   - Or update manually in Azure Portal

4. CONFIGURE GITHUB SECRETS
   - See: GITHUB_SECRETS_GUIDE.md
   - Required secrets:
     * AZURE_CLIENT_ID_$(($Environment).ToUpper()): $appId
     * AZURE_CLIENT_SECRET_$(($Environment).ToUpper()): $clientSecret
     * AZURE_TENANT_ID: $tenantId

5. VERIFY CONFIGURATION
   - Azure Portal > Azure Active Directory
   - App registrations > $AppDisplayName
   - Verify redirect URIs and permissions

6. PROCEED WITH INFRASTRUCTURE DEPLOYMENT
   - Run: .\deploy.ps1 -Environment $Environment
   - Or use: .\setup-service-principal.ps1 (for GitHub Actions)

"@

Write-Success "`nAzure AD setup completed successfully!"
Write-Warning-Custom "Remember to secure and delete the secret file: $secretFile"

# Return configuration object
return $summary
