# Azure AD App Registration Setup Guide

**Document Version:** 1.0
**Last Updated:** October 4, 2025
**Target Environment:** Production, Staging, Development
**Platform:** Windows PowerShell

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Overview](#overview)
3. [App Registration for Backend + Frontend](#app-registration-for-backend--frontend)
4. [Service Principal for GitHub Actions](#service-principal-for-github-actions)
5. [Verification Steps](#verification-steps)
6. [Troubleshooting](#troubleshooting)
7. [Security Best Practices](#security-best-practices)

---

## Prerequisites

### Required Permissions

You must have one of the following Azure AD roles:
- **Global Administrator** (recommended for initial setup)
- **Application Administrator**
- **Cloud Application Administrator**

### Required Software

```powershell
# 1. Azure CLI (version 2.50.0 or higher)
az --version
# If not installed: https://aka.ms/installazurecliwindows

# 2. PowerShell 7+ (recommended)
$PSVersionTable.PSVersion
# If not installed: https://github.com/PowerShell/PowerShell/releases

# 3. Active Azure subscription
az account show
# If not logged in: az login
```

### Environment Information

Gather the following information before proceeding:

| Item | Value | Notes |
|------|-------|-------|
| **Subscription ID** | `<your-subscription-id>` | From Azure Portal |
| **Tenant ID** | `<your-tenant-id>` | From Azure AD overview |
| **Environment** | dev/staging/prod | Which environment you're setting up |
| **Frontend URL** | `https://...` | Your frontend application URL |
| **Backend URL** | `https://...` | Your backend API URL |

---

## Overview

### What This Guide Does

This guide will help you create:
1. **Azure AD App Registration** for user authentication (OAuth 2.0 + OpenID Connect)
2. **Service Principal** for automated deployments via GitHub Actions
3. **API Permissions** for Microsoft Graph access
4. **Secrets and Certificates** for secure authentication

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│               Azure Active Directory                     │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │     App Registration                            │    │
│  │     (Azure Advisor Reports - Production)        │    │
│  │                                                  │    │
│  │  Client ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx │    │
│  │  Tenant ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx │    │
│  │  Client Secret: ******************************** │    │
│  │                                                  │    │
│  │  Redirect URIs:                                 │    │
│  │    - https://frontend.azurewebsites.net         │    │
│  │    - https://backend.azurewebsites.net/api/auth │    │
│  │                                                  │    │
│  │  API Permissions:                               │    │
│  │    - Microsoft Graph User.Read                   │    │
│  │    - OpenID Connect (openid, profile, email)    │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │     Service Principal                           │    │
│  │     (GitHub-Actions-AzureAdvisorReports)        │    │
│  │                                                  │    │
│  │  Role: Contributor                              │    │
│  │  Scope: /subscriptions/<subscription-id>        │    │
│  │  Credentials: JSON output for GitHub secrets     │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## App Registration for Backend + Frontend

### Step 1: Connect to Azure

```powershell
# Open PowerShell 7 as Administrator

# Login to Azure
Write-Host "Logging in to Azure..." -ForegroundColor Cyan
az login

# Verify you're in the correct subscription
$subscription = az account show | ConvertFrom-Json
Write-Host "Current Subscription: $($subscription.name)" -ForegroundColor Green
Write-Host "Subscription ID: $($subscription.id)" -ForegroundColor Green
Write-Host "Tenant ID: $($subscription.tenantId)" -ForegroundColor Green

# If wrong subscription, set the correct one:
# az account set --subscription "<subscription-id or name>"
```

### Step 2: Define Environment Variables

```powershell
# Environment-specific configuration
# CHANGE THESE VALUES FOR YOUR ENVIRONMENT

$environment = "prod"  # Options: dev, staging, prod

# App Registration Name
$appName = "Azure Advisor Reports - Production"

# Frontend URL (CHANGE THIS)
$frontendUrl = "https://app-advisor-frontend-prod.azurewebsites.net"

# Backend URL (CHANGE THIS)
$backendUrl = "https://app-advisor-backend-prod.azurewebsites.net"

# Redirect URIs
$redirectUris = @(
    "$frontendUrl",
    "$frontendUrl/auth/callback",
    "$backendUrl/api/auth/callback",
    "http://localhost:3000",  # For local development
    "http://localhost:3000/auth/callback"
)

Write-Host "`nConfiguration:" -ForegroundColor Cyan
Write-Host "  App Name: $appName"
Write-Host "  Frontend: $frontendUrl"
Write-Host "  Backend: $backendUrl"
Write-Host "  Redirect URIs: $($redirectUris.Count) URIs configured"
```

### Step 3: Create App Registration

```powershell
Write-Host "`nCreating App Registration..." -ForegroundColor Cyan

# Create the app registration
$app = az ad app create `
    --display-name $appName `
    --sign-in-audience "AzureADMyOrg" `
    --web-redirect-uris $redirectUris `
    --enable-id-token-issuance true `
    --enable-access-token-issuance true | ConvertFrom-Json

if (-not $app) {
    Write-Host "❌ Failed to create App Registration" -ForegroundColor Red
    exit 1
}

$appId = $app.appId
$objectId = $app.id

Write-Host "✅ App Registration created successfully!" -ForegroundColor Green
Write-Host "  App ID (Client ID): $appId" -ForegroundColor Yellow
Write-Host "  Object ID: $objectId" -ForegroundColor Yellow

# Save to file for reference
$appDetails = @{
    AppName = $appName
    ClientId = $appId
    ObjectId = $objectId
    TenantId = $subscription.tenantId
    CreatedDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
} | ConvertTo-Json

$appDetails | Out-File "app-registration-$environment.json"
Write-Host "✅ App details saved to: app-registration-$environment.json" -ForegroundColor Green
```

### Step 4: Create Client Secret

```powershell
Write-Host "`nCreating Client Secret..." -ForegroundColor Cyan

# Create client secret with 24-month expiration
$secretName = "GitHub-Actions-Secret"
$secretExpiry = (Get-Date).AddMonths(24).ToString("yyyy-MM-dd")

$secret = az ad app credential reset `
    --id $appId `
    --append `
    --display-name $secretName `
    --years 2 | ConvertFrom-Json

$clientSecret = $secret.password

Write-Host "✅ Client Secret created successfully!" -ForegroundColor Green
Write-Host "`n┌─────────────────────────────────────────────────────────────┐" -ForegroundColor Red
Write-Host "│  IMPORTANT: SAVE THIS SECRET - IT WON'T BE SHOWN AGAIN!    │" -ForegroundColor Red
Write-Host "└─────────────────────────────────────────────────────────────┘" -ForegroundColor Red
Write-Host "`nClient Secret: " -NoNewline -ForegroundColor Yellow
Write-Host $clientSecret -ForegroundColor Cyan
Write-Host "Expires On: $($secret.endDateTime)" -ForegroundColor Yellow

# Save secret to secure file (WARNING: Contains sensitive data)
$secretDetails = @{
    ClientSecret = $clientSecret
    CreatedDate = $secret.startDateTime
    ExpiryDate = $secret.endDateTime
    SecretId = $secret.keyId
} | ConvertTo-Json

$secretDetails | Out-File "client-secret-$environment.json"
Write-Host "`n⚠️  Secret saved to: client-secret-$environment.json" -ForegroundColor Yellow
Write-Host "⚠️  STORE THIS FILE SECURELY AND DELETE AFTER USE!" -ForegroundColor Red
```

### Step 5: Configure API Permissions

```powershell
Write-Host "`nConfiguring API Permissions..." -ForegroundColor Cyan

# Microsoft Graph API ID
$graphApiId = "00000003-0000-0000-c000-000000000000"

# Permission IDs for Microsoft Graph
$permissions = @(
    @{
        Name = "User.Read"
        Id = "e1fe6dd8-ba31-4d61-89e7-88639da4683d"
        Type = "Scope"  # Delegated permission
    },
    @{
        Name = "openid"
        Id = "37f7f235-527c-4136-accd-4a02d197296e"
        Type = "Scope"
    },
    @{
        Name = "profile"
        Id = "14dad69e-099b-42c9-810b-d002981feec1"
        Type = "Scope"
    },
    @{
        Name = "email"
        Id = "64a6cdd6-aab1-4aaf-94b8-3cc8405e90d0"
        Type = "Scope"
    }
)

# Add each permission
foreach ($permission in $permissions) {
    Write-Host "  Adding permission: $($permission.Name)" -ForegroundColor Gray

    az ad app permission add `
        --id $appId `
        --api $graphApiId `
        --api-permissions "$($permission.Id)=$($permission.Type)" | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✅ Added $($permission.Name)" -ForegroundColor Green
    } else {
        Write-Host "    ⚠️  Failed to add $($permission.Name)" -ForegroundColor Yellow
    }
}

Write-Host "`n✅ API Permissions configured" -ForegroundColor Green
```

### Step 6: Grant Admin Consent

```powershell
Write-Host "`nGranting Admin Consent..." -ForegroundColor Cyan

# Grant admin consent for the permissions
az ad app permission admin-consent --id $appId

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Admin consent granted successfully!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Admin consent may require Global Admin privileges" -ForegroundColor Yellow
    Write-Host "   Please grant consent manually in Azure Portal:" -ForegroundColor Yellow
    Write-Host "   https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/CallAnAPI/appId/$appId" -ForegroundColor Cyan
}
```

### Step 7: Configure Optional Settings

```powershell
Write-Host "`nConfiguring optional settings..." -ForegroundColor Cyan

# Set application logo (optional - requires image file)
# az ad app update --id $appId --set logo=@logo.png

# Set homepage URL
az ad app update --id $appId --set web.homePageUrl=$frontendUrl

# Set terms of service and privacy statement URLs
az ad app update --id $appId `
    --set info.termsOfServiceUrl="$frontendUrl/terms" `
    --set info.privacyStatementUrl="$frontendUrl/privacy"

Write-Host "✅ Optional settings configured" -ForegroundColor Green
```

### Step 8: Display Summary

```powershell
Write-Host "`n" -NoNewline
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  App Registration Summary" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host "`nEnvironment: " -NoNewline -ForegroundColor White
Write-Host $environment.ToUpper() -ForegroundColor Green

Write-Host "`nApp Registration Details:" -ForegroundColor White
Write-Host "  Name:      " -NoNewline -ForegroundColor White
Write-Host $appName -ForegroundColor Yellow
Write-Host "  Client ID: " -NoNewline -ForegroundColor White
Write-Host $appId -ForegroundColor Yellow
Write-Host "  Tenant ID: " -NoNewline -ForegroundColor White
Write-Host $subscription.tenantId -ForegroundColor Yellow
Write-Host "  Object ID: " -NoNewline -ForegroundColor White
Write-Host $objectId -ForegroundColor Gray

Write-Host "`nClient Secret:" -ForegroundColor White
Write-Host "  Secret:    " -NoNewline -ForegroundColor White
Write-Host $clientSecret -ForegroundColor Cyan
Write-Host "  Expires:   " -NoNewline -ForegroundColor White
Write-Host $secret.endDateTime -ForegroundColor Yellow

Write-Host "`nRedirect URIs:" -ForegroundColor White
foreach ($uri in $redirectUris) {
    Write-Host "  - $uri" -ForegroundColor Gray
}

Write-Host "`nAPI Permissions:" -ForegroundColor White
foreach ($permission in $permissions) {
    Write-Host "  - Microsoft Graph: $($permission.Name)" -ForegroundColor Gray
}

Write-Host "`nNext Steps:" -ForegroundColor White
Write-Host "  1. Save the Client ID and Client Secret" -ForegroundColor Yellow
Write-Host "  2. Update GitHub Secrets with these values" -ForegroundColor Yellow
Write-Host "  3. Update .env files in your application" -ForegroundColor Yellow
Write-Host "  4. Delete the sensitive JSON files after copying values" -ForegroundColor Yellow

Write-Host "`n" -NoNewline
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
```

---

## Service Principal for GitHub Actions

### Step 1: Create Service Principal

```powershell
Write-Host "`n┌─────────────────────────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host "│  Creating Service Principal for GitHub Actions          │" -ForegroundColor Cyan
Write-Host "└─────────────────────────────────────────────────────────┘" -ForegroundColor Cyan

# Get subscription ID
$subscriptionId = (az account show --query "id" -o tsv)

# Service Principal Name
$spName = "GitHub-Actions-AzureAdvisorReports-$environment"

Write-Host "`nCreating Service Principal: $spName" -ForegroundColor Yellow

# Create service principal with Contributor role
$sp = az ad sp create-for-rbac `
    --name $spName `
    --role Contributor `
    --scopes "/subscriptions/$subscriptionId" `
    --sdk-auth | ConvertFrom-Json

if (-not $sp) {
    Write-Host "❌ Failed to create Service Principal" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Service Principal created successfully!" -ForegroundColor Green
```

### Step 2: Save Service Principal Credentials

```powershell
Write-Host "`nService Principal Details:" -ForegroundColor White

# Format for GitHub secrets
$githubSecret = @{
    clientId = $sp.clientId
    clientSecret = $sp.clientSecret
    subscriptionId = $sp.subscriptionId
    tenantId = $sp.tenantId
} | ConvertTo-Json

Write-Host "`n┌─────────────────────────────────────────────────────────────┐" -ForegroundColor Red
Write-Host "│  SAVE THIS JSON FOR GITHUB SECRET: AZURE_CREDENTIALS       │" -ForegroundColor Red
Write-Host "└─────────────────────────────────────────────────────────────┘" -ForegroundColor Red

Write-Host "`n$githubSecret" -ForegroundColor Cyan

# Save to file
$githubSecret | Out-File "service-principal-$environment.json"
Write-Host "`n✅ Service Principal credentials saved to: service-principal-$environment.json" -ForegroundColor Green
Write-Host "⚠️  STORE THIS FILE SECURELY AND DELETE AFTER USE!" -ForegroundColor Red
```

### Step 3: Verify Service Principal Permissions

```powershell
Write-Host "`nVerifying Service Principal permissions..." -ForegroundColor Cyan

# Get role assignments
$roleAssignments = az role assignment list `
    --assignee $sp.clientId `
    --query "[].{Role:roleDefinitionName, Scope:scope}" `
    -o json | ConvertFrom-Json

Write-Host "`nRole Assignments:" -ForegroundColor White
foreach ($role in $roleAssignments) {
    Write-Host "  Role:  " -NoNewline -ForegroundColor White
    Write-Host $role.Role -ForegroundColor Green
    Write-Host "  Scope: " -NoNewline -ForegroundColor White
    Write-Host $role.Scope -ForegroundColor Gray
}

if ($roleAssignments.Count -eq 0) {
    Write-Host "⚠️  No role assignments found!" -ForegroundColor Yellow
} else {
    Write-Host "`n✅ Service Principal has required permissions" -ForegroundColor Green
}
```

---

## Verification Steps

### Verify App Registration

```powershell
Write-Host "`n┌─────────────────────────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host "│  Verification Tests                                      │" -ForegroundColor Cyan
Write-Host "└─────────────────────────────────────────────────────────┘" -ForegroundColor Cyan

# Test 1: Verify app exists
Write-Host "`n1️⃣  Verifying App Registration exists..." -ForegroundColor Yellow
$appCheck = az ad app show --id $appId 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ App Registration found" -ForegroundColor Green
} else {
    Write-Host "   ❌ App Registration not found" -ForegroundColor Red
}

# Test 2: Verify redirect URIs
Write-Host "`n2️⃣  Verifying Redirect URIs..." -ForegroundColor Yellow
$appDetails = az ad app show --id $appId | ConvertFrom-Json
$configuredUris = $appDetails.web.redirectUris
Write-Host "   Configured $($configuredUris.Count) redirect URIs:" -ForegroundColor White
foreach ($uri in $configuredUris) {
    Write-Host "     - $uri" -ForegroundColor Gray
}
if ($configuredUris.Count -gt 0) {
    Write-Host "   ✅ Redirect URIs configured" -ForegroundColor Green
} else {
    Write-Host "   ❌ No redirect URIs found" -ForegroundColor Red
}

# Test 3: Verify API permissions
Write-Host "`n3️⃣  Verifying API Permissions..." -ForegroundColor Yellow
$apiPermissions = az ad app permission list --id $appId | ConvertFrom-Json
$permissionCount = $apiPermissions.Count
Write-Host "   Configured $permissionCount permission(s)" -ForegroundColor White
if ($permissionCount -gt 0) {
    Write-Host "   ✅ API permissions configured" -ForegroundColor Green
} else {
    Write-Host "   ❌ No API permissions found" -ForegroundColor Red
}

# Test 4: Verify Service Principal
Write-Host "`n4️⃣  Verifying Service Principal..." -ForegroundColor Yellow
$spCheck = az ad sp show --id $sp.clientId 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Service Principal exists" -ForegroundColor Green
} else {
    Write-Host "   ❌ Service Principal not found" -ForegroundColor Red
}

# Test 5: Test authentication (requires user interaction)
Write-Host "`n5️⃣  Testing Authentication Flow..." -ForegroundColor Yellow
Write-Host "   To test authentication, visit:" -ForegroundColor White
Write-Host "   https://login.microsoftonline.com/$($subscription.tenantId)/oauth2/v2.0/authorize?client_id=$appId&response_type=code&redirect_uri=$frontendUrl&scope=openid%20profile%20email" -ForegroundColor Cyan
Write-Host "   ⚠️  Manual verification required" -ForegroundColor Yellow
```

### Azure Portal Verification

```powershell
Write-Host "`n┌─────────────────────────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host "│  Azure Portal Links for Verification                    │" -ForegroundColor Cyan
Write-Host "└─────────────────────────────────────────────────────────┘" -ForegroundColor Cyan

Write-Host "`nApp Registration:" -ForegroundColor White
Write-Host "  https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Overview/appId/$appId" -ForegroundColor Cyan

Write-Host "`nAPI Permissions:" -ForegroundColor White
Write-Host "  https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/CallAnAPI/appId/$appId" -ForegroundColor Cyan

Write-Host "`nAuthentication Settings:" -ForegroundColor White
Write-Host "  https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Authentication/appId/$appId" -ForegroundColor Cyan

Write-Host "`nCertificates & Secrets:" -ForegroundColor White
Write-Host "  https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Credentials/appId/$appId" -ForegroundColor Cyan
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: "Insufficient privileges to complete the operation"

**Cause:** You don't have the required Azure AD role.

**Solution:**
```powershell
# Check your current role assignments
az role assignment list --assignee (az account show --query user.name -o tsv)

# Request Global Administrator or Application Administrator role
# Contact your Azure AD administrator
```

#### Issue 2: "The redirect URI is not valid"

**Cause:** Redirect URI format is incorrect or contains invalid characters.

**Solution:**
```powershell
# Ensure URIs use HTTPS (except localhost)
# Valid format: https://domain.com/path
# Valid localhost: http://localhost:3000

# Update redirect URIs
az ad app update --id $appId --web-redirect-uris "https://your-correct-url.com"
```

#### Issue 3: "Admin consent required"

**Cause:** Application requires admin consent for API permissions.

**Solution:**
```powershell
# Grant admin consent via CLI
az ad app permission admin-consent --id $appId

# Or grant via Azure Portal:
# https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/CallAnAPI/appId/$appId
```

#### Issue 4: "Service Principal creation failed"

**Cause:** Insufficient permissions or quota limits.

**Solution:**
```powershell
# Verify you have Owner or Contributor role on subscription
az role assignment list --scope "/subscriptions/$subscriptionId" --assignee (az account show --query user.name -o tsv)

# Check service principal quota
az ad sp list --all --query "length(@)"
```

#### Issue 5: "Client secret not visible"

**Cause:** Secret values are only shown once during creation.

**Solution:**
```powershell
# Create a new client secret
az ad app credential reset --id $appId --append --display-name "New-Secret" --years 2

# The new secret will be displayed - save it immediately
```

### Validation Script

```powershell
# Complete validation script
function Test-AzureADSetup {
    param(
        [string]$ClientId,
        [string]$TenantId
    )

    Write-Host "`nRunning validation checks..." -ForegroundColor Cyan

    $allPassed = $true

    # Check 1: App exists
    try {
        az ad app show --id $ClientId | Out-Null
        Write-Host "✅ App Registration exists" -ForegroundColor Green
    } catch {
        Write-Host "❌ App Registration not found" -ForegroundColor Red
        $allPassed = $false
    }

    # Check 2: Redirect URIs configured
    $app = az ad app show --id $ClientId | ConvertFrom-Json
    if ($app.web.redirectUris.Count -gt 0) {
        Write-Host "✅ Redirect URIs configured ($($app.web.redirectUris.Count))" -ForegroundColor Green
    } else {
        Write-Host "❌ No redirect URIs configured" -ForegroundColor Red
        $allPassed = $false
    }

    # Check 3: API permissions
    $permissions = az ad app permission list --id $ClientId | ConvertFrom-Json
    if ($permissions.Count -gt 0) {
        Write-Host "✅ API permissions configured ($($permissions.Count))" -ForegroundColor Green
    } else {
        Write-Host "❌ No API permissions configured" -ForegroundColor Red
        $allPassed = $false
    }

    # Check 4: Client secrets
    $credentials = az ad app credential list --id $ClientId | ConvertFrom-Json
    if ($credentials.Count -gt 0) {
        Write-Host "✅ Client secrets configured ($($credentials.Count))" -ForegroundColor Green
    } else {
        Write-Host "⚠️  No client secrets found" -ForegroundColor Yellow
    }

    if ($allPassed) {
        Write-Host "`n✅ All validation checks passed!" -ForegroundColor Green
        return $true
    } else {
        Write-Host "`n❌ Some validation checks failed" -ForegroundColor Red
        return $false
    }
}

# Run validation
Test-AzureADSetup -ClientId $appId -TenantId $subscription.tenantId
```

---

## Security Best Practices

### 1. Secret Management

```powershell
# DO: Store secrets in Azure Key Vault
az keyvault secret set `
    --vault-name "kv-advisor-$environment" `
    --name "AzureADClientSecret" `
    --value $clientSecret

# DO: Use managed identities when possible
# DO: Rotate secrets every 6-12 months
# DO: Delete local secret files after saving to secure location

# DON'T: Commit secrets to Git
# DON'T: Share secrets via email or chat
# DON'T: Use secrets in client-side code
```

### 2. Permission Principle of Least Privilege

```powershell
# Only request the minimum required permissions
# Current permissions:
# - User.Read (to read user profile)
# - openid, profile, email (for authentication)

# If you need additional permissions in the future, add them explicitly:
# az ad app permission add --id $appId --api $graphApiId --api-permissions "<permission-id>=Scope"
```

### 3. Regular Auditing

```powershell
# Script to audit app registrations
function Audit-AppRegistration {
    param([string]$AppId)

    Write-Host "`nAuditing App Registration..." -ForegroundColor Cyan

    # Get app details
    $app = az ad app show --id $AppId | ConvertFrom-Json

    # Check credential expiration
    $credentials = az ad app credential list --id $AppId | ConvertFrom-Json

    Write-Host "`nCredentials Audit:" -ForegroundColor White
    foreach ($cred in $credentials) {
        $expiryDate = [DateTime]::Parse($cred.endDateTime)
        $daysUntilExpiry = ($expiryDate - (Get-Date)).Days

        if ($daysUntilExpiry -lt 30) {
            Write-Host "  ⚠️  Secret expires in $daysUntilExpiry days" -ForegroundColor Red
        } elseif ($daysUntilExpiry -lt 90) {
            Write-Host "  ⚠️  Secret expires in $daysUntilExpiry days" -ForegroundColor Yellow
        } else {
            Write-Host "  ✅ Secret valid for $daysUntilExpiry days" -ForegroundColor Green
        }
    }

    # Check permissions
    $permissions = az ad app permission list --id $AppId | ConvertFrom-Json
    Write-Host "`nPermissions Audit:" -ForegroundColor White
    Write-Host "  Total permissions: $($permissions.Count)" -ForegroundColor Gray

    # Check redirect URIs
    Write-Host "`nRedirect URIs Audit:" -ForegroundColor White
    Write-Host "  Total URIs: $($app.web.redirectUris.Count)" -ForegroundColor Gray
    foreach ($uri in $app.web.redirectUris) {
        if ($uri -like "http://*" -and $uri -notlike "http://localhost*") {
            Write-Host "  ⚠️  Non-HTTPS URI: $uri" -ForegroundColor Yellow
        } else {
            Write-Host "  ✅ $uri" -ForegroundColor Green
        }
    }
}

# Run audit
Audit-AppRegistration -AppId $appId
```

### 4. Environment Isolation

```powershell
# Create separate app registrations for each environment
# Example naming convention:
# - Azure Advisor Reports - Development
# - Azure Advisor Reports - Staging
# - Azure Advisor Reports - Production

# This ensures:
# - No accidental cross-environment access
# - Easy credential rotation per environment
# - Clear audit trails
```

---

## Complete Setup Script

Save this as `setup-azure-ad.ps1` and run it:

```powershell
<#
.SYNOPSIS
    Complete Azure AD setup script for Azure Advisor Reports Platform

.DESCRIPTION
    This script creates:
    - App Registration with proper permissions
    - Client Secret
    - Service Principal for GitHub Actions

.PARAMETER Environment
    Target environment (dev, staging, prod)

.PARAMETER FrontendUrl
    Frontend application URL

.PARAMETER BackendUrl
    Backend API URL

.EXAMPLE
    .\setup-azure-ad.ps1 -Environment prod -FrontendUrl "https://app-advisor-frontend-prod.azurewebsites.net" -BackendUrl "https://app-advisor-backend-prod.azurewebsites.net"
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment,

    [Parameter(Mandatory=$true)]
    [string]$FrontendUrl,

    [Parameter(Mandatory=$true)]
    [string]$BackendUrl
)

# Import the full script content from above...
# (All the steps combined into one script)

Write-Host "Setup complete! Check the generated JSON files for credentials." -ForegroundColor Green
```

---

## Summary Checklist

After completing this guide, you should have:

- [ ] App Registration created in Azure AD
- [ ] Client ID obtained
- [ ] Client Secret created and securely stored
- [ ] Tenant ID identified
- [ ] Redirect URIs configured (frontend + backend)
- [ ] API permissions configured (Microsoft Graph User.Read)
- [ ] Admin consent granted
- [ ] Service Principal created for GitHub Actions
- [ ] Service Principal credentials saved as JSON
- [ ] All credentials stored in secure location (Azure Key Vault or password manager)
- [ ] Local JSON files deleted
- [ ] GitHub Secrets updated (next step)
- [ ] Application .env files updated

---

## Next Steps

1. **Configure GitHub Secrets** using `configure-github-secrets.ps1`
2. **Update Application Configuration** (.env files)
3. **Test Authentication** in development environment
4. **Run Pre-Deployment Checks** before Azure deployment

---

## Support

If you encounter issues:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review Azure AD documentation: https://docs.microsoft.com/azure/active-directory/
3. Check Azure CLI reference: https://docs.microsoft.com/cli/azure/ad/app

---

**Document End**
