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
    // Viridis: yellow → green → blue → purple. Colorblind-safe and stays clear of the gray basemap.
    stops: [[0, "#fde725"], [3, "#5ec962"], [12, "#21918c"], [24, "#3b528b"], [48, "#440154"]],
    format: (s) => (s.depth == null ? "–" : `${s.depth}"`),
    help: "Current snow depth at the sensor, in inches.",
  },
  dDepth3: {
    label: "New snow (3 days)",
    short: "3-day",
    unit: '"',
    stops: [[-99, "#fde725"], [1, "#5ec962"], [3, "#21918c"], [6, "#3b528b"], [12, "#440154"]],
    format: (s) => signed(s.dDepth3, '"'),
    help: "Change in snow depth over the last 3 days. Small changes (±1\") are often sensor noise or settling.",
  },
  pctMed: {
    label: "% of normal (SWE)",
    short: "% med",
    unit: "%",
    // RdYlBu: the "normal" band is pale yellow, not a gray that disappears into the basemap.
    stops: [[0, "#d73027"], [50, "#fc8d59"], [90, "#fee090"], [110, "#91bfdb"], [150, "#4575b4"]],
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
