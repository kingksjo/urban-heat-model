"""Bounded, credit-safe retry script for a single POST /v1/satellite smoke test."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from src.client import FortyGuardClient, sanitize_payload, save_sanitized_json
from src.polling import poll_activity


def wait_for_healthy_backend(
    client: FortyGuardClient,
    *,
    max_checks: int = 20,
    wait_s: float = 15.0,
) -> int | None:
    """Poll free fetch-api-key-usage until HTTP 200; return remaining credits or None."""
    for i in range(1, max_checks + 1):
        try:
            resp = client.request(
                "POST",
                "/v1/system/fetch-api-key-usage",
                json_body={"api_key": client._api_key},
                timeout=20.0,
                retries=0,
            )
            if resp.status_code == 200 and isinstance(resp.body, dict):
                remaining = resp.body.get("credit_summary", {}).get("cycle_remaining_credits")
                print(f"[health {i}/{max_checks}] Backend healthy (200 in {resp.latency_s}s); credits={remaining}")
                return int(remaining) if remaining is not None else 0
            print(f"[health {i}/{max_checks}] HTTP {resp.status_code} ({resp.latency_s}s); waiting {wait_s}s...")
        except Exception as exc:  # noqa: BLE001
            print(f"[health {i}/{max_checks}] {type(exc).__name__}; waiting {wait_s}s...")
        if i < max_checks:
            time.sleep(wait_s)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Bounded retry runner for POST /v1/satellite")
    parser.add_argument("--lat", type=float, default=34.0522)
    parser.add_argument("--lon", type=float, default=-118.2437)
    parser.add_argument("--date", default="2024-07-15")
    parser.add_argument("--granularity", type=int, default=20, choices=[20, 60, 80, 100])
    parser.add_argument("--max-submissions", type=int, default=3)
    parser.add_argument("--max-health-checks", type=int, default=20)
    parser.add_argument("--wait-s", type=float, default=15.0)
    parser.add_argument("--out", default="data/raw/satellite_retry_result.json")
    args = parser.parse_args()

    client = FortyGuardClient(timeout=60.0)
    payload = {
        "sat": {"latitude": args.lat, "longitude": args.lon},
        "date_time": {"start_date": args.date, "filter_type": 3},
        "granularity": args.granularity,
    }

    worker_failures = 0
    for sub in range(1, args.max_submissions + 1):
        print(f"\n=== Attempt {sub}/{args.max_submissions} (granularity={args.granularity}) ===")
        credits_before = wait_for_healthy_backend(
            client, max_checks=args.max_health_checks, wait_s=args.wait_s
        )
        if credits_before is None:
            print("Stopped: backend did not become healthy within health-check budget.")
            return

        try:
            resp = client.request("POST", "/v1/satellite", json_body=payload, retries=0)
        except Exception as exc:  # noqa: BLE001
            print(f"Submit failed with {type(exc).__name__}; waiting {args.wait_s}s before next check...")
            time.sleep(args.wait_s)
            continue

        print(f"POST /v1/satellite -> HTTP {resp.status_code} ({resp.latency_s}s)")
        if resp.status_code != 200 or not isinstance(resp.body, dict):
            print(f"Non-200 submit ({resp.status_code}): {str(resp.body)[:200]}")
            time.sleep(args.wait_s)
            continue

        data_obj = resp.body.get("data") if isinstance(resp.body.get("data"), dict) else {}
        activity_id = resp.body.get("activity_id") or data_obj.get("activity_id")
        if not activity_id:
            # Synchronous success if ever returned directly
            save_sanitized_json({"request": payload, "submit_body": resp.body}, args.out)
            print(f"Saved direct response to {args.out}")
            return

        print(f"Submitted activity_id={activity_id}; polling...")
        poll_res = poll_activity(client, str(activity_id), interval_s=5.0, max_attempts=36)
        print(f"Poll result: status={poll_res.final_status} in {poll_res.total_elapsed_s}s")

        if poll_res.final_status.lower() == "completed":
            out_data = {
                "request": payload,
                "submit_status": resp.status_code,
                "submit_latency_s": resp.latency_s,
                "submit_body": sanitize_payload(resp.body),
                "poll": {
                    "activity_id": poll_res.activity_id,
                    "final_status": poll_res.final_status,
                    "attempts": poll_res.attempts,
                    "total_elapsed_s": poll_res.total_elapsed_s,
                    "transitions": poll_res.transitions,
                    "final_body": sanitize_payload(
                        poll_res.final_response.body if poll_res.final_response else None
                    ),
                },
            }
            save_sanitized_json(out_data, args.out)
            print(f"SUCCESS! Saved sanitized response to {Path(args.out)}")
            # Print compact summary without dumping Base64 images
            final_body = out_data["poll"]["final_body"]
            res = (final_body.get("data") or {}).get("result") if isinstance(final_body, dict) else None
            if isinstance(res, dict):
                seg = res.get("segmentation") or {}
                print("image_year:", res.get("image_year"), "image_date:", res.get("image_date"))
                print("segments:", json.dumps(seg.get("segments"), ensure_ascii=False))
            return

        if poll_res.final_status.lower() == "failed":
            worker_failures += 1
            print(f"Worker returned Failed (worker_failures={worker_failures}).")
            if worker_failures >= 2:
                print("Stopping: satellite worker returned Failed twice (not a transient 504).")
                return
            time.sleep(args.wait_s)

    print("Reached max_submissions without a Completed satellite job.")


if __name__ == "__main__":
    main()
