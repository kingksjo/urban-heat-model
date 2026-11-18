"""Zero-cost account and credit-balance check for FortyGuard API."""

from __future__ import annotations

import json

from src.client import FortyGuardClient, sanitize_payload, save_sanitized_json


def main() -> None:
    client = FortyGuardClient()
    resp = client.fetch_api_key_usage()
    print(f"Method/URL: {resp.method} {resp.url}")
    print(f"HTTP Status: {resp.status_code}")
    print(f"Latency: {resp.latency_s}s")
    print(f"Content-Type: {resp.content_type}")
    print("Response body:")
    if isinstance(resp.body, (dict, list)):
        sanitized = sanitize_payload(resp.body)
        print(json.dumps(sanitized, indent=2, ensure_ascii=False))
        save_sanitized_json(sanitized, "data/raw/account_usage.json")
    else:
        print(resp.body)


if __name__ == "__main__":
    main()
