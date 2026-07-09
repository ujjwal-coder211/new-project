"""Routely adapter — sends chat turns to the external Omni brain.

Routely/Saas is a separate project (not vendored in Nexus). Nexus only calls
its HTTP API via ROUTELY_URL and passes thread_id through for Hermes memory.
"""

from __future__ import annotations

from typing import Any

import httpx

from adapters.base import post_json
from contracts.task_envelope import TaskEnvelope
from gateway.registry import Service


async def send_chat(
    client: httpx.AsyncClient,
    service: Service,
    envelope: TaskEnvelope,
) -> dict[str, Any]:
    payload = {
        "message": envelope.payload.get("message", ""),
        "thread_id": envelope.payload.get("thread_id"),
        "user_id": envelope.user_id,
        "tier": envelope.tier,
        "trace_id": envelope.trace_id,
    }
    return await post_json(client, service, "/chat", payload, envelope.trace_id)
