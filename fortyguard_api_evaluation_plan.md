# FortyGuard API Evaluation & ML Prototype Plan

## Purpose

Use this plan to do two things in parallel:

1. **Evaluate the FortyGuard Temperature API and MCP as a developer would** — test the documented workflows, inspect actual responses, identify strengths and friction points, and collect evidence for a professional product evaluation.
2. **Build a small ML proof of concept using FortyGuard data** — demonstrate how the API could support a downstream machine-learning application without letting the project become so large that the product evaluation suffers.

The final deliverable will be a concise technical evaluation report, supported by request/response evidence, plus a reproducible ML prototype and a short explanation of what it demonstrates.

---

## Working principles

- **Test before judging.** Separate what the documentation promises from what you actually observe.
- **Record evidence as you go.** Save timestamps, endpoint/tool names, sanitized request parameters, response examples, latency, activity IDs, errors, and screenshots where useful.
- **Protect the trial account.** Check plan access and credit costs before running expensive operations. Do not repeatedly submit the same costly job just to test it.
- **Keep secrets out of the project.** Store the API key in an environment variable or an ignored `.env` file. Never commit it or include it in screenshots, notebooks, logs, or the final report.
- **Keep the ML claims modest.** A small prototype can demonstrate a plausible use case; it cannot establish that the model is suitable for real-world urban planning.
- **Distinguish REST from MCP.** They expose related capabilities, but the documented request patterns are not identical. Test and describe each interface on its own terms.

## Suggested project structure

```text
fortyguard-evaluation/
├── README.md
├── .env                  # API key; never commit
├── .gitignore
├── requirements.txt
├── notes/
│   ├── api-test-log.md
│   └── findings.md
├── src/
│   ├── client.py         # REST request helpers
│   └── polling.py        # bounded polling for async jobs
├── notebooks/
│   ├── 01_api_exploration.ipynb
│   ├── 02_dataset_build.ipynb
│   └── 03_ml_prototype.ipynb
├── data/
│   ├── raw/              # sanitized API outputs
│   └── processed/
└── report/
    ├── figures/
    └── fortyguard_evaluation.md
```

Add `.env`, any exported secrets, and any private account material to `.gitignore`. Only retain API responses in the project if the account terms permit it; remove credentials and personal information from saved material.

---

# Phase 1 — Account, access and documentation review

### 1.1 Set up the account and local environment

- [ ] Create/sign in to the FortyGuard account using the link in the hiring email.
- [ ] Locate the API key and record where it is configured (do not record the key itself).
- [ ] Record the account plan, available trial credits, and any visible expiry date or usage limits.
- [ ] Check the plan label shown beside each endpoint in the documentation.
- [ ] Create the project folder and Python environment.
- [ ] Install the initial dependencies: `requests`, `python-dotenv`, `pandas`, `numpy`, `scikit-learn`, `matplotlib`, and `jupyter`.
- [ ] Add `.env` and notebook checkpoint files to `.gitignore`.

Example `.env` entry:

```text
FORTYGUARD_API_KEY=your_key_here
```

### 1.2 Build an endpoint inventory

For every REST endpoint you intend to test, record:

| Item | What to capture |
|---|---|
| Name and route | Exact endpoint name, HTTP method and path shown in the docs |
| Purpose | What problem the endpoint is designed to solve |
| Access | Basic, Premium, or both |
| Inputs | Required/optional fields, types, units, coordinate order, date formats |
| Outputs | Response fields, units, data types, geographic format, imagery/artifacts |
| Processing | Direct response or asynchronous job; how results are retrieved |
| Cost/limits | Credits, area limits, resolution options, rate limits, date/coverage constraints |
| Documentation | Working example, schema clarity, missing or ambiguous details |

Do not infer a route or field name from an example in another endpoint. Copy the exact route and schema from that endpoint's own documentation page.

### 1.3 Questions to resolve from the docs

- [ ] What does the `temperature` input mean for each endpoint where it appears: an observed value, a reference value, or a threshold?
- [ ] Which date/time filters are supported, and are timestamps interpreted in UTC or local time?
- [ ] Which temperature units are returned? Are units stated consistently in the response?
- [ ] What does each heatmap `granularity` value represent, and how does it affect output size and credit use?
- [ ] Which heatmap `analytic_type` and `map_type` values are accepted?
- [ ] What are the maximum polygon dimensions/area and coordinate constraints?
- [ ] Are there documented retry rules, request timeouts, rate limits, or idempotency protections?
- [ ] How long are generated results and signed report links available?
- [ ] Which capabilities are actually included in the trial account?

**Important documentation comparison:** the REST Quickstart describes POST submissions as asynchronous and uses a status endpoint, while the MCP tools page classifies `env_params`, `satellite`, and `streetview` as direct tools and `heatmap`, `report`, and `temperature_routing` as asynchronous tools with corresponding read tools. Record whether this is an interface-specific difference or a documentation inconsistency after testing. Do not assume the REST workflow is identical to MCP.

**Phase 1 output:** an endpoint inventory and a short list of unknowns to verify through testing.

---

# Phase 2 — REST API testing

Use Python `requests` or an API client such as Postman. Start with one low-cost request, inspect the result, and only then expand testing.

## 2.1 Authentication and basic connectivity

- [ ] Make one valid request using the documented REST authentication header: `api-key: YOUR_API_KEY`.
- [ ] Confirm the API accepts the key and returns a valid response.
- [ ] Record the HTTP status, response time, response content type, and top-level JSON structure.
- [ ] Confirm that error responses are understandable and do not expose sensitive details.

Do not put the API key directly into notebook cells that may later be shared. Load it from an environment variable.

## 2.2 Environmental Parameters

This is the recommended first endpoint to test because it provides point-level environmental information and is a natural starting point for data exploration.

- [ ] Choose one location with valid coordinates and record its latitude/longitude.
- [ ] Choose a date/time supported by the API and record the time zone assumption.
- [ ] Submit the smallest sensible request using the documented required fields.
- [ ] Inspect the returned measurements, units, timestamps, null values, and metadata.
- [ ] Check whether optional analysis fields change which measurements are returned.
- [ ] Repeat only if necessary to understand consistency or time-filter behaviour.

Capture: request fields (without secrets), HTTP status, latency, returned field names, units, missing values, and any plan-specific limitations.

## 2.3 Heatmap generation and result retrieval

- [ ] Choose a small, valid polygon that stays within the documented area limits.
- [ ] Use the coarsest/least expensive documented granularity for the first run.
- [ ] Submit one heatmap request and record the returned activity ID.
- [ ] Poll the documented status endpoint at a reasonable interval with a maximum retry count and timeout.
- [ ] Record status transitions, total completion time, and the final response structure.
- [ ] Inspect whether the result contains only summary statistics or also cell-level/geospatial temperature values.
- [ ] Save a sanitized response sample and, where possible, visualize the returned geographic data.

Do not assume that a heatmap is automatically a grid-level training dataset. Confirm the spatial resolution and granularity of the actual response. This will determine whether it can support the ML experiment below.

## 2.4 Other REST capabilities — test only where accessible

Use the endpoint documentation and the account's actual access level to decide whether to run these. Do not upgrade or spend credits solely to complete the checklist.

- [ ] **Heat Intelligence report:** submit one focused report if available; inspect the activity lifecycle, report content, link expiry and whether the findings are traceable to returned data.
- [ ] **Satellite segmentation:** if enabled, test one suitable location; inspect class labels, percentages, imagery date, metadata and whether the output is usable as structured features.
- [ ] **Street-view segmentation:** if enabled and useful, test one location; inspect image availability, capture date, segmentation classes and image artifacts. Check how the endpoint behaves where street imagery is unavailable.
- [ ] **Temperature-aware routing:** review the route schema and plan requirements. Test only if access and credit budget make it reasonable; record route geometry, travel duration and thermal metrics.

## 2.5 Error handling and validation

Run safe negative tests that should fail validation without consuming meaningful credits:

- [ ] Missing a required field.
- [ ] Out-of-range latitude/longitude.
- [ ] Malformed date/time or unsupported enum value.
- [ ] Invalid polygon structure (only if validation is inexpensive and safe to test).

For each failure, record the HTTP code, error message, whether the response identifies the invalid field, and whether the guidance helps a developer fix the request.

Also record naturally occurring `401`, `403`, `404`, `429` or `500` responses if they occur. Do not deliberately flood the API to trigger rate limits or repeatedly submit expensive jobs.

## 2.6 API developer-experience review

Assess the following based on what you observed:

- Authentication clarity and secure key handling.
- Consistency of endpoint naming, field names, date formats and response envelopes.
- Quality and completeness of request/response examples.
- Schema discoverability and type/units documentation.
- Validation messages and error consistency.
- Asynchronous job tracking, polling guidance and timeout behaviour.
- Result persistence, pagination or download mechanisms where relevant.
- Latency and reliability across your small number of tests.
- Ease of turning the responses into a reusable Python data pipeline.

**Phase 2 output:** a REST test log, sanitized response samples, and a short list of API strengths, issues and unanswered questions.

---

# Phase 3 — MCP testing

The MCP evaluation should answer a different question from the REST evaluation: **How easily can an AI client discover and use FortyGuard's capabilities as tools?**

## 3.1 Connect an MCP-compatible client

Use a client you already work with that supports remote MCP over Streamable HTTP. Follow FortyGuard's client-specific setup instructions.

Documented connection details:

- Endpoint: `https://tos-mcp.app.fortyguard.com/mcp`
- Transport: remote HTTP / Streamable HTTP
- Authentication: `Authorization: Bearer YOUR_API_KEY`

The MCP authentication header differs from the REST `api-key` header. Store the key using the client's secure environment/configuration mechanism; do not paste it into a prompt.

- [ ] Configure the server.
- [ ] Confirm that the client reports a successful connection.
- [ ] Confirm that the tool catalog is discovered.
- [ ] Record tool names, descriptions, required inputs and any schema details visible to the client.

## 3.2 Test representative MCP tools

Start with a direct tool and one asynchronous workflow:

- [ ] **`env_params`:** request environmental conditions for the same point/date tested through REST, where the inputs are equivalent.
- [ ] **`heatmap`:** submit one small-area request, capture its activity ID, and use **`heatmap_read`** to retrieve the result.
- [ ] **`satellite` or `streetview`:** test one direct segmentation tool if the trial plan permits it.

Only test `report`/`report_read` or `temperature_routing`/`temperature_routing_read` if they add useful evidence and the plan/credits allow it.

## 3.3 Evaluate MCP usability

- [ ] Does the client discover all tools reliably?
- [ ] Are tool names and descriptions clear enough for an AI agent to select the correct capability?
- [ ] Are required fields, units and accepted values understandable?
- [ ] Does the tool return structured, usable results or mostly opaque text?
- [ ] Is the asynchronous submit/read process easy for an agent to follow?
- [ ] Does the client handle permission errors, missing inputs and failed activities clearly?
- [ ] Does the MCP connection remain stable during normal testing?
- [ ] Is the distinction between REST endpoints and MCP tools explained clearly in the docs?

## 3.4 Compare REST and MCP

Where possible, run equivalent requests through both interfaces and compare:

- Input names and semantics.
- Output fields and units.
- Error behaviour.
- Processing model and status visibility.
- Ease of integration.

Do not expect identical wrappers or response formats. Focus on whether both interfaces expose the same underlying information consistently and whether differences are documented.

**Phase 3 output:** MCP setup notes, tool-discovery observations, one or two execution examples, and a REST-versus-MCP comparison.

---

# Phase 4 — ML proof of concept

## Proposed project: Urban Heat Pattern Explorer

**Question:** Can characteristics of the built and natural environment help explain or estimate local temperature differences across sampled urban locations?

The intended prototype combines FortyGuard's temperature information with land-cover information. It is deliberately a small, exploratory regression experiment—not a city-scale forecasting system.

### 4.1 Feasibility gate: confirm the data first

Before collecting a dataset, verify all of the following:

- [ ] The account can access the required temperature data.
- [ ] The API returns a clearly defined temperature target with units and timestamps.
- [ ] Satellite segmentation is accessible, or there is another defensible source of environmental features.
- [ ] Temperature and segmentation data can be aligned to the same location and a reasonably comparable time period.
- [ ] The response provides enough usable variation and enough distinct samples for a small experiment.

**Preferred data pairing:**

- Target: an observed/returned temperature measure from Environmental Parameters or heatmap output.
- Features: satellite segmentation class percentages, such as vegetation, built-up surfaces and road coverage, if returned by the endpoint.
- Optional controls: latitude/longitude and time-derived features such as hour or month, where relevant and supported.

Check the exact meaning of every field before using it. Do not use a reference temperature or a value derived directly from the target as a model feature; that would create target leakage.

### 4.2 Choose the smallest useful study area

- [ ] Choose one city/neighbourhood where the API has coverage and where you can identify several distinct points or small areas.
- [ ] Define a manageable sample design (for example, 20–50 locations if credits and endpoint access make that practical).
- [ ] Keep the date/time window as consistent as possible across samples.
- [ ] Record the imagery date returned by segmentation; it may not match the requested temperature date.
- [ ] Track failed requests and missing coverage rather than silently dropping them.

If the API's credit limits do not support dozens of samples, reduce the scope and present the result as a pipeline demonstration rather than claiming a robust predictive model.

### 4.3 Build the dataset

Create one row per location (or per location-time observation if you intentionally collect repeated times).

Example schema — adjust it to the actual API response:

| Column | Description |
|---|---|
| `location_id` | Your stable identifier for the sampled location |
| `latitude`, `longitude` | Coordinates |
| `observed_at` | Temperature observation/request time |
| `temperature_c` | Target temperature in Celsius, after verifying units |
| `vegetation_pct` | Returned vegetation coverage, if available |
| `built_up_pct` | Returned built-up coverage, if available |
| `road_pct` | Returned road coverage, if available |
| `imagery_date` | Source imagery date, if returned |

- [ ] Preserve sanitized raw JSON separately from the processed CSV/Parquet dataset.
- [ ] Normalize class labels and units consistently.
- [ ] Check missing values, duplicate coordinates, impossible values and feature percentages.
- [ ] Document any mismatch between imagery date and temperature date.
- [ ] Plot feature distributions and temperature distributions before training.

### 4.4 Train simple baseline models

Start with models that are interpretable and appropriate for a small tabular dataset:

1. **Baseline:** predict the mean temperature of the training set.
2. **Linear Regression:** establish a simple interpretable relationship.
3. **Random Forest Regressor:** test whether non-linear feature relationships improve performance.

Evaluate with MAE and RMSE; use R² as a supplementary metric, not the only measure. Compare every model with the mean baseline.

### 4.5 Avoid spatial leakage

Do not randomly split neighbouring observations if the purpose is to test performance on unseen parts of the city. Nearby points can be highly similar and make results look better than they are.

- [ ] Group samples by neighbourhood/grid/area and hold out one or more groups for testing, where sample size allows.
- [ ] Fit preprocessing only on the training data.
- [ ] Report the number of samples and the limitations of the split.
- [ ] If there are too few locations for a meaningful spatial holdout, report the experiment as exploratory and avoid strong generalization claims.

### 4.6 Interpret and visualize

Produce a small set of figures:

- Map or scatter plot of sampled locations coloured by observed temperature (if coordinates and a mapping approach are available).
- Distribution of temperature values.
- Feature-versus-temperature plots for key land-cover classes.
- Predicted-versus-actual plot for the held-out samples.
- Feature-importance or coefficient summary, with a note that association does not establish causation.

### 4.7 Fallback paths if trial access is limited

- **No satellite segmentation access:** test whether the available environmental/heatmap data support a different exploratory task, such as clustering locations by environmental profile. Do not pretend this is the same land-cover regression project.
- **Heatmap returns only area-level summaries:** do not treat the summary as grid-cell training data. Use point-level environmental observations if available, or make the heatmap a visualization/analysis component rather than the ML target.
- **Too few usable samples:** build a reproducible ingestion and cleaning pipeline, train only a baseline as a demonstration, and clearly label the model as a prototype. Do not manufacture or duplicate observations to inflate the dataset.
- **No usable ML target:** complete the API evaluation and document the data-access limitation. A defensible explanation is better than an unsupported model.

**Phase 4 output:** a notebook, sanitized dataset, a small number of evaluation plots, model metrics and a short statement of what the prototype does and does not establish.

---

# Phase 5 — Consolidate findings and write the report

Keep the report evidence-led. For every important finding, label it as one of:

- **Documented:** stated in FortyGuard's documentation.
- **Observed:** directly confirmed during your testing.
- **Inferred:** a reasonable interpretation, but not independently verified.
- **Not tested:** unavailable, blocked by plan/credits, or outside the evaluation scope.

## Recommended final report structure

1. **Executive summary** — what you evaluated, the strongest positive finding, the most important issue/opportunity, and your overall assessment.
2. **Scope and methodology** — account plan, test environment, date, interfaces tested, number of requests, and any constraints.
3. **Product and API overview** — a brief explanation of the Temperature API and MCP capabilities.
4. **REST API findings** — authentication, endpoint design, schemas, response structure, async workflow, validation, errors, performance and developer experience.
5. **MCP findings** — setup, authentication, tool discovery, tool descriptions, direct/async workflows, output usability and agent experience.
6. **UX and workflow observations** — how easily a developer can move from documentation to a working integration.
7. **Strengths** — specific strengths backed by examples.
8. **Issues and risks** — each issue with impact, evidence, reproducibility and severity (High/Medium/Low).
9. **Recommendations** — practical improvements, prioritized by user/developer impact and implementation effort.
10. **ML proof of concept** — use case, data source, data preparation, model, evaluation, results, limitations and potential next steps.
11. **Conclusion** — who would benefit most from the product and what would most improve the developer experience.
12. **Appendix** — sanitized request/response examples, test log and links to relevant documentation pages.

## Use this format for individual findings

| Field | What to write |
|---|---|
| Finding | One clear observation |
| Category | UX, API design, docs, reliability, MCP, data, scalability, etc. |
| Evidence | Endpoint/tool, request ID or sanitized response, screenshot, timing |
| Impact | Why it matters to a developer or end user |
| Severity | High, Medium or Low |
| Recommendation | A specific, actionable improvement |

Avoid vague statements such as "the API is slow" based on one request. Instead write: "In three tests under [conditions], completion took between X and Y seconds; this is a small sample and not a load test." Do not claim to have evaluated production scalability unless you have conducted an approved load test.

---

# Suggested execution schedule

The hiring instructions mention that the product evaluation typically takes 45–90 minutes. The ML prototype is an additional piece of work, so treat it as a separate extension rather than trying to squeeze it into that window.

| Session | Focus | Deliverable |
|---|---|---|
| 1 — 45–90 min | Account, docs, REST smoke tests, one asynchronous workflow, MCP connection and one or two tool calls | Completed test log and initial product findings |
| 2 — 1–2 hours | Inspect responses, confirm data access, build a small dataset | Sanitized dataset and data-quality notes |
| 3 — 1–2 hours | Baselines, model, evaluation and visuals | ML notebook and prototype results |
| 4 — 45–60 min | Consolidate evidence and write the report | Final evaluation report and project README |

If the submission deadline is close, prioritize Session 1 and the report. A thorough, honest evaluation of the product is more valuable than a rushed or weak ML model.

---

# Final submission checklist

## Product evaluation

- [ ] I tested the REST API with at least one successful request.
- [ ] I tested an asynchronous workflow and retrieved its result, where accessible.
- [ ] I tested MCP connection and tool discovery.
- [ ] I compared at least one equivalent REST/MCP capability where possible.
- [ ] I recorded actual errors, response structure, units, latency and limitations.
- [ ] I separated documented behaviour from observed behaviour.
- [ ] My recommendations are specific and supported by evidence.

## ML prototype

- [ ] The dataset comes from real, permitted API responses.
- [ ] Feature and target definitions are clear.
- [ ] Time and imagery-date mismatches are documented.
- [ ] There is a baseline and a defensible evaluation approach.
- [ ] Spatial leakage and small-sample limitations are addressed.
- [ ] The project does not claim causation or city-wide predictive validity without evidence.

## Security and presentation

- [ ] No API key, access token or private account information appears in the repository or report.
- [ ] Raw response examples are sanitized.
- [ ] Figures have labels, units and captions.
- [ ] The README explains how to reproduce the prototype without exposing credentials.
- [ ] The report states what was not tested and why.

---

## Official documentation to use during the evaluation

- [FortyGuard API documentation](https://docs-api.fortyguard.com/docs/)
- [REST API Quickstart](https://docs-api.fortyguard.com/docs/quickstart)
- [FortyGuard MCP overview](https://docs-api.fortyguard.com/docs/mcp-overview)
- [Available MCP tools](https://docs-api.fortyguard.com/docs/mcp-tools)
- [MCP Quickstart](https://docs-api.fortyguard.com/docs/mcp-quickstart)
- [MCP authentication](https://docs-api.fortyguard.com/docs/mcp-authentication)
- [MCP client setup](https://docs-api.fortyguard.com/docs/mcp-client-setup)

For exact REST request schemas, endpoint paths, plan labels and credit costs, use the individual endpoint pages in the live documentation. Those details can change and should be captured from the account/documentation at the time you test.
