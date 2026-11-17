# Phase 1 — Account, Endpoint Inventory & Documentation Questions

> **Note:** Initial entries below marked `[Doc-Search]` were gathered from `docs-api.fortyguard.com` search summaries and must be confirmed directly against each endpoint's live documentation page and your account dashboard before testing.

## 1.1 Account & Access Summary (No Secrets!)

- **Account setup completed:** [ ] Yes / [ ] No
- **API key location / management UI:** _TBD (never paste the key itself)_
- **Local storage:** `.env` (`FORTYGUARD_API_KEY`)
- **Account plan / tier:** _TBD (check Basic vs. Premium vs. Trial)_
- **Available trial credits:** _TBD_
- **Expiry date / usage limits:** _TBD_
- **Included capabilities vs. gated capabilities:** _TBD_

---

## 1.2 REST Endpoint Inventory

- **Base URL `[Doc-Search]`:** `https://api.fortyguard.com/v1`
- **Authentication header `[Doc-Search]`:** `api-key: <YOUR_API_KEY>` + `Content-Type: application/json`

| Name & Route `[Doc-Search]` | Purpose | Access Tier | Inputs (Required / Optional) | Outputs | Processing | Credit Cost / Limits `[Doc-Search]` | Doc Clarity / Verification Notes |
|---|---|---|---|---|---|---|---|
| **Environmental Parameters**<br>`POST /v1/env_params` | Point-level atmospheric, hydrological, AQI, thermal stress, and solar irradiance metrics | Basic (up to 3 custom params) & Premium (all params) | **Req:** `latitude`, `longitude`, `temperature` (°C), `date_time` (`start_date`, `filter_type`: 1=Single Hour, 2=Range of Hours, 3=Single Day)<br>**Opt:** `date_time.end_date`, `start_time`, `end_time`, `analysis` (string[]) | Point-level environmental metrics (no `granularity` field) | Verify: REST Quickstart says POST is async via `GET /v1/status/{activity_id}`, whereas MCP treats `env_params` as direct | Basic/Startup: `2,110` credits/req; Premium: `2,900` credits/req | Verify exact meaning of required `temperature` input; confirm sync vs. async on REST |
| **Heatmap**<br>`POST /v1/heatmap` | Hyper-local thermal map over a GeoJSON AOI | Basic & Premium | **Req:** `polygon_aoi` (GeoJSON FeatureCollection/Polygon, `[lon, lat]`), `date_time` (`filter_type` 1–4)<br>**Opt:** `granularity` (`60`, `80`, `100` m; default `100`; 20m in certain layers), `analytic_type` (`tcm`, `time_of_measure`, `exceedance`, `persistence`), `map_type` (`bm`, `tcm`, `tccm`), `threshold` (°C, default 30, used for exceedance/persistence) | `activity_id` -> GeoJSON tiles/polygons + thermal stats | Async (`GET /v1/status/{activity_id}`) | Basic: up to `10 mi²`, `3,500` credits/req; Premium: up to `50 mi²`, `4,220` credits/req. Credits deducted on `Completed`. | Verify whether response includes cell-level temperatures or only area summaries, and exact meaning of `bm`/`tcm`/`tccm` |
| **Heat Intelligence Report**<br>`POST /v1/report` or `POST /v1/heat-intelligence` _(verify exact path)_ | Multi-dimensional location/property thermal report | API Premium | Verify exact schema on endpoint page | `activity_id` -> temporary download link for PDF/JSON report | Async (`GET /v1/status/{activity_id}`) | Premium: `8,600` credits/req | Verify exact route name, trial eligibility, and signed link expiry |
| **Satellite Segmentation**<br>`POST /v1/satellite` | Semantic segmentation of overhead satellite imagery (land cover/materials) | API Premium | **Req:** `latitude`, `longitude` _(verify additional fields)_ | Class labels, percentages, metadata _(verify exact schema)_ | Verify sync vs. async on REST | Premium: `14,400` credits/req | High credit cost! Confirm trial access & credit budget before running; verify if imagery date is returned |
| **Street-View Segmentation**<br>`POST /v1/streetview` | Ground-level street imagery segmentation (facades, vegetation, road, shading) | API Premium | **Req:** `latitude`, `longitude` _(verify additional fields)_ | Segmentation classes, imagery/artifacts _(verify exact schema)_ | Verify sync vs. async on REST | Premium: `8,600` credits/req | High credit cost! Confirm trial access & behavior where imagery is unavailable |
| **Temperature-Aware Routing**<br>`POST /v1/routing` _(verify path vs. `temperature_routing`)_ | Thermal-aware driving route alternatives | API Premium | **Req:** `origin` (`lat`, `lon`), `destination` (`lat`, `lon`), `departure_time` (ISO-8601) | `activity_id` -> route geometry, travel time, thermal metrics | Async (`GET /v1/status/{activity_id}`) | Premium: `3,500` credits/req; max `200 km` straight-line distance | Verify exact route path and field names on live doc page |
| **Task Status**<br>`GET /v1/status/{activity_id}` | Poll async job status & fetch completed output | All async endpoints | Path param: `activity_id` | `Processing` / `Completed` (+ payload) / `Failed` | Direct GET | No extra cost noted; credits deducted on job completion | Confirm polling interval guidance, TTL of results, and `4xx`/`429` error format |

---

## 1.3 MCP Tool Inventory

- **Server endpoint `[Documented]`:** `https://tos-mcp.app.fortyguard.com/mcp`
- **Transport `[Documented]`:** Remote HTTP / Streamable HTTP
- **Authentication `[Documented]`:** `Authorization: Bearer <API_KEY>` (differs from REST `api-key` header)

| Tool Name | Mode `[Documented in plan]` | Required Inputs | Optional Inputs | Output Structure | Notes |
|---|---|---|---|---|---|
| `env_params` | Direct | _Verify via MCP schema discovery_ | | | Compare against `POST /v1/env_params` |
| `satellite` | Direct | _Verify via MCP schema discovery_ | | | High credit cost if Premium-gated |
| `streetview` | Direct | _Verify via MCP schema discovery_ | | | High credit cost if Premium-gated |
| `heatmap` / `heatmap_read` | Async submit + read tool | _Verify via MCP schema discovery_ | | | Compare against `POST /v1/heatmap` + `GET /v1/status/{id}` |
| `report` / `report_read` | Async submit + read tool | _Verify via MCP schema discovery_ | | | Test only if credits/plan permit |
| `temperature_routing` / `temperature_routing_read` | Async submit + read tool | _Verify via MCP schema discovery_ | | | Test only if credits/plan permit |

---

## 1.4 Questions to Resolve from Docs & Testing

- [ ] **Account check:** What plan tier, credit balance, and expiry does your trial account actually have? Given credit costs (`2,110`–`14,400` credits/call in docs), how many total calls can the trial budget support?
- [ ] **Meaning of `temperature` in `POST /v1/env_params`:** Docs list `temperature` (°C) as a required input — is this an observed reference temperature you supply, a baseline, or a threshold? (In `heatmap`, `threshold` is documented as optional in °C defaulting to `30` for `exceedance`/`persistence`.)
- [ ] **Timestamps & Timezones:** Standard heatmaps and `time_of_measure` are documented as **UTC**, while 20m resolution maps to **local AOI timezone** — verify what `env_params` and `date_time` inputs expect (UTC vs. local) and what timestamps are returned.
- [ ] **Units:** Confirm whether temperature is always °C across all endpoints/responses and whether units are explicitly stated in JSON responses.
- [ ] **Heatmap options:** Confirm exact definitions of `granularity` (`60`, `80`, `100`, `20`), `analytic_type` (`tcm`, `time_of_measure`, `exceedance`, `persistence`), and `map_type` (`bm`, `tcm`, `tccm`), and how each affects credit consumption and payload size.
- [ ] **Polygon limits & coordinates:** Basic (`10 mi²`) vs. Premium (`50 mi²`) documented — check minimum area, vertex limits, and GeoJSON coordinate order (`[lon, lat]`).
- [ ] **Retries, timeouts, rate limits, idempotency:** Check documented `429` limits, timeout behavior, and whether duplicate payloads return a cached job or consume new credits.
- [ ] **Result persistence:** How long do `activity_id` results and signed report links remain valid?
- [ ] **REST vs. MCP sync/async discrepancy:** Confirm whether REST `env_params` returns directly or returns an `activity_id` (since Quickstart says POSTs are async, while MCP classifies `env_params`, `satellite`, `streetview` as direct).
- [ ] **Exact routes:** Verify `/v1/report` vs. `/v1/heat-intelligence` and `/v1/routing` vs. `/v1/temperature_routing` on the individual doc pages.
