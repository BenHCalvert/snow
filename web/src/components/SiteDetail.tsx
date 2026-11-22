import { useEffect, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Reachable, Series } from "../types";

const MONTHS = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"];
const fmtDay = (i: number) => {
  const d = new Date(Date.UTC(2001, 9, 1) + i * 86400000); // any non-leap water year works for labels
  return `${MONTHS[(d.getUTCMonth() + 3) % 12]} ${d.getUTCDate()}`;
};

export default function SiteDetail({ site, onClose }: { site: Reachable; onClose: () => void }) {
  const [series, setSeries] = useState<Series | null>(null);
  const [err, setErr] = useState(false);
  const file = `${site.t.split(":")[0]}_${site.t.split(":")[1]}.json`;

  useEffect(() => {
    setSeries(null);
    setErr(false);
    fetch(`./data/series/${file}`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setSeries)
      .catch(() => setErr(true));
  }, [file]);

  // Chart from Oct 1 to the later of today+45 days or Jun 30, so early-season charts aren't squashed.
  const rows = series
    ? Array.from({ length: Math.min(365, Math.max(series.cur.swe.length + 45, 273)) }, (_, i) => ({
        day: i,
        thisYear: series.cur.swe[i] ?? null,
        lastYear: series.prev.swe[i] ?? null,
        median: series.median.swe[i] ?? null,
      }))
    : [];

  return (
    <section className="detail" aria-label={`${site.name} details`}>
      <header>
        <div>
          <h2>{site.name}</h2>
          <p className="muted">
            {site.st} · {site.elev.toLocaleString()} ft · {site.hrs.toFixed(1)} hr drive
          </p>
        </div>
        <button className="close" onClick={onClose} aria-label="Close details">×</button>
      </header>

      <dl className="stats">
        <div><dt>Depth</dt><dd>{site.depth ?? "–"}"</dd></div>
        <div><dt>SWE</dt><dd>{site.swe ?? "–"}"</dd></div>
        <div><dt>% of normal</dt><dd>{site.pctMed == null ? "–" : `${site.pctMed}%`}</dd></div>
        <div><dt>3-day Δ</dt><dd>{site.dDepth3 == null ? "–" : `${site.dDepth3 > 0 ? "+" : ""}${site.dDepth3}"`}</dd></div>
        <div><dt>3-day hi / lo</dt><dd>{site.tmax3 == null ? "–" : `${Math.round(site.tmax3)}° / ${Math.round(site.tmin3 ?? 0)}°`}</dd></div>
        <div><dt>As of</dt><dd className={site.stale ? "warn" : ""}>{site.asof ? new Date(`${site.asof}T12:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" }) : "–"}</dd></div>
      </dl>

      <h3>Snow water equivalent this season</h3>
      {err && <p className="muted">Couldn't load the season history for this site.</p>}
      {!series && !err && <p className="muted">Loading…</p>}
      {series && (
        <div className="chart">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={rows} margin={{ top: 8, right: 12, bottom: 0, left: -18 }}>
              <CartesianGrid stroke="#eee" />
              <XAxis dataKey="day" tickFormatter={fmtDay} ticks={[0, 61, 123, 182, 243]} fontSize={11} />
              <YAxis unit='"' fontSize={11} />
              <Tooltip labelFormatter={(d) => fmtDay(Number(d))} formatter={(v) => (v == null ? "–" : `${v}"`)} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line dataKey="median" name="Median (1991–2020)" stroke="#9e9e9e" strokeDasharray="4 3" dot={false} connectNulls />
              <Line dataKey="lastYear" name={`Last season`} stroke="#90caf9" dot={false} connectNulls />
              <Line dataKey="thisYear" name="This season" stroke="#1565c0" strokeWidth={2.5} dot={false} connectNulls />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
      <p className="muted small">
        <a href={`https://wcc.sc.egov.usda.gov/nwcc/site?sitenum=${site.t.split(":")[0]}`} target="_blank" rel="noreferrer">
          NRCS station page ↗
        </a>
      </p>
    </section>
  );
}
