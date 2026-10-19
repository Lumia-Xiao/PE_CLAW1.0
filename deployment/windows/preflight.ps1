[CmdletBinding()]
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
    [string]$EnvironmentFile = (Join-Path $PSScriptRoot 'pe-claw.env.ps1'),
    [string]$Nssm = 'nssm.exe',
    [string]$PostgresBin = '',
    [string]$RedisExecutable = '',
    [string]$CertificateThumbprint = '',
    [switch]$RequireAdministrator,
    [switch]$RequireIis,
    [string]$EvidencePath = ''
)

$ErrorActionPreference = 'Stop'
$checks = [ordered]@{}
$details = [ordered]@{}

function Resolve-CommandPath([string]$Name, [string]$ExplicitPath = '') {
    if ($ExplicitPath) {
        if (Test-Path -LiteralPath $ExplicitPath -PathType Leaf) {
            return (Resolve-Path -LiteralPath $ExplicitPath).Path
        }
        return $null
    }
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    return $null
}

function Test-OutsideProject([string]$PathValue) {
    try {
        $full = [IO.Path]::GetFullPath([Environment]::ExpandEnvironmentVariables($PathValue))
        $project = [IO.Path]::GetFullPath($ProjectRoot).TrimEnd('\')
        return -not (
            $full.Equals($project, [StringComparison]::OrdinalIgnoreCase) -or
            $full.StartsWith($project + '\', [StringComparison]::OrdinalIgnoreCase)
        )
    } catch { return $false }
}

function Get-VersionLine([string]$Executable, [string[]]$Arguments = @('--version')) {
    if (-not $Executable) { return $null }
    try { return ((& $Executable @Arguments 2>&1 | Select-Object -First 1).ToString().Trim()) }
    catch { return $null }
}

$checks.windows = ([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT)
$checks.administrator = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)
$pythonCandidate = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$python = if (Test-Path -LiteralPath $pythonCandidate) { (Resolve-Path -LiteralPath $pythonCandidate).Path } else { Resolve-CommandPath 'python.exe' }
$checks.python = [bool]$python
$checks.node = [bool](Resolve-CommandPath 'node.exe')
$checks.npm = [bool](Resolve-CommandPath 'npm.cmd')
$checks.nssm = [bool](Resolve-CommandPath $Nssm)
$pgRoot = if ($PostgresBin) { (Resolve-Path -LiteralPath $PostgresBin -ErrorAction SilentlyContinue).Path } else { '' }
$checks.psql = [bool](Resolve-CommandPath 'psql.exe' $(if ($pgRoot) { Join-Path $pgRoot 'psql.exe' } else { '' }))
$checks.pg_dump = [bool](Resolve-CommandPath 'pg_dump.exe' $(if ($pgRoot) { Join-Path $pgRoot 'pg_dump.exe' } else { '' }))
$checks.pg_restore = [bool](Resolve-CommandPath 'pg_restore.exe' $(if ($pgRoot) { Join-Path $pgRoot 'pg_restore.exe' } else { '' }))
$redis = if ($RedisExecutable) { Resolve-CommandPath '' $RedisExecutable } else { Resolve-CommandPath 'redis-server.exe' }
if (-not $redis) { $redis = Resolve-CommandPath 'memurai.exe' }
$checks.redis = [bool]$redis
$details.executables = [ordered]@{
    python = $python
    node = Resolve-CommandPath 'node.exe'
    npm = Resolve-CommandPath 'npm.cmd'
    nssm = Resolve-CommandPath $Nssm
    psql = Resolve-CommandPath 'psql.exe' $(if ($pgRoot) { Join-Path $pgRoot 'psql.exe' } else { '' })
    pg_dump = Resolve-CommandPath 'pg_dump.exe' $(if ($pgRoot) { Join-Path $pgRoot 'pg_dump.exe' } else { '' })
    pg_restore = Resolve-CommandPath 'pg_restore.exe' $(if ($pgRoot) { Join-Path $pgRoot 'pg_restore.exe' } else { '' })
    redis = $redis
}
$details.versions = [ordered]@{
    python = Get-VersionLine $details.executables.python @('--version')
    node = Get-VersionLine $details.executables.node @('--version')
    npm = Get-VersionLine $details.executables.npm @('--version')
    postgres = Get-VersionLine $details.executables.psql @('--version')
    redis = Get-VersionLine $details.executables.redis @('--version')
}
$checks.frontend = (Test-Path -LiteralPath (Join-Path $ProjectRoot 'web\frontend\dist\index.html') -PathType Leaf)
$checks.environment_file = (Test-Path -LiteralPath $EnvironmentFile -PathType Leaf)

if ($checks.environment_file) {
    . $EnvironmentFile
    $required = 'PE_CLAW_DATABASE_URL', 'PE_CLAW_REDIS_URL', 'PE_CLAW_ARTIFACT_ROOT', 'PE_CLAW_LEASE_SECONDS', 'PE_CLAW_HEARTBEAT_SECONDS'
    $missing = @($required | Where-Object { -not [Environment]::GetEnvironmentVariable($_) })
    $placeholder = @($required | Where-Object { [Environment]::GetEnvironmentVariable($_) -match '<[^>]+>|REPLACE' })
    $checks.environment_values = ($missing.Count -eq 0 -and $placeholder.Count -eq 0)
    $checks.connection_schemes = $checks.environment_values -and
        ($env:PE_CLAW_DATABASE_URL -match '^postgresql\+psycopg://') -and
        ($env:PE_CLAW_REDIS_URL -match '^rediss?://')
    $checks.artifact_isolation = $checks.environment_values -and (Test-OutsideProject $env:PE_CLAW_ARTIFACT_ROOT)
    $numericSettings = [ordered]@{
        PE_CLAW_SESSION_HOURS = if ($env:PE_CLAW_SESSION_HOURS) { $env:PE_CLAW_SESSION_HOURS } else { '8' }
        PE_CLAW_MAX_REQUEST_BYTES = if ($env:PE_CLAW_MAX_REQUEST_BYTES) { $env:PE_CLAW_MAX_REQUEST_BYTES } else { '65536' }
        PE_CLAW_MAX_CONCURRENT_JOBS = if ($env:PE_CLAW_MAX_CONCURRENT_JOBS) { $env:PE_CLAW_MAX_CONCURRENT_JOBS } else { '2' }
        PE_CLAW_DAILY_JOB_LIMIT = if ($env:PE_CLAW_DAILY_JOB_LIMIT) { $env:PE_CLAW_DAILY_JOB_LIMIT } else { '25' }
        PE_CLAW_JOB_TIMEOUT_SECONDS = if ($env:PE_CLAW_JOB_TIMEOUT_SECONDS) { $env:PE_CLAW_JOB_TIMEOUT_SECONDS } else { '1800' }
    }
    $invalidNumericSettings = @()
    foreach ($setting in $numericSettings.GetEnumerator()) {
        $parsed = 0
        if (-not [int]::TryParse([string]$setting.Value, [ref]$parsed) -or $parsed -lt 1) { $invalidNumericSettings += $setting.Key }
    }
    $checks.security_limits = ($invalidNumericSettings.Count -eq 0)
    $details.invalid_numeric_settings = $invalidNumericSettings
    $details.missing_environment_names = $missing
    $details.placeholder_environment_names = $placeholder
} else {
    $checks.environment_values = $false
    $checks.connection_schemes = $false
    $checks.artifact_isolation = $false
    $checks.security_limits = $false
}

if ($RequireIis) {
    $checks.iis_module = [bool](Get-Module -ListAvailable WebAdministration)
    $rewritePath = Join-Path $env:SystemRoot 'System32\inetsrv\rewrite.dll'
    $arrPath = Join-Path $env:SystemRoot 'System32\inetsrv\requestRouter.dll'
    $checks.url_rewrite = Test-Path -LiteralPath $rewritePath -PathType Leaf
    $checks.arr = Test-Path -LiteralPath $arrPath -PathType Leaf
    $normalizedThumbprint = $CertificateThumbprint.Replace(' ', '')
    $checks.certificate = ($normalizedThumbprint -match '^[0-9A-Fa-f]{40}$') -and (Test-Path -LiteralPath "Cert:\LocalMachine\My\$normalizedThumbprint")
}

$requiredChecks = @('windows', 'python', 'node', 'npm', 'nssm', 'psql', 'pg_dump', 'pg_restore', 'redis', 'frontend', 'environment_file', 'environment_values', 'connection_schemes', 'artifact_isolation', 'security_limits')
if ($RequireAdministrator) { $requiredChecks += 'administrator' }
if ($RequireIis) { $requiredChecks += 'iis_module', 'url_rewrite', 'arr', 'certificate' }
$blocked = @($requiredChecks | Where-Object { -not $checks[$_] })
$result = [ordered]@{
    schema_version = '1.0'
    status = if ($blocked.Count) { 'blocked' } else { 'ready' }
    checks = $checks
    blocked_checks = $blocked
    details = $details
    timestamp = (Get-Date).ToUniversalTime().ToString('o')
}
$json = $result | ConvertTo-Json -Depth 6
if ($EvidencePath) {
    $parent = Split-Path -Parent $EvidencePath
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    [IO.File]::WriteAllText([IO.Path]::GetFullPath($EvidencePath), $json, (New-Object Text.UTF8Encoding($false)))
}
$json
if ($blocked.Count) { exit 2 }
