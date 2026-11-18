"""Phase 2.2 smoke test for POST /v1/env_params in Los Angeles, California."""

from __future__ import annotations

from src.smoke_runner import run_smoke_post


def main() -> None:
    payload = {
        "latitude": 34.0522,
        "longitude": -118.2437,
        "temperature": 30.0,
        "date_time": {
            "start_date": "2024-07-15",
            "start_time": "14:00",
            "filter_type": 1,
        },
    }
    run_smoke_post(
        "/v1/env_params",
        payload,
        "data/raw/env_params_la_20240715.json",
        label="POST /v1/env_params (Downtown LA)",
        poll_interval_s=3.0,
        max_attempts=20,
        print_full_result=True,
    )


if __name__ == "__main__":
    main()
