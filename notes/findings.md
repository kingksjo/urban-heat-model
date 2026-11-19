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

**F-01 addendum 4 (2026-11-18 ~07:10–07:13 UTC, controlled A/B):** the same free request sent through plain `curl` and our Python client succeeded and failed at random (2 of 9 calls returned `200`, the rest `504` or timeout), with both clients failing in the same rounds and the same request succeeding on one client then failing on the other. This rules out a client-side cause (see Test 18). Backend success rate was roughly 20–30% in this window.

**F-01 addendum 3 (2026-11-18 ~06:42–06:46 UTC):** Test 15 (`POST /v1/satellite`) and 4 consecutive retried `POST /v1/system/fetch-api-key-usage` calls (with 5s/10s/15s backoff) all returned `504 text/plain "upstream request timeout"`, and MCP (`tos-mcp.app.fortyguard.com`) hung at the TLS handshake (`ReadTimeoutError` at `25s`). Across sessions, availability has alternated between healthy responses (`06:10–06:26 UTC`) and multi-minute outages across REST, MCP, and Docs (`22:11–22:19 UTC`, `05:31 UTC` partial, `06:42–06:46 UTC`).

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

### F-08: Async `Failed` jobs return `error: false`, `status_code: 200`, and no diagnostic reason
| Field | Details |
|---|---|
| **Finding** | After `POST /v1/satellite` accepted our Downtown LA payload (`200`), `GET /v1/status/{activity_id}` reported `Processing` for ~2 minutes before transitioning to `Failed` (`124.599s` with `filter_type: 1`; `123.548s` with `filter_type: 3`) with `{"error": false, "status_code": 200, "message": "Failed", "data": {"activity_id": "...", "status": "Failed", "task_id": "..."}}` and **no reason or error detail** (0 credits charged). |
| **Evidence Status** | **Observed** |
| **Category** | Error Handling / Async Workflow / Developer Experience |
| **Evidence** | Tests 19 & 21 in [api-test-log.md](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/notes/api-test-log.md); [satellite_la_20240715_ft3.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/satellite_la_20240715_ft3.json). |
| **Impact** | Developers cannot tell whether a job failed due to missing imagery for the requested date/filter, an invalid parameter combination, or an internal worker failure/timeout—making debugging and automated fallback difficult. Also confirms REST `satellite` is async (contrasting with MCP's direct `satellite` tool). |
| **Severity** | **High** |
| **Recommendation** | Populate a structured `error_code` and human-readable `failure_reason` (e.g., `"no_imagery_for_date"` vs. `"worker_timeout"`) inside `data` when `status` is `"Failed"`. |

### F-09: Contradictions and typos across the live REST documentation and MCP schemas
| Field | Details |
|---|---|
| **Finding** | Direct inspection of the live `docs-api.fortyguard.com` bundle revealed multiple internal inconsistencies and conflicts with MCP tool schemas: (1) `heat_intelligence` docs describe `temperature` as **Fahrenheit** (`82.4`), while the immediately following `date` description says *"Date for the supplied **Celsius** temperature"*; (2) `streetview` REST docs define `vertical_angle` as tilt (up/down) and `horizontal_angle` as pan (0–360), whereas the live MCP `streetview` schema defines `vertical_angle` as heading and `horizontal_angle` as pitch (`÷ 100`); (3) `limitations` requires `polygon_aoi` to be a GeoJSON `FeatureCollection`, while `create-heatmap` examples pass a bare `Polygon`; (4) `satellite` docs document a misspelled `orignal_image` field; (5) `limitations` has a truncated sentence (*"analysis must be a subset of ."*); and (6) `routing` documents structured `data.error.{code, message, retryable}` on `Failed`, whereas `satellite` omitted any `error` object when it failed. |
| **Evidence Status** | **Documented** (extracted directly from `docs-api.fortyguard.com` JS bundle `main.f63c9170caed3b34.js`) & **Observed** (vs. [mcp_tools.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/mcp_tools.json) and Test 19/21) |
| **Category** | Documentation / Schema Consistency / Developer Experience |
| **Evidence** | Live docs pages `/docs/heat-intelligence`, `/docs/street-view-segmentation`, `/docs/satellite-view-segmentation`, `/docs/create-heatmap`, `/docs/routing`, `/docs/limitations`; [mcp_tools.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/mcp_tools.json). |
| **Impact** | Causes integration bugs when developers switch between REST and MCP (especially `streetview` heading/pitch and `heat_intelligence` °F/°C) or rely on `Failed` payloads having a consistent `data.error` object. |
| **Severity** | **High** (for `streetview` angle inversion and `heat_intelligence` unit contradiction) / **Medium** (for `FeatureCollection` vs `Polygon` and doc typos) |
| **Recommendation** | Reconcile REST docs and MCP descriptions from a single source of truth (OpenAPI + shared schema), fix the `Celsius`/`Fahrenheit` typo in `heat_intelligence`, unify `data.error` across all async `Failed` responses, and expose a working `/openapi.json` endpoint. |

### F-10: `satellite` (`granularity=20`) returns `80×80` cropped imagery with missing capture dates and non-urban `others`/`sand`/`sea` labels
| Field | Details |
|---|---|
| **Finding** | When `POST /v1/satellite` succeeded with `granularity=20` at Downtown LA (`34.0522, -118.2437`), it returned an `80×80` `Google Maps Static API` crop showing a single white rooftop/pavement edge (with a cropped Google watermark), `image_year: null`, `image_date: null`, `imagery_date_status: "unavailable"`, and segments `{"earth, ground": 8.61, "sea": 0.83, "sand": 13.97, "others": 76.59}` — with no `building`, `road`, or `vegetation` classes detected. |
| **Evidence Status** | **Observed** |
| **Category** | Data Quality / ML Feasibility / Computer Vision |
| **Evidence** | Test 23 in [api-test-log.md](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/notes/api-test-log.md); [satellite_la_20240715_g20.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/satellite_la_20240715_g20.json) and decoded `80×80` PNGs. |
| **Impact** | `granularity=20` is unsuitable for urban land-cover ML features because 76.6% is uninformative `others`, concrete/shadows are mislabeled as `sand`/`sea`, and imagery capture date is unavailable (preventing temporal alignment with `2024-07-15` heat data). |
| **Severity** | **High** (for ML usability at `20m` and metadata transparency) |
| **Recommendation** | Test whether `granularity=80` produces meaningful urban classes (`building`, `road`, `vegetation`) at `350×350`; otherwise trigger Plan Section 4.7 fallback. For the product, expose urban-tuned segmentation classes and clearly document the `20m` crop's class limitations. |

**F-10 addendum (Test 24, `granularity=80`):** Switching the exact same Downtown LA coordinate to `granularity=80` succeeded in `9.771s` (`350×350` image) and eliminated the `20m` misclassification—returning `road, route: 63.04%`, `building: 22.22%`, `earth, ground: 6.33%`, `tree: 6.22%`, `grass: 2.19%`, and `others: 0.01%` (though `image_year`/`image_date` remained `null`). `granularity=80` is therefore usable for ML features, while `granularity=20` is unsuitable for urban land-cover classification.

### F-11: Unhandled `500` on malformed date/enum input & inconsistent `400`/`422`/`500` validation envelopes
| Field | Details |
|---|---|
| **Finding** | In Phase 2.5 negative testing, missing fields and out-of-range coordinates on `POST /v1/env_params` returned `422` with `detail[]`, unclosed polygons on `POST /v1/heatmap` returned `400` with `field`, and passing `start_date: "2024-99-99"` + `filter_type: 99` to `POST /v1/env_params` caused an **`HTTP 500`** (`"Something went wrong on our side..."`) omitting `status_code` and `field`. |
| **Evidence Status** | **Observed** |
| **Category** | Validation / Error Handling / API Consistency |
| **Evidence** | Test 25 in [api-test-log.md](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/notes/api-test-log.md); [negative_validation_tests.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/negative_validation_tests.json) vs. `/docs/limitations` ("returns `400 Bad Request`"). |
| **Impact** | Clients cannot distinguish a real backend outage (`500`) from their own bad date/enum input, and error-parsing code has to handle three different validation/error shapes (`422` Pydantic, `400` custom, `500` generic). |
| **Severity** | **Medium** |
| **Recommendation** | Validate `date_time` calendar validity and `filter_type` enums at request parsing so malformed dates/enums return `400`/`422` with `field`, and standardize one consistent error envelope across all `4xx`/`5xx` responses. |
