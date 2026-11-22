"""Thin client for the NRCS AWDB REST API and the OSRM routing table (standard library only)."""
import json
import time
import urllib.parse
import urllib.request

API = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1"
OSRM = "https://router.project-osrm.org/table/v1/driving"
UA = {"User-Agent": "snow-within-reach/0.1"}

WESTERN_STATES = ["WA", "OR", "ID", "MT", "WY", "CA", "NV", "UT", "CO", "AZ", "NM", "SD"]


def get_json(url, timeout=120, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def stations(state, network="SNTL"):
    q = urllib.parse.urlencode({
        "stationTriplets": f"*:{state}:{network}", "activeOnly": "true",
        "returnForecastPointMetadata": "false", "returnReservoirMetadata": "false",
        "returnStationElements": "false"})
    return get_json(f"{API}/stations?{q}")


def daily(triplets, elements, start, end, median=False):
    """Return {triplet: {element: {date: (value, median)}}} for one batch of stations."""
    params = {"stationTriplets": ",".join(triplets), "elements": ",".join(elements),
              "duration": "DAILY", "beginDate": start, "endDate": end}
    if median:
        params["centralTendencyType"] = "MEDIAN"
    out = {}
    for st in get_json(f"{API}/data?{urllib.parse.urlencode(params)}"):
        d = out.setdefault(st["stationTriplet"], {})
        for e in st.get("data", []):
            d[e["stationElement"]["elementCode"]] = {
                v["date"][:10]: (v.get("value"), v.get("median")) for v in e.get("values", [])}
    return out


def drive_hours(origin, dests):
    """origin: (lat, lon); dests: list of (lat, lon). Returns hours (or None) per destination."""
    out = []
    for i in range(0, len(dests), 90):
        chunk = dests[i:i + 90]
        coords = ";".join([f"{origin[1]:.5f},{origin[0]:.5f}"] + [f"{lon:.5f},{lat:.5f}" for lat, lon in chunk])
        d = get_json(f"{OSRM}/{coords}?sources=0&annotations=duration")
        out += [None if s is None else s / 3600 for s in d["durations"][0][1:]]
        time.sleep(1.5)  # the public demo server is shared; be polite
    return out
