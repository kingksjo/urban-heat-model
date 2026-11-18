"""CLI helper to poll GET /v1/status/{activity_id} and save sanitized result."""

from __future__ import annotations

import json
import sys

from src.client import FortyGuardClient, sanitize_payload, save_sanitized_json
from src.polling import poll_activity


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m src.poll_job <activity_id> [output_path]")

    activity_id = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    client = FortyGuardClient(timeout=60.0)
    # Inspect one raw status call first so nested status keys are visible
    first = client.get_status(activity_id)
    print(f"GET /v1/status/{activity_id} -> HTTP {first.status_code} ({first.latency_s}s)")
    if isinstance(first.body, (dict, list)):
        print(json.dumps(sanitize_payload(first.body), indent=2, ensure_ascii=False))
    else:
        print(first.body)

    # Check if still processing (top-level or under data)
    status_val = ""
    if isinstance(first.body, dict):
        data_obj = first.body.get("data") if isinstance(first.body.get("data"), dict) else {}
        raw_status = first.body.get("status") or data_obj.get("status") or ""
        status_val = str(raw_status).lower()

    final_body = first.body
    if status_val in {"processing", "pending", "queued", "in_progress"}:
        res = poll_activity(client, activity_id, interval_s=3.0, max_attempts=20)
        print(f"\nPolling done: {res.final_status} in {res.total_elapsed_s}s ({res.attempts} attempts)")
        print("Transitions:", res.transitions)
        if res.final_response is not None:
            final_body = res.final_response.body
            print(json.dumps(sanitize_payload(final_body), indent=2, ensure_ascii=False))

    if output_path and final_body is not None:
        save_sanitized_json(final_body, output_path)
        print(f"\nSaved to {output_path}")

    usage = client.fetch_api_key_usage()
    if isinstance(usage.body, dict):
        summary = usage.body.get("credit_summary", {})
        print(
            f"Credits remaining: {summary.get('cycle_remaining_credits')} "
            f"(used: {summary.get('cycle_credits_used')})"
        )


if __name__ == "__main__":
    main()
