# NRCS SNOTEL data access reference

Everything here is free and public, with no API key. All of it was verified working in Nov 2026.

## Contents
1. AWDB REST API (JSON)
2. Report Generator CSV URLs
3. Element codes
4. Gotchas

---

## 1. AWDB REST API

Base: `https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1`
Interactive docs: `https://wcc.sc.egov.usda.gov/awdbRestApi/swagger-ui/index.html`

### Stations are "triplets"
`id:state:network`, e.g. `637:ID:SNTL` (Mores Creek Summit). Networks: `SNTL` (SNOTEL),
`SNTLT` (SNOTEL-lite), `SCAN`, `MSNT` (manual snow course), etc. Wildcards work: `*:ID:SNTL`.

### `/stations`: metadata and search
```
/stations?stationTriplets=*:ID:SNTL&activeOnly=true&returnStationElements=false
```
Returns name, lat/lon, elevation (ft), county, HUC, beginDate (period of record).
There is no name-search parameter, so fetch a state (or `*:*:SNTL`, ~900 sites) and filter locally.

### `/data`: measurements
```
/data?stationTriplets=637:ID:SNTL,312:ID:SNTL&elements=WTEQ,SNWD&duration=DAILY
      &beginDate=2020-11-27&endDate=2020-11-27&centralTendencyType=MEDIAN
```
- `duration`: `HOURLY`, `DAILY`, `SEMIMONTHLY`, `MONTHLY`, `ANNUAL`, `WATER_YEAR`
- Dates: `YYYY-MM-DD` (daily), `YYYY-MM-DD HH:MM` works for hourly
- `centralTendencyType=MEDIAN` (or `AVERAGE`) adds a `median` field per value (1991-2020 normals)
  plus `timingCentralTendencies` (median peak SWE date/value, median onset, median melt-out)
- Many stations per call is fine (comma-separated; ~50 at a time is safe)

Response shape:
```json
[{"stationTriplet":"637:ID:SNTL","data":[{"stationElement":{"elementCode":"WTEQ",...},
   "values":[{"date":"2020-11-27","value":6.9,"median":3.6}]}]}]
```

### `/reference-data`
Lists all element codes, units, durations, and networks.

---

## 2. Report Generator CSV URLs

The web site's report builder. Every report is also a URL that returns CSV, which is handy for Google
Sheets `=IMPORTDATA(url)`, Excel, or `pandas.read_csv(url, comment="#")`.

```
https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/customSingleStationReport/daily/637:ID:SNTL|id=""|name/-4,0/WTEQ::value,SNWD::value,TMAX::value,TMIN::value
```
- `-4,0` = relative days (4 days ago through today). Absolute: `2020-11-20,2020-11-30`.
- Swap `daily` for `hourly`. Swap `customSingleStationReport` for `customMultipleStationReport`
  with `637:ID:SNTL|312:ID:SNTL|...`
- Add stats: `WTEQ::value,WTEQ::median_1991,WTEQ::pctOfMedian_1991`
- `view_csv` → `view` to get the HTML version for a human.
- Lines starting with `#` are header comments; skip them.
- URL-encode `|` as `%7C` and `"` as `%22` when using curl.

---

## 3. Element codes

| Code | Meaning | Units |
|---|---|---|
| WTEQ | Snow water equivalent (SWE) | in |
| SNWD | Snow depth | in |
| PREC | Precipitation accumulation (water year to date) | in |
| PRCP | Precipitation increment | in |
| TOBS | Observed air temperature (instantaneous; hourly is the useful one) | °F |
| TMAX / TMIN / TAVG | Daily max/min/avg air temperature | °F |
| SNDN | Snow density | % |
| WSPDV / WDIRV | Wind speed / direction (only some sites) | mph / deg |
| RHUM | Relative humidity (some sites) | % |
| SMS / STO | Soil moisture / soil temperature (with `ordinal` = depth) | % / °F |

---

## 4. Gotchas

- **Start-of-day vs end-of-day.** The Report Generator labels daily snow values "Start of Day" (the
  midnight reading at the *start* of that date). The REST API's DAILY values for a date correspond to the
  following midnight. The same reading can therefore appear one date apart in the two sources. When the user
  compares against the website, say which convention you're using.
- **Today's daily value often isn't there yet** in the REST API. Use HOURLY for "right now" and for
  24/48/72-hour new snow.
- **Snow depth is noisy** (±1-2" sensor jitter, settling). For "new snow," prefer the hourly depth
  increase, and cross-check with the SWE increase. Example: ~1" depth per ~0.1" SWE is typical of fresh snow.
- **SWE that's flat while depth drops** = settlement, not melt. **SWE dropping** = melt (or sublimation).
- **Freeze/thaw:** look at hourly TOBS. If it's above 32°F by day and below by night, expect a crust.
- **Period of record:** SWE/precip daily go back to ~1978-1980 at most sites. Snow depth and temperature
  sensors were added later (often the late 1990s). Hourly data is reliable from the mid-2000s.
- **Water year** runs Oct 1 – Sep 30 (WY2021 = Oct 2020 – Sep 2021).
- **Missing values** come back as absent `value` keys or nulls; don't treat them as zero.
- **Timezone:** station local standard time (`dataTimeZone`, e.g. -8 for PST), no DST.
