# Caprae AI-Readiness and Acquisition Fit Scorer

This project ranks B2B SaaS companies by acquisition fit and AI-readiness for
Caprae-style sourcing workflows. It combines a FastAPI backend, a Next.js
frontend, a heuristic scoring engine, and a lightweight outreach generator.

## What it does

- Scores companies across AI readiness, growth, and buy-box fit
- Explains each score with top reasons
- Lets users filter, sort, inspect, and export the ranked list
- Enriches a single domain from public homepage signals
- Generates a one-line outreach angle with an LLM or deterministic fallback
- Accepts CSV uploads shaped like `data/companies.csv` through `/api/ingest.csv`

## Stack

- Backend: FastAPI, Pydantic, pandas
- Frontend: Next.js 14, React, Tailwind, TypeScript
- Cache: SQLite
- Optional LLM: Anthropic Claude Haiku

## Quickstart

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8765 --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## API

| Method | Path | Notes |
|---|---|---|
| GET | `/api/health` | Health check and dataset size |
| GET | `/api/companies` | Raw company rows |
| GET | `/api/companies/scored` | Scored companies with filters |
| GET | `/api/companies/scored/{domain}/outreach` | Cached outreach angle |
| POST | `/api/enrich` | Single-domain enrichment preview |
| POST | `/api/ingest.csv` | Replace the working dataset from CSV |
| GET | `/api/export.csv` | Export the filtered scored list |

## Repo layout

```text
backend/   FastAPI app, scoring, enrichment, cache, tests
frontend/  Next.js UI
data/      Seed CSV dataset
docs/      Architecture and walkthrough notes
```

## Tooling added

- Backend unit and API tests under `backend/tests/`
- GitHub Actions CI in `.github/workflows/ci.yml`
- Backend deployment scaffolding with `Dockerfile` and `render.yaml`

## Current prototype limits

- The enrichment endpoint still uses synthetic defaults when firmographics are
  unknown.
- There is no auth or multitenancy yet.
- SQLite is still the prototype cache store.
