# PATCH HEADER
#
# Discovered anchors:
#   - storage-scripts/config/environments.json: environments structure
#   - dist/src/platform/config/infra_config_runner.js: compiled Node.js runner
#   - config/InfraConfig.ts: loadInfraConfig() function
#
# Files created/edited:
#   - scripts/di_config_verify.ps1 (created)
#   - src/platform/config/infra_config_runner.ts (created)
#   - docs/DI_Config_README.md (created)
#   - tsconfig.config.json (created)
#
# STOP/MISSING triggers:
#   - None encountered
#   - No new dependencies added (uses existing Node.js, no ts-node)
#   - No placeholder interpolation (loader preserves placeholders as-is)
#   - No vendor strings in neutral infra (validation code only)
#   - No environments.json keys renamed/removed
#   - No log truncation behavior introduced
#
# DI Config Verification Script
#
# Validates infrastructure configuration for all environments in environments.json
# Uses compiled JavaScript runner (no ts-node dependency)

param(
    [string]$BuildPath = "dist\src\platform\config\infra_config_runner.js"
)

$ErrorActionPreference = "Stop"

# Get script directory and repo root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir

# Paths
$EnvironmentsJson = Join-Path $RepoRoot "storage-scripts\config\environments.json"
$RunnerPath = Join-Path $RepoRoot $BuildPath

# Check if environments.json exists
if (-not (Test-Path $EnvironmentsJson)) {
    Write-Host "FAIL: environments.json not found at: $EnvironmentsJson" -ForegroundColor Red
    exit 1
}

# Check if runner exists
if (-not (Test-Path $RunnerPath)) {
    Write-Host "FAIL: Runner not found at: $RunnerPath" -ForegroundColor Red
    Write-Host "HINT: Build the TypeScript project first (e.g., tsc)" -ForegroundColor Yellow
    exit 1
}

# Read environments.json
try {
    $EnvironmentsData = Get-Content $EnvironmentsJson -Raw | ConvertFrom-Json
} catch {
    Write-Host "FAIL: Failed to parse environments.json: $_" -ForegroundColor Red
    exit 1
}

# Get list of environments
if (-not $EnvironmentsData.environments) {
    Write-Host "FAIL: No 'environments' key found in environments.json" -ForegroundColor Red
    exit 1
}

$EnvNames = $EnvironmentsData.environments.PSObject.Properties.Name
if ($EnvNames.Count -eq 0) {
    Write-Host "FAIL: No environments found in environments.json" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== DI Config Verification ===" -ForegroundColor Cyan
Write-Host "Environments to verify: $($EnvNames.Count)`n" -ForegroundColor Cyan

# Track results
$Results = @()
$HasFailures = $false

# Change to repo root for runner execution
Push-Location $RepoRoot

try {
    foreach ($EnvName in $EnvNames) {
        Write-Host -NoNewline "  $EnvName ... "

        # Run the Node.js runner
        $ProcessInfo = New-Object System.Diagnostics.ProcessStartInfo
        $ProcessInfo.FileName = "node"
        $ProcessInfo.Arguments = "`"$RunnerPath`" --env `"$EnvName`""
        $ProcessInfo.UseShellExecute = $false
        $ProcessInfo.RedirectStandardOutput = $true
        $ProcessInfo.RedirectStandardError = $true
        $ProcessInfo.CreateNoWindow = $true
        $ProcessInfo.WorkingDirectory = $RepoRoot

        $Process = New-Object System.Diagnostics.Process
        $Process.StartInfo = $ProcessInfo

        # Capture output
        $OutputBuilder = New-Object System.Text.StringBuilder
        $ErrorBuilder = New-Object System.Text.StringBuilder

        $OutputEvent = Register-ObjectEvent -InputObject $Process -EventName OutputDataReceived -Action {
            if ($EventArgs.Data) {
                [void]$Event.MessageData.AppendLine($EventArgs.Data)
            }
        } -MessageData $OutputBuilder

        $ErrorEvent = Register-ObjectEvent -InputObject $Process -EventName ErrorDataReceived -Action {
            if ($EventArgs.Data) {
                [void]$Event.MessageData.AppendLine($EventArgs.Data)
            }
        } -MessageData $ErrorBuilder

        $Process.Start() | Out-Null
        $Process.BeginOutputReadLine()
        $Process.BeginErrorReadLine()
        $Process.WaitForExit()

        $ExitCode = $Process.ExitCode
        $Output = $OutputBuilder.ToString()
        $ErrorOutput = $ErrorBuilder.ToString()

        # Cleanup events
        Unregister-Event -SourceIdentifier $OutputEvent.Name
        Unregister-Event -SourceIdentifier $ErrorEvent.Name

        # Parse JSON output (last line should be JSON)
        $OutputLines = $Output -split "`n" | Where-Object { $_.Trim() -ne "" }
        $JsonOutput = $null
        if ($OutputLines.Count -gt 0) {
            try {
                $JsonOutput = $OutputLines[-1] | ConvertFrom-Json
            } catch {
                # If JSON parsing fails, use error output
            }
        }

        if ($ExitCode -eq 0) {
            Write-Host "PASS" -ForegroundColor Green
            $Results += [PSCustomObject]@{
                Environment = $EnvName
                Status = "PASS"
                Reason = "Configuration loaded successfully"
            }
        } else {
            Write-Host "FAIL" -ForegroundColor Red
            $Reason = if ($JsonOutput -and $JsonOutput.error) {
                $JsonOutput.error
            } elseif ($ErrorOutput) {
                $ErrorOutput.Trim()
            } else {
                "Unknown error (exit code: $ExitCode)"
            }
            Write-Host "    Reason: $Reason" -ForegroundColor Red
            $Results += [PSCustomObject]@{
                Environment = $EnvName
                Status = "FAIL"
                Reason = $Reason
            }
            $HasFailures = $true
        }
    }
} finally {
    Pop-Location
}

# Print PASS matrix
Write-Host "`n=== PASS Matrix ===" -ForegroundColor Cyan
Write-Host ""

$MaxEnvLength = ($Results | ForEach-Object { $_.Environment.Length } | Measure-Object -Maximum).Maximum
$FormatString = "  {0,-$MaxEnvLength}  {1,-4}  {2}"

Write-Host ($FormatString -f "Environment", "Status", "Reason") -ForegroundColor Yellow
Write-Host ("  " + ("-" * ($MaxEnvLength + 4 + 4 + 50))) -ForegroundColor Gray

foreach ($Result in $Results) {
    $Color = if ($Result.Status -eq "PASS") { "Green" } else { "Red" }
    Write-Host ($FormatString -f $Result.Environment, $Result.Status, $Result.Reason) -ForegroundColor $Color
}

Write-Host ""

# Summary
$PassCount = ($Results | Where-Object { $_.Status -eq "PASS" }).Count
$FailCount = ($Results | Where-Object { $_.Status -eq "FAIL" }).Count
$TotalCount = $Results.Count

Write-Host "Summary: $PassCount/$TotalCount PASSED, $FailCount/$TotalCount FAILED" -ForegroundColor $(if ($HasFailures) { "Red" } else { "Green" })
Write-Host ""

# Exit with appropriate code
if ($HasFailures) {
    Write-Host "FAIL: One or more environments failed validation" -ForegroundColor Red
    exit 1
} else {
    Write-Host "PASS: All environments validated successfully" -ForegroundColor Green
    exit 0
}
