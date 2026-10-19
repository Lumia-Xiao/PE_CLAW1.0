[CmdletBinding()]
param(
    [string]$BaseUrl = 'https://pe-claw.local',
    [string]$EnvironmentFile = (Join-Path $PSScriptRoot 'pe-claw.env.ps1'),
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
    [string]$Python = '',
    [string]$Nssm = 'nssm.exe',
    [string]$LogRoot = 'C:\ProgramData\PE-Claw\logs',
    [string]$EvidenceRoot = 'C:\ProgramData\PE-Claw\evidence',
    [string]$PostgresService = 'postgresql-x64-16',
    [string]$RedisService = 'Memurai',
    [int]$TimeoutSeconds = 900,
    [switch]$ExerciseRecovery,
    [switch]$AllowHttp
)

$ErrorActionPreference = 'Stop'
if (-not $AllowHttp -and -not $BaseUrl.StartsWith('https://', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Acceptance requires HTTPS. Use -AllowHttp only for an isolated pre-IIS diagnostic.'
}
if (-not (Test-Path -LiteralPath $EnvironmentFile -PathType Leaf)) { throw 'The Git-ignored deployment environment file is required.' }
. $EnvironmentFile
if (-not $Python) {
    $candidate = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
    $Python = if (Test-Path -LiteralPath $candidate) { $candidate } else { (Get-Command python.exe -ErrorAction Stop).Source }
}
$nssmPath = (Get-Command $Nssm -ErrorAction Stop).Source
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$evidenceDirectory = Join-Path $EvidenceRoot "windows-native-$stamp"
New-Item -ItemType Directory -Force -Path $evidenceDirectory | Out-Null
$evidencePath = Join-Path $evidenceDirectory 'evidence.json'
$serviceNames = 'PE-Claw-API', 'PE-Claw-Worker', 'PE-Claw-Recovery'
$evidence = [ordered]@{
    schema_version = '1.0'
    status = 'running'
    timestamp = (Get-Date).ToUniversalTime().ToString('o')
    base_url = $BaseUrl
    services = [ordered]@{}
    checks = [ordered]@{}
}
$failed = $false

function Get-Sha256([string]$Value) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = $sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Value))
        return (($bytes | ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally { $sha.Dispose() }
}

function Get-ServiceEvidence([string]$Name) {
    $service = Get-Service -Name $Name -ErrorAction Stop
    $escaped = $Name.Replace("'", "''")
    $configuration = Get-CimInstance Win32_Service -Filter "Name='$escaped'" -ErrorAction Stop
    if ($service.Status -ne 'Running' -or $configuration.StartMode -ne 'Auto') {
        throw "$Name is not running with Automatic startup."
    }
    return [ordered]@{ status = $service.Status.ToString(); start_type = $configuration.StartMode }
}

function Assert-ForbiddenPath([string]$Path) {
    try {
        $response = Invoke-WebRequest "$($BaseUrl.TrimEnd('/'))$Path" -TimeoutSec 15
        if ([int]$response.StatusCode -lt 400) { throw "Forbidden path was served: $Path" }
    } catch {
        if ($_.Exception.Message -like 'Forbidden path was served:*') { throw }
        $status = $null
        if ($_.Exception.Response) { $status = [int]$_.Exception.Response.StatusCode }
        if (-not $status -or $status -lt 400) { throw }
    }
}

function Get-Job([string]$JobId) {
    Invoke-RestMethod "$($BaseUrl.TrimEnd('/'))/api/v1/design-jobs/$JobId" -TimeoutSec 15
}

function Wait-ForState([string]$JobId, [scriptblock]$Ready, [int]$PollMilliseconds = 2000) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $job = Get-Job $JobId
        if (& $Ready $job) { return $job }
        if ($job.status -in 'failed', 'cancelled', 'expired') { throw "Job entered terminal status $($job.status)" }
        Start-Sleep -Milliseconds $PollMilliseconds
    }
    throw 'Timed out waiting for the design job.'
}

function Get-CheckpointEvidence([string]$JobId, [string]$ThroughStage = '') {
    $arguments = @('-B', (Join-Path $ProjectRoot 'scripts\web_job_recovery_evidence.py'), $JobId)
    if ($ThroughStage) { $arguments += '--through-stage', $ThroughStage }
    $output = & $Python @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Could not read checkpoint evidence.' }
    return ($output | ConvertFrom-Json)
}

try {
    $environmentHashes = @()
    $expectedParameters = @{
        'PE-Claw-API' = '-m uvicorn pe_claw_web.api.main:app --host 127.0.0.1 --port 8000'
        'PE-Claw-Worker' = '-m celery -A pe_claw_web.workers.celery_app:celery_app worker --pool=solo --concurrency=1 --loglevel=info'
        'PE-Claw-Recovery' = '-m pe_claw_web.jobs.maintenance recover --loop'
    }
    $expectedProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path.TrimEnd('\')
    $expectedPython = (Resolve-Path -LiteralPath $Python).Path
    foreach ($name in $serviceNames) {
        $evidence.services[$name] = Get-ServiceEvidence $name
        $rawEnvironment = (& $nssmPath get $name AppEnvironmentExtra) -join "`n"
        if ($LASTEXITCODE -ne 0) { throw "Could not read NSSM configuration for $name" }
        $application = ((& $nssmPath get $name Application) -join '').Trim()
        $appDirectory = ((& $nssmPath get $name AppDirectory) -join '').Trim().TrimEnd('\')
        $appParameters = ((& $nssmPath get $name AppParameters) -join '').Trim()
        if ($LASTEXITCODE -ne 0) { throw "Could not read NSSM application configuration for $name" }
        if (-not $application.Equals($expectedPython, [StringComparison]::OrdinalIgnoreCase)) { throw "$name does not use the accepted Python executable." }
        if (-not $appDirectory.Equals($expectedProjectRoot, [StringComparison]::OrdinalIgnoreCase)) { throw "$name does not use the accepted source checkout." }
        if ($appParameters -ne $expectedParameters[$name]) { throw "$name does not use the accepted entry point and arguments." }
        $environmentHashes += Get-Sha256 $rawEnvironment
    }
    foreach ($name in $PostgresService, $RedisService, 'W3SVC') {
        $evidence.services[$name] = Get-ServiceEvidence $name
    }
    if (($environmentHashes | Select-Object -Unique).Count -ne 1) { throw 'API, Worker and Recovery do not share the same environment configuration.' }
    $evidence.checks.shared_configuration = $true
    $gitPath = (Get-Command git.exe -ErrorAction Stop).Source
    $revision = (& $gitPath -C $ProjectRoot rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $revision -notmatch '^[0-9a-f]{40}$') { throw 'Could not resolve the deployed Git revision.' }
    $worktreeChanges = @(& $gitPath -C $ProjectRoot status --porcelain --untracked-files=all)
    if ($LASTEXITCODE -ne 0 -or $worktreeChanges.Count -ne 0) { throw 'The deployed checkout is not clean and cannot be tied to one code revision.' }
    $evidence.code_revision = $revision

    $frontend = Invoke-WebRequest $BaseUrl -TimeoutSec 15
    if ([int]$frontend.StatusCode -ne 200 -or $frontend.Content -notmatch '<div id="root"') { throw 'IIS did not serve the React entry page.' }
    foreach ($header in 'Strict-Transport-Security', 'Content-Security-Policy', 'X-Content-Type-Options', 'X-Frame-Options') {
        if (-not $frontend.Headers[$header]) { throw "IIS response is missing security header $header." }
    }
    $health = Invoke-RestMethod "$($BaseUrl.TrimEnd('/'))/api/v1/health" -TimeoutSec 15
    if ($health.status -ne 'ok') { throw 'API health check failed.' }
    $catalog = Invoke-RestMethod "$($BaseUrl.TrimEnd('/'))/api/v1/topologies" -TimeoutSec 15
    if (-not $catalog.topologies) { throw 'Topology catalog is empty.' }
    $evidence.checks.https_frontend_headers_and_proxy = $true

    foreach ($path in '/src/pe_claw_web/api/main.py', '/libraries/semiconductors/data/private.csv', '/.git/config', '/outputs/', '/pe-claw.env.ps1') {
        Assert-ForbiddenPath $path
    }
    $evidence.checks.internal_paths_blocked = $true

    $payload = @{
        request = @{
            topology = 'buck_diode_rectified_unidirectional'; vin_min = 36; vin_max = 60; vout = 12; pout = 120
            fs_khz = 100; ripple_current_ratio = 0.3; ripple_voltage_ratio_percent = 1
        }
        execution_profile = 'complete'
        client_request_id = "windows-$stamp"
    } | ConvertTo-Json -Depth 5
    $created = Invoke-RestMethod "$($BaseUrl.TrimEnd('/'))/api/v1/design-jobs" -Method Post -ContentType 'application/json' -Body $payload -TimeoutSec 30
    $jobId = $created.job_id
    $evidence.job_id = $jobId

    if ($ExerciseRecovery) {
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
        if (-not ([Security.Principal.WindowsPrincipal]$identity).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
            throw 'Recovery exercise requires an Administrator PowerShell.'
        }
        Wait-ForState $jobId { param($job) $job.stage_details.capacitor.status -eq 'succeeded' -and $job.status -eq 'running' } 250 | Out-Null
        Stop-Service -Name 'PE-Claw-Worker' -Force
        $before = Get-CheckpointEvidence $jobId 'capacitor'
        if ($before.completed_stage -ne 'capacitor') { throw 'Checkpoint did not stop at the capacitor safety boundary.' }
        Stop-Service -Name $RedisService -Force
        Stop-Service -Name $PostgresService -Force
        Start-Service -Name $PostgresService
        Start-Service -Name $RedisService
        Start-Service -Name 'PE-Claw-Recovery'
        Start-Service -Name 'PE-Claw-API'
        Start-Sleep -Seconds ([int]$env:PE_CLAW_LEASE_SECONDS + 5)
        Start-Service -Name 'PE-Claw-Worker'
        Restart-Service -Name W3SVC -Force
        $evidence.recovery_before = $before
    }

    $completed = Wait-ForState $jobId { param($job) $job.status -eq 'succeeded' }
    if ($ExerciseRecovery -and $completed.attempt -ne 2) { throw "Expected exactly two attempts, observed $($completed.attempt)." }
    if ($ExerciseRecovery) {
        Start-Sleep -Seconds 5
        $stable = Get-Job $jobId
        if ($stable.status -ne 'succeeded' -or $stable.attempt -ne 2) { throw 'A late delivery changed the terminal job or created a third attempt.' }
    }
    $result = Invoke-RestMethod "$($BaseUrl.TrimEnd('/'))/api/v1/design-jobs/$jobId/result" -TimeoutSec 30
    if ($result.job_id -ne $jobId -or $result.schema_version -ne '1.0') { throw 'Result response does not belong to the accepted job contract.' }
    $manifest = Invoke-RestMethod "$($BaseUrl.TrimEnd('/'))/api/v1/design-jobs/$jobId/artifacts" -TimeoutSec 30
    if (-not $manifest) { throw 'Artifact manifest is empty.' }
    foreach ($artifact in $manifest) {
        if (-not $artifact.download_url.StartsWith("/api/v1/design-jobs/$jobId/")) { throw 'Artifact is not scoped to the current job.' }
        $target = Join-Path $evidenceDirectory $artifact.name
        Invoke-WebRequest "$($BaseUrl.TrimEnd('/'))$($artifact.download_url)" -OutFile $target -TimeoutSec 60
        $actual = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $artifact.sha256 -or (Get-Item -LiteralPath $target).Length -ne $artifact.size) { throw "Artifact verification failed: $($artifact.id)" }
    }
    if ($ExerciseRecovery) {
        $after = Get-CheckpointEvidence $jobId 'capacitor'
        if ($after.hardware_sha256 -ne $evidence.recovery_before.hardware_sha256) { throw 'Selected hardware changed across recovery.' }
        $evidence.recovery_after = $after
    }
    $evidence.attempt = $completed.attempt
    $evidence.artifact_count = @($manifest).Count
    $evidence.checks.job_and_artifact_hashes = $true

    $secretCandidates = @()
    foreach ($value in $env:PE_CLAW_DATABASE_URL, $env:PE_CLAW_REDIS_URL) {
        if ($value -match '://[^:]*:([^@]+)@') { $secretCandidates += [Uri]::UnescapeDataString($Matches[1]) }
    }
    $logViolations = @()
    if (Test-Path -LiteralPath $LogRoot) {
        foreach ($log in Get-ChildItem -LiteralPath $LogRoot -File -Filter '*.log') {
            $content = Get-Content -LiteralPath $log.FullName -Raw
            if ($content -match 'Traceback \(most recent call last\)') { $logViolations += $log.Name }
            foreach ($secret in $secretCandidates) {
                if ($secret -and $content.Contains($secret)) { $logViolations += $log.Name }
            }
        }
    }
    if ($logViolations) { throw 'Deployment logs contain a traceback or configured secret.' }
    $evidence.checks.logs_sanitized = $true
    $evidence.status = 'passed'
} catch {
    $failed = $true
    $evidence.status = 'failed'
    $evidence.error_type = $_.Exception.GetType().Name
} finally {
    $json = $evidence | ConvertTo-Json -Depth 8
    [IO.File]::WriteAllText($evidencePath, $json, (New-Object Text.UTF8Encoding($false)))
    $json
}
if ($failed) { throw "Windows native acceptance failed. Inspect $evidencePath and service logs." }
