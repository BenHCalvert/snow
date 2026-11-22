# snow

Tools for pulling NRCS SNOTEL snowpack and weather data. The data is free and public, and no API key is needed.

## What's here

| Path | What it is |
|---|---|
| `.claude/skills/snotel-data/` | A Claude skill. Claude Code loads it automatically in this repo. |
| `.claude/skills/snotel-data/scripts/snotel.py` | A command-line tool (standard-library Python, nothing to install) |
| `.claude/skills/snotel-data/references/api.md` | NRCS API and CSV URL reference: element codes and gotchas |
| `.claude/skills/snotel-data/references/metloom.md` | How to use the `metloom` Python package |
| `dist/snotel-data.skill` | Packaged skill for uploading to claude.ai (Settings → Capabilities → Skills) |

## Quick start

```bash
S=.claude/skills/snotel-data/scripts/snotel.py

# Find a station's ID ("triplet") by name
python3 $S find "mores"

# Historical lookup, with the 1991-2020 median
python3 $S data 637:ID:SNTL --start 2020-11-25 --end 2020-11-29 --median

# Hourly depth, SWE, and temperature for "right now"
python3 $S data 637:ID:SNTL --start 2026-11-21 --end 2026-11-22 \
  --elements SNWD,WTEQ,TOBS --duration HOURLY

# Every SNOTEL site within a 4-hour drive of Boise, with current conditions
python3 $S near --lat 43.615 --lon -116.202 --hours 4 --conditions --out near_boise.csv
```

Add `--out file.csv` to any command to save the results.

## Data sources

- **NRCS AWDB REST API** (JSON): `https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/`.
  Docs are at `.../awdbRestApi/swagger-ui/index.html`.
- **Report Generator CSV URLs** work in Google Sheets with `=IMPORTDATA(url)`. For example, the last 4 days at Mores Creek:
  ```
  https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/customSingleStationReport/daily/637:ID:SNTL|id=""|name/-4,0/WTEQ::value,SNWD::value,TMAX::value,TMIN::value
  ```
- **metloom** (`pip install metloom`) gives pandas DataFrames and covers other networks (CDEC, USGS, MesoWest).
- **Drive times** come from the public OSRM demo router (`router.project-osrm.org`). It uses summer
  road routing, so it knows nothing about winter closures.

## Handy station triplets

| Site | Triplet |
|---|---|
| Bogus Basin | `978:ID:SNTL` |
| Mores Creek Summit | `637:ID:SNTL` |
| Banner Summit | `312:ID:SNTL` |
| Galena | `489:ID:SNTL` |
| Galena Summit | `490:ID:SNTL` |

## Gotchas

- The website shows **start-of-day** values, while the REST API's daily value for a date is the *following*
  midnight. The same reading can show up one date apart in the two sources.
- Today's daily value usually isn't published yet. Use `--duration HOURLY` for current conditions.
- Snow depth sensors jitter by ±1-2". Check SWE before calling something "new snow."
