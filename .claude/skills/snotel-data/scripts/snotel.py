#!/usr/bin/env python3
"""SNOTEL data helper (standard library only).

Subcommands:
  find  NAME [--state ID]                     search stations by name
  data  TRIPLET [TRIPLET...] --start --end    daily/hourly values (+ optional median)
  near  --lat --lon --hours H                 stations within a drive time, optional current conditions

Data source: NRCS AWDB REST API (https://wcc.sc.egov.usda.gov/awdbRestApi/).
Drive times: public OSRM demo server (router.project-osrm.org), summer road routing.
"""
import argparse, csv, json, math, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

API = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1"
OSRM = "https://router.project-osrm.org/table/v1/driving"
UA = {"User-Agent": "snotel-data-skill/1.0"}


def get_json(url, timeout=60, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))


def stations(state="*", network="SNTL"):
    q = urllib.parse.urlencode({
        "stationTriplets": f"*:{state}:{network}", "activeOnly": "true",
        "returnForecastPointMetadata": "false", "returnReservoirMetadata": "false",
        "returnStationElements": "false"})
    return get_json(f"{API}/stations?{q}")


def fetch(triplets, elements, start, end, duration="DAILY", median=False):
    """Return {triplet: {element: [(date, value, median), ...]}}."""
    out = {}
    for i in range(0, len(triplets), 50):
        params = {"stationTriplets": ",".join(triplets[i:i + 50]), "elements": ",".join(elements),
                  "duration": duration, "beginDate": start, "endDate": end}
        if median:
            params["centralTendencyType"] = "MEDIAN"
        for st in get_json(f"{API}/data?{urllib.parse.urlencode(params)}"):
            d = out.setdefault(st["stationTriplet"], {})
            for e in st.get("data", []):
                d[e["stationElement"]["elementCode"]] = [
                    (v["date"], v.get("value"), v.get("median")) for v in e.get("values", [])]
    return out


def haversine_mi(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2 +
         math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 7917.5 * math.asin(math.sqrt(a))


def drive_times(lat, lon, pts):
    """pts: list of (lat, lon). Returns list of (hours, miles, snap_m) per point."""
    res = []
    for i in range(0, len(pts), 90):
        chunk = pts[i:i + 90]
        coords = ";".join([f"{lon:.5f},{lat:.5f}"] + [f"{b:.5f},{a:.5f}" for a, b in chunk])
        d = get_json(f"{OSRM}/{coords}?sources=0&annotations=duration,distance")
        for dur, dist, dst in zip(d["durations"][0][1:], d["distances"][0][1:], d["destinations"][1:]):
            res.append((None if dur is None else dur / 3600,
                        None if dist is None else dist / 1609.34,
                        round(dst.get("distance", 0))))
        time.sleep(1)  # be polite to the free demo server
    return res


def write(rows, fields, out):
    if out:
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader(); w.writerows(rows)
        print(f"wrote {len(rows)} rows to {out}", file=sys.stderr)
    w = csv.DictWriter(sys.stdout, fieldnames=fields)
    w.writeheader(); w.writerows(rows)


def cmd_find(a):
    needle = a.name.lower()
    rows = [dict(triplet=s["stationTriplet"], name=s["name"], state=s["stateCode"],
                 elev_ft=int(s.get("elevation") or 0), lat=s["latitude"], lon=s["longitude"],
                 county=s.get("countyName"), since=(s.get("beginDate") or "")[:10])
            for s in stations(a.state or "*") if needle in s["name"].lower()]
    write(rows, ["triplet", "name", "state", "elev_ft", "lat", "lon", "county", "since"], a.out)


def cmd_data(a):
    els = a.elements.split(",")
    data = fetch(a.triplets, els, a.start, a.end, a.duration, a.median)
    rows = []
    for t, d in data.items():
        dates = sorted({x[0] for v in d.values() for x in v})
        for dt in dates:
            r = {"triplet": t, "date": dt}
            for e in els:
                hit = next((x for x in d.get(e, []) if x[0] == dt), None)
                r[e] = hit[1] if hit else None
                if a.median:
                    r[f"{e}_median"] = hit[2] if hit else None
            rows.append(r)
    fields = ["triplet", "date"] + [c for e in els for c in ([e, f"{e}_median"] if a.median else [e])]
    write(rows, fields, a.out)


def summarize(series, n):
    vals = [v for _, v, _ in series if v is not None]
    last = vals[-1] if vals else None
    chg = round(vals[-1] - vals[-1 - n], 1) if len(vals) > n else None
    return last, chg


def cmd_near(a):
    allst = stations(a.state or "*")
    radius = a.radius_mi or a.hours * 65  # straight-line prefilter
    cand = [s for s in allst if haversine_mi(a.lat, a.lon, s["latitude"], s["longitude"]) <= radius]
    print(f"{len(cand)} stations within {radius:.0f} mi straight-line; routing...", file=sys.stderr)
    dts = drive_times(a.lat, a.lon, [(s["latitude"], s["longitude"]) for s in cand])
    rows = []
    for s, (h, mi, snap) in zip(cand, dts):
        if h is not None and h <= a.hours:
            rows.append(dict(triplet=s["stationTriplet"], name=s["name"], state=s["stateCode"],
                             drive_hr=round(h, 2), drive_mi=round(mi), elev_ft=int(s.get("elevation") or 0),
                             road_gap_m=snap, lat=s["latitude"], lon=s["longitude"]))
    rows.sort(key=lambda r: r["drive_hr"])
    fields = ["triplet", "name", "state", "drive_hr", "drive_mi", "elev_ft", "road_gap_m", "lat", "lon"]
    if a.conditions and rows:
        end = date.today(); start = end - timedelta(days=8)
        data = fetch([r["triplet"] for r in rows], ["WTEQ", "SNWD", "TMAX", "TMIN"],
                     start.isoformat(), end.isoformat(), "DAILY", median=True)
        for r in rows:
            d = data.get(r["triplet"], {})
            swe, swe7 = summarize(d.get("WTEQ", []), 7)
            dep, dep3 = summarize(d.get("SNWD", []), 3)
            med = next((m for _, v, m in reversed(d.get("WTEQ", [])) if v is not None), None)
            tx = [v for _, v, _ in d.get("TMAX", [])[-3:] if v is not None]
            tn = [v for _, v, _ in d.get("TMIN", [])[-3:] if v is not None]
            asof = next((dt for dt, v, _ in reversed(d.get("SNWD", []) or d.get("WTEQ", [])) if v is not None), None)
            r.update(depth_in=dep, depth_chg_3d=dep3, swe_in=swe, swe_chg_7d=swe7,
                     swe_pct_median=round(100 * swe / med) if swe is not None and med else None,
                     tmax_3d=max(tx) if tx else None, tmin_3d=min(tn) if tn else None, asof=asof)
        fields += ["depth_in", "depth_chg_3d", "swe_in", "swe_chg_7d", "swe_pct_median",
                   "tmax_3d", "tmin_3d", "asof"]
    write(rows, fields, a.out)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("find"); f.add_argument("name"); f.add_argument("--state")
    d = sub.add_parser("data"); d.add_argument("triplets", nargs="+")
    d.add_argument("--start", required=True); d.add_argument("--end", required=True)
    d.add_argument("--elements", default="WTEQ,SNWD")
    d.add_argument("--duration", default="DAILY", choices=["DAILY", "HOURLY", "SEMIMONTHLY", "MONTHLY"])
    d.add_argument("--median", action="store_true", help="add 1991-2020 median columns (daily only)")
    n = sub.add_parser("near"); n.add_argument("--lat", type=float, required=True)
    n.add_argument("--lon", type=float, required=True); n.add_argument("--hours", type=float, default=4)
    n.add_argument("--radius-mi", type=float, help="straight-line prefilter (default hours*65)")
    n.add_argument("--state", help="limit to one state code")
    n.add_argument("--conditions", action="store_true", help="add current snow/temp summary")
    for sp in (f, d, n):
        sp.add_argument("--out", help="also write CSV to this path")
    a = p.parse_args()
    {"find": cmd_find, "data": cmd_data, "near": cmd_near}[a.cmd](a)


if __name__ == "__main__":
    main()
