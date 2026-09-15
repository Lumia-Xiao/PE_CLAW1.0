param([string]$BaseUrl='http://127.0.0.1:8000', [string]$ArtifactRoot=$env:PE_CLAW_ARTIFACT_ROOT)
$ErrorActionPreference='Stop'
$services='PE-Claw-API','PE-Claw-Worker','PE-Claw-Recovery'
$state=@{services=@{}; checks=@{}}
foreach($name in $services){$s=Get-Service $name -ErrorAction SilentlyContinue; $state.services[$name]=if($s){$s.Status.ToString()}else{'missing'}}
$health=Invoke-RestMethod "$BaseUrl/api/v1/health" -TimeoutSec 10
if($health.status -ne 'ok'){throw 'API health check failed'}
$state.checks.health=$true
$topologies=Invoke-RestMethod "$BaseUrl/api/v1/topologies" -TimeoutSec 10
if(-not $topologies){throw 'Topology catalog is empty'}
$state.checks.topologies=$true
$state.timestamp=(Get-Date).ToUniversalTime().ToString('o')
$state | ConvertTo-Json -Depth 5
