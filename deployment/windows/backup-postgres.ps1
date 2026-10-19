[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Database,
    [string]$HostName = '127.0.0.1',
    [int]$Port = 5432,
    [Parameter(Mandatory)][string]$User,
    [string]$PgDump = 'pg_dump.exe',
    [string]$PgRestore = 'pg_restore.exe',
    [string]$BackupRoot = 'C:\ProgramData\PE-Claw\backups',
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
foreach ($tool in $PgDump, $PgRestore) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { throw "PostgreSQL tool not found: $tool" }
}
New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$target = Join-Path $BackupRoot "pe-claw-$stamp.dump"
if ((Test-Path -LiteralPath $target) -and -not $Force) { throw "Backup already exists: $target" }

# Authentication must come from a service-account PGPASSFILE or an interactive
# password prompt. Passwords are never accepted as script parameters or logged.
& $PgDump --host $HostName --port $Port --username $User --dbname $Database --format custom --file $target
if ($LASTEXITCODE -ne 0) { throw "pg_dump failed with exit code $LASTEXITCODE" }
& $PgRestore --list $target | Out-Null
if ($LASTEXITCODE -ne 0) { throw "pg_restore could not read the backup" }

$file = Get-Item -LiteralPath $target
$manifest = [ordered]@{
    schema_version = '1.0'
    created_at = (Get-Date).ToUniversalTime().ToString('o')
    database = $Database
    host = $HostName
    port = $Port
    file = $file.Name
    size = $file.Length
    sha256 = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
}
$manifestPath = "$target.json"
[IO.File]::WriteAllText($manifestPath, ($manifest | ConvertTo-Json), (New-Object Text.UTF8Encoding($false)))
$manifest | ConvertTo-Json
