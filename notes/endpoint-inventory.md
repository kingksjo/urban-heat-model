# Phase 1 — Account, Endpoint Inventory & Documentation Questions

> **Note:** Initial entries below marked `[Doc-Search]` were gathered from `docs-api.fortyguard.com` search summaries and must be confirmed directly against each endpoint's live documentation page and your account dashboard before testing.

## 1.1 Account & Access Summary (No Secrets!)

- **Account setup completed:** [x] Yes
- **API key location / management UI:** Provided via FortyGuard account onboarding; stored locally in `.env` (never committed)
- **Local storage:** `.env` (`FORTYGUARD_API_KEY`)
- **Account plan / tier:** `Premium` (`One-Time` cycle, `active: true`, `api_access_available: true`) — **Observed** via `POST /v1/system/fetch-api-key-usage`
- **Available trial credits:** `1,000,000` (`0` used, `1,000,000` remaining)
- **Expiry date / usage limits:** `2026-12-17T00:57:50.656133Z` (`Nov 17, 2026 – Dec 17, 2026`)
- **Included capabilities vs. gated capabilities:** `Premium` tier confirmed active; verify individual endpoints via Phase 2 smoke tests.

---

## 1.2 REST Endpoint Inventory

- **Base URL `[Doc-Search]`:** `https://api.fortyguard.com/v1`
- **Authentication header `[Doc-Search]`:** `api-key: <YOUR_API_KEY>` + `Content-Type: application/json`

| Name & Route `[Doc-Search]` | Purpose | Access Tier | Inputs (Required / Optional) | Outputs | Processing | Credit Cost / Limits `[Doc-Search]` | Doc Clarity / Verification Notes |
|---|---|---|---|---|---|---|---|
| **Environmental Parameters**<br>`POST /v1/env_params` | Point-level atmospheric, hydrological, AQI, thermal stress, and solar irradiance metrics | Basic (up to 3 custom params) & Premium (all params) | **Req:** `latitude`, `longitude`, `temperature` (°C), `date_time` (`start_date`, `filter_type`: 1=Single Hour, 2=Range of Hours, 3=Single Day)<br>**Opt:** `date_time.end_date`, `start_time`, `end_time`, `analysis` (string[]) | Point-level environmental metrics (no `granularity` field) | Verify: REST Quickstart says POST is async via `GET /v1/status/{activity_id}`, whereas MCP treats `env_params` as direct | Basic/Startup: `2,110` credits/req; Premium: `2,900` credits/req | Verify exact meaning of required `temperature` input; confirm sync vs. async on REST |
| **Heatmap**<br>`POST /v1/heatmap` | Hyper-local thermal map over a GeoJSON AOI | Basic & Premium | **Req:** `polygon_aoi` (GeoJSON FeatureCollection/Polygon, `[lon, lat]`), `date_time` (`filter_type` 1–4)<br>**Opt:** `granularity` (`60`, `80`, `100` m; default `100`; 20m in certain layers), `analytic_type` (`tcm`, `time_of_measure`, `exceedance`, `persistence`), `map_type` (`bm`, `tcm`, `tccm`), `threshold` (°C, default 30, used for exceedance/persistence) | `activity_id` -> GeoJSON tiles/polygons + thermal stats | Async (`GET /v1/status/{activity_id}`) | Basic: up to `10 mi²`, `3,500` credits/req; Premium: up to `50 mi²`, `4,220` credits/req. Credits deducted on `Completed`. | Verify whether response includes cell-level temperatures or only area summaries, and exact meaning of `bm`/`tcm`/`tccm` |
| **Heat Intelligence Report**<br>`POST /v1/heat_intelligence` | Multi-dimensional location/property thermal report | API Premium | Verify exact schema on endpoint page | `activity_id` -> temporary download link for PDF/JSON report | Async (`GET /v1/status/{activity_id}`) | Premium: `8,600` credits/req | Verify trial eligibility and signed link expiry |
| **Satellite Segmentation**<br>`POST /v1/satellite` | Semantic segmentation of overhead satellite imagery (land cover/materials) | API Premium | **Req:** `latitude`, `longitude` _(verify additional fields)_ | Class labels, percentages, Base64 imagery, metadata _(verify exact schema)_ | Verify sync vs. async on REST | Premium: `14,400` credits/req | High credit cost! Confirm trial access & credit budget before running; verify if imagery date is returned |
| **Street-View Segmentation**<br>`POST /v1/streetview` | Ground-level street imagery segmentation (facades, vegetation, road, shading) | API Premium | **Req:** `latitude`, `longitude` _(verify additional fields)_ | Front/optional back segmentation classes, coverage metrics | Verify sync vs. async on REST | Premium: `8,600` credits/req | High credit cost! Confirm trial access & behavior where imagery is unavailable |
| **Temperature-Aware Routing**<br>`POST /v1/routing` | Thermal-aware driving route alternatives | API Premium | **Req:** `origin` (`lat`, `lon`), `destination` (`lat`, `lon`), `departure_time` (ISO-8601) | `activity_id` -> route geometry, travel time, thermal metrics | Async (`GET /v1/status/{activity_id}`) | Premium: `3,500` credits/req; max `200 km` straight-line distance | Verify field names on live doc page |
| **Task Status**<br>`GET /v1/status/{activity_id}` | Poll async job status & fetch completed output | All async endpoints | Path param: `activity_id` | `Processing` / `Completed` (+ payload) / `Failed` | Direct GET | No extra cost noted; credits deducted on job completion | Confirm polling interval guidance, TTL of results, and `4xx`/`429` error format |
| **API Credits Usage**<br>`POST /v1/system/fetch-api-key-usage`<br>(`.../fetch-api-key-custom-usage`) | Track API key usage, active subscription tier, and credit balance | All plans | Empty or date-range JSON _(verify exact schema)_ | Subscription tier, credits used/remaining, `credits_reset_date` | Direct POST | Zero credit cost expected | Use as initial Phase 2 connectivity + account-tier verification call |
| **Monitors**<br>`GET/POST/PATCH /v1/monitors` | Manage forecast temperature alert monitors on finished heatmaps | Verify plan | Monitor rules / `monitor_id` | Monitor list, details, alerts | Direct | Verify cost | Out of primary scope unless needed |

---

## 1.3 MCP Tool Inventory

- **Server endpoint `[Observed]`:** `https://tos-mcp.app.fortyguard.com/mcp` (`FortyGuard` v`4.0.11`, `protocolVersion: 2024-11-05`)
- **Transport `[Observed]`:** Remote HTTP / Streamable HTTP (`Content-Type: text/event-stream` SSE response)
- **Authentication `[Observed]`:** `Authorization: Bearer <API_KEY>` (differs from REST `api-key` header)
- **Raw schema capture:** [mcp_tools.json](file:///C:/Users/Kamiye/Desktop/urban-heat%20model/data/raw/mcp_tools.json) (`11` tools discovered)

| Tool Name | Mode & Credit Cost `[Observed in schema]` | Required Inputs | Key Optional Inputs | Output / Notes |
|---|---|---|---|---|
| `credit_balance` | Direct, **free** (read-only) | None (`{}`) | — | Returns `{"available_credits": int}` |
| `env_params` | Direct; `2,110` (Basic/Startup) / `2,900` (Premium) | `latitude`, `longitude`, `temperature` **(°C, caller-supplied ref!)**, `date_time` (`start_date`, `filter_type`: 1–4) | `heatmap_id`, `date_time.end_date/start_time/end_time` (local HH:MM), `analysis` (17 metrics enum) | Calculates `heat_index_celsius` from caller's `temperature` + provider RH; returns apparent/wet-bulb temp, AQI, irradiance |
| `heatmap` | Async; `3,500` (Free/Basic/Startup) / `4,220` (Premium) | `polygon_aoi` (closed GeoJSON Polygon/Feature/FeatureCollection, `[lon, lat]`), `date_time` (local wall time, ≤31 days) | `granularity` (60/80/100m, def 100), `analytic_type` (`tcm`/`time_of_measure`/`exceedance`/`persistence`), `threshold` (°C, def 30), `direction` (`above`/`below`), `idempotency_key`, `map_type` (legacy, ignored) | Returns `status=processing` + `activity_id`; US coverage only |
| `heatmap_read` | Direct read-only (free) | `activity_id` or `heatmap_id` | — | Reads bounded persisted statistics from an existing heatmap |
| `monitoring` | Direct/Action; `list_monitors`/`list_alerts` **free**, others `3,500` credits | `operation` (14 enum values) | `monitor_id`, `alert_id`, `run_id`, `heatmap_id`, `name`, `boundary_geojson`, `rules`, `notifications`, `enabled`, `generate_report`, `file_type`, `cursor`, `limit`, `status` | Rules allow `unit`: `celsius` or `fahrenheit` |
| `report` | Async; `6,300` (Free) / `8,600` (Premium) | `latitude`, `longitude`, `temperature` **(°F!)**, `date` (`YYYY-MM-DD`), `analysis` (1–5: `geographic`, `environmental`, `urban`, `events`, `anthropogenic`; Premium max 2) | `heatmap_id`, `polygon`, `report_polygon`, `selected_heat_intelligence_tile_id`, `date_time`, `granularity`, `notify_by_email` | Note unit switch: asks for **°F**; returns `activity_id` |
| `report_read` | Direct read-only (free) | `analytics_id` (`activity_id` alias) | `heatmap_id` | Reads existing completed Heat Intelligence report |
| `satellite` | Direct; `14,400` (Premium) | `date_time` (plus `sat: {latitude, longitude}` for point requests) | `heatmap_id`, `tiles`, `big_area` (ignored by MCP), `granularity` (60/80/100m radius) | Returns `coordinates`, `image_year`, `segmentation.segments` (0–100% land-cover classes), `image_legend`. MCP omits embedded images. |
| `streetview` | Direct; `8,600` (Premium) | `latitude`, `longitude`, `vertical_angle` (heading °), `horizontal_angle` (0–360; divided by 100 for pitch °), `back_view` (bool) | `heatmap_id`, `date_time` | Returns `coordinates`, `front`/`back` (`segments`, `image_legend`, `image_date`). MCP omits embedded images. |
| `temperature_routing` | Async; `3,500` credits | `origin` (`lat`, `lon`), `destination` (`lat`, `lon`), `departure_time` (ISO-8601) | — | Contiguous US driving roads only; returns `activity_id` |
| `temperature_routing_read` | Direct read-only (free) | `activity_id` | — | Reads existing routing result |

---

## 1.4 Questions to Resolve from Docs & Testing

- [x] **Account check:** `Premium` plan (`One-Time`, valid `2026-11-17` to `2026-12-17`), `1,000,000` credits remaining (`0` used).
- [x] **Meaning of `temperature` in `env_params` vs. `heatmap`:** In `env_params`, `temperature` is a caller-supplied reference temperature (°C) used with provider relative humidity to compute `heat_index_celsius`. In `report`, `temperature` is in **°F**. In `heatmap`, `threshold` is optional (°C, default `30`) for `exceedance`/`persistence`.
- [x] **Timestamps & Timezones (MCP schema):** `env_params`, `heatmap`, `satellite`, and `streetview` treat `start_time`/`end_time` as **local wall time** at the AOI/coordinates (`time_of_measure` outputs UTC hour). Verify whether REST behaves identically.
- [ ] **REST response schemas & units:** Confirm what fields REST `POST /v1/env_params` and `POST /v1/heatmap` return (especially whether `heatmap` returns cell-level temperature values per GeoJSON tile or only summary statistics, and whether REST `env_params` is sync or async).
- [x] **Heatmap options (MCP schema):** `granularity` = `60` / `80` / `100` m; `analytic_type` = `tcm` / `time_of_measure` / `exceedance` / `persistence`; `map_type` (`bm`/`tcm`/`tccm`) is documented as legacy & ignored; `idempotency_key` is supported.
- [ ] **Polygon limits & REST errors:** Confirm `10 mi²` / `50 mi²` limits, minimum polygon area, and validation error formats via REST.
- [ ] **Result persistence:** How long do `activity_id` results and signed report links remain valid?
- [ ] **REST vs. MCP sync/async discrepancy:** Verify whether REST `POST /v1/env_params`, `POST /v1/satellite`, and `POST /v1/streetview` return directly (like MCP) or return an `activity_id` (as REST Quickstart search summary suggested).
- [ ] **Exact REST route for Report:** Confirm `/v1/heat_intelligence` vs. `/v1/report` on REST.
