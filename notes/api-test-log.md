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

### Test 11 — REST Environmental Parameters Smoke Test (Downtown Los Angeles, CA)
- **Timestamp (local):** 2026-11-18T07:10–07:11+01:00 (2026-11-18T06:10:28Z – 06:11:33Z)
- **Interface:** REST
- **Endpoint / Tool:** `POST /v1/env_params` -> `GET /v1/status/830ebd44-024d-4f37-88a6-20be5801d505`
- **Sanitized Request Parameters:** `{"latitude": 34.0522, "longitude": -118.2437, "temperature": 30.0, "date_time": {"start_date": "2024-07-15", "start_time": "14:00", "filter_type": 1}}`
- **HTTP Status / MCP Outcome:** Submit `200` (`10.182s`); Status Poll `200` (`3.404s`, `data.status: "Completed"`)
- **Latency (seconds):** `10.182` (submit), `3.404` (status poll)
- **Activity ID (if async):** `830ebd44-024d-4f37-88a6-20be5801d505`
- **Observed Response Summary / Sanitized File:** Saved to [env_params_la_20240715.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/env_params_la_20240715.json) and [env_params_la_20240715_result.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/env_params_la_20240715_result.json). Returned `America/Los_Angeles` (`-07:00`) timestamp `2024-07-15T14:00:00-07:00`, `elevation: 91.0`, `heat_index_celsius: [30.0]`, `apparent_temperature_celsius: [29.9]`, `relative_humidity_percent: [42.6]`, `wet_bulb_temperature_celsius: [20.3]`, `precipitation_mm: [0.0]`, `cloud_cover_octas: [0]`, AQI metrics, clear-sky solar irradiance (`ghi: 908.63, dni: 791.83, dhi: 157.67`), and `null` for `methane_ppb` and `co2_ppm`. Credits deducted: `2,900` (`997,100` remaining).
- **Notes / Anomalies:** Confirmed REST `POST /v1/env_params` is **asynchronous** (`data.activity_id`, no `status` field on submit), unlike MCP's direct `env_params` tool. Also observed inconsistent AQI key naming (`air_quality:idx`, `air_quality_pm2p5:idx`, ..., vs. `aqi_us_co`).

### Test 12 — REST Heatmap Smoke Test (`POST /v1/heatmap` — Downtown LA)
- **Timestamp (local):** 2026-11-18T07:20+01:00 (2026-11-18T06:20:32Z)
- **Interface:** REST
- **Endpoint / Tool:** `POST https://api.fortyguard.com/v1/heatmap`
- **Sanitized Request Parameters:** `polygon_aoi` GeoJSON `FeatureCollection` (~0.8 km² box around `[-118.248, 34.048]` to `[-118.238, 34.056]`), `date_time: {"start_date": "2024-07-15", "start_time": "14:00", "filter_type": 1}`, `granularity: 100`, `analytic_type: "tcm"`
- **HTTP Status / MCP Outcome:** `504`
- **Latency (seconds):** `17.755`
- **Activity ID (if async):** None returned
- **Observed Response Summary / Sanitized File:** Saved to [heatmap_la_20240715.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/heatmap_la_20240715.json). Returned `Content-Type: text/plain`, body: `upstream request timeout`.
- **Notes / Anomalies:** Gateway cut off the request at `17.755s` with `504`. Follow-up `fetch-api-key-usage` inside the same script also did not return JSON, indicating either another transient backend stall or a gateway timeout shorter than slow submit handlers (~10.2s even for `env_params` submit).

### Test 13 — REST Heatmap Retry With `idempotency_key` (`POST /v1/heatmap` — Downtown LA)
- **Timestamp (local):** 2026-11-18T07:24+01:00 (2026-11-18T06:24:35Z)
- **Interface:** REST
- **Endpoint / Tool:** `POST /v1/heatmap` -> `GET /v1/status/470b48bb-e48b-4eb6-906e-6980fcfd9420` (6 polls)
- **Sanitized Request Parameters:** Same ~0.8 km² Downtown LA `FeatureCollection`, `2024-07-15 14:00` (`filter_type: 1`), `granularity: 100`, `analytic_type: "tcm"`, `idempotency_key: "la-smoke-20240715-v1"`
- **HTTP Status / MCP Outcome:** Submit `200` (`6.799s`); Status Polling `200` (`Processing` × 5 -> `Completed` on attempt 6 in `32.469s`)
- **Latency (seconds):** `6.799` (submit), `32.469` (total polling to `Completed`)
- **Activity ID (if async):** `470b48bb-e48b-4eb6-906e-6980fcfd9420`
- **Observed Response Summary / Sanitized File:** Saved to [heatmap_la_20240715.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/heatmap_la_20240715.json). Returned `data.result.map_data` (GeoJSON `FeatureCollection` of **72** 100m grid polygons, each with `tile_id`, `average_temperature`, `min_temperature`, `max_temperature` ranging `32.6518` to `33.4092 °C`, mean `33.096 °C`, stdev `0.252 °C`) plus `data.result.stats_data`. Credits deducted: `4,220` (`992,880` remaining).
- **Notes / Anomalies:** Confirmed cell-level spatial temperatures ARE returned (feasible for Phase 4 ML!) and credit cost matches documented `4,220` Premium cost. Note that on a single-hour (`filter_type: 1`) query, `min_temperature == average_temperature == max_temperature` per tile.

### Test 14 — MCP Read-Only Checks (`credit_balance` & `heatmap_read`)
- **Timestamp (local):** 2026-11-18T07:26+01:00 (2026-11-18T06:26:42Z)
- **Interface:** MCP (Streamable HTTP)
- **Endpoint / Tool:** `credit_balance`, `heatmap_read` (`activity_id="470b48bb-e48b-4eb6-906e-6980fcfd9420"`)
- **Sanitized Request Parameters:** `{}` for `credit_balance`; `{"activity_id": "470b48bb-e48b-4eb6-906e-6980fcfd9420"}` for `heatmap_read`
- **HTTP Status / MCP Outcome:** `200`, `isError: false` for both
- **Latency (seconds):** `4.748` (init), `5.319` (`credit_balance`, server `latency_ms: 2896`), `2.769` (`heatmap_read`, server `latency_ms: 1366`)
- **Activity ID (if async):** `470b48bb-e48b-4eb6-906e-6980fcfd9420` (reused from Test 13)
- **Observed Response Summary / Sanitized File:** Saved to [mcp_readonly_check.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/mcp_readonly_check.json). `credit_balance` returned `available_credits: 992880`. `heatmap_read` returned `temperature_unit: "celsius"`, `minimum_celsius: 32.6518`, `maximum_celsius: 33.4092`, `mean_celsius: 33.095505555555555`, `standard_deviation_celsius: 0.2520848107278321`, plus `trace` (`cost_credits: 0`).
- **Notes / Anomalies:** Confirmed REST-created `activity_id` works seamlessly in MCP `heatmap_read`. Unlike REST `GET /v1/status/{id}`, MCP returns bounded summary statistics (`structuredContent` + `trace`) and omits the 72-polygon GeoJSON payload.
