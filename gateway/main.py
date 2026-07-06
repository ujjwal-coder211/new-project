"""Aitotech Nexus gateway — app entrypoint.

Run: uvicorn gateway.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI

from gateway.logging_config import setup_logging
from gateway.registry import load_registry
from gateway.routes import health, route, status


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    setup_logging()
    app.state.registry = load_registry()
    app.state.http = httpx.AsyncClient()
    try:
        yield
    finally:
        await app.state.http.aclose()


app = FastAPI(
    title="Aitotech Nexus",
    description="Master orchestrator / control plane for the Aitotech ecosystem.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(route.router)
app.include_router(status.router)
