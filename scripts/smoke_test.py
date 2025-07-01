"""VENDORA Post-Deployment Smoke Test
===================================
Run health and basic functional tests against a live VENDORA service.

Usage:
    python scripts/smoke_test.py --url https://staging-xyz.a.run.app

Exit status:
    0  – all checks passed
    1  – one or more checks failed
"""

import argparse
import json
import sys
import textwrap
from typing import Tuple

import requests

SAMPLE_QUERY_PAYLOAD = {
    "query": "What were my top selling vehicles last month?",
    "dealership_id": "demo_dealer_001",
    "context": {"user_role": "manager"},
}


def check_health(base_url: str) -> Tuple[bool, str]:
    try:
        resp = requests.get(f"{base_url}/health", timeout=10)
        if resp.status_code == 200:
            return True, "Health endpoint OK"
        return False, f"Health endpoint status {resp.status_code}"
    except Exception as exc:
        return False, f"Health check error: {exc}"


def check_query(base_url: str) -> Tuple[bool, str]:
    try:
        resp = requests.post(
            f"{base_url}/api/v1/query", json=SAMPLE_QUERY_PAYLOAD, timeout=30
        )
        if resp.status_code != 200:
            return False, f"/api/v1/query status {resp.status_code}"
        data = resp.json()
        missing = [k for k in ("analysis", "recommendations") if k not in data]
        if missing:
            return False, f"/api/v1/query response missing keys: {missing}"
        return True, "Query endpoint OK"
    except Exception as exc:
        return False, f"Query check error: {exc}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run health and functional smoke tests for VENDORA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """Examples:
            python scripts/smoke_test.py --url https://vendora-api-staging-uc.a.run.app
            """
        ),
    )
    parser.add_argument("--url", required=True, help="Base URL of the deployed service")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")

    results = []

    ok, msg = check_health(base_url)
    print(f"[health ] {'✅' if ok else '❌'} {msg}")
    results.append(ok)

    ok, msg = check_query(base_url)
    print(f"[query  ] {'✅' if ok else '❌'} {msg}")
    results.append(ok)

    if all(results):
        print("\n🎉 All smoke tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Smoke tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()