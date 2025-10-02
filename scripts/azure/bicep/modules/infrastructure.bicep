// ================================
// Infrastructure Module
// Core Azure Resources
// ================================

@description('Location for all resources')
param location string

@description('Environment name')
param environment string

@description('Application name prefix')
param appNamePrefix string

@description('Application name suffix')
param appNameSuffix string

@description('Resource tags')
param tags object

@description('Enable Application Insights')
param enableAppInsights bool = true

// ================================
// Variables
// ================================
var environmentConfig = {
  dev: {
    appServicePlanSku: 'B1'
    appServicePlanCapacity: 1
    postgreSqlSku: 'Standard_B2s'
    postgreSqlStorageMB: 32768
    redisSku: 'Basic'
    redisCapacity: 0
  }
  staging: {
    appServicePlanSku: 'S2'
    appServicePlanCapacity: 1
    postgreSqlSku: 'GeneralPurpose_D2s_v3'
    postgreSqlStorageMB: 65536
    redisSku: 'Standard'
    redisCapacity: 1
  }
  prod: {
    appServicePlanSku: 'P2v3'
    appServicePlanCapacity: 2
    postgreSqlSku: 'GeneralPurpose_D4s_v3'
    postgreSqlStorageMB: 131072
    redisSku: 'Premium'
    redisCapacity: 1
  }
}

var config = environmentConfig[environment]

// Resource names
var appServicePlanBackendName = '${appNamePrefix}-backend-asp${appNameSuffix}'
var appServicePlanFrontendName = '${appNamePrefix}-frontend-asp${appNameSuffix}'
var appServiceBackendName = '${appNamePrefix}-backend${appNameSuffix}'
var appServiceFrontendName = '${appNamePrefix}-frontend${appNameSuffix}'
var postgreSqlServerName = '${appNamePrefix}-psql${appNameSuffix}'
var postgreSqlDatabaseName = 'azure_advisor_reports'
var redisName = '${appNamePrefix}-redis${appNameSuffix}'
var storageAccountName = replace('${appNamePrefix}stor${appNameSuffix}', '-', '')
var appInsightsName = '${appNamePrefix}-ai${appNameSuffix}'
var logAnalyticsWorkspaceName = '${appNamePrefix}-law${appNameSuffix}'

// ================================
// Log Analytics Workspace
// ================================
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = if (enableAppInsights) {
  name: logAnalyticsWorkspaceName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    workspaceCapping: {
      dailyQuotaGb: 1
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// ================================
// Application Insights
// ================================
resource appInsights 'Microsoft.Insights/components@2020-02-02' = if (enableAppInsights) {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Flow_Type: 'Redfield'
    Request_Source: 'IbizaAIExtension'
    WorkspaceResourceId: enableAppInsights ? logAnalyticsWorkspace.id : null
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// ================================
// Storage Account
// ================================
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    dnsEndpointType: 'Standard'
    defaultToOAuthAuthentication: false
    publicNetworkAccess: 'Enabled'
    allowCrossTenantReplication: false
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true
    networkAcls: {
      bypass: 'AzureServices'
      virtualNetworkRules: []
      ipRules: []
      defaultAction: 'Allow'
    }
    supportsHttpsTrafficOnly: true
    encryption: {
      requireInfrastructureEncryption: false
      services: {
        file: {
          keyType: 'Account'
          enabled: true
        }
        blob: {
          keyType: 'Account'
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
    accessTier: 'Hot'
  }
}

// ================================
// Storage Containers
// ================================
resource blobServices 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    changeFeed: {
      enabled: false
    }
    restorePolicy: {
      enabled: false
    }
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    isVersioningEnabled: false
  }
}

var containers = [
  'csv-uploads'
  'reports-html'
  'reports-pdf'
  'static-assets'
]

resource storageContainers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = [for containerName in containers: {
  parent: blobServices
  name: containerName
  properties: {
    immutableStorageWithVersioning: {
      enabled: false
    }
    defaultEncryptionScope: '$account-encryption-key'
    denyEncryptionScopeOverride: false
    publicAccess: containerName == 'static-assets' ? 'Blob' : 'None'
  }
}]

// ================================
// PostgreSQL Server
// ================================
resource postgreSqlServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-06-01-preview' = {
  name: postgreSqlServerName
  location: location
  tags: tags
  sku: {
    name: config.postgreSqlSku
    tier: startsWith(config.postgreSqlSku, 'Standard_B') ? 'Burstable' : 'GeneralPurpose'
  }
  properties: {
    createMode: 'Default'
    version: '15'
    administratorLogin: 'postgres'
    administratorLoginPassword: '${uniqueString(resourceGroup().id)}Aa1!'
    availabilityZone: '1'
    storage: {
      storageSizeGB: config.postgreSqlStorageMB / 1024
      autoGrow: 'Enabled'
      type: 'PremiumV2_LRS'
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: environment == 'prod' ? 'ZoneRedundant' : 'Disabled'
    }
    network: {
      delegatedSubnetResourceId: null
      privateDnsZoneArmResourceId: null
      publicNetworkAccess: 'Enabled'
    }
  }
}

// ================================
// PostgreSQL Database
// ================================
resource postgreSqlDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-06-01-preview' = {
  parent: postgreSqlServer
  name: postgreSqlDatabaseName
  properties: {
    charset: 'utf8'
    collation: 'en_US.utf8'
  }
}

// ================================
// PostgreSQL Firewall Rules
// ================================
resource postgreSqlFirewallRuleAzure 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-06-01-preview' = {
  parent: postgreSqlServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// ================================
// Redis Cache
// ================================
resource redisCache 'Microsoft.Cache/redis@2023-08-01' = {
  name: redisName
  location: location
  tags: tags
  properties: {
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
    sku: {
      capacity: config.redisCapacity
      family: config.redisSku == 'Premium' ? 'P' : 'C'
      name: config.redisSku
    }
    redisConfiguration: {
      'rdb-backup-enabled': config.redisSku == 'Premium' ? 'true' : 'false'
      'rdb-storage-connection-string': config.redisSku == 'Premium' ? storageAccount.properties.primaryEndpoints.blob : ''
    }
    publicNetworkAccess: 'Enabled'
  }
}

// ================================
// App Service Plans
// ================================
resource appServicePlanBackend 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanBackendName
  location: location
  tags: tags
  sku: {
    name: config.appServicePlanSku
    capacity: config.appServicePlanCapacity
  }
  kind: 'linux'
  properties: {
    perSiteScaling: false
    elasticScaleEnabled: false
    maximumElasticWorkerCount: 1
    isSpot: false
    reserved: true
    isXenon: false
    hyperV: false
    targetWorkerCount: 0
    targetWorkerSizeId: 0
    zoneRedundant: false
  }
}

resource appServicePlanFrontend 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanFrontendName
  location: location
  tags: tags
  sku: {
    name: environment == 'dev' ? 'B1' : config.appServicePlanSku
    capacity: 1
  }
  kind: 'linux'
  properties: {
    perSiteScaling: false
    elasticScaleEnabled: false
    maximumElasticWorkerCount: 1
    isSpot: false
    reserved: true
    isXenon: false
    hyperV: false
    targetWorkerCount: 0
    targetWorkerSizeId: 0
    zoneRedundant: false
  }
}

// ================================
// Backend App Service
// ================================
resource appServiceBackend 'Microsoft.Web/sites@2023-01-01' = {
  name: appServiceBackendName
  location: location
  tags: tags
  properties: {
    enabled: true
    hostNameSslStates: [
      {
        name: '${appServiceBackendName}.azurewebsites.net'
        sslState: 'Disabled'
        hostType: 'Standard'
      }
      {
        name: '${appServiceBackendName}.scm.azurewebsites.net'
        sslState: 'Disabled'
        hostType: 'Repository'
      }
    ]
    serverFarmId: appServicePlanBackend.id
    reserved: true
    isXenon: false
    hyperV: false
    vnetRouteAllEnabled: false
    vnetImagePullEnabled: false
    vnetContentShareEnabled: false
    siteConfig: {
      numberOfWorkers: 1
      linuxFxVersion: 'PYTHON|3.11'
      acrUseManagedIdentityCreds: false
      alwaysOn: config.appServicePlanSku != 'F1' && config.appServicePlanSku != 'D1'
      http20Enabled: true
      functionAppScaleLimit: 0
      minimumElasticInstanceCount: 0
      appSettings: [
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        {
          name: 'DJANGO_SETTINGS_MODULE'
          value: 'azure_advisor_reports.settings.production'
        }
        {
          name: 'PYTHONPATH'
          value: '/home/site/wwwroot'
        }
        {
          name: 'AZURE_STORAGE_CONNECTION_STRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${az.environment().suffixes.storage}'
        }
        {
          name: 'DATABASE_URL'
          value: 'postgresql://postgres:${uniqueString(resourceGroup().id)}Aa1!@${postgreSqlServer.properties.fullyQualifiedDomainName}:5432/${postgreSqlDatabaseName}'
        }
        {
          name: 'REDIS_URL'
          value: 'rediss://:${redisCache.listKeys().primaryKey}@${redisCache.properties.hostName}:${redisCache.properties.sslPort}/0'
        }
        {
          name: 'CELERY_BROKER_URL'
          value: 'rediss://:${redisCache.listKeys().primaryKey}@${redisCache.properties.hostName}:${redisCache.properties.sslPort}/0'
        }
        {
          name: 'CELERY_RESULT_BACKEND'
          value: 'rediss://:${redisCache.listKeys().primaryKey}@${redisCache.properties.hostName}:${redisCache.properties.sslPort}/0'
        }
        {
          name: 'APPINSIGHTS_CONNECTION_STRING'
          value: enableAppInsights ? appInsights.properties.ConnectionString : ''
        }
      ]
    }
    scmSiteAlsoStopped: false
    clientAffinityEnabled: false
    clientCertEnabled: false
    clientCertMode: 'Required'
    hostNamesDisabled: false
    containerSize: 0
    dailyMemoryTimeQuota: 0
    httpsOnly: true
    redundancyMode: 'None'
    storageAccountRequired: false
    keyVaultReferenceIdentity: 'SystemAssigned'
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// ================================
// Frontend App Service
// ================================
resource appServiceFrontend 'Microsoft.Web/sites@2023-01-01' = {
  name: appServiceFrontendName
  location: location
  tags: tags
  properties: {
    enabled: true
    hostNameSslStates: [
      {
        name: '${appServiceFrontendName}.azurewebsites.net'
        sslState: 'Disabled'
        hostType: 'Standard'
      }
      {
        name: '${appServiceFrontendName}.scm.azurewebsites.net'
        sslState: 'Disabled'
        hostType: 'Repository'
      }
    ]
    serverFarmId: appServicePlanFrontend.id
    reserved: true
    isXenon: false
    hyperV: false
    vnetRouteAllEnabled: false
    vnetImagePullEnabled: false
    vnetContentShareEnabled: false
    siteConfig: {
      numberOfWorkers: 1
      linuxFxVersion: 'NODE|18-lts'
      acrUseManagedIdentityCreds: false
      alwaysOn: true
      http20Enabled: true
      functionAppScaleLimit: 0
      minimumElasticInstanceCount: 0
      appSettings: [
        {
          name: 'WEBSITE_NODE_DEFAULT_VERSION'
          value: '18.17.0'
        }
        {
          name: 'REACT_APP_API_URL'
          value: 'https://${appServiceBackendName}.azurewebsites.net/api/v1'
        }
      ]
    }
    scmSiteAlsoStopped: false
    clientAffinityEnabled: false
    clientCertEnabled: false
    clientCertMode: 'Required'
    hostNamesDisabled: false
    containerSize: 0
    dailyMemoryTimeQuota: 0
    httpsOnly: true
    redundancyMode: 'None'
    storageAccountRequired: false
    keyVaultReferenceIdentity: 'SystemAssigned'
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// ================================
// Outputs
// ================================
output appServicePlanBackendName string = appServicePlanBackend.name
output appServicePlanFrontendName string = appServicePlanFrontend.name

output appServiceBackendName string = appServiceBackend.name
output appServiceBackendUrl string = 'https://${appServiceBackend.properties.defaultHostName}'
output appServiceBackendId string = appServiceBackend.id

output appServiceFrontendName string = appServiceFrontend.name
output appServiceFrontendUrl string = 'https://${appServiceFrontend.properties.defaultHostName}'
output appServiceFrontendId string = appServiceFrontend.id

output postgreSqlServerName string = postgreSqlServer.name
output postgreSqlDatabaseName string = postgreSqlDatabase.name
output postgreSqlConnectionString string = 'postgresql://postgres:${uniqueString(resourceGroup().id)}Aa1!@${postgreSqlServer.properties.fullyQualifiedDomainName}:5432/${postgreSqlDatabaseName}'

output redisName string = redisCache.name
output redisConnectionString string = 'rediss://:${redisCache.listKeys().primaryKey}@${redisCache.properties.hostName}:${redisCache.properties.sslPort}/0'

output storageAccountName string = storageAccount.name
output storageAccountConnectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${az.environment().suffixes.storage}'

output appInsightsName string = enableAppInsights ? appInsights.name : ''
output appInsightsConnectionString string = enableAppInsights ? appInsights.properties.ConnectionString : ''
output appInsightsInstrumentationKey string = enableAppInsights ? appInsights.properties.InstrumentationKey : ''

output logAnalyticsWorkspaceName string = enableAppInsights ? logAnalyticsWorkspace.name : ''
output logAnalyticsWorkspaceId string = enableAppInsights ? logAnalyticsWorkspace.id : ''