# Bring the Nexus local stack up with one command.
# Usage: .\scripts\dev-up.ps1
#
# Starts: nexus, sayra, n8n, agents.
# Does NOT start Routely/Saas — set ROUTELY_URL in .env to your external deploy.

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "==> Syncing submodules..." -ForegroundColor Cyan
git submodule update --init --recursive

if (-not (Test-Path ".env")) {
    Write-Host "==> No .env found, copying .env.example (edit ROUTELY_URL for your Routely deploy)" -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

Write-Host "==> Building and starting the stack (Routely not included)..." -ForegroundColor Cyan
docker compose up --build -d

Write-Host "==> Stack is starting. Check status:" -ForegroundColor Green
Write-Host "    Nexus    http://localhost:8080/health/all"
Write-Host "    Sayra    http://localhost:7860"
Write-Host "    n8n      http://localhost:5678"
Write-Host "    Agents   http://localhost:8090"
Write-Host "    Routely  (external — see ROUTELY_URL in .env)"
Write-Host ""
Write-Host "Smoke test: python scripts\smoke.py"
