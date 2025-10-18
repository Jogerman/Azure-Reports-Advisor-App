// ================================
// Networking Module
// Azure Front Door, WAF, CDN
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

@description('Custom domain name (optional)')
param customDomain string = ''

@description('Backend App Service URL')
param backendUrl string

@description('Frontend App Service URL')
param frontendUrl string

// ================================
// Variables
// ================================
var frontDoorProfileName = '${appNamePrefix}-afd${appNameSuffix}'
var frontDoorEndpointName = '${appNamePrefix}-endpoint${appNameSuffix}'
var frontDoorSkuName = environment == 'prod' ? 'Premium_AzureFrontDoor' : 'Standard_AzureFrontDoor'
var wafPolicyName = '${appNamePrefix}wafpolicy${replace(appNameSuffix, '-', '')}'

// Origin names
var backendOriginGroupName = 'backend-origin-group'
var frontendOriginGroupName = 'frontend-origin-group'
var backendOriginName = 'backend-origin'
var frontendOriginName = 'frontend-origin'

// Route names
var apiRouteName = 'api-route'
var defaultRouteName = 'default-route'

// Extract hostname from URLs
var backendHostname = replace(replace(backendUrl, 'https://', ''), 'http://', '')
var frontendHostname = replace(replace(frontendUrl, 'https://', ''), 'http://', '')

// ================================
// WAF Policy
// ================================
resource wafPolicy 'Microsoft.Network/FrontDoorWebApplicationFirewallPolicies@2022-05-01' = {
  name: wafPolicyName
  location: 'Global'
  tags: tags
  sku: {
    name: frontDoorSkuName
  }
  properties: {
    policySettings: {
      enabledState: 'Enabled'
      mode: environment == 'dev' ? 'Detection' : 'Prevention'
      redirectUrl: null
      customBlockResponseStatusCode: 403
      customBlockResponseBody: null
      requestBodyCheck: 'Enabled'
    }
    customRules: {
      rules: [
        {
          name: 'RateLimitRule'
          priority: 100
          ruleType: 'RateLimitRule'
          rateLimitDurationInMinutes: 1
          rateLimitThreshold: environment == 'prod' ? 100 : 300
          action: 'Block'
          matchConditions: [
            {
              matchVariable: 'RequestUri'
              operator: 'Contains'
              negateCondition: false
              matchValue: [
                '/api/'
              ]
              transforms: []
            }
          ]
        }
        {
          name: 'BlockSuspiciousUserAgents'
          priority: 200
          ruleType: 'MatchRule'
          action: 'Block'
          matchConditions: [
            {
              matchVariable: 'RequestHeader'
              selector: 'User-Agent'
              operator: 'Contains'
              negateCondition: false
              matchValue: [
                'bot'
                'crawler'
                'spider'
                'scraper'
              ]
              transforms: [
                'Lowercase'
              ]
            }
          ]
        }
        {
          name: 'GeoBlockingRule'
          priority: 300
          ruleType: 'MatchRule'
          action: environment == 'prod' ? 'Log' : 'Log'
          matchConditions: [
            {
              matchVariable: 'RemoteAddr'
              operator: 'GeoMatch'
              negateCondition: true
              matchValue: [
                'US'
                'CA'
                'GB'
                'DE'
                'FR'
                'AU'
                'IN'
              ]
              transforms: []
            }
          ]
        }
      ]
    }
    managedRules: {
      managedRuleSets: [
        {
          ruleSetType: 'Microsoft_DefaultRuleSet'
          ruleSetVersion: '2.1'
          ruleSetAction: 'Block'
          ruleGroupOverrides: []
          exclusions: []
        }
        {
          ruleSetType: 'Microsoft_BotManagerRuleSet'
          ruleSetVersion: '1.0'
          ruleSetAction: 'Block'
          ruleGroupOverrides: []
          exclusions: []
        }
      ]
    }
  }
}

// ================================
// Front Door Profile
// ================================
resource frontDoorProfile 'Microsoft.Cdn/profiles@2023-05-01' = {
  name: frontDoorProfileName
  location: 'Global'
  tags: tags
  sku: {
    name: frontDoorSkuName
  }
  properties: {
    originResponseTimeoutSeconds: 60
  }
}

// ================================
// Front Door Endpoint
// ================================
resource frontDoorEndpoint 'Microsoft.Cdn/profiles/afdEndpoints@2023-05-01' = {
  name: frontDoorEndpointName
  parent: frontDoorProfile
  location: 'Global'
  tags: tags
  properties: {
    enabledState: 'Enabled'
  }
}

// ================================
// Origin Groups
// ================================

// Backend Origin Group
resource backendOriginGroup 'Microsoft.Cdn/profiles/originGroups@2023-05-01' = {
  name: backendOriginGroupName
  parent: frontDoorProfile
  properties: {
    loadBalancingSettings: {
      sampleSize: 4
      successfulSamplesRequired: 3
      additionalLatencyInMilliseconds: 50
    }
    healthProbeSettings: {
      probePath: '/api/health/'
      probeRequestType: 'GET'
      probeProtocol: 'Https'
      probeIntervalInSeconds: 30
    }
    sessionAffinityState: 'Disabled'
  }
}

// Frontend Origin Group
resource frontendOriginGroup 'Microsoft.Cdn/profiles/originGroups@2023-05-01' = {
  name: frontendOriginGroupName
  parent: frontDoorProfile
  properties: {
    loadBalancingSettings: {
      sampleSize: 4
      successfulSamplesRequired: 3
      additionalLatencyInMilliseconds: 50
    }
    healthProbeSettings: {
      probePath: '/'
      probeRequestType: 'GET'
      probeProtocol: 'Https'
      probeIntervalInSeconds: 30
    }
    sessionAffinityState: 'Disabled'
  }
}

// ================================
// Origins
// ================================

// Backend Origin
resource backendOrigin 'Microsoft.Cdn/profiles/originGroups/origins@2023-05-01' = {
  name: backendOriginName
  parent: backendOriginGroup
  properties: {
    hostName: backendHostname
    httpPort: 80
    httpsPort: 443
    originHostHeader: backendHostname
    priority: 1
    weight: 1000
    enabledState: 'Enabled'
    enforceCertificateNameCheck: true
  }
}

// Frontend Origin
resource frontendOrigin 'Microsoft.Cdn/profiles/originGroups/origins@2023-05-01' = {
  name: frontendOriginName
  parent: frontendOriginGroup
  properties: {
    hostName: frontendHostname
    httpPort: 80
    httpsPort: 443
    originHostHeader: frontendHostname
    priority: 1
    weight: 1000
    enabledState: 'Enabled'
    enforceCertificateNameCheck: true
  }
}

// ================================
// Routes
// ================================

// API Route (Backend)
resource apiRoute 'Microsoft.Cdn/profiles/afdEndpoints/routes@2023-05-01' = {
  name: apiRouteName
  parent: frontDoorEndpoint
  dependsOn: [
    backendOrigin
    frontendOrigin
  ]
  properties: {
    originGroup: {
      id: backendOriginGroup.id
    }
    supportedProtocols: [
      'Http'
      'Https'
    ]
    patternsToMatch: [
      '/api/*'
      '/admin/*'
      '/static/*'
    ]
    forwardingProtocol: 'HttpsOnly'
    linkToDefaultDomain: 'Enabled'
    httpsRedirect: 'Enabled'
    enabledState: 'Enabled'
    cacheConfiguration: {
      queryStringCachingBehavior: 'IgnoreQueryString'
      compressionSettings: {
        contentTypesToCompress: [
          'application/json'
          'application/javascript'
          'text/css'
          'text/html'
          'text/javascript'
          'text/plain'
        ]
        isCompressionEnabled: true
      }
    }
  }
}

// Default Route (Frontend)
resource defaultRoute 'Microsoft.Cdn/profiles/afdEndpoints/routes@2023-05-01' = {
  name: defaultRouteName
  parent: frontDoorEndpoint
  dependsOn: [
    backendOrigin
    frontendOrigin
    apiRoute
  ]
  properties: {
    originGroup: {
      id: frontendOriginGroup.id
    }
    supportedProtocols: [
      'Http'
      'Https'
    ]
    patternsToMatch: [
      '/*'
    ]
    forwardingProtocol: 'HttpsOnly'
    linkToDefaultDomain: 'Enabled'
    httpsRedirect: 'Enabled'
    enabledState: 'Enabled'
    cacheConfiguration: {
      queryStringCachingBehavior: 'IgnoreQueryString'
      compressionSettings: {
        contentTypesToCompress: [
          'application/javascript'
          'application/json'
          'application/x-javascript'
          'application/xml'
          'text/css'
          'text/html'
          'text/javascript'
          'text/plain'
          'text/xml'
        ]
        isCompressionEnabled: true
      }
    }
  }
}

// ================================
// Security Policy (WAF Association)
// ================================
resource securityPolicy 'Microsoft.Cdn/profiles/securityPolicies@2023-05-01' = {
  name: 'SecurityPolicy'
  parent: frontDoorProfile
  properties: {
    parameters: {
      type: 'WebApplicationFirewall'
      wafPolicy: {
        id: wafPolicy.id
      }
      associations: [
        {
          domains: [
            {
              id: frontDoorEndpoint.id
            }
          ]
          patternsToMatch: [
            '/*'
          ]
        }
      ]
    }
  }
}

// ================================
// Custom Domain (Optional)
// ================================

// NOTE: Custom domain configuration requires:
// 1. Domain ownership validation
// 2. DNS CNAME record pointing to Front Door endpoint
// 3. SSL certificate (auto-managed or custom)
// Uncomment and configure when ready:

/*
resource customDomainResource 'Microsoft.Cdn/profiles/customDomains@2023-05-01' = if (customDomain != '') {
  name: replace(customDomain, '.', '-')
  parent: frontDoorProfile
  properties: {
    hostName: customDomain
    tlsSettings: {
      certificateType: 'ManagedCertificate'
      minimumTlsVersion: 'TLS12'
    }
  }
}

resource customDomainAssociation 'Microsoft.Cdn/profiles/afdEndpoints/routes@2023-05-01' = if (customDomain != '') {
  name: 'custom-domain-route'
  parent: frontDoorEndpoint
  dependsOn: [
    customDomainResource
  ]
  properties: {
    customDomains: [
      {
        id: customDomainResource.id
      }
    ]
    originGroup: {
      id: frontendOriginGroup.id
    }
    supportedProtocols: [
      'Https'
    ]
    patternsToMatch: [
      '/*'
    ]
    forwardingProtocol: 'HttpsOnly'
    linkToDefaultDomain: 'Enabled'
    httpsRedirect: 'Enabled'
    enabledState: 'Enabled'
  }
}
*/

// ================================
// Diagnostic Settings
// ================================
resource frontDoorDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'FrontDoorDiagnostics'
  scope: frontDoorProfile
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
output frontDoorName string = frontDoorProfile.name
output frontDoorEndpoint string = frontDoorEndpoint.properties.hostName
output frontDoorEndpointUrl string = 'https://${frontDoorEndpoint.properties.hostName}'
output frontDoorResourceId string = frontDoorProfile.id
output wafPolicyId string = wafPolicy.id
output wafPolicyName string = wafPolicy.name

// Custom domain outputs (if configured)
output customDomainConfigured bool = customDomain != ''
output customDomainName string = customDomain
