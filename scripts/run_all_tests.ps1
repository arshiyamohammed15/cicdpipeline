Param(
    [int]$Workers = 4
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $repoRoot

function Invoke-Step {
    param(
        [string]$Name,
        [ScriptBlock]$Action
    )

    Write-Host "==> $Name" -ForegroundColor Cyan
    & $Action
    Write-Host "<== $Name`n" -ForegroundColor Green
}

function With-Location {
    param(
        [string]$Path,
        [ScriptBlock]$Action
    )

    Push-Location $Path
    try {
        & $Action
    } finally {
        Pop-Location
    }
}

function Resolve-PythonExe {
    $venvPy = Join-Path $repoRoot 'venv\Scripts\python.exe'
    if (Test-Path $venvPy) {
        return $venvPy
    }
    return 'python'
}

Invoke-Step "Install root JS deps" {
    npm ci
}

Invoke-Step "Build TypeScript" {
    npm run build:typescript
}

Invoke-Step "Run TypeScript tests (Jest)" {
    npx jest --config jest.config.js --maxWorkers=$Workers --silent
}

Invoke-Step "Run Python tests (pytest)" {
    & (Resolve-PythonExe) -m pytest -n $Workers
}

Invoke-Step "Install VS Code extension deps" {
    With-Location (Join-Path $repoRoot 'src\vscode-extension') {
        npm ci
    }
}

Invoke-Step "Compile VS Code extension" {
    With-Location (Join-Path $repoRoot 'src\vscode-extension') {
        npm run compile
    }
}

Invoke-Step "Run VS Code extension tests" {
    With-Location (Join-Path $repoRoot 'src\vscode-extension') {
        npm test
    }
}

