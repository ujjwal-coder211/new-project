# Bring the whole Aitotech stack up with one command.
# Usage: .\scripts\dev-up.ps1

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "==> Syncing submodules..." -ForegroundColor Cyan
git submodule update --init --recursive

if (-not (Test-Path ".env")) {
    Write-Host "==> No .env found, copying .env.example (edit it for real keys)" -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

Write-Host "==> Building and starting the stack..." -ForegroundColor Cyan
docker compose up --build -d

Write-Host "==> Stack is starting. Check status:" -ForegroundColor Green
Write-Host "    Nexus    http://localhost:8080/health/all"
Write-Host "    Routely  http://localhost:8000/health"
Write-Host "    Sayra    http://localhost:7860"
Write-Host "    n8n      http://localhost:5678"
Write-Host "    Agents   http://localhost:8090"
Write-Host ""
Write-Host "Smoke test: python scripts\smoke.py"
