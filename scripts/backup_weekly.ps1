[CmdletBinding()]
param(
    [string]$SourceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$BackupRoot = '',
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($BackupRoot)) {
    $BackupRoot = Split-Path -Parent $SourceRoot
}

$source = [System.IO.Path]::GetFullPath($SourceRoot.TrimEnd('\'))
$destinationRoot = [System.IO.Path]::GetFullPath($BackupRoot.TrimEnd('\'))

if (-not (Test-Path -LiteralPath $source -PathType Container)) {
    throw "Source directory does not exist: $source"
}
if (-not (Test-Path -LiteralPath $destinationRoot -PathType Container)) {
    New-Item -ItemType Directory -Path $destinationRoot | Out-Null
}

$projectName = Split-Path -Leaf $source
$dateStamp = Get-Date -Format 'yyyy-MM-dd'
$archivePath = Join-Path $destinationRoot ("{0}_backup_{1}.zip" -f $projectName, $dateStamp)

if ((Test-Path -LiteralPath $archivePath) -and -not $Force) {
    throw "Backup already exists for $dateStamp. Use -Force to replace it: $archivePath"
}

Add-Type -AssemblyName System.IO.Compression.FileSystem

$excludedDirectoryNames = @('__pycache__')
$excludedDirectoryPrefixes = @('.pytest-')
$excludedExtensions = @('.pyc', '.pyo', '.tmp', '.temp')
$files = @()
$excludedFiles = @()

foreach ($file in Get-ChildItem -LiteralPath $source -Recurse -Force -File) {
    $relative = $file.FullName.Substring($source.Length).TrimStart('\')
    $parts = $relative -split '[\\/]'
    $excluded = $false

    if ($parts.Length -gt 1) {
        foreach ($part in $parts[0..($parts.Length - 2)]) {
            if ($excludedDirectoryNames -contains $part) {
                $excluded = $true
            }
            foreach ($prefix in $excludedDirectoryPrefixes) {
                if ($part.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
                    $excluded = $true
                }
            }
        }
    }
    if ($excludedExtensions -contains $file.Extension.ToLowerInvariant()) {
        $excluded = $true
    }

    if ($excluded) {
        $excludedFiles += $relative
    } else {
        $files += $file
    }
}

$gitBranch = ''
$gitCommit = ''
$gitStatus = ''
try {
    $gitBranch = (& git -C $source branch --show-current 2>$null).Trim()
    $gitCommit = (& git -C $source rev-parse HEAD 2>$null).Trim()
    $gitStatus = (& git -C $source status --porcelain --untracked-files=all 2>$null) -join "`n"
} catch {
    $gitStatus = "Git metadata unavailable: $($_.Exception.Message)"
}

[int64]$sourceBytes = 0
foreach ($file in $files) {
    $sourceBytes += [int64]$file.Length
}

$manifest = [ordered]@{
    contract_version = 'pe_claw_weekly_backup_v1'
    created_at_local = (Get-Date).ToString('o')
    source_root = $source
    archive_path = $archivePath
    project_name = $projectName
    git_branch = $gitBranch
    git_commit = $gitCommit
    git_status = $gitStatus
    included_file_count = $files.Count
    included_bytes = $sourceBytes
    excluded_file_count = $excludedFiles.Count
    exclusions = @{
        directory_names = $excludedDirectoryNames
        directory_prefixes = $excludedDirectoryPrefixes
        extensions = $excludedExtensions
    }
}

$archive = $null
try {
    if (Test-Path -LiteralPath $archivePath) {
        Remove-Item -LiteralPath $archivePath -Force
    }

    $archive = [System.IO.Compression.ZipFile]::Open(
        $archivePath,
        [System.IO.Compression.ZipArchiveMode]::Create
    )

    foreach ($file in $files) {
        $relative = $file.FullName.Substring($source.Length).TrimStart('\')
        $entryName = ($projectName + '/' + $relative) -replace '\\', '/'
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $archive,
            $file.FullName,
            $entryName,
            [System.IO.Compression.CompressionLevel]::Optimal
        ) | Out-Null
    }

    $manifestEntry = $archive.CreateEntry($projectName + '/backup_manifest.json')
    $manifestWriter = New-Object System.IO.StreamWriter($manifestEntry.Open(), (New-Object System.Text.UTF8Encoding($false)))
    try {
        $manifestWriter.Write(($manifest | ConvertTo-Json -Depth 8))
        $manifestWriter.Write("`n")
    } finally {
        $manifestWriter.Dispose()
    }
} finally {
    if ($null -ne $archive) {
        $archive.Dispose()
    }
}

$archiveInfo = Get-Item -LiteralPath $archivePath
$result = [ordered]@{
    archive = $archivePath
    created_at_local = $manifest.created_at_local
    git_branch = $gitBranch
    git_commit = $gitCommit
    included_file_count = $files.Count
    excluded_file_count = $excludedFiles.Count
    source_bytes = $sourceBytes
    archive_bytes = [int64]$archiveInfo.Length
    compression_ratio = if ($sourceBytes -gt 0) { [math]::Round($archiveInfo.Length / $sourceBytes, 4) } else { $null }
}
$result | ConvertTo-Json -Depth 6
