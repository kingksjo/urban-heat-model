"""Phase 2.4 smoke test for POST /v1/satellite in Downtown Los Angeles, California."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from src.smoke_runner import run_smoke_post


def _save_b64_png(b64_str: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(base64.b64decode(b64_str.split(",")[-1]))


def _summarize_satellite_payload(body: Any, prefix: str = "satellite") -> None:
    """Print satellite metadata and land-cover segments without dumping Base64 images."""
    if not isinstance(body, dict):
        print("Body:", body)
        return
    print("Top-level keys:", list(body.keys()))
    data = body.get("data") if isinstance(body.get("data"), dict) else body
    result = data.get("result") if isinstance(data.get("result"), dict) else data
    if isinstance(result, dict):
        print("Result keys:", list(result.keys()))
        for key in ("coordinates", "image_year", "image_date"):
            if key in result:
                print(f"  {key}: {result[key]}")
        if "original_image" in result:
            orig = result["original_image"]
            desc = f"list[{len(orig)}]" if isinstance(orig, list) else f"len={len(str(orig))}"
            print(f"  original_image: <omitted ({desc})>")
            first_orig = orig[0] if isinstance(orig, list) and orig else orig
            if isinstance(first_orig, str) and first_orig:
                out_orig = Path(f"report/figures/{prefix}_orig.png")
                _save_b64_png(first_orig, out_orig)
                print(f"    saved original PNG -> {out_orig}")
        seg = result.get("segmentation")
        if isinstance(seg, dict):
            print("  segmentation keys:", list(seg.keys()))
            for key in ("request_id", "processing_time_seconds", "image_dimensions", "mode", "segments", "image_legend"):
                if key in seg:
                    print(f"    {key}: {json.dumps(seg[key], ensure_ascii=False)}")
            if seg.get("image_content"):
                print(f"    image_content: <omitted (len={len(str(seg['image_content']))})>")
                out_seg = Path(f"report/figures/{prefix}_seg.png")
                _save_b64_png(str(seg["image_content"]), out_seg)
                print(f"    saved segmentation PNG -> {out_seg}")


def main() -> None:
    payload = {
        "sat": {"latitude": 34.0522, "longitude": -118.2437},
        "date_time": {
            "start_date": "2024-07-15",
            "filter_type": 3,
        },
        "granularity": 80,
    }
    output = run_smoke_post(
        "/v1/satellite",
        payload,
        "data/raw/satellite_la_20240715_g80.json",
        label="POST /v1/satellite (Downtown LA 34.0522, -118.2437, granularity=80, filter_type=3)",
        poll_interval_s=5.0,
        max_attempts=36,
        print_submit_body=False,
        print_full_result=False,
    )
    print("\n--- Satellite Summary ---")
    poll_info = output.get("poll")
    if isinstance(poll_info, dict) and poll_info.get("final_body") is not None:
        _summarize_satellite_payload(poll_info["final_body"], prefix="satellite_g80")
    else:
        _summarize_satellite_payload(output.get("submit_body"), prefix="satellite_g80")


if __name__ == "__main__":
    main()
