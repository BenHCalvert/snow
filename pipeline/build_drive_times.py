"""Precompute drive times from each hub city to every western SNOTEL station.

Roads don't change often, so this runs by hand (not on the schedule) and the result is committed:
    python3 pipeline/build_drive_times.py                       # all hubs
    python3 pipeline/build_drive_times.py --only durango,steamboat  # add/refresh some hubs, keep the rest
Output: pipeline/data/drive_times.json  ->  {hub_id: {triplet: hours}} (only stations <= MAX_HOURS)
"""
import argparse
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from snotel_api import WESTERN_STATES, drive_hours, stations  # noqa: E402

ROOT = pathlib.Path(__file__).parent
MAX_HOURS = 8
PREFILTER_MI = 520  # straight-line cutoff before asking the router


def miles(a, b):
    p = math.pi / 180
    h = (math.sin((b[0] - a[0]) * p / 2) ** 2 +
         math.cos(a[0] * p) * math.cos(b[0] * p) * math.sin((b[1] - a[1]) * p / 2) ** 2)
    return 7917.5 * math.asin(math.sqrt(h))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated hub ids to (re)compute; others are kept from the existing file")
    a = ap.parse_args()
    hubs = json.loads((ROOT / "hubs.json").read_text())
    path = ROOT / "data" / "drive_times.json"
    out = json.loads(path.read_text()) if a.only and path.exists() else {}
    if a.only:
        wanted = set(a.only.split(","))
        unknown = wanted - {h["id"] for h in hubs}
        if unknown:
            sys.exit(f"unknown hub ids: {sorted(unknown)}")
        hubs = [h for h in hubs if h["id"] in wanted]
    sts = [s for st in WESTERN_STATES for s in stations(st)]
    print(f"{len(sts)} stations", file=sys.stderr)
    for hub in hubs:
        origin = (hub["lat"], hub["lon"])
        near = [s for s in sts if miles(origin, (s["latitude"], s["longitude"])) <= PREFILTER_MI]
        hrs = drive_hours(origin, [(s["latitude"], s["longitude"]) for s in near])
        out[hub["id"]] = {s["stationTriplet"]: round(h, 2) for s, h in zip(near, hrs)
                          if h is not None and h <= MAX_HOURS}
        print(f"{hub['id']}: {len(out[hub['id']])} stations within {MAX_HOURS} h", file=sys.stderr)
    (ROOT / "data").mkdir(exist_ok=True)
    path.write_text(json.dumps(out, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    main()
