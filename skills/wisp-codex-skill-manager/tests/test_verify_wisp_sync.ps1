[CmdletBinding()]
param(
    [string]$VerifierPath,
    [string]$FixtureRoot
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ([string]::IsNullOrWhiteSpace($VerifierPath)) {
    $VerifierPath = Join-Path $PSScriptRoot '..\scripts\verify_wisp_sync.ps1'
}
$VerifierPath = [IO.Path]::GetFullPath($VerifierPath)
if (-not (Test-Path -LiteralPath $VerifierPath -PathType Leaf)) {
    throw "Verifier is not ready: $VerifierPath"
}

# These fixtures are intentionally retained. Never recursively remove a fixture
# containing a junction: its target must remain available for failure diagnosis.
$runId = (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 8)
if ([string]::IsNullOrWhiteSpace($FixtureRoot)) {
    $FixtureRoot = Join-Path ([IO.Path]::GetTempPath()) 'wisp-sync-verifier-tests'
}
$fixtureRoot = Join-Path ([IO.Path]::GetFullPath($FixtureRoot)) $runId
$null = New-Item -ItemType Directory -Path $fixtureRoot -Force
$script:Results = New-Object 'System.Collections.Generic.List[object]'
$utf8NoBom = New-Object Text.UTF8Encoding($false)
$shellPath = Join-Path $PSHOME 'powershell.exe'
if (-not (Test-Path -LiteralPath $shellPath -PathType Leaf)) {
    $shellPath = (Get-Command powershell.exe -ErrorAction Stop).Source
}

function Write-DemoSkill {
    param([string]$Directory, [string]$Name = 'demo-skill')
    $null = New-Item -ItemType Directory -Path $Directory -Force
    $contents = "---`nname: $Name`ndescription: Synthetic skill for isolated sharing verification tests.`n---`n`n# Demo`n`nThis is test fixture content only.`n"
    [IO.File]::WriteAllText((Join-Path $Directory 'SKILL.md'), $contents, $utf8NoBom)
}

function New-Fixture {
    param([string]$Name, [switch]$RootJunction, [switch]$NoSkill)
    $root = Join-Path $fixtureRoot $Name
    $codexDir = Join-Path $root 'codex-home'
    $canonical = Join-Path $codexDir 'skills'
    $profileDir = Join-Path $root 'profile'
    $wispDir = Join-Path $profileDir '.wisp'
    $global = Join-Path $wispDir 'skills'
    foreach ($dir in @($canonical, $wispDir)) {
        $null = New-Item -ItemType Directory -Path $dir -Force
    }
    if ($RootJunction) {
        $null = New-Item -ItemType Junction -Path $global -Target $canonical
    } else {
        $null = New-Item -ItemType Directory -Path $global
    }
    $skill = Join-Path $canonical 'demo-skill'
    if (-not $NoSkill) { Write-DemoSkill -Directory $skill }
    return [pscustomobject]@{
        Root = $root; CodexHome = $codexDir; CanonicalRoot = $canonical
        Profile = $profileDir; GlobalRoot = $global; SkillPath = $skill
        ObservedPath = (Join-Path $global 'demo-skill')
    }
}

function Quote-NativeArgument {
    param([AllowEmptyString()][string]$Value)
    # Windows CommandLineToArgvW-compatible quoting, including trailing slashes.
    return '"' + [regex]::Replace([regex]::Replace($Value, '(\\*)"', '$1$1\"'), '(\\+)$', '$1$1') + '"'
}

function Invoke-Verifier {
    param(
        [object]$Fixture,
        [hashtable]$Parameters,
        [string]$ScriptPath = $VerifierPath,
        [hashtable]$Environment = @{}
    )
    # Configure only the child process. ProcessStartInfo's environment getter can
    # throw when the inherited native block contains both Path and PATH, so use a
    # child bootstrap instead of normalizing or changing the test host environment.
    $childEnvironment = @{
        CODEX_HOME = $Fixture.CodexHome; USERPROFILE = $Fixture.Profile; WISP_SKILLS_PATH = $null
    }
    foreach ($key in $Environment.Keys) { $childEnvironment[$key] = $Environment[$key] }
    $specPath = Join-Path $Fixture.Root 'invocation.json'
    $spec = @{ script_path = $ScriptPath; parameters = $Parameters; environment = $childEnvironment }
    [IO.File]::WriteAllText($specPath, ($spec | ConvertTo-Json -Depth 5), $utf8NoBom)
    $quotedSpec = "'" + $specPath.Replace("'", "''") + "'"
    $bootstrap = @"
[Console]::OutputEncoding = New-Object Text.UTF8Encoding(`$false)
`$spec = Get-Content -Raw -Encoding UTF8 -LiteralPath $quotedSpec | ConvertFrom-Json
foreach (`$property in `$spec.environment.PSObject.Properties) {
    [Environment]::SetEnvironmentVariable(`$property.Name, `$property.Value, 'Process')
}
`$parameters = @{}
foreach (`$property in `$spec.parameters.PSObject.Properties) { `$parameters[`$property.Name] = `$property.Value }
& `$spec.script_path @parameters
exit `$LASTEXITCODE
"@
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($bootstrap))
    $start = New-Object Diagnostics.ProcessStartInfo
    $start.FileName = $shellPath
    $start.Arguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand ' + $encoded
    $start.WorkingDirectory = $Fixture.Root
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $start.StandardOutputEncoding = $utf8NoBom
    $start.StandardErrorEncoding = $utf8NoBom
    $process = New-Object Diagnostics.Process
    $process.StartInfo = $start
    try {
        $null = $process.Start()
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit(30000)) {
            $process.Kill()
            throw 'Verifier child process exceeded 30 seconds.'
        }
        $stdout = $stdoutTask.GetAwaiter().GetResult()
        $stderr = $stderrTask.GetAwaiter().GetResult()
        $exitCode = $process.ExitCode
        try { $data = $stdout | ConvertFrom-Json -ErrorAction Stop }
        catch { throw "Verifier did not return JSON (exit $exitCode). stdout: $stdout stderr: $stderr" }
        return [pscustomobject]@{ ExitCode = $exitCode; Data = $data; Stdout = $stdout; Stderr = $stderr }
    } finally {
        $process.Dispose()
    }
}

function Assert-Fields {
    param([object]$Result, [hashtable]$Expected, [int]$ExitCode)
    if ($Result.ExitCode -ne $ExitCode) {
        throw "Exit code expected $ExitCode but received $($Result.ExitCode). stderr: $($Result.Stderr) stdout: $($Result.Stdout)"
    }
    foreach ($field in $Expected.Keys) {
        $property = $Result.Data.PSObject.Properties[$field]
        if ($null -eq $property) { throw "Missing JSON property: $field" }
        $actual = $property.Value
        $wanted = $Expected[$field]
        if ($null -eq $wanted) {
            if ($null -ne $actual) { throw "$field expected JSON null but received '$actual'." }
        } elseif ($wanted -is [bool]) {
            if (($actual -isnot [bool]) -or ($actual -ne $wanted)) {
                throw "$field expected JSON boolean $wanted but received '$actual'."
            }
        } elseif ($actual -cne $wanted) {
            throw "$field expected '$wanted' but received '$actual'."
        }
    }
}

function Test-Scenario {
    param([string]$Name, [scriptblock]$Body)
    try {
        & $Body
        $script:Results.Add([pscustomobject]@{ name = $Name; result = 'passed'; error = $null })
        Write-Host "PASS $Name"
    } catch {
        $script:Results.Add([pscustomobject]@{ name = $Name; result = 'failed'; error = $_.Exception.Message; stack = $_.ScriptStackTrace })
        Write-Host "FAIL $Name : $($_.Exception.Message) $($_.ScriptStackTrace)"
    }
}

Test-Scenario 'root junction works without environment configuration' {
    $f = New-Fixture 'root-no-env' -RootJunction
    $r = Invoke-Verifier $f @{ SkillPath = $f.SkillPath; CanonicalRoot = $f.CanonicalRoot; WispGlobalRoot = $f.GlobalRoot }
    Assert-Fields $r @{
        source_is_valid = $true; filesystem_shared = $true; root_identity_matches = $true
        wisp_reads_canonical_source = $false; status = 'configured_unverified'
        session_status = 'unknown'; session_refresh_required = $null
    } 2
}

Test-Scenario 'canonical skill can be supplied through Wisp root alias' {
    $f = New-Fixture 'skill-alias' -RootJunction
    $r = Invoke-Verifier $f @{
        SkillPath = $f.ObservedPath; CanonicalRoot = $f.CanonicalRoot; WispGlobalRoot = $f.GlobalRoot
        WispDiscoveryVerified = $true; WispDiscoveryEvidence = 'SYNTHETIC UI evidence for test fixture only'
    }
    Assert-Fields $r @{
        source_is_valid = $true; filesystem_shared = $true; root_identity_matches = $true
        wisp_reads_canonical_source = $true; status = 'shared'; session_status = 'unknown'
        session_refresh_required = $null
    } 0
}

Test-Scenario 'script invocation through alias respects process CODEX_HOME default' {
    $f = New-Fixture 'script-alias' -RootJunction
    $scriptDir = Join-Path $f.CanonicalRoot 'synthetic-manager\scripts'
    $null = New-Item -ItemType Directory -Path $scriptDir -Force
    Copy-Item -LiteralPath $VerifierPath -Destination (Join-Path $scriptDir 'verify_wisp_sync.ps1')
    $aliasScript = Join-Path $f.GlobalRoot 'synthetic-manager\scripts\verify_wisp_sync.ps1'
    $r = Invoke-Verifier $f @{
        SkillPath = $f.ObservedPath; WispGlobalRoot = $f.GlobalRoot
        WispDiscoveryVerified = $true; WispDiscoveryEvidence = 'SYNTHETIC catalog evidence for alias invocation'
    } -ScriptPath $aliasScript
    Assert-Fields $r @{
        canonical_root = $f.CanonicalRoot; source_is_valid = $true; filesystem_shared = $true
        root_identity_matches = $true; wisp_reads_canonical_source = $true; status = 'shared'
    } 0
}

Test-Scenario 'identical independent copy is not shared source' {
    $f = New-Fixture 'independent-copy'
    Copy-Item -LiteralPath $f.SkillPath -Destination $f.ObservedPath -Recurse
    if ((Get-FileHash -LiteralPath (Join-Path $f.SkillPath 'SKILL.md')).Hash -ne (Get-FileHash -LiteralPath (Join-Path $f.ObservedPath 'SKILL.md')).Hash) {
        throw 'Test setup error: copy must have identical content.'
    }
    $r = Invoke-Verifier $f @{
        SkillPath = $f.SkillPath; CanonicalRoot = $f.CanonicalRoot; WispGlobalRoot = $f.GlobalRoot
        WispDiscoveryVerified = $true; WispDiscoveryEvidence = 'SYNTHETIC evidence cannot establish file identity'
    }
    Assert-Fields $r @{
        source_is_valid = $true; filesystem_shared = $false; root_identity_matches = $false
        wisp_reads_canonical_source = $false; status = 'wisp_source_mismatch'
    } 2
}

Test-Scenario 'per-skill child junction cannot be blessed by evidence' {
    $f = New-Fixture 'child-junction'
    $null = New-Item -ItemType Junction -Path $f.ObservedPath -Target $f.SkillPath
    $r = Invoke-Verifier $f @{
        SkillPath = $f.SkillPath; CanonicalRoot = $f.CanonicalRoot; WispGlobalRoot = $f.GlobalRoot
        WispDiscoveryVerified = $true; WispDiscoveryEvidence = 'SYNTHETIC evidence must not override child link policy'
    }
    Assert-Fields $r @{
        source_is_valid = $true; root_identity_matches = $false
        wisp_reads_canonical_source = $false; status = 'unsupported_child_link'
    } 2
}

Test-Scenario 'missing SKILL.md is invalid' {
    $f = New-Fixture 'missing-manifest' -RootJunction -NoSkill
    $null = New-Item -ItemType Directory -Path $f.SkillPath
    $r = Invoke-Verifier $f @{
        SkillPath = $f.SkillPath; CanonicalRoot = $f.CanonicalRoot; WispGlobalRoot = $f.GlobalRoot
        WispDiscoveryVerified = $true; WispDiscoveryEvidence = 'SYNTHETIC stale evidence'
    }
    Assert-Fields $r @{ source_is_valid = $false; wisp_reads_canonical_source = $false; status = 'invalid_skill' } 2
}

Test-Scenario 'environment match alone does not establish Wisp discovery' {
    $f = New-Fixture 'env-only' -RootJunction
    $r = Invoke-Verifier $f @{
        SkillPath = $f.SkillPath; CanonicalRoot = $f.CanonicalRoot; WispGlobalRoot = $f.GlobalRoot
        WispSkillsPath = $f.CanonicalRoot
    } -Environment @{ WISP_SKILLS_PATH = $f.CanonicalRoot }
    Assert-Fields $r @{
        filesystem_shared = $true; wisp_reads_canonical_source = $false; status = 'configured_unverified'
        session_status = 'unknown'; session_refresh_required = $null
    } 2
}

Test-Scenario 'invalid UTF-8 manifest returns structured invalid_skill' {
    $f = New-Fixture 'invalid-utf8' -RootJunction
    [IO.File]::WriteAllBytes((Join-Path $f.SkillPath 'SKILL.md'), [byte[]]@(0xFF, 0xFE, 0xFF))
    $r = Invoke-Verifier $f @{
        SkillPath = $f.SkillPath; CanonicalRoot = $f.CanonicalRoot; WispGlobalRoot = $f.GlobalRoot
        WispDiscoveryVerified = $true; WispDiscoveryEvidence = 'SYNTHETIC evidence cannot override invalid encoding'
    }
    Assert-Fields $r @{ source_is_valid = $false; wisp_reads_canonical_source = $false; status = 'invalid_skill' } 2
}

Test-Scenario 'explicit UI evidence verifies sharing but leaves session unknown' {
    $f = New-Fixture 'ui-evidence' -RootJunction
    $r = Invoke-Verifier $f @{
        SkillPath = $f.SkillPath; CanonicalRoot = $f.CanonicalRoot; WispGlobalRoot = $f.GlobalRoot
        WispDiscoveryVerified = $true; WispDiscoveryEvidence = 'SYNTHETIC Settings Skills lists demo-skill at fixture Wisp root'
        WispObservedSkillPath = (Join-Path $f.ObservedPath 'SKILL.md')
    }
    Assert-Fields $r @{
        filesystem_shared = $true; wisp_reads_canonical_source = $true; status = 'shared'
        session_status = 'unknown'; session_refresh_required = $null
    } 0
}

Test-Scenario 'discovery flag without evidence remains unverified' {
    $f = New-Fixture 'flag-only' -RootJunction
    $r = Invoke-Verifier $f @{
        SkillPath = $f.SkillPath; CanonicalRoot = $f.CanonicalRoot; WispGlobalRoot = $f.GlobalRoot
        WispDiscoveryVerified = $true
    }
    Assert-Fields $r @{
        wisp_reads_canonical_source = $false; status = 'configured_unverified'
        session_status = 'unknown'; session_refresh_required = $null
    } 2
}

Test-Scenario 'evidence string without discovery flag remains unverified' {
    $f = New-Fixture 'evidence-only' -RootJunction
    $r = Invoke-Verifier $f @{
        SkillPath = $f.SkillPath; CanonicalRoot = $f.CanonicalRoot; WispGlobalRoot = $f.GlobalRoot
        WispDiscoveryEvidence = 'SYNTHETIC string alone does not assert discovery'
    }
    Assert-Fields $r @{ wisp_reads_canonical_source = $false; status = 'configured_unverified' } 2
}

Test-Scenario 'folder and frontmatter name mismatch is invalid' {
    $f = New-Fixture 'name-mismatch' -RootJunction
    Write-DemoSkill -Directory $f.SkillPath -Name 'different-skill'
    $r = Invoke-Verifier $f @{
        SkillPath = $f.SkillPath; CanonicalRoot = $f.CanonicalRoot; WispGlobalRoot = $f.GlobalRoot
        WispDiscoveryVerified = $true; WispDiscoveryEvidence = 'SYNTHETIC evidence for invalid manifest'
    }
    Assert-Fields $r @{ source_is_valid = $false; wisp_reads_canonical_source = $false; status = 'invalid_skill' } 2
}

Test-Scenario 'explicit observed independent copy rejects otherwise shared root' {
    $f = New-Fixture 'observed-copy' -RootJunction
    $copy = Join-Path $f.Root 'independent\demo-skill'
    $null = New-Item -ItemType Directory -Path (Split-Path -Parent $copy) -Force
    Copy-Item -LiteralPath $f.SkillPath -Destination $copy -Recurse
    $r = Invoke-Verifier $f @{
        SkillPath = $f.SkillPath; CanonicalRoot = $f.CanonicalRoot; WispGlobalRoot = $f.GlobalRoot
        WispDiscoveryVerified = $true; WispDiscoveryEvidence = 'SYNTHETIC observed UI path is an independent copy'
        WispObservedSkillPath = $copy
    }
    Assert-Fields $r @{
        source_is_valid = $true; root_identity_matches = $true
        wisp_reads_canonical_source = $false; status = 'wisp_source_mismatch'
    } 2
}

Test-Scenario 'conversation verification succeeds only with verified sharing' {
    $f = New-Fixture 'conversation-shared' -RootJunction
    $r = Invoke-Verifier $f @{
        SkillPath = $f.SkillPath; CanonicalRoot = $f.CanonicalRoot; WispGlobalRoot = $f.GlobalRoot
        WispDiscoveryVerified = $true; WispDiscoveryEvidence = 'SYNTHETIC current conversation loaded same fixture source'
        ConversationDiscoveryVerified = $true
    }
    Assert-Fields $r @{
        status = 'shared'; wisp_reads_canonical_source = $true
        session_status = 'verified'; session_refresh_required = $false
    } 0
}

Test-Scenario 'conversation flag cannot bypass missing Wisp evidence' {
    $f = New-Fixture 'conversation-unverified' -RootJunction
    $r = Invoke-Verifier $f @{
        SkillPath = $f.SkillPath; CanonicalRoot = $f.CanonicalRoot; WispGlobalRoot = $f.GlobalRoot
        ConversationDiscoveryVerified = $true
    }
    Assert-Fields $r @{
        status = 'configured_unverified'; wisp_reads_canonical_source = $false
        session_status = 'unknown'; session_refresh_required = $null
    } 2
}

Test-Scenario 'conversation flag cannot bypass source mismatch' {
    $f = New-Fixture 'conversation-copy'
    Copy-Item -LiteralPath $f.SkillPath -Destination $f.ObservedPath -Recurse
    $r = Invoke-Verifier $f @{
        SkillPath = $f.SkillPath; CanonicalRoot = $f.CanonicalRoot; WispGlobalRoot = $f.GlobalRoot
        WispDiscoveryVerified = $true; WispDiscoveryEvidence = 'SYNTHETIC copy is not canonical'
        ConversationDiscoveryVerified = $true
    }
    Assert-Fields $r @{
        status = 'wisp_source_mismatch'; wisp_reads_canonical_source = $false
        session_status = 'unknown'; session_refresh_required = $null
    } 2
}

Test-Scenario 'USERPROFILE fallback applies when CODEX_HOME is absent' {
    $f = New-Fixture 'profile-default' -RootJunction
    $fallbackCodex = Join-Path $f.Profile '.codex'
    $null = New-Item -ItemType Junction -Path $fallbackCodex -Target $f.CodexHome
    $r = Invoke-Verifier $f @{
        SkillPath = $f.SkillPath; WispGlobalRoot = $f.GlobalRoot
        WispDiscoveryVerified = $true; WispDiscoveryEvidence = 'SYNTHETIC profile fallback evidence'
    } -Environment @{ CODEX_HOME = $null }
    Assert-Fields $r @{
        canonical_root = (Join-Path $fallbackCodex 'skills'); source_is_valid = $true
        filesystem_shared = $true; wisp_reads_canonical_source = $true; status = 'shared'
    } 0
}

# File symlink creation is privilege-dependent on Windows. Report an explicit skip
# when unavailable; do not request privilege elevation or substitute a hard link.
$symlinkFixture = New-Fixture 'manifest-symlink'
$null = New-Item -ItemType Directory -Path $symlinkFixture.ObservedPath
$symlinkAvailable = $true
$symlinkError = $null
try {
    $null = New-Item -ItemType SymbolicLink -Path (Join-Path $symlinkFixture.ObservedPath 'SKILL.md') -Target (Join-Path $symlinkFixture.SkillPath 'SKILL.md')
} catch {
    $symlinkAvailable = $false
    $symlinkError = $_.Exception.Message
}
if ($symlinkAvailable) {
    Test-Scenario 'SKILL.md file symlink is unsupported despite evidence' {
        $r = Invoke-Verifier $symlinkFixture @{
            SkillPath = $symlinkFixture.SkillPath; CanonicalRoot = $symlinkFixture.CanonicalRoot
            WispGlobalRoot = $symlinkFixture.GlobalRoot; WispDiscoveryVerified = $true
            WispDiscoveryEvidence = 'SYNTHETIC evidence cannot override file symlink scanner constraint'
        }
        Assert-Fields $r @{ wisp_reads_canonical_source = $false; status = 'unsupported_child_link' } 2
    }
} else {
    $script:Results.Add([pscustomobject]@{
        name = 'SKILL.md file symlink is unsupported despite evidence'; result = 'skipped'; error = $symlinkError
    })
    Write-Host "SKIP SKILL.md file symlink: $symlinkError"
}

$summary = [ordered]@{
    generated_at = (Get-Date).ToString('o')
    verifier_path = $VerifierPath
    fixture_root = $fixtureRoot
    synthetic_evidence_only = $true
    user_configuration_changed = $false
    passed = @($script:Results | Where-Object result -eq 'passed').Count
    failed = @($script:Results | Where-Object result -eq 'failed').Count
    skipped = @($script:Results | Where-Object result -eq 'skipped').Count
    cases = @($script:Results.ToArray())
}
$summaryPath = Join-Path $fixtureRoot 'summary.json'
[IO.File]::WriteAllText($summaryPath, ($summary | ConvertTo-Json -Depth 8), $utf8NoBom)
Write-Output ($summary | ConvertTo-Json -Depth 8)
Write-Host "Summary: $summaryPath"
if ($summary.failed -gt 0) { exit 1 }
exit 0
