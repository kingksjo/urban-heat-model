"""Shared REST smoke-test runner for sync and async FortyGuard endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.client import FortyGuardClient, sanitize_payload, save_sanitized_json
from src.polling import poll_activity


def run_smoke_post(
    path: str,
    payload: dict[str, Any],
    output_path: str | Path,
    *,
    label: str | None = None,
    poll_interval_s: float = 5.0,
    max_attempts: int = 36,
    print_submit_body: bool = True,
    print_full_result: bool = False,
) -> dict[str, Any]:
    """Submit a POST request (no retries), poll if async, save sanitized output, and check credits."""
    client = FortyGuardClient(timeout=60.0)
    header = label or f"POST {path}"
    print(f"Submitting {header}...")
    resp = client.request("POST", path, json_body=payload, retries=0)
    print(f"POST {path} -> HTTP {resp.status_code} ({resp.latency_s}s) [{resp.content_type}]")

    output: dict[str, Any] = {
        "request": payload,
        "submit_status": resp.status_code,
        "submit_latency_s": resp.latency_s,
        "submit_body": sanitize_payload(resp.body),
    }

    if isinstance(resp.body, dict):
        if print_submit_body:
            print(json.dumps(sanitize_payload(resp.body), indent=2, ensure_ascii=False))
        else:
            print("Submit body keys:", list(resp.body.keys()))
        data_obj = resp.body.get("data") if isinstance(resp.body.get("data"), dict) else {}
        activity_id = resp.body.get("activity_id") or data_obj.get("activity_id")
        status = str(resp.body.get("status") or data_obj.get("status") or "").lower()
        if activity_id and status in {"", "processing", "pending", "queued", "in_progress"}:
            print(f"\nPolling activity_id={activity_id}...")
            poll_res = poll_activity(
                client,
                str(activity_id),
                interval_s=poll_interval_s,
                max_attempts=max_attempts,
            )
            print(
                f"Polling finished: status={poll_res.final_status}, "
                f"attempts={poll_res.attempts}, elapsed={poll_res.total_elapsed_s}s"
            )
            print("Transitions:", poll_res.transitions)
            final_body = poll_res.final_response.body if poll_res.final_response else None
            sanitized_final = sanitize_payload(final_body)
            output["poll"] = {
                "activity_id": poll_res.activity_id,
                "final_status": poll_res.final_status,
                "attempts": poll_res.attempts,
                "total_elapsed_s": poll_res.total_elapsed_s,
                "transitions": poll_res.transitions,
                "final_body": sanitized_final,
            }
            if isinstance(sanitized_final, dict):
                if print_full_result:
                    print(json.dumps(sanitized_final, indent=2, ensure_ascii=False))
                else:
                    print("Top-level keys:", list(sanitized_final.keys()))
                    if isinstance(sanitized_final.get("data"), dict):
                        print("data keys:", list(sanitized_final["data"].keys()))
    else:
        print(resp.body)

    save_sanitized_json(output, output_path)
    print(f"\nSaved sanitized output to {output_path}")

    usage = client.fetch_api_key_usage()
    if isinstance(usage.body, dict):
        summary = usage.body.get("credit_summary", {})
        print(
            f"Credits remaining: {summary.get('cycle_remaining_credits')} "
            f"(used: {summary.get('cycle_credits_used')})"
        )
    else:
        print(f"Credit check returned HTTP {usage.status_code}: {usage.body}")

    return output
