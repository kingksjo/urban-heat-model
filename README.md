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
