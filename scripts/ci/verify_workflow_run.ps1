Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

param(
    [string]$Owner = "ShaiksTeam",
    [string]$Repo = "ZeroUI2.0",
    [string]$WorkflowFile = "pm_modules_audit.yml",
    [string]$Branch = "main",
    [string[]]$TokenEnvVarNames = @("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT")
)

function Get-Token {
    param([string[]]$Names)
    foreach ($name in $Names) {
        $value = [Environment]::GetEnvironmentVariable($name)
        if ($value) {
            return @{ Name = $name; Value = $value }
        }
    }
    return $null
}

$tokenInfo = Get-Token -Names $TokenEnvVarNames
if (-not $tokenInfo) {
    Write-Host "No GitHub token found in env vars: $($TokenEnvVarNames -join ', ')"
    Write-Host "Manual steps:"
    Write-Host "1) Open GitHub -> Actions"
    Write-Host "2) Select the workflow: $WorkflowFile"
    Write-Host "3) Check the latest run on branch $Branch"
    exit 2
}

$headers = @{
    Authorization = "token $($tokenInfo.Value)"
    Accept = "application/vnd.github+json"
    "User-Agent" = "ZeroUI-Audit-Verify"
}

try {
    $workflowUrl = "https://api.github.com/repos/$Owner/$Repo/actions/workflows/$WorkflowFile"
    $workflow = Invoke-RestMethod -Uri $workflowUrl -Headers $headers -Method Get
} catch {
    $statusCode = $null
    if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
        $statusCode = [int]$_.Exception.Response.StatusCode
    }
    if ($statusCode -eq 404) {
        Write-Host "ERROR: Workflow not found. Check owner/repo/workflow filename."
        Write-Host ("Owner=" + $Owner + " Repo=" + $Repo + " WorkflowFile=" + $WorkflowFile)
        exit 1
    }
    throw
}

$workflowId = $workflow.id
$runsUrl = "https://api.github.com/repos/$Owner/$Repo/actions/workflows/$workflowId/runs?branch=$Branch&per_page=1"
$runs = Invoke-RestMethod -Uri $runsUrl -Headers $headers -Method Get

if (-not $runs.workflow_runs -or $runs.workflow_runs.Count -eq 0) {
    Write-Host "ERROR: No workflow runs returned for $WorkflowFile on branch $Branch."
    exit 1
}

$latest = $runs.workflow_runs[0]
Write-Host ("RUN_ID=" + $latest.id)
Write-Host ("STATUS=" + $latest.status)
Write-Host ("CONCLUSION=" + $latest.conclusion)
Write-Host ("CREATED_AT=" + $latest.created_at)
Write-Host ("HEAD_SHA=" + $latest.head_sha)
Write-Host ("HTML_URL=" + $latest.html_url)

if ($latest.status -ne "completed" -or $latest.conclusion -ne "success") {
    exit 1
}
exit 0
