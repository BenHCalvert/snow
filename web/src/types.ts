export type Station = {
  t: string; // triplet, e.g. "637:ID:SNTL"
  name: string;
  st: string;
  elev: number;
  lat: number;
  lon: number;
  depth: number | null;
  dDepth3: number | null;
  dDepth7: number | null;
  swe: number | null;
  dSwe7: number | null;
  pctMed: number | null;
  tmax3: number | null;
  tmin3: number | null;
  asof: string | null;
  stale: boolean;
};

export type Hub = { id: string; name: string; lat: number; lon: number; drive: Record<string, number> };

export type Meta = { built: string; wy: number; stations: number; reporting: number };

export type Series = {
  t: string;
  name: string;
  wy: number;
  cur: { swe: (number | null)[]; depth: (number | null)[] };
  prev: { swe: (number | null)[]; depth: (number | null)[] };
  median: { swe: (number | null)[] };
};

export type MetricKey = "depth" | "dDepth3" | "pctMed";

/** A station plus its drive time from the selected hub. */
export type Reachable = Station & { hrs: number };
