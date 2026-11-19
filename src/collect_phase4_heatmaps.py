"""Collect contrasting LA Basin heatmaps for Phase 4 Urban Heat Pattern Explorer.

Keeps Phase 2/3 API-test files separate from the Phase 4 ML dataset:
- Reuses the two existing 2024-07-15 14:00 heatmaps (`downtown_la`, `griffith_park`)
  by referencing them in `data/raw/phase4_heatmaps/manifest.json` without re-querying.
- Saves all new Phase 4 heatmaps under `data/raw/phase4_heatmaps/<slug>_20240715.json`.
- Checkpoints after every neighborhood and stops once cumulative tiles reach target_tiles.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from src.client import FortyGuardClient, save_sanitized_json
from src.polling import poll_activity

PHASE4_DIR = Path("data/raw/phase4_heatmaps")
MANIFEST_PATH = PHASE4_DIR / "manifest.json"

EXISTING_HEATMAPS: list[dict[str, Any]] = [
    {
        "slug": "downtown_la",
        "name": "Downtown LA",
        "zone": "urban_core",
        "bbox": [-118.248, 34.048, -118.238, 34.056],
        "source": "phase2_smoke_test",
        "file_path": "data/raw/heatmap_la_20240715.json",
    },
    {
        "slug": "griffith_park",
        "name": "Griffith Park",
        "zone": "park_hills",
        "bbox": [-118.305, 34.128, -118.295, 34.136],
        "source": "phase3_mcp_test",
        "file_path": "data/raw/heatmap_griffith_20240715.json",
    },
]

# 0.010 deg lon x 0.008 deg lat (~0.8 km^2) boxes across contrasting LA microclimates.
NEW_NEIGHBORHOODS: list[dict[str, Any]] = [
    {"slug": "santa_monica", "name": "Santa Monica", "zone": "coastal", "bbox": [-118.492, 34.014, -118.482, 34.022]},
    {"slug": "venice", "name": "Venice", "zone": "coastal", "bbox": [-118.468, 33.990, -118.458, 33.998]},
    {"slug": "playa_vista", "name": "Playa Vista", "zone": "coastal", "bbox": [-118.422, 33.972, -118.412, 33.980]},
    {"slug": "el_segundo", "name": "El Segundo", "zone": "coastal_industrial", "bbox": [-118.415, 33.918, -118.405, 33.926]},
    {"slug": "westwood_ucla", "name": "Westwood / UCLA", "zone": "westside", "bbox": [-118.448, 34.062, -118.438, 34.070]},
    {"slug": "century_city", "name": "Century City", "zone": "westside", "bbox": [-118.420, 34.054, -118.410, 34.062]},
    {"slug": "brentwood", "name": "Brentwood", "zone": "westside", "bbox": [-118.478, 34.052, -118.468, 34.060]},
    {"slug": "culver_city", "name": "Culver City", "zone": "westside", "bbox": [-118.398, 34.018, -118.388, 34.026]},
    {"slug": "koreatown", "name": "Koreatown", "zone": "urban_core", "bbox": [-118.305, 34.058, -118.295, 34.066]},
    {"slug": "hollywood", "name": "Hollywood", "zone": "urban_core", "bbox": [-118.332, 34.096, -118.322, 34.104]},
    {"slug": "echo_park", "name": "Echo Park", "zone": "central_east", "bbox": [-118.268, 34.072, -118.258, 34.080]},
    {"slug": "boyle_heights", "name": "Boyle Heights", "zone": "central_east", "bbox": [-118.212, 34.036, -118.202, 34.044]},
    {"slug": "lincoln_heights", "name": "Lincoln Heights", "zone": "central_east", "bbox": [-118.215, 34.068, -118.205, 34.076]},
    {"slug": "west_adams", "name": "West Adams", "zone": "central", "bbox": [-118.338, 34.028, -118.328, 34.036]},
    {"slug": "vernon_industrial", "name": "Vernon Industrial", "zone": "industrial", "bbox": [-118.230, 34.000, -118.220, 34.008]},
    {"slug": "commerce", "name": "City of Commerce", "zone": "industrial", "bbox": [-118.155, 33.998, -118.145, 34.006]},
    {"slug": "inglewood", "name": "Inglewood", "zone": "south_la", "bbox": [-118.355, 33.956, -118.345, 33.964]},
    {"slug": "watts", "name": "Watts", "zone": "south_la", "bbox": [-118.250, 33.938, -118.240, 33.946]},
    {"slug": "compton", "name": "Compton", "zone": "south_la", "bbox": [-118.225, 33.892, -118.215, 33.900]},
    {"slug": "torrance", "name": "Torrance", "zone": "south_bay", "bbox": [-118.345, 33.832, -118.335, 33.840]},
    {"slug": "long_beach_downtown", "name": "Long Beach Downtown", "zone": "harbor", "bbox": [-118.195, 33.768, -118.185, 33.776]},
    {"slug": "long_beach_port", "name": "Long Beach / Wilmington", "zone": "harbor_industrial", "bbox": [-118.228, 33.772, -118.218, 33.780]},
    {"slug": "burbank", "name": "Burbank", "zone": "valley", "bbox": [-118.315, 34.178, -118.305, 34.186]},
    {"slug": "glendale", "name": "Glendale", "zone": "foothills", "bbox": [-118.260, 34.142, -118.250, 34.150]},
    {"slug": "pasadena", "name": "Pasadena", "zone": "sgv_foothills", "bbox": [-118.148, 34.144, -118.138, 34.152]},
    {"slug": "sherman_oaks", "name": "Sherman Oaks", "zone": "valley", "bbox": [-118.450, 34.148, -118.440, 34.156]},
    {"slug": "van_nuys", "name": "Van Nuys", "zone": "valley", "bbox": [-118.452, 34.184, -118.442, 34.192]},
    {"slug": "northridge", "name": "Northridge", "zone": "valley", "bbox": [-118.535, 34.234, -118.525, 34.242]},
    {"slug": "woodland_hills", "name": "Woodland Hills", "zone": "west_valley", "bbox": [-118.608, 34.166, -118.598, 34.174]},
    {"slug": "alhambra", "name": "Alhambra", "zone": "sgv", "bbox": [-118.132, 34.090, -118.122, 34.098]},
    {"slug": "el_monte", "name": "El Monte", "zone": "sgv", "bbox": [-118.032, 34.068, -118.022, 34.076]},
    {"slug": "arcadia", "name": "Arcadia", "zone": "sgv_foothills", "bbox": [-118.040, 34.136, -118.030, 34.144]},
    {"slug": "sun_valley", "name": "Sun Valley", "zone": "valley_industrial", "bbox": [-118.385, 34.222, -118.375, 34.230]},
    {"slug": "la_canada_foothills", "name": "La Canada Foothills", "zone": "foothills", "bbox": [-118.180, 34.202, -118.170, 34.210]},
]


def build_heatmap_payload(bbox: list[float], slug: str) -> dict[str, Any]:
    min_lon, min_lat, max_lon, max_lat = bbox
    return {
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
                                [min_lon, min_lat],
                                [max_lon, min_lat],
                                [max_lon, max_lat],
                                [min_lon, max_lat],
                                [min_lon, min_lat],
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
        "idempotency_key": f"p4-{slug}-20240715-v1",
    }


def extract_tile_summary(raw_path: Path) -> tuple[str | None, list[dict[str, Any]]]:
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    if "poll" in data and isinstance(data["poll"], dict):
        poll_node = data["poll"]
        data_node = (poll_node.get("final_body") or {}).get("data") or {}
        activity_id = poll_node.get("activity_id") or data_node.get("activity_id")
        features = ((data_node.get("result") or {}).get("map_data") or {}).get("features") or []
        return activity_id, features
    if "final_body" in data:
        data_node = (data["final_body"] or {}).get("data") or {}
        activity_id = data.get("activity_id") or data_node.get("activity_id")
        features = ((data_node.get("result") or {}).get("map_data") or {}).get("features") or []
        return activity_id, features
    # Support direct status body format (e.g., Phase 3 Griffith Park REST status file)
    data_node = data.get("data") or {}
    activity_id = data_node.get("activity_id")
    features = ((data_node.get("result") or {}).get("map_data") or {}).get("features") or []
    return activity_id, features


def get_remaining_credits(client: FortyGuardClient) -> int | None:
    usage = client.fetch_api_key_usage()
    if isinstance(usage.body, dict):
        summary = usage.body.get("credit_summary")
        if isinstance(summary, dict):
            return summary.get("total_remaining_credits")
        data_node = usage.body.get("data")
        if isinstance(data_node, dict):
            return data_node.get("credits_remaining")
    return None


def summarize_entry(meta: dict[str, Any], raw_path: Path) -> dict[str, Any] | None:
    if not raw_path.exists():
        return None
    activity_id, features = extract_tile_summary(raw_path)
    if not features:
        return None
    temps = [
        float(f["properties"]["average_temperature"])
        for f in features
        if isinstance(f.get("properties"), dict) and f["properties"].get("average_temperature") is not None
    ]
    if not temps:
        return None
    return {
        "slug": meta["slug"],
        "name": meta["name"],
        "zone": meta["zone"],
        "bbox": meta["bbox"],
        "source": meta["source"],
        "file_path": str(raw_path).replace("\\", "/"),
        "activity_id": activity_id,
        "tile_count": len(features),
        "mean_temp_c": round(sum(temps) / len(temps), 3),
        "min_temp_c": round(min(temps), 3),
        "max_temp_c": round(max(temps), 3),
    }


def save_manifest(entries: list[dict[str, Any]]) -> None:
    PHASE4_DIR.mkdir(parents=True, exist_ok=True)
    total_tiles = sum(e["tile_count"] for e in entries)
    manifest = {
        "dataset": "urban_heat_pattern_explorer_phase4",
        "date_time": "2024-07-15 14:00",
        "granularity_m": 100,
        "analytic_type": "tcm",
        "total_neighborhoods": len(entries),
        "total_tiles": total_tiles,
        "neighborhoods": entries,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect Phase 4 LA heatmaps up to target tile count.")
    parser.add_argument("--target-tiles", type=int, default=2500, help="Stop once total tiles >= this value.")
    args = parser.parse_args()

    PHASE4_DIR.mkdir(parents=True, exist_ok=True)
    client = FortyGuardClient(timeout=60.0)

    start_credits = get_remaining_credits(client)
    print(f"Starting credits remaining: {start_credits}")

    entries: list[dict[str, Any]] = []
    for existing in EXISTING_HEATMAPS:
        summary = summarize_entry(existing, Path(existing["file_path"]))
        if summary:
            entries.append(summary)
            print(f"[reused] {summary['slug']}: {summary['tile_count']} tiles, mean={summary['mean_temp_c']} C")

    total_tiles = sum(e["tile_count"] for e in entries)
    save_manifest(entries)
    print(f"Baseline reused tiles: {total_tiles} across {len(entries)} neighborhoods\n")

    failures: list[dict[str, Any]] = []
    for idx, nb in enumerate(NEW_NEIGHBORHOODS, start=1):
        if total_tiles >= args.target_tiles:
            print(f"Target {args.target_tiles} tiles reached ({total_tiles} tiles). Stopping.")
            break

        out_path = PHASE4_DIR / f"{nb['slug']}_20240715.json"
        meta = {**nb, "source": "phase4_collection"}

        cached = summarize_entry(meta, out_path)
        if cached:
            entries.append(cached)
            total_tiles += cached["tile_count"]
            print(f"[{idx}/{len(NEW_NEIGHBORHOODS)}] [cached] {nb['slug']}: {cached['tile_count']} tiles (total={total_tiles})")
            save_manifest(entries)
            continue

        payload = build_heatmap_payload(nb["bbox"], nb["slug"])
        print(f"[{idx}/{len(NEW_NEIGHBORHOODS)}] Submitting POST /v1/heatmap for {nb['name']} ({nb['slug']})...")
        try:
            submit_resp = client.request("POST", "/v1/heatmap", json_body=payload, retries=0)
        except Exception as exc:
            print(f"  ERROR submit exception: {exc}")
            failures.append({"slug": nb["slug"], "stage": "submit", "error": str(exc)})
            continue

        if submit_resp.status_code != 200 or not isinstance(submit_resp.body, dict):
            print(f"  ERROR submit HTTP {submit_resp.status_code}: {str(submit_resp.body)[:200]}")
            failures.append({"slug": nb["slug"], "stage": "submit", "status_code": submit_resp.status_code, "body": str(submit_resp.body)[:200]})
            continue

        data_node = submit_resp.body.get("data") or {}
        activity_id = submit_resp.body.get("activity_id") or data_node.get("activity_id")
        if not activity_id:
            print(f"  ERROR missing activity_id in response: {list(submit_resp.body.keys())}")
            failures.append({"slug": nb["slug"], "stage": "submit", "error": "missing activity_id"})
            continue

        poll = poll_activity(client, activity_id, interval_s=5.0, max_attempts=36)
        print(f"  Polled {activity_id}: status={poll.final_status}, attempts={poll.attempts}, elapsed={poll.total_elapsed_s:.1f}s")
        if poll.final_status != "Completed":
            failures.append({"slug": nb["slug"], "stage": "poll", "activity_id": activity_id, "status": poll.final_status})
            continue

        final_body = poll.final_response.body if poll.final_response else None
        record = {
            "label": f"Phase 4 heatmap: {nb['name']} ({nb['slug']})",
            "endpoint": "/v1/heatmap",
            "neighborhood": meta,
            "request_payload": payload,
            "submit_status_code": submit_resp.status_code,
            "submit_elapsed_s": round(submit_resp.latency_s, 3),
            "activity_id": activity_id,
            "poll_status": poll.final_status,
            "poll_attempts": poll.attempts,
            "poll_elapsed_s": round(poll.total_elapsed_s, 3),
            "final_body": final_body,
        }
        save_sanitized_json(record, out_path)
        saved = summarize_entry(meta, out_path)
        if saved:
            entries.append(saved)
            total_tiles += saved["tile_count"]
            save_manifest(entries)
            print(
                f"  Saved {saved['tile_count']} tiles (mean={saved['mean_temp_c']} C, "
                f"range={saved['min_temp_c']}..{saved['max_temp_c']} C) | cumulative={total_tiles}"
            )
        else:
            print(f"  WARNING: saved file had no valid tile temperatures: {out_path}")
            failures.append({"slug": nb["slug"], "stage": "parse", "activity_id": activity_id})

    end_credits = get_remaining_credits(client)

    print("\n--- Phase 4 Heatmap Collection Summary ---")
    print(f"Neighborhoods collected: {len(entries)}")
    print(f"Total tiles: {total_tiles}")
    print(f"Failures: {len(failures)}")
    if failures:
        print(f"Failure details: {failures}")
    print(f"Credits remaining: {end_credits} (spent: {(start_credits - end_credits) if (start_credits is not None and end_credits is not None) else 'unknown'})")
    print(f"Manifest saved to: {MANIFEST_PATH}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
