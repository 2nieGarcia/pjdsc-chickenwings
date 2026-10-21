// One backtest row: which value is best, and whether the event model (first value) is behind it.
// dir < 0: lower is better; dir > 0: higher is better. null means the model has no score here.
export function scoreRow(vals, dir) {
  const known = vals.filter((x) => x != null);
  if (!known.length) return { best: null, behind: false };
  const best = dir < 0 ? Math.min(...known) : Math.max(...known);
  return { best, behind: vals[0] != null && vals[0] !== best };
}
