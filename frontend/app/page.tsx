"use client";

import { useEffect, useMemo, useState } from "react";
import type { ScoredCompany } from "@/lib/types";
import CompanyRow from "@/components/CompanyRow";
import EnrichPanel from "@/components/EnrichPanel";
import Filters, { type FilterState } from "@/components/Filters";

type SortKey = "company" | "vertical" | "headcount" | "growth" | "score";
type SortDirection = "asc" | "desc";

export default function Home() {
  const [rows, setRows] = useState<ScoredCompany[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("score");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [filters, setFilters] = useState<FilterState>({
    minScore: 0,
    subIndustry: null,
    sizeBand: null,
  });

  useEffect(() => {
    fetch("/api/companies/scored")
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setRows)
      .catch((e) => setError(String(e)));
  }, []);

  const subIndustries = useMemo(() => {
    if (!rows) return [];
    return Array.from(new Set(rows.map((r) => r.sub_industry))).sort();
  }, [rows]);

  const visible = useMemo(() => {
    if (!rows) return [];
    const filtered = rows.filter((r) => {
      if (r.score.composite < filters.minScore) return false;
      if (filters.subIndustry && r.sub_industry !== filters.subIndustry) {
        return false;
      }
      if (filters.sizeBand) {
        const n = r.employee_count;
        const ok =
          (filters.sizeBand === "micro" && n < 30) ||
          (filters.sizeBand === "smb" && n >= 30 && n <= 200) ||
          (filters.sizeBand === "mid" && n > 200 && n <= 500) ||
          (filters.sizeBand === "large" && n > 500);
        if (!ok) return false;
      }
      return true;
    });

    return [...filtered].sort((a, b) => {
      const direction = sortDirection === "asc" ? 1 : -1;
      switch (sortKey) {
        case "company":
          return a.company_name.localeCompare(b.company_name) * direction;
        case "vertical":
          return a.sub_industry.localeCompare(b.sub_industry) * direction;
        case "headcount":
          return (a.employee_count - b.employee_count) * direction;
        case "growth":
          return (a.headcount_6mo_delta_pct - b.headcount_6mo_delta_pct) * direction;
        case "score":
        default:
          return (a.score.composite - b.score.composite) * direction;
      }
    });
  }, [filters, rows, sortDirection, sortKey]);

  function setSort(nextKey: SortKey) {
    if (sortKey === nextKey) {
      setSortDirection((value) => (value === "desc" ? "asc" : "desc"));
      return;
    }
    setSortKey(nextKey);
    setSortDirection(
      nextKey === "company" || nextKey === "vertical" ? "asc" : "desc",
    );
  }

  function exportCsv() {
    const params = new URLSearchParams();
    if (filters.minScore > 0) params.set("min_score", String(filters.minScore));
    if (filters.subIndustry) params.set("sub_industry", filters.subIndustry);
    if (filters.sizeBand) params.set("size_band", filters.sizeBand);
    window.location.href = `/api/export.csv?${params.toString()}`;
  }

  function sortLabel(key: SortKey) {
    if (sortKey !== key) return "";
    return sortDirection === "desc" ? " v" : " ^";
  }

  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <header className="mb-8 flex items-end justify-between gap-6">
        <div>
          <div className="mb-1 text-xs font-medium uppercase tracking-[0.18em] text-accent-soft">
            Caprae Capital - Lead Intelligence
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-50">
            AI-Readiness &amp; Acquisition Fit Scorer
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-zinc-400">
            Volume in, signal out. Every B2B SaaS company is scored on three
            dimensions - how ready they are to absorb AI, whether they&apos;re
            growing, and whether they fit Caprae&apos;s lower-middle-market buy
            box. Click a row to see why a score landed where it did, plus a
            ready-to-send outreach hook.
          </p>
        </div>
      </header>

      <div className="mb-6">
        <EnrichPanel />
      </div>

      <div className="mb-3">
        <Filters
          state={filters}
          onChange={setFilters}
          subIndustries={subIndustries}
          totalCount={rows?.length ?? 0}
          visibleCount={visible.length}
          onExport={exportCsv}
        />
      </div>

      {error && (
        <div className="rounded-md border border-bad/40 bg-bad/10 p-4 text-sm text-bad">
          Failed to load: {error}. Make sure the FastAPI backend is running on
          port 8765.
        </div>
      )}

      {!rows && !error && (
        <div className="rounded-md border border-line bg-ink-900 p-8 text-center text-sm text-zinc-500">
          Loading scored leads...
        </div>
      )}

      {rows && (
        <div className="overflow-hidden rounded-xl border border-line bg-ink-900">
          <table className="w-full">
            <thead className="border-b border-line bg-ink-800/60 text-xs uppercase tracking-wide text-zinc-500">
              <tr>
                <th className="py-2 pl-4 pr-2 text-right font-medium">#</th>
                <th className="py-2 pr-3 text-left font-medium">
                  <button onClick={() => setSort("company")}>
                    Company{sortLabel("company")}
                  </button>
                </th>
                <th className="py-2 pr-3 text-left font-medium">
                  <button onClick={() => setSort("vertical")}>
                    Vertical{sortLabel("vertical")}
                  </button>
                </th>
                <th className="py-2 pr-3 text-right font-medium">
                  <button onClick={() => setSort("headcount")}>
                    Headcount{sortLabel("headcount")}
                  </button>
                </th>
                <th className="py-2 pr-3 text-right font-medium">
                  <button onClick={() => setSort("growth")}>
                    6mo Delta{sortLabel("growth")}
                  </button>
                </th>
                <th className="py-2 pr-4 text-right font-medium">
                  <button onClick={() => setSort("score")}>
                    Score{sortLabel("score")}
                  </button>
                </th>
              </tr>
            </thead>
            <tbody>
              {visible.map((c, i) => (
                <CompanyRow key={c.domain} c={c} rank={i + 1} />
              ))}
              {visible.length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-8 text-center text-sm text-zinc-500"
                  >
                    No companies match the current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      <footer className="mt-10 flex flex-wrap items-center justify-between gap-3 text-xs text-zinc-500">
        <span>
          Prototype dataset: 66 hand-curated B2B SaaS companies. Production:
          feed this scorer with the SaaSquatchLeads scraper output.
        </span>
        <span className="font-mono">AI-readiness 40% - Growth 30% - Fit 30%</span>
      </footer>
    </main>
  );
}
