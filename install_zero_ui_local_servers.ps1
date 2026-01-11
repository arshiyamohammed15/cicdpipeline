param(
  [string]$RootDrive = "D",
  [string]$RootFolder = "zero-ui-local-servers"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Join-Root([string]$Drive, [string]$Folder) {
  return (Join-Path -Path ($Drive + ":\") -ChildPath $Folder)
}

function Fail([string]$Msg) {
  Write-Host "ERROR: $Msg" -ForegroundColor Red
  exit 1
}

function Ensure-Dir([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
  }
}

function Get-RelPath([string]$Base, [string]$Full) {
  $b = $Base.TrimEnd('\')
  if (-not $Full.StartsWith($b, [System.StringComparison]::OrdinalIgnoreCase)) {
    return $null
  }
  $rel = $Full.Substring($b.Length).TrimStart('\')
  return $rel
}

function Get-BytesHash([byte[]]$Bytes) {
  $sha = [System.Security.Cryptography.SHA256]::Create()
  try {
    $h = $sha.ComputeHash($Bytes)
    return ([System.BitConverter]::ToString($h)).Replace("-", "").ToLowerInvariant()
  } finally {
    $sha.Dispose()
  }
}

# Expected structure from the attached zip (directories + files)
$ExpectedDirs = @(
  "IDE",
  "IDE\apps",
  "IDE\apps\edge-agent",
  "IDE\apps\edge-agent\src",
  "IDE\apps\edge-agent\tests",
  "IDE\apps\vscode-extension",
  "IDE\apps\vscode-extension\media",
  "IDE\apps\vscode-extension\out",
  "IDE\apps\vscode-extension\src",
  "IDE\apps\vscode-extension\tests",
  "IDE\configs",
  "IDE\data",
  "IDE\data\cache",
  "IDE\data\policy",
  "IDE\data\receipts",
  "IDE\data\state",
  "IDE\logs",
  "IDE\runbooks",
  "IDE\scripts",
  "Product",
  "Product\audit",
  "Product\configs",
  "Product\exports",
  "Product\features",
  "Product\integrations",
  "Product\logs",
  "Product\migrations",
  "Product\policy",
  "Product\receipts",
  "Product\runbooks",
  "Product\scripts",
  "Shared",
  "Shared\audit",
  "Shared\configs",
  "Shared\db",
  "Shared\db\backups",
  "Shared\db\migrations",
  "Shared\db\ops",
  "Shared\db\schemas",
  "Shared\db\seed",
  "Shared\evidence",
  "Shared\exports",
  "Shared\logs",
  "Shared\migrations",
  "Shared\observability",
  "Shared\policy",
  "Shared\receipts",
  "Shared\runbooks",
  "Shared\scripts",
  "Shared\security",
  "Tenant",
  "Tenant\audit",
  "Tenant\configs",
  "Tenant\exports",
  "Tenant\logs",
  "Tenant\migrations",
  "Tenant\policy",
  "Tenant\receipts",
  "Tenant\runbooks",
  "Tenant\scripts",
  "Tenant\security",
  "Tenant\tenants"
)
$ExpectedFiles = @(
  "Shared\db\README.md",
  "Shared\db\schemas\001_ide.sql",
  "Shared\db\schemas\001_product.sql",
  "Shared\db\schemas\001_shared.sql",
  "Shared\db\schemas\001_tenant.sql"
)
$ExpectedFileBytesB64 = @{
  "Shared\db\README.md" = "77u/IyBaZXJvVUkgTG9jYWwgLSBEYXRhYmFzZSBBcnRpZmFjdHMgKFBvc3RncmVTUUwpCgpUaGlzIGZvbGRlciBjb250YWlucyBzY2hlbWEgZGVmaW5pdGlvbnMgYW5kIG9wZXJhdGlvbmFsIHNjcmlwdHMgZm9yIHRoZSBzaW5nbGUgUG9zdGdyZVNRTCBkYXRhYmFzZSB1c2VkIGFjcm9zcyBhbGwgcGxhbmVzLgoKRW50ZXJwcmlzZSBsYXlvdXQ6Ci0gT25lIERCIChleGFtcGxlOiB6ZXJvdWkpCi0gRm91ciBzY2hlbWFzOiBpZGUsIHRlbmFudCwgcHJvZHVjdCwgc2hhcmVkCgpGb2xkZXJzOgotIHNjaGVtYXMvICAgICA6IGJhc2VsaW5lIERETCBwZXIgc2NoZW1hCi0gbWlncmF0aW9ucy8gIDogZm9yd2FyZC1vbmx5IG1pZ3JhdGlvbiBzY3JpcHRzIChleHBhbmQtPm1pZ3JhdGUtPmNvbnRyYWN0IHBhdHRlcm4gcmVjb21tZW5kZWQpCi0gb3BzLyAgICAgICAgIDogb3BlcmF0aW9uYWwgc2NyaXB0cyAoYXBwbHkvYmFja3VwKQotIGJhY2t1cHMvICAgICA6IGxvY2FsIGR1bXBzIChkbyBub3QgY29tbWl0KQ0K"
  "Shared\db\schemas\001_ide.sql" = "77u/LS0gU2NoZW1hOiBpZGUKQ1JFQVRFIFNDSEVNQSBJRiBOT1QgRVhJU1RTIGlkZTsKCkNSRUFURSBUQUJMRSBJRiBOT1QgRVhJU1RTIGlkZS5yZWNlaXB0cyAoCiAgcmVjZWlwdF9pZCAgICAgICAgICAgVEVYVCBQUklNQVJZIEtFWSwKICB0ZW5hbnRfaWQgICAgICAgICAgICBVVUlELAogIHJlcG9faWQgICAgICAgICAgICAgIFRFWFQgTk9UIE5VTEwsCiAgZ2F0ZV9pZCAgICAgICAgICAgICAgVEVYVCBOT1QgTlVMTCwKICBkZWNpc2lvbiAgICAgICAgICAgICBURVhUIE5PVCBOVUxMLAogIHJlYXNvbl9jb2RlcyAgICAgICAgIFRFWFRbXSBOT1QgTlVMTCBERUZBVUxUIEFSUkFZW106OlRFWFRbXSwKICBwb2xpY3lfc25hcHNob3RfaGFzaCBURVhULAogIHBvbGljeV92ZXJzaW9uX2lkcyAgIFRFWFRbXSBOT1QgTlVMTCBERUZBVUxUIEFSUkFZW106OlRFWFRbXSwKICBjcmVhdGVkX2F0ICAgICAgICAgICBUSU1FU1RBTVBUWiBOT1QgTlVMTCBERUZBVUxUIG5vdygpCik7CgpDUkVBVEUgSU5ERVggSUYgTk9UIEVYSVNUUyBpZGVfcmVjZWlwdHNfcmVwb19nYXRlX2lkeAogIE9OIGlkZS5yZWNlaXB0cyAocmVwb19pZCwgZ2F0ZV9pZCwgY3JlYXRlZF9hdCBERVNDKTsNCg=="
  "Shared\db\schemas\001_product.sql" = "77u/LS0gU2NoZW1hOiBwcm9kdWN0CkNSRUFURSBTQ0hFTUEgSUYgTk9UIEVYSVNUUyBwcm9kdWN0OwoKQ1JFQVRFIFRBQkxFIElGIE5PVCBFWElTVFMgcHJvZHVjdC5wb2xpY3lfc25hcHNob3RzICgKICBwb2xpY3lfc25hcHNob3RfaGFzaCBURVhUIFBSSU1BUlkgS0VZLAogIHBvbGljeV92ZXJzaW9uX2lkcyAgIFRFWFRbXSBOT1QgTlVMTCBERUZBVUxUIEFSUkFZW106OlRFWFRbXSwKICBwb2xpY3lfanNvbiAgICAgICAgICBKU09OQiBOT1QgTlVMTCwKICBjcmVhdGVkX2F0ICAgICAgICAgICBUSU1FU1RBTVBUWiBOT1QgTlVMTCBERUZBVUxUIG5vdygpCik7CgpDUkVBVEUgVEFCTEUgSUYgTk9UIEVYSVNUUyBwcm9kdWN0LnJlbGVhc2VzICgKICByZWxlYXNlX2lkICAgICAgICAgICBURVhUIFBSSU1BUlkgS0VZLAogIHRlbmFudF9pZCAgICAgICAgICAgIFVVSUQsCiAgcmVwb19pZCAgICAgICAgICAgICAgVEVYVCBOT1QgTlVMTCwKICB2ZXJzaW9uICAgICAgICAgICAgICBURVhULAogIGNyZWF0ZWRfYXQgICAgICAgICAgIFRJTUVTVEFNUFRaIE5PVCBOVUxMIERFRkFVTFQgbm93KCkKKTsKCkNSRUFURSBJTkRFWCBJRiBOT1QgRVhJU1RTIHByb2R1Y3RfcmVsZWFzZXNfcmVwb19pZHgKICBPTiBwcm9kdWN0LnJlbGVhc2VzIChyZXBvX2lkLCBjcmVhdGVkX2F0IERFU0MpOw0K"
  "Shared\db\schemas\001_shared.sql" = "77u/LS0gU2NoZW1hOiBzaGFyZWQKQ1JFQVRFIFNDSEVNQSBJRiBOT1QgRVhJU1RTIHNoYXJlZDsKCkNSRUFURSBUQUJMRSBJRiBOT1QgRVhJU1RTIHNoYXJlZC5hdWRpdF9sb2cgKAogIGF1ZGl0X2lkICAgICAgICAgICAgIEJJR1NFUklBTCBQUklNQVJZIEtFWSwKICB0ZW5hbnRfaWQgICAgICAgICAgICBVVUlELAogIHJlcG9faWQgICAgICAgICAgICAgIFRFWFQsCiAgYWN0b3JfaWQgICAgICAgICAgICAgVEVYVCwKICBhY3Rpb24gICAgICAgICAgICAgICBURVhUIE5PVCBOVUxMLAogIG9iamVjdF90eXBlICAgICAgICAgIFRFWFQsCiAgb2JqZWN0X2lkICAgICAgICAgICAgVEVYVCwKICByZWNlaXB0X2lkICAgICAgICAgICBURVhULAogIG1ldGFkYXRhICAgICAgICAgICAgIEpTT05CIE5PVCBOVUxMIERFRkFVTFQgJ3t9Jzo6SlNPTkIsCiAgY3JlYXRlZF9hdCAgICAgICAgICAgVElNRVNUQU1QVFogTk9UIE5VTEwgREVGQVVMVCBub3coKQopOwoKQ1JFQVRFIElOREVYIElGIE5PVCBFWElTVFMgc2hhcmVkX2F1ZGl0X2NyZWF0ZWRfaWR4CiAgT04gc2hhcmVkLmF1ZGl0X2xvZyAoY3JlYXRlZF9hdCBERVNDKTsKCkNSRUFURSBUQUJMRSBJRiBOT1QgRVhJU1RTIHNoYXJlZC5yZWNlaXB0c19pbmRleCAoCiAgcmVjZWlwdF9pZCAgICAgICAgICAgVEVYVCBQUklNQVJZIEtFWSwKICB0ZW5hbnRfaWQgICAgICAgICAgICBVVUlELAogIHJlcG9faWQgICAgICAgICAgICAgIFRFWFQsCiAgZ2F0ZV9pZCAgICAgICAgICAgICAgVEVYVCwKICBkZWNpc2lvbiAgICAgICAgICAgICBURVhULAogIHBvbGljeV9zbmFwc2hvdF9oYXNoIFRFWFQsCiAgY3JlYXRlZF9hdCAgICAgICAgICAgVElNRVNUQU1QVFogTk9UIE5VTEwgREVGQVVMVCBub3coKQopOw0K"
  "Shared\db\schemas\001_tenant.sql" = "77u/LS0gU2NoZW1hOiB0ZW5hbnQKQ1JFQVRFIFNDSEVNQSBJRiBOT1QgRVhJU1RTIHRlbmFudDsKCkNSRUFURSBUQUJMRSBJRiBOT1QgRVhJU1RTIHRlbmFudC50ZW5hbnRzICgKICB0ZW5hbnRfaWQgICAgICAgICAgICBVVUlEIFBSSU1BUlkgS0VZLAogIHRlbmFudF9uYW1lICAgICAgICAgIFRFWFQgTk9UIE5VTEwsCiAgc3RhdHVzICAgICAgICAgICAgICAgVEVYVCBOT1QgTlVMTCBERUZBVUxUICdhY3RpdmUnLAogIGNyZWF0ZWRfYXQgICAgICAgICAgIFRJTUVTVEFNUFRaIE5PVCBOVUxMIERFRkFVTFQgbm93KCkKKTsKCkNSRUFURSBUQUJMRSBJRiBOT1QgRVhJU1RTIHRlbmFudC5wb2xpY3lfc25hcHNob3RzICgKICBwb2xpY3lfc25hcHNob3RfaGFzaCBURVhUIFBSSU1BUlkgS0VZLAogIHBvbGljeV92ZXJzaW9uX2lkcyAgIFRFWFRbXSBOT1QgTlVMTCBERUZBVUxUIEFSUkFZW106OlRFWFRbXSwKICBwb2xpY3lfanNvbiAgICAgICAgICBKU09OQiBOT1QgTlVMTCwKICBjcmVhdGVkX2F0ICAgICAgICAgICBUSU1FU1RBTVBUWiBOT1QgTlVMTCBERUZBVUxUIG5vdygpCik7DQo="
}

$RootPath = Join-Root $RootDrive $RootFolder
Write-Host "Target root: $RootPath"

# --- STRICT VALIDATION OR FRESH INSTALL ---
if (Test-Path -LiteralPath $RootPath) {
  # Validate EXACT match: no missing, no extra, and file bytes must match zip
  Write-Host "Root already exists. Performing strict validation against the zip structure..."

  $expectedDirSet = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
  foreach ($d in $ExpectedDirs) { [void]$expectedDirSet.Add($d) }

  $expectedFileSet = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
  foreach ($f in $ExpectedFiles) { [void]$expectedFileSet.Add($f) }

  # Collect actual dirs/files relative to root
  $actualDirs = @()
  $actualFiles = @()

  foreach ($item in Get-ChildItem -LiteralPath $RootPath -Recurse -Force) {
    $rel = Get-RelPath $RootPath $item.FullName
    if ($null -eq $rel -or $rel -eq "") { continue }
    if ($item.PSIsContainer) {
      $actualDirs += $rel
    } else {
      $actualFiles += $rel
    }
  }

  # 1) Missing dirs
  $missingDirs = @()
  foreach ($d in $ExpectedDirs) {
    $full = Join-Path -Path $RootPath -ChildPath $d
    if (-not (Test-Path -LiteralPath $full)) { $missingDirs += $d }
  }

  # 2) Missing files
  $missingFiles = @()
  foreach ($f in $ExpectedFiles) {
    $full = Join-Path -Path $RootPath -ChildPath $f
    if (-not (Test-Path -LiteralPath $full)) { $missingFiles += $f }
  }

  # 3) Extra dirs/files (STRICT: anything not in expected is extra)
  $extraDirs = @()
  foreach ($d in $actualDirs) {
    if (-not $expectedDirSet.Contains($d)) { $extraDirs += $d }
  }

  $extraFiles = @()
  foreach ($f in $actualFiles) {
    if (-not $expectedFileSet.Contains($f)) { $extraFiles += $f }
  }

  # 4) File content mismatches
  $mismatchFiles = @()
  foreach ($f in $ExpectedFiles) {
    $full = Join-Path -Path $RootPath -ChildPath $f
    if (-not (Test-Path -LiteralPath $full)) { continue }

    $expectedB64 = $ExpectedFileBytesB64[$f]
    if ($null -eq $expectedB64) {
      $mismatchFiles += $f
      continue
    }

    $expectedBytes = [System.Convert]::FromBase64String($expectedB64)
    $actualBytes = [System.IO.File]::ReadAllBytes($full)

    if ((Get-BytesHash $expectedBytes) -ne (Get-BytesHash $actualBytes)) {
      $mismatchFiles += $f
    }
  }

  if ($missingDirs.Count -eq 0 -and $missingFiles.Count -eq 0 -and $extraDirs.Count -eq 0 -and $extraFiles.Count -eq 0 -and $mismatchFiles.Count -eq 0) {
    Write-Host "OK: Target root already matches the attached zip structure exactly."
    exit 0
  }

  Write-Host ""
  Write-Host "STRICT VALIDATION FAILED. Differences found:" -ForegroundColor Yellow

  if ($missingDirs.Count -gt 0) {
    Write-Host ""
    Write-Host "Missing directories:" -ForegroundColor Yellow
    $missingDirs | Sort-Object | ForEach-Object { Write-Host "  - $_" }
  }

  if ($missingFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "Missing files:" -ForegroundColor Yellow
    $missingFiles | Sort-Object | ForEach-Object { Write-Host "  - $_" }
  }

  if ($extraDirs.Count -gt 0) {
    Write-Host ""
    Write-Host "Extra directories (not in zip):" -ForegroundColor Yellow
    $extraDirs | Sort-Object | ForEach-Object { Write-Host "  - $_" }
  }

  if ($extraFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "Extra files (not in zip):" -ForegroundColor Yellow
    $extraFiles | Sort-Object | ForEach-Object { Write-Host "  - $_" }
  }

  if ($mismatchFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "Files with content mismatch vs zip:" -ForegroundColor Yellow
    $mismatchFiles | Sort-Object | ForEach-Object { Write-Host "  - $_" }
  }

  Write-Host ""
  Write-Host "To get a 100% exact structure, uninstall the target root and re-run install:" -ForegroundColor Yellow
  Write-Host "  powershell -ExecutionPolicy Bypass -File .\uninstall_zero_ui_local_servers.ps1 -RootDrive $RootDrive -RootFolder `"$RootFolder`" -Force" -ForegroundColor Yellow
  Fail "Install aborted to preserve strict accuracy."
}

# Fresh install: create exact structure
Write-Host "Creating exact folder/file structure from the attached zip..."

Ensure-Dir $RootPath

# Create directories (exact)
foreach ($d in $ExpectedDirs) {
  Ensure-Dir (Join-Path -Path $RootPath -ChildPath $d)
}

# Create files (exact bytes)
foreach ($f in $ExpectedFiles) {
  $full = Join-Path -Path $RootPath -ChildPath $f
  $parent = Split-Path -Path $full -Parent
  Ensure-Dir $parent

  $b64 = $ExpectedFileBytesB64[$f]
  if ($null -eq $b64) {
    Fail "Missing embedded bytes for file: $f"
  }

  $bytes = [System.Convert]::FromBase64String($b64)
  [System.IO.File]::WriteAllBytes($full, $bytes)
}

Write-Host "DONE: Installed exact structure at $RootPath"
