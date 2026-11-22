import pathlib
import sys
import unittest
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))
from metrics import (align_to_wy, change_over, is_stale, last_valid,  # noqa: E402
                     pct_of_median, water_year, wy_start)


class WaterYear(unittest.TestCase):
    def test_october_starts_next_water_year(self):
        self.assertEqual(water_year(date(2026, 10, 1)), 2027)
        self.assertEqual(water_year(date(2026, 9, 30)), 2026)

    def test_start(self):
        self.assertEqual(wy_start(2027), date(2026, 10, 1))


class Series(unittest.TestCase):
    S = [("2026-11-18", 8), ("2026-11-19", 7), ("2026-11-20", None), ("2026-11-21", 10), ("2026-11-22", None)]

    def test_last_valid_skips_nulls(self):
        self.assertEqual(last_valid(self.S), ("2026-11-21", 10))

    def test_change_uses_calendar_days(self):
        self.assertEqual(change_over(self.S, 3), 2)   # 11-21 vs 11-18
        self.assertEqual(change_over(self.S, 2), 3)   # 11-21 vs 11-19

    def test_change_missing_baseline_is_none(self):
        self.assertIsNone(change_over(self.S, 1))     # 11-20 is null, don't guess
        self.assertIsNone(change_over([], 3))

    def test_pct_of_median_guards(self):
        self.assertEqual(pct_of_median(1.4, 2.6), 54)
        self.assertIsNone(pct_of_median(1.0, 0))      # early season median of 0
        self.assertIsNone(pct_of_median(None, 2.0))

    def test_stale(self):
        self.assertFalse(is_stale("2026-11-21", date(2026, 11, 22)))
        self.assertTrue(is_stale("2026-11-16", date(2026, 11, 22)))
        self.assertTrue(is_stale(None, date(2026, 11, 22)))

    def test_align(self):
        self.assertEqual(align_to_wy({"2026-10-01": 1, "2026-10-03": 3}, 2027, 4), [1, None, 3, None])


if __name__ == "__main__":
    unittest.main()
