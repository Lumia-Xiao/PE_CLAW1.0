[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$ArtifactRoot,
    [string]$BackupRoot = 'C:\ProgramData\PE-Claw\backups',
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
function Get-Sha256File([string]$Path) {
    $sha = [Security.Cryptography.SHA256]::Create()
    $inputStream = [IO.File]::OpenRead($Path)
    try { return ([BitConverter]::ToString($sha.ComputeHash($inputStream))).Replace('-', '').ToLowerInvariant() }
    finally { $inputStream.Dispose(); $sha.Dispose() }
}

if (-not (Test-Path -LiteralPath $ArtifactRoot -PathType Container)) { throw "Artifact root not found: $ArtifactRoot" }
$source = (Resolve-Path -LiteralPath $ArtifactRoot).Path.TrimEnd('\')
$project = (Resolve-Path -LiteralPath $ProjectRoot).Path.TrimEnd('\')
if ($source.Equals($project, [StringComparison]::OrdinalIgnoreCase) -or $source.StartsWith("$project\", [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Artifact storage must be outside the source checkout.'
}
New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
$destination = (Resolve-Path -LiteralPath $BackupRoot).Path.TrimEnd('\')
if ($destination.Equals($source, [StringComparison]::OrdinalIgnoreCase) -or $destination.StartsWith("$source\", [StringComparison]::OrdinalIgnoreCase)) {
    throw 'BackupRoot must not be inside ArtifactRoot.'
}

$files = @(Get-ChildItem -LiteralPath $source -Recurse -File -Force | Sort-Object FullName)
$links = @(Get-ChildItem -LiteralPath $source -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
if ($links.Count) { throw 'Artifact backups refuse junctions and symbolic links.' }
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$archivePath = Join-Path $destination "pe-claw-artifacts-$stamp.zip"
$manifestPath = "$archivePath.json"
if (((Test-Path -LiteralPath $archivePath) -or (Test-Path -LiteralPath $manifestPath)) -and -not $Force) {
    throw "Artifact backup already exists: $archivePath"
}
if ($Force) {
    Remove-Item -LiteralPath $archivePath, $manifestPath -Force -ErrorAction SilentlyContinue
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$stream = [IO.File]::Open($archivePath, [IO.FileMode]::CreateNew)
try {
    $archive = New-Object IO.Compression.ZipArchive($stream, [IO.Compression.ZipArchiveMode]::Create, $false)
    try {
        $entries = @()
        foreach ($file in $files) {
            $relative = $file.FullName.Substring($source.Length).TrimStart('\').Replace('\', '/')
            if (-not $relative -or $relative.StartsWith('/') -or $relative.Split('/') -contains '..') { throw "Unsafe artifact path: $relative" }
            [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, $file.FullName, $relative, [IO.Compression.CompressionLevel]::Optimal) | Out-Null
            $entries += [ordered]@{
                path = $relative
                size = $file.Length
                sha256 = Get-Sha256File $file.FullName
            }
        }
    }
    finally { $archive.Dispose() }
}
finally { $stream.Dispose() }

$verification = [IO.Compression.ZipFile]::OpenRead($archivePath)
try {
    $names = @($verification.Entries | ForEach-Object FullName | Sort-Object)
    $expected = @($entries | ForEach-Object path | Sort-Object)
    if ((Compare-Object $names $expected).Count) { throw 'Artifact archive entry verification failed.' }
}
finally { $verification.Dispose() }

$archiveFile = Get-Item -LiteralPath $archivePath
$manifest = [ordered]@{
    schema_version = '1.0'
    created_at = (Get-Date).ToUniversalTime().ToString('o')
    source = $source
    archive = $archiveFile.Name
    file_count = $files.Count
    source_bytes = ($files | Measure-Object Length -Sum).Sum
    archive_bytes = $archiveFile.Length
    archive_sha256 = Get-Sha256File $archivePath
    files = $entries
}
[IO.File]::WriteAllText($manifestPath, ($manifest | ConvertTo-Json -Depth 5), (New-Object Text.UTF8Encoding($false)))
$manifest | ConvertTo-Json -Depth 5
