[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $SkillPath,

    [string] $CanonicalRoot,

    [string] $WispSkillsPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function ConvertTo-NormalizedPath {
    param(
        [Parameter(Mandatory = $true)]
        [string] $PathValue
    )

    $trimmedValue = $PathValue.Trim().Trim('"')
    $expandedValue = [Environment]::ExpandEnvironmentVariables($trimmedValue)
    $fullPath = [System.IO.Path]::GetFullPath($expandedValue)
    $pathRoot = [System.IO.Path]::GetPathRoot($fullPath)

    if ($fullPath.Length -gt $pathRoot.Length) {
        return $fullPath.TrimEnd([char[]]@(
            [System.IO.Path]::DirectorySeparatorChar,
            [System.IO.Path]::AltDirectorySeparatorChar
        ))
    }

    return $fullPath
}

if ([string]::IsNullOrWhiteSpace($CanonicalRoot)) {
    $CanonicalRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
}

$resolvedSkillPath = (Resolve-Path -LiteralPath $SkillPath).Path
$normalizedSkillPath = ConvertTo-NormalizedPath -PathValue $resolvedSkillPath
$normalizedCanonicalRoot = ConvertTo-NormalizedPath -PathValue $CanonicalRoot
$skillFile = Join-Path $normalizedSkillPath "SKILL.md"
$problems = [System.Collections.Generic.List[string]]::new()

if (-not (Test-Path -LiteralPath $skillFile -PathType Leaf)) {
    $problems.Add("SKILL.md is missing")
}

$canonicalPrefix = $normalizedCanonicalRoot + [System.IO.Path]::DirectorySeparatorChar
$isInsideCanonicalRoot = $normalizedSkillPath.StartsWith(
    $canonicalPrefix,
    [System.StringComparison]::OrdinalIgnoreCase
)

if (-not $isInsideCanonicalRoot) {
    $problems.Add("Skill is outside the canonical Codex skills root")
}

$relativeSkillPath = if ($isInsideCanonicalRoot) {
    $normalizedSkillPath.Substring($canonicalPrefix.Length)
}
else {
    ""
}

if ($relativeSkillPath.StartsWith(
    ".system" + [System.IO.Path]::DirectorySeparatorChar,
    [System.StringComparison]::OrdinalIgnoreCase
)) {
    $problems.Add("Personal shared skills must not be stored under .system")
}

$skillName = Split-Path -Leaf $normalizedSkillPath
if (Test-Path -LiteralPath $skillFile -PathType Leaf) {
    $skillText = Get-Content -Raw -Encoding UTF8 -LiteralPath $skillFile
    $nameMatch = [regex]::Match($skillText, '(?m)^name:\s*([^\r\n]+)$')
    if (-not $nameMatch.Success) {
        $problems.Add("SKILL.md frontmatter has no name field")
    }
    else {
        $frontmatterName = $nameMatch.Groups[1].Value.Trim().Trim('"').Trim("'")
        if (-not $frontmatterName.Equals($skillName, [System.StringComparison]::Ordinal)) {
            $problems.Add("Skill folder and frontmatter name do not match")
        }
    }
}

$configuredRoots = [System.Collections.Generic.List[object]]::new()
$matchingScopes = [System.Collections.Generic.List[string]]::new()
$pathSeparatorPattern = [regex]::Escape([string][System.IO.Path]::PathSeparator)
$pathSources = [System.Collections.Generic.List[object]]::new()

if (-not [string]::IsNullOrWhiteSpace($WispSkillsPath)) {
    $pathSources.Add([ordered]@{
        scope = "Argument"
        value = $WispSkillsPath
    })
}

foreach ($scope in @("Process", "User", "Machine")) {
    $rawValue = [Environment]::GetEnvironmentVariable("WISP_SKILLS_PATH", $scope)
    if ([string]::IsNullOrWhiteSpace($rawValue)) {
        continue
    }

    $pathSources.Add([ordered]@{
        scope = $scope
        value = $rawValue
    })
}

foreach ($pathSource in $pathSources) {
    foreach ($entry in ($pathSource.value -split $pathSeparatorPattern)) {
        if ([string]::IsNullOrWhiteSpace($entry)) {
            continue
        }

        try {
            $normalizedEntry = ConvertTo-NormalizedPath -PathValue $entry
            $configuredRoots.Add([ordered]@{
                scope = $pathSource.scope
                path = $normalizedEntry
            })

            if ($normalizedEntry.Equals(
                $normalizedCanonicalRoot,
                [System.StringComparison]::OrdinalIgnoreCase
            )) {
                $matchingScopes.Add($pathSource.scope)
            }
        }
        catch {
            $configuredRoots.Add([ordered]@{
                scope = $pathSource.scope
                path = $entry
                error = $_.Exception.Message
            })
        }
    }
}

$wispReadsCanonicalSource = $matchingScopes.Count -gt 0
$status = if ($problems.Count -gt 0) {
    "invalid_skill"
}
elseif (-not $wispReadsCanonicalSource -and $configuredRoots.Count -eq 0) {
    "wisp_path_missing"
}
elseif (-not $wispReadsCanonicalSource) {
    "wisp_path_mismatch"
}
else {
    "shared"
}

$result = [ordered]@{
    status = $status
    skill_name = $skillName
    skill_path = $normalizedSkillPath
    canonical_root = $normalizedCanonicalRoot
    source_is_valid = $problems.Count -eq 0
    wisp_reads_canonical_source = $wispReadsCanonicalSource
    matching_scopes = @($matchingScopes)
    configured_roots = @($configuredRoots)
    problems = @($problems)
    next_action = if ($status -eq "shared") {
        "Reload skills in Wisp and start a new conversation when required."
    }
    else {
        "Configure WISP_SKILLS_PATH to include the canonical root, restart Wisp, and verify again."
    }
}

$result | ConvertTo-Json -Depth 6

if ($status -ne "shared") {
    exit 2
}
