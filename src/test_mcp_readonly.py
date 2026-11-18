"""Free read-only MCP tool checks: credit_balance and heatmap_read."""

from __future__ import annotations

import json

from src.client import sanitize_payload, save_sanitized_json
from src.mcp_client import FortyGuardMCPClient


def main() -> None:
    mcp = FortyGuardMCPClient(timeout=30.0)
    init_res = mcp.initialize()
    print(f"MCP initialize -> HTTP {init_res['status_code']} ({init_res['latency_s']}s)")

    cb = mcp.call_tool("credit_balance", {})
    print(f"\ncredit_balance -> HTTP {cb['status_code']} ({cb['latency_s']}s)")
    print(json.dumps(sanitize_payload(cb["body"]), indent=2, ensure_ascii=False))

    hm_read = mcp.call_tool(
        "heatmap_read",
        {"activity_id": "470b48bb-e48b-4eb6-906e-6980fcfd9420"},
    )
    print(f"\nheatmap_read -> HTTP {hm_read['status_code']} ({hm_read['latency_s']}s)")
    print(json.dumps(sanitize_payload(hm_read["body"]), indent=2, ensure_ascii=False))

    save_sanitized_json(
        {"credit_balance": cb, "heatmap_read": hm_read},
        "data/raw/mcp_readonly_check.json",
    )
    print("\nSaved to data/raw/mcp_readonly_check.json")


if __name__ == "__main__":
    main()
