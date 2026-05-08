"use client";

import { useState } from "react";
import type { ScoredCompany } from "@/lib/types";
import CompositeBadge from "./CompositeBadge";
import ScoreBar from "./ScoreBar";

type Props = { c: ScoredCompany; rank: number };

export default function CompanyRow({ c, rank }: Props) {
  const [open, setOpen] = useState(false);
  const [angle, setAngle] = useState<string | null>(null);
  const [angleLoading, setAngleLoading] = useState(false);

  async function loadAngle() {
    if (angle || angleLoading) return;
    setAngleLoading(true);
    try {
      const r = await fetch(
        `/api/companies/scored/${encodeURIComponent(c.domain)}/outreach`,
      );
      const j = await r.json();
      setAngle(j.outreach_angle ?? "");
    } catch {
      setAngle("(failed to load)");
    } finally {
      setAngleLoading(false);
    }
  }

  function toggle() {
    setOpen((o) => {
      const next = !o;
      if (next) loadAngle();
      return next;
    });
  }

  const stackTokens = c.tech_stack_signals
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);

  return (
    <>
      <tr
        onClick={toggle}
        className="cursor-pointer border-b border-line hover:bg-ink-800/60"
      >
        <td className="py-3 pl-4 pr-2 text-right font-mono text-xs text-zinc-500 tabular-nums">
          {rank}
        </td>
        <td className="py-3 pr-3">
          <div className="font-medium text-zinc-100">{c.company_name}</div>
          <div className="font-mono text-xs text-zinc-500">{c.domain}</div>
        </td>
        <td className="py-3 pr-3 text-sm text-zinc-300">{c.sub_industry}</td>
        <td className="py-3 pr-3 text-right font-mono text-sm text-zinc-300 tabular-nums">
          {c.employee_count}
        </td>
        <td className="py-3 pr-3 text-right font-mono text-sm tabular-nums">
          <span
            className={
              c.headcount_6mo_delta_pct >= 0 ? "text-good" : "text-bad"
            }
          >
            {c.headcount_6mo_delta_pct >= 0 ? "+" : ""}
            {c.headcount_6mo_delta_pct.toFixed(0)}%
          </span>
        </td>
        <td className="py-3 pr-4 text-right">
          <CompositeBadge value={c.score.composite} />
        </td>
      </tr>
      {open && (
        <tr className="border-b border-line bg-ink-800/40">
          <td colSpan={6} className="px-4 py-5">
            <div className="grid gap-6 md:grid-cols-2">
              <div>
                <div className="mb-2 text-xs uppercase tracking-wide text-zinc-500">
                  Score breakdown
                </div>
                <div className="space-y-1.5">
                  <ScoreBar label="AI readiness" value={c.score.ai_readiness} />
                  <ScoreBar label="Growth" value={c.score.growth} />
                  <ScoreBar label="Fit" value={c.score.fit} />
                </div>
                <div className="mt-3 text-xs uppercase tracking-wide text-zinc-500">
                  Top reasons
                </div>
                <ul className="mt-1 space-y-1 text-sm text-zinc-300">
                  {c.score.reasons.length === 0 && (
                    <li className="text-zinc-500">No standout signals</li>
                  )}
                  {c.score.reasons.map((r) => (
                    <li key={r}>- {r}</li>
                  ))}
                </ul>
              </div>
              <div>
                <div className="mb-2 text-xs uppercase tracking-wide text-zinc-500">
                  Profile
                </div>
                <div className="text-sm text-zinc-300">{c.description}</div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-zinc-400">
                  <div>
                    HQ <span className="text-zinc-200">{c.headquarters}</span>
                  </div>
                  <div>
                    Founded <span className="text-zinc-200">{c.founded_year}</span>
                  </div>
                  <div>
                    Founder-CEO{" "}
                    <span className="text-zinc-200">
                      {c.founder_is_ceo ? "yes" : "no"}
                    </span>
                  </div>
                  <div>
                    PE-backed{" "}
                    <span className="text-zinc-200">
                      {c.has_pe_backing ? "yes" : "no"}
                    </span>
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {stackTokens.map((t) => (
                    <span
                      key={t}
                      className="rounded border border-line bg-ink-900 px-1.5 py-0.5 font-mono text-[11px] text-zinc-300"
                    >
                      {t}
                    </span>
                  ))}
                </div>

                <div className="mt-4 rounded-md border border-line bg-ink-900 p-3">
                  <div className="mb-1 text-xs uppercase tracking-wide text-accent-soft">
                    Outreach angle
                  </div>
                  <div className="text-sm text-zinc-200">
                    {angleLoading ? "Generating..." : (angle ?? "Loading...")}
                  </div>
                  <div className="mt-2 text-[11px] text-zinc-600">
                    Generated by Claude (or deterministic fallback when no API
                    key is set). Cached per domain.
                  </div>
                </div>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
