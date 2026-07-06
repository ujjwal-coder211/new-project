import pytest
from pydantic import ValidationError

from contracts.task_envelope import ResultEnvelope, Source, TaskEnvelope


def test_envelope_defaults():
    env = TaskEnvelope(source=Source.SAYRA, intent="chat")
    assert env.task_id
    assert env.trace_id
    assert env.tier == "free"
    assert env.payload == {}
    assert env.created_at is not None


def test_envelope_requires_intent():
    with pytest.raises(ValidationError):
        TaskEnvelope(source=Source.SAYRA, intent="")


def test_envelope_rejects_unknown_source():
    with pytest.raises(ValidationError):
        TaskEnvelope(source="alien", intent="chat")


def test_result_success_carries_ids():
    env = TaskEnvelope(source=Source.SAYRA, intent="chat")
    res = ResultEnvelope.success(env, "routely", {"answer": "hi"}, latency_ms=12)
    assert res.ok
    assert res.task_id == env.task_id
    assert res.trace_id == env.trace_id
    assert res.service == "routely"
    assert res.result == {"answer": "hi"}


def test_result_failure():
    env = TaskEnvelope(source=Source.N8N, intent="automation.run")
    res = ResultEnvelope.failure(env, "boom", service="n8n")
    assert not res.ok
    assert res.error == "boom"
