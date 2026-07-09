# Aitotech Nexus — Master Orchestrator

Nexus is the **control plane** for the Aitotech ecosystem. It contains no business
logic — only routing, contracts, health checks, auth, and the infrastructure to bring
the local stack up with one command.

```
Sayra (voice/chat)  ──►  Nexus Gateway  ──►  Routely (external brain — separate repo)
                              │
                              ├──►  ai-engine (n8n workflows)
                              ├──►  Aitotech-agents (Supabase)
                              └──►  Aitotech website (status feed)
```

**Routely / Saas is not vendored here.** It is a separate project. Nexus talks to it
only via `ROUTELY_URL` (and optional `ROUTELY_API_KEY`).

## What lives here

| Path | Purpose |
|---|---|
| `contracts/` | Task envelope schema + service registry (single source of truth) |
| `gateway/` | FastAPI app: `/v1/route`, `/health/all`, `/v1/status`, auth |
| `adapters/` | Connectors for Routely, n8n, Aitotech-agents, Sayra |
| `repos/` | Git submodules: Sayra, ai-engine, Aitotech-agents (local full-stack) |
| `scripts/` | `dev-up.ps1` (one-command stack) + `smoke.py` (round-trip test) |

## Quick start (gateway only)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # set ROUTELY_URL to your Routely deploy
uvicorn gateway.main:app --reload
```

Check: `http://localhost:8000/health`

## Quick start (local stack)

Brings up Nexus + Sayra + n8n + agents. Routely must already be running elsewhere
(or set `ROUTELY_URL` to its deploy URL).

```powershell
.\scripts\dev-up.ps1
python scripts\smoke.py
```

## API

- `POST /v1/route` — send a task envelope; Nexus forwards it to the right service
  based on the `intent -> service` mapping in `contracts/service_registry.yaml`.
  Requires header `X-Nexus-Key`.
- `GET /health` — gateway self health.
- `GET /health/all` — parallel fan-out health of every registered service.
- `GET /v1/status` — public-safe status feed (for the Aitotech website widget).

## Task envelope

Every inter-service message uses one standard format (see `contracts/task_envelope.py`):

```json
{
  "task_id": "uuid",
  "source": "sayra",
  "intent": "chat",
  "payload": {"message": "hello"},
  "user_id": "u_123",
  "tier": "free",
  "trace_id": "uuid",
  "created_at": "2026-07-05T00:00:00Z"
}
```

## Environment variables

See `.env.example`. Secrets are never committed — use env / Railway secrets only.
