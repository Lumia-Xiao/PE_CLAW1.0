param([string]$SiteName='PE-Claw', [string]$DistRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\web\frontend\dist')).Path,
      [string]$HostName='pe-claw.local', [int]$HttpsPort=443)
$ErrorActionPreference='Stop'
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
if (-not ([Security.Principal.WindowsPrincipal]$identity).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Run PowerShell as Administrator.' }
Import-Module WebAdministration -ErrorAction Stop
if (-not (Get-Website $SiteName -ErrorAction SilentlyContinue)) { New-Website -Name $SiteName -PhysicalPath $DistRoot -Port 80 -HostHeader $HostName | Out-Null }
Copy-Item (Join-Path $PSScriptRoot 'web.config') (Join-Path $DistRoot 'web.config') -Force
Write-Host "IIS site $SiteName configured for $DistRoot. Bind a trusted certificate to HTTPS/$HttpsPort and install URL Rewrite + ARR before production use."
