# Evaluation Findings

> Label every important claim as **Documented**, **Observed**, **Inferred**, or **Not tested**.

## Finding Template

| Field | Details |
|---|---|
| **Finding** | _One clear observation_ |
| **Evidence Status** | _Documented / Observed / Inferred / Not tested_ |
| **Category** | _UX, API design, docs, reliability, MCP, data, scalability, etc._ |
| **Evidence** | _Endpoint/tool, request/activity ID, sanitized response, timing, screenshot_ |
| **Impact** | _Why it matters to a developer or end user_ |
| **Severity** | _High / Medium / Low_ |
| **Recommendation** | _Specific, actionable improvement_ |

---

## Recorded Findings

### F-01: Simultaneous `504 upstream request timeout` across REST, MCP, and Docs hosts
| Field | Details |
|---|---|
| **Finding** | All tested FortyGuard REST endpoints (`POST /v1/system/fetch-api-key-usage`, `GET /v1/monitors`, `POST /v1/env_params`), the MCP server (`POST https://tos-mcp.app.fortyguard.com/mcp`), and the documentation site (`docs-api.fortyguard.com`) timed out during testing on 2026-11-17 between `22:11 UTC` and `22:19 UTC`. |
| **Evidence Status** | **Observed** |
| **Category** | Reliability / Error Handling / Availability |
| **Evidence** | See Tests 1–7 in [api-test-log.md](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/notes/api-test-log.md): 5 REST calls returned `504` (`Content-Type: text/plain`, body `upstream request timeout`) in `15.520s`–`18.304s`; MCP `initialize` returned `504` `text/plain` `upstream request timeout`; `docs-api.fortyguard.com/docs/quickstart` hit a `15s` `ReadTimeoutError`. |
| **Impact** | Blocks all API/MCP workflows and documentation access during the window; additionally, clients expecting JSON error bodies receive `text/plain` (`upstream request timeout`) on gateway timeouts, which can break strict JSON parsers if not guarded. |
| **Severity** | **High** (for availability during window) / **Medium** (for non-JSON gateway error response format) |
| **Recommendation** | Publish a public status page or health endpoint, ensure gateway timeouts return structured JSON (`{"error": ..., "code": 504}`) when `Accept`/`Content-Type` is `application/json`, and document recommended client retry/backoff behavior for `504` responses. |

**F-01 addendum (2026-11-18 ~05:31 UTC):** after the API recovered, the docs host was still unstable: `docs-api.fortyguard.com/docs/` returned `200` (20.7s, SPA shell only), while `/docs/quickstart`, `/llms.txt`, `/openapi.json` and `api.fortyguard.com/openapi.json` returned `503 text/plain "no healthy upstream"` (Envoy-style proxy message). Unauthenticated GETs failed too, so the cause is server-side. Also observed: intermittent `504` vs `503`, both as `text/plain`. No public OpenAPI spec was reachable.

**F-01 addendum 2 (2026-11-18 ~06:20 UTC):** Even after Test 11 (`POST /v1/env_params`) succeeded (`10.182s` just to return `activity_id`), Test 12 (`POST /v1/heatmap`) hit `504 text/plain "upstream request timeout"` at `17.755s`. The ~15–18s edge gateway timeout appears tight relative to slow submit handlers (10s+) and intermittent backend stalls.

### F-02: Credential handling inconsistency & raw key echo on `POST /v1/system/fetch-api-key-usage`
| Field | Details |
|---|---|
| **Finding** | `POST /v1/system/fetch-api-key-usage` rejects requests that only pass the `api-key` header (`422 Field 'api_key' is required` in `body.api_key`) and, when supplied in the JSON body, echoes the full `api_key` string back in the `200` response payload. |
| **Evidence Status** | **Observed** |
| **Category** | API Design / Security / Developer Experience |
| **Evidence** | Tests 8 & 9 in [api-test-log.md](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/notes/api-test-log.md); sanitized output in [account_usage.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/account_usage.json). |
| **Impact** | Forces callers to pass the secret in both a header (`api-key`, hyphenated) and JSON body (`api_key`, underscored), and increases risk of accidental credential leakage in application logs or saved response payloads. |
| **Severity** | **Medium** |
| **Recommendation** | Authenticate `fetch-api-key-usage` solely via the standard `api-key` header (or make `body.api_key` optional for multi-key admin lookups) and mask the returned `api_key` (e.g., prefix/last-4 characters) in responses. |

### F-03: Inconsistent temperature units & confusing Street View angle parameter naming in MCP schemas
| Field | Details |
|---|---|
| **Finding** | Across the live MCP tool schemas, `env_params` and `heatmap` expect temperature inputs in Celsius (°C), whereas `report` requires `temperature` in Fahrenheit (°F) and `monitoring` supports choosing `"celsius"` or `"fahrenheit"`. Additionally, `streetview` names the compass heading parameter `vertical_angle` and the pitch parameter `horizontal_angle` (0–360, which the engine divides by 100 so `100` becomes `1°`). |
| **Evidence Status** | **Observed** (in MCP `tools/list` schema) |
| **Category** | API Design / MCP / Developer Experience |
| **Evidence** | [mcp_tools.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/mcp_tools.json) (`env_params`, `heatmap`, `monitoring`, `report`, `streetview` schemas). |
| **Impact** | Easy for developers or LLM agents chaining tools (e.g., passing an `env_params` °C value directly into `report`, or passing normal pitch/heading degrees into `streetview`) to silently supply wrong units or camera angles. |
| **Severity** | **Medium** |
| **Recommendation** | Standardize on Celsius (or accept an explicit `unit` field consistently across `env_params`, `heatmap`, and `report`), and introduce clear aliases (`heading_deg`, `pitch_deg`) alongside the legacy `vertical_angle`/`horizontal_angle` fields. |

### F-04: `env_params` requires caller-supplied temperature & `heatmap` carries legacy ignored `map_type`
| Field | Details |
|---|---|
| **Finding** | `env_params` requires a caller-supplied `temperature` (°C) to compute `heat_index_celsius` alongside provider-sourced apparent/wet-bulb temperatures, rather than returning FortyGuard's own LTM air temperature directly. Meanwhile, `heatmap` accepts `map_type` (`bm`/`tcm`/`tccm`) only as an ignored legacy compatibility parameter in favor of `analytic_type`. |
| **Evidence Status** | **Observed** (in MCP `tools/list` schema) |
| **Category** | API Design / Documentation / ML Feasibility |
| **Evidence** | [mcp_tools.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/mcp_tools.json) (`env_params` and `heatmap` descriptions/schemas). |
| **Impact** | Important for downstream modeling: using `env_params` `heat_index_celsius` against the caller's own `temperature` input would create target leakage or trivial identity if misunderstood; `heatmap` (or provider-sourced `apparent_temperature_celsius`/`wet_bulb_temperature_celsius`) must be inspected first before choosing an ML target. |
| **Severity** | **Low** (UX/docs clarity) / **High** (for correct ML target selection) |
| **Recommendation** | Clearly separate `env_params` ("ambient weather/AQI enrichment given a reference temp") from `heatmap` ("FortyGuard LTM temperature grid") in top-level docs, and deprecate `map_type` cleanly in the schema. |

### F-05: REST `POST /v1/env_params` is asynchronous with nested `data.activity_id` (and no initial `status` field)
| Field | Details |
|---|---|
| **Finding** | Unlike MCP (which exposes `env_params` as a direct single-call tool), REST `POST /v1/env_params` runs asynchronously: it returns `HTTP 200` after `10.182s` with `{"data": {"activity_id": "..."}}` and no `status` field; the caller must then poll `GET /v1/status/{activity_id}`, where `status` (`"Completed"`) and `result` are nested under `data`. |
| **Evidence Status** | **Observed** |
| **Category** | API Design / REST vs. MCP / Developer Experience |
| **Evidence** | Test 11 in [api-test-log.md](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/notes/api-test-log.md); [env_params_la_20240715.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/env_params_la_20240715.json) and [env_params_la_20240715_result.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/env_params_la_20240715_result.json). |
| **Impact** | Developers switching between MCP and REST—or writing generic polling clients expecting top-level `activity_id`/`status` fields—must inspect nested `data` keys and handle async polling for REST `env_params` despite its 10s submit latency. |
| **Severity** | **Medium** |
| **Recommendation** | Document the exact `{data: {activity_id}}` submit envelope and `{data: {status, result}}` status envelope clearly, and consider returning `202 Accepted` with an initial `status: "processing"` field on REST async submissions. |

### F-06: Inconsistent AQI field naming and `null` greenhouse-gas values in `env_params` output
| Field | Details |
|---|---|
| **Finding** | In the `POST /v1/env_params` result for Downtown Los Angeles (`2024-07-15 14:00`), `locations[0].parameters` mixes two naming conventions (`air_quality:idx`, `air_quality_pm2p5:idx`, `air_quality_pm10:idx`, `air_quality_no2:idx`, `air_quality_o3:idx`, `air_quality_so2:idx` with colons vs. `aqi_us_co` with underscores), differing from the `aqi_us_*` enum names in the MCP `env_params` schema. Additionally, `methane_ppb` and `co2_ppm` both returned `[null]`. |
| **Evidence Status** | **Observed** |
| **Category** | Data Quality / Schema Consistency |
| **Evidence** | [env_params_la_20240715_result.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/env_params_la_20240715_result.json) vs. `AnalysisField` enum in [mcp_tools.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/mcp_tools.json). |
| **Impact** | Downstream pipelines mapping `analysis` request names directly to output keys will fail on all AQI keys except `aqi_us_co`, and ML/analytics code must explicitly guard against `null` values for `methane_ppb`/`co2_ppm`. |
| **Severity** | **Medium** |
| **Recommendation** | Align output field names with the documented `analysis` enum (`aqi_us`, `aqi_us_pm25`, etc.) and document expected coverage/nullability for greenhouse-gas parameters. |

### F-07: Strong MCP ergonomics (`structuredContent`, `trace`, cross-interface `activity_id`) and intentional GeoJSON omission in `heatmap_read`
| Field | Details |
|---|---|
| **Finding** | MCP `credit_balance` and `heatmap_read` return both text and `structuredContent` alongside a `trace` block (`trace_id`, `plan_type`, `latency_ms`, `cost_credits`), and `heatmap_read` successfully reads an `activity_id` originally created via REST `POST /v1/heatmap` while returning bounded summary statistics (explicit `temperature_unit: "celsius"`, min/max/mean/std) instead of raw GeoJSON polygons. |
| **Evidence Status** | **Observed** |
| **Category** | MCP / Strengths / REST-vs-MCP Comparison |
| **Evidence** | Test 14 in [api-test-log.md](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/notes/api-test-log.md); [mcp_readonly_check.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/mcp_readonly_check.json) vs. [heatmap_la_20240715.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/heatmap_la_20240715.json). |
| **Impact** | **Positive for AI agents:** prevents context-window overflow and gives agents transparent credit/latency telemetry and explicit units (`celsius`). **Tradeoff for ML pipelines:** REST `GET /v1/status/{id}` must still be used to extract tile-level GeoJSON geometries and temperatures. |
| **Severity** | **Low** (Strength / Design Tradeoff) |
| **Recommendation** | Keep bounded summaries as the default in MCP `heatmap_read`, and document explicitly that REST is required when callers need full per-tile GeoJSON geometries. |
