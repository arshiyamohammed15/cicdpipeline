# Client Generation

Use `tools/generate_clients.ps1` to generate typed clients from the OpenAPI specs.

## Prerequisites
- `openapi-generator` CLI in PATH (install from https://openapi-generator.tech/ or via npm/homebrew/other package managers).
- PowerShell available (used in CI and locally).

## Usage
```pwsh
# Default generator (typescript-fetch) and output directory (./generated-clients)
./tools/generate_clients.ps1

# Custom generator/output
./tools/generate_clients.ps1 -Generator "python" -OutputDir "C:\tmp\clients"
```

Specs used:
- `docs/design/openapi_sin.yaml`
- `docs/design/openapi_validator.yaml`
