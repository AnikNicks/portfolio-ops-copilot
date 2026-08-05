export function formatDollarRange(low: number, high: number): string {
  const fmt = (n: number) => `$${(n / 1000).toFixed(0)}K`;
  return `${fmt(low)}–${fmt(high)}/yr`;
}

export function titleCase(slug: string): string {
  return slug
    .split("-")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
