# Snow Within Reach: product brief

## Problem

Backcountry skiers and snow-curious drivers decide on a weekend destination by piecing together several sources:
the NRCS SNOTEL map, individual station pages, Google Maps for drive times, and memory of "what's normal."
No single tool answers the question they actually have:

> **"Where's the best snow I can drive to, and how does it compare to normal?"**

### Long-term vision

> **"Where's the best snow, that's safe to ski, within X hours of me, and how does it compare to normal?"**

V1 answers the snow and distance parts. Later phases add conditions (freeze/thaw, forecast) and then safety
(avalanche danger). See the [Roadmap](#roadmap).

The NRCS tools are built for hydrologists (water supply, basins, percent of median). They're accurate but
don't account for *where the user is* or *how far they're willing to drive*.

## Target users

| Persona | Situation | What they need |
|---|---|---|
| **Weekend backcountry skier** (primary) | Lives in a mountain-west city and picks a zone Thursday night | Ranked list of reachable sites by depth or new snow |
| **Early/late-season planner** | Wondering whether it's worth driving yet, or still worth driving | Comparison to normal and to last season |
| **Snow-curious local** | Wants to know "is this a good year?" | % of normal at a glance, season chart |

## Jobs to be done

1. *When I'm planning a ski day*, I want to see which areas within my drive budget have the most snow,
   so I don't waste a 6-hour round trip.
2. *When a storm just passed*, I want to see where it actually delivered, so I go where the new snow is.
3. *When I hear "it's a bad year,"* I want to see how this season compares to normal and to last year,
   so I can set expectations.

## V1 scope (shipped)

- Map + ranked list of SNOTEL sites within **1–8 hours' drive** of 17 mountain-west hub cities
- Color/rank by **snow depth**, **3-day depth change**, or **% of median SWE**
- Site detail: current stats + season SWE chart (this season vs. last season vs. 1991–2020 median)
- Shareable URLs (`?from=boise&hours=3&metric=pctMed`)
- Stale-data flagging (sites that haven't reported in 2+ days fade out)
- Mobile layout (map on top, list below)
- Data refreshes every 3 hours, with no backend server

## Explicitly out of scope for V1 (and why)

| Cut | Why |
|---|---|
| Drive time from the user's exact location | Needs a live routing call per visitor. The free router can't take that load, and hubs cover most users. See DECISIONS #2. |
| Avalanche danger | Must come from avalanche centers with care and attribution. Showing it wrong is a safety risk. Planned as Phase 3 (see Roadmap and DECISIONS #8). |
| Weather forecast | High value, but a separate integration. Planned for Phase 1. |
| Freeze/thaw / crust flag | Needs hourly temperature data, while V1 is daily only. Planned for Phase 1. |
| Winter road closures | No reliable cross-state source. Flagged in the UI copy instead. |
| Accounts, favorites, alerts | No evidence of need yet. Shareable URLs cover "save this view." |

## Success metrics

| Type | Metric | V1 target |
|---|---|---|
| North star | Weekly users who open a site detail (= used it to make a decision) | Baseline, then grow |
| Activation | % of sessions that change hub or drive time (= personalized) | > 50% |
| Engagement | Shared URLs opened (`?site=` present on landing) | Tracked |
| Quality | % of stations reporting within 48 h | > 95% (shown in `meta.json`) |
| Reliability | Successful scheduled data refreshes | > 98% |

Analytics are not wired in yet. Adding privacy-friendly page analytics (e.g., Plausible) is a V1.1 task.

## Risks and assumptions

- **Sensor ≠ slope.** A SNOTEL site is one point, often in a sheltered clearing. The copy frames the data as
  an *indicator*, not a guarantee of conditions.
- **Drive times are optimistic in winter.** The router uses summer roads. Mitigation: a disclaimer, plus
  showing distance from the nearest road in the data. Longer term: flag sites behind seasonal closures.
- **Free dependencies** (NRCS API, OSRM demo server, OpenFreeMap tiles) could change or rate-limit.
  Drive times are precomputed and committed, so routing outages don't affect the live site.

## Roadmap

Phases build toward the long-term vision: **snow → conditions → safety**.

### Phase 1: Conditions ("what will it ski like?")
| Feature | Notes | Depends on |
|---|---|---|
| **72-hour new snow from hourly data** (`metric=new72`) | Replaces the V1 3-day *daily* depth change. Sum hourly depth gains, smoothed to ignore ±1" sensor jitter, and cross-check with SWE gain. Also 24 h and 48 h. | Pipeline: hourly SNWD/WTEQ fetch |
| **Shareable links for the new metric** | URL state already ships in V1 (`?from=&hours=&metric=&site=`). Add `new72` (and `new24`/`new48`) as valid `metric` values, and keep old links working. | 72 h new snow |
| **Freeze/thaw / crust flag** | From hourly air temperature: flag sites where it went above 32°F then back below within the last 72 h (likely melt-freeze crust), with hours above freezing as the strength. Show as a badge on the list and the detail view. Copy should say "likely crust at the sensor," not a slope guarantee. | Pipeline: hourly TOBS fetch |
| **NWS forecast per site** | Use the National Weather Service API (`api.weather.gov`, free, no key) gridpoint forecast at each station's lat/lon: next 3 days of snow amount, temperature high/low, and wind. Show "forecast new snow (3 days)" as a ranking option. Precompute in the scheduled job so the site stays static. | Pipeline: NWS integration, caching gridpoint lookups |
| Analytics | Privacy-friendly page analytics to measure the success metrics above. | — |

### Phase 2: History and reach
- "This date in history": compare any date across 40+ seasons
- User location instead of hub cities (precomputed isochrone grid)
- Storm alerts ("8"+ new snow within 3 h of you")

### Phase 3: Safety ("is it safe to ski?")
Completes the vision: **the best snow that's safe to ski, within X hours of me, compared to normal.**
| Feature | Notes |
|---|---|
| **Avalanche danger overlay** | Show the current danger rating from regional avalanche centers (e.g., via the National Avalanche Center / avalanche.org forecast zones) as a map layer under the stations. Each station inherits the danger rating of its forecast zone. |
| **Rank by snow *and* safety** | Option to hide or de-rank sites in zones at Considerable or higher, and to show "best snow at Low/Moderate danger." |
| **Avalanche weather context** | Combine Phase 1 signals that matter for stability: recent loading (72 h new snow and SWE), wind from the forecast, and warming or crust. Present them as *context next to the official forecast*, never as our own danger rating. |
| **Required guardrails** | Always link to the full avalanche center forecast. Show issue date and expiration, and gray out expired forecasts. Show "no forecast available" rather than nothing. Credit the centers clearly. Add a prominent disclaimer: this tool does not replace reading the forecast, training, or field observations. |

Open questions for Phase 3 (to resolve in user research and with avalanche centers):
- Do avalanche centers permit this kind of reuse, and what attribution do they require?
- Does showing danger next to "best snow" encourage risky choices? Test the framing with users.
- How do we handle stations outside any forecast zone, and forecasts issued only some days of the week?

See [DECISIONS.md](DECISIONS.md) for the reasoning behind key choices, and [USER_RESEARCH.md](USER_RESEARCH.md)
for the interview plan.
