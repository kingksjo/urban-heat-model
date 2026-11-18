"""Reusable Streamable HTTP MCP client helper for FortyGuard."""

from __future__ import annotations

import json
import time
from typing import Any

import requests

from src.client import load_api_key

MCP_URL = "https://tos-mcp.app.fortyguard.com/mcp"


def parse_mcp_response(resp: requests.Response) -> Any:
    """Parse either JSON or Server-Sent Events (SSE) JSON-RPC payloads."""
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


class FortyGuardMCPClient:
    """Minimal MCP Streamable HTTP session client."""

    def __init__(self, api_key: str | None = None, timeout: float = 30.0) -> None:
        self._api_key = api_key or load_api_key()
        self.timeout = timeout
        self._session = requests.Session()
        self._headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        self._next_id = 1
        self.initialized = False

    def _rpc(self, method: str, params: dict[str, Any] | None = None) -> tuple[requests.Response, float, Any]:
        """Send one JSON-RPC request and return the HTTP response, latency, and parsed body."""
        req_id = self._next_id
        self._next_id += 1
        payload = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}}
        start = time.perf_counter()
        resp = self._session.post(
            MCP_URL, headers=self._headers, json=payload, timeout=self.timeout
        )
        latency_s = round(time.perf_counter() - start, 3)
        return resp, latency_s, parse_mcp_response(resp)

    def initialize(self) -> dict[str, Any]:
        """Perform MCP initialize handshake and send notifications/initialized."""
        resp, latency_s, parsed = self._rpc(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "fortyguard-eval", "version": "0.1"},
            },
        )
        if resp.status_code != 200:
            raise RuntimeError(f"MCP initialize failed: HTTP {resp.status_code}: {parsed}")

        sid = resp.headers.get("mcp-session-id") or resp.headers.get("Mcp-Session-Id")
        if sid:
            self._headers["mcp-session-id"] = sid

        self._session.post(
            MCP_URL,
            headers=self._headers,
            json={"jsonrpc": "2.0", "method": "notifications/initialized"},
            timeout=15.0,
        )
        self.initialized = True
        return {"status_code": resp.status_code, "latency_s": latency_s, "body": parsed}

    def list_tools(self) -> dict[str, Any]:
        """Discover available MCP tools via tools/list."""
        if not self.initialized:
            self.initialize()
        resp, latency_s, parsed = self._rpc("tools/list", {})
        return {
            "status_code": resp.status_code,
            "latency_s": latency_s,
            "content_type": resp.headers.get("Content-Type"),
            "body": parsed,
        }

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        """Invoke an MCP tool by name and return HTTP status, latency, and parsed result."""
        if not self.initialized:
            self.initialize()
        resp, latency_s, parsed = self._rpc(
            "tools/call", {"name": name, "arguments": arguments or {}}
        )
        return {
            "tool": name,
            "status_code": resp.status_code,
            "latency_s": latency_s,
            "content_type": resp.headers.get("Content-Type"),
            "body": parsed,
        }
