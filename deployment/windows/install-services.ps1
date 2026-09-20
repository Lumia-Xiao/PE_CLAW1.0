param([string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
      [string]$Nssm = 'nssm.exe', [switch]$Force)
$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if (-not ([Security.Principal.WindowsPrincipal]$identity).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Run PowerShell as Administrator.' }
$python = (Get-Command python.exe -ErrorAction Stop).Source
$envFile = Join-Path $PSScriptRoot 'pe-claw.env.ps1'
if (-not (Test-Path $envFile)) { throw "Copy pe-claw.env.ps1.example to pe-claw.env.ps1 and set secrets." }
. $envFile
$artifact = [Environment]::ExpandEnvironmentVariables($env:PE_CLAW_ARTIFACT_ROOT)
New-Item -ItemType Directory -Force -Path $artifact | Out-Null
$services = @(
 @{Name='PE-Claw-API'; Args='-m uvicorn pe_claw_web.api.main:app --host 127.0.0.1 --port 8000'},
 @{Name='PE-Claw-Worker'; Args='-m celery -A pe_claw_web.workers.celery_app:celery_app worker --pool=solo --loglevel=info'},
 @{Name='PE-Claw-Recovery'; Args='-m pe_claw_web.jobs.maintenance recover --loop'})
foreach ($service in $services) {
  if (Get-Service $service.Name -ErrorAction SilentlyContinue) { if ($Force) { & $Nssm remove $service.Name confirm } else { throw "$($service.Name) already exists; use -Force." } }
  & $Nssm install $service.Name $python $service.Args
  & $Nssm set $service.Name AppDirectory $ProjectRoot
  & $Nssm set $service.Name AppEnvironmentExtra "PYTHONPATH=$ProjectRoot\src" "PE_CLAW_DATABASE_URL=$env:PE_CLAW_DATABASE_URL" "PE_CLAW_REDIS_URL=$env:PE_CLAW_REDIS_URL" "PE_CLAW_ARTIFACT_ROOT=$env:PE_CLAW_ARTIFACT_ROOT" "PE_CLAW_LEASE_SECONDS=$env:PE_CLAW_LEASE_SECONDS" "PE_CLAW_HEARTBEAT_SECONDS=$env:PE_CLAW_HEARTBEAT_SECONDS"
  & $Nssm set $service.Name Start SERVICE_AUTO_START
  & $Nssm set $service.Name AppExit Default Restart
  & $Nssm set $service.Name AppStdout "$ProjectRoot\logs\$($service.Name).out.log"
  & $Nssm set $service.Name AppStderr "$ProjectRoot\logs\$($service.Name).err.log"
}
& $python -m alembic upgrade head
Write-Host 'Services installed. Start them with Start-Service PE-Claw-API,PE-Claw-Worker,PE-Claw-Recovery.'
