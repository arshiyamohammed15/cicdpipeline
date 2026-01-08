# Batched dependency installation to prevent pip resolver hang
# Installs dependencies in logical groups to avoid resolution-too-deep errors

$ErrorActionPreference = "Stop"
if ($PSScriptRoot) {
    $repoRoot = $PSScriptRoot
} else {
    $repoRoot = Get-Location
}
Set-Location $repoRoot

Write-Host "Installing dependencies in batches to prevent resolver hang..." -ForegroundColor Cyan
Write-Host ""

# Batch 1: Core dependencies (foundation)
Write-Host "[1/13] Installing core framework dependencies..." -ForegroundColor Yellow
python -m pip install --no-deps pydantic==2.12.3 PyYAML==6.0.3 jsonschema==4.25.1 GitPython==3.1.45 Jinja2==3.1.6 psutil==7.1.1
python -m pip install pydantic==2.12.3 PyYAML==6.0.3 jsonschema==4.25.1 GitPython==3.1.45 Jinja2==3.1.6 psutil==7.1.1

# Batch 2: Pydantic dependencies
Write-Host "[2/13] Installing pydantic dependencies..." -ForegroundColor Yellow
python -m pip install annotated-types==0.7.0 pydantic-core==2.41.4 pydantic-settings==2.12.0 typing-extensions==4.15.0

# Batch 3: Web framework
Write-Host "[3/13] Installing web framework..." -ForegroundColor Yellow
python -m pip install starlette==0.38.6
python -m pip install fastapi==0.115.0
python -m pip install "uvicorn[standard]==0.32.0"
python -m pip install Flask==2.3.3 Flask-Cors==4.0.0

# Batch 4: HTTP clients
Write-Host "[4/13] Installing HTTP clients..." -ForegroundColor Yellow
python -m pip install httpx==0.27.0 requests==2.31.0 aiohttp==3.13.2
python -m pip install certifi==2025.11.12 charset-normalizer==3.4.4 idna==3.11 urllib3==2.5.0
python -m pip install h11==0.16.0 httpcore==1.0.9 anyio==3.7.1 sniffio==1.3.1 yarl==1.22.0

# Batch 5: Database
Write-Host "[5/13] Installing database dependencies..." -ForegroundColor Yellow
python -m pip install SQLAlchemy==2.0.44 sqlmodel==0.0.27 alembic==1.13.1 psycopg2-binary==2.9.9
python -m pip install greenlet==3.3.0

# Batch 6: Security & Auth
Write-Host "[6/13] Installing security dependencies..." -ForegroundColor Yellow
python -m pip install PyJWT==2.8.0 cryptography==46.0.3 "python-jose[cryptography]==3.3.0"
python -m pip install cffi==2.0.0

# Batch 7: Observability
Write-Host "[7/13] Installing observability dependencies..." -ForegroundColor Yellow
python -m pip install opentelemetry-api==1.39.1 opentelemetry-sdk==1.39.1
python -m pip install opentelemetry-exporter-otlp==1.39.1
python -m pip install opentelemetry-instrumentation-fastapi==0.60b1 opentelemetry-instrumentation-asgi==0.60b1 opentelemetry-instrumentation==0.60b1
python -m pip install opentelemetry-util-http==0.60b1 opentelemetry-semantic-conventions==0.60b1
python -m pip install prometheus-client==0.23.1

# Batch 8: Data processing
Write-Host "[8/13] Installing data processing dependencies..." -ForegroundColor Yellow
python -m pip install orjson==3.9.10 python-dateutil==2.9.0.post0 pytz==2025.2
python -m pip install pandas==2.3.3 pyarrow==22.0.0 fastavro==1.9.0 protobuf==4.24.0
python -m pip install semantic-version==2.10.0 py-mini-racer==0.6.0

# Batch 9: Caching & Queues
Write-Host "[9/13] Installing caching and message queues..." -ForegroundColor Yellow
python -m pip install redis==5.0.1 hiredis==2.2.3 aiokafka==0.10.0 aio-pika==9.3.0

# Batch 10: LLM & Config
Write-Host "[10/13] Installing LLM and configuration..." -ForegroundColor Yellow
python -m pip install "openai[datalib]==1.3.0"
python -m pip install python-dotenv==1.2.1

# Batch 11: Testing
Write-Host "[11/13] Installing testing framework..." -ForegroundColor Yellow
python -m pip install pytest==8.4.2 pytest-asyncio==1.3.0 pytest-cov==7.0.0 pytest-xdist==3.8.0 pytest-mock==3.12.0
python -m pip install coverage==7.12.0 iniconfig==2.3.0 pluggy==1.6.0 attrs==25.4.0

# Batch 12: Development tools
Write-Host "[12/13] Installing development tools..." -ForegroundColor Yellow
python -m pip install black==25.9.0 ruff==0.14.1 mypy==1.18.2 pylint==4.0.4 flake8==7.3.0 pre-commit==4.3.0
python -m pip install "types-PyYAML==6.0.12.20250915" "types-requests==2.32.4.20250913"
python -m pip install mypy-extensions==1.1.0 pathspec==0.12.1 packaging==23.1 pyparsing==3.3.1

# Batch 13: Remaining dependencies
Write-Host "[13/13] Installing remaining dependencies..." -ForegroundColor Yellow
python -m pip install locust==2.17.0
python -m pip install click==8.3.1
python -m pip install jsonschema-specifications==2025.9.1 markdown-it-py==4.0.0 MarkupSafe==3.0.3
python -m pip install referencing==0.37.0 regex==2025.11.3 rpds-py==0.30.0 six==1.17.0 tenacity==9.1.2 tzdata==2025.3 Werkzeug==3.1.4

Write-Host ""
Write-Host "All dependencies installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Verifying installation..." -ForegroundColor Cyan
python -m pip check
