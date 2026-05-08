"use client";

export type FilterState = {
  minScore: number;
  subIndustry: string | null;
  sizeBand: string | null;
};

type Props = {
  state: FilterState;
  onChange: (s: FilterState) => void;
  subIndustries: string[];
  totalCount: number;
  visibleCount: number;
  onExport: () => void;
};

const SIZE_BANDS: { id: string; label: string }[] = [
  { id: "micro", label: "<30" },
  { id: "smb", label: "30-200" },
  { id: "mid", label: "200-500" },
  { id: "large", label: ">500" },
];

export default function Filters({
  state,
  onChange,
  subIndustries,
  totalCount,
  visibleCount,
  onExport,
}: Props) {
  return (
    <div className="rounded-xl border border-line bg-ink-900 p-4">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3 text-sm">
        <div className="flex items-center gap-3">
          <label className="text-xs uppercase tracking-wide text-zinc-500">
            Min score
          </label>
          <input
            type="range"
            min={0}
            max={100}
            step={5}
            value={state.minScore}
            onChange={(e) =>
              onChange({ ...state, minScore: Number(e.target.value) })
            }
            className="w-40 accent-accent"
          />
          <span className="w-8 font-mono text-xs tabular-nums text-zinc-300">
            {state.minScore}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs uppercase tracking-wide text-zinc-500">
            Size
          </label>
          <div className="flex rounded-md border border-line bg-ink-950 p-0.5">
            {SIZE_BANDS.map((b) => {
              const active = state.sizeBand === b.id;
              return (
                <button
                  key={b.id}
                  onClick={() =>
                    onChange({ ...state, sizeBand: active ? null : b.id })
                  }
                  className={`rounded px-2 py-1 text-xs ${
                    active
                      ? "bg-accent text-white"
                      : "text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  {b.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs uppercase tracking-wide text-zinc-500">
            Vertical
          </label>
          <select
            value={state.subIndustry ?? ""}
            onChange={(e) =>
              onChange({
                ...state,
                subIndustry: e.target.value || null,
              })
            }
            className="rounded-md border border-line bg-ink-950 px-2 py-1 text-xs"
          >
            <option value="">All</option>
            {subIndustries.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        <div className="ml-auto flex items-center gap-3">
          <span className="text-xs text-zinc-500">
            {visibleCount} / {totalCount} companies
          </span>
          <button
            onClick={onExport}
            className="rounded-md border border-line px-3 py-1 text-xs hover:border-accent hover:text-accent"
          >
            Export CSV
          </button>
        </div>
      </div>
    </div>
  );
}
