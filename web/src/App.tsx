import { useEffect, useMemo, useState } from "react";
import SnowMap from "./components/SnowMap";
import SiteDetail from "./components/SiteDetail";
import { METRICS, colorFor, rankValue } from "./metrics";
import type { Hub, Meta, MetricKey, Reachable, Station } from "./types";

// State lives in the URL so any view can be shared: ?from=boise&hours=3&metric=pctMed&site=637:ID:SNTL
const params = new URLSearchParams(location.search);

export default function App() {
  const [stations, setStations] = useState<Station[]>([]);
  const [hubs, setHubs] = useState<Hub[]>([]);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [error, setError] = useState(false);
  const [hubId, setHubId] = useState(params.get("from") ?? "boise");
  const [hours, setHours] = useState(Number(params.get("hours") ?? 4));
  const [metric, setMetric] = useState<MetricKey>((params.get("metric") as MetricKey) ?? "depth");
  const [selected, setSelected] = useState<string | null>(params.get("site"));

  useEffect(() => {
    const get = (f: string) => fetch(`./data/${f}`).then((r) => (r.ok ? r.json() : Promise.reject(f)));
    Promise.all([get("stations.json"), get("hubs.json"), get("meta.json")])
      .then(([s, h, m]) => { setStations(s); setHubs(h); setMeta(m); })
      .catch(() => setError(true));
  }, []);

  useEffect(() => {
    const p = new URLSearchParams({ from: hubId, hours: String(hours), metric });
    if (selected) p.set("site", selected);
    history.replaceState(null, "", `?${p}`);
  }, [hubId, hours, metric, selected]);

  const hub = hubs.find((h) => h.id === hubId) ?? hubs[0];
  const reachable: Reachable[] = useMemo(() => {
    if (!hub) return [];
    return stations
      .filter((s) => hub.drive[s.t] != null && hub.drive[s.t] <= hours)
      .map((s) => ({ ...s, hrs: hub.drive[s.t] }))
      .sort((a, b) => rankValue(metric, b) - rankValue(metric, a) || a.hrs - b.hrs);
  }, [stations, hub, hours, metric]);
  const sel = reachable.find((s) => s.t === selected) ?? null;

  if (error) return <div className="empty">Couldn't load snow data. Try refreshing in a minute.</div>;
  if (!hub) return <div className="empty">Loading snow data…</div>;

  return (
    <div className="app">
      <aside className="panel">
        <header className="brand">
          <h1>❄️ Snow Within Reach</h1>
        </header>

        <div className="controls">
          <label>
            Starting from
            <select value={hubId} onChange={(e) => { setHubId(e.target.value); setSelected(null); }}>
              {hubs.map((h) => <option key={h.id} value={h.id}>{h.name}</option>)}
            </select>
          </label>
          <label>
            Max drive: <strong>{hours} hr</strong>
            <input type="range" min={1} max={8} step={0.5} value={hours} onChange={(e) => setHours(Number(e.target.value))} />
          </label>
          <div className="seg" role="radiogroup" aria-label="Color sites by">
            {(Object.keys(METRICS) as MetricKey[]).map((k) => (
              <button key={k} role="radio" aria-checked={metric === k} className={metric === k ? "on" : ""} onClick={() => setMetric(k)}>
                {METRICS[k].label}
              </button>
            ))}
          </div>
          <p className="muted small">{METRICS[metric].help}</p>
        </div>

        {sel ? (
          <SiteDetail site={sel} onClose={() => setSelected(null)} />
        ) : (
          <>
            <p className="count">
              <strong>{reachable.length}</strong> SNOTEL sites within {hours} hr of {hub.name}, ranked by {METRICS[metric].label.toLowerCase()}
            </p>
            <ol className="list">
              {reachable.map((s) => (
                <li key={s.t}>
                  <button onClick={() => setSelected(s.t)}>
                    <span className="dot" style={{ background: colorFor(metric, s) }} />
                    <span className="name">
                      {s.name} <span className="muted">{s.st} · {s.elev.toLocaleString()}'</span>
                      {s.stale && <span className="warn"> · stale</span>}
                    </span>
                    <span className="val">{METRICS[metric].format(s)}</span>
                    <span className="hrs muted">{s.hrs.toFixed(1)}h</span>
                  </button>
                </li>
              ))}
            </ol>
          </>
        )}

        <footer className="muted small">
          Data: NRCS SNOTEL{meta && <> · updated {new Date(meta.built).toLocaleString()}</>}. Drive times assume
          summer roads, so check closures before you go. Faded dots haven't reported in 2+ days.
        </footer>
      </aside>

      <main>
        <SnowMap hub={hub} sites={reachable} metric={metric} selected={selected} onSelect={setSelected} />
      </main>
    </div>
  );
}
