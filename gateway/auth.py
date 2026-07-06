"""Shared-secret auth: X-Nexus-Key header must match NEXUS_API_KEY.

If NEXUS_API_KEY is unset, auth is disabled (local dev only).
"""

from __future__ import annotations

import hmac
import os

from fastapi import Header, HTTPException


async def require_nexus_key(x_nexus_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("NEXUS_API_KEY", "")
    if not expected:
        return
    if x_nexus_key is None or not hmac.compare_digest(x_nexus_key, expected):
        raise HTTPException(status_code=401, detail="invalid or missing X-Nexus-Key")
