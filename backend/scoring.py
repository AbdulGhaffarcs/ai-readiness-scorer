"""
Caprae AI-Readiness & Acquisition Fit scoring engine.

Three weighted dimensions, each 0-100, combined into a composite score.
Every score is paired with the top reasons that drove it, so a buyer
analyst can see *why* a company surfaces — not just a black-box ranking.

Weights chosen to reflect Caprae's stated thesis: post-acquisition value
creation through AI enablement matters more than raw growth, and growth
matters more than pure size-fit.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from models import Company, ScoreBreakdown


W_AI = 0.40
W_GROWTH = 0.30
W_FIT = 0.30

MODERN_STACK_TOKENS = {
    "react", "nextjs", "typescript", "graphql", "rust", "go",
    "kubernetes", "kafka", "clickhouse", "snowflake", "bigquery",
    "vercel", "edge", "serverless", "openai", "gpu", "ray", "cuda",
}
LEGACY_STACK_TOKENS = {"php", "jquery", "wordpress", "drupal", "coldfusion"}
AI_INFRA_INDUSTRIES = {
    "AI Infrastructure", "AI Enterprise", "AI Marketing", "AI Creative",
}


@dataclass
class _SubScore:
    value: float
    reasons: list[str]


def _clip(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _score_ai_readiness(c: Company) -> _SubScore:
    """How prepared is this company to absorb and ship AI features?

    Signal mix:
      - Modern tech stack tokens (max +35)
      - Legacy stack penalty (-15 each, capped)
      - AI/ML job-post density per 100 employees (max +30)
      - Operates in AI-native industry (+20)
      - Has dev-facing surface area: API, webhooks, SDK (+10 from stack proxy)
    """
    reasons: list[str] = []
    stack = {t.strip().lower() for t in c.tech_stack_signals.split(",") if t.strip()}

    modern_hits = stack & MODERN_STACK_TOKENS
    legacy_hits = stack & LEGACY_STACK_TOKENS
    modern_pts = min(35.0, len(modern_hits) * 7.0)
    legacy_pts = -min(15.0, len(legacy_hits) * 8.0)
    if modern_hits:
        reasons.append(
            f"Modern stack: {', '.join(sorted(modern_hits)[:4])}"
        )
    if legacy_hits:
        reasons.append(f"Legacy tech detected: {', '.join(sorted(legacy_hits))}")

    headcount = max(c.employee_count, 1)
    ai_density = c.ai_job_posts_count / headcount * 100.0
    ai_pts = min(30.0, ai_density * 3.0)
    if c.ai_job_posts_count >= 5:
        reasons.append(
            f"{c.ai_job_posts_count} open AI/ML roles "
            f"({ai_density:.1f} per 100 employees)"
        )

    industry_pts = 20.0 if c.industry in AI_INFRA_INDUSTRIES or c.sub_industry in AI_INFRA_INDUSTRIES else 0.0
    if industry_pts:
        reasons.append(f"AI-native vertical ({c.sub_industry})")

    api_pts = 10.0 if {"go", "rust", "typescript", "graphql"} & stack else 0.0

    raw = 35.0 + modern_pts + legacy_pts + ai_pts + industry_pts + api_pts - 35.0
    # Calibrate: baseline 35 so an empty profile lands ~35, not 0.
    value = _clip(35.0 + modern_pts + legacy_pts + ai_pts + industry_pts + api_pts)
    return _SubScore(value, reasons[:3])


def _score_growth(c: Company) -> _SubScore:
    """Healthy trajectory worth acquiring vs. acquiring a melting ice cube."""
    reasons: list[str] = []
    pts = 40.0  # baseline

    delta = c.headcount_6mo_delta_pct
    if delta >= 30:
        pts += 30; reasons.append(f"Strong hiring: +{delta:.0f}% headcount in 6mo")
    elif delta >= 10:
        pts += 18; reasons.append(f"Healthy hiring: +{delta:.0f}% headcount in 6mo")
    elif delta >= 0:
        pts += 6
    elif delta >= -10:
        pts -= 5; reasons.append(f"Flat-to-shrinking: {delta:.0f}% headcount in 6mo")
    else:
        pts -= 18; reasons.append(f"Contracting: {delta:.0f}% headcount in 6mo")

    today_year = date.today().year
    if c.last_funding_year and c.last_funding_year >= today_year - 1:
        pts += 15
        reasons.append(f"Recently funded ({c.last_funding_year})")
    elif c.last_funding_year and c.last_funding_year >= today_year - 3:
        pts += 6

    if c.recent_news_count >= 20:
        pts += 12; reasons.append(f"High news velocity ({c.recent_news_count} mentions)")
    elif c.recent_news_count >= 10:
        pts += 6

    age = today_year - c.founded_year
    if 4 <= age <= 12:
        pts += 5  # sweet spot: past survival, not yet ossified

    return _SubScore(_clip(pts), reasons[:3])


def _score_fit(c: Company) -> _SubScore:
    """Caprae buy box: lower middle market, B2B SaaS, owner-operator, US-centric."""
    reasons: list[str] = []
    pts = 30.0

    n = c.employee_count
    if 30 <= n <= 200:
        pts += 30; reasons.append(f"Sweet-spot size band ({n} employees)")
    elif 10 <= n < 30:
        pts += 18; reasons.append(f"Early but reachable ({n} employees)")
    elif 200 < n <= 500:
        pts += 14; reasons.append(f"Slightly above buy-box ceiling ({n} employees)")
    elif n > 500:
        pts -= 5; reasons.append(f"Above buy-box ceiling ({n} employees)")

    if c.industry == "B2B SaaS":
        pts += 18; reasons.append("Recurring-revenue B2B SaaS")

    if c.founder_is_ceo and not c.has_pe_backing:
        pts += 18
        reasons.append("Owner-operator, no PE backing yet")
    elif c.founder_is_ceo and c.has_pe_backing:
        pts += 6
    elif c.has_pe_backing:
        pts -= 8; reasons.append("Already PE-backed")

    if c.hq_country == "US":
        pts += 4

    return _SubScore(_clip(pts), reasons[:3])


def score_company(c: Company) -> ScoreBreakdown:
    ai = _score_ai_readiness(c)
    growth = _score_growth(c)
    fit = _score_fit(c)

    composite = round(W_AI * ai.value + W_GROWTH * growth.value + W_FIT * fit.value, 1)

    # Pick top reasons across dimensions, weighting by dimension importance.
    weighted: list[tuple[float, str]] = []
    for sub, w in ((ai, W_AI), (growth, W_GROWTH), (fit, W_FIT)):
        for r in sub.reasons:
            weighted.append((w, r))
    weighted.sort(key=lambda x: -x[0])
    top_reasons = [r for _, r in weighted[:3]]

    return ScoreBreakdown(
        composite=composite,
        ai_readiness=round(ai.value, 1),
        growth=round(growth.value, 1),
        fit=round(fit.value, 1),
        reasons=top_reasons,
    )
