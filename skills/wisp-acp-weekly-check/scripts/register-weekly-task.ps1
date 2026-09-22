#requires -Version 5.1
<#
.SYNOPSIS
Registers the current user's weekly Wisp ACP version check without a console window.
.DESCRIPTION
Uses Task Scheduler and an existing pythonw.exe. Does not install or update software,
store credentials, elevate privileges, or start the task immediately. The schedule is
local China Standard Time; the script does not change the computer's time zone.
Use -WhatIf to review the resolved action and schedule without registering anything.
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Medium')]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$PythonPath,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$OutputDir,

    [ValidateSet('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')]
    [string]$Weekday = 'Monday',

    [ValidatePattern('^(?:[01][0-9]|2[0-3]):[0-5][0-9]$')]
    [string]$At = '09:00',

    [string]$SkillDir = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($SkillDir)) {
    # Resolve after parameter binding: PSScriptRoot may be empty while defaults
    # are evaluated by Windows PowerShell launched with -File.
    $scriptDirectory = $PSScriptRoot
    if ([string]::IsNullOrWhiteSpace($scriptDirectory)) {
        $scriptFile = $PSCommandPath
        if ([string]::IsNullOrWhiteSpace($scriptFile)) {
            $scriptFile = $MyInvocation.MyCommand.Path
        }
        if ([string]::IsNullOrWhiteSpace($scriptFile)) {
            throw 'Cannot determine the skill directory. Run this script with -File or provide -SkillDir explicitly.'
        }
        $scriptDirectory = Split-Path -Parent $scriptFile
    }
    $SkillDir = Split-Path -Parent $scriptDirectory
}
Import-Module ScheduledTasks -ErrorAction Stop

function ConvertTo-WindowsArgument {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Value)
    if ($Value.IndexOfAny([char[]]@([char]0, [char]10, [char]13)) -ge 0) {
        throw 'A task argument contains an unsupported control character.'
    }
    # Quote for Windows argv parsing, including any backslashes before quotes or
    # at the end of an argument. No shell interprets this command line.
    $escaped = [regex]::Replace($Value, '(\\*)"', '$1$1\"')
    $escaped = [regex]::Replace($escaped, '(\\+)$', '$1$1')
    return '"' + $escaped + '"'
}

$taskName = 'Wisp-ACP-Weekly-Check'
$taskPath = '\'
$marker = '[wisp-acp-weekly-check:v1]'
$timeZone = Get-TimeZone
if ($timeZone.Id -ne 'China Standard Time') {
    throw "This schedule expects China Standard Time (Beijing time); the computer uses '$($timeZone.Id)'. No time zone or task was changed."
}

$pythonItem = Get-Item -LiteralPath $PythonPath -ErrorAction Stop
if ($pythonItem.PSIsContainer -or $pythonItem.Name -notin @('python.exe', 'pythonw.exe')) {
    throw 'PythonPath must point to an existing python.exe or pythonw.exe.'
}
$pythonwPath = Join-Path -Path $pythonItem.DirectoryName -ChildPath 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonwPath -PathType Leaf)) {
    throw "pythonw.exe is missing beside '$($pythonItem.FullName)'. Supply a Python installation with pythonw.exe; no task was registered."
}
$pythonwPath = (Get-Item -LiteralPath $pythonwPath).FullName

$skillItem = Get-Item -LiteralPath $SkillDir -ErrorAction Stop
if (-not $skillItem.PSIsContainer) {
    throw 'SkillDir must be a directory.'
}
$skillPath = $skillItem.FullName
$checkerPath = Join-Path -Path $skillPath -ChildPath 'scripts\check_acp.py'
if (-not (Test-Path -LiteralPath $checkerPath -PathType Leaf)) {
    throw "The checker is missing: $checkerPath"
}
$checkerPath = (Get-Item -LiteralPath $checkerPath).FullName
$outputPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputDir)
if (Test-Path -LiteralPath $outputPath -PathType Leaf) {
    throw "OutputDir is an existing file: $outputPath"
}
$arguments = (ConvertTo-WindowsArgument $checkerPath) + ' --output-dir ' + (ConvertTo-WindowsArgument $outputPath)

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$currentUser = $identity.Name
$currentSid = $identity.User.Value
# Enumerate the root with terminating errors so access failures cannot be mistaken
# for an absent task. Never replace an unrelated task with the same name.
$existing = @(Get-ScheduledTask -TaskPath $taskPath -ErrorAction Stop | Where-Object { $_.TaskName -eq $taskName })
if ($existing.Count -gt 1) {
    throw "Multiple tasks matched $taskPath$taskName; no task was changed."
}
if ($existing.Count -eq 1) {
    $previous = $existing[0]
    $markedAsOurs = ([string]$previous.Description).Contains($marker)
    $checkerPrefix = (ConvertTo-WindowsArgument $checkerPath) + ' '
    $pointsToChecker = @($previous.Actions | Where-Object {
        ([IO.Path]::GetFileName([string]$_.Execute) -in @('python.exe', 'pythonw.exe')) -and
        ([string]$_.Arguments).StartsWith($checkerPrefix, [StringComparison]::OrdinalIgnoreCase)
    }).Count -gt 0
    if (-not ($markedAsOurs -or $pointsToChecker)) {
        throw "An unrelated task already uses $taskPath$taskName. It was not overwritten."
    }
    if ([string]$previous.Principal.UserId -notin @($currentUser, $currentSid)) {
        throw "The existing task belongs to another user. It was not overwritten."
    }
}

$atTime = [datetime]::ParseExact($At, 'HH:mm', [Globalization.CultureInfo]::InvariantCulture)
$action = New-ScheduledTaskAction -Execute $pythonwPath -Argument $arguments -WorkingDirectory $skillPath
$trigger = New-ScheduledTaskTrigger -Weekly -WeeksInterval 1 -DaysOfWeek $Weekday -At $atTime
$principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew
$description = "$marker Checks configured Wisp ACP adapter versions each $Weekday at $At (China Standard Time). Reports to $outputPath. Check only; no software updates. Runs only while this user is logged on."
$definition = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description $description

$operation = if ($existing.Count -eq 1) { 'Update' } else { 'Create' }
$registered = $false
$nextRunTime = $null
if ($PSCmdlet.ShouldProcess("$taskPath$taskName ($currentUser; $Weekday $At China Standard Time)", "$operation weekly ACP check")) {
    if ($existing.Count -eq 1) {
        $null = Register-ScheduledTask -TaskPath $taskPath -TaskName $taskName -InputObject $definition -Force
    }
    else {
        $null = Register-ScheduledTask -TaskPath $taskPath -TaskName $taskName -InputObject $definition
    }
    $savedTask = Get-ScheduledTask -TaskPath $taskPath -TaskName $taskName -ErrorAction Stop
    if (([string]$savedTask.Description).Contains($marker) -eq $false -or
        @($savedTask.Actions).Count -ne 1 -or
        $savedTask.Actions[0].Execute -ne $pythonwPath -or
        $savedTask.Actions[0].Arguments -ne $arguments) {
        throw 'Task registration returned, but the saved action could not be verified. Inspect the task before reporting success.'
    }
    $registered = $true
    $nextRunTime = (Get-ScheduledTaskInfo -TaskPath $taskPath -TaskName $taskName).NextRunTime
}

[pscustomobject]@{
    TaskName = $taskName
    TaskPath = $taskPath
    Registered = $registered
    Operation = $operation
    Weekday = $Weekday
    At = $At
    TimeZone = $timeZone.Id
    User = $currentUser
    LogonType = 'Interactive'
    RunLevel = 'Limited'
    Execute = $pythonwPath
    Arguments = $arguments
    WorkingDirectory = $skillPath
    OutputDir = $outputPath
    NextRunTime = $nextRunTime
    StartWhenAvailable = $true
    ExecutionTimeLimit = 'PT5M'
    AllowStartIfOnBatteries = $true
    DontStopIfGoingOnBatteries = $true
    MultipleInstances = 'IgnoreNew'
}
