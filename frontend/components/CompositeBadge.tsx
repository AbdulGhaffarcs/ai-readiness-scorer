type Props = { value: number };

export default function CompositeBadge({ value }: Props) {
  const v = Math.round(value);
  let cls = "bg-bad/20 text-bad border-bad/30";
  if (v >= 75) cls = "bg-good/20 text-good border-good/30";
  else if (v >= 55) cls = "bg-warn/20 text-warn border-warn/30";
  return (
    <span
      className={`inline-flex h-7 min-w-[2.5rem] items-center justify-center rounded-md border px-2 font-mono text-sm font-semibold tabular-nums ${cls}`}
    >
      {v}
    </span>
  );
}
