"""GET /v1/status — public-safe status feed for the Aitotech website widget.

Exposes only up/down + latency per service. No URLs, no errors, no secrets.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, Request

from gateway.routes.health import check_service

router = APIRouter()


@router.get("/v1/status")
async def public_status(request: Request) -> dict:
    registry = request.app.state.registry
    client: httpx.AsyncClient = request.app.state.http
    results = await asyncio.gather(
        *(check_service(client, svc) for svc in registry.services.values())
    )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "overall": "operational" if all(r["up"] for r in results) else "degraded",
        "services": [
            {
                "name": r["service"],
                "up": r["up"],
                "latency_ms": r.get("latency_ms"),
            }
            for r in results
        ],
    }
