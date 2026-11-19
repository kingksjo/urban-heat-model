# Urban Heat Model — FortyGuard API Evaluation & ML Prototype

Evaluation of the FortyGuard Temperature REST API and MCP interface, paired with a small exploratory ML proof of concept ("Urban Heat Pattern Explorer").

## Project Structure

```text
urban-heat model/
├── README.md
├── .env                          # Local API key (gitignored; never commit)
├── .env.example
├── .gitignore
├── requirements.txt
├── fortyguard_api_evaluation_plan.md
├── notes/
│   ├── endpoint-inventory.md     # Phase 1: account info, REST/MCP inventory, doc questions
│   ├── api-test-log.md           # Chronological REST & MCP test log
│   └── findings.md               # Structured findings (Documented / Observed / Inferred / Not tested)
├── src/                          # Reusable REST client & polling helpers
├── notebooks/                    # Exploration, dataset build, and ML prototype notebooks
├── data/
│   ├── raw/                      # Sanitized API outputs
│   └── processed/                # Cleaned tabular datasets
└── report/
    └── figures/                  # Plots and charts for the final report
```

## Setup

1. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. Add your FortyGuard API key to `.env`:
   ```text
   FORTYGUARD_API_KEY=your_actual_key
   ```
   Never commit `.env` or include credentials in notebooks, logs, screenshots, or reports.

## Data Separation (API Tests vs. ML Dataset)

* `data/raw/*.json` — Sanitized outputs from Phase 2 (REST) and Phase 3 (MCP) API evaluation tests.
* `data/raw/phase4_heatmaps/` — Dedicated Phase 4 ML dataset heatmaps (`34` new neighborhoods + `manifest.json` referencing the `2` reused `2024-07-15 14:00` smoke-test neighborhoods = **`36` neighborhoods / `2,507` tiles**).
* `data/processed/` — Cleaned ML table (`urban_heat_tiles.csv`, `2,507 × 24`) and spatial-CV metrics (`ml_results_summary.json`).

## Reproducing the Phase 4 Pipeline

```powershell
# 1. Collect LA Basin heatmaps (skips cached neighborhoods; stops at 2,500+ tiles)
python -m src.collect_phase4_heatmaps --target-tiles 2500

# 2. Enrich all 2,507 tiles with OpenStreetMap, coastal distance, and elevation (0 FortyGuard credits)
python -m src.build_gis_features

# 3. Train & evaluate models under 5-fold Spatial GroupKFold (by neighborhood)
python -m src.train_ml_prototype
```

## Current Snapshot

* **Dataset:** `2,507` `100m × 100m` tiles across `36` LA Basin neighborhoods (`20.72–36.99 °C` on `2024-07-15 14:00`).
* **Best Spatial-CV Model (`Extra Trees`, Urban Form + Macro-Geography):** `MAE = 0.9900 °C`, `RMSE = 1.4114 °C`, `R² = 0.8858` (vs. Mean Baseline `MAE = 3.7219 °C`).
* **Figures:** Saved under `report/figures/phase4_*.png`.
* **Notebooks & Final Report:** See [notebooks/01_api_exploration.ipynb](notebooks/01_api_exploration.ipynb), [notebooks/02_dataset_build.ipynb](notebooks/02_dataset_build.ipynb), [notebooks/03_ml_prototype.ipynb](notebooks/03_ml_prototype.ipynb), and [report/fortyguard_evaluation.md](report/fortyguard_evaluation.md).
