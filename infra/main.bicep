targetScope = 'subscription'

param location string = 'eastus'
@description('SQL region can differ from the existing storage account region.')
param sqlLocation string = 'centralus'
param resourceGroupName string = 'monsterforge-rg'
@description('Object ID of the signed-in user in this subscription tenant, not an email or application ID.')
param storageUserObjectId string
@description('Public IPv4 address of the computer running Python; opens only this address for SQL.')
param clientIpAddress string
param sqlAdminLogin string = 'monsteradmin'
@secure()
@minLength(12)
param sqlAdminPassword string

resource projectGroup 'Microsoft.Resources/resourceGroups@2025-04-01' = {
  name: resourceGroupName
  location: location
  tags: {
    project: 'MonsterForge'
    environment: 'portfolio'
  }
}

module resources './resources.bicep' = {
  name: 'monsterforge-resources'
  scope: projectGroup
  params: {
    location: location
    sqlLocation: sqlLocation
    storageUserObjectId: storageUserObjectId
    clientIpAddress: clientIpAddress
    sqlAdminLogin: sqlAdminLogin
    sqlAdminPassword: sqlAdminPassword
  }
}

output resourceGroupName string = projectGroup.name
output storageAccountName string = resources.outputs.storageAccountName
output sqlServerName string = resources.outputs.sqlServerName
output sqlServerHost string = resources.outputs.sqlServerHost
output sqlDatabaseName string = resources.outputs.sqlDatabaseName
output sqlAdminLogin string = sqlAdminLogin
