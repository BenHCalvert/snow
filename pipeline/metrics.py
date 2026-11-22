"""Pure functions that turn raw daily series into the numbers the app shows. Unit-tested."""
from datetime import date, timedelta


def water_year(d: date) -> int:
    """Water year runs Oct 1 - Sep 30 and is named for the year it ends in."""
    return d.year + 1 if d.month >= 10 else d.year


def wy_start(wy: int) -> date:
    return date(wy - 1, 10, 1)


def last_valid(series):
    """series: list of (date_str, value). Returns (date_str, value) of the latest non-null value."""
    for dt, v in reversed(series):
        if v is not None:
            return dt, v
    return None, None


def change_over(series, days):
    """Change between the latest valid value and the valid value `days` calendar days earlier.

    Uses calendar days (not reading count) so a gap in reporting doesn't stretch the window.
    """
    dt, v = last_valid(series)
    if dt is None:
        return None
    target = (date.fromisoformat(dt) - timedelta(days=days)).isoformat()
    past = dict(series).get(target)
    return None if past is None else round(v - past, 1)


def pct_of_median(value, median):
    if value is None or median is None or median <= 0:
        return None
    return round(100 * value / median)


def is_stale(asof: str, today: date, max_age_days=2) -> bool:
    return asof is None or (today - date.fromisoformat(asof)).days > max_age_days


def align_to_wy(values: dict, wy: int, days: int):
    """values: {date_str: x}. Returns a list indexed by day-of-water-year (0 = Oct 1)."""
    start = wy_start(wy)
    return [values.get((start + timedelta(days=i)).isoformat()) for i in range(days)]
