param(
    [Parameter(Mandatory = $false)]
    [ValidateSet('NCBI_API_KEY', 'OPENALEX_API_KEY')]
    [string]$Name = 'NCBI_API_KEY',

    [Parameter(Mandatory = $false)]
    [string]$CredentialPath = (Join-Path $env:USERPROFILE '.codex\secrets\jlyl-literature-delivery\credentials.json')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$secret = if ([Console]::IsInputRedirected) {
    [Console]::In.ReadLine()
} else {
    $builder = [System.Text.StringBuilder]::new()
    while ($true) {
        $key = [Console]::ReadKey($true)
        if ($key.Key -eq [ConsoleKey]::Enter) {
            break
        }
        if ($key.Key -eq [ConsoleKey]::Backspace) {
            if ($builder.Length -gt 0) {
                $builder.Length -= 1
            }
            continue
        }
        if (-not [char]::IsControl($key.KeyChar)) {
            [void]$builder.Append($key.KeyChar)
        }
    }
    $builder.ToString()
}
if ([string]::IsNullOrWhiteSpace($secret)) {
    throw 'No credential was provided on standard input.'
}

Add-Type -AssemblyName System.Security.Cryptography.ProtectedData
$clearBytes = [System.Text.Encoding]::UTF8.GetBytes($secret)
try {
    $protectedBytes = [System.Security.Cryptography.ProtectedData]::Protect(
        $clearBytes,
        $null,
        [System.Security.Cryptography.DataProtectionScope]::CurrentUser
    )
} finally {
    [System.Array]::Clear($clearBytes, 0, $clearBytes.Length)
    $secret = $null
}
$encoded = [Convert]::ToBase64String($protectedBytes)

$directory = Split-Path -Parent $CredentialPath
New-Item -ItemType Directory -Path $directory -Force | Out-Null

if (Test-Path -LiteralPath $CredentialPath -PathType Leaf) {
    $payload = Get-Content -LiteralPath $CredentialPath -Raw | ConvertFrom-Json -AsHashtable
} else {
    $payload = @{}
}
$payload['version'] = 1
$payload['storage'] = 'windows-dpapi-current-user'
if (-not $payload.ContainsKey('secrets') -or $null -eq $payload['secrets']) {
    $payload['secrets'] = @{}
}
$payload['secrets'][$Name] = $encoded

$json = $payload | ConvertTo-Json -Depth 5
[System.IO.File]::WriteAllText(
    $CredentialPath,
    $json + [Environment]::NewLine,
    [System.Text.UTF8Encoding]::new($false)
)

$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$acl = Get-Acl -LiteralPath $CredentialPath
$acl.SetAccessRuleProtection($true, $false)
$rule = [System.Security.AccessControl.FileSystemAccessRule]::new(
    $identity,
    [System.Security.AccessControl.FileSystemRights]::FullControl,
    [System.Security.AccessControl.AccessControlType]::Allow
)
$acl.SetAccessRule($rule)
Set-Acl -LiteralPath $CredentialPath -AclObject $acl

[PSCustomObject]@{
    credential_file = (Resolve-Path -LiteralPath $CredentialPath).Path
    credential_name = $Name
    storage = 'windows-dpapi-current-user'
}
