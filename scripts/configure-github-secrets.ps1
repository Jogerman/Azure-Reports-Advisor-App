<#
.SYNOPSIS
    Interactive GitHub Secrets Configuration Script for Azure Advisor Reports Platform

.DESCRIPTION
    This script helps configure all required GitHub secrets for CI/CD pipelines.
    It walks through each secret with explanations and validation.

.PARAMETER Repository
    GitHub repository in format "owner/repo"

.PARAMETER Environment
    Target environment (production or staging)

.EXAMPLE
    .\configure-github-secrets.ps1 -Repository "myorg/azure-advisor-reports" -Environment production

.NOTES
    Requires GitHub CLI (gh) to be installed and authenticated
    Version: 1.0
    Last Updated: October 4, 2025
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$Repository,

    [Parameter(Mandatory=$false)]
    [ValidateSet('production', 'staging')]
    [string]$Environment = 'production'
)

# Colors and formatting
$script:SuccessColor = "Green"
$script:WarningColor = "Yellow"
$script:ErrorColor = "Red"
$script:InfoColor = "Cyan"
$script:HighlightColor = "Magenta"

function Write-Header {
    param([string]$Title)
    Write-Host "`n" -NoNewline
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor $InfoColor
    Write-Host "  $Title" -ForegroundColor $InfoColor
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor $InfoColor
    Write-Host ""
}

function Write-Section {
    param([string]$Title)
    Write-Host "`n┌─────────────────────────────────────────────────────────┐" -ForegroundColor $InfoColor
    Write-Host "│  $Title" -ForegroundColor $InfoColor
    Write-Host "└─────────────────────────────────────────────────────────┘" -ForegroundColor $InfoColor
}

function Write-Success {
    param([string]$Message)
    Write-Host "  ✅ $Message" -ForegroundColor $SuccessColor
}

function Write-Warning {
    param([string]$Message)
    Write-Host "  ⚠️  $Message" -ForegroundColor $WarningColor
}

function Write-Error {
    param([string]$Message)
    Write-Host "  ❌ $Message" -ForegroundColor $ErrorColor
}

function Write-Info {
    param([string]$Message)
    Write-Host "  ℹ️  $Message" -ForegroundColor $InfoColor
}

function Test-GitHubCLI {
    Write-Section "Checking Prerequisites"

    # Check if gh CLI is installed
    $ghInstalled = Get-Command gh -ErrorAction SilentlyContinue
    if (-not $ghInstalled) {
        Write-Error "GitHub CLI (gh) not found"
        Write-Info "Install from: https://cli.github.com/"
        Write-Host "`nInstallation commands:" -ForegroundColor $WarningColor
        Write-Host "  Windows: winget install --id GitHub.cli" -ForegroundColor Gray
        Write-Host "  macOS:   brew install gh" -ForegroundColor Gray
        Write-Host "  Linux:   See https://github.com/cli/cli/blob/trunk/docs/install_linux.md" -ForegroundColor Gray
        return $false
    }

    Write-Success "GitHub CLI (gh) is installed"

    # Check version
    $version = gh --version | Select-String -Pattern "gh version (\d+\.\d+\.\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }
    Write-Info "Version: $version"

    # Check authentication
    try {
        $authStatus = gh auth status 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "GitHub CLI is authenticated"
            return $true
        } else {
            Write-Warning "GitHub CLI is not authenticated"
            return $false
        }
    } catch {
        Write-Warning "GitHub CLI is not authenticated"
        return $false
    }
}

function Initialize-GitHubAuth {
    Write-Section "GitHub Authentication"

    Write-Host "`nInitiating GitHub authentication..." -ForegroundColor $InfoColor
    Write-Info "A browser window will open for authentication"

    gh auth login --web

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Successfully authenticated with GitHub"
        return $true
    } else {
        Write-Error "Authentication failed"
        return $false
    }
}

function Get-RepositoryName {
    Write-Section "Repository Configuration"

    if ($Repository) {
        Write-Info "Using provided repository: $Repository"
        return $Repository
    }

    # Try to detect from git remote
    try {
        $gitRemote = git remote get-url origin 2>$null
        if ($gitRemote -match "github\.com[:/](.+/.+?)(\.git)?$") {
            $detectedRepo = $Matches[1] -replace '\.git$', ''
            Write-Info "Detected repository from git remote: $detectedRepo"

            $useDetected = Read-Host "`nUse this repository? (Y/n)"
            if ($useDetected -eq '' -or $useDetected -eq 'Y' -or $useDetected -eq 'y') {
                return $detectedRepo
            }
        }
    } catch {
        # Git not available or not in a git repository
    }

    # Manual input
    Write-Host "`nEnter repository in format 'owner/repo' (e.g., 'microsoft/azure-advisor-reports'):" -ForegroundColor $HighlightColor
    $repo = Read-Host "Repository"

    if ($repo -notmatch '^[\w\-]+/[\w\-]+$') {
        Write-Error "Invalid repository format. Expected: owner/repo"
        return $null
    }

    return $repo
}

function Set-GitHubSecret {
    param(
        [string]$SecretName,
        [string]$SecretValue,
        [string]$Repository,
        [string]$Environment
    )

    $envSuffix = if ($Environment -eq 'production') { '_PROD' } else { '_STAGING' }
    $fullSecretName = "$SecretName$envSuffix"

    try {
        # Use environment variable to pass secret (avoids command-line exposure)
        $env:GITHUB_SECRET_VALUE = $SecretValue

        # Set the secret using gh CLI
        $env:GITHUB_SECRET_VALUE | gh secret set $fullSecretName --repo $Repository 2>&1 | Out-Null

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Set secret: $fullSecretName"
            return $true
        } else {
            Write-Error "Failed to set secret: $fullSecretName"
            return $false
        }
    } catch {
        Write-Error "Error setting secret: $fullSecretName - $_"
        return $false
    } finally {
        # Clear the environment variable
        Remove-Item Env:\GITHUB_SECRET_VALUE -ErrorAction SilentlyContinue
    }
}

function Get-SecretValue {
    param(
        [string]$SecretName,
        [string]$Description,
        [string]$Example,
        [bool]$IsMultiline = $false,
        [bool]$IsJson = $false,
        [bool]$Generate = $false
    )

    Write-Host "`n┌─────────────────────────────────────────────────────────┐" -ForegroundColor $HighlightColor
    Write-Host "│  Secret: $SecretName" -ForegroundColor $HighlightColor
    Write-Host "└─────────────────────────────────────────────────────────┘" -ForegroundColor $HighlightColor

    Write-Host "`nDescription:" -ForegroundColor White
    Write-Host "  $Description" -ForegroundColor Gray

    if ($Example) {
        Write-Host "`nExample Format:" -ForegroundColor White
        Write-Host "  $Example" -ForegroundColor Gray
    }

    if ($Generate) {
        $generateResponse = Read-Host "`nGenerate random value? (Y/n)"
        if ($generateResponse -eq '' -or $generateResponse -eq 'Y' -or $generateResponse -eq 'y') {
            $generatedValue = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 50 | ForEach-Object {[char]$_})
            Write-Success "Generated random value"
            return $generatedValue
        }
    }

    if ($IsJson) {
        Write-Host "`nPaste the entire JSON object (press Enter, then Ctrl+Z, then Enter when done):" -ForegroundColor $HighlightColor
        $jsonLines = @()
        while ($true) {
            $line = Read-Host
            if ($line -eq '') { break }
            $jsonLines += $line
        }
        $secretValue = $jsonLines -join "`n"

        # Validate JSON
        try {
            $null = $secretValue | ConvertFrom-Json
            Write-Success "Valid JSON format"
        } catch {
            Write-Error "Invalid JSON format"
            return $null
        }

        return $secretValue
    }

    if ($IsMultiline) {
        Write-Host "`nEnter the value (multiple lines allowed, press Enter twice when done):" -ForegroundColor $HighlightColor
        $lines = @()
        $emptyLineCount = 0
        while ($emptyLineCount -lt 2) {
            $line = Read-Host
            if ($line -eq '') {
                $emptyLineCount++
            } else {
                $emptyLineCount = 0
                $lines += $line
            }
        }
        return $lines -join "`n"
    }

    Write-Host "`nEnter the value:" -ForegroundColor $HighlightColor
    $secretValue = Read-Host -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secretValue)
    $plainValue = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)

    return $plainValue
}

function Set-AllSecrets {
    param(
        [string]$Repository,
        [string]$Environment
    )

    $envName = if ($Environment -eq 'production') { 'Production' } else { 'Staging' }

    Write-Header "Configuring $envName Secrets"

    $secretsConfigured = 0
    $secretsFailed = 0

    # Secret 1: Azure Credentials (Service Principal)
    Write-Section "1/11: Azure Credentials"
    $azureCredentials = Get-SecretValue `
        -SecretName "AZURE_CREDENTIALS" `
        -Description "Service Principal JSON output from: az ad sp create-for-rbac --sdk-auth" `
        -Example '{"clientId":"xxx","clientSecret":"xxx","subscriptionId":"xxx","tenantId":"xxx"}' `
        -IsJson $true

    if ($azureCredentials) {
        if (Set-GitHubSecret -SecretName "AZURE_CREDENTIALS" -SecretValue $azureCredentials -Repository $Repository -Environment $Environment) {
            $secretsConfigured++
        } else {
            $secretsFailed++
        }
    } else {
        Write-Warning "Skipped AZURE_CREDENTIALS"
        $secretsFailed++
    }

    # Secret 2: Django Secret Key
    Write-Section "2/11: Django Secret Key"
    $djangoSecret = Get-SecretValue `
        -SecretName "DJANGO_SECRET_KEY" `
        -Description "Django secret key for cryptographic signing (50+ characters)" `
        -Example "a8f5f167f44f4964e6c998dee827110c5a1e" `
        -Generate $true

    if ($djangoSecret) {
        if (Set-GitHubSecret -SecretName "DJANGO_SECRET_KEY" -SecretValue $djangoSecret -Repository $Repository -Environment $Environment) {
            $secretsConfigured++
        } else {
            $secretsFailed++
        }
    } else {
        Write-Warning "Skipped DJANGO_SECRET_KEY"
        $secretsFailed++
    }

    # Secret 3: Database URL
    Write-Section "3/11: Database URL"
    Write-Info "Format: postgresql://user:password@host:port/database?sslmode=require"

    $dbHost = Read-Host "Database Host (e.g., servername.postgres.database.azure.com)"
    $dbName = Read-Host "Database Name"
    $dbUser = Read-Host "Database User"
    Write-Host "Database Password:" -NoNewline -ForegroundColor $HighlightColor
    $dbPassSecure = Read-Host -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($dbPassSecure)
    $dbPass = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)

    $dbUrl = "postgresql://${dbUser}:${dbPass}@${dbHost}:5432/${dbName}?sslmode=require"

    if (Set-GitHubSecret -SecretName "DATABASE_URL" -SecretValue $dbUrl -Repository $Repository -Environment $Environment) {
        $secretsConfigured++
    } else {
        $secretsFailed++
    }

    # Secret 4: Redis URL
    Write-Section "4/11: Redis URL"
    Write-Info "Format: rediss://:password@host:port/database?ssl_cert_reqs=required"

    $redisHost = Read-Host "Redis Host (e.g., cachename.redis.cache.windows.net)"
    Write-Host "Redis Password:" -NoNewline -ForegroundColor $HighlightColor
    $redisPassSecure = Read-Host -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($redisPassSecure)
    $redisPass = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)

    $redisUrl = "rediss://:${redisPass}@${redisHost}:6380/0?ssl_cert_reqs=required"

    if (Set-GitHubSecret -SecretName "REDIS_URL" -SecretValue $redisUrl -Repository $Repository -Environment $Environment) {
        $secretsConfigured++
    } else {
        $secretsFailed++
    }

    # Secret 5: Azure Client ID
    Write-Section "5/11: Azure AD Client ID"
    $azureClientId = Get-SecretValue `
        -SecretName "AZURE_CLIENT_ID" `
        -Description "Azure AD App Registration Client ID (Application ID)" `
        -Example "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

    if ($azureClientId) {
        if (Set-GitHubSecret -SecretName "AZURE_CLIENT_ID" -SecretValue $azureClientId -Repository $Repository -Environment $Environment) {
            $secretsConfigured++
        } else {
            $secretsFailed++
        }
    } else {
        Write-Warning "Skipped AZURE_CLIENT_ID"
        $secretsFailed++
    }

    # Secret 6: Azure Client Secret
    Write-Section "6/11: Azure AD Client Secret"
    $azureClientSecret = Get-SecretValue `
        -SecretName "AZURE_CLIENT_SECRET" `
        -Description "Azure AD App Registration Client Secret" `
        -Example "abc123~def456_ghi789"

    if ($azureClientSecret) {
        if (Set-GitHubSecret -SecretName "AZURE_CLIENT_SECRET" -SecretValue $azureClientSecret -Repository $Repository -Environment $Environment) {
            $secretsConfigured++
        } else {
            $secretsFailed++
        }
    } else {
        Write-Warning "Skipped AZURE_CLIENT_SECRET"
        $secretsFailed++
    }

    # Secret 7: Azure Tenant ID
    Write-Section "7/11: Azure AD Tenant ID"
    $azureTenantId = Get-SecretValue `
        -SecretName "AZURE_TENANT_ID" `
        -Description "Azure AD Tenant ID (Directory ID)" `
        -Example "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

    if ($azureTenantId) {
        if (Set-GitHubSecret -SecretName "AZURE_TENANT_ID" -SecretValue $azureTenantId -Repository $Repository -Environment $Environment) {
            $secretsConfigured++
        } else {
            $secretsFailed++
        }
    } else {
        Write-Warning "Skipped AZURE_TENANT_ID"
        $secretsFailed++
    }

    # Secret 8: Azure Storage Connection String
    Write-Section "8/11: Azure Storage Connection String"
    Write-Info "Format: DefaultEndpointsProtocol=https;AccountName=xxx;AccountKey=xxx;EndpointSuffix=core.windows.net"

    $storageAccount = Read-Host "Storage Account Name"
    Write-Host "Storage Account Key:" -NoNewline -ForegroundColor $HighlightColor
    $storageKeySecure = Read-Host -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($storageKeySecure)
    $storageKey = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)

    $storageConnStr = "DefaultEndpointsProtocol=https;AccountName=${storageAccount};AccountKey=${storageKey};EndpointSuffix=core.windows.net"

    if (Set-GitHubSecret -SecretName "AZURE_STORAGE_CONNECTION_STRING" -SecretValue $storageConnStr -Repository $Repository -Environment $Environment) {
        $secretsConfigured++
    } else {
        $secretsFailed++
    }

    # Secret 9: Application Insights Connection String
    Write-Section "9/11: Application Insights Connection String"
    $appInsightsConnStr = Get-SecretValue `
        -SecretName "APPLICATIONINSIGHTS_CONNECTION_STRING" `
        -Description "Application Insights connection string for monitoring" `
        -Example "InstrumentationKey=xxx;IngestionEndpoint=https://xxx.applicationinsights.azure.com/"

    if ($appInsightsConnStr) {
        if (Set-GitHubSecret -SecretName "APPLICATIONINSIGHTS_CONNECTION_STRING" -SecretValue $appInsightsConnStr -Repository $Repository -Environment $Environment) {
            $secretsConfigured++
        } else {
            $secretsFailed++
        }
    } else {
        Write-Warning "Skipped APPLICATIONINSIGHTS_CONNECTION_STRING"
        $secretsFailed++
    }

    # Secret 10: Allowed Hosts
    Write-Section "10/11: Allowed Hosts"
    $allowedHosts = Get-SecretValue `
        -SecretName "ALLOWED_HOSTS" `
        -Description "Comma-separated list of allowed hostnames for Django" `
        -Example "app-advisor-backend-prod.azurewebsites.net,yourdomain.com"

    if ($allowedHosts) {
        if (Set-GitHubSecret -SecretName "ALLOWED_HOSTS" -SecretValue $allowedHosts -Repository $Repository -Environment $Environment) {
            $secretsConfigured++
        } else {
            $secretsFailed++
        }
    } else {
        Write-Warning "Skipped ALLOWED_HOSTS"
        $secretsFailed++
    }

    # Secret 11: CORS Allowed Origins
    Write-Section "11/11: CORS Allowed Origins"
    $corsOrigins = Get-SecretValue `
        -SecretName "CORS_ALLOWED_ORIGINS" `
        -Description "Comma-separated list of allowed CORS origins" `
        -Example "https://app-advisor-frontend-prod.azurewebsites.net,https://yourdomain.com"

    if ($corsOrigins) {
        if (Set-GitHubSecret -SecretName "CORS_ALLOWED_ORIGINS" -SecretValue $corsOrigins -Repository $Repository -Environment $Environment) {
            $secretsConfigured++
        } else {
            $secretsFailed++
        }
    } else {
        Write-Warning "Skipped CORS_ALLOWED_ORIGINS"
        $secretsFailed++
    }

    # Summary
    Write-Header "Configuration Summary"

    Write-Host "`nEnvironment: " -NoNewline -ForegroundColor White
    Write-Host $envName -ForegroundColor $HighlightColor

    Write-Host "`nSecrets Configured: " -NoNewline -ForegroundColor White
    Write-Host $secretsConfigured -ForegroundColor $SuccessColor

    if ($secretsFailed -gt 0) {
        Write-Host "Secrets Failed: " -NoNewline -ForegroundColor White
        Write-Host $secretsFailed -ForegroundColor $ErrorColor
    }

    Write-Host "`nTotal Secrets: " -NoNewline -ForegroundColor White
    Write-Host "11" -ForegroundColor Gray

    if ($secretsConfigured -eq 11) {
        Write-Host "`n✅ All secrets configured successfully!" -ForegroundColor $SuccessColor
    } else {
        Write-Host "`n⚠️  Some secrets were not configured. Please review and retry." -ForegroundColor $WarningColor
    }
}

function Show-NextSteps {
    Write-Header "Next Steps"

    Write-Host "1. Verify secrets in GitHub:" -ForegroundColor White
    Write-Host "   https://github.com/$Repository/settings/secrets/actions" -ForegroundColor $InfoColor

    Write-Host "`n2. Review GitHub Actions workflows:" -ForegroundColor White
    Write-Host "   - .github/workflows/ci.yml" -ForegroundColor Gray
    Write-Host "   - .github/workflows/deploy-staging.yml" -ForegroundColor Gray
    Write-Host "   - .github/workflows/deploy-production.yml" -ForegroundColor Gray

    Write-Host "`n3. Run pre-deployment validation:" -ForegroundColor White
    Write-Host "   .\scripts\pre-deployment-check.ps1 -Environment $Environment" -ForegroundColor $InfoColor

    Write-Host "`n4. Deploy infrastructure:" -ForegroundColor White
    Write-Host "   .\scripts\azure\deploy.ps1 -Environment $Environment" -ForegroundColor $InfoColor

    Write-Host "`n5. Trigger GitHub Actions workflow:" -ForegroundColor White
    Write-Host "   Push to main branch or manually trigger workflow" -ForegroundColor Gray

    Write-Host ""
}

# Main Script Execution
Clear-Host

Write-Header "GitHub Secrets Configuration for Azure Advisor Reports"

Write-Host "This script will help you configure GitHub secrets for CI/CD pipelines." -ForegroundColor White
Write-Host "You'll be prompted for each secret value with examples and validation." -ForegroundColor White

# Step 1: Check prerequisites
if (-not (Test-GitHubCLI)) {
    Write-Error "GitHub CLI is required. Please install and try again."
    exit 1
}

# Step 2: Authenticate if needed
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    if (-not (Initialize-GitHubAuth)) {
        Write-Error "GitHub authentication failed. Exiting."
        exit 1
    }
}

# Step 3: Get repository name
$Repository = Get-RepositoryName
if (-not $Repository) {
    Write-Error "Repository name is required. Exiting."
    exit 1
}

# Verify repository exists
Write-Host "`nVerifying repository..." -ForegroundColor $InfoColor
$repoCheck = gh repo view $Repository 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Repository '$Repository' not found or you don't have access"
    exit 1
}

Write-Success "Repository verified: $Repository"

# Step 4: Configure secrets
Write-Host "`nConfiguring secrets for environment: " -NoNewline -ForegroundColor White
Write-Host $Environment.ToUpper() -ForegroundColor $HighlightColor

$continue = Read-Host "`nContinue? (Y/n)"
if ($continue -eq 'n' -or $continue -eq 'N') {
    Write-Warning "Configuration cancelled by user"
    exit 0
}

Set-AllSecrets -Repository $Repository -Environment $Environment

# Step 5: Show next steps
Show-NextSteps

Write-Host "`n✅ GitHub Secrets configuration complete!" -ForegroundColor $SuccessColor
Write-Host ""
