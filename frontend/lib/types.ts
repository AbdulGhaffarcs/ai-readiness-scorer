export type ScoreBreakdown = {
  composite: number;
  ai_readiness: number;
  growth: number;
  fit: number;
  reasons: string[];
};

export type ScoredCompany = {
  company_name: string;
  domain: string;
  industry: string;
  sub_industry: string;
  employee_count: number;
  founded_year: number;
  headquarters: string;
  hq_country: string;
  last_funding_year: number | null;
  funding_total_usd: number;
  headcount_6mo_delta_pct: number;
  founder_is_ceo: boolean;
  has_pe_backing: boolean;
  tech_stack_signals: string;
  ai_job_posts_count: number;
  recent_news_count: number;
  description: string;
  score: ScoreBreakdown;
};

export type EnrichResponse = {
  domain: string;
  detected_stack: string[];
  has_careers_page: boolean;
  title: string | null;
  description: string | null;
  score_preview: ScoreBreakdown | null;
};
