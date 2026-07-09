"""End-to-end smoke test for the Aitotech Nexus stack.

1. /health must be ok (gateway self).
2. /health/all is reported (Routely may be DOWN if not running externally).
3. If Routely is up, a chat envelope round-trips Nexus -> Routely.

Usage: python scripts/smoke.py [--base http://localhost:8080] [--key dev-key]
Exit code 0 = gateway + local services healthy (Routely optional unless --require-routely).
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
    parser.add_argument(
        "--require-routely",
        action="store_true",
        help="Fail if Routely is down or chat round-trip fails",
    )
    args = parser.parse_args()

    failures = 0
    local_services = {"sayra", "n8n", "agents"}

    print("[1/3] GET /health ...")
    try:
        health = get(f"{args.base}/health")
        if health.get("status") != "ok":
            print(f"   [FAIL] unexpected: {health}")
            failures += 1
        else:
            print("   [OK ] nexus")
    except (urllib.error.URLError, OSError) as exc:
        print(f"   FAILED: cannot reach nexus: {exc}")
        return 1

    print("[2/3] GET /health/all ...")
    try:
        health = get(f"{args.base}/health/all")
        routely_up = False
        for svc in health["services"]:
            mark = "OK " if svc["up"] else "DOWN"
            print(f"   [{mark}] {svc['service']} ({svc.get('latency_ms', '?')} ms)")
            if svc["service"] == "routely":
                routely_up = bool(svc["up"])
                if args.require_routely and not svc["up"]:
                    failures += 1
            elif svc["service"] in local_services and not svc["up"]:
                failures += 1
    except (urllib.error.URLError, OSError) as exc:
        print(f"   FAILED: {exc}")
        return 1

    print("[3/3] POST /v1/route (intent=chat, Nexus -> Routely) ...")
    if not routely_up and not args.require_routely:
        print("   [SKIP] Routely down (external — set ROUTELY_URL or pass --require-routely)")
    else:
        envelope = {
            "source": "sayra",
            "intent": "chat",
            "payload": {"message": "smoke test: reply with pong"},
            "user_id": "smoke-test",
        }
        try:
            result = post(f"{args.base}/v1/route", envelope, {"X-Nexus-Key": args.key})
            if result.get("ok"):
                print(
                    f"   [OK ] round-trip via {result.get('service')} "
                    f"in {result.get('latency_ms')} ms"
                )
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
