<#
.SYNOPSIS
  Configure ZeroUI LLM Topology - Environment-driven LLM endpoint routing

.DESCRIPTION
  Configures LLM topology mode (LOCAL_SINGLE_PLANE or PER_PLANE) and plane-specific
  LLM base URLs via environment variables. Supports dry-run, verification, and
  idempotent updates to .env files.

  LOCAL_SINGLE_PLANE: All planes route to IDE LLM endpoint (local dev)
  PER_PLANE: Each plane has its own LLM endpoint (on-prem/staging)

.PARAMETER Mode
  Operation mode: "local" (LOCAL_SINGLE_PLANE), "per-plane" (PER_PLANE), or "verify" (validation only)

.PARAMETER RepoEnvPath
  Path to .env file relative to repo root (default: ".env")

.PARAMETER OutEnvPath
  Optional: Write to this file instead of RepoEnvPath. If set, RepoEnvPath is only read for existing values.

.PARAMETER IdeLlmBaseUrl
  IDE plane LLM base URL (default: "http://localhost:11434" for Ollama)

.PARAMETER TenantLlmBaseUrl
  Tenant plane LLM base URL (required for per-plane mode)

.PARAMETER ProductLlmBaseUrl
  Product plane LLM base URL (required for per-plane mode)

.PARAMETER SharedLlmBaseUrl
  Shared plane LLM base URL (required for per-plane mode)

.PARAMETER DoNotTouchRepoEnv
  If set, only write to OutEnvPath; do not modify RepoEnvPath. If OutEnvPath is not set, script exits with error.

.PARAMETER PrintDiff
  Show what keys would be added/changed (dry-run output)

.PARAMETER Apply
  Actually write changes; otherwise dry-run only

.EXAMPLE
  # Dry-run local mode
  .\configure_llm_topology.ps1 -Mode local -PrintDiff

.EXAMPLE
  # Apply local mode
  .\configure_llm_topology.ps1 -Mode local -Apply

.EXAMPLE
  # Apply per-plane mode
  .\configure_llm_topology.ps1 -Mode per-plane -TenantLlmBaseUrl "http://tenant-ollama:11434" -ProductLlmBaseUrl "http://product-ollama:11434" -SharedLlmBaseUrl "http://shared-ollama:11434" -Apply

.EXAMPLE
  # Verify current configuration
  .\configure_llm_topology.ps1 -Mode verify

.EXAMPLE
  # Write to separate file without touching .env
  .\configure_llm_topology.ps1 -Mode local -OutEnvPath "infra/local/llm.env" -DoNotTouchRepoEnv -Apply
#>

[CmdletBinding()]
param(
    [ValidateSet("local", "per-plane", "verify")]
    [string]$Mode,
    [string]$RepoEnvPath = ".env",
    [string]$OutEnvPath,
    [string]$IdeLlmBaseUrl = "http://localhost:11434",
    [string]$TenantLlmBaseUrl,
    [string]$ProductLlmBaseUrl,
    [string]$SharedLlmBaseUrl,
    [switch]$DoNotTouchRepoEnv,
    [switch]$PrintDiff,
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# --- Helper Functions ---

function Find-RepoRoot {
    <#
    .SYNOPSIS
      Find repository root directory.
    #>
    $current = Get-Location
    $maxDepth = 10
    $depth = 0

    while ($depth -lt $maxDepth) {
        if (Test-Path (Join-Path $current ".git")) {
            return $current
        }
        $parent = Split-Path -Parent $current -ErrorAction SilentlyContinue
        if (-not $parent -or $parent -eq $current) {
            break
        }
        $current = $parent
        $depth++
    }

    # Fallback: use current directory
    Write-Warning "Could not find .git directory; using current directory as repo root"
    return Get-Location
}

function Read-EnvFile {
    <#
    .SYNOPSIS
      Read .env file and return hashtable of key-value pairs, preserving comments and structure.
    #>
    param(
        [string]$FilePath
    )

    $result = @{
        Variables = @{}
        Lines = @()
        Comments = @()
    }

    if (-not (Test-Path $FilePath)) {
        return $result
    }

    $content = Get-Content -Path $FilePath -Raw
    if (-not $content) {
        return $result
    }

    $lines = $content -split "`r?`n"
    foreach ($line in $lines) {
        $trimmed = $line.Trim()
        
        # Preserve comments and empty lines
        if ($trimmed.StartsWith("#") -or $trimmed -eq "") {
            $result.Comments += $line
            $result.Lines += @{ Type = "comment"; Content = $line }
            continue
        }

        # Parse KEY=VALUE
        if ($trimmed -match '^([^#=]+?)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            # Remove inline comments
            if ($value -match '^([^#]+)') {
                $value = $matches[1].Trim()
            }
            # Remove quotes if present
            if ($value -match '^["''](.+)["'']$') {
                $value = $matches[1]
            }
            $result.Variables[$key] = $value
            $result.Lines += @{ Type = "variable"; Key = $key; Value = $value; Original = $line }
        } else {
            # Unknown format, preserve as-is
            $result.Lines += @{ Type = "unknown"; Content = $line }
        }
    }

    return $result
}

function Write-EnvFile {
    <#
    .SYNOPSIS
      Write .env file, updating existing keys and appending new ones in managed block.
    #>
    param(
        [string]$FilePath,
        [hashtable]$ExistingEnv,
        [hashtable]$NewVariables
    )

    $output = New-Object System.Collections.ArrayList
    $managedBlockStart = "# --- ZeroUI LLM Topology (managed) ---"
    $managedBlockEnd = "# --- end ---"
    $inManagedBlock = $false
    $managedKeysWritten = @()

    # Process existing lines
    foreach ($lineInfo in $ExistingEnv.Lines) {
        if ($lineInfo.Type -eq "comment") {
            if ($lineInfo.Content -eq $managedBlockStart) {
                $inManagedBlock = $true
                continue
            }
            if ($lineInfo.Content -eq $managedBlockEnd) {
                $inManagedBlock = $false
                continue
            }
            if (-not $inManagedBlock) {
                $output.Add($lineInfo.Content) | Out-Null
            }
            continue
        }

        if ($lineInfo.Type -eq "variable") {
            $key = $lineInfo.Key
            if ($NewVariables.ContainsKey($key)) {
                # Update existing variable
                $newValue = $NewVariables[$key]
                $output.Add("$key=$newValue") | Out-Null
                $managedKeysWritten += $key
                $NewVariables.Remove($key) | Out-Null
            } elseif (-not $inManagedBlock) {
                # Preserve existing variable not being updated
                $output.Add($lineInfo.Original) | Out-Null
            }
            continue
        }

        if ($lineInfo.Type -eq "unknown" -and -not $inManagedBlock) {
            $output.Add($lineInfo.Content) | Out-Null
        }
    }

    # Append managed block with new variables
    if ($NewVariables.Count -gt 0) {
        if ($output.Count -gt 0 -and $output[-1] -ne "") {
            $output.Add("") | Out-Null
        }
        $output.Add($managedBlockStart) | Out-Null
        foreach ($key in ($NewVariables.Keys | Sort-Object)) {
            $output.Add("$key=$($NewVariables[$key])") | Out-Null
        }
        $output.Add($managedBlockEnd) | Out-Null
    }

    # Ensure trailing newline
    $content = ($output -join "`n") + "`n"
    [System.IO.File]::WriteAllText($FilePath, $content, [System.Text.Encoding]::UTF8)
}

function Test-OllamaReachable {
    <#
    .SYNOPSIS
      Best-effort check if Ollama endpoint is reachable.
    #>
    param(
        [string]$BaseUrl
    )

    if (-not $BaseUrl) {
        return $false
    }

    # Check if it's localhost and ollama CLI exists
    if ($BaseUrl -match '^https?://localhost(:\d+)?') {
        $ollamaCmd = Get-Command "ollama" -ErrorAction SilentlyContinue
        if ($ollamaCmd) {
            try {
                $null = & ollama list 2>&1
                if ($LASTEXITCODE -eq 0) {
                    return $true
                }
            } catch {
                # Ignore errors
            }
        }
    }

    # Try HTTP HEAD/GET
    try {
        $uri = [System.Uri]$BaseUrl
        $request = [System.Net.WebRequest]::Create($uri)
        $request.Method = "HEAD"
        $request.Timeout = 2000
        $response = $request.GetResponse()
        $response.Close()
        return $true
    } catch {
        return $false
    }
}

# --- Main Logic ---

$repoRoot = Find-RepoRoot
$repoEnvFullPath = Join-Path $repoRoot $RepoEnvPath

# Determine target file
if ($OutEnvPath) {
    $targetEnvPath = if ([System.IO.Path]::IsPathRooted($OutEnvPath)) {
        $OutEnvPath
    } else {
        Join-Path $repoRoot $OutEnvPath
    }
} elseif ($DoNotTouchRepoEnv) {
    Write-Error "DoNotTouchRepoEnv is set but OutEnvPath is not provided. Cannot proceed."
    exit 1
} else {
    $targetEnvPath = $repoEnvFullPath
}

# Load existing env file
$existingEnv = Read-EnvFile -FilePath $repoEnvFullPath

# Compute desired configuration
$desiredVars = @{}

if ($Mode -eq "local") {
    $desiredVars["LLM_TOPOLOGY_MODE"] = "LOCAL_SINGLE_PLANE"
    $desiredVars["IDE_LLM_BASE_URL"] = $IdeLlmBaseUrl
    $desiredVars["TENANT_LLM_BASE_URL"] = $IdeLlmBaseUrl
    $desiredVars["PRODUCT_LLM_BASE_URL"] = $IdeLlmBaseUrl
    $desiredVars["SHARED_LLM_BASE_URL"] = $IdeLlmBaseUrl
    $desiredVars["LLM_FORWARD_TO_IDE_PLANES"] = "tenant,product,shared"
    $desiredVars["LLM_ROUTER_BASE_PATH"] = "/api/v1/llm"
    $desiredVars["LLM_ROUTER_HEALTH_PATH"] = "/health"
} elseif ($Mode -eq "per-plane") {
    if (-not $TenantLlmBaseUrl -or -not $ProductLlmBaseUrl -or -not $SharedLlmBaseUrl) {
        Write-Error "per-plane mode requires TenantLlmBaseUrl, ProductLlmBaseUrl, and SharedLlmBaseUrl parameters."
        exit 1
    }
    $desiredVars["LLM_TOPOLOGY_MODE"] = "PER_PLANE"
    $desiredVars["IDE_LLM_BASE_URL"] = $IdeLlmBaseUrl
    $desiredVars["TENANT_LLM_BASE_URL"] = $TenantLlmBaseUrl
    $desiredVars["PRODUCT_LLM_BASE_URL"] = $ProductLlmBaseUrl
    $desiredVars["SHARED_LLM_BASE_URL"] = $SharedLlmBaseUrl
    $desiredVars["LLM_ROUTER_BASE_PATH"] = "/api/v1/llm"
    $desiredVars["LLM_ROUTER_HEALTH_PATH"] = "/health"
    # Note: LLM_FORWARD_TO_IDE_PLANES is omitted in per-plane mode (not added to desiredVars)
    # If it exists in the managed block, it will be removed by Write-EnvFile
} elseif ($Mode -eq "verify") {
    # Verification mode: validate existing configuration
    $errors = @()
    $warnings = @()

    # Check required keys
    $requiredKeys = @(
        "LLM_TOPOLOGY_MODE",
        "IDE_LLM_BASE_URL",
        "TENANT_LLM_BASE_URL",
        "PRODUCT_LLM_BASE_URL",
        "SHARED_LLM_BASE_URL"
    )

    foreach ($key in $requiredKeys) {
        if (-not $existingEnv.Variables.ContainsKey($key) -or $existingEnv.Variables[$key] -eq "") {
            $errors += "Missing or empty required key: $key"
        }
    }

    # Validate mode-specific rules
    $topologyMode = $existingEnv.Variables["LLM_TOPOLOGY_MODE"]
    if ($topologyMode -eq "LOCAL_SINGLE_PLANE") {
        $ideUrl = $existingEnv.Variables["IDE_LLM_BASE_URL"]
        $tenantUrl = $existingEnv.Variables["TENANT_LLM_BASE_URL"]
        $productUrl = $existingEnv.Variables["PRODUCT_LLM_BASE_URL"]
        $sharedUrl = $existingEnv.Variables["SHARED_LLM_BASE_URL"]

        if ($tenantUrl -ne $ideUrl) {
            $errors += "LOCAL_SINGLE_PLANE violation: TENANT_LLM_BASE_URL ($tenantUrl) must equal IDE_LLM_BASE_URL ($ideUrl)"
        }
        if ($productUrl -ne $ideUrl) {
            $errors += "LOCAL_SINGLE_PLANE violation: PRODUCT_LLM_BASE_URL ($productUrl) must equal IDE_LLM_BASE_URL ($ideUrl)"
        }
        if ($sharedUrl -ne $ideUrl) {
            $errors += "LOCAL_SINGLE_PLANE violation: SHARED_LLM_BASE_URL ($sharedUrl) must equal IDE_LLM_BASE_URL ($ideUrl)"
        }
    } elseif ($topologyMode -eq "PER_PLANE") {
        $tenantUrl = $existingEnv.Variables["TENANT_LLM_BASE_URL"]
        $productUrl = $existingEnv.Variables["PRODUCT_LLM_BASE_URL"]
        $sharedUrl = $existingEnv.Variables["SHARED_LLM_BASE_URL"]

        if ([string]::IsNullOrWhiteSpace($tenantUrl)) {
            $errors += "PER_PLANE violation: TENANT_LLM_BASE_URL is empty"
        }
        if ([string]::IsNullOrWhiteSpace($productUrl)) {
            $errors += "PER_PLANE violation: PRODUCT_LLM_BASE_URL is empty"
        }
        if ([string]::IsNullOrWhiteSpace($sharedUrl)) {
            $errors += "PER_PLANE violation: SHARED_LLM_BASE_URL is empty"
        }
    } else {
        $errors += "Invalid LLM_TOPOLOGY_MODE: $topologyMode (must be LOCAL_SINGLE_PLANE or PER_PLANE)"
    }

    # Optional: probe reachability
    $ideUrl = $existingEnv.Variables["IDE_LLM_BASE_URL"]
    if ($ideUrl) {
        $reachable = Test-OllamaReachable -BaseUrl $ideUrl
        if ($reachable) {
            Write-Host "[OK] IDE LLM endpoint appears reachable: $ideUrl" -ForegroundColor Green
        } else {
            $warnings += "IDE LLM endpoint may be unreachable: $ideUrl"
        }
    }

    # Print results
    Write-Host "`n=== LLM Topology Verification ===" -ForegroundColor Cyan
    Write-Host "Configuration file: $repoEnvFullPath" -ForegroundColor Gray

    if ($errors.Count -eq 0) {
        Write-Host "`n[PASS] Configuration is valid" -ForegroundColor Green
        if ($warnings.Count -gt 0) {
            Write-Host "`nWarnings:" -ForegroundColor Yellow
            foreach ($warn in $warnings) {
                Write-Host "  - $warn" -ForegroundColor Yellow
            }
        }
        exit 0
    } else {
        Write-Host "`n[FAIL] Configuration has errors" -ForegroundColor Red
        foreach ($err in $errors) {
            Write-Host "  - $err" -ForegroundColor Red
        }
        if ($warnings.Count -gt 0) {
            Write-Host "`nWarnings:" -ForegroundColor Yellow
            foreach ($warn in $warnings) {
                Write-Host "  - $warn" -ForegroundColor Yellow
            }
        }
        exit 1
    }
}

# Compute changes
$changes = @{}
$updates = @{}
$additions = @{}

foreach ($key in $desiredVars.Keys) {
    $newValue = $desiredVars[$key]
    if ($existingEnv.Variables.ContainsKey($key)) {
        $oldValue = $existingEnv.Variables[$key]
        if ($oldValue -ne $newValue) {
            $changes[$key] = @{ Old = $oldValue; New = $newValue }
            $updates[$key] = $newValue
        }
    } else {
        $changes[$key] = @{ Old = $null; New = $newValue }
        $additions[$key] = $newValue
    }
}

# Print diff if requested
if ($PrintDiff -or -not $Apply) {
    Write-Host "`n=== LLM Topology Configuration Changes ===" -ForegroundColor Cyan
    Write-Host "Target file: $targetEnvPath" -ForegroundColor Gray
    Write-Host "Mode: $Mode" -ForegroundColor Gray

    if ($changes.Count -eq 0) {
        Write-Host "`nNo changes needed; configuration is already up to date." -ForegroundColor Green
    } else {
        Write-Host "`nChanges:" -ForegroundColor Yellow
        foreach ($key in ($changes.Keys | Sort-Object)) {
            $change = $changes[$key]
            if ($null -eq $change.Old) {
                Write-Host "  + $key = $($change.New)" -ForegroundColor Green
            } else {
                Write-Host "  ~ $key" -ForegroundColor Yellow
                Write-Host "    Old: $($change.Old)" -ForegroundColor Gray
                Write-Host "    New: $($change.New)" -ForegroundColor Gray
            }
        }
    }

    if (-not $Apply) {
        Write-Host "`n[DRY-RUN] Use -Apply to write changes." -ForegroundColor Cyan
        exit 0
    }
}

# Apply changes
if ($Apply) {
    # Ensure directory exists
    $targetDir = Split-Path -Parent $targetEnvPath
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }

    # Merge updates and additions
    $allNewVars = @{}
    foreach ($key in $updates.Keys) {
        $allNewVars[$key] = $updates[$key]
    }
    foreach ($key in $additions.Keys) {
        $allNewVars[$key] = $additions[$key]
    }

    Write-EnvFile -FilePath $targetEnvPath -ExistingEnv $existingEnv -NewVariables $allNewVars

    Write-Host "`n[OK] Configuration written to: $targetEnvPath" -ForegroundColor Green
    Write-Host "  Updated: $($updates.Count) keys" -ForegroundColor Gray
    Write-Host "  Added: $($additions.Count) keys" -ForegroundColor Gray
}

