# ============================================================================
# Azure Advisor Reports - Deployment Configuration Verification Script
# Version: 1.2.2
# ============================================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$BackendAppName = "",

    [Parameter(Mandatory=$false)]
    [string]$FrontendAppName = "",

    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = ""
)

$EXPECTED_TENANT_ID = "9acf6dd6-1978-4d9c-9a9c-c9be95245565"
$TENANT_NAME = "Solvex Dominicana"

# Colors
$COLOR_SUCCESS = "Green"
$COLOR_ERROR = "Red"
$COLOR_WARNING = "Yellow"
$COLOR_INFO = "Cyan"

function Write-Section {
    param([string]$Title)
    Write-Host "`n╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor $COLOR_INFO
    Write-Host "║  $Title" -ForegroundColor $COLOR_INFO
    Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor $COLOR_INFO
}

function Write-Check {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Value = "",
        [string]$Expected = ""
    )

    if ($Passed) {
        Write-Host "  ✓ " -NoNewline -ForegroundColor $COLOR_SUCCESS
        Write-Host $Name -ForegroundColor $COLOR_SUCCESS
        if ($Value) {
            Write-Host "    Value: $Value" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ✗ " -NoNewline -ForegroundColor $COLOR_ERROR
        Write-Host $Name -ForegroundColor $COLOR_ERROR
        if ($Value) {
            Write-Host "    Found: $Value" -ForegroundColor $COLOR_ERROR
        }
        if ($Expected) {
            Write-Host "    Expected: $Expected" -ForegroundColor $COLOR_WARNING
        }
    }
}

function Test-LocalConfiguration {
    Write-Section "Local Configuration Files"

    $allPassed = $true

    # Check frontend .env.production
    $frontendEnvPath = Join-Path $PSScriptRoot "frontend\.env.production"
    if (Test-Path $frontendEnvPath) {
        Write-Check -Name "Frontend .env.production exists" -Passed $true -Value $frontendEnvPath

        $envContent = Get-Content $frontendEnvPath -Raw

        # Check Tenant ID
        $tenantIdMatch = $envContent -match "REACT_APP_AZURE_TENANT_ID=([a-f0-9-]+)"
        if ($tenantIdMatch) {
            $foundTenantId = $Matches[1]
            $tenantCorrect = ($foundTenantId -eq $EXPECTED_TENANT_ID)
            Write-Check -Name "Frontend Tenant ID" -Passed $tenantCorrect -Value $foundTenantId -Expected $EXPECTED_TENANT_ID
            $allPassed = $allPassed -and $tenantCorrect
        } else {
            Write-Check -Name "Frontend Tenant ID" -Passed $false -Value "Not found" -Expected $EXPECTED_TENANT_ID
            $allPassed = $false
        }

        # Check other required vars
        $requiredVars = @("REACT_APP_API_URL", "REACT_APP_AZURE_CLIENT_ID", "REACT_APP_AZURE_REDIRECT_URI")
        foreach ($var in $requiredVars) {
            $varMatch = $envContent -match "$var=(.+)"
            if ($varMatch) {
                $varValue = $Matches[1].Trim()
                $isPlaceholder = $varValue -match "your-|YOUR_"
                Write-Check -Name "$var configured" -Passed (-not $isPlaceholder) -Value $varValue
                if ($isPlaceholder) {
                    $allPassed = $false
                }
            } else {
                Write-Check -Name "$var present" -Passed $false -Value "Not found"
                $allPassed = $false
            }
        }
    } else {
        Write-Check -Name "Frontend .env.production exists" -Passed $false -Expected $frontendEnvPath
        $allPassed = $false
    }

    # Check authConfig.ts
    $authConfigPath = Join-Path $PSScriptRoot "frontend\src\config\authConfig.ts"
    if (Test-Path $authConfigPath) {
        Write-Check -Name "AuthConfig.ts exists" -Passed $true -Value $authConfigPath

        $authConfig = Get-Content $authConfigPath -Raw

        # Check that it uses environment variable
        $usesEnvVar = $authConfig -match "REACT_APP_AZURE_TENANT_ID"
        Write-Check -Name "AuthConfig uses env var for Tenant ID" -Passed $usesEnvVar
        $allPassed = $allPassed -and $usesEnvVar

        # Check for hardcoded wrong tenant ID
        $hasWrongTenantId = $authConfig -match "06bf3e54-7223-498a-a4db-2f4e68d7e38d"
        Write-Check -Name "No hardcoded wrong Tenant ID" -Passed (-not $hasWrongTenantId)
        if ($hasWrongTenantId) {
            Write-Host "    WARNING: Found hardcoded wrong Tenant ID in authConfig.ts!" -ForegroundColor $COLOR_ERROR
            $allPassed = $false
        }
    } else {
        Write-Check -Name "AuthConfig.ts exists" -Passed $false
        $allPassed = $false
    }

    # Check backend settings
    $backendSettingsPath = Join-Path $PSScriptRoot "azure_advisor_reports\azure_advisor_reports\settings\production.py"
    if (Test-Path $backendSettingsPath) {
        Write-Check -Name "Backend production settings exist" -Passed $true -Value $backendSettingsPath

        $backendSettings = Get-Content $backendSettingsPath -Raw

        # Check that it uses config() for tenant ID
        $usesConfig = $backendSettings -match "config\('AZURE_TENANT_ID'\)"
        Write-Check -Name "Backend uses config for Tenant ID" -Passed $usesConfig
        $allPassed = $allPassed -and $usesConfig

        # Check for hardcoded tenant ID
        $hasHardcodedTenant = $backendSettings -match "'TENANT_ID':\s*'[a-f0-9-]{36}'"
        Write-Check -Name "No hardcoded Tenant ID in backend" -Passed (-not $hasHardcodedTenant)
        if ($hasHardcodedTenant) {
            $allPassed = $false
        }
    } else {
        Write-Check -Name "Backend production settings exist" -Passed $false
        $allPassed = $false
    }

    # Check Dockerfiles
    $frontendDockerPath = Join-Path $PSScriptRoot "frontend\Dockerfile.prod"
    if (Test-Path $frontendDockerPath) {
        Write-Check -Name "Frontend Dockerfile.prod exists" -Passed $true

        $dockerfile = Get-Content $frontendDockerPath -Raw

        # Check for build args
        $hasTenantIdArg = $dockerfile -match "ARG REACT_APP_AZURE_TENANT_ID"
        Write-Check -Name "Frontend Dockerfile has Tenant ID build arg" -Passed $hasTenantIdArg
        $allPassed = $allPassed -and $hasTenantIdArg

        # Check no hardcoded values
        $hasHardcodedTenant = $dockerfile -match "AZURE_TENANT_ID=[a-f0-9-]{36}"
        Write-Check -Name "Frontend Dockerfile has no hardcoded Tenant ID" -Passed (-not $hasHardcodedTenant)
        if ($hasHardcodedTenant) {
            $allPassed = $false
        }
    }

    return $allPassed
}

function Test-AzureConfiguration {
    Write-Section "Azure Configuration"

    $allPassed = $true

    if (-not $BackendAppName -or -not $ResourceGroup) {
        Write-Host "  ℹ  Skipping Azure configuration check (provide -BackendAppName and -ResourceGroup to check)" -ForegroundColor $COLOR_WARNING
        return $true
    }

    try {
        # Check Azure CLI
        $account = az account show 2>&1 | ConvertFrom-Json
        if (-not $account) {
            Write-Host "  ✗ Not logged in to Azure CLI" -ForegroundColor $COLOR_ERROR
            return $false
        }

        Write-Check -Name "Azure CLI authenticated" -Passed $true -Value $account.user.name

        # Check backend app settings
        Write-Host "`n  Checking Backend App Settings..." -ForegroundColor $COLOR_INFO

        $appSettings = az webapp config appsettings list `
            --name $BackendAppName `
            --resource-group $ResourceGroup 2>&1 | ConvertFrom-Json

        if ($LASTEXITCODE -ne 0) {
            Write-Check -Name "Backend app exists" -Passed $false -Value $BackendAppName
            return $false
        }

        Write-Check -Name "Backend app exists" -Passed $true -Value $BackendAppName

        # Check critical settings
        $criticalSettings = @{
            "AZURE_TENANT_ID" = $EXPECTED_TENANT_ID
            "AZURE_CLIENT_ID" = $null
            "AZURE_CLIENT_SECRET" = $null
            "SECRET_KEY" = $null
            "DEBUG" = "False"
            "DJANGO_ENVIRONMENT" = "production"
        }

        foreach ($settingName in $criticalSettings.Keys) {
            $setting = $appSettings | Where-Object { $_.name -eq $settingName }

            if ($setting) {
                $expectedValue = $criticalSettings[$settingName]

                if ($expectedValue) {
                    $matches = ($setting.value -eq $expectedValue)
                    Write-Check -Name $settingName -Passed $matches -Value $setting.value -Expected $expectedValue
                    $allPassed = $allPassed -and $matches
                } else {
                    # Just check it's not a placeholder
                    $isPlaceholder = $setting.value -match "YOUR_|your-|changeme|insecure"
                    Write-Check -Name $settingName -Passed (-not $isPlaceholder) -Value ($setting.value.Substring(0, [Math]::Min(20, $setting.value.Length)) + "...")
                    if ($isPlaceholder) {
                        $allPassed = $false
                    }
                }
            } else {
                Write-Check -Name "$settingName present" -Passed $false -Value "Not configured"
                $allPassed = $false
            }
        }

        # Check CORS and CSRF settings
        $corsOrigins = ($appSettings | Where-Object { $_.name -eq "CORS_ALLOWED_ORIGINS" }).value
        if ($corsOrigins) {
            $hasLocalhost = $corsOrigins -match "localhost|127.0.0.1"
            Write-Check -Name "CORS doesn't include localhost" -Passed (-not $hasLocalhost)
            if ($hasLocalhost) {
                Write-Host "    WARNING: Production should not allow localhost" -ForegroundColor $COLOR_WARNING
                $allPassed = $false
            }
        }

        # Check frontend app if provided
        if ($FrontendAppName) {
            Write-Host "`n  Checking Frontend App..." -ForegroundColor $COLOR_INFO

            $frontendInfo = az webapp show `
                --name $FrontendAppName `
                --resource-group $ResourceGroup 2>&1 | ConvertFrom-Json

            if ($LASTEXITCODE -eq 0) {
                Write-Check -Name "Frontend app exists" -Passed $true -Value $FrontendAppName

                # Check container image
                $containerSettings = az webapp config container show `
                    --name $FrontendAppName `
                    --resource-group $ResourceGroup 2>&1 | ConvertFrom-Json

                $imageName = $containerSettings[0].value
                Write-Host "  Current image: $imageName" -ForegroundColor Gray

                # Check if image tag includes version
                $hasVersion = $imageName -match ":1\.2\.2|:latest"
                Write-Check -Name "Frontend uses versioned image" -Passed $hasVersion -Value $imageName
            } else {
                Write-Check -Name "Frontend app exists" -Passed $false -Value $FrontendAppName
                $allPassed = $false
            }
        }

    } catch {
        Write-Host "  ✗ Error checking Azure configuration: $_" -ForegroundColor $COLOR_ERROR
        return $false
    }

    return $allPassed
}

function Test-AzureAD {
    Write-Section "Azure AD Configuration"

    $allPassed = $true

    try {
        # Get current account info
        $account = az account show 2>&1 | ConvertFrom-Json

        Write-Host "  Current Azure Context:" -ForegroundColor $COLOR_INFO
        Write-Host "    Tenant ID: $($account.tenantId)" -ForegroundColor Gray
        Write-Host "    Tenant Name: $($account.tenantDisplayName)" -ForegroundColor Gray
        Write-Host "    Subscription: $($account.name)" -ForegroundColor Gray

        # Check tenant ID
        $tenantCorrect = ($account.tenantId -eq $EXPECTED_TENANT_ID)
        Write-Check -Name "Logged into correct tenant" -Passed $tenantCorrect -Value "$($account.tenantDisplayName) ($($account.tenantId))" -Expected "$TENANT_NAME ($EXPECTED_TENANT_ID)"

        if (-not $tenantCorrect) {
            Write-Host "`n  To switch tenant, run:" -ForegroundColor $COLOR_WARNING
            Write-Host "    az login --tenant $EXPECTED_TENANT_ID" -ForegroundColor $COLOR_WARNING
            $allPassed = $false
        }

        # Try to list app registrations (requires permissions)
        Write-Host "`n  Checking App Registrations..." -ForegroundColor $COLOR_INFO
        $apps = az ad app list --filter "startswith(displayName,'Azure')" 2>&1

        if ($LASTEXITCODE -eq 0) {
            $appsList = $apps | ConvertFrom-Json
            Write-Check -Name "Can list App Registrations" -Passed $true -Value "$($appsList.Count) apps found"

            # Look for advisor app
            $advisorApp = $appsList | Where-Object { $_.displayName -match "Advisor" }
            if ($advisorApp) {
                Write-Host "`n  Found Advisor App Registration:" -ForegroundColor $COLOR_INFO
                Write-Host "    Name: $($advisorApp.displayName)" -ForegroundColor Gray
                Write-Host "    App ID: $($advisorApp.appId)" -ForegroundColor Gray
            }
        } else {
            Write-Check -Name "Can list App Registrations" -Passed $false -Value "Permission denied or not found"
            Write-Host "    Note: You may not have permission to list apps" -ForegroundColor $COLOR_WARNING
        }

    } catch {
        Write-Host "  ✗ Error checking Azure AD: $_" -ForegroundColor $COLOR_ERROR
        return $false
    }

    return $allPassed
}

function Test-Connectivity {
    Write-Section "Connectivity Tests"

    $allPassed = $true

    # Test URLs if provided
    if ($BackendAppName) {
        $backendUrl = "https://$BackendAppName.azurewebsites.net"

        Write-Host "  Testing Backend Connectivity..." -ForegroundColor $COLOR_INFO

        # Health check
        try {
            $response = Invoke-WebRequest -Uri "$backendUrl/api/health/" -TimeoutSec 10 -ErrorAction Stop
            Write-Check -Name "Backend health endpoint" -Passed ($response.StatusCode -eq 200) -Value "HTTP $($response.StatusCode)"
        } catch {
            Write-Check -Name "Backend health endpoint" -Passed $false -Value $_.Exception.Message
            $allPassed = $false
        }

        # Auth config endpoint
        try {
            $response = Invoke-WebRequest -Uri "$backendUrl/api/auth/config" -TimeoutSec 10 -ErrorAction Stop
            $config = $response.Content | ConvertFrom-Json

            Write-Check -Name "Backend auth config endpoint" -Passed ($response.StatusCode -eq 200) -Value "HTTP $($response.StatusCode)"

            if ($config.tenantId) {
                $tenantCorrect = ($config.tenantId -eq $EXPECTED_TENANT_ID)
                Write-Check -Name "Backend returns correct Tenant ID" -Passed $tenantCorrect -Value $config.tenantId -Expected $EXPECTED_TENANT_ID
                $allPassed = $allPassed -and $tenantCorrect
            }
        } catch {
            Write-Check -Name "Backend auth config endpoint" -Passed $false -Value $_.Exception.Message
            $allPassed = $false
        }
    }

    if ($FrontendAppName) {
        $frontendUrl = "https://$FrontendAppName.azurewebsites.net"

        Write-Host "`n  Testing Frontend Connectivity..." -ForegroundColor $COLOR_INFO

        try {
            $response = Invoke-WebRequest -Uri "$frontendUrl/health" -TimeoutSec 10 -ErrorAction Stop
            Write-Check -Name "Frontend health endpoint" -Passed ($response.StatusCode -eq 200) -Value "HTTP $($response.StatusCode)"
        } catch {
            Write-Check -Name "Frontend health endpoint" -Passed $false -Value $_.Exception.Message
            $allPassed = $false
        }

        # Try to load main page
        try {
            $response = Invoke-WebRequest -Uri $frontendUrl -TimeoutSec 10 -ErrorAction Stop
            Write-Check -Name "Frontend main page" -Passed ($response.StatusCode -eq 200) -Value "HTTP $($response.StatusCode)"
        } catch {
            Write-Check -Name "Frontend main page" -Passed $false -Value $_.Exception.Message
            $allPassed = $false
        }
    }

    return $allPassed
}

# ============================================================================
# Main Script
# ============================================================================

Clear-Host
Write-Host @"
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║      Azure Advisor Reports - Deployment Configuration Verification      ║
║                           Version: 1.2.2                                 ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor $COLOR_INFO

Write-Host "`nExpected Tenant ID: " -NoNewline -ForegroundColor $COLOR_INFO
Write-Host "$EXPECTED_TENANT_ID ($TENANT_NAME)" -ForegroundColor White

# Run all checks
$localPassed = Test-LocalConfiguration
$azureADPassed = Test-AzureAD
$azurePassed = Test-AzureConfiguration
$connectivityPassed = Test-Connectivity

# Summary
Write-Host "`n╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor $COLOR_INFO
Write-Host "║                            VERIFICATION SUMMARY                          ║" -ForegroundColor $COLOR_INFO
Write-Host "╚══════════════════════════════════════════════════════════════════════════╝`n" -ForegroundColor $COLOR_INFO

$checks = @{
    "Local Configuration" = $localPassed
    "Azure AD" = $azureADPassed
    "Azure Configuration" = $azurePassed
    "Connectivity" = $connectivityPassed
}

foreach ($check in $checks.GetEnumerator()) {
    Write-Check -Name $check.Key -Passed $check.Value
}

$allPassed = $localPassed -and $azureADPassed -and $azurePassed -and $connectivityPassed

Write-Host ""
if ($allPassed) {
    Write-Host "✓ All checks passed! Configuration is correct." -ForegroundColor $COLOR_SUCCESS
    Write-Host "`nYou can proceed with deployment using:" -ForegroundColor $COLOR_INFO
    Write-Host "  .\deploy-production.ps1" -ForegroundColor White
    exit 0
} else {
    Write-Host "✗ Some checks failed. Please review the errors above." -ForegroundColor $COLOR_ERROR
    Write-Host "`nRefer to PRODUCTION_DEPLOYMENT_GUIDE.md for troubleshooting." -ForegroundColor $COLOR_WARNING
    exit 1
}
