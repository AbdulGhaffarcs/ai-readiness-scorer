"""
Outreach-angle generation via Claude.

The LLM call is optional: if ANTHROPIC_API_KEY is not set, we fall back to a
deterministic template so the demo runs end-to-end without a key. Production
deploys with a key, while local development and CI can run without one.
"""
from __future__ import annotations

import os

from models import Company, ScoreBreakdown

try:
    from anthropic import Anthropic  # type: ignore
except Exception:  # pragma: no cover
    Anthropic = None  # type: ignore


_SYSTEM_PROMPT = (
    "You are a senior PE-backed sales analyst writing one outreach hook "
    "for a Caprae Capital deal team. Keep it to ONE sentence, max 30 words, "
    "no fluff, no greetings, no signoff. Lead with the most acquisition-relevant "
    "signal. Reference the company's actual situation, not generic SaaS talk."
)


def _fallback_angle(c: Company, s: ScoreBreakdown) -> str:
    """Deterministic template used when no API key is configured."""
    if s.ai_readiness >= 70:
        lead = (
            f"{c.company_name}'s AI-native stack means a Caprae play here is "
            "acceleration, not a rebuild"
        )
    elif s.growth >= 70:
        lead = (
            f"{c.company_name} is hiring fast - perfect window to introduce "
            "Caprae's post-acquisition AI playbook"
        )
    elif s.fit >= 70:
        lead = (
            f"{c.company_name} sits squarely in Caprae's lower-middle-market "
            "buy box and shows owner-operator signals"
        )
    else:
        lead = (
            f"{c.company_name} is worth a conversation: "
            f"{s.reasons[0] if s.reasons else 'fit signal mix'}"
        )
    return lead + "."


def generate_outreach(c: Company, s: ScoreBreakdown) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or Anthropic is None:
        return _fallback_angle(c, s)

    client = Anthropic(api_key=api_key)
    user = (
        f"Company: {c.company_name} ({c.domain})\n"
        f"Industry: {c.industry} / {c.sub_industry}\n"
        f"Size: {c.employee_count} employees, founded {c.founded_year}\n"
        f"Headcount 6mo delta: {c.headcount_6mo_delta_pct:+.0f}%\n"
        f"Composite score: {s.composite}/100 "
        f"(AI {s.ai_readiness}, Growth {s.growth}, Fit {s.fit})\n"
        f"Top signals: {'; '.join(s.reasons) if s.reasons else 'none'}\n"
        f"Description: {c.description}"
    )
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=120,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(
        block.text for block in msg.content if getattr(block, "type", "") == "text"
    ).strip()
    return text or _fallback_angle(c, s)
