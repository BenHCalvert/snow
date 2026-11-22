import { useEffect, useRef } from "react";
import maplibregl, { GeoJSONSource, Map as MlMap } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { Hub, MetricKey, Reachable } from "../types";
import { colorFor } from "../metrics";

// Free vector basemap, no API key: https://openfreemap.org
const STYLE = "https://tiles.openfreemap.org/styles/positron";

type Props = {
  hub: Hub;
  sites: Reachable[];
  metric: MetricKey;
  selected: string | null;
  onSelect: (t: string) => void;
};

export default function SnowMap({ hub, sites, metric, selected, onSelect }: Props) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<MlMap | null>(null);
  const ready = useRef(false);
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;

  useEffect(() => {
    const m = new maplibregl.Map({ container: el.current!, style: STYLE, center: [hub.lon, hub.lat], zoom: 6, attributionControl: false });
    m.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");
    m.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    m.on("load", () => {
      m.addSource("sites", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      m.addSource("hub", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      m.addLayer({
        id: "sites",
        type: "circle",
        source: "sites",
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 5, 5, 9, 10],
          "circle-color": ["get", "color"],
          "circle-opacity": ["case", ["get", "stale"], 0.35, 0.95],
          "circle-stroke-width": ["case", ["get", "sel"], 3, 1],
          "circle-stroke-color": ["case", ["get", "sel"], "#111", "#fff"],
        },
      });
      m.addLayer({
        id: "hub",
        type: "circle",
        source: "hub",
        paint: { "circle-radius": 7, "circle-color": "#1d2329", "circle-stroke-width": 3, "circle-stroke-color": "#fff" },
      });
      m.on("click", "sites", (e) => {
        const t = e.features?.[0]?.properties?.t;
        if (t) onSelectRef.current(t);
      });
      m.on("mouseenter", "sites", () => (m.getCanvas().style.cursor = "pointer"));
      m.on("mouseleave", "sites", () => (m.getCanvas().style.cursor = ""));
      ready.current = true;
      m.fire("data-ready");
    });
    map.current = m;
    return () => m.remove();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Push data into the map whenever inputs change.
  useEffect(() => {
    const m = map.current;
    if (!m) return;
    const update = () => {
      (m.getSource("sites") as GeoJSONSource).setData({
        type: "FeatureCollection",
        features: sites.map((s) => ({
          type: "Feature",
          geometry: { type: "Point", coordinates: [s.lon, s.lat] },
          properties: { t: s.t, color: colorFor(metric, s), stale: s.stale, sel: s.t === selected },
        })),
      });
      (m.getSource("hub") as GeoJSONSource).setData({
        type: "Feature",
        geometry: { type: "Point", coordinates: [hub.lon, hub.lat] },
        properties: {},
      });
    };
    if (ready.current) update();
    else m.once("data-ready", update);
  }, [sites, metric, selected, hub]);

  // Re-frame the map when the hub or the reachable set changes size.
  useEffect(() => {
    const m = map.current;
    if (!m || sites.length === 0) return;
    const b = new maplibregl.LngLatBounds([hub.lon, hub.lat], [hub.lon, hub.lat]);
    sites.forEach((s) => b.extend([s.lon, s.lat]));
    m.fitBounds(b, { padding: 40, maxZoom: 8, duration: 600 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hub.id, sites.length]);

  return <div ref={el} className="map" aria-label="Map of SNOTEL sites" />;
}
