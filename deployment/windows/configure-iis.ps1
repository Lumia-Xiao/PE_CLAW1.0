[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$SiteName = 'PE-Claw',
    [string]$AppPoolName = 'PE-Claw',
    [string]$DistRoot = (Join-Path $PSScriptRoot '..\..\web\frontend\dist'),
    [string]$HostName = 'pe-claw.local',
    [int]$HttpPort = 80,
    [int]$HttpsPort = 443,
    [Parameter(Mandatory)][ValidatePattern('^[0-9A-Fa-f]{40}$')][string]$CertificateThumbprint,
    [switch]$EnableHttpRedirect,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if (-not ([Security.Principal.WindowsPrincipal]$identity).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run PowerShell as Administrator.'
}
Import-Module WebAdministration -ErrorAction Stop
if (-not (Test-Path -LiteralPath (Join-Path $DistRoot 'index.html') -PathType Leaf)) { throw 'Build web/frontend/dist before configuring IIS.' }
$DistRoot = (Resolve-Path -LiteralPath $DistRoot).Path
$forbidden = Get-ChildItem -LiteralPath $DistRoot -Recurse -File | Where-Object { $_.Extension -in '.py', '.ps1', '.env', '.db', '.sqlite', '.toml', '.ini' }
if ($forbidden) { throw 'The frontend distribution contains forbidden server-side files.' }
$rewrite = Get-WebGlobalModule | Where-Object Name -EQ 'RewriteModule'
if (-not $rewrite) { throw 'IIS URL Rewrite is not installed.' }
try { Get-WebConfigurationProperty -PSPath 'MACHINE/WEBROOT/APPHOST' -Filter 'system.webServer/proxy' -Name enabled -ErrorAction Stop | Out-Null }
catch { throw 'Application Request Routing (ARR) is not installed.' }
$certificatePath = "Cert:\LocalMachine\My\$($CertificateThumbprint.Replace(' ', ''))"
if (-not (Test-Path -LiteralPath $certificatePath)) { throw 'The requested LocalMachine certificate was not found.' }

$existing = Get-Website -Name $SiteName -ErrorAction SilentlyContinue
if ($existing -and -not $Force) { throw "IIS site $SiteName already exists; use -Force to replace only that named site." }
if ($PSCmdlet.ShouldProcess($SiteName, 'Configure IIS application pool, HTTPS site and reverse proxy')) {
    if ($existing) { Remove-Website -Name $SiteName }
    if (-not (Test-Path "IIS:\AppPools\$AppPoolName")) { New-WebAppPool -Name $AppPoolName | Out-Null }
    Set-ItemProperty "IIS:\AppPools\$AppPoolName" -Name managedRuntimeVersion -Value ''
    Set-ItemProperty "IIS:\AppPools\$AppPoolName" -Name processModel.identityType -Value ApplicationPoolIdentity
    Copy-Item (Join-Path $PSScriptRoot 'web.config') (Join-Path $DistRoot 'web.config') -Force
    & icacls.exe $DistRoot /grant:r "IIS AppPool\${AppPoolName}:(OI)(CI)RX" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Failed to grant the IIS application pool read access to the frontend distribution.' }
    New-Website -Name $SiteName -PhysicalPath $DistRoot -ApplicationPool $AppPoolName -Port $HttpsPort -HostHeader $HostName -Ssl | Out-Null
    Set-WebBinding -Name $SiteName -Protocol https -BindingInformation "*:${HttpsPort}:$HostName" -PropertyName sslFlags -Value 1
    $binding = Get-WebBinding -Name $SiteName -Protocol https
    $binding.AddSslCertificate($CertificateThumbprint.Replace(' ', ''), 'My')
    if ($EnableHttpRedirect) {
        New-WebBinding -Name $SiteName -Protocol http -Port $HttpPort -HostHeader $HostName
    }
    Set-WebConfigurationProperty -PSPath 'MACHINE/WEBROOT/APPHOST' -Filter 'system.webServer/proxy' -Name enabled -Value true
}
Write-Host "IIS site $SiteName is bound to https://$HostName`:$HttpsPort. Validate the trusted certificate and API proxy with verify-windows-native.ps1."
