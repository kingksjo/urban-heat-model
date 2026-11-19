"""Phase 3.2 async MCP heatmap + heatmap_read test (Griffith Park, LA) + REST GeoJSON fetch."""

from __future__ import annotations

import json
import time

from src.client import FortyGuardClient, sanitize_payload, save_sanitized_json
from src.mcp_client import FortyGuardMCPClient


def _extract_structured(resp: dict) -> dict:
    body = resp.get("body") or {}
    res = body.get("result") or {}
    sc = res.get("structuredContent")
    if isinstance(sc, dict):
        return sc
    content = res.get("content") or []
    if content and isinstance(content[0], dict) and content[0].get("text"):
        try:
            return json.loads(content[0]["text"])
        except json.JSONDecodeError:
            pass
    return {}


def main() -> None:
    mcp = FortyGuardMCPClient(timeout=45.0)
    init_res = mcp.initialize()
    print(f"MCP initialize -> HTTP {init_res['status_code']} ({init_res['latency_s']}s)")

    args = {
        "polygon_aoi": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [-118.3050, 34.1280],
                                [-118.2950, 34.1280],
                                [-118.2950, 34.1360],
                                [-118.3050, 34.1360],
                                [-118.3050, 34.1280],
                            ]
                        ],
                    },
                }
            ],
        },
        "date_time": {
            "start_date": "2024-07-15",
            "start_time": "14:00",
            "filter_type": 1,
        },
        "granularity": 100,
        "analytic_type": "tcm",
        "idempotency_key": "griffith-mcp-20240715-v1",
    }

    submit_res = mcp.call_tool("heatmap", args)
    print(f"MCP heatmap -> HTTP {submit_res['status_code']} ({submit_res['latency_s']}s)")
    sc_sub = _extract_structured(submit_res)
    print(json.dumps(sanitize_payload(sc_sub), indent=2, ensure_ascii=False))

    result_obj = sc_sub.get("result") if isinstance(sc_sub.get("result"), dict) else sc_sub
    activity_id = result_obj.get("activity_id") or result_obj.get("heatmap_id")
    if not activity_id and isinstance(result_obj.get("value"), dict):
        activity_id = result_obj["value"].get("activity_id") or result_obj["value"].get("heatmap_id")

    if not activity_id:
        save_sanitized_json({"submit": submit_res}, "data/raw/mcp_heatmap_griffith_20240715.json")
        print("No activity_id returned; stopping.")
        return

    print(f"\nPolling MCP heatmap_read for activity_id={activity_id}...")
    transitions = []
    start = time.perf_counter()
    final_read = None
    for attempt in range(1, 31):
        read_res = mcp.call_tool("heatmap_read", {"activity_id": str(activity_id)})
        final_read = read_res
        sc_read = _extract_structured(read_res)
        val = ((sc_read.get("result") or {}).get("value") or {}) if isinstance(sc_read.get("result"), dict) else {}
        status = str(val.get("status") or sc_read.get("status") or "unknown").lower()
        elapsed = round(time.perf_counter() - start, 3)
        transitions.append((attempt, status, elapsed))
        if status in {"completed", "failed", "error"}:
            break
        time.sleep(5.0)

    print("MCP transitions:", transitions)
    print("Final MCP heatmap_read:")
    print(json.dumps(sanitize_payload(_extract_structured(final_read or {})), indent=2, ensure_ascii=False))

    save_sanitized_json(
        {"request": args, "submit": submit_res, "transitions": transitions, "final_read": final_read},
        "data/raw/mcp_heatmap_griffith_20240715.json",
    )

    # Fetch full GeoJSON tiles via REST GET /v1/status/{activity_id} (0 extra credits)
    rest = FortyGuardClient(timeout=45.0)
    rest_res = rest.get_status(str(activity_id))
    print(f"\nREST GET /v1/status/{activity_id} -> HTTP {rest_res.status_code} ({rest_res.latency_s}s)")
    if isinstance(rest_res.body, dict):
        feats = (((rest_res.body.get("data") or {}).get("result") or {}).get("map_data") or {}).get("features") or []
        print(f"REST GeoJSON tile count: {len(feats)}")
        save_sanitized_json(rest_res.body, "data/raw/heatmap_griffith_20240715.json")
        print("Saved full GeoJSON to data/raw/heatmap_griffith_20240715.json")

    cb = mcp.call_tool("credit_balance", {})
    print("MCP credit_balance:", _extract_structured(cb))


if __name__ == "__main__":
    main()
