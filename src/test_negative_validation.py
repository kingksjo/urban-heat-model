"""Phase 2.5: Safe negative validation tests (0 credits expected)."""

from __future__ import annotations

import json

from src.client import FortyGuardClient, save_sanitized_json


def main() -> None:
    client = FortyGuardClient(timeout=30.0)
    cases = [
        {
            "name": "missing_required_fields_env_params",
            "path": "/v1/env_params",
            "payload": {"latitude": 34.0522, "longitude": -118.2437},
        },
        {
            "name": "out_of_range_coords_env_params",
            "path": "/v1/env_params",
            "payload": {
                "latitude": 95.0,
                "longitude": -200.0,
                "temperature": 30.0,
                "date_time": {"start_date": "2024-07-15", "filter_type": 3},
            },
        },
        {
            "name": "malformed_date_and_enum_env_params",
            "path": "/v1/env_params",
            "payload": {
                "latitude": 34.0522,
                "longitude": -118.2437,
                "temperature": 30.0,
                "date_time": {"start_date": "2024-99-99", "filter_type": 99},
            },
        },
        {
            "name": "unclosed_polygon_heatmap",
            "path": "/v1/heatmap",
            "payload": {
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
                                        [-118.248, 34.048],
                                        [-118.238, 34.048],
                                        [-118.238, 34.056],
                                    ]
                                ],
                            },
                        }
                    ],
                },
                "date_time": {"start_date": "2024-07-15", "filter_type": 3},
                "granularity": 100,
            },
        },
    ]

    results = []
    for case in cases:
        resp = client.request("POST", case["path"], json_body=case["payload"], retries=0)
        print(f"\n[{case['name']}] POST {case['path']} -> HTTP {resp.status_code} ({resp.latency_s}s)")
        print(json.dumps(resp.body, indent=2, ensure_ascii=False) if isinstance(resp.body, (dict, list)) else resp.body)
        results.append(
            {
                "name": case["name"],
                "path": case["path"],
                "request": case["payload"],
                "status_code": resp.status_code,
                "latency_s": resp.latency_s,
                "body": resp.body,
            }
        )

    save_sanitized_json(results, "data/raw/negative_validation_tests.json")
    print("\nSaved to data/raw/negative_validation_tests.json")


if __name__ == "__main__":
    main()
