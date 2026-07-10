# Bring the Nexus local stack up with one command.
# Usage: .\scripts\dev-up.ps1
#
# Starts: nexus, sayra, n8n.
# Does NOT start Routely/Saas or Aitotech-agents (outreach) —
# set ROUTELY_URL and AGENTS_URL in .env to your external deploys.

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "==> Syncing submodules..." -ForegroundColor Cyan
git submodule update --init --recursive

if (-not (Test-Path ".env")) {
    Write-Host "==> No .env found, copying .env.example (edit ROUTELY_URL / AGENTS_URL)" -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

Write-Host "==> Building and starting the stack (Routely + agents not included)..." -ForegroundColor Cyan
docker compose up --build -d

Write-Host "==> Stack is starting. Check status:" -ForegroundColor Green
Write-Host "    Nexus    http://localhost:8080/health/all"
Write-Host "    Sayra    http://localhost:7860"
Write-Host "    n8n      http://localhost:5678"
Write-Host "    Routely  (external — see ROUTELY_URL in .env)"
Write-Host "    Agents   (external outreach — see AGENTS_URL in .env)"
Write-Host ""
Write-Host "Smoke test: python scripts\smoke.py"
