[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
    [string]$EnvironmentFile = (Join-Path $PSScriptRoot 'pe-claw.env.ps1'),
    [string]$Nssm = 'nssm.exe',
    [string]$Python = '',
    [string]$LogRoot = 'C:\ProgramData\PE-Claw\logs',
    [string]$ServiceAccount = 'NT AUTHORITY\NetworkService',
    [string]$PostgresService = 'postgresql-x64-16',
    [string]$RedisService = 'Memurai',
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]$identity
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run PowerShell as Administrator.'
}
if (-not (Test-Path -LiteralPath $EnvironmentFile -PathType Leaf)) {
    throw 'Copy pe-claw.env.ps1.example to the Git-ignored pe-claw.env.ps1 and replace all placeholders.'
}
. $EnvironmentFile
$required = 'PE_CLAW_DATABASE_URL', 'PE_CLAW_REDIS_URL', 'PE_CLAW_ARTIFACT_ROOT', 'PE_CLAW_LEASE_SECONDS', 'PE_CLAW_HEARTBEAT_SECONDS'
foreach ($name in $required) {
    $value = [Environment]::GetEnvironmentVariable($name)
    if (-not $value -or $value -match '<[^>]+>|REPLACE') { throw "Missing or placeholder environment value: $name" }
}
if ($env:PE_CLAW_DATABASE_URL -notmatch '^postgresql\+psycopg://' -or $env:PE_CLAW_REDIS_URL -notmatch '^rediss?://') {
    throw 'Windows deployment requires PostgreSQL (postgresql+psycopg://) and Redis/Memurai (redis:// or rediss://).'
}

$nssmPath = (Get-Command $Nssm -ErrorAction Stop).Source
if (-not $Python) {
    $venvPython = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
    $Python = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { (Get-Command python.exe -ErrorAction Stop).Source }
}
$Python = (Resolve-Path -LiteralPath $Python).Path
$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$retentionHours = if ($env:PE_CLAW_ARTIFACT_RETENTION_HOURS) { $env:PE_CLAW_ARTIFACT_RETENTION_HOURS } else { '168' }
$artifactRoot = [IO.Path]::GetFullPath([Environment]::ExpandEnvironmentVariables($env:PE_CLAW_ARTIFACT_ROOT))
$normalizedProjectRoot = $ProjectRoot.TrimEnd('\')
if ($artifactRoot.Equals($normalizedProjectRoot, [StringComparison]::OrdinalIgnoreCase) -or
    $artifactRoot.StartsWith($normalizedProjectRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'PE_CLAW_ARTIFACT_ROOT must be outside the source checkout for a Windows deployment.'
}
foreach ($dependency in $PostgresService, $RedisService) {
    if (-not (Get-Service -Name $dependency -ErrorAction SilentlyContinue)) { throw "Required Windows service is missing: $dependency" }
}

function Invoke-Nssm([Parameter(ValueFromRemainingArguments)][string[]]$Arguments) {
    & $nssmPath @Arguments | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "NSSM failed: $($Arguments[0..1] -join ' ')" }
}

foreach ($path in $artifactRoot, $LogRoot) {
    if ($PSCmdlet.ShouldProcess($path, 'Create deployment directory and grant service-account modify access')) {
        New-Item -ItemType Directory -Force -Path $path | Out-Null
        & icacls.exe $path /inheritance:r /grant:r "${ServiceAccount}:(OI)(CI)M" 'BUILTIN\Administrators:(OI)(CI)F' | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Failed to set ACL on $path" }
    }
}
if ($PSCmdlet.ShouldProcess($ProjectRoot, 'Grant service-account read and execute access')) {
    & icacls.exe $ProjectRoot /grant:r "${ServiceAccount}:(OI)(CI)RX" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Failed to grant source read access.' }
}

$environment = @(
    "PYTHONPATH=$ProjectRoot\src",
    "PE_CLAW_DATABASE_URL=$env:PE_CLAW_DATABASE_URL",
    "PE_CLAW_REDIS_URL=$env:PE_CLAW_REDIS_URL",
    "PE_CLAW_ARTIFACT_ROOT=$artifactRoot",
    "PE_CLAW_LEASE_SECONDS=$env:PE_CLAW_LEASE_SECONDS",
    "PE_CLAW_HEARTBEAT_SECONDS=$env:PE_CLAW_HEARTBEAT_SECONDS",
    "PE_CLAW_ARTIFACT_RETENTION_HOURS=$retentionHours"
)
$services = @(
    @{ Name = 'PE-Claw-API'; Arguments = '-m uvicorn pe_claw_web.api.main:app --host 127.0.0.1 --port 8000'; Dependencies = @($PostgresService) },
    @{ Name = 'PE-Claw-Worker'; Arguments = '-m celery -A pe_claw_web.workers.celery_app:celery_app worker --pool=solo --concurrency=1 --loglevel=info'; Dependencies = @($PostgresService, $RedisService) },
    @{ Name = 'PE-Claw-Recovery'; Arguments = '-m pe_claw_web.jobs.maintenance recover --loop'; Dependencies = @($PostgresService, $RedisService) }
)

if ($PSCmdlet.ShouldProcess('PostgreSQL database', 'Run Alembic upgrade head before service registration')) {
    & $Python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw 'Alembic migration failed; no services were registered.' }
}

foreach ($service in $services) {
    $existing = Get-Service -Name $service.Name -ErrorAction SilentlyContinue
    if ($existing -and -not $Force) { throw "$($service.Name) already exists; rerun with -Force only after backing up its configuration." }
    if (-not $PSCmdlet.ShouldProcess($service.Name, 'Install and configure Windows service')) { continue }
    if ($existing) {
        Stop-Service -Name $service.Name -Force -ErrorAction SilentlyContinue
        Invoke-Nssm remove $service.Name confirm
    }
    Invoke-Nssm install $service.Name $Python
    Invoke-Nssm set $service.Name AppParameters $service.Arguments
    Invoke-Nssm set $service.Name AppDirectory $ProjectRoot
    Invoke-Nssm set $service.Name AppEnvironmentExtra @environment
    Invoke-Nssm set $service.Name ObjectName $ServiceAccount
    Invoke-Nssm set $service.Name DependOnService @($service.Dependencies)
    Invoke-Nssm set $service.Name Start SERVICE_AUTO_START
    Invoke-Nssm set $service.Name AppExit Default Restart
    Invoke-Nssm set $service.Name AppRestartDelay 5000
    Invoke-Nssm set $service.Name AppStdout (Join-Path $LogRoot "$($service.Name).out.log")
    Invoke-Nssm set $service.Name AppStderr (Join-Path $LogRoot "$($service.Name).err.log")
    Invoke-Nssm set $service.Name AppRotateFiles 1
    Invoke-Nssm set $service.Name AppRotateOnline 1
    Invoke-Nssm set $service.Name AppRotateBytes 10485760
}

Write-Host 'Services registered but not started. Review NSSM configuration, then start PE-Claw-API, PE-Claw-Worker and PE-Claw-Recovery.'
