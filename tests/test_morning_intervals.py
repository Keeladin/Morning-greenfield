from __future__ import annotations

import unittest
from datetime import datetime, timezone

from morning.intervals import DowntimeInterval, IntervalError, clip_interval, merge_intervals, total_downtime_seconds


def _t(hour: int, minute: int = 0, day: int = 1) -> datetime:
    return datetime(2026, 3, day, hour, minute, tzinfo=timezone.utc)


class IntervalMergeTests(unittest.TestCase):
    def test_spec_example_overlapping_reports_do_not_double_count(self) -> None:
        a = DowntimeInterval(_t(22, day=1), _t(0, 30, day=2), source="a")
        b = DowntimeInterval(_t(23, 45, day=1), _t(1, 0, day=2), source="b")
        merged = merge_intervals((a, b))
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].start, _t(22, day=1))
        self.assertEqual(merged[0].end, _t(1, 0, day=2))
        self.assertEqual(total_downtime_seconds((a, b)), 3 * 3600)

    def test_non_overlapping_intervals_stay_separate_and_sum(self) -> None:
        a = DowntimeInterval(_t(22, 0), _t(22, 40), source="hydraulic")
        b = DowntimeInterval(_t(0, 15, day=2), _t(1, 30, day=2), source="battery")
        c = DowntimeInterval(_t(3, 0, day=2), _t(6, 31, day=2), source="brake")
        merged = merge_intervals((a, b, c))
        self.assertEqual(len(merged), 3)
        total = total_downtime_seconds((a, b, c))
        self.assertEqual(total, 40 * 60 + 75 * 60 + 211 * 60)

    def test_touching_intervals_merge(self) -> None:
        a = DowntimeInterval(_t(10, 0), _t(11, 0), source="a")
        b = DowntimeInterval(_t(11, 0), _t(12, 0), source="b")
        merged = merge_intervals((a, b))
        self.assertEqual(len(merged), 1)
        self.assertEqual(total_downtime_seconds((a, b)), 2 * 3600)

    def test_merged_interval_preserves_every_source(self) -> None:
        a = DowntimeInterval(_t(1, 0), _t(3, 0), source="report-a")
        b = DowntimeInterval(_t(2, 0), _t(4, 0), source="report-b")
        merged = merge_intervals((a, b))
        self.assertEqual(set(merged[0].sources), {"report-a", "report-b"})

    def test_empty_input_has_zero_downtime(self) -> None:
        self.assertEqual(merge_intervals(()), ())
        self.assertEqual(total_downtime_seconds(()), 0)

    def test_interval_end_before_start_is_rejected(self) -> None:
        with self.assertRaises(IntervalError):
            DowntimeInterval(_t(10), _t(9), source="bad")

    def test_clip_interval_to_reporting_window(self) -> None:
        interval = DowntimeInterval(_t(23, 0, day=1), _t(2, 0, day=2), source="a")
        clipped = clip_interval(interval, window_start=_t(0, 0, day=2), window_end=_t(6, 0, day=2))
        assert clipped is not None
        self.assertEqual(clipped.start, _t(0, 0, day=2))
        self.assertEqual(clipped.end, _t(2, 0, day=2))

    def test_clip_interval_entirely_outside_window_is_none(self) -> None:
        interval = DowntimeInterval(_t(1, 0, day=1), _t(2, 0, day=1), source="a")
        clipped = clip_interval(interval, window_start=_t(6, 0, day=2), window_end=_t(18, 0, day=2))
        self.assertIsNone(clipped)


if __name__ == "__main__":
    unittest.main()
