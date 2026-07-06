"""Shared HTTP plumbing for service adapters."""

from __future__ import annotations

import os
from typing import Any

import httpx

from gateway.registry import Service


def forward_timeout() -> float:
    return float(os.getenv("NEXUS_FORWARD_TIMEOUT", "30"))


async def post_json(
    client: httpx.AsyncClient,
    service: Service,
    path: str,
    payload: dict[str, Any],
    trace_id: str,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """POST JSON to a service and return the parsed body. Raises httpx errors."""
    headers = {"X-Trace-Id": trace_id, **service.auth_headers(), **(extra_headers or {})}
    resp = await client.post(
        service.base_url.rstrip("/") + path,
        json=payload,
        headers=headers,
        timeout=forward_timeout(),
    )
    resp.raise_for_status()
    try:
        body = resp.json()
    except ValueError:
        return {"raw": resp.text}
    return body if isinstance(body, dict) else {"data": body}
