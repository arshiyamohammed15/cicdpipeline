
# Cursor Testing Constitution & Deterministic Test Framework
*Author: in the style of Martin Fowler — crisp, pragmatic, and systemically rigorous.*

> **Goal**: Eliminate non‑determinism and “test cache” behaviour when using AI code‑generation tools (e.g., Cursor). Provide a gold‑standard, repeatable framework so **creation → discovery → execution → validation** are consistent on every machine, every run.

---

## 1. Principles (Non‑Negotiable)

1. **Determinism over speed** — A slower test run that is reproducible is superior to a fast but flaky run.
2. **No test-result caching** — Disable or purge all framework caches before every run. Treat any cached test discovery or compiled output as a defect source.
3. **Hermetic runs** — Tests must not talk to the network, system clocks, global OS state, or previous runs.
4. **Idempotent fixtures** — A fixture must leave the world exactly as it found it.
5. **Single source of truth** — Each test declares its inputs; no “ambient” configuration.
6. **Independent order** — Any test can run alone or in any order and still pass.
7. **Auditable evidence** — Every run emits machine‑readable artefacts (jUnit XML, coverage, run manifest) for forensic debugging.
8. **Explicit seeds and time** — All randomness is seeded; time is frozen or explicitly controlled.
9. **Local‑first** — Works offline; CI is a faithful mirror, not an oracle.
10. **Human‑legible** — Failures must be actionable without spelunking the framework internals.

---

## 2. Directory & Naming Conventions

```
repo-root/
├─ src/                         # Production code (language-agnostic)
├─ tests/
│  ├─ unit/                     # Fast, isolated tests
│  ├─ component/                # Cross-module without external systems
│  ├─ integration/              # With real adapters, no third-party calls
│  ├─ fixtures/                 # Static test data (read-only)
│  └─ helpers/                  # Test utilities (pure, small)
├─ tools/
│  ├─ run-tests.ps1             # Deterministic PowerShell harness (Windows-first)
│  ├─ run-tests.sh              # Deterministic Bash harness (Unix)
│  └─ verify-artifacts.py       # Optional: validate jUnit/coverage/manifests
├─ .testframework/
│  └─ manifest.json             # What ran, with hashes & environment fingerprint
└─ package.json / pyproject.toml / etc.
```

**Discovery rules:**

- **Python (pytest):** files named `test_*.py` or `*_test.py` under `tests/**`.
- **TypeScript/JavaScript (Vitest/Jest/Mocha):** `*.test.(ts|js)` or `*.spec.(ts|js)` under `tests/**`.
- **VS Code extension tests:** live under `tests/extension/**` with Electron/Node harness.

---

## 3. “No Cache” Policy (Enforced)

Before every run, the harness **deletes** the following (if present):

- Python: `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`
- Node: `node_modules/.cache/`, `node_modules/.vite/`, `node_modules/.vitest/`, `coverage/`
- Tooling: `.cache/`, `.nyc_output/`, `dist/`, `out/`
- Custom: anything under `tmp/test-*`

Framework flags to **disable caching**:

- **pytest**: run with `PYTHONDONTWRITEBYTECODE=1` and `-c` pointing to a minimal config if needed.
- **Jest**: `--no-cache --ci --runInBand`
- **Vitest**: `--no-threads --watch=false --update=false` (Vitest doesn’t persist result caches by default; the harness still wipes `.vitest` and Vite cache).
- **Mocha**: no cache by default; ensure transpilation artefacts are cleaned.

---

## 4. Deterministic Test Harness (Windows‑first)

### 4.1 PowerShell (tools/run-tests.ps1)

```powershell
<# 
  Deterministic test runner.
  - Purges all caches
  - Sets env to hermetic defaults
  - Pins seeds & time behaviour via env
  - Executes Python + Node test stacks (if present)
  - Emits jUnit + coverage + run manifest
#>
[CmdletBinding()]
param(
  [switch]$PythonOnly,
  [switch]$NodeOnly,
  [string]$ReportDir = ".testframework"
)

$ErrorActionPreference = "Stop"
$PSStyle.OutputRendering = "Ansi"

function Remove-IfExists([string]$path) {
  if (Test-Path $path) { 
    Write-Host "🧹 Removing $path"
    Remove-Item -Recurse -Force $path 
  }
}

Write-Host "== Deterministic Test Run =="

# 1) Clean caches (idempotent)
$pathsToClean = @(
  ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache",
  "node_modules/.cache", "node_modules/.vite", "node_modules/.vitest",
  ".nyc_output", "coverage", ".cache", "dist", "out", "tmp/test-*"
)
foreach ($p in $pathsToClean) { Get-ChildItem -Path . -Recurse -Force -ErrorAction SilentlyContinue -Filter $p | ForEach-Object { Remove-IfExists $_.FullName } }

# 2) Hermetic env
$env:CI = "1"
$env:FORCE_COLOR = "0"
$env:NO_COLOR = "1"
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTHONHASHSEED = "0"
$env:TEST_RANDOM_SEED = "12345"
$env:TZ = "UTC"

# 3) Prepare reports
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$timestamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
$manifestPath = Join-Path $ReportDir "manifest-$timestamp.json"
$junitPython = Join-Path $ReportDir "junit-python.xml"
$junitNode   = Join-Path $ReportDir "junit-node.xml"

# 4) Python
if (-not $NodeOnly) {
  if (Test-Path "pyproject.toml" -or (Get-ChildItem -Recurse -Filter "test_*.py","*_test.py" | Measure-Object).Count -gt 0) {
    Write-Host "🐍 Running Python tests (pytest)"
    $pytest = "pytest -q --disable-warnings --maxfail=1 --cache-clear --junitxml `"$junitPython`" tests"
    # Note: --cache-clear clears .pytest_cache; our pre-wipe already removed it.
    & pwsh -NoProfile -Command $pytest
  } else {
    Write-Host "🐍 Skipping Python (no tests detected)"
  }
}

# 5) Node (Vitest/Jest/Mocha)
if (-not $PythonOnly) {
  if (Test-Path "package.json") {
    Write-Host "🟩 Running Node tests"
    # Prefer Vitest if present, else Jest, else Mocha
    $hasVitest = (Get-Content package.json) -match '"vitest"'
    $hasJest   = (Get-Content package.json) -match '"jest"'
    if ($hasVitest) {
      $cmd = "npx vitest run --no-threads --watch=false --update=false --reporter=junit --outputFile=`"$junitNode`""
    } elseif ($hasJest) {
      $cmd = "npx jest --ci --runInBand --no-cache --reporters=default --reporters=jest-junit"
      $env:JEST_JUNIT_OUTPUT = $junitNode
    } else {
      $cmd = "npx mocha --recursive 'tests/**/*.test.{ts,js}' --reporter spec"
      # For Mocha, a JUnit reporter can be configured in package.json if required
    }
    & pwsh -NoProfile -Command $cmd
  } else {
    Write-Host "🟩 Skipping Node (no package.json)"
  }
}

# 6) Create run manifest
$manifest = @{
  timestamp    = $timestamp
  hostname     = $env:COMPUTERNAME
  os           = (Get-CimInstance Win32_OperatingSystem).Caption
  python       = (python --version) 2>$null
  node         = (node --version) 2>$null
  seeds        = @{ TEST_RANDOM_SEED = $env:TEST_RANDOM_SEED; PYTHONHASHSEED = $env:PYTHONHASHSEED }
  timezone     = $env:TZ
  reports      = @{ junit_python = $junitPython; junit_node = $junitNode }
  cache_policy = "purged-before-run"
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $manifestPath

Write-Host "✅ Done. Manifest: $manifestPath"
```

### 4.2 Bash (tools/run-tests.sh)

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "== Deterministic Test Run =="

# 1) Clean caches
paths=(
  ".pytest_cache" "__pycache__" ".mypy_cache" ".ruff_cache"
  "node_modules/.cache" "node_modules/.vite" "node_modules/.vitest"
  ".nyc_output" "coverage" ".cache" "dist" "out" "tmp/test-*"
)
for p in "${paths[@]}"; do
  find . -name "$p" -prune -exec rm -rf {} + 2>/dev/null || true
done

# 2) Hermetic env
export CI=1
export FORCE_COLOR=0
export NO_COLOR=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONHASHSEED=0
export TEST_RANDOM_SEED=12345
export TZ=UTC

# 3) Reports
report_dir=".testframework"
mkdir -p "$report_dir"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
manifest_path="$report_dir/manifest-$timestamp.json"
junit_python="$report_dir/junit-python.xml"
junit_node="$report_dir/junit-node.xml"

# 4) Python
if ls tests/**/*_test.py tests/**/test_*.py >/dev/null 2>&1 || [ -f "pyproject.toml" ]; then
  echo "🐍 Running Python tests (pytest)"
  pytest -q --disable-warnings --maxfail=1 --cache-clear --junitxml "$junit_python" tests || exit 1
else
  echo "🐍 Skipping Python (no tests detected)"
fi

# 5) Node
if [ -f "package.json" ]; then
  echo "🟩 Running Node tests"
  if grep -q '"vitest"' package.json; then
    npx vitest run --no-threads --watch=false --update=false --reporter=junit --outputFile="$junit_node"
  elif grep -q '"jest"' package.json; then
    JEST_JUNIT_OUTPUT="$junit_node" npx jest --ci --runInBand --no-cache --reporters=default --reporters=jest-junit
  else
    npx mocha --recursive 'tests/**/*.test.{ts,js}' --reporter spec
  fi
else
  echo "🟩 Skipping Node (no package.json)"
fi

# 6) Manifest
python - <<PY > "$manifest_path"
import json, os, platform, subprocess
def v(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True).strip()
    except Exception:
        return None

manifest = {
  "timestamp": "$timestamp",
  "hostname": platform.node(),
  "os": platform.platform(),
  "python": v("python --version"),
  "node": v("node --version"),
  "seeds": {"TEST_RANDOM_SEED": os.getenv("TEST_RANDOM_SEED"), "PYTHONHASHSEED": os.getenv("PYTHONHASHSEED")},
  "timezone": os.getenv("TZ"),
  "reports": {"junit_python": "$junit_python", "junit_node": "$junit_node"},
  "cache_policy": "purged-before-run"
}
print(json.dumps(manifest, indent=2))
PY

echo "✅ Done. Manifest: $manifest_path"
```

---

## 5. Test Taxonomy & Rules

### 5.1 Unit tests
- Pure functions; no I/O, no network, no time.
- Use **table‑driven tests** for clarity.
- 1 behaviour ⇒ 1 assertion group; avoid over‑asserting.

### 5.2 Component tests
- Multiple modules interacting with in‑memory doubles only.
- No file system writes except under `tmp/test-*` managed by the harness.

### 5.3 Integration tests
- Real adapters (e.g., real parser, real DB driver) with **in‑process** instances or test containers, **never** shared across tests.
- No calls to the public Internet.

### 5.4 End‑to‑end (optional)
- Run as a separate job; never block the unit/component cadence.
- Still hermetic: ephemeral environment spun up for the run, then destroyed.

---

## 6. Time & Randomness Control

- **Random seeds:** All test pseudo‑randomness must use `TEST_RANDOM_SEED`.
- **Time:** Freeze time via a helper (e.g., `with frozen_time("2025-01-01T00:00:00Z")`); never depend on wall‑clock.
- **Retry‑free:** Flaky tests are bugs; do not mask with retries.

Example Python helper (`tests/helpers/time.py`):

```python
from contextlib import contextmanager
from datetime import datetime, timezone

@contextmanager
def frozen_time(iso_utc: str):
    class _Frozen(datetime):
        @classmethod
        def utcnow(cls):
            return datetime.fromisoformat(iso_utc.replace("Z","+00:00")).astimezone(timezone.utc)
    import builtins
    import datetime as _dt
    orig = _dt.datetime
    _dt.datetime = _Frozen
    try:
        yield
    finally:
        _dt.datetime = orig
```

---

## 7. Data & Fixtures

- Fixtures reside under `tests/fixtures/` and are **read‑only**.
- Synthetic data beats real data; if real, scrubbed and minimal.
- Large fixtures are hashed; the manifest records their SHA‑256.

---

## 8. Reporting & Evidence

Each run emits:

- **jUnit XML** per stack
- **Coverage** (language‑specific) — optional but encouraged
- **Run manifest** (`.testframework/manifest-*.json`) including seeds, versions, and hashes

Use `tools/verify-artifacts.py` (optional) to validate presence and schema of outputs.

---

## 9. Constitution for Cursor‑Generated Tests (Copy into Your Prompts)

> **Cursor Constitution — Testing Rules (Strict)**  
> Paste the following at the top of any AI generation prompt that involves tests.

1. **No caching**: Do not rely on or mention any test cache. Assume the harness **purges** caches before each run. Do not generate code that reads previous results.
2. **Deterministic by design**: Use `TEST_RANDOM_SEED` if randomness is needed; otherwise avoid randomness entirely.
3. **Hermetic tests only**: No network calls, no wall‑clock, no global OS state; file I/O only in `tmp/test-*` subfolders.
4. **Explicit discovery**: Place tests under `tests/{unit|component|integration}` using `*_test.py` or `*.test.ts` conventions.
5. **Pure helpers**: Put any reusable test utilities in `tests/helpers/`; they must have no side effects.
6. **Minimal dependencies**: Prefer standard libraries. If a third‑party library is required, justify within the code comments.
7. **One behaviour per test**: Keep tests small, table‑driven where useful, with clear Arrange‑Act‑Assert sections.
8. **No TODOs**: Provide complete, runnable tests. No placeholders, stubs without assertions, or commented‑out sections.
9. **Actionable failures**: Failure messages must state the expected vs actual and the scenario parameters.
10. **Runner compliance**: Tests must run under the provided `tools/run-tests.ps1|.sh` without modifying the harness.

---

## 10. Runners & Config Examples

### 10.1 Python (pytest)

`pyproject.toml` (excerpt):

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
addopts = "-q --disable-warnings --maxfail=1 --cache-clear"
```

Run via harness: `pwsh ./tools/run-tests.ps1 -PythonOnly`

### 10.2 Node (Vitest)

`package.json` (excerpt):

```json
{
  "scripts": {
    "test": "vitest run --no-threads --watch=false --update=false",
    "test:ci": "vitest run --no-threads --watch=false --update=false --reporter=junit"
  },
  "devDependencies": {
    "vitest": "^2.0.0"
  }
}
```

### 10.3 Node (Jest)

```json
{
  "scripts": {
    "test": "jest --runInBand --no-cache",
    "test:ci": "jest --ci --runInBand --no-cache --reporters=default --reporters=jest-junit"
  },
  "devDependencies": {
    "jest": "^29.0.0",
    "jest-junit": "^16.0.0"
  }
}
```

### 10.4 Mocha (for VS Code extension tests)

```json
{
  "scripts": {
    "test": "mocha --recursive "tests/**/*.test.{ts,js}" --reporter spec"
  },
  "devDependencies": {
    "mocha": "^10.0.0"
  }
}
```

---

## 11. Quality Gates

A run is **green** only if:

- All tests pass.
- No network access was attempted (enforced via global stub if applicable).
- jUnit XML + manifest exist and are well‑formed.
- Cache directories are absent post‑run.
- (Optional) Coverage ≥ threshold appropriate for the test layer.

---

## 12. Reviewer Checklist (Keep With Every PR)

- [ ] Tests are deterministic, small, and hermetic.
- [ ] No TODOs / placeholders.
- [ ] Seeds and time are explicit where needed.
- [ ] Tests live under the correct layer (unit/component/integration).
- [ ] Harness scripts are used; no ad‑hoc runners.
- [ ] Reports and manifest present.
- [ ] No evidence of cached results or order reliance.

---

## 13. Why This Works

Flakiness arises when the test environment remembers the past (caches) or consults the outside world (clocks, networks, previous artefacts). The harness **resets** the memory, **pins** the sources of variability (randomness, time), and **records** what happened. That is how you move from “works on my machine” to **“works every time.”**

---

## 14. Quickstart

- Windows: `pwsh ./tools/run-tests.ps1`
- Unix: `bash ./tools/run-tests.sh`

Commit the harness scripts, the folder structure, and this Constitution. Enforce via CI and pre‑merge gates.
