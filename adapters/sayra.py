"""Sayra adapter — pushes notifications/callbacks to the voice/chat interface.

Used when an async task (n8n workflow, agent job) finishes and the user needs
to be told about it.
"""

from __future__ import annotations

from typing import Any

import httpx

from adapters.base import post_json
from contracts.task_envelope import TaskEnvelope
from gateway.registry import Service


async def notify_user(
    client: httpx.AsyncClient,
    service: Service,
    envelope: TaskEnvelope,
) -> dict[str, Any]:
    payload = {
        "user_id": envelope.user_id,
        "title": envelope.payload.get("title", "Task update"),
        "message": envelope.payload.get("message", ""),
        "task_id": envelope.payload.get("origin_task_id", envelope.task_id),
        "trace_id": envelope.trace_id,
    }
    return await post_json(client, service, "/v1/notify", payload, envelope.trace_id)
