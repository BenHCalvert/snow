# Snow Within Reach: product brief

## Problem

Backcountry skiers and snow-curious drivers decide on a weekend destination by piecing together several sources:
the NRCS SNOTEL map, individual station pages, Google Maps for drive times, and memory of "what's normal."
No single tool answers the question they actually have:

> **"Where's the best snow I can drive to, and how does it compare to normal?"**

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

- Map + ranked list of SNOTEL sites within **1–8 hours' drive** of 15 mountain-west hub cities
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
| Avalanche danger | Must come from avalanche centers with care and attribution. Showing it wrong is a safety risk. |
| Weather forecast | High value, but a separate integration. It's the top V2 candidate. |
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

1. **V1.1:** analytics, NWS 3-day forecast snow per site, "new snow (24h)" from hourly data
2. **V2:** "this date in history" (compare any date across 40+ seasons), freeze/thaw/crust indicator
3. **V3:** user location via precomputed isochrones, storm alerts ("8"+ within 3 h of you")

See [DECISIONS.md](DECISIONS.md) for the reasoning behind key choices, and [USER_RESEARCH.md](USER_RESEARCH.md)
for the interview plan.
