"use client";

import { useState } from "react";
import type { EnrichResponse } from "@/lib/types";
import ScoreBar from "./ScoreBar";

export default function EnrichPanel() {
  const [domain, setDomain] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<EnrichResponse | null>(null);

  async function go(e: React.FormEvent) {
    e.preventDefault();
    if (!domain.trim()) return;
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const r = await fetch("/api/enrich", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain: domain.trim() }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setData(await r.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-xl border border-line bg-ink-900 p-5">
      <div className="mb-3 flex items-baseline justify-between">
        <h2 className="text-sm font-semibold text-zinc-200">
          Score a new domain
        </h2>
        <span className="text-xs text-zinc-500">
          Live homepage scrape · stack sniff · score preview
        </span>
      </div>

      <form onSubmit={go} className="flex gap-2">
        <input
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          placeholder="acme.com"
          className="flex-1 rounded-md border border-line bg-ink-950 px-3 py-2 text-sm placeholder:text-zinc-600 focus:border-accent focus:outline-none"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-soft disabled:opacity-50"
        >
          {loading ? "Scoring..." : "Enrich"}
        </button>
      </form>

      {error && <p className="mt-3 text-sm text-bad">Error: {error}</p>}

      {data && (
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="rounded-md border border-line bg-ink-800 p-4 text-sm">
            <div className="mb-1 text-xs uppercase tracking-wide text-zinc-500">
              {data.domain}
            </div>
            <div className="font-medium text-zinc-100">
              {data.title || "(no title found)"}
            </div>
            {data.description && (
              <p className="mt-1 text-zinc-400">{data.description}</p>
            )}
            <div className="mt-3 flex flex-wrap gap-1.5">
              {data.detected_stack.length === 0 && (
                <span className="text-xs text-zinc-500">
                  No stack signals detected
                </span>
              )}
              {data.detected_stack.map((s) => (
                <span
                  key={s}
                  className="rounded border border-line bg-ink-900 px-1.5 py-0.5 font-mono text-[11px] text-zinc-300"
                >
                  {s}
                </span>
              ))}
            </div>
            <div className="mt-3 text-xs text-zinc-500">
              Careers page: {data.has_careers_page ? "yes" : "not detected"}
            </div>
          </div>

          {data.score_preview && (
            <div className="rounded-md border border-line bg-ink-800 p-4 text-sm">
              <div className="mb-3 flex items-baseline justify-between">
                <span className="text-xs uppercase tracking-wide text-zinc-500">
                  Score preview
                </span>
                <span className="font-mono text-2xl font-semibold text-zinc-100 tabular-nums">
                  {data.score_preview.composite.toFixed(0)}
                </span>
              </div>
              <div className="space-y-1.5">
                <ScoreBar
                  label="AI readiness"
                  value={data.score_preview.ai_readiness}
                />
                <ScoreBar label="Growth" value={data.score_preview.growth} />
                <ScoreBar label="Fit" value={data.score_preview.fit} />
              </div>
              {data.score_preview.reasons.length > 0 && (
                <ul className="mt-3 space-y-1 text-xs text-zinc-400">
                  {data.score_preview.reasons.map((r) => (
                    <li key={r}>- {r}</li>
                  ))}
                </ul>
              )}
              <p className="mt-3 text-[11px] text-zinc-600">
                Preview based only on public homepage signals - full score blends
                in firmographics, hiring data, and funding history.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
