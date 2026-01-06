# CI Guard: Forbid Direct Ollama Usage in Functional Modules
# ID: CI.NO-DIRECT-OLLAMA.FM.GUARD.MT-01
# Purpose: Enforce that Functional Modules call plane-local LLM Router contract only

param(
    [string]$RepoRoot = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# File extensions to scan
$fileExtensions = @(
    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".kt", ".cs", ".rs", 
    ".php", ".rb", ".sh", ".ps1", ".yaml", ".yml", ".json"
)

# Blocklist patterns (case-insensitive)
$blocklistPatterns = @(
    "ollama",
    "http://localhost:11434",
    "11434/api",
    "/api/generate",
    "/api/chat",
    "OLLAMA_HOST",
    "OLLAMA_BASE_URL",
    "qwen2.5-coder",
    "tinyllama",
    "llama3"
)

# Allowlist path patterns (case-insensitive)
$allowlistPatterns = @(
    "/llm_router/",
    "/llm/",
    "/model_router/",
    "/adapters/llm/",
    "/docs/",
    "/scripts/",
    "/tests/",
    "/test/",
    "/__tests__/",
    "llm_gateway",
    "ollama-ai-agent"
)

# Candidate FM root paths (check which exist)
$candidateFmRoots = @(
    "src/vscode-extension/modules",
    "src/cloud_services/client-services",
    "src/cloud_services/product_services"
)

# Normalize repo root path
if ([string]::IsNullOrEmpty($RepoRoot)) {
    $RepoRoot = (Get-Location).Path
}
if (-not (Test-Path -Path $RepoRoot)) {
    # Try to find repo root by looking for .git or known root files
    $currentDir = Get-Location
    $searchPath = $currentDir
    while ($searchPath -and $searchPath -ne $searchPath.Parent) {
        if (Test-Path (Join-Path $searchPath ".git") -PathType Container) {
            $RepoRoot = $searchPath.Path
            break
        }
        if (Test-Path (Join-Path $searchPath "AGENTS.md")) {
            $RepoRoot = $searchPath.Path
            break
        }
        $searchPath = $searchPath.Parent
    }
    if (-not $RepoRoot) {
        $RepoRoot = $currentDir.Path
    }
}
$RepoRoot = (Resolve-Path -Path $RepoRoot -ErrorAction Stop).Path

Write-Host "Scanning for Functional Module roots in: $RepoRoot" -ForegroundColor Cyan

# Find existing FM roots
$fmRoots = @()
foreach ($candidate in $candidateFmRoots) {
    $fullPath = Join-Path $RepoRoot $candidate
    if (Test-Path -Path $fullPath -PathType Container) {
        $fmRoots += $fullPath
        Write-Host "  Found FM root: $candidate" -ForegroundColor Green
    }
}

if ($fmRoots.Count -eq 0) {
    Write-Host "No FM roots detected; skipping." -ForegroundColor Yellow
    exit 0
}

# Collect violations
$violations = @()

foreach ($fmRoot in $fmRoots) {
    Write-Host "`nScanning FM root: $fmRoot" -ForegroundColor Cyan
    
    # Get all files matching extensions
    $files = Get-ChildItem -Path $fmRoot -Recurse -File | 
        Where-Object { $fileExtensions -contains $_.Extension }
    
    foreach ($file in $files) {
        $relativePath = $file.FullName.Replace($RepoRoot, "").TrimStart("\", "/")
        $normalizedPath = $relativePath.Replace("\", "/")
        
        # Check if path matches allowlist
        $isAllowed = $false
        foreach ($allowPattern in $allowlistPatterns) {
            if ($normalizedPath -like "*$allowPattern*") {
                $isAllowed = $true
                break
            }
        }
        
        if ($isAllowed) {
            continue
        }
        
        # Read file content and check for blocklist patterns
        try {
            $content = Get-Content -Path $file.FullName -Raw -ErrorAction Stop
            $lines = Get-Content -Path $file.FullName -ErrorAction Stop
            
            foreach ($pattern in $blocklistPatterns) {
                $patternMatches = [regex]::Matches($content, $pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
                
                if ($patternMatches.Count -gt 0) {
                    foreach ($match in $patternMatches) {
                        # Find line number
                        $lineNumber = 1
                        $charIndex = 0
                        foreach ($line in $lines) {
                            $lineStart = $charIndex
                            $lineEnd = $charIndex + $line.Length
                            if ($match.Index -ge $lineStart -and $match.Index -lt $lineEnd) {
                                break
                            }
                            $charIndex = $lineEnd + 1  # +1 for newline
                            $lineNumber++
                        }
                        
                        # Extract context (line content, max 100 chars)
                        $lineContent = if ($lineNumber -le $lines.Count) {
                            $lines[$lineNumber - 1].Trim()
                        } else {
                            ""
                        }
                        if ($lineContent.Length -gt 100) {
                            $lineContent = $lineContent.Substring(0, 97) + "..."
                        }
                        
                        $violations += [PSCustomObject]@{
                            File = $relativePath
                            Line = $lineNumber
                            Pattern = $pattern
                            Context = $lineContent
                        }
                    }
                }
            }
        }
        catch {
            # Skip files that can't be read (binary, permissions, etc.)
            Write-Host "  Warning: Could not read $relativePath - $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

# Report results
Write-Host "`n" + ("=" * 80) -ForegroundColor Cyan
if ($violations.Count -gt 0) {
    Write-Host "VIOLATIONS DETECTED: Direct Ollama usage in Functional Module code" -ForegroundColor Red
    Write-Host "=" * 80 -ForegroundColor Red
    Write-Host ""
    Write-Host "Functional Modules must call the plane-local LLM Router contract only." -ForegroundColor Yellow
    Write-Host "Direct Ollama calls are forbidden. Use the LLM Router instead." -ForegroundColor Yellow
    Write-Host ""
    
    # Group by file for cleaner output
    $grouped = $violations | Group-Object -Property File
    
    foreach ($group in $grouped) {
        Write-Host "File: $($group.Name)" -ForegroundColor Red
        foreach ($violation in $group.Group) {
            Write-Host "  Line $($violation.Line): Pattern '$($violation.Pattern)'" -ForegroundColor Yellow
            if ($violation.Context) {
                Write-Host "    Context: $($violation.Context)" -ForegroundColor Gray
            }
        }
        Write-Host ""
    }
    
    Write-Host "Total violations: $($violations.Count)" -ForegroundColor Red
    exit 1
}
else {
    Write-Host "OK: No direct Ollama usage in FM code" -ForegroundColor Green
    Write-Host "=" * 80 -ForegroundColor Green
    exit 0
}

