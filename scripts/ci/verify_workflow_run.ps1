[CmdletBinding()]
param(
  [Parameter()][string]$Owner = "ShaiksTeam",
  [Parameter()][string]$Repo = "ZeroUI2.0",
  [Parameter()][string]$WorkflowFile = "ccp_modules_audit.yml",
  [Parameter()][string]$Branch = "FM-1-Release-Failures",
  [Parameter()][string]$Token = $env:GITHUB_TOKEN
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Token)) {
  Write-Host "FAIL: GITHUB_TOKEN is empty. Set it in this PowerShell session:" -ForegroundColor Red
  Write-Host "  `$env:GITHUB_TOKEN = '<PAT>'" -ForegroundColor Yellow
  exit 2
}

$Token = $Token.Trim()

$headers = @{
  Authorization = "Bearer $Token"
  Accept        = "application/vnd.github+json"
  "X-GitHub-Api-Version" = "2022-11-28"
}

function Invoke-GitHub([string]$Url) {
  try {
    return Invoke-RestMethod -Headers $headers -Uri $Url -Method Get
  } catch {
    $msg = $_.Exception.Message
    Write-Host "FAIL: GitHub API call failed: $Url" -ForegroundColor Red
    Write-Host "ERROR: $msg" -ForegroundColor Red
    if ($msg -match "401") { Write-Host "Hint: Token missing/invalid/revoked." -ForegroundColor Yellow }
    if ($msg -match "403") { Write-Host "Hint: Token lacks permissions (needs Actions read + repo access)." -ForegroundColor Yellow }
    if ($msg -match "404") { Write-Host "Hint: Repo/workflow not found OR token lacks access to this repo." -ForegroundColor Yellow }
    exit 3
  }
}

# 1) Verify auth works (no token printing)
$me = Invoke-GitHub "https://api.github.com/user"
Write-Host ("OK: authenticated as login={0}" -f $me.login)

# 2) Resolve workflow by filename
$wfUrl = "https://api.github.com/repos/$Owner/$Repo/actions/workflows/$WorkflowFile"
$wf = Invoke-GitHub $wfUrl
Write-Host ("OK: workflow resolved name={0} id={1}" -f $wf.name, $wf.id)

# 3) Get latest run for branch
$runsUrl = "https://api.github.com/repos/$Owner/$Repo/actions/workflows/$($wf.id)/runs?branch=$Branch&per_page=1"
$runs = Invoke-GitHub $runsUrl

if (-not $runs.workflow_runs -or $runs.workflow_runs.Count -lt 1) {
  Write-Host "FAIL: No workflow runs found for this workflow+branch." -ForegroundColor Red
  Write-Host ("workflow={0} branch={1}" -f $WorkflowFile, $Branch)
  exit 4
}

$run = $runs.workflow_runs[0]

Write-Host ("WORKFLOW_NAME={0}" -f $wf.name)
Write-Host ("BRANCH={0}" -f $Branch)
Write-Host ("RUN_ID={0}" -f $run.id)
Write-Host ("STATUS={0}" -f $run.status)
Write-Host ("CONCLUSION={0}" -f $run.conclusion)
Write-Host ("CREATED_AT={0}" -f $run.created_at)
Write-Host ("HTML_URL={0}" -f $run.html_url)

if ($run.conclusion -ne "success") {
  Write-Host "FAIL: latest run is not success." -ForegroundColor Red
  exit 5
}

Write-Host "PASS: latest workflow run is success." -ForegroundColor Green
exit 0
