using './main.bicep'

param location = 'eastus'
param sqlLocation = 'centralus'
param resourceGroupName = 'monsterforge-rg'
param storageUserObjectId = readEnvironmentVariable('MF_STORAGE_USER_OBJECT_ID')
param clientIpAddress = readEnvironmentVariable('MF_CLIENT_IP')
param sqlAdminLogin = 'monsteradmin'
param sqlAdminPassword = readEnvironmentVariable('MF_SQL_ADMIN_PASSWORD')
