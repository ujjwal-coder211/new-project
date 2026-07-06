"""Routely (Saas repo) adapter — sends chat turns to the Omni brain.

Routely does its own model routing (Omni conductor); Nexus just forwards the
message and passes thread_id through so Hermes memory keeps continuity.
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
