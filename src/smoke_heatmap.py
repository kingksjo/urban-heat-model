"""Phase 2.3 smoke test for POST /v1/heatmap in Downtown Los Angeles, California."""

from __future__ import annotations

from src.smoke_runner import run_smoke_post


def main() -> None:
    payload = {
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
                                [-118.2480, 34.0480],
                                [-118.2380, 34.0480],
                                [-118.2380, 34.0560],
                                [-118.2480, 34.0560],
                                [-118.2480, 34.0480],
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
        "idempotency_key": "la-smoke-20240715-v1",
    }
    run_smoke_post(
        "/v1/heatmap",
        payload,
        "data/raw/heatmap_la_20240715.json",
        label="POST /v1/heatmap (Downtown LA ~0.8 km^2, granularity=100, tcm)",
        poll_interval_s=5.0,
        max_attempts=36,
    )


if __name__ == "__main__":
    main()
