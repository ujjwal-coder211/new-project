"""Aitotech-agents adapter — submits business-agent tasks.

The agents service persists jobs in Supabase and returns a job id that callers
can poll or receive callbacks for.
"""

from __future__ import annotations

from typing import Any

import httpx

from adapters.base import post_json
from contracts.task_envelope import TaskEnvelope
from gateway.registry import Service


async def submit_task(
    client: httpx.AsyncClient,
    service: Service,
    envelope: TaskEnvelope,
) -> dict[str, Any]:
    payload = {
        "task_id": envelope.task_id,
        "trace_id": envelope.trace_id,
        "agent": envelope.payload.get("agent"),
        "input": envelope.payload.get("input", {}),
        "user_id": envelope.user_id,
        "tier": envelope.tier,
    }
    body = await post_json(client, service, "/v1/tasks", payload, envelope.trace_id)
    # Normalize the Supabase job id under a stable key
    if "job_id" not in body:
        for key in ("id", "jobId", "task_id"):
            if key in body:
                body["job_id"] = body[key]
                break
    return body
