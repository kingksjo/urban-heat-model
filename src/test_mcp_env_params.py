"""Phase 3.2/3.4: Equivalent MCP env_params call for REST vs MCP comparison."""

from __future__ import annotations

import json

from src.client import sanitize_payload, save_sanitized_json
from src.mcp_client import FortyGuardMCPClient


def main() -> None:
    mcp = FortyGuardMCPClient(timeout=45.0)
    init_res = mcp.initialize()
    print(f"MCP initialize -> HTTP {init_res['status_code']} ({init_res['latency_s']}s)")

    args = {
        "latitude": 34.0522,
        "longitude": -118.2437,
        "temperature": 30.0,
        "date_time": {
            "start_date": "2024-07-15",
            "start_time": "14:00",
            "filter_type": 1,
        },
    }
    res = mcp.call_tool("env_params", args)
    print(f"env_params -> HTTP {res['status_code']} ({res['latency_s']}s)")
    print(json.dumps(sanitize_payload(res["body"]), indent=2, ensure_ascii=False))

    save_sanitized_json({"request": args, "response": res}, "data/raw/mcp_env_params_la.json")
    print("\nSaved to data/raw/mcp_env_params_la.json")


if __name__ == "__main__":
    main()
