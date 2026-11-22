# metloom (Python)

metloom ("Location Oriented Observed Meteorology") is an open-source package from M3Works. It wraps
SNOTEL and other station networks and returns pandas/GeoPandas DataFrames with units and locations
attached. It's on PyPI as `metloom`.

## When to use it vs. `scripts/snotel.py`
- Use `snotel.py` (stdlib, no install) for lookups, tables, near-me searches, and quick history.
- Use metloom when the user wants analysis in pandas, multi-network comparisons (CDEC, USGS,
  MesoWest/Synoptic, etc.), or a spatial search inside a polygon or shapefile (a watershed or forest
  boundary).

## Install
It's heavy (geopandas, shapely, pyproj), so put it in a venv:
```bash
python3 -m venv venv && ./venv/bin/pip install metloom
```

## Basics
```python
from datetime import datetime
from metloom.pointdata import SnotelPointData

site = SnotelPointData("637:ID:SNTL", "Mores Creek Summit")
V = site.ALLOWED_VARIABLES        # SWE, SNOWDEPTH, TEMP, TEMPMAX, TEMPMIN, TEMPAVG,
                                  # PRECIPITATION, PRECIPITATIONACCUM, RH, WINDSPEED, ...
daily  = site.get_daily_data(datetime(2020, 11, 20), datetime(2020, 11, 30), [V.SWE, V.SNOWDEPTH])
hourly = site.get_hourly_data(datetime(2026, 11, 20), datetime(2026, 11, 22), [V.SNOWDEPTH, V.TEMP])
```
It returns a DataFrame indexed by (`datetime` UTC, `site`), with a `geometry` column (POINT Z, lon/lat/elev ft),
value columns such as `SWE`, `SNOWDEPTH`, `MAX AIR TEMP`, `MIN AIR TEMP`, matching `*_units` columns, and `datasource`.
Daily timestamps show as 08:00 UTC (= midnight PST).

## Spatial search
```python
import geopandas as gpd
from shapely.geometry import Point
g = gpd.GeoDataFrame(geometry=[Point(-116.202, 43.615)], crs="EPSG:4326").to_crs("EPSG:5070")
g["geometry"] = g.buffer(100 * 1609.34)          # 100-mile circle
pts = SnotelPointData.points_from_geometry(g.to_crs("EPSG:4326"), [SnotelPointData.ALLOWED_VARIABLES.SWE])
df = pts.to_dataframe()                          # id, name, geometry
```
A shapefile or GeoJSON works the same way: `gpd.read_file("watershed.geojson")`.

## Other networks (same interface)
`from metloom.pointdata import CDECPointData, USGSPointData, MesowestPointData` (Mesowest needs a free
Synoptic token). Check the metloom docs or `dir(metloom.pointdata)` for the current list.

## Tips
- Suppress noisy warnings with `warnings.filterwarnings("ignore")`.
- Run multiple sites in a small thread pool (8 workers is fine).
- Run Python with `-I` when the working directory holds downloaded files.
