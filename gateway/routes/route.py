"""POST /v1/route — validate a task envelope and forward it to the right service.

Routing (intent -> service) lives in contracts/service_registry.yaml. Each
service has an adapter that shapes the payload for that service's API.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Request

from adapters import agents as agents_adapter
from adapters import n8n as n8n_adapter
from adapters import routely as routely_adapter
from adapters import sayra as sayra_adapter
from contracts.task_envelope import ResultEnvelope, TaskEnvelope
from gateway.auth import require_nexus_key
from gateway.registry import Service

log = logging.getLogger("nexus.route")

router = APIRouter(dependencies=[Depends(require_nexus_key)])

MAX_ATTEMPTS = 2

Adapter = Callable[[httpx.AsyncClient, Service, TaskEnvelope], Awaitable[dict[str, Any]]]

ADAPTERS: dict[str, Adapter] = {
    "routely": routely_adapter.send_chat,
    "n8n": n8n_adapter.trigger_workflow,
    "agents": agents_adapter.submit_task,
    "sayra": sayra_adapter.notify_user,
}


@router.post("/v1/route", response_model=ResultEnvelope)
async def route_task(envelope: TaskEnvelope, request: Request) -> ResultEnvelope:
    registry = request.app.state.registry
    resolved = registry.service_for_intent(envelope.intent)
    if resolved is None:
        log.warning(
            "unknown intent",
            extra={"trace_id": envelope.trace_id, "task_id": envelope.task_id, "intent": envelope.intent},
        )
        return ResultEnvelope.failure(envelope, error=f"unknown intent: {envelope.intent}")

    service, _intent = resolved
    adapter = ADAPTERS.get(service.name)
    if adapter is None:
        return ResultEnvelope.failure(
            envelope, error=f"no adapter for service: {service.name}", service=service.name
        )

    client: httpx.AsyncClient = request.app.state.http
    last_error = "unknown error"
    start = time.monotonic()

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            body = await adapter(client, service, envelope)
            latency_ms = int((time.monotonic() - start) * 1000)
            log.info(
                "routed",
                extra={
                    "trace_id": envelope.trace_id,
                    "task_id": envelope.task_id,
                    "intent": envelope.intent,
                    "service": service.name,
                    "latency_ms": latency_ms,
                },
            )
            return ResultEnvelope.success(envelope, service.name, body, latency_ms=latency_ms)
        except httpx.HTTPStatusError as exc:
            last_error = f"{service.name} returned {exc.response.status_code}: {exc.response.text[:500]}"
            if exc.response.status_code < 500 or attempt == MAX_ATTEMPTS:
                break
        except httpx.HTTPError as exc:
            last_error = f"{type(exc).__name__}: {exc}"

    log.error(
        "forward failed",
        extra={
            "trace_id": envelope.trace_id,
            "task_id": envelope.task_id,
            "intent": envelope.intent,
            "service": service.name,
        },
    )
    return ResultEnvelope.failure(envelope, error=last_error, service=service.name)
