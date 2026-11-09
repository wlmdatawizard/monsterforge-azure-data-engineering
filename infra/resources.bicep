targetScope = 'resourceGroup'

param location string
param sqlLocation string
param storageUserObjectId string
param clientIpAddress string
param sqlAdminLogin string
@secure()
param sqlAdminPassword string

// Preserve the original project names; Azure must confirm global availability.
var tags = {
  project: 'MonsterForge'
  environment: 'portfolio'
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: 'monsterforgewlm'
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    defaultToOAuthAuthentication: true
    publicNetworkAccess: 'Enabled'
  }
}

resource blobs 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: {}
}

resource containers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = [for name in ['raw', 'clean', 'quarantine', 'reports']: {
  parent: blobs
  name: name
  properties: {
    publicAccess: 'None'
  }
}]

var blobContributorRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
resource storageAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, storageUserObjectId, blobContributorRoleId)
  scope: storage
  properties: {
    roleDefinitionId: blobContributorRoleId
    principalId: storageUserObjectId
    principalType: 'User'
  }
}

resource sqlServer 'Microsoft.Sql/servers@2023-08-01' = {
  name: 'monsterforge-sql-wlm-centralus'
  location: sqlLocation
  tags: tags
  properties: {
    version: '12.0'
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: sqlAdminPassword
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
  }
}

resource sqlFirewall 'Microsoft.Sql/servers/firewallRules@2023-08-01' = {
  parent: sqlServer
  name: 'LocalPipelineClient'
  properties: {
    startIpAddress: clientIpAddress
    endIpAddress: clientIpAddress
  }
}

// No paid fallback: deployment must fail if the free offer is unavailable.
resource database 'Microsoft.Sql/servers/databases@2025-01-01' = {
  parent: sqlServer
  name: 'monsterforge'
  location: sqlLocation
  tags: tags
  sku: {
    name: 'GP_S_Gen5_2'
    tier: 'GeneralPurpose'
    family: 'Gen5'
    capacity: 2
  }
  properties: {
    useFreeLimit: true
    freeLimitExhaustionBehavior: 'AutoPause'
    maxSizeBytes: 34359738368
    requestedBackupStorageRedundancy: 'Local'
    zoneRedundant: false
  }
}

output storageAccountName string = storage.name
output sqlServerName string = sqlServer.name
output sqlServerHost string = sqlServer.properties.fullyQualifiedDomainName
output sqlDatabaseName string = database.name
