// ================================
// Security Module
// Key Vault, Secrets, RBAC
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

@description('Azure AD client ID for authentication')
param azureAdClientId string

@description('Azure AD tenant ID')
param azureAdTenantId string

@secure()
@description('Azure AD client secret')
param azureAdClientSecret string

@description('Backend App Service name')
param appServiceBackendName string

@description('Frontend App Service name')
param appServiceFrontendName string

// ================================
// Variables
// ================================
var keyVaultName = '${appNamePrefix}-kv${appNameSuffix}-${uniqueString(resourceGroup().id)}'
var keyVaultSku = environment == 'prod' ? 'premium' : 'standard'

// ================================
// Key Vault
// ================================
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    enabledForDeployment: true
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: true
    tenantId: subscription().tenantId
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
    enableRbacAuthorization: true
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
      ipRules: []
      virtualNetworkRules: []
    }
    sku: {
      family: 'A'
      name: keyVaultSku
    }
  }
}

// ================================
// Secrets (Placeholders - Manual Setup Required)
// ================================

// NOTE: These secrets must be manually configured after deployment
// using Azure CLI or Azure Portal with actual values.
// The values below are placeholders to create the secret structure.

resource secretDatabaseUrl 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'DATABASE-URL'
  tags: tags
  properties: {
    value: 'PLACEHOLDER-Configure-After-Deployment'
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

resource secretRedisUrl 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'REDIS-URL'
  tags: tags
  properties: {
    value: 'PLACEHOLDER-Configure-After-Deployment'
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

resource secretStorageConnectionString 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'AZURE-STORAGE-CONNECTION-STRING'
  tags: tags
  properties: {
    value: 'PLACEHOLDER-Configure-After-Deployment'
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

resource secretDjangoSecretKey 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'DJANGO-SECRET-KEY'
  tags: tags
  properties: {
    value: base64(uniqueString(resourceGroup().id, deployment().name))
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

resource secretAzureAdClientId 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'AZURE-AD-CLIENT-ID'
  tags: tags
  properties: {
    value: azureAdClientId
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

resource secretAzureAdClientSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'AZURE-AD-CLIENT-SECRET'
  tags: tags
  properties: {
    value: azureAdClientSecret
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

resource secretAzureAdTenantId 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'AZURE-AD-TENANT-ID'
  tags: tags
  properties: {
    value: azureAdTenantId
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// ================================
// Get App Service Identities
// ================================
resource appServiceBackend 'Microsoft.Web/sites@2023-01-01' existing = {
  name: appServiceBackendName
}

resource appServiceFrontend 'Microsoft.Web/sites@2023-01-01' existing = {
  name: appServiceFrontendName
}

// ================================
// RBAC Role Assignments
// ================================

// Key Vault Secrets User role definition ID
var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

// Assign Key Vault Secrets User role to Backend App Service
resource backendKeyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, appServiceBackend.id, keyVaultSecretsUserRoleId)
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalId: appServiceBackend.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Assign Key Vault Secrets User role to Frontend App Service
resource frontendKeyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, appServiceFrontend.id, keyVaultSecretsUserRoleId)
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalId: appServiceFrontend.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ================================
// Certificate Configuration (Optional)
// ================================

// NOTE: Certificates for custom domains must be imported manually
// or provisioned through Azure App Service Managed Certificates.
// Uncomment and configure the following if using custom certificates:

/*
resource customCertificate 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'custom-domain-certificate'
  properties: {
    contentType: 'application/x-pkcs12'
    value: 'IMPORT-PFX-CERTIFICATE-BASE64'
    attributes: {
      enabled: true
    }
  }
}
*/

// ================================
// Diagnostic Settings
// ================================
resource keyVaultDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'KeyVaultDiagnostics'
  scope: keyVault
  properties: {
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 30
        }
      }
      {
        categoryGroup: 'audit'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 90
        }
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 30
        }
      }
    ]
  }
}

// ================================
// Outputs
// ================================
output keyVaultName string = keyVault.name
output keyVaultUri string = keyVault.properties.vaultUri
output keyVaultResourceId string = keyVault.id
output backendManagedIdentityPrincipalId string = appServiceBackend.identity.principalId
output frontendManagedIdentityPrincipalId string = appServiceFrontend.identity.principalId

// Secret reference URIs (for App Service configuration)
output secretDatabaseUrlReference string = '@Microsoft.KeyVault(SecretUri=${secretDatabaseUrl.properties.secretUri})'
output secretRedisUrlReference string = '@Microsoft.KeyVault(SecretUri=${secretRedisUrl.properties.secretUri})'
output secretStorageConnectionStringReference string = '@Microsoft.KeyVault(SecretUri=${secretStorageConnectionString.properties.secretUri})'
output secretDjangoSecretKeyReference string = '@Microsoft.KeyVault(SecretUri=${secretDjangoSecretKey.properties.secretUri})'
output secretAzureAdClientIdReference string = '@Microsoft.KeyVault(SecretUri=${secretAzureAdClientId.properties.secretUri})'
output secretAzureAdClientSecretReference string = '@Microsoft.KeyVault(SecretUri=${secretAzureAdClientSecret.properties.secretUri})'
output secretAzureAdTenantIdReference string = '@Microsoft.KeyVault(SecretUri=${secretAzureAdTenantId.properties.secretUri})'
