from typing import Optional
from pydantic import BaseModel, Field


class Company(BaseModel):
    company_name: str
    domain: str
    industry: str
    sub_industry: str
    employee_count: int
    founded_year: int
    headquarters: str
    hq_country: str
    last_funding_year: Optional[int] = None
    funding_total_usd: int = 0
    headcount_6mo_delta_pct: float = 0.0
    founder_is_ceo: bool = False
    has_pe_backing: bool = False
    tech_stack_signals: str = ""
    ai_job_posts_count: int = 0
    recent_news_count: int = 0
    description: str = ""


class ScoreBreakdown(BaseModel):
    composite: float
    ai_readiness: float
    growth: float
    fit: float
    reasons: list[str] = Field(default_factory=list)


class ScoredCompany(Company):
    score: ScoreBreakdown
    outreach_angle: Optional[str] = None


class EnrichRequest(BaseModel):
    domain: str


class EnrichResponse(BaseModel):
    domain: str
    detected_stack: list[str]
    has_careers_page: bool
    title: Optional[str] = None
    description: Optional[str] = None
    score_preview: Optional[ScoreBreakdown] = None
