# Decision log

Short records of product and technical decisions: what we chose, what we gave up, and when to revisit.

---

### 1. Static site + scheduled data job, no backend
**Context:** The data changes hourly at most, and every user sees the same data.
**Decision:** A GitHub Action fetches NRCS data every 3 hours and writes JSON files. The site is static (GitHub Pages).
**Trade-offs:** Data can be up to 3 hours old, and per-user queries aren't possible. In exchange, hosting costs $0,
nothing needs to stay up, pages load fast, and NRCS sees one request batch every 3 hours instead of one per visitor.
**Revisit when:** we need per-user features (alerts, accounts).

### 2. Drive times from 15 hub cities instead of the user's location
**Context:** Real drive times need a routing engine. The free OSRM demo server is rate-limited and not meant for
production traffic, and paid routing APIs cost money per request.
**Decision:** Precompute drive times from 15 mountain-west hubs to every station within 8 hours, and commit the result.
**Trade-offs:** Users outside a hub are approximated (Eagle uses Boise). This covers most of the population
that skis in the region, at zero ongoing cost.
**Revisit when:** analytics show many users far from hubs, or users request it. Option: precomputed isochrone
grid, or a small paid routing tier.

### 3. Three metrics, not ten
**Context:** NRCS publishes dozens of elements (SWE, depth, density, precipitation, soil moisture…).
**Decision:** Offer only snow depth, 3-day depth change, and % of median SWE. They map directly to the three jobs to be done.
**Trade-offs:** Power users lose detail. They get a link to the NRCS station page.
**Revisit when:** users repeatedly ask for a specific metric.

### 4. "New snow" = 3-day depth change, labeled honestly
**Context:** Depth sensors jitter ±1–2" and snow settles. True new snow needs hourly data and smoothing.
**Decision:** V1 shows the 3-day depth change and says plainly in the UI that small changes are noise.
**Trade-offs:** It can show a negative value after settling, which is accurate but less satisfying.
**Revisit when:** building V1.1's 24-hour new snow from hourly data.

### 5. Show stale stations faded, don't hide them
**Context:** A few stations stop reporting at any given time.
**Decision:** Fade stations that haven't reported in 2+ days, and label them "stale" in the list.
**Trade-offs:** Slight visual noise. But hiding them would make users think a site doesn't exist, and silently
showing old data would mislead them.

### 6. Season chart: this season vs. last season vs. median
**Context:** "Is this a good year?" needs a reference. Showing every past year is noisy and heavy to download.
**Decision:** Show three lines. Last season is the comparison people remember. The median is the objective baseline.
**Trade-offs:** No arbitrary year comparison yet (planned for V2, "this date in history").

### 7. Free, keyless map tiles (OpenFreeMap + MapLibre)
**Decision:** MapLibre GL with OpenFreeMap vector tiles. No API key, no billing, no usage caps.
**Trade-offs:** Less polished terrain styling than Mapbox. A terrain/hillshade layer is a likely V2 polish item.
