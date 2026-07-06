"""Standard message format for every inter-service call in the Aitotech ecosystem.

Every message that crosses a service boundary (Sayra -> Nexus -> Routely / n8n /
agents) is a TaskEnvelope. Responses are wrapped in a ResultEnvelope so callers
always get a uniform shape, even on failure.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Source(StrEnum):
    SAYRA = "sayra"
    ROUTELY = "routely"
    N8N = "n8n"
    AGENT = "agent"
    WEBSITE = "website"


def _now() -> datetime:
    return datetime.now(UTC)


def _uuid() -> str:
    return str(uuid.uuid4())


class TaskEnvelope(BaseModel):
    task_id: str = Field(default_factory=_uuid)
    source: Source
    intent: str = Field(min_length=1, description="Routing key, e.g. 'chat', 'automation.run'")
    payload: dict[str, Any] = Field(default_factory=dict)
    user_id: str | None = None
    tier: str = "free"
    trace_id: str = Field(default_factory=_uuid)
    created_at: datetime = Field(default_factory=_now)


class ResultEnvelope(BaseModel):
    task_id: str
    trace_id: str
    ok: bool
    service: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    latency_ms: int | None = None
    completed_at: datetime = Field(default_factory=_now)

    @classmethod
    def success(
        cls,
        envelope: TaskEnvelope,
        service: str,
        result: dict[str, Any],
        latency_ms: int | None = None,
    ) -> ResultEnvelope:
        return cls(
            task_id=envelope.task_id,
            trace_id=envelope.trace_id,
            ok=True,
            service=service,
            result=result,
            latency_ms=latency_ms,
        )

    @classmethod
    def failure(
        cls,
        envelope: TaskEnvelope,
        error: str,
        service: str | None = None,
    ) -> ResultEnvelope:
        return cls(
            task_id=envelope.task_id,
            trace_id=envelope.trace_id,
            ok=False,
            service=service,
            error=error,
        )
