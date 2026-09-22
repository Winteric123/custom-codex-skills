[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string] $SkillPath,
    [string] $CanonicalRoot,
    [string] $WispSkillsPath,
    [string] $WispGlobalRoot,
    [string] $WispObservedSkillPath,
    # Caller-observed Wisp listing/loading or Skills UI evidence, not a request
    # for this read-only script to reload Wisp or refresh an ACP conversation.
    [switch] $WispDiscoveryVerified,
    [string] $WispDiscoveryEvidence,
    [switch] $ConversationDiscoveryVerified
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not ('WispSync.FileIdentity' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
namespace WispSync {
    public static class FileIdentity {
        [StructLayout(LayoutKind.Sequential)]
        private struct Info {
            public uint Attributes;
            public System.Runtime.InteropServices.ComTypes.FILETIME CreationTime;
            public System.Runtime.InteropServices.ComTypes.FILETIME LastAccessTime;
            public System.Runtime.InteropServices.ComTypes.FILETIME LastWriteTime;
            public uint VolumeSerialNumber, FileSizeHigh, FileSizeLow, NumberOfLinks;
            public uint FileIndexHigh, FileIndexLow;
        }
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern SafeFileHandle CreateFileW(string path, uint access,
            uint share, IntPtr security, uint disposition, uint flags, IntPtr template);
        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetFileInformationByHandle(SafeFileHandle file, out Info info);
        public static string Read(string path) {
            // Zero desired access; share read/write/delete. BACKUP_SEMANTICS
            // permits directory handles. Omit OPEN_REPARSE_POINT to follow aliases.
            using (SafeFileHandle file = CreateFileW(path, 0, 7, IntPtr.Zero, 3,
                    0x02000000, IntPtr.Zero)) {
                if (file.IsInvalid) throw new Win32Exception(Marshal.GetLastWin32Error());
                Info info;
                if (!GetFileInformationByHandle(file, out info))
                    throw new Win32Exception(Marshal.GetLastWin32Error());
                return String.Format("{0:X8}:{1:X8}{2:X8}", info.VolumeSerialNumber,
                    info.FileIndexHigh, info.FileIndexLow);
            }
        }
    }
}
'@
}

function Get-NormalizedPath([string] $Value) {
    $full = [IO.Path]::GetFullPath([Environment]::ExpandEnvironmentVariables($Value.Trim().Trim('"')))
    $root = [IO.Path]::GetPathRoot($full)
    if ($full.Length -gt $root.Length) { return $full.TrimEnd('\', '/') }
    return $full
}

function Get-Identity([string] $Path) {
    try { return [WispSync.FileIdentity]::Read($Path) }
    catch { return $null }
}

function Test-SameIdentity($Left, $Right) {
    return -not [string]::IsNullOrEmpty($Left) -and
        -not [string]::IsNullOrEmpty($Right) -and $Left -eq $Right
}

function Test-ReparsePoint([string] $Path) {
    try { return ([IO.File]::GetAttributes($Path) -band [IO.FileAttributes]::ReparsePoint) -ne 0 }
    catch { return $false }
}

$userProfilePath = [Environment]::GetEnvironmentVariable('USERPROFILE', 'Process')
if ([string]::IsNullOrWhiteSpace($userProfilePath)) {
    $userProfilePath = [Environment]::GetFolderPath('UserProfile')
}
if ([string]::IsNullOrWhiteSpace($CanonicalRoot)) {
    $configuredCodexHome = [Environment]::GetEnvironmentVariable('CODEX_HOME', 'Process')
    $CanonicalRoot = if ([string]::IsNullOrWhiteSpace($configuredCodexHome)) {
        Join-Path $userProfilePath '.codex\skills'
    } else { Join-Path $configuredCodexHome 'skills' }
}
if ([string]::IsNullOrWhiteSpace($WispGlobalRoot)) {
    $WispGlobalRoot = Join-Path $userProfilePath '.wisp\skills'
}
$canonicalRootPath = Get-NormalizedPath $CanonicalRoot
$wispGlobalRootPath = Get-NormalizedPath $WispGlobalRoot
$inputSkillPath = Get-NormalizedPath $SkillPath
$skillName = Split-Path -Leaf $inputSkillPath
$canonicalSkillPath = Join-Path $canonicalRootPath $skillName
$canonicalSkillFile = Join-Path $canonicalSkillPath 'SKILL.md'
$inputSkillFile = Join-Path $inputSkillPath 'SKILL.md'
$observedSkillPath = if ([string]::IsNullOrWhiteSpace($WispObservedSkillPath)) {
    Join-Path $wispGlobalRootPath $skillName
} else { Get-NormalizedPath $WispObservedSkillPath }
if ((Split-Path -Leaf $observedSkillPath) -eq 'SKILL.md') {
    $observedSkillPath = Split-Path -Parent $observedSkillPath
}
$observedSkillFile = Join-Path $observedSkillPath 'SKILL.md'
$problems = [Collections.Generic.List[string]]::new()
$warnings = [Collections.Generic.List[string]]::new()

$canonicalRootIdentity = Get-Identity $canonicalRootPath
$wispRootIdentity = Get-Identity $wispGlobalRootPath
$canonicalDirectoryIdentity = Get-Identity $canonicalSkillPath
$inputDirectoryIdentity = Get-Identity $inputSkillPath
$observedDirectoryIdentity = Get-Identity $observedSkillPath
$canonicalFileIdentity = Get-Identity $canonicalSkillFile
$inputFileIdentity = Get-Identity $inputSkillFile
$observedFileIdentity = Get-Identity $observedSkillFile
$rootIdentityMatches = Test-SameIdentity $canonicalRootIdentity $wispRootIdentity
$inputMatchesCanonical = (Test-SameIdentity $canonicalDirectoryIdentity $inputDirectoryIdentity) -and
    (Test-SameIdentity $canonicalFileIdentity $inputFileIdentity)

if (-not [IO.File]::Exists($canonicalSkillFile)) { $problems.Add('Canonical SKILL.md is missing') }
if (-not [IO.File]::Exists($inputSkillFile)) { $problems.Add('Input SKILL.md is missing') }
if (-not $inputMatchesCanonical) {
    $problems.Add('Input skill directory and SKILL.md do not have the canonical filesystem identities, or identity could not be read')
}
if ($skillName -eq '.system' -or $inputSkillPath -match '[\\/]\.system(?:[\\/]|$)') {
    $problems.Add('Personal shared skills must not be stored under .system')
}
if ([IO.File]::Exists($canonicalSkillFile)) {
    try {
        # Decode strictly without stripping a BOM: Wisp requires the first line ---.
        $skillText = [Text.UTF8Encoding]::new($false, $true).GetString([IO.File]::ReadAllBytes($canonicalSkillFile))
        $frontmatter = [regex]::Match($skillText, '\A---\r?\n(?<yaml>[\s\S]*?)\r?\n---(?:\r?\n|\z)')
        if (-not $frontmatter.Success) {
            $problems.Add('SKILL.md requires a leading, closed frontmatter block without a BOM')
        } else {
            $nameMatch = [regex]::Match($frontmatter.Groups['yaml'].Value, '(?m)^name:[ \t]*([^\r\n]+)\r?$')
            if (-not $nameMatch.Success -or
                $nameMatch.Groups[1].Value.Trim().Trim('"').Trim("'") -cne $skillName) {
                $problems.Add('Skill folder and frontmatter name do not match')
            }
            if (-not [regex]::IsMatch($frontmatter.Groups['yaml'].Value, '(?m)^description:[ \t]*\S')) {
                $problems.Add('SKILL.md frontmatter has no non-empty description field')
            }
        }
    } catch {
        $problems.Add('SKILL.md could not be read as valid UTF-8: ' + $_.Exception.Message)
    }
}

# WalkDir follows its root link, but not a link at the skill-directory/file level.
$unsupportedChildLink = (Test-ReparsePoint $observedSkillPath) -or (Test-ReparsePoint $observedSkillFile)
$filesystemShared = (Test-SameIdentity $canonicalDirectoryIdentity $observedDirectoryIdentity) -and
    (Test-SameIdentity $canonicalFileIdentity $observedFileIdentity)
$scanSupported = $filesystemShared -and -not $unsupportedChildLink
if ($unsupportedChildLink) { $warnings.Add('unsupported_child_link') }
if ($WispDiscoveryVerified -and [string]::IsNullOrWhiteSpace($WispDiscoveryEvidence)) {
    $warnings.Add('live_evidence_missing')
}

# Keep environment diagnostics for compatibility. They never determine success.
$configuredRoots = [Collections.Generic.List[object]]::new()
$matchingScopes = [Collections.Generic.List[string]]::new()
$pathSources = [Collections.Generic.List[object]]::new()
if (-not [string]::IsNullOrWhiteSpace($WispSkillsPath)) {
    $pathSources.Add(@{ scope = 'Argument'; value = $WispSkillsPath })
}
foreach ($scope in @('Process', 'User', 'Machine')) {
    $raw = [Environment]::GetEnvironmentVariable('WISP_SKILLS_PATH', $scope)
    if (-not [string]::IsNullOrWhiteSpace($raw)) { $pathSources.Add(@{ scope = $scope; value = $raw }) }
}
foreach ($pathSource in $pathSources) {
    foreach ($entry in ($pathSource.value -split ';')) {
        if ([string]::IsNullOrWhiteSpace($entry)) { continue }
        if ($entry.Trim().Trim('"') -match '^[A-Za-z]:[\\/]' -and -not $warnings.Contains('windows_drive_separator')) {
            $warnings.Add('windows_drive_separator')
        }
        try {
            $normalizedEntry = Get-NormalizedPath $entry
            $entryMatches = Test-SameIdentity $canonicalRootIdentity (Get-Identity $normalizedEntry)
            $configuredRoots.Add([ordered]@{ scope = $pathSource.scope; path = $normalizedEntry; same_root_identity = $entryMatches })
            if ($entryMatches) { $matchingScopes.Add($pathSource.scope) }
        } catch {
            $configuredRoots.Add([ordered]@{ scope = $pathSource.scope; path = $entry; error = $_.Exception.Message })
        }
    }
}
$configurationStatus = if ($matchingScopes.Count -gt 0) { 'configured' }
    elseif ($configuredRoots.Count -eq 0) { 'missing' } else { 'mismatch_or_unresolved_alias' }
$sourceValid = $problems.Count -eq 0
$liveVerified = $sourceValid -and $scanSupported -and $WispDiscoveryVerified.IsPresent -and
    -not [string]::IsNullOrWhiteSpace($WispDiscoveryEvidence)
$status = if (-not $sourceValid) { 'invalid_skill' }
    elseif ($unsupportedChildLink) { 'unsupported_child_link' }
    elseif (-not $filesystemShared) { 'wisp_source_mismatch' }
    elseif (-not $liveVerified) { 'configured_unverified' }
    else { 'shared' }
$conversationVerified = $liveVerified -and $ConversationDiscoveryVerified.IsPresent

[ordered]@{
    status = $status
    skill_name = $skillName
    skill_path = $inputSkillPath
    canonical_root = $canonicalRootPath
    canonical_skill_path = $canonicalSkillPath
    wisp_global_root = $wispGlobalRootPath
    wisp_observed_skill_path = $observedSkillPath
    source_is_valid = $sourceValid
    root_identity_matches = $rootIdentityMatches
    filesystem_shared = $filesystemShared
    scan_path_supported = $scanSupported
    identity_method = 'Windows volume serial number and file index; directory and SKILL.md both compared'
    identities = [ordered]@{
        canonical_root = $canonicalRootIdentity; wisp_global_root = $wispRootIdentity
        canonical_directory = $canonicalDirectoryIdentity; input_directory = $inputDirectoryIdentity; observed_directory = $observedDirectoryIdentity
        canonical_file = $canonicalFileIdentity; input_file = $inputFileIdentity; observed_file = $observedFileIdentity
    }
    configuration_status = $configurationStatus
    configured_roots = @($configuredRoots)
    matching_scopes = @($matchingScopes)
    configuration_note = 'Environment values are diagnostics only. Process means this verifier, not Wisp. Root junction sharing does not require WISP_SKILLS_PATH.'
    wisp_reads_canonical_source = $liveVerified
    live_verification = [ordered]@{
        verified = $liveVerified
        evidence_source = if ($liveVerified) { 'caller_observed_wisp' } else { 'none' }
        evidence = $WispDiscoveryEvidence
    }
    session_status = if ($conversationVerified) { 'verified' } else { 'unknown' }
    session_refresh_required = if ($conversationVerified) { $false } else { $null }
    session_note = 'A shared result verifies filesystem identity and supplied Wisp discovery evidence, not an existing ACP conversation snapshot. Only attest conversation discovery after checking that conversation.'
    warnings = @($warnings)
    problems = @($problems)
    next_action = if ($status -eq 'shared') {
        'Sharing verified from supplied Wisp evidence. Check current-conversation discovery separately; otherwise reload skills or start a new conversation when needed.'
    } elseif ($status -eq 'configured_unverified') {
        'Same files verified. Reload Wisp Skills, then record actual listing/loading or UI source-path evidence. Existing ACP conversations can retain an earlier snapshot.'
    } elseif ($status -eq 'unsupported_child_link') {
        'Wisp does not traverse child skill/file links. Use a verified catalog-root link or a supported extra root; preserve other skills before any authorized repair.'
    } else {
        'Inspect the reported canonical/input/Wisp paths and identities. This read-only script changed no files, links, environment variables, or Wisp state.'
    }
} | ConvertTo-Json -Depth 6

if ($status -eq 'shared') { exit 0 }
exit 2
