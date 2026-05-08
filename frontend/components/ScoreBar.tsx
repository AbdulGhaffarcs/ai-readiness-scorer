type Props = {
  value: number;
  label?: string;
  className?: string;
};

function tone(v: number): string {
  if (v >= 75) return "bg-good";
  if (v >= 55) return "bg-warn";
  return "bg-bad";
}

export default function ScoreBar({ value, label, className = "" }: Props) {
  const v = Math.max(0, Math.min(100, value));
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {label && (
        <div className="w-24 shrink-0 text-xs text-zinc-400">{label}</div>
      )}
      <div className="relative h-1.5 flex-1 overflow-hidden rounded-full bg-ink-700">
        <div
          className={`absolute inset-y-0 left-0 ${tone(v)}`}
          style={{ width: `${v}%` }}
        />
      </div>
      <div className="w-9 text-right font-mono text-xs tabular-nums text-zinc-300">
        {v.toFixed(0)}
      </div>
    </div>
  );
}
