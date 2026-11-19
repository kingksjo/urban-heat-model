"""Phase 2.4 smoke tests for routing, streetview, and heat_intelligence in LA."""

from __future__ import annotations

import json
import sys
from typing import Any

from src.client import sanitize_payload
from src.smoke_runner import run_smoke_post


def _redact_download_link(obj: Any) -> Any:
    """Redact temporary signed download_link URLs before persisting JSON."""
    if isinstance(obj, dict):
        return {
            k: ("[REDACTED_SIGNED_URL]" if k == "download_link" else _redact_download_link(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_redact_download_link(item) for item in obj]
    return obj


def run_routing() -> None:
    payload = {
        "origin": {"lat": 34.0522, "lon": -118.2437},
        "destination": {"lat": 34.1184, "lon": -118.3004},
        "departure_time": "2024-07-15T14:00:00-07:00",
    }
    out = run_smoke_post(
        "/v1/routing",
        payload,
        "data/raw/routing_la_20240715.json",
        label="POST /v1/routing (Downtown LA -> Griffith Park)",
        poll_interval_s=5.0,
        max_attempts=36,
        print_submit_body=True,
        print_full_result=False,
    )
    poll = out.get("poll") or {}
    final_body = poll.get("final_body") if isinstance(poll, dict) else None
    if isinstance(final_body, dict):
        res = (final_body.get("data") or {}).get("result") or {}
        rr = res.get("result_routing") or {}
        feats = rr.get("features") or []
        print(f"Routing features returned: {len(feats)}, dial: {rr.get('dial')}")
        for idx, f in enumerate(feats[:3]):
            props = f.get("properties") or {}
            print(
                f"  Route {idx}: label={props.get('label')}, dist_km={props.get('distance_km')}, "
                f"dur_min={props.get('duration_min')}, thermal={props.get('thermal')}"
            )


def run_streetview() -> None:
    payload = {
        "latitude": 34.0522,
        "longitude": -118.2437,
        "vertical_angle": 10.0,
        "horizontal_angle": 90.0,
        "back_view": False,
    }
    out = run_smoke_post(
        "/v1/streetview",
        payload,
        "data/raw/streetview_la_20240715.json",
        label="POST /v1/streetview (Downtown LA 34.0522, -118.2437)",
        poll_interval_s=5.0,
        max_attempts=36,
        print_submit_body=False,
        print_full_result=False,
    )
    poll = out.get("poll") or {}
    final_body = poll.get("final_body") if isinstance(poll, dict) else None
    if isinstance(final_body, dict):
        res = (final_body.get("data") or {}).get("result") or {}
        front = res.get("front") or {}
        print(
            f"StreetView front: image_date={front.get('image_date')}, "
            f"segments={json.dumps(front.get('segments'), ensure_ascii=False)}"
        )


def run_heat_intelligence() -> None:
    payload = {
        "latitude": 34.0522,
        "longitude": -118.2437,
        "temperature": 91.6,
        "date": "2024-07-15",
        "analysis": ["environmental"],
    }
    out = run_smoke_post(
        "/v1/heat_intelligence",
        payload,
        "data/raw/heat_intelligence_la_20240715.json",
        label="POST /v1/heat_intelligence (Downtown LA 34.0522, -118.2437, 91.6 F)",
        poll_interval_s=5.0,
        max_attempts=60,
        print_submit_body=True,
        print_full_result=False,
    )
    # Redact signed download_link in saved JSON per docs/limitations
    from src.client import save_sanitized_json

    poll = out.get("poll") or {}
    final_body = poll.get("final_body") if isinstance(poll, dict) else None
    if isinstance(final_body, dict):
        res = (final_body.get("data") or {}).get("result") or {}
        has_link = bool(res.get("download_link"))
        print(f"Heat Intelligence completed; download_link present={has_link}")
    save_sanitized_json(_redact_download_link(sanitize_payload(out)), "data/raw/heat_intelligence_la_20240715.json")


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    if target in ("routing", "all"):
        run_routing()
    if target in ("streetview", "all"):
        run_streetview()
    if target in ("heat_intelligence", "all"):
        run_heat_intelligence()


if __name__ == "__main__":
    main()
