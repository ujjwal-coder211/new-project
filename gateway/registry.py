"""Loads contracts/service_registry.yaml and resolves env-driven URLs."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "contracts" / "service_registry.yaml"


@dataclass(frozen=True)
class Service:
    name: str
    base_url: str
    health_path: str
    auth: str  # "none" | "bearer"
    api_key: str | None

    @property
    def health_url(self) -> str:
        return self.base_url.rstrip("/") + self.health_path

    def auth_headers(self) -> dict[str, str]:
        if self.auth == "bearer" and self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return {}


@dataclass(frozen=True)
class Intent:
    name: str
    service: str
    path: str


class Registry:
    def __init__(self, services: dict[str, Service], intents: dict[str, Intent]):
        self.services = services
        self.intents = intents

    def service_for_intent(self, intent: str) -> tuple[Service, Intent] | None:
        route = self.intents.get(intent)
        if route is None:
            return None
        service = self.services.get(route.service)
        if service is None:
            return None
        return service, route


def load_registry(path: Path = REGISTRY_PATH) -> Registry:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    services: dict[str, Service] = {}
    for name, cfg in raw.get("services", {}).items():
        base_url = os.getenv(cfg["url_env"], cfg["default_url"])
        api_key = os.getenv(cfg["key_env"]) if cfg.get("key_env") else None
        services[name] = Service(
            name=name,
            base_url=base_url,
            health_path=cfg.get("health_path", "/health"),
            auth=cfg.get("auth", "none"),
            api_key=api_key,
        )

    intents: dict[str, Intent] = {}
    for name, cfg in raw.get("intents", {}).items():
        intents[name] = Intent(name=name, service=cfg["service"], path=cfg["path"])

    unknown = {i.service for i in intents.values()} - set(services)
    if unknown:
        raise ValueError(f"service_registry.yaml: intents reference unknown services: {unknown}")

    return Registry(services, intents)
