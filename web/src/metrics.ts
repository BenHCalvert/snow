import type { MetricKey, Station } from "./types";

type Metric = {
  label: string;
  short: string;
  unit: string;
  /** [threshold, color] stops, ascending. */
  stops: [number, string][];
  format: (s: Station) => string;
  help: string;
};

const signed = (v: number | null, u: string) => (v == null ? "–" : `${v > 0 ? "+" : ""}${v}${u}`);

export const METRICS: Record<MetricKey, Metric> = {
  depth: {
    label: "Snow depth",
    short: "Depth",
    unit: '"',
    stops: [[0, "#d9d4cc"], [3, "#c6dbef"], [12, "#6baed6"], [24, "#2171b5"], [48, "#08306b"]],
    format: (s) => (s.depth == null ? "–" : `${s.depth}"`),
    help: "Current snow depth at the sensor, in inches.",
  },
  dDepth3: {
    label: "New snow (3 days)",
    short: "3-day",
    unit: '"',
    stops: [[-99, "#d9d4cc"], [1, "#c7e9c0"], [3, "#74c476"], [6, "#31a354"], [12, "#006d2c"]],
    format: (s) => signed(s.dDepth3, '"'),
    help: "Change in snow depth over the last 3 days. Small changes (±1\") are often sensor noise or settling.",
  },
  pctMed: {
    label: "% of normal (SWE)",
    short: "% med",
    unit: "%",
    stops: [[0, "#b2182b"], [50, "#ef8a62"], [90, "#e7e1d8"], [110, "#67a9cf"], [150, "#2166ac"]],
    format: (s) => (s.pctMed == null ? "–" : `${s.pctMed}%`),
    help: "Snow water equivalent compared with the 1991–2020 median for today's date.",
  },
};

export function colorFor(key: MetricKey, s: Station): string {
  const v = s[key];
  if (v == null) return "#bdbdbd";
  const stops = METRICS[key].stops;
  let c = stops[0][1];
  for (const [t, col] of stops) if (v >= t) c = col;
  return c;
}

/** Sort key: higher is better for every metric we offer. */
export const rankValue = (key: MetricKey, s: Station) => s[key] ?? -Infinity;
