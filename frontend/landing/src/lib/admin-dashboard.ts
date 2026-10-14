// A complete workload total must never treat an unavailable source as zero.
export function sumAvailableCounts(values: Array<number | null | undefined>): number | null {
  if (values.some((value) => value === null || value === undefined || !Number.isFinite(value))) return null;
  return (values as number[]).reduce((sum, value) => sum + value, 0);
}
