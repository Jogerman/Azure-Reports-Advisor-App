# ============================================================================
# Azure Advisor Reports Platform - Production Deployment Script
# Version: 1.2.2
# ============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$RegistryName,

    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,

    [Parameter(Mandatory=$false)]
    [string]$Version = "1.2.2",

    [Parameter(Mandatory=$false)]
    [string]$BackendAppName = "",

    [Parameter(Mandatory=$false)]
    [string]$FrontendAppName = "",

    [Parameter(Mandatory=$false)]
    [string]$AzureClientId = "",

    [Parameter(Mandatory=$false)]
    [string]$BackendUrl = "",

    [Parameter(Mandatory=$false)]
    [string]$FrontendUrl = "",

    [Parameter(Mandatory=$false)]
    [switch]$SkipBackend = $false,

    [Parameter(Mandatory=$false)]
    [switch]$SkipFrontend = $false,

    [Parameter(Mandatory=$false)]
    [switch]$BuildOnly = $false
)

# ============================================================================
# Constants
# ============================================================================

$TENANT_ID = "9acf6dd6-1978-4d9c-9a9c-c9be95245565"
$SOLVEX_TENANT = "Solvex Dominicana"
$PROJECT_ROOT = $PSScriptRoot
$BACKEND_PATH = Join-Path $PROJECT_ROOT "azure_advisor_reports"
$FRONTEND_PATH = Join-Path $PROJECT_ROOT "frontend"

# Colors for output
$COLOR_SUCCESS = "Green"
$COLOR_ERROR = "Red"
$COLOR_WARNING = "Yellow"
$COLOR_INFO = "Cyan"

# ============================================================================
# Functions
# ============================================================================

function Write-Step {
    param([string]$Message)
    Write-Host "`n========================================" -ForegroundColor $COLOR_INFO
    Write-Host $Message -ForegroundColor $COLOR_INFO
    Write-Host "========================================`n" -ForegroundColor $COLOR_INFO
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor $COLOR_SUCCESS
}

function Write-Error-Message {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor $COLOR_ERROR
}

function Write-Warning-Message {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor $COLOR_WARNING
}

function Test-AzureCLI {
    Write-Step "Verificando Azure CLI"

    try {
        $azVersion = az version --output json | ConvertFrom-Json
        Write-Success "Azure CLI instalado: $($azVersion.'azure-cli')"

        # Verificar login
        $account = az account show 2>&1 | ConvertFrom-Json
        if ($account) {
            Write-Success "Autenticado como: $($account.user.name)"
            Write-Success "Subscription: $($account.name)"
            Write-Success "Tenant ID: $($account.tenantId)"

            # Verificar que estamos en el tenant correcto
            if ($account.tenantId -ne $TENANT_ID) {
                Write-Warning-Message "WARNING: Tenant ID actual ($($account.tenantId)) no coincide con el tenant esperado ($TENANT_ID - $SOLVEX_TENANT)"
                Write-Host "`nDesea continuar de todas formas? (y/n): " -NoNewline
                $response = Read-Host
                if ($response -ne "y") {
                    Write-Error-Message "Deployment cancelado por el usuario"
                    exit 1
                }
            } else {
                Write-Success "Tenant correcto: $SOLVEX_TENANT"
            }
        } else {
            Write-Error-Message "No está autenticado en Azure CLI"
            Write-Host "Ejecute: az login"
            exit 1
        }
    }
    catch {
        Write-Error-Message "Azure CLI no está instalado o no está en el PATH"
        Write-Host "Instale Azure CLI desde: https://docs.microsoft.com/cli/azure/install-azure-cli"
        exit 1
    }
}

function Test-Docker {
    Write-Step "Verificando Docker"

    try {
        $dockerVersion = docker version --format '{{.Server.Version}}'
        Write-Success "Docker instalado: $dockerVersion"

        # Verificar que Docker esté corriendo
        docker ps > $null 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Docker daemon está corriendo"
        } else {
            Write-Error-Message "Docker daemon no está corriendo"
            Write-Host "Inicie Docker Desktop"
            exit 1
        }
    }
    catch {
        Write-Error-Message "Docker no está instalado o no está en el PATH"
        exit 1
    }
}

function Get-UserConfirmation {
    param(
        [string]$Message,
        [hashtable]$Details
    )

    Write-Host "`n$Message" -ForegroundColor $COLOR_WARNING
    Write-Host "Detalles del deployment:" -ForegroundColor $COLOR_INFO

    foreach ($key in $Details.Keys) {
        Write-Host "  $key : " -NoNewline -ForegroundColor $COLOR_INFO
        Write-Host $Details[$key] -ForegroundColor White
    }

    Write-Host "`n¿Desea continuar? (y/n): " -NoNewline -ForegroundColor $COLOR_WARNING
    $response = Read-Host

    return ($response -eq "y")
}

function Build-BackendImage {
    Write-Step "Building Backend Image (Django)"

    try {
        # Login to Azure Container Registry
        Write-Host "Logging in to Azure Container Registry..."
        az acr login --name $RegistryName

        if ($LASTEXITCODE -ne 0) {
            Write-Error-Message "Failed to login to Azure Container Registry"
            return $false
        }

        $registryUrl = "$RegistryName.azurecr.io"
        $imageName = "azure-advisor-backend"
        $imageTag = "$registryUrl/${imageName}:${Version}"
        $imageLatest = "$registryUrl/${imageName}:latest"

        Write-Host "Building backend image directly in Azure..."
        Write-Host "Registry: $registryUrl"
        Write-Host "Image: $imageName"
        Write-Host "Version: $Version"

        # Build using az acr build (recommended for production)
        az acr build --registry $RegistryName `
            --image "${imageName}:${Version}" `
            --image "${imageName}:latest" `
            --file azure_advisor_reports/Dockerfile.prod `
            --platform linux `
            azure_advisor_reports

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Backend image built and pushed successfully"
            Write-Success "Image: $imageTag"
            return $true
        } else {
            Write-Error-Message "Failed to build backend image"
            return $false
        }
    }
    catch {
        Write-Error-Message "Error building backend image: $_"
        return $false
    }
}

function Build-FrontendImage {
    Write-Step "Building Frontend Image (React)"

    # Validate required parameters
    if ([string]::IsNullOrEmpty($AzureClientId)) {
        Write-Error-Message "AzureClientId is required for frontend build"
        Write-Host "Use parameter: -AzureClientId <your-client-id>"
        return $false
    }

    if ([string]::IsNullOrEmpty($BackendUrl)) {
        Write-Error-Message "BackendUrl is required for frontend build"
        Write-Host "Use parameter: -BackendUrl <your-backend-url>"
        return $false
    }

    if ([string]::IsNullOrEmpty($FrontendUrl)) {
        Write-Error-Message "FrontendUrl is required for frontend build"
        Write-Host "Use parameter: -FrontendUrl <your-frontend-url>"
        return $false
    }

    try {
        # Login to Azure Container Registry
        Write-Host "Logging in to Azure Container Registry..."
        az acr login --name $RegistryName

        if ($LASTEXITCODE -ne 0) {
            Write-Error-Message "Failed to login to Azure Container Registry"
            return $false
        }

        $registryUrl = "$RegistryName.azurecr.io"
        $imageName = "azure-advisor-frontend"
        $imageTag = "$registryUrl/${imageName}:${Version}"
        $imageLatest = "$registryUrl/${imageName}:latest"

        Write-Host "Building frontend image directly in Azure..."
        Write-Host "Registry: $registryUrl"
        Write-Host "Image: $imageName"
        Write-Host "Version: $Version"
        Write-Host "API URL: $BackendUrl"
        Write-Host "Client ID: $AzureClientId"
        Write-Host "Tenant ID: $TENANT_ID"
        Write-Host "Redirect URI: $FrontendUrl"

        # Build using az acr build with build arguments
        az acr build --registry $RegistryName `
            --image "${imageName}:${Version}" `
            --image "${imageName}:latest" `
            --build-arg REACT_APP_API_URL="${BackendUrl}/api" `
            --build-arg REACT_APP_AZURE_CLIENT_ID="$AzureClientId" `
            --build-arg REACT_APP_AZURE_TENANT_ID="$TENANT_ID" `
            --build-arg REACT_APP_AZURE_REDIRECT_URI="$FrontendUrl" `
            --build-arg REACT_APP_ENVIRONMENT="production" `
            --file frontend/Dockerfile.prod `
            --platform linux `
            frontend

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Frontend image built and pushed successfully"
            Write-Success "Image: $imageTag"
            return $true
        } else {
            Write-Error-Message "Failed to build frontend image"
            return $false
        }
    }
    catch {
        Write-Error-Message "Error building frontend image: $_"
        return $false
    }
}

function Deploy-Backend {
    Write-Step "Deploying Backend to Azure"

    if ([string]::IsNullOrEmpty($BackendAppName)) {
        Write-Error-Message "BackendAppName is required for deployment"
        Write-Host "Use parameter: -BackendAppName <your-app-name>"
        return $false
    }

    try {
        $registryUrl = "$RegistryName.azurecr.io"
        $imageName = "azure-advisor-backend"
        $imageTag = "$registryUrl/${imageName}:${Version}"

        Write-Host "Updating Azure App Service with new image..."
        Write-Host "App: $BackendAppName"
        Write-Host "Image: $imageTag"

        # Update container image
        az webapp config container set `
            --name $BackendAppName `
            --resource-group $ResourceGroup `
            --docker-custom-image-name $imageTag `
            --docker-registry-server-url "https://$registryUrl"

        if ($LASTEXITCODE -ne 0) {
            Write-Error-Message "Failed to update backend container"
            return $false
        }

        # Restart the app
        Write-Host "Restarting backend app..."
        az webapp restart --name $BackendAppName --resource-group $ResourceGroup

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Backend deployed successfully"
            Write-Host "`nBackend URL: https://$BackendAppName.azurewebsites.net" -ForegroundColor $COLOR_INFO
            return $true
        } else {
            Write-Error-Message "Failed to restart backend app"
            return $false
        }
    }
    catch {
        Write-Error-Message "Error deploying backend: $_"
        return $false
    }
}

function Deploy-Frontend {
    Write-Step "Deploying Frontend to Azure"

    if ([string]::IsNullOrEmpty($FrontendAppName)) {
        Write-Error-Message "FrontendAppName is required for deployment"
        Write-Host "Use parameter: -FrontendAppName <your-app-name>"
        return $false
    }

    try {
        $registryUrl = "$RegistryName.azurecr.io"
        $imageName = "azure-advisor-frontend"
        $imageTag = "$registryUrl/${imageName}:${Version}"

        Write-Host "Updating Azure App Service with new image..."
        Write-Host "App: $FrontendAppName"
        Write-Host "Image: $imageTag"

        # Update container image
        az webapp config container set `
            --name $FrontendAppName `
            --resource-group $ResourceGroup `
            --docker-custom-image-name $imageTag `
            --docker-registry-server-url "https://$registryUrl"

        if ($LASTEXITCODE -ne 0) {
            Write-Error-Message "Failed to update frontend container"
            return $false
        }

        # Restart the app
        Write-Host "Restarting frontend app..."
        az webapp restart --name $FrontendAppName --resource-group $ResourceGroup

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Frontend deployed successfully"
            Write-Host "`nFrontend URL: https://$FrontendAppName.azurewebsites.net" -ForegroundColor $COLOR_INFO
            return $true
        } else {
            Write-Error-Message "Failed to restart frontend app"
            return $false
        }
    }
    catch {
        Write-Error-Message "Error deploying frontend: $_"
        return $false
    }
}

function Test-Deployment {
    Write-Step "Testing Deployment"

    $allHealthy = $true

    # Test backend
    if (-not $SkipBackend -and -not [string]::IsNullOrEmpty($BackendAppName)) {
        Write-Host "Testing backend health..."
        $backendUrl = "https://$BackendAppName.azurewebsites.net/api/health/"

        try {
            $response = Invoke-WebRequest -Uri $backendUrl -TimeoutSec 30 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Success "Backend health check passed"
            } else {
                Write-Error-Message "Backend health check failed: HTTP $($response.StatusCode)"
                $allHealthy = $false
            }
        }
        catch {
            Write-Error-Message "Backend health check failed: $_"
            $allHealthy = $false
        }
    }

    # Test frontend
    if (-not $SkipFrontend -and -not [string]::IsNullOrEmpty($FrontendAppName)) {
        Write-Host "Testing frontend health..."
        $frontendUrl = "https://$FrontendAppName.azurewebsites.net/health"

        try {
            $response = Invoke-WebRequest -Uri $frontendUrl -TimeoutSec 30 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Success "Frontend health check passed"
            } else {
                Write-Error-Message "Frontend health check failed: HTTP $($response.StatusCode)"
                $allHealthy = $false
            }
        }
        catch {
            Write-Error-Message "Frontend health check failed: $_"
            $allHealthy = $false
        }
    }

    return $allHealthy
}

# ============================================================================
# Main Script
# ============================================================================

Clear-Host
Write-Host @"
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║         Azure Advisor Reports Platform - Production Deployment          ║
║                           Version: $Version                              ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor $COLOR_INFO

# Verify prerequisites
Test-AzureCLI
Test-Docker

# Get user confirmation
$deploymentDetails = @{
    "Version" = $Version
    "Registry" = "$RegistryName.azurecr.io"
    "Resource Group" = $ResourceGroup
    "Tenant ID" = "$TENANT_ID ($SOLVEX_TENANT)"
}

if (-not $SkipBackend) {
    $deploymentDetails["Backend App"] = if ($BackendAppName) { $BackendAppName } else { "Build Only" }
}

if (-not $SkipFrontend) {
    $deploymentDetails["Frontend App"] = if ($FrontendAppName) { $FrontendAppName } else { "Build Only" }
    $deploymentDetails["Azure Client ID"] = $AzureClientId
    $deploymentDetails["Backend URL"] = $BackendUrl
    $deploymentDetails["Frontend URL"] = $FrontendUrl
}

if ($BuildOnly) {
    $deploymentDetails["Mode"] = "Build Only (No Deployment)"
}

$confirmed = Get-UserConfirmation -Message "PRODUCTION DEPLOYMENT" -Details $deploymentDetails

if (-not $confirmed) {
    Write-Warning-Message "Deployment canceled by user"
    exit 0
}

# Track overall success
$overallSuccess = $true

# Build and deploy backend
if (-not $SkipBackend) {
    $backendBuildSuccess = Build-BackendImage
    $overallSuccess = $overallSuccess -and $backendBuildSuccess

    if ($backendBuildSuccess -and -not $BuildOnly -and -not [string]::IsNullOrEmpty($BackendAppName)) {
        $backendDeploySuccess = Deploy-Backend
        $overallSuccess = $overallSuccess -and $backendDeploySuccess
    }
}

# Build and deploy frontend
if (-not $SkipFrontend) {
    $frontendBuildSuccess = Build-FrontendImage
    $overallSuccess = $overallSuccess -and $frontendBuildSuccess

    if ($frontendBuildSuccess -and -not $BuildOnly -and -not [string]::IsNullOrEmpty($FrontendAppName)) {
        $frontendDeploySuccess = Deploy-Frontend
        $overallSuccess = $overallSuccess -and $frontendDeploySuccess
    }
}

# Test deployment
if (-not $BuildOnly) {
    Start-Sleep -Seconds 10  # Wait for apps to start
    $testSuccess = Test-Deployment
    $overallSuccess = $overallSuccess -and $testSuccess
}

# Summary
Write-Host "`n╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor $COLOR_INFO
Write-Host "║                        DEPLOYMENT SUMMARY                                ║" -ForegroundColor $COLOR_INFO
Write-Host "╚══════════════════════════════════════════════════════════════════════════╝`n" -ForegroundColor $COLOR_INFO

if ($overallSuccess) {
    Write-Success "Deployment completed successfully!"

    Write-Host "`nNext steps:" -ForegroundColor $COLOR_INFO
    Write-Host "1. Verify authentication with correct Tenant ID in browser"
    Write-Host "2. Check Application Insights for any errors"
    Write-Host "3. Run smoke tests"
    Write-Host "4. Monitor performance metrics"

    if (-not [string]::IsNullOrEmpty($BackendAppName)) {
        Write-Host "`nBackend URL: https://$BackendAppName.azurewebsites.net" -ForegroundColor $COLOR_INFO
    }
    if (-not [string]::IsNullOrEmpty($FrontendAppName)) {
        Write-Host "Frontend URL: https://$FrontendAppName.azurewebsites.net" -ForegroundColor $COLOR_INFO
    }

    exit 0
} else {
    Write-Error-Message "Deployment completed with errors"
    Write-Host "`nCheck the logs above for details" -ForegroundColor $COLOR_WARNING
    Write-Host "For troubleshooting, see: PRODUCTION_DEPLOYMENT_GUIDE.md" -ForegroundColor $COLOR_WARNING
    exit 1
}
