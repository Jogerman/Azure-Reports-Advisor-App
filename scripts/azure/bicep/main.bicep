// ================================
// Azure Advisor Reports Platform
// Main Bicep Template
// ================================

targetScope = 'subscription'

@description('Environment name (dev, staging, prod)')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Location for all resources')
param location string = 'eastus2'

@description('Resource group name prefix')
param resourceGroupPrefix string = 'rg-azure-advisor'

@description('Application name prefix')
param appNamePrefix string = 'azure-advisor'

@description('Azure AD client ID for authentication')
param azureAdClientId string

@description('Azure AD tenant ID')
param azureAdTenantId string

@secure()
@description('Azure AD client secret')
param azureAdClientSecret string

@description('Custom domain name (optional)')
param customDomain string = ''

@description('Enable Application Insights')
param enableAppInsights bool = true

@description('Enable Azure Front Door')
param enableFrontDoor bool = true

@description('Tags to apply to all resources')
param tags object = {
  Environment: environment
  Project: 'AzureAdvisorReports'
  ManagedBy: 'Bicep'
  CreatedDate: utcNow('yyyy-MM-dd')
}

// ================================
// Variables
// ================================
var resourceGroupName = '${resourceGroupPrefix}-${environment}'
var appNameSuffix = environment == 'prod' ? '' : '-${environment}'

// ================================
// Resource Group
// ================================
resource resourceGroup 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

// ================================
// Main Infrastructure Module
// ================================
module infrastructure 'modules/infrastructure.bicep' = {
  scope: resourceGroup
  name: 'infrastructure-deployment'
  params: {
    location: location
    environment: environment
    appNamePrefix: appNamePrefix
    appNameSuffix: appNameSuffix
    tags: tags
    enableAppInsights: enableAppInsights
  }
}

// ================================
// Security Module
// ================================
module security 'modules/security.bicep' = {
  scope: resourceGroup
  name: 'security-deployment'
  dependsOn: [infrastructure]
  params: {
    location: location
    environment: environment
    appNamePrefix: appNamePrefix
    appNameSuffix: appNameSuffix
    tags: tags
    azureAdClientId: azureAdClientId
    azureAdTenantId: azureAdTenantId
    azureAdClientSecret: azureAdClientSecret
    appServiceBackendName: infrastructure.outputs.appServiceBackendName
    appServiceFrontendName: infrastructure.outputs.appServiceFrontendName
  }
}

// ================================
// Networking Module (Optional)
// ================================
module networking 'modules/networking.bicep' = if (enableFrontDoor) {
  scope: resourceGroup
  name: 'networking-deployment'
  dependsOn: [infrastructure]
  params: {
    location: location
    environment: environment
    appNamePrefix: appNamePrefix
    appNameSuffix: appNameSuffix
    tags: tags
    customDomain: customDomain
    backendUrl: infrastructure.outputs.appServiceBackendUrl
    frontendUrl: infrastructure.outputs.appServiceFrontendUrl
  }
}

// ================================
// Outputs
// ================================
output resourceGroupName string = resourceGroupName
output subscriptionId string = subscription().subscriptionId

// Infrastructure outputs
output appServiceBackendName string = infrastructure.outputs.appServiceBackendName
output appServiceBackendUrl string = infrastructure.outputs.appServiceBackendUrl
output appServiceFrontendName string = infrastructure.outputs.appServiceFrontendName
output appServiceFrontendUrl string = infrastructure.outputs.appServiceFrontendUrl

output postgreSqlServerName string = infrastructure.outputs.postgreSqlServerName
output postgreSqlDatabaseName string = infrastructure.outputs.postgreSqlDatabaseName
output postgreSqlConnectionString string = infrastructure.outputs.postgreSqlConnectionString

output redisName string = infrastructure.outputs.redisName
output redisConnectionString string = infrastructure.outputs.redisConnectionString

output storageAccountName string = infrastructure.outputs.storageAccountName
output storageAccountConnectionString string = infrastructure.outputs.storageAccountConnectionString

output appInsightsName string = enableAppInsights ? infrastructure.outputs.appInsightsName : ''
output appInsightsConnectionString string = enableAppInsights ? infrastructure.outputs.appInsightsConnectionString : ''

// Security outputs
output keyVaultName string = security.outputs.keyVaultName
output keyVaultUri string = security.outputs.keyVaultUri

// Networking outputs (if enabled)
output frontDoorEndpoint string = enableFrontDoor ? networking.outputs.frontDoorEndpoint : ''
output frontDoorName string = enableFrontDoor ? networking.outputs.frontDoorName : ''

// Deployment information
output deploymentInfo object = {
  timestamp: deployment().properties.timestamp
  correlationId: deployment().properties.correlationId
  environment: environment
  location: location
  resourceGroupName: resourceGroupName
}