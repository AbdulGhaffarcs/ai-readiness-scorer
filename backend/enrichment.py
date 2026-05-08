"""
Live single-domain enrichment.

Fetches a homepage, sniffs response headers + HTML for tech-stack signals,
and detects whether the company has a careers page. The result feeds the
scoring engine the same way a row from the dataset does, demonstrating
that the pipeline is real, not just CSV-backed.
"""
from __future__ import annotations

import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from models import Company, EnrichResponse, ScoreBreakdown
from scoring import score_company


HEADER_HINTS = {
    "x-powered-by": {"php": "php", "express": "nodejs", "asp.net": "dotnet"},
    "server": {"vercel": "vercel", "cloudflare": "cloudflare", "nginx": "nginx"},
}
HTML_PATTERNS: dict[str, re.Pattern[str]] = {
    "react": re.compile(r"(?i)__NEXT_DATA__|react|/_next/"),
    "nextjs": re.compile(r"(?i)/_next/|__NEXT_DATA__"),
    "vue": re.compile(r"(?i)data-v-|nuxt"),
    "wordpress": re.compile(r"(?i)wp-content|wp-includes"),
    "shopify": re.compile(r"(?i)cdn\.shopify\.com"),
    "vercel": re.compile(r"(?i)vercel\.app|vercel-analytics"),
    "intercom": re.compile(r"(?i)intercomcdn|intercom\.io"),
    "segment": re.compile(r"(?i)segment\.com|cdn\.segment"),
    "openai": re.compile(r"(?i)openai|gpt-4|chatgpt"),
    "stripe": re.compile(r"(?i)js\.stripe\.com|stripe-elements"),
}
CAREERS_RX = re.compile(r"(?i)(careers|jobs|join[- ]us|hiring|we'?re hiring)")


def _normalize(domain: str) -> str:
    domain = domain.strip().lower()
    domain = re.sub(r"^https?://", "", domain)
    domain = domain.split("/")[0]
    return domain


async def enrich_domain(raw_domain: str) -> EnrichResponse:
    domain = _normalize(raw_domain)
    url = f"https://{domain}"
    detected: set[str] = set()
    title: Optional[str] = None
    description: Optional[str] = None
    has_careers = False

    async with httpx.AsyncClient(
        timeout=8.0, follow_redirects=True,
        headers={"User-Agent": "CapraeReadinessBot/1.0 (+demo)"},
    ) as client:
        try:
            r = await client.get(url)
        except Exception as e:
            return EnrichResponse(
                domain=domain, detected_stack=[], has_careers_page=False,
                title=None, description=f"Fetch failed: {e}",
            )

        for hk, mapping in HEADER_HINTS.items():
            v = r.headers.get(hk, "").lower()
            for needle, label in mapping.items():
                if needle in v:
                    detected.add(label)

        html = r.text[:200_000]
        for label, rx in HTML_PATTERNS.items():
            if rx.search(html):
                detected.add(label)

        soup = BeautifulSoup(html, "html.parser")
        if soup.title and soup.title.string:
            title = soup.title.string.strip()[:200]
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            description = meta["content"].strip()[:300]

        for a in soup.find_all("a", href=True):
            text_blob = (a.get_text() or "") + " " + a["href"]
            if CAREERS_RX.search(text_blob):
                has_careers = True
                break

    # Build a synthetic Company so we can run the same scoring pipeline.
    synthetic = Company(
        company_name=domain,
        domain=domain,
        industry="B2B SaaS",
        sub_industry="Unknown",
        employee_count=80,
        founded_year=2020,
        headquarters="Unknown",
        hq_country="US",
        last_funding_year=None,
        funding_total_usd=0,
        headcount_6mo_delta_pct=0.0,
        founder_is_ceo=True,
        has_pe_backing=False,
        tech_stack_signals=",".join(sorted(detected)),
        ai_job_posts_count=2 if has_careers else 0,
        recent_news_count=0,
        description=description or "",
    )
    score: ScoreBreakdown = score_company(synthetic)

    return EnrichResponse(
        domain=domain,
        detected_stack=sorted(detected),
        has_careers_page=has_careers,
        title=title,
        description=description,
        score_preview=score,
    )
