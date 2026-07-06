from gateway.registry import load_registry


def test_registry_loads_all_services():
    reg = load_registry()
    assert set(reg.services) == {"sayra", "routely", "n8n", "agents"}


def test_registry_intents_resolve():
    reg = load_registry()
    for intent in ("chat", "automation.run", "agent.task", "notify.user"):
        resolved = reg.service_for_intent(intent)
        assert resolved is not None, intent
        service, route = resolved
        assert service.base_url.startswith("http")
        assert route.path.startswith("/")


def test_unknown_intent_returns_none():
    reg = load_registry()
    assert reg.service_for_intent("does.not.exist") is None


def test_env_overrides_url(monkeypatch):
    monkeypatch.setenv("ROUTELY_URL", "http://example.com:9999")
    reg = load_registry()
    assert reg.services["routely"].base_url == "http://example.com:9999"


def test_bearer_auth_headers(monkeypatch):
    monkeypatch.setenv("ROUTELY_API_KEY", "sekret")
    reg = load_registry()
    assert reg.services["routely"].auth_headers() == {"Authorization": "Bearer sekret"}
    assert reg.services["sayra"].auth_headers() == {}
