"""
Caprae AI-Readiness Scorer — FastAPI app.

Endpoints
---------
GET  /api/health              healthcheck
GET  /api/companies           raw dataset
GET  /api/companies/scored    dataset + 3-dim scores + top reasons
GET  /api/companies/scored/{domain}/outreach   per-lead outreach hook
POST /api/enrich              live single-domain scrape + score preview
GET  /api/export.csv          filtered scored leads as CSV download
"""
from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from db import get_outreach, init_db, put_outreach
from enrichment import enrich_domain
from llm import generate_outreach
from models import Company, EnrichRequest, EnrichResponse, ScoredCompany
from scoring import score_company


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "companies.csv"
CSV_BOOL_FIELDS = ("founder_is_ceo", "has_pe_backing")
CSV_INT_FIELDS = (
    "employee_count",
    "founded_year",
    "last_funding_year",
    "funding_total_usd",
    "ai_job_posts_count",
    "recent_news_count",
)
CSV_FLOAT_FIELDS = ("headcount_6mo_delta_pct",)

app = FastAPI(title="Caprae AI-Readiness Scorer", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


_companies_cache: list[Company] | None = None


def _coerce_company_row(row: dict) -> Company:
    normalized = dict(row)
    for key in CSV_BOOL_FIELDS:
        value = normalized.get(key)
        if isinstance(value, str):
            normalized[key] = value.strip().lower() == "true"
    for key in CSV_INT_FIELDS:
        value = normalized.get(key)
        if value in ("", None):
            normalized[key] = None if key == "last_funding_year" else 0
        elif isinstance(value, str):
            normalized[key] = int(float(value))
    for key in CSV_FLOAT_FIELDS:
        value = normalized.get(key)
        if value in ("", None):
            normalized[key] = 0.0
        elif isinstance(value, str):
            normalized[key] = float(value)
    return Company(**normalized)


def _load_companies() -> list[Company]:
    global _companies_cache
    if _companies_cache is not None:
        return _companies_cache
    df = pd.read_csv(DATA_PATH)
    df = df.where(pd.notnull(df), None)
    out = [_coerce_company_row(row) for row in df.to_dict(orient="records")]
    _companies_cache = out
    return out


def _score_all() -> list[ScoredCompany]:
    return [
        ScoredCompany(**c.model_dump(), score=score_company(c))
        for c in _load_companies()
    ]


def _persist_companies(companies: list[Company]) -> None:
    global _companies_cache
    fieldnames = list(Company.model_fields.keys())
    with DATA_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for company in companies:
            writer.writerow(company.model_dump())
    _companies_cache = companies


@app.on_event("startup")
def _startup() -> None:
    load_dotenv(Path(__file__).resolve().parent / ".env")
    init_db()
    _load_companies()  # warm cache + fail fast if CSV is broken


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "companies_loaded": len(_load_companies())}


@app.get("/api/companies", response_model=list[Company])
def list_companies() -> list[Company]:
    return _load_companies()


_BANDS = {
    "micro": lambda n: n < 30,
    "smb": lambda n: 30 <= n <= 200,
    "mid": lambda n: 200 < n <= 500,
    "large": lambda n: n > 500,
}


def _filter_score(
    min_score: float = 0.0,
    industry: Optional[str] = None,
    sub_industry: Optional[str] = None,
    size_band: Optional[str] = None,
) -> list[ScoredCompany]:
    rows = _score_all()
    if min_score > 0:
        rows = [r for r in rows if r.score.composite >= min_score]
    if industry:
        rows = [r for r in rows if r.industry.lower() == industry.lower()]
    if sub_industry:
        rows = [r for r in rows if r.sub_industry.lower() == sub_industry.lower()]
    if size_band:
        check = _BANDS.get(size_band.lower())
        if check is None:
            raise HTTPException(400, f"Unknown size_band {size_band!r}")
        rows = [r for r in rows if check(r.employee_count)]
    rows.sort(key=lambda r: r.score.composite, reverse=True)
    return rows


@app.get("/api/companies/scored", response_model=list[ScoredCompany])
def list_scored(
    min_score: float = Query(0.0, ge=0, le=100),
    industry: Optional[str] = None,
    sub_industry: Optional[str] = None,
    size_band: Optional[str] = Query(
        None,
        description="One of: micro (<30), smb (30-200), mid (200-500), large (>500)",
    ),
) -> list[ScoredCompany]:
    return _filter_score(min_score, industry, sub_industry, size_band)


@app.get("/api/companies/scored/{domain}/outreach")
def outreach(domain: str) -> dict:
    cached = get_outreach(domain)
    if cached:
        return {"domain": domain, "outreach_angle": cached, "cached": True}
    match = next((c for c in _load_companies() if c.domain.lower() == domain.lower()), None)
    if match is None:
        raise HTTPException(404, f"Unknown domain {domain!r}")
    s = score_company(match)
    angle = generate_outreach(match, s)
    put_outreach(domain, angle)
    return {"domain": domain, "outreach_angle": angle, "cached": False}


@app.post("/api/enrich", response_model=EnrichResponse)
async def enrich(req: EnrichRequest) -> EnrichResponse:
    if not req.domain:
        raise HTTPException(400, "domain is required")
    return await enrich_domain(req.domain)


@app.post("/api/ingest.csv")
async def ingest_csv(file: UploadFile = File(...)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Please upload a CSV file")

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(400, "CSV must be UTF-8 encoded") from exc

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(400, "CSV is missing a header row")

    try:
        companies = [_coerce_company_row(row) for row in reader]
    except Exception as exc:
        raise HTTPException(400, f"Invalid CSV row: {exc}") from exc

    if not companies:
        raise HTTPException(400, "CSV did not contain any companies")

    _persist_companies(companies)
    return {"ok": True, "companies_loaded": len(companies)}


@app.get("/api/export.csv")
def export_csv(
    min_score: float = Query(0.0, ge=0, le=100),
    industry: Optional[str] = None,
    sub_industry: Optional[str] = None,
    size_band: Optional[str] = Query(
        None,
        description="One of: micro (<30), smb (30-200), mid (200-500), large (>500)",
    ),
) -> StreamingResponse:
    rows = _filter_score(
        min_score=min_score,
        industry=industry,
        sub_industry=sub_industry,
        size_band=size_band,
    )
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "company_name", "domain", "industry", "sub_industry",
        "employee_count", "headquarters",
        "composite_score", "ai_readiness", "growth", "fit",
        "top_reasons",
    ])
    for r in rows:
        writer.writerow([
            r.company_name, r.domain, r.industry, r.sub_industry,
            r.employee_count, r.headquarters,
            r.score.composite, r.score.ai_readiness, r.score.growth, r.score.fit,
            " | ".join(r.score.reasons),
        ])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=caprae_scored_leads.csv"},
    )
