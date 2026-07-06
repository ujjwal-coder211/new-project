"""ai-engine (n8n) adapter — triggers workflow webhooks.

Fire-and-forget: n8n gets the payload plus a callback URL it can POST results to
(/v1/route with intent notify.user) when the workflow completes.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from adapters.base import forward_timeout
from contracts.task_envelope import TaskEnvelope
from gateway.registry import Service


def webhook_base(service: Service) -> str:
    return os.getenv("N8N_WEBHOOK_BASE", service.base_url.rstrip("/") + "/webhook")


async def trigger_workflow(
    client: httpx.AsyncClient,
    service: Service,
    envelope: TaskEnvelope,
) -> dict[str, Any]:
    workflow = envelope.payload.get("workflow")
    if not workflow:
        return {"ok": False, "error": "payload.workflow (webhook slug) is required"}

    callback_url = envelope.payload.get("callback_url")
    body = {
        "task_id": envelope.task_id,
        "trace_id": envelope.trace_id,
        "user_id": envelope.user_id,
        "data": envelope.payload.get("data", {}),
        "callback_url": callback_url,
    }
    url = webhook_base(service).rstrip("/") + "/" + str(workflow).lstrip("/")
    resp = await client.post(
        url,
        json=body,
        headers={"X-Trace-Id": envelope.trace_id},
        timeout=forward_timeout(),
    )
    return {
        "ok": resp.status_code < 400,
        "status_code": resp.status_code,
        "workflow": workflow,
        "accepted": resp.status_code < 400,
    }
