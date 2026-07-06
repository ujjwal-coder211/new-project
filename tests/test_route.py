import pytest
from fastapi.testclient import TestClient

from gateway.main import app
from gateway.routes import route as route_module


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("NEXUS_API_KEY", "test-key")
    with TestClient(app) as c:
        yield c


AUTH = {"X-Nexus-Key": "test-key"}


def envelope(intent="chat", **kwargs):
    return {"source": "sayra", "intent": intent, "payload": {"message": "hi"}, **kwargs}


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_route_requires_auth(client):
    resp = client.post("/v1/route", json=envelope())
    assert resp.status_code == 401


def test_route_rejects_bad_key(client):
    resp = client.post("/v1/route", json=envelope(), headers={"X-Nexus-Key": "wrong"})
    assert resp.status_code == 401


def test_route_unknown_intent(client):
    resp = client.post("/v1/route", json=envelope(intent="nope"), headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is False
    assert "unknown intent" in body["error"]


def test_route_success_via_mocked_adapter(client, monkeypatch):
    async def fake_adapter(http, service, env):
        return {"reply": "pong", "thread_id": "t1"}

    monkeypatch.setitem(route_module.ADAPTERS, "routely", fake_adapter)
    resp = client.post("/v1/route", json=envelope(), headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["service"] == "routely"
    assert body["result"] == {"reply": "pong", "thread_id": "t1"}
    assert body["latency_ms"] is not None


def test_route_adapter_failure(client, monkeypatch):
    import httpx

    async def failing_adapter(http, service, env):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setitem(route_module.ADAPTERS, "routely", failing_adapter)
    resp = client.post("/v1/route", json=envelope(), headers=AUTH)
    body = resp.json()
    assert body["ok"] is False
    assert "ConnectError" in body["error"]


def test_status_is_public(client):
    # /v1/status needs no auth (website widget) — services will be down locally
    resp = client.get("/v1/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["overall"] in ("operational", "degraded")
    assert {s["name"] for s in body["services"]} == {"sayra", "routely", "n8n", "agents"}
    for svc in body["services"]:
        assert set(svc) == {"name", "up", "latency_ms"}  # no secrets/URLs leak
