"""End-to-end smoke test for the Aitotech stack.

1. /health/all must report every service up.
2. A test envelope must round-trip Nexus -> Routely (intent: chat).

Usage: python scripts/smoke.py [--base http://localhost:8080] [--key dev-key]
Exit code 0 = all green.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read())


def post(url: str, body: dict, headers: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8080")
    parser.add_argument("--key", default="dev-key")
    args = parser.parse_args()

    failures = 0

    print("[1/2] GET /health/all ...")
    try:
        health = get(f"{args.base}/health/all")
        for svc in health["services"]:
            mark = "OK " if svc["up"] else "DOWN"
            print(f"   [{mark}] {svc['service']} ({svc.get('latency_ms', '?')} ms)")
            if not svc["up"]:
                failures += 1
    except (urllib.error.URLError, OSError) as exc:
        print(f"   FAILED: cannot reach nexus: {exc}")
        return 1

    print("[2/2] POST /v1/route (intent=chat, Nexus -> Routely) ...")
    envelope = {
        "source": "sayra",
        "intent": "chat",
        "payload": {"message": "smoke test: reply with pong"},
        "user_id": "smoke-test",
    }
    try:
        result = post(f"{args.base}/v1/route", envelope, {"X-Nexus-Key": args.key})
        if result.get("ok"):
            print(f"   [OK ] round-trip via {result.get('service')} in {result.get('latency_ms')} ms")
        else:
            print(f"   [FAIL] {result.get('error')}")
            failures += 1
    except (urllib.error.URLError, OSError) as exc:
        print(f"   FAILED: {exc}")
        failures += 1

    print("\nRESULT:", "ALL GREEN" if failures == 0 else f"{failures} FAILURE(S)")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
