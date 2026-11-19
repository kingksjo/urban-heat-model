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

### Test 15 — REST Satellite Segmentation Smoke Test (`POST /v1/satellite` — Downtown LA)
- **Timestamp (local):** 2026-11-18T07:42–07:45+01:00 (2026-11-18T06:42–06:45Z)
- **Interface:** REST
- **Endpoint / Tool:** `POST https://api.fortyguard.com/v1/satellite` (plus follow-up `fetch-api-key-usage` x4 with retries)
- **Sanitized Request Parameters:** `{"sat": {"latitude": 34.0522, "longitude": -118.2437}, "date_time": {"start_date": "2024-07-15", "start_time": "14:00", "filter_type": 1}, "granularity": 100}`
- **HTTP Status / MCP Outcome:** `504` (`satellite`) and `504` across all 4 `fetch-api-key-usage` attempts
- **Latency (seconds):** `18.017` (`satellite`)
- **Activity ID (if async):** None returned
- **Observed Response Summary / Sanitized File:** Saved to [satellite_la_20240715.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/satellite_la_20240715.json). Returned `Content-Type: text/plain`, body: `upstream request timeout`.
- **Notes / Anomalies:** Another platform-wide `504` window occurred ~18 minutes after Test 13/14 succeeded cleanly. Even `fetch-api-key-usage` with 3 retries + linear backoff (`5s, 10s, 15s`) failed with `504` throughout the window.

### Test 16 — MCP Availability Check (`credit_balance`)
- **Timestamp (local):** 2026-11-18T07:45–07:46+01:00 (2026-11-18T06:45–06:46Z)
- **Interface:** MCP (Streamable HTTP)
- **Endpoint / Tool:** `POST https://tos-mcp.app.fortyguard.com/mcp` (`initialize`)
- **Sanitized Request Parameters:** `initialize` JSON-RPC (`timeout=25s`)
- **HTTP Status / MCP Outcome:** Client `ReadTimeoutError` during TLS handshake (`_ssl.c:983: The handshake operation timed out`)
- **Latency (seconds):** `>25.0`
- **Activity ID (if async):** N/A
- **Observed Response Summary / Sanitized File:** Connection hung during SSL/TLS handshake.
- **Notes / Anomalies:** Confirms both REST (`api.fortyguard.com`) and MCP (`tos-mcp.app.fortyguard.com`) were simultaneously degraded during the `06:42–06:46 UTC` window.

### Test 17 — Edge vs. Backend Diagnostic & Credits Re-check (`06:53–06:57 UTC`)
- **Timestamp (local):** 2026-11-18T07:53–07:57+01:00 (2026-11-18T06:53–06:57Z)
- **Interface:** REST
- **Endpoint / Tool:** `GET /` (no key via `curl`) and `POST /v1/system/fetch-api-key-usage` (4 retried attempts)
- **Sanitized Request Parameters:** Unauthenticated `GET /`; authenticated `POST /v1/system/fetch-api-key-usage`
- **HTTP Status / MCP Outcome:** `GET /` -> `401` (`2.371s` on `50.18.24.237`); `fetch-api-key-usage` -> `504` (`15.401s` on final attempt)
- **Latency (seconds):** `2.371` (`GET /`), `15.401` (`fetch-api-key-usage`)
- **Activity ID (if async):** N/A
- **Observed Response Summary / Sanitized File:** Edge gateway responded quickly with `401` when no key was passed, while authenticated backend calls continued returning `504 text/plain "upstream request timeout"`.
- **Notes / Anomalies:** Confirms outage window persisted at least `06:42–06:57 UTC` (~15 minutes) at the backend behind the edge proxy.

### Test 18 — Controlled A/B Diagnostic: plain `curl` vs. our Python client (`07:10–07:13 UTC`)
- **Interface:** REST, `POST /v1/system/fetch-api-key-usage` (free), identical headers and body, 3 interleaved rounds
- **Observed:**

| Round | `curl.exe` | Python `requests` (our client headers) | Python + `curl` User-Agent |
|---|---|---|---|
| 1 | `000` (40s timeout) | **`200`** (2.9s) | ReadTimeout (40.9s) |
| 2 | `504` (16.7s) | `504` (16.7s) | **`200`** (2.0s) |
| 3 | `504` (16.3s) | `504` (16.8s) | `504` (16.9s) |

- **Conclusion:** Outcomes are random and independent of the client. Each client both succeeded and failed on the identical request, and `curl` failed in the same rounds as Python. This rules out our headers, body, User-Agent, session reuse, TLS stack and retry code as the cause. Each failure took ~15–17s, which matches a gateway timeout waiting on the backend.

### Test 19 — REST Satellite Segmentation Smoke Test (`POST /v1/satellite` — Downtown LA)
- **Timestamp (local):** 2026-11-18T08:48–08:51+01:00 (2026-11-18T07:48–07:51Z)
- **Interface:** REST
- **Endpoint / Tool:** `POST /v1/satellite` -> `GET /v1/status/f9d10005-83ad-447e-8b49-1f59a4f66e85` (19 polls)
- **Sanitized Request Parameters:** `{"sat": {"latitude": 34.0522, "longitude": -118.2437}, "date_time": {"start_date": "2024-07-15", "start_time": "14:00", "filter_type": 1}, "granularity": 100}`
- **HTTP Status / MCP Outcome:** Submit `200` (`9.031s`, `"Satellite Segmentation Submitted Successfully"`); Status Polling `200` (`Processing` × 18 -> `Failed` on attempt 19 at `124.599s`)
- **Latency (seconds):** `9.031` (submit), `124.599` (total polling until `Failed`)
- **Activity ID (if async):** `f9d10005-83ad-447e-8b49-1f59a4f66e85` (`task_id: 8e3966f1-30e0-4e17-b72d-3e129c175864`)
- **Observed Response Summary / Sanitized File:** Saved to [satellite_la_20240715.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/satellite_la_20240715.json). Final status response was `{"error": false, "status_code": 200, "message": "Failed", "data": {"activity_id": "...", "status": "Failed", "task_id": "..."}}` with **no failure reason**. Credits deducted: **`0`** (`992,880` remaining).
- **Notes / Anomalies:** Confirmed REST `POST /v1/satellite` is **asynchronous** (unlike MCP's direct `satellite` tool) and that failed jobs do not consume credits. However, polling `Processing` for ~2 minutes ended in an opaque `Failed` state without any error code or explanation.

### Test 20 — REST Satellite Retry With `filter_type: 3` (`POST /v1/satellite` — Downtown LA)
- **Timestamp (local):** 2026-11-18T08:54–08:56+01:00 (2026-11-18T07:54–07:56Z)
- **Interface:** REST
- **Endpoint / Tool:** `POST https://api.fortyguard.com/v1/satellite` + follow-up `fetch-api-key-usage`
- **Sanitized Request Parameters:** `{"sat": {"latitude": 34.0522, "longitude": -118.2437}, "date_time": {"start_date": "2024-07-15", "filter_type": 3}, "granularity": 100}`
- **HTTP Status / MCP Outcome:** `504` (`satellite`) and `504` (`fetch-api-key-usage`)
- **Latency (seconds):** `17.209` (`satellite`)
- **Activity ID (if async):** None returned
- **Observed Response Summary / Sanitized File:** Returned `Content-Type: text/plain`, body: `upstream request timeout`. (Note: overwrote `data/raw/satellite_la_20240715.json` before output path was split.)
- **Notes / Anomalies:** Backend entered another `504` window ~6 minutes after Test 19 submitted. Needs re-test during a healthy window.

### Test 21 — REST Satellite Retry With `filter_type: 3` (`POST /v1/satellite` — Downtown LA)
- **Timestamp (local):** 2026-11-18T09:06–09:09+01:00 (2026-11-18T08:06–08:09Z)
- **Interface:** REST
- **Endpoint / Tool:** `POST /v1/satellite` -> `GET /v1/status/859f718e-b7b4-41a6-adb9-b93afaf661f8` (20 polls)
- **Sanitized Request Parameters:** `{"sat": {"latitude": 34.0522, "longitude": -118.2437}, "date_time": {"start_date": "2024-07-15", "filter_type": 3}, "granularity": 100}`
- **HTTP Status / MCP Outcome:** Submit `200` (`8.321s`); Status Polling `200` (`Processing` × 19 -> `Failed` on attempt 20 at `123.548s`)
- **Latency (seconds):** `8.321` (submit), `123.548` (total polling until `Failed`)
- **Activity ID (if async):** `859f718e-b7b4-41a6-adb9-b93afaf661f8`
- **Observed Response Summary / Sanitized File:** Saved to [satellite_la_20240715_ft3.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/satellite_la_20240715_ft3.json). Same opaque `Failed` payload (`error: false`, `status_code: 200`, `status: "Failed"`, `task_id`, no reason). Credits deducted: **`0`** (`992,880` remaining).
- **Notes / Anomalies:** Reproducible failure right around ~124s (`124.599s` on Test 19 vs. `123.548s` on Test 21), suggesting an internal ~120s worker timeout or systematic `satellite` worker failure on this input.

### Test 22 — REST Satellite Retry With `granularity: 20` (`POST /v1/satellite` — Downtown LA)
- **Timestamp (local):** 2026-11-18T09:20–09:21+01:00 (2026-11-18T08:20–08:21Z)
- **Interface:** REST
- **Endpoint / Tool:** `POST https://api.fortyguard.com/v1/satellite` + follow-up `fetch-api-key-usage`
- **Sanitized Request Parameters:** `{"sat": {"latitude": 34.0522, "longitude": -118.2437}, "date_time": {"start_date": "2024-07-15", "filter_type": 3}, "granularity": 20}`
- **HTTP Status / MCP Outcome:** `504` (`satellite`) and `504` (`fetch-api-key-usage`)
- **Latency (seconds):** `17.998` (`satellite`)
- **Activity ID (if async):** None returned
- **Observed Response Summary / Sanitized File:** Saved to [satellite_la_20240715_g20.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/satellite_la_20240715_g20.json). Returned `Content-Type: text/plain`, body: `upstream request timeout`.
- **Notes / Anomalies:** Backend entered another `504` window; retry once `check_account` returns `200`.

### Test 23 — REST Satellite Segmentation (`granularity: 20` — Downtown LA)
- **Timestamp (local):** 2026-11-18T10:52–10:53+01:00 (2026-11-18T09:52–09:53Z)
- **Interface:** REST
- **Endpoint / Tool:** `POST /v1/satellite` -> `GET /v1/status/562be909-9066-4b42-8033-0a652d79dc04` (5 polls)
- **Sanitized Request Parameters:** `{"sat": {"latitude": 34.0522, "longitude": -118.2437}, "date_time": {"start_date": "2024-07-15", "filter_type": 3}, "granularity": 20}`
- **HTTP Status / MCP Outcome:** Submit `200` (`4.707s`); Status Polling `200` (`Processing` × 4 -> `Completed` on attempt 5 in `26.367s`)
- **Latency (seconds):** `4.707` (submit), `26.367` (total polling to `Completed`)
- **Activity ID (if async):** `562be909-9066-4b42-8033-0a652d79dc04`
- **Observed Response Summary / Sanitized File:** Saved to [satellite_la_20240715_g20.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/satellite_la_20240715_g20.json). Returned `80x80` crop from `Google Maps Static API`, `image_year: null`, `image_date: null`, `imagery_date_status: "unavailable"`, `imagery_retrieved_at: "2026-11-18T09:52:31.227916+00:00"`, and `segments`: `{"earth, ground": 8.61, "sea": 0.83, "sand": 13.97, "others": 76.59}`. Credits deducted: `14,400` (`978,480` remaining).
- **Notes / Anomalies:** Inspecting the decoded `80x80` PNGs shows a tight rooftop + shadow crop with a cropped Google watermark; the model labeled Downtown LA roofs/pavement/shadows as `others` (`76.59%`), `sand` (`13.97%`), `earth, ground` (`8.61%`), and `sea` (`0.83%`), with zero `building`, `road`, or `vegetation` classes and no capture date.

### Test 24 — REST Satellite Segmentation (`granularity: 80` — Downtown LA)
- **Timestamp (local):** 2026-11-18T11:57–11:58+01:00 (2026-11-18T10:57–10:58Z)
- **Interface:** REST
- **Endpoint / Tool:** `POST /v1/satellite` -> `GET /v1/status/b09f9fa5-17e5-4a9e-b126-169bccd396e9` (2 polls)
- **Sanitized Request Parameters:** `{"sat": {"latitude": 34.0522, "longitude": -118.2437}, "date_time": {"start_date": "2024-07-15", "filter_type": 3}, "granularity": 80}`
- **HTTP Status / MCP Outcome:** Submit `200` (`4.088s`); Status Polling `200` (`Processing` -> `Completed` on attempt 2 in `9.771s`)
- **Latency (seconds):** `4.088` (submit), `9.771` (total polling to `Completed`)
- **Activity ID (if async):** `b09f9fa5-17e5-4a9e-b126-169bccd396e9`
- **Observed Response Summary / Sanitized File:** Saved to [satellite_la_20240715_g80.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/satellite_la_20240715_g80.json) and decoded PNGs [satellite_g80_orig.png](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/report/figures/satellite_g80_orig.png) / [satellite_g80_seg.png](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/report/figures/satellite_g80_seg.png). Returned `350x350` imagery from `Google Maps Static API`, `image_year: null`, `image_date: null`, `imagery_date_status: "unavailable"`, and clean urban `segments`: `{"building": 22.22, "tree": 6.22, "road, route": 63.04, "grass": 2.19, "earth, ground": 6.33, "others": 0.01}`. Credits deducted: `14,400` (`964,080` remaining).
- **Notes / Anomalies:** `granularity: 80` produced high-quality `350x350` urban segmentation (only `0.01%` `others`), passing the Phase 4.1 ML feasibility gate for land-cover features (with the documented caveat that `image_date` is unavailable).

### Test 25 — Phase 2.5 Safe Negative Validation Suite (0 Credits)
- **Timestamp (local):** 2026-11-19T18:34+01:00 (2026-11-19T17:34:26Z)
- **Interface:** REST
- **Endpoint / Tool:** `POST /v1/env_params` (3 cases) & `POST /v1/heatmap` (1 case)
- **Sanitized Request Parameters:** (1) missing `temperature` & `date_time`; (2) `latitude: 95.0, longitude: -200.0`; (3) `start_date: "2024-99-99", filter_type: 99`; (4) 3-point unclosed `Polygon`
- **HTTP Status / MCP Outcome:** (1) `422` (`2.633s`); (2) `422` (`0.804s`); (3) **`500`** (`1.980s`); (4) `400` (`1.390s`)
- **Latency (seconds):** `0.804`–`2.633`
- **Activity ID (if async):** N/A
- **Observed Response Summary / Sanitized File:** Saved to [negative_validation_tests.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/negative_validation_tests.json). Cases 1, 2 (`422`), and 4 (`400`) returned clear field-level messages. Case 3 (`start_date: "2024-99-99", filter_type: 99`) triggered an unhandled **`500`** (`"Something went wrong on our side..."`) without `status_code` or `field`.
- **Notes / Anomalies:** `0` credits consumed. Confirms a server-side `500` crash on malformed date/enum input and inconsistent status codes (`422` vs `400` vs documented `400`).

### Test 26 — MCP `env_params` Execution & REST-vs-MCP Comparison (Downtown LA)
- **Timestamp (local):** 2026-11-19T18:38+01:00 (2026-11-19T17:38:56Z)
- **Interface:** MCP (Streamable HTTP)
- **Endpoint / Tool:** `env_params`
- **Sanitized Request Parameters:** `{"latitude": 34.0522, "longitude": -118.2437, "temperature": 30.0, "date_time": {"start_date": "2024-07-15", "start_time": "14:00", "filter_type": 1}}`
- **HTTP Status / MCP Outcome:** `200`, `isError: false`
- **Latency (seconds):** `2.742` (init), `8.449` (`env_params`, server `latency_ms: 6628`)
- **Activity ID (if async):** `48203131-b96f-414c-bc42-cd42da3ddb66` (handled internally by MCP)
- **Observed Response Summary / Sanitized File:** Saved to [mcp_env_params_la.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/mcp_env_params_la.json). Returned identical values to REST Test 11 (`apparent_temperature_celsius: 29.9`, `relative_humidity_percent: 42.6`, `wet_bulb_temperature_celsius: 20.3`, `aqi_us: 62.2`, `ghi: 908.63`), with `value.parameters` normalized to clean snake_case (`aqi_us`, `elevation_meters`) alongside `value.raw`, `evidence`, and `trace` (`cost_credits: 2900`).
- **Notes / Anomalies:** Confirmed MCP wraps REST `/env_params` async polling into a single synchronous tool call and normalizes AQI/elevation keys in `value.parameters`.

### Test 27 — REST Temperature-Aware Routing (`POST /v1/routing` — Downtown LA to Griffith Park)
- **Timestamp (local):** 2026-11-19T18:39–18:40+01:00 (2026-11-19T17:39–17:40Z)
- **Interface:** REST
- **Endpoint / Tool:** `POST /v1/routing` -> `GET /v1/status/cff11fe1-e363-4db7-aad3-ec7bffc30d4f` (5 polls)
- **Sanitized Request Parameters:** `origin: {34.0522, -118.2437}`, `destination: {34.1184, -118.3004}`, `departure_time: "2024-07-15T14:00:00-07:00"`
- **HTTP Status / MCP Outcome:** Submit `200` (`5.709s`); Status Polling `200` (`Processing` × 4 -> `Completed` in `30.144s`)
- **Latency (seconds):** `5.709` (submit), `30.144` (total polling to `Completed`)
- **Activity ID (if async):** `cff11fe1-e363-4db7-aad3-ec7bffc30d4f`
- **Observed Response Summary / Sanitized File:** Saved to [routing_la_20240715.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/routing_la_20240715.json). Returned 1 route (`12.996 km`, `13.6 min`, `mean_c: 38.521`, `peak_c: 39.09`, `no_cooling_available: True`).
- **Notes / Anomalies:** `0` credits deducted in the immediate `fetch-api-key-usage` check (`961,180` remaining, vs. documented `3,500`).

### Test 28 — REST Street-View Segmentation (`POST /v1/streetview` — Downtown LA)
- **Timestamp (local):** 2026-11-19T18:40+01:00 (2026-11-19T17:40Z)
- **Interface:** REST
- **Endpoint / Tool:** `POST /v1/streetview` -> `GET /v1/status/d793acf5-1827-4bfd-97b5-c4d87064cf63` (2 polls)
- **Sanitized Request Parameters:** `latitude: 34.0522, longitude: -118.2437, vertical_angle: 10.0, horizontal_angle: 90.0, back_view: false`
- **HTTP Status / MCP Outcome:** Submit `200` (`3.528s`); Status Polling `200` (`Processing` -> `Completed` in `14.822s`)
- **Latency (seconds):** `3.528` (submit), `14.822` (total polling to `Completed`)
- **Activity ID (if async):** `d793acf5-1827-4bfd-97b5-c4d87064cf63`
- **Observed Response Summary / Sanitized File:** Saved to [streetview_la_20240715.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/streetview_la_20240715.json). Returned `image_date: "2026-06-01"` and `segments`: `{"sky": 11.15, "tree": 55.53, "road": 29.49, "earth": 3.22, "others": 0.61}`. Credits deducted: `8,600` (`952,580` remaining).
- **Notes / Anomalies:** Confirmed REST `streetview` is **asynchronous** (unlike MCP's direct `streetview` tool) and returns an explicit `image_date` (`2026-06-01`).

### Test 29 — REST Heat Intelligence Report (`POST /v1/heat_intelligence` — Downtown LA)
- **Timestamp (local):** 2026-11-19T18:40–18:43+01:00 (2026-11-19T17:40–17:43Z)
- **Interface:** REST
- **Endpoint / Tool:** `POST /v1/heat_intelligence` -> `GET /v1/status/2c342194-a432-4d72-a382-83a996d8cefb` (26 polls)
- **Sanitized Request Parameters:** `latitude: 34.0522, longitude: -118.2437, temperature: 91.6, date: "2024-07-15", analysis: ["environmental"]`
- **HTTP Status / MCP Outcome:** Submit `200` (`2.818s`); Status Polling `200` (`Processing` × 25 -> `Completed` in `157.309s`)
- **Latency (seconds):** `2.818` (submit), `157.309` (total polling to `Completed`)
- **Activity ID (if async):** `2c342194-a432-4d72-a382-83a996d8cefb`
- **Observed Response Summary / Sanitized File:** Saved to [heat_intelligence_la_20240715.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/heat_intelligence_la_20240715.json) with `download_link` redacted (`[REDACTED_SIGNED_URL]`). Credits deducted: `8,600` (`943,980` remaining).
- **Notes / Anomalies:** Report generation took ~2.6 minutes as documented; `download_link` was present on completion.

### Test 30 — MCP Async `heatmap` + `heatmap_read` & REST GeoJSON Retrieval (Griffith Park, LA)
- **Timestamp (local):** 2026-11-19T18:50+01:00 (2026-11-19T17:50:47Z)
- **Interface:** MCP (`heatmap`, `heatmap_read`, `credit_balance`) + REST (`GET /v1/status/{id}`)
- **Endpoint / Tool:** `heatmap` -> `heatmap_read` (3 polls) -> `GET /v1/status/3840fee2-56ad-4e68-be94-e98da30019c9`
- **Sanitized Request Parameters:** ~0.8 km² Griffith Park `FeatureCollection` (`[-118.305, 34.128]` to `[-118.295, 34.136]`), `2024-07-15 14:00` (`filter_type: 1`), `granularity: 100`, `analytic_type: "tcm"`, `idempotency_key: "griffith-mcp-20240715-v1"`
- **HTTP Status / MCP Outcome:** `200`, `isError: false`; `processing` × 2 -> `completed` in `21.671s`; REST status `200` (`5.514s`)
- **Latency (seconds):** `2.830` (MCP submit), `21.671` (MCP polling), `5.514` (REST GeoJSON fetch)
- **Activity ID (if async):** `3840fee2-56ad-4e68-be94-e98da30019c9`
- **Observed Response Summary / Sanitized File:** Saved to [mcp_heatmap_griffith_20240715.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/mcp_heatmap_griffith_20240715.json) and [heatmap_griffith_20240715.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/heatmap_griffith_20240715.json) (**81** GeoJSON tiles). Griffith Park temp: `28.61` to `30.63 °C` (mean `29.70 °C`, stdev `0.66 °C`) vs. Downtown LA mean `33.10 °C` at the same hour. MCP `credit_balance`: `936,260` (`4,220` for heatmap + delayed `3,500` settlement from Test 27 `routing`).
- **Notes / Anomalies:** Confirms bidirectional REST/MCP `activity_id` interoperability (`heatmap` submitted via MCP can be fetched as full GeoJSON via REST). Phase 3 is now 100% complete.
