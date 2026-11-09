[CmdletBinding()]
param(
    [Parameter(Mandatory)][guid]$SubscriptionId,
    [Parameter(Mandatory)][string]$ClientIpAddress,
    [string]$Location = 'eastus',
    [string]$SqlLocation = 'centralus',
    [switch]$Deploy
)
$ErrorActionPreference = 'Stop'

function Invoke-AzureCli {
    param([string[]]$Arguments)
    $result = & az @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Azure CLI command failed: $($Arguments[0..1] -join ' ')" }
    return $result
}

$parsedIp = $null
if (-not [Net.IPAddress]::TryParse($ClientIpAddress, [ref]$parsedIp) -or
    $parsedIp.AddressFamily -ne [Net.Sockets.AddressFamily]::InterNetwork -or
    $ClientIpAddress -eq '0.0.0.0' -or $ClientIpAddress -eq '255.255.255.255' -or
    [Net.IPAddress]::IsLoopback($parsedIp)) {
    throw 'Supply your computer network public IPv4 address, not a wildcard or loopback.'
}

$account = (Invoke-AzureCli -Arguments @('account', 'show', '--subscription', "$SubscriptionId", '--output', 'json')) | ConvertFrom-Json
if ($account.state -ne 'Enabled') { throw 'The subscription must be enabled before deployment.' }
Write-Host "Target subscription: $($account.name) ($($account.id))"
# Graph identity commands use the active tenant and do not accept --subscription.
Invoke-AzureCli -Arguments @('account', 'set', '--subscription', "$SubscriptionId") | Out-Null
$objectId = Invoke-AzureCli -Arguments @('ad', 'signed-in-user', 'show', '--query', 'id', '--output', 'tsv')
if (-not $objectId) { throw 'Could not determine the signed-in user object ID.' }

$secret = Read-Host 'SQL administrator password (12+ characters; mixed case, numbers and symbols)' -AsSecureString
$secretPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
$previousPassword = $env:MF_SQL_ADMIN_PASSWORD
$previousObjectId = $env:MF_STORAGE_USER_OBJECT_ID
$previousIp = $env:MF_CLIENT_IP
try {
    $env:MF_SQL_ADMIN_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($secretPointer)
    $env:MF_STORAGE_USER_OBJECT_ID = "$objectId".Trim()
    $env:MF_CLIENT_IP = $ClientIpAddress
    $parameters = Join-Path $PSScriptRoot 'main.bicepparam'
    $common = @('--subscription', "$SubscriptionId", '--location', $Location, '--name', 'monsterforge-infra', '--parameters', $parameters, '--parameters', "location=$Location", "sqlLocation=$SqlLocation")
    # Default is a preview; deployment is an explicit separate invocation.
    if (-not $Deploy) {
        Invoke-AzureCli -Arguments (@('deployment', 'sub', 'what-if') + $common)
        return
    }
    Invoke-AzureCli -Arguments (@('deployment', 'sub', 'create') + $common + @('--output', 'none'))
    $outputs = (Invoke-AzureCli -Arguments @('deployment', 'sub', 'show', '--subscription', "$SubscriptionId", '--name', 'monsterforge-infra', '--query', 'properties.outputs', '--output', 'json')) | ConvertFrom-Json
    $db = (Invoke-AzureCli -Arguments @('sql', 'db', 'show', '--subscription', "$SubscriptionId", '--resource-group', $outputs.resourceGroupName.value, '--server', $outputs.sqlServerName.value, '--name', $outputs.sqlDatabaseName.value, '--output', 'json')) | ConvertFrom-Json
    if ($db.useFreeLimit -ne $true -or $db.freeLimitExhaustionBehavior -ne 'AutoPause') {
        throw 'SQL free-tier settings could not be verified. Inspect the database before running the pipeline.'
    }
    $outputs | ConvertTo-Json -Depth 6
    Write-Host 'Verified SQL free limits with AutoPause. Allow time for Blob role propagation before running Python.'
} finally {
    $env:MF_SQL_ADMIN_PASSWORD = $previousPassword
    $env:MF_STORAGE_USER_OBJECT_ID = $previousObjectId
    $env:MF_CLIENT_IP = $previousIp
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($secretPointer)
    $secret.Dispose()
}
