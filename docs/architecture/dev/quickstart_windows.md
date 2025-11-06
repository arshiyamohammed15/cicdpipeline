# Quick Start Guide (Windows)

This guide helps you get started with ZeroUI 2.0 development on Windows.

## Prerequisites

### Required Software

1. **Git** (2.30+)
   - Download: https://git-scm.com/download/win
   - Verify: `git --version`

2. **Node.js** (18.x or 20.x)
   - Download: https://nodejs.org/
   - Verify: `node --version` and `npm --version`

3. **Python** (3.11+)
   - Download: https://www.python.org/downloads/
   - Verify: `python --version`

4. **VS Code** (Latest)
   - Download: https://code.visualstudio.com/
   - Install recommended extensions

5. **PowerShell** (5.1+ or PowerShell 7+)
   - Usually pre-installed on Windows
   - Verify: `$PSVersionTable.PSVersion`

### Optional Software

- **Docker Desktop** (for containerized services)
- **WSL2** (Windows Subsystem for Linux) - Optional but recommended

## Initial Setup

### 1. Clone Repository

```powershell
# Clone repository
git clone https://github.com/your-org/ZeroUI2.0.git
cd ZeroUI2.0
```

### 2. Set Up Python Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

**Note**: If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Set Up Node.js Environment

```powershell
# Install dependencies for VS Code Extension
cd src/vscode-extension
npm install

# Install dependencies for Edge Agent
cd ../edge-agent
npm install
```

### 4. Set Up Environment Variables

```powershell
# Create .env file in project root
$env:ZU_ROOT = "$PWD\storage"
$env:ZU_ROOT | Out-File -FilePath .env -Encoding utf8
```

Or create `.env` file manually:
```
ZU_ROOT=D:\Projects\ZeroUI2.0\storage
```

## Development Workflow

### Running Tests

#### Python Tests

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run all tests
pytest

# Run specific test file
pytest tests/test_receipt_validator.py

# Run with coverage
pytest --cov=validator --cov-report=html
```

#### TypeScript Tests

```powershell
# VS Code Extension tests
cd src/vscode-extension
npm test

# Edge Agent tests
cd ../edge-agent
npm test
```

### Building

#### VS Code Extension

```powershell
cd src/vscode-extension
npm run build
```

#### Edge Agent

```powershell
cd src/edge-agent
npm run build
```

### Running Services

#### Cloud Services (Python)

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run specific service
cd src/cloud-services/client-services/mmm-engine
uvicorn main:app --reload --port 8000
```

#### Edge Agent

```powershell
cd src/edge-agent
npm run start
```

## Common Tasks

### Creating a New Module

```powershell
# 1. Create module directory
New-Item -ItemType Directory -Path "src/vscode-extension/modules/m21-new-module"

# 2. Create module files
# (Follow MODULE_IMPLEMENTATION_GUIDE.md)

# 3. Update module loader
# (Add to module-loader.ts)
```

### Running Linters

```powershell
# Python linting
.\venv\Scripts\Activate.ps1
pylint src/cloud-services/

# TypeScript linting
cd src/vscode-extension
npm run lint
```

### Formatting Code

```powershell
# Python formatting
.\venv\Scripts\Activate.ps1
black src/cloud-services/

# TypeScript formatting
cd src/vscode-extension
npm run format
```

## Troubleshooting

### Python Virtual Environment Issues

```powershell
# If activation fails, try:
.\venv\Scripts\python.exe -m pip install --upgrade pip

# Recreate virtual environment if corrupted
Remove-Item -Recurse -Force venv
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Node.js Module Issues

```powershell
# Clear node_modules and reinstall
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

### Path Issues

```powershell
# Check ZU_ROOT is set
$env:ZU_ROOT

# Set if not set
$env:ZU_ROOT = "$PWD\storage"
[System.Environment]::SetEnvironmentVariable('ZU_ROOT', "$PWD\storage", 'User')
```

### Permission Issues

```powershell
# If you get permission errors, run PowerShell as Administrator
# Or adjust execution policy:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## VS Code Setup

### Recommended Extensions

- **Python** (Microsoft)
- **TypeScript and JavaScript Language Features** (Microsoft)
- **ESLint** (Microsoft)
- **Prettier** (Prettier)
- **GitLens** (GitKraken)

### Workspace Settings

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/Scripts/python.exe",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode"
}
```

## Getting Help

- **Documentation**: Check `docs/` directory
- **Architecture**: See `docs/architecture/`
- **Issues**: Create GitHub issue
- **Slack**: Ask in #zeroui-dev channel

## Next Steps

1. Read `docs/architecture/MODULE_IMPLEMENTATION_GUIDE.md`
2. Review `docs/architecture/dev/standards.md`
3. Set up your development environment
4. Run tests to verify setup
5. Create your first feature branch

## Windows-Specific Notes

### Line Endings

Git should handle line endings automatically with `.gitattributes`, but if you encounter issues:

```powershell
# Configure Git for Windows
git config --global core.autocrlf true
```

### Path Length

Windows has a 260-character path limit. If you encounter issues:

```powershell
# Enable long paths in Git
git config --global core.longpaths true
```

### File Permissions

If you encounter permission issues:

```powershell
# Take ownership of directory
takeown /F "path\to\directory" /R /D Y
icacls "path\to\directory" /grant Administrators:F /T
```

