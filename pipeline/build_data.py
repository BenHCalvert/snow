"""Fetch current SNOTEL data for the West and write the static JSON the web app reads.

    python3 pipeline/build_data.py [--out web/public/data] [--states ID,OR]

Writes:
  stations.json         one record per station with current metrics (map + list)
  hubs.json             hub cities + drive times (copied from pipeline/)
  series/<id>_<st>.json this season, last season, and median SWE/depth by day of water year (charts)
  meta.json             build time and counts
"""
import argparse
import json
import pathlib
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from metrics import (align_to_wy, change_over, is_stale, last_valid,  # noqa: E402
                     pct_of_median, water_year, wy_start)
from snotel_api import WESTERN_STATES, daily, stations  # noqa: E402

ROOT = pathlib.Path(__file__).parent
BATCH = 25


def build(out_dir: pathlib.Path, states):
    today = date.today()
    wy = water_year(today)
    start = wy_start(wy - 1).isoformat()  # last season + this season in one request
    sts = [s for st in states for s in stations(st)]
    print(f"{len(sts)} stations; fetching {start}..{today}", file=sys.stderr)

    batches = [[s["stationTriplet"] for s in sts[i:i + BATCH]] for i in range(0, len(sts), BATCH)]
    raw = {}
    with ThreadPoolExecutor(4) as ex:
        for part in ex.map(lambda b: daily(b, ["WTEQ", "SNWD", "TMAX", "TMIN"], start, today.isoformat(),
                                           median=True), batches):
            raw.update(part)

    (out_dir / "series").mkdir(parents=True, exist_ok=True)
    cur_days = (today - wy_start(wy)).days + 1
    prev_days = (wy_start(wy) - wy_start(wy - 1)).days
    records = []
    for s in sts:
        t = s["stationTriplet"]
        d = raw.get(t, {})
        val = {e: {k: v[0] for k, v in d.get(e, {}).items()} for e in ("WTEQ", "SNWD", "TMAX", "TMIN")}
        med = {k: v[1] for k, v in d.get("WTEQ", {}).items()}
        swe_s = sorted(val["WTEQ"].items())
        dep_s = sorted(val["SNWD"].items())
        swe_dt, swe = last_valid(swe_s)
        dep_dt, dep = last_valid(dep_s)
        asof = max(filter(None, [swe_dt, dep_dt]), default=None)
        tx = [v for k, v in sorted(val["TMAX"].items())[-3:] if v is not None]
        tn = [v for k, v in sorted(val["TMIN"].items())[-3:] if v is not None]
        records.append({
            "t": t, "name": s["name"], "st": s["stateCode"], "elev": int(s.get("elevation") or 0),
            "lat": round(s["latitude"], 5), "lon": round(s["longitude"], 5),
            "depth": dep, "dDepth3": change_over(dep_s, 3), "dDepth7": change_over(dep_s, 7),
            "swe": swe, "dSwe7": change_over(swe_s, 7),
            "pctMed": pct_of_median(swe, med.get(swe_dt)) if swe_dt else None,
            "tmax3": max(tx) if tx else None, "tmin3": min(tn) if tn else None,
            "asof": asof, "stale": is_stale(asof, today),
        })
        # Median is a calendar-day statistic, so last season's dates give the full-year curve.
        series = {
            "t": t, "name": s["name"], "wy": wy,
            "cur": {"swe": align_to_wy(val["WTEQ"], wy, cur_days), "depth": align_to_wy(val["SNWD"], wy, cur_days)},
            "prev": {"swe": align_to_wy(val["WTEQ"], wy - 1, prev_days),
                     "depth": align_to_wy(val["SNWD"], wy - 1, prev_days)},
            "median": {"swe": align_to_wy(med, wy - 1, prev_days)},
        }
        (out_dir / "series" / f"{t.split(':')[0]}_{t.split(':')[1]}.json").write_text(
            json.dumps(series, separators=(",", ":")))

    (out_dir / "stations.json").write_text(json.dumps(records, separators=(",", ":")))
    hubs = json.loads((ROOT / "hubs.json").read_text())
    drive = json.loads((ROOT / "data" / "drive_times.json").read_text())
    for h in hubs:
        h["drive"] = drive.get(h["id"], {})
    (out_dir / "hubs.json").write_text(json.dumps(hubs, separators=(",", ":")))
    (out_dir / "meta.json").write_text(json.dumps({
        "built": datetime.now(timezone.utc).isoformat(timespec="minutes"), "wy": wy,
        "stations": len(records), "reporting": sum(not r["stale"] for r in records)}))
    print(f"wrote {len(records)} stations to {out_dir}", file=sys.stderr)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=str(ROOT.parent / "web" / "public" / "data"))
    p.add_argument("--states", default=",".join(WESTERN_STATES))
    a = p.parse_args()
    build(pathlib.Path(a.out), a.states.split(","))


if __name__ == "__main__":
    main()
