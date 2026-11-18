"""Zero-cost MCP connectivity and tool-discovery check for FortyGuard."""

from __future__ import annotations

from src.client import save_sanitized_json
from src.mcp_client import FortyGuardMCPClient


def main() -> None:
    mcp = FortyGuardMCPClient(timeout=25.0)
    init_res = mcp.initialize()
    print(f"initialize -> HTTP {init_res['status_code']} ({init_res['latency_s']}s)")

    tools_res = mcp.list_tools()
    print(f"tools/list -> HTTP {tools_res['status_code']} ({tools_res['latency_s']}s)")

    save_sanitized_json(
        {"initialize": init_res["body"], "tools_list": tools_res["body"]},
        "data/raw/mcp_tools.json",
    )
    print("Saved MCP discovery output to data/raw/mcp_tools.json")

    parsed = tools_res["body"]
    tools = parsed.get("result", {}).get("tools", []) if isinstance(parsed, dict) else []
    print(f"Discovered {len(tools)} tools:")
    for tool in tools:
        name = tool.get("name")
        desc = (tool.get("description") or "").splitlines()[0][:100]
        print(f"  - {name}: {desc}")


if __name__ == "__main__":
    main()
