"""GET /health (self) and GET /health/all (fan-out to every registered service)."""

from __future__ import annotations

import asyncio
import os
import time

import httpx
from fastapi import APIRouter, Request

from gateway.registry import Service

router = APIRouter()


def _health_timeout() -> float:
    return float(os.getenv("NEXUS_HEALTH_TIMEOUT", "5"))


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "nexus"}


async def check_service(client: httpx.AsyncClient, service: Service) -> dict:
    start = time.monotonic()
    try:
        resp = await client.get(
            service.health_url,
            headers=service.auth_headers(),
            timeout=_health_timeout(),
        )
        latency_ms = int((time.monotonic() - start) * 1000)
        return {
            "service": service.name,
            "up": resp.status_code < 400,
            "status_code": resp.status_code,
            "latency_ms": latency_ms,
        }
    except httpx.HTTPError as exc:
        return {
            "service": service.name,
            "up": False,
            "error": f"{type(exc).__name__}: {exc}",
            "latency_ms": int((time.monotonic() - start) * 1000),
        }


@router.get("/health/all")
async def health_all(request: Request) -> dict:
    registry = request.app.state.registry
    client: httpx.AsyncClient = request.app.state.http
    results = await asyncio.gather(
        *(check_service(client, svc) for svc in registry.services.values())
    )
    return {
        "status": "ok" if all(r["up"] for r in results) else "degraded",
        "services": results,
    }
