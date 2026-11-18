"""Zero-cost MCP connectivity and tool-discovery check for FortyGuard."""

from __future__ import annotations

import json
import time
from typing import Any

import requests

from src.client import load_api_key, save_sanitized_json

MCP_URL = "https://tos-mcp.app.fortyguard.com/mcp"


def parse_mcp_response(resp: requests.Response) -> Any:
    """Parse either plain JSON or Server-Sent Events (SSE) JSON-RPC payloads."""
    content_type = (resp.headers.get("Content-Type") or "").lower()
    if "text/event-stream" in content_type:
        messages = []
        for line in resp.text.splitlines():
            if line.startswith("data:"):
                payload = line[5:].strip()
                if payload:
                    try:
                        messages.append(json.loads(payload))
                    except json.JSONDecodeError:
                        messages.append(payload)
        return messages if len(messages) != 1 else messages[0]
    try:
        return resp.json()
    except ValueError:
        return resp.text


def mcp_post(
    session: requests.Session,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: float = 25.0,
) -> tuple[requests.Response, float, Any]:
    """Send one JSON-RPC POST to the MCP endpoint and measure latency."""
    start = time.perf_counter()
    resp = session.post(MCP_URL, headers=headers, json=payload, timeout=timeout)
    latency_s = round(time.perf_counter() - start, 3)
    return resp, latency_s, parse_mcp_response(resp)


def main() -> None:
    api_key = load_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    with requests.Session() as session:
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "fortyguard-eval", "version": "0.1"},
            },
        }
        resp, latency_s, parsed = mcp_post(session, headers, init_payload)
        print(f"initialize -> HTTP {resp.status_code} ({latency_s}s) [{resp.headers.get('Content-Type')}]")

        if resp.status_code != 200:
            print("Response:", parsed if isinstance(parsed, str) else json.dumps(parsed, indent=2)[:800])
            return

        session_id = resp.headers.get("mcp-session-id") or resp.headers.get("Mcp-Session-Id")
        if session_id:
            headers["mcp-session-id"] = session_id

        # Send initialized notification (best-effort)
        notif_payload = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        session.post(MCP_URL, headers=headers, json=notif_payload, timeout=15.0)

        tools_payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        t_resp, t_latency, t_parsed = mcp_post(session, headers, tools_payload)
        print(f"tools/list -> HTTP {t_resp.status_code} ({t_latency}s)")

        save_sanitized_json({"initialize": parsed, "tools_list": t_parsed}, "data/raw/mcp_tools.json")
        print("Saved MCP discovery output to data/raw/mcp_tools.json")

        tools = (
            t_parsed.get("result", {}).get("tools", [])
            if isinstance(t_parsed, dict)
            else []
        )
        print(f"Discovered {len(tools)} tools:")
        for tool in tools:
            name = tool.get("name")
            desc = (tool.get("description") or "").splitlines()[0][:100]
            print(f"  - {name}: {desc}")


if __name__ == "__main__":
    main()
