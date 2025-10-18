<#
.SYNOPSIS
    Post-Deployment Verification Script for Azure Advisor Reports Platform

.DESCRIPTION
    Comprehensive verification script to test all deployed Azure resources and application functionality.
    Tests infrastructure health, connectivity, and basic application operations.

.PARAMETER Environment
    Target environment (dev, staging, or prod)

.PARAMETER ResourceGroup
    Override resource group name (default: rg-azure-advisor-reports-{environment})

.PARAMETER SkipHealthCheck
    Skip application health check endpoints

.EXAMPLE
    .\post-deployment-verify.ps1 -Environment prod

.EXAMPLE
    .\post-deployment-verify.ps1 -Environment staging -SkipHealthCheck

.NOTES
    Version: 1.0
    Last Updated: October 4, 2025
    Exit Codes:
        0 = All verifications passed
        1 = One or more verifications failed
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment,

    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup,

    [Parameter(Mandatory=$false)]
    [switch]$SkipHealthCheck
)

# Script configuration
$ErrorActionPreference = "Continue"
$script:TestsPassed = 0
$script:TestsFailed = 0
$script:TestsWarning = 0
$script:TotalTests = 15

# Resource naming convention
if (-not $ResourceGroup) {
    $ResourceGroup = "rg-azure-advisor-reports-$Environment"
}

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

function Write-TestHeader {
    param([string]$Title, [int]$Number)
    Write-Host "`n┌─────────────────────────────────────────────────────────┐" -ForegroundColor $InfoColor
    Write-Host "│  Test $Number/$script:TotalTests : $Title" -ForegroundColor $InfoColor
    Write-Host "└─────────────────────────────────────────────────────────┘" -ForegroundColor $InfoColor
}

function Write-Pass {
    param([string]$Message)
    Write-Host "  ✅ $Message" -ForegroundColor $SuccessColor
    $script:TestsPassed++
}

function Write-Fail {
    param([string]$Message)
    Write-Host "  ❌ $Message" -ForegroundColor $ErrorColor
    $script:TestsFailed++
}

function Write-Warn {
    param([string]$Message)
    Write-Host "  ⚠️  $Message" -ForegroundColor $WarningColor
    $script:TestsWarning++
}

function Write-Info {
    param([string]$Message)
    Write-Host "  ℹ️  $Message" -ForegroundColor $InfoColor
}

function Write-Detail {
    param([string]$Message)
    Write-Host "     $Message" -ForegroundColor Gray
}

function Test-ResourceGroupExists {
    Write-TestHeader "Resource Group Existence" 1

    $rg = az group show --name $ResourceGroup 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Resource group not found: $ResourceGroup"
        return $false
    }

    $rgDetails = $rg | ConvertFrom-Json

    Write-Pass "Resource group exists"
    Write-Detail "Name: $($rgDetails.name)"
    Write-Detail "Location: $($rgDetails.location)"
    Write-Detail "State: $($rgDetails.properties.provisioningState)"

    return $true
}

function Test-AppServicePlan {
    Write-TestHeader "App Service Plans" 2

    $backendPlan = "asp-advisor-backend-$Environment"
    $frontendPlan = "asp-advisor-frontend-$Environment"

    $plans = az appservice plan list --resource-group $ResourceGroup | ConvertFrom-Json

    $backendFound = $false
    $frontendFound = $false

    foreach ($plan in $plans) {
        if ($plan.name -eq $backendPlan) {
            $backendFound = $true
            Write-Detail "Backend Plan: $($plan.name) (SKU: $($plan.sku.name))"
        }
        if ($plan.name -eq $frontendPlan) {
            $frontendFound = $true
            Write-Detail "Frontend Plan: $($plan.name) (SKU: $($plan.sku.name))"
        }
    }

    if ($backendFound -and $frontendFound) {
        Write-Pass "App Service Plans deployed"
        return $true
    } else {
        if (-not $backendFound) {
            Write-Fail "Backend App Service Plan not found: $backendPlan"
        }
        if (-not $frontendFound) {
            Write-Fail "Frontend App Service Plan not found: $frontendPlan"
        }
        return $false
    }
}

function Test-WebApps {
    Write-TestHeader "Web Apps Deployment" 3

    $backendApp = "app-advisor-backend-$Environment"
    $frontendApp = "app-advisor-frontend-$Environment"

    $apps = az webapp list --resource-group $ResourceGroup | ConvertFrom-Json

    $backendFound = $false
    $frontendFound = $false
    $allRunning = $true

    foreach ($app in $apps) {
        if ($app.name -eq $backendApp) {
            $backendFound = $true
            $backendState = $app.state
            Write-Detail "Backend App: $($app.name)"
            Write-Detail "  State: $backendState"
            Write-Detail "  URL: https://$($app.defaultHostName)"

            if ($backendState -ne "Running") {
                $allRunning = $false
                Write-Warn "Backend app not running"
            }
        }
        if ($app.name -eq $frontendApp) {
            $frontendFound = $true
            $frontendState = $app.state
            Write-Detail "Frontend App: $($app.name)"
            Write-Detail "  State: $frontendState"
            Write-Detail "  URL: https://$($app.defaultHostName)"

            if ($frontendState -ne "Running") {
                $allRunning = $false
                Write-Warn "Frontend app not running"
            }
        }
    }

    if ($backendFound -and $frontendFound) {
        if ($allRunning) {
            Write-Pass "Web Apps deployed and running"
            return $true
        } else {
            Write-Warn "Web Apps deployed but not all running"
            return $true
        }
    } else {
        Write-Fail "Not all Web Apps deployed"
        return $false
    }
}

function Test-PostgreSQLServer {
    Write-TestHeader "PostgreSQL Database" 4

    $serverName = "psql-advisor-$Environment"

    $servers = az postgres flexible-server list --resource-group $ResourceGroup 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Failed to list PostgreSQL servers"
        return $false
    }

    $serverList = $servers | ConvertFrom-Json
    $server = $serverList | Where-Object { $_.name -eq $serverName }

    if (-not $server) {
        Write-Fail "PostgreSQL server not found: $serverName"
        return $false
    }

    Write-Pass "PostgreSQL server deployed"
    Write-Detail "Server: $($server.name)"
    Write-Detail "Version: $($server.version)"
    Write-Detail "State: $($server.state)"
    Write-Detail "FQDN: $($server.fullyQualifiedDomainName)"

    if ($server.state -ne "Ready") {
        Write-Warn "PostgreSQL server state is not 'Ready'"
    }

    return $true
}

function Test-RedisCache {
    Write-TestHeader "Redis Cache" 5

    $cacheName = "redis-advisor-$Environment"

    $caches = az redis list --resource-group $ResourceGroup 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Failed to list Redis caches"
        return $false
    }

    $cacheList = $caches | ConvertFrom-Json
    $cache = $cacheList | Where-Object { $_.name -eq $cacheName }

    if (-not $cache) {
        Write-Fail "Redis cache not found: $cacheName"
        return $false
    }

    Write-Pass "Redis cache deployed"
    Write-Detail "Cache: $($cache.name)"
    Write-Detail "SKU: $($cache.sku.name) $($cache.sku.family) $($cache.sku.capacity)"
    Write-Detail "State: $($cache.provisioningState)"
    Write-Detail "Hostname: $($cache.hostName)"

    if ($cache.provisioningState -ne "Succeeded") {
        Write-Warn "Redis cache provisioning state is not 'Succeeded'"
    }

    return $true
}

function Test-StorageAccount {
    Write-TestHeader "Storage Account" 6

    # Storage account names must be lowercase and no hyphens
    $storageAccountName = "stadvisor$Environment"

    $storageAccounts = az storage account list --resource-group $ResourceGroup 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Failed to list storage accounts"
        return $false
    }

    $accountList = $storageAccounts | ConvertFrom-Json
    $account = $accountList | Where-Object { $_.name -eq $storageAccountName }

    if (-not $account) {
        Write-Fail "Storage account not found: $storageAccountName"
        return $false
    }

    Write-Pass "Storage account deployed"
    Write-Detail "Account: $($account.name)"
    Write-Detail "Kind: $($account.kind)"
    Write-Detail "SKU: $($account.sku.name)"
    Write-Detail "State: $($account.provisioningState)"

    # Check blob containers
    $containers = az storage container list --account-name $storageAccountName --auth-mode login 2>&1

    if ($LASTEXITCODE -eq 0) {
        $containerList = $containers | ConvertFrom-Json
        $containerNames = $containerList.name -join ', '
        Write-Detail "Containers: $containerNames"
    } else {
        Write-Info "Could not list blob containers (permissions may be needed)"
    }

    return $true
}

function Test-KeyVault {
    Write-TestHeader "Key Vault" 7

    $keyVaultName = "kv-advisor-$Environment"

    $keyVaults = az keyvault list --resource-group $ResourceGroup 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Failed to list Key Vaults"
        return $false
    }

    $vaultList = $keyVaults | ConvertFrom-Json
    $vault = $vaultList | Where-Object { $_.name -eq $keyVaultName }

    if (-not $vault) {
        Write-Fail "Key Vault not found: $keyVaultName"
        return $false
    }

    Write-Pass "Key Vault deployed"
    Write-Detail "Vault: $($vault.name)"
    Write-Detail "SKU: $($vault.properties.sku.name)"
    Write-Detail "URI: $($vault.properties.vaultUri)"

    # Check secrets count
    $secrets = az keyvault secret list --vault-name $keyVaultName 2>&1

    if ($LASTEXITCODE -eq 0) {
        $secretList = $secrets | ConvertFrom-Json
        Write-Detail "Secrets: $($secretList.Count) stored"
    } else {
        Write-Info "Could not list secrets (permissions may be needed)"
    }

    return $true
}

function Test-ApplicationInsights {
    Write-TestHeader "Application Insights" 8

    $appInsightsName = "appi-advisor-$Environment"

    # Application Insights is under Microsoft.Insights/components
    $appInsights = az monitor app-insights component show `
        --app $appInsightsName `
        --resource-group $ResourceGroup 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Application Insights not found: $appInsightsName"
        return $false
    }

    $insights = $appInsights | ConvertFrom-Json

    Write-Pass "Application Insights deployed"
    Write-Detail "Name: $($insights.name)"
    Write-Detail "Type: $($insights.applicationType)"
    Write-Detail "State: $($insights.provisioningState)"
    Write-Detail "Instrumentation Key: $($insights.instrumentationKey.Substring(0,8))..."

    return $true
}

function Test-ManagedIdentity {
    Write-TestHeader "Managed Identity" 9

    $identityName = "id-advisor-$Environment"

    $identities = az identity list --resource-group $ResourceGroup 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Failed to list managed identities"
        return $false
    }

    $identityList = $identities | ConvertFrom-Json
    $identity = $identityList | Where-Object { $_.name -eq $identityName }

    if (-not $identity) {
        Write-Warn "Managed identity not found: $identityName (may be using system-assigned)"
        return $true
    }

    Write-Pass "Managed identity deployed"
    Write-Detail "Identity: $($identity.name)"
    Write-Detail "Principal ID: $($identity.principalId)"
    Write-Detail "Client ID: $($identity.clientId)"

    return $true
}

function Test-DatabaseConnectivity {
    Write-TestHeader "Database Connectivity" 10

    $serverName = "psql-advisor-$Environment"

    # Get server FQDN
    $server = az postgres flexible-server show `
        --resource-group $ResourceGroup `
        --name $serverName 2>&1 | ConvertFrom-Json

    if (-not $server) {
        Write-Fail "Cannot get PostgreSQL server details"
        return $false
    }

    $serverFQDN = $server.fullyQualifiedDomainName

    # Test TCP connectivity
    Write-Info "Testing connectivity to: $serverFQDN"

    try {
        $testConnection = Test-NetConnection `
            -ComputerName $serverFQDN `
            -Port 5432 `
            -InformationLevel Quiet `
            -WarningAction SilentlyContinue

        if ($testConnection) {
            Write-Pass "Database server is reachable"
            Write-Detail "Host: $serverFQDN"
            Write-Detail "Port: 5432 (Open)"
        } else {
            Write-Fail "Cannot reach database server on port 5432"
            Write-Info "Check firewall rules and network connectivity"
            return $false
        }
    } catch {
        Write-Warn "Could not test database connectivity: $_"
        return $true
    }

    return $true
}

function Test-RedisConnectivity {
    Write-TestHeader "Redis Connectivity" 11

    $cacheName = "redis-advisor-$Environment"

    # Get Redis hostname
    $cache = az redis show `
        --resource-group $ResourceGroup `
        --name $cacheName 2>&1 | ConvertFrom-Json

    if (-not $cache) {
        Write-Fail "Cannot get Redis cache details"
        return $false
    }

    $redisHostname = $cache.hostName
    $redisPort = $cache.sslPort

    Write-Info "Testing connectivity to: $redisHostname"

    try {
        $testConnection = Test-NetConnection `
            -ComputerName $redisHostname `
            -Port $redisPort `
            -InformationLevel Quiet `
            -WarningAction SilentlyContinue

        if ($testConnection) {
            Write-Pass "Redis cache is reachable"
            Write-Detail "Host: $redisHostname"
            Write-Detail "Port: $redisPort (SSL, Open)"
        } else {
            Write-Fail "Cannot reach Redis cache on port $redisPort"
            return $false
        }
    } catch {
        Write-Warn "Could not test Redis connectivity: $_"
        return $true
    }

    return $true
}

function Test-StorageConnectivity {
    Write-TestHeader "Storage Account Connectivity" 12

    $storageAccountName = "stadvisor$Environment"

    # Get storage account details
    $account = az storage account show `
        --resource-group $ResourceGroup `
        --name $storageAccountName 2>&1 | ConvertFrom-Json

    if (-not $account) {
        Write-Fail "Cannot get storage account details"
        return $false
    }

    $blobEndpoint = $account.primaryEndpoints.blob
    Write-Info "Testing connectivity to: $blobEndpoint"

    try {
        # Try to access the blob endpoint
        $response = Invoke-WebRequest -Uri $blobEndpoint -Method Head -TimeoutSec 10 -UseBasicParsing -ErrorAction SilentlyContinue

        if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 400) {
            # 400 is OK - it means the endpoint is reachable but requires auth
            Write-Pass "Storage account is reachable"
            Write-Detail "Endpoint: $blobEndpoint"
        } else {
            Write-Warn "Storage endpoint returned status: $($response.StatusCode)"
        }
    } catch {
        # Check if it's an authentication error (expected) or connectivity error
        if ($_.Exception.Message -like "*401*" -or $_.Exception.Message -like "*403*") {
            Write-Pass "Storage account is reachable (authentication required)"
        } else {
            Write-Warn "Could not reach storage account: $($_.Exception.Message)"
        }
    }

    return $true
}

function Test-BackendHealthCheck {
    Write-TestHeader "Backend Health Check" 13

    if ($SkipHealthCheck) {
        Write-Warn "Health check skipped (--SkipHealthCheck flag)"
        return $true
    }

    $backendApp = "app-advisor-backend-$Environment"

    # Get app URL
    $app = az webapp show `
        --resource-group $ResourceGroup `
        --name $backendApp 2>&1 | ConvertFrom-Json

    if (-not $app) {
        Write-Fail "Cannot get backend app details"
        return $false
    }

    $healthCheckUrl = "https://$($app.defaultHostName)/api/health/"

    Write-Info "Testing health endpoint: $healthCheckUrl"

    try {
        $response = Invoke-RestMethod -Uri $healthCheckUrl -Method Get -TimeoutSec 30 -ErrorAction Stop

        if ($response.status -eq "healthy" -or $response.status -eq "ok") {
            Write-Pass "Backend health check passed"
            Write-Detail "Status: $($response.status)"
            if ($response.database) {
                Write-Detail "Database: $($response.database)"
            }
            if ($response.redis) {
                Write-Detail "Redis: $($response.redis)"
            }
        } else {
            Write-Warn "Backend health check returned: $($response.status)"
        }
    } catch {
        Write-Fail "Backend health check failed: $($_.Exception.Message)"
        Write-Info "The application may still be starting up"
        return $false
    }

    return $true
}

function Test-FrontendAccessibility {
    Write-TestHeader "Frontend Accessibility" 14

    if ($SkipHealthCheck) {
        Write-Warn "Frontend check skipped (--SkipHealthCheck flag)"
        return $true
    }

    $frontendApp = "app-advisor-frontend-$Environment"

    # Get app URL
    $app = az webapp show `
        --resource-group $ResourceGroup `
        --name $frontendApp 2>&1 | ConvertFrom-Json

    if (-not $app) {
        Write-Fail "Cannot get frontend app details"
        return $false
    }

    $frontendUrl = "https://$($app.defaultHostName)"

    Write-Info "Testing frontend URL: $frontendUrl"

    try {
        $response = Invoke-WebRequest -Uri $frontendUrl -Method Get -TimeoutSec 30 -UseBasicParsing -ErrorAction Stop

        if ($response.StatusCode -eq 200) {
            Write-Pass "Frontend is accessible"
            Write-Detail "URL: $frontendUrl"
            Write-Detail "Status: $($response.StatusCode) OK"

            # Check if it contains React app indicators
            $content = $response.Content
            if ($content -like "*<div id=`"root`">*" -or $content -like "*React*") {
                Write-Detail "React application detected"
            }
        } else {
            Write-Warn "Frontend returned status: $($response.StatusCode)"
        }
    } catch {
        Write-Fail "Frontend is not accessible: $($_.Exception.Message)"
        Write-Info "The application may still be starting up or deploying"
        return $false
    }

    return $true
}

function Test-FrontDoor {
    Write-TestHeader "Azure Front Door (Optional)" 15

    $frontDoorName = "afd-advisor-$Environment"

    # Front Door is optional for dev environment
    if ($Environment -eq 'dev') {
        Write-Info "Front Door not expected in dev environment"
        $script:TestsPassed++  # Count as pass
        return $true
    }

    $frontDoors = az afd profile list --resource-group $ResourceGroup 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Azure Front Door not deployed (optional)"
        return $true
    }

    $fdList = $frontDoors | ConvertFrom-Json
    $fd = $fdList | Where-Object { $_.name -eq $frontDoorName }

    if (-not $fd) {
        Write-Warn "Azure Front Door not found: $frontDoorName (optional)"
        return $true
    }

    Write-Pass "Azure Front Door deployed"
    Write-Detail "Profile: $($fd.name)"
    Write-Detail "SKU: $($fd.sku.name)"
    Write-Detail "State: $($fd.provisioningState)"

    return $true
}

function Write-Summary {
    Write-Header "Post-Deployment Verification Summary"

    Write-Host "`nEnvironment: " -NoNewline -ForegroundColor White
    Write-Host $Environment.ToUpper() -ForegroundColor $HeaderColor

    Write-Host "Resource Group: " -NoNewline -ForegroundColor White
    Write-Host $ResourceGroup -ForegroundColor Gray

    Write-Host "`nVerification Results:" -ForegroundColor White
    Write-Host "  ✅ Passed:  " -NoNewline -ForegroundColor White
    Write-Host "$script:TestsPassed" -ForegroundColor $SuccessColor

    if ($script:TestsWarning -gt 0) {
        Write-Host "  ⚠️  Warnings:" -NoNewline -ForegroundColor White
        Write-Host "$script:TestsWarning" -ForegroundColor $WarningColor
    }

    if ($script:TestsFailed -gt 0) {
        Write-Host "  ❌ Failed:  " -NoNewline -ForegroundColor White
        Write-Host "$script:TestsFailed" -ForegroundColor $ErrorColor
    }

    Write-Host "`nTotal Tests: " -NoNewline -ForegroundColor White
    Write-Host "$script:TotalTests" -ForegroundColor Gray

    $percentage = [math]::Round(($script:TestsPassed / $script:TotalTests) * 100)

    Write-Host "`n" -NoNewline
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor $HeaderColor

    if ($script:TestsFailed -eq 0) {
        Write-Host "`n✅ Deployment verification passed! ($percentage% success)" -ForegroundColor $SuccessColor

        if ($script:TestsWarning -gt 0) {
            Write-Host "`n⚠️  $script:TestsWarning warning(s) detected. Review before production use." -ForegroundColor $WarningColor
        }

        Write-Host "`nNext Steps:" -ForegroundColor White
        Write-Host "  1. Test application functionality manually" -ForegroundColor Gray
        Write-Host "  2. Run integration tests" -ForegroundColor Gray
        Write-Host "  3. Configure monitoring alerts" -ForegroundColor Gray
        Write-Host "  4. Setup backups and disaster recovery" -ForegroundColor Gray
        Write-Host "  5. Update DNS and custom domains (if applicable)" -ForegroundColor Gray

        # Show application URLs
        Write-Host "`nApplication URLs:" -ForegroundColor White
        Write-Host "  Backend:  https://app-advisor-backend-$Environment.azurewebsites.net" -ForegroundColor $InfoColor
        Write-Host "  Frontend: https://app-advisor-frontend-$Environment.azurewebsites.net" -ForegroundColor $InfoColor
        Write-Host "  Health:   https://app-advisor-backend-$Environment.azurewebsites.net/api/health/" -ForegroundColor Gray

        return 0
    } else {
        Write-Host "`n❌ Deployment verification failed! ($percentage% success)" -ForegroundColor $ErrorColor
        Write-Host "   $script:TestsFailed test(s) failed" -ForegroundColor $ErrorColor

        Write-Host "`nRequired Actions:" -ForegroundColor White
        Write-Host "  1. Review failed tests above" -ForegroundColor Gray
        Write-Host "  2. Check Azure Portal for resource status" -ForegroundColor Gray
        Write-Host "  3. Review deployment logs" -ForegroundColor Gray
        Write-Host "  4. Fix issues and re-deploy if necessary" -ForegroundColor Gray
        Write-Host "  5. Re-run verification after fixes" -ForegroundColor Gray

        return 1
    }
}

# Main Script Execution
Clear-Host

Write-Header "Post-Deployment Verification for Azure Advisor Reports"

Write-Host "Environment: " -NoNewline -ForegroundColor White
Write-Host $Environment.ToUpper() -ForegroundColor $HeaderColor

Write-Host "Resource Group: " -NoNewline -ForegroundColor White
Write-Host $ResourceGroup -ForegroundColor Gray

Write-Host "`nThis script will verify:" -ForegroundColor White
Write-Host "  - All Azure resources are deployed" -ForegroundColor Gray
Write-Host "  - Services are running and accessible" -ForegroundColor Gray
Write-Host "  - Network connectivity is working" -ForegroundColor Gray
Write-Host "  - Health check endpoints respond" -ForegroundColor Gray

Write-Host "`nStarting verification..." -ForegroundColor $InfoColor

# Run all tests
Test-ResourceGroupExists
Test-AppServicePlan
Test-WebApps
Test-PostgreSQLServer
Test-RedisCache
Test-StorageAccount
Test-KeyVault
Test-ApplicationInsights
Test-ManagedIdentity
Test-DatabaseConnectivity
Test-RedisConnectivity
Test-StorageConnectivity
Test-BackendHealthCheck
Test-FrontendAccessibility
Test-FrontDoor

# Display summary and exit
$exitCode = Write-Summary
Write-Host ""
exit $exitCode
