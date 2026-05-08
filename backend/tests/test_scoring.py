from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models import Company  # noqa: E402
from scoring import score_company  # noqa: E402


def test_score_company_rewards_modern_ai_ready_profile() -> None:
    company = Company(
        company_name="Acme AI",
        domain="acme.ai",
        industry="B2B SaaS",
        sub_industry="AI Infrastructure",
        employee_count=120,
        founded_year=2020,
        headquarters="New York, NY",
        hq_country="US",
        last_funding_year=2026,
        funding_total_usd=10000000,
        headcount_6mo_delta_pct=35,
        founder_is_ceo=True,
        has_pe_backing=False,
        tech_stack_signals="react,nextjs,typescript,graphql,openai",
        ai_job_posts_count=12,
        recent_news_count=25,
        description="AI infrastructure for B2B SaaS teams.",
    )

    score = score_company(company)

    assert score.composite >= 85
    assert score.ai_readiness >= 80
    assert score.fit >= 80
