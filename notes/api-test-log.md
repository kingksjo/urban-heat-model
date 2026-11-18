# API & MCP Test Log

> Record every test chronologically. Never store API keys, Bearer tokens, or private account identifiers.

## Test Entry Template

- **Timestamp (local / UTC):**
- **Interface:** REST / MCP
- **Endpoint / Tool:**
- **Sanitized Request Parameters:**
- **HTTP Status / MCP Outcome:**
- **Latency (seconds):**
- **Activity ID (if async):**
- **Observed Response Summary / Sanitized File:**
- **Notes / Anomalies:**

---

## Log Entries

### Test 1 — Account Credits & Usage Check (`POST /v1/system/fetch-api-key-usage`)
- **Timestamp (local):** 2026-11-17T23:11+01:00 (2026-11-17T22:11:50Z)
- **Interface:** REST
- **Endpoint / Tool:** `POST https://api.fortyguard.com/v1/system/fetch-api-key-usage`
- **Sanitized Request Parameters:** Headers: `api-key: [REDACTED]`, `Content-Type: application/json`; Body: `{}`
- **HTTP Status / MCP Outcome:** `504`
- **Latency (seconds):** `17.502`
- **Activity ID (if async):** N/A
- **Observed Response Summary / Sanitized File:** `Content-Type: text/plain`, body: `upstream request timeout`
- **Notes / Anomalies:** Gateway returned a `504` plain-text upstream timeout after ~17.5s rather than a JSON response. Retesting without an empty `{}` body and checking a lightweight `GET` endpoint to distinguish endpoint-specific timeout vs. broader upstream outage.

### Test 2 — Account Credits & Usage Check Without Body (`POST /v1/system/fetch-api-key-usage`)
- **Timestamp (local):** 2026-11-17T23:12+01:00 (2026-11-17T22:12Z)
- **Interface:** REST
- **Endpoint / Tool:** `POST https://api.fortyguard.com/v1/system/fetch-api-key-usage`
- **Sanitized Request Parameters:** Headers: `api-key: [REDACTED]`, `Content-Type: application/json`; Body: none
- **HTTP Status / MCP Outcome:** `504`
- **Latency (seconds):** `18.304`
- **Activity ID (if async):** N/A
- **Observed Response Summary / Sanitized File:** `Content-Type: text/plain`, body: `upstream request timeout`
- **Notes / Anomalies:** Identical `504` gateway timeout even without `{}` body.

### Test 3 — Read-Only Monitors List (`GET /v1/monitors`)
- **Timestamp (local):** 2026-11-17T23:13+01:00 (2026-11-17T22:13Z)
- **Interface:** REST
- **Endpoint / Tool:** `GET https://api.fortyguard.com/v1/monitors`
- **Sanitized Request Parameters:** Headers: `api-key: [REDACTED]`, `Content-Type: application/json`
- **HTTP Status / MCP Outcome:** `504`
- **Latency (seconds):** `15.520`
- **Activity ID (if async):** N/A
- **Observed Response Summary / Sanitized File:** `Content-Type: text/plain`, body: `upstream request timeout`
- **Notes / Anomalies:** Different endpoint (`GET /v1/monitors`) also returned `504 upstream request timeout` after ~15.5s, pointing to a broader upstream backend timeout/outage behind `api.fortyguard.com` (or a base URL change to verify against live docs).

### Test 4 — Documentation Reachability (`GET https://docs-api.fortyguard.com/docs/quickstart`)
- **Timestamp (local):** 2026-11-17T23:14+01:00 (2026-11-17T22:14:03Z)
- **Interface:** Web Docs
- **Endpoint / Tool:** `GET https://docs-api.fortyguard.com/docs/quickstart`
- **Sanitized Request Parameters:** Timeout: `15s`
- **HTTP Status / MCP Outcome:** Client `ReadTimeoutError`
- **Latency (seconds):** `>15.0`
- **Activity ID (if async):** N/A
- **Observed Response Summary / Sanitized File:** Read timed out before headers/body returned.
- **Notes / Anomalies:** Documentation host also unresponsive during the same window.

### Test 5 — Invalid Input Validation Probe (`POST /v1/env_params`)
- **Timestamp (local):** 2026-11-17T23:15+01:00 (2026-11-17T22:15:09Z)
- **Interface:** REST
- **Endpoint / Tool:** `POST https://api.fortyguard.com/v1/env_params`
- **Sanitized Request Parameters:** Headers: `api-key: [REDACTED]`, `Content-Type: application/json`; Body: `{}` (intentionally missing required fields)
- **HTTP Status / MCP Outcome:** `504`
- **Latency (seconds):** `16.817`
- **Activity ID (if async):** N/A
- **Observed Response Summary / Sanitized File:** `Content-Type: text/plain`, body: `upstream request timeout`
- **Notes / Anomalies:** Validation did not execute because upstream timed out at the gateway.

### Test 6 — MCP Handshake Probe (`initialize`)
- **Timestamp (local):** 2026-11-17T23:15+01:00 (2026-11-17T22:15:09Z)
- **Interface:** MCP (Streamable HTTP)
- **Endpoint / Tool:** `POST https://tos-mcp.app.fortyguard.com/mcp` (`initialize`)
- **Sanitized Request Parameters:** Headers: `Authorization: Bearer [REDACTED]`, `Content-Type: application/json`, `Accept: application/json, text/event-stream`; JSON-RPC `initialize`
- **HTTP Status / MCP Outcome:** `504`
- **Latency (seconds):** ~`15–18s` (shared command)
- **Activity ID (if async):** N/A
- **Observed Response Summary / Sanitized File:** `Content-Type: text/plain`, body: `upstream request timeout`
- **Notes / Anomalies:** Confirms both REST (`api.fortyguard.com`) and MCP (`tos-mcp.app.fortyguard.com`) gateways are returning `504 upstream request timeout` during this test window.

### Test 7 — Retry Account Credits & Usage Check (`POST /v1/system/fetch-api-key-usage`)
- **Timestamp (local):** 2026-11-17T23:19+01:00 (2026-11-17T22:19:42Z)
- **Interface:** REST
- **Endpoint / Tool:** `POST https://api.fortyguard.com/v1/system/fetch-api-key-usage`
- **Sanitized Request Parameters:** Headers: `api-key: [REDACTED]`, `Content-Type: application/json`; Body: `{}`
- **HTTP Status / MCP Outcome:** `504`
- **Latency (seconds):** `17.651`
- **Activity ID (if async):** N/A
- **Observed Response Summary / Sanitized File:** `Content-Type: text/plain`, body: `upstream request timeout`
- **Notes / Anomalies:** Outage/upstream timeout still ongoing ~8 minutes after Test 1.

### Test 8 — Account Credits Check With Empty `{}` Body (`POST /v1/system/fetch-api-key-usage`)
- **Timestamp (local):** 2026-11-18T06:25+01:00 (2026-11-18T05:25:41Z)
- **Interface:** REST
- **Endpoint / Tool:** `POST https://api.fortyguard.com/v1/system/fetch-api-key-usage`
- **Sanitized Request Parameters:** Headers: `api-key: [REDACTED]`, `Content-Type: application/json`; Body: `{}`
- **HTTP Status / MCP Outcome:** `422`
- **Latency (seconds):** `2.335`
- **Activity ID (if async):** N/A
- **Observed Response Summary / Sanitized File:** Structured JSON validation error (`error: true`, `status_code: 422`, `message: "Field 'api_key' is required."`, `field: "api_key"`, `detail: [{"type": "missing", "loc": ["body", "api_key"], ...}]`).
- **Notes / Anomalies:** Service recovered; notable schema detail: endpoint requires `api_key` in the JSON body (`api_key`) in addition to/despite the `api-key` request header. Also noticed `account_usage.json` was overwritten by the `422` error before sanitization—fixed `src/check_account.py` and `src/client.py` to sanitize first.

### Test 9 — Account Credits & Plan Verification (`POST /v1/system/fetch-api-key-usage`)
- **Timestamp (local):** 2026-11-18T06:26+01:00 (2026-11-18T05:27:06Z)
- **Interface:** REST
- **Endpoint / Tool:** `POST https://api.fortyguard.com/v1/system/fetch-api-key-usage`
- **Sanitized Request Parameters:** Headers: `api-key: [REDACTED]`, `Content-Type: application/json`; Body: `{"api_key": "[REDACTED]"}`
- **HTTP Status / MCP Outcome:** `200`
- **Latency (seconds):** `4.630`
- **Activity ID (if async):** N/A
- **Observed Response Summary / Sanitized File:** Saved to [account_usage.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/account_usage.json). Plan: `Premium` (`One-Time`, active `2026-11-17` to `2026-12-17`). API key status: `active`, `valid: true`, `api_access_available: true`. Credits: `1,000,000` available / `0` used.
- **Notes / Anomalies:** Confirmed API key works and zero credits were consumed by this query. Notably, the response echoes the raw `api_key` value back in the JSON payload.

### Test 10 — MCP Handshake & Tool Discovery (`initialize` + `tools/list`)
- **Timestamp (local):** 2026-11-18T06:38+01:00 (2026-11-18T05:38Z)
- **Interface:** MCP (Streamable HTTP)
- **Endpoint / Tool:** `POST https://tos-mcp.app.fortyguard.com/mcp` (`initialize`, `notifications/initialized`, `tools/list`)
- **Sanitized Request Parameters:** Headers: `Authorization: Bearer [REDACTED]`, `Content-Type: application/json`, `Accept: application/json, text/event-stream`, plus `mcp-session-id` for follow-up calls
- **HTTP Status / MCP Outcome:** `200` (`initialize` in `5.509s`, `tools/list` in `1.952s`)
- **Latency (seconds):** `5.509` (init), `1.952` (tools/list)
- **Activity ID (if async):** N/A
- **Observed Response Summary / Sanitized File:** Saved to [mcp_tools.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/mcp_tools.json). Server `FortyGuard` v`4.0.11` (`protocolVersion: 2024-11-05`) returned `text/event-stream` and exposed `11` tools: `credit_balance`, `env_params`, `heatmap`, `heatmap_read`, `monitoring`, `report`, `report_read`, `satellite`, `streetview`, `temperature_routing`, `temperature_routing_read`.
- **Notes / Anomalies:** Tool schemas include detailed credit costs, US-only coverage bounds, input/output schemas, and unit definitions (e.g., °C for `env_params`/`heatmap` vs. °F for `report`).
