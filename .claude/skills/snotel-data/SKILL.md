---
name: snotel-data
description: Programmatic access to NRCS SNOTEL snowpack and weather station data. Covers the AWDB REST API, Report Generator CSV URLs, and the metloom Python package. Use it for historical lookups ("what was the snow depth at Mores Creek on Thanksgiving 2020"), comparing years or percent of median, finding every SNOTEL site within a drive time or distance of a place, station searches, pulling SWE/depth/temperature series for any site in the western US, building Google Sheets or scripts that pull SNOTEL data, and any question about how to get SNOTEL data. Use it whenever the user mentions SNOTEL, SWE, snowpack data, NRCS snow data, or metloom, even if they don't ask for code. For Ben's routine daily ski-conditions dashboard at his usual central Idaho sites, prefer the snotel-ski-conditions skill.
---

# SNOTEL data

SNOTEL is the NRCS network of ~900 automated snow and weather stations across the western US. All of its
data is public and needs no API key. This skill bundles a no-install script for common jobs, plus reference
docs for everything else.

## Quick start: `scripts/snotel.py` (Python standard library only)

```bash
S=<skill-dir>/scripts/snotel.py
python3 -I $S find "galena" --state ID                    # find triplets by name
python3 -I $S data 637:ID:SNTL --start 2020-11-27 --end 2020-11-27 --median
python3 -I $S data 637:ID:SNTL 312:ID:SNTL --start 2026-11-20 --end 2026-11-22 \
        --elements SNWD,WTEQ,TOBS --duration HOURLY
python3 -I $S near --lat 43.615 --lon -116.202 --hours 4 --conditions --out sites.csv
```
- `find` searches station names (case-insensitive substring) and returns triplet, elevation, lat/lon, and
  period of record.
- `data` returns one row per station per date. `--median` adds 1991-2020 median columns (daily only), so you
  can compute percent of median.
- `near` combines a straight-line prefilter with real road drive times from the public OSRM router. With
  `--conditions` it adds current depth, 3-day depth change, SWE, 7-day SWE change, SWE % of median,
  3-day high/low, and an as-of date. Searching ~45 sites takes about 10-15 seconds.
- Add `--out file.csv` to any command to save a CSV as well as printing it.

Stations are identified by a **triplet**, `id:state:network`, for example `637:ID:SNTL`. When the user names
a site, run `find` to get its triplet rather than guessing the ID.

## Workflows

### Historical lookup ("what was X on date Y")
1. Resolve the date. Holidays move, so compute them (Thanksgiving = 4th Thursday of November; the
   "Friday after" is the next day). State the actual date in your answer so the user can check it.
2. Run `data` for a window of a few days around the date, not just the one day. The surrounding days show
   whether a storm or melt was underway, and a single missing reading won't leave you empty-handed.
3. Add `--median` when comparing to normal. Comparing to the current season is often what the user really
   wants, so offer it.
4. Present a small table with the target date in bold, plus one or two sentences on the trend.

### Sites near a place / within a drive time
1. Ask for the starting point if it's unclear. Use a **town-center coordinate**, not a home address. The
   coordinates go to a third-party routing server, so don't send anything more precise than the town.
2. Run `near`. The default prefilter radius is hours × 65 miles. Raise `--radius-mi` for fast-highway regions.
3. Show a full table including the **state** column (users miss out-of-state sites otherwise), sorted by
   drive time. Highlight the deepest or snowiest sites, and flag stale `asof` dates.
4. Always mention two caveats: OSRM uses summer road routing (no winter closures or unplowed roads), and
   `road_gap_m` is the distance from the sensor to the nearest road. Treat values over ~1,000 m as "more
   access than the drive time suggests."

### "Right now" / new snow / freeze-thaw
Use HOURLY data (`SNWD`, `WTEQ`, `TOBS`). Today's daily value is usually not published yet. Compute
24/48/72-hour depth gain from the hourly series, and check temperatures crossing 32°F for crust formation.

### Recurring pulls (Google Sheets, cron, dashboards)
Give the user a Report Generator CSV URL (see `references/api.md` §2). It works directly in
`=IMPORTDATA()` and needs no code.

## Interpretation tips
- Flat SWE with dropping depth means settlement. Dropping SWE means melt.
- Depth sensors jitter ±1-2", so don't call a 1" change "new snow" unless SWE rose too.
- The website (Report Generator) shows "start of day" values. The REST API's daily value for a date is the
  following midnight, so the two can differ by one date. Mention this if the user compares with the website.
- Snow depth and temperature records often start in the late 1990s, while SWE goes back to ~1978. A blank
  depth in older years usually means no sensor yet, not zero snow.

## When to reach for something else
- **Deeper API details** (all parameters, CSV URL syntax, element codes, more gotchas): read
  `references/api.md`.
- **pandas analysis, other networks (CDEC, USGS, MesoWest), or polygon/shapefile searches**: read
  `references/metloom.md`. metloom is a heavy install, so use a venv.
- **Charts**: pull the data with the script, then follow the dataviz skill if available.

## Network notes
- If a request fails in a sandbox, check the proxy. The required hosts are `wcc.sc.egov.usda.gov` (data) and
  `router.project-osrm.org` (drive times only).
- The OSRM demo server is free but rate-limited. The script batches 90 destinations per call with a pause.
  Don't loop it hundreds of times.
