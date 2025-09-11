# Health Report Generator

A local, offline tool that reads medical lab report PDFs from `reports/`, extracts measurements, analyzes trends and risk, and generates an interactive multi‑page HTML report in `build/health-report/`.

## Quickstart

1. Ensure Python 3.10+
2. Install dependencies:
   - `python -m venv venv && venv/Scripts/activate` (Windows)
   - `pip install -r requirements.txt`
3. Run:
   - `python -m src.health_report.cli --reports-dir ./reports --out-dir ./build/health-report`

## Features
- Parses all PDFs in `reports/` (text-based)
- Detects per-measurement units from table headers, value suffixes, or names
- Normalizes tests to canonical codes and units
- Computes trends and risk scores
- Generates interactive HTML report (overview, categories, tests)

## Notes
- No OCR is enabled by default (your PDFs are text-based)
- Raw PDFs are ignored by Git via `.gitignore`
- Outputs and caches are in `data/` and `build/`

## Disclaimer
This tool provides information only and is not medical advice.
