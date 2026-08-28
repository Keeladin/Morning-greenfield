from __future__ import annotations

import unittest
from datetime import datetime, timezone

from morning.intervals import IntervalError, TimeInterval, clip_interval, merge_intervals, total_interval_seconds


def _t(hour: int, minute: int = 0, day: int = 1) -> datetime:
    return datetime(2026, 3, day, hour, minute, tzinfo=timezone.utc)


class IntervalMergeTests(unittest.TestCase):
    def test_overlapping_intervals_merge_without_double_counting(self) -> None:
        first = TimeInterval(_t(22, day=1), _t(0, 30, day=2), source="a")
        second = TimeInterval(_t(23, 45, day=1), _t(1, 0, day=2), source="b")
        merged = merge_intervals((first, second))
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].start, _t(22, day=1))
        self.assertEqual(merged[0].end, _t(1, 0, day=2))
        self.assertEqual(total_interval_seconds((first, second)), 3 * 3600)

    def test_non_overlapping_intervals_stay_separate_and_sum(self) -> None:
        first = TimeInterval(_t(22, 0), _t(22, 40), source="hydraulic")
        second = TimeInterval(_t(0, 15, day=2), _t(1, 30, day=2), source="battery")
        third = TimeInterval(_t(3, 0, day=2), _t(6, 31, day=2), source="brake")
        self.assertEqual(len(merge_intervals((first, second, third))), 3)
        self.assertEqual(total_interval_seconds((first, second, third)), 40 * 60 + 75 * 60 + 211 * 60)

    def test_touching_intervals_merge_and_preserve_sources(self) -> None:
        first = TimeInterval(_t(10, 0), _t(11, 0), source="a")
        second = TimeInterval(_t(11, 0), _t(12, 0), source="b")
        merged = merge_intervals((first, second))
        self.assertEqual(len(merged), 1)
        self.assertEqual(set(merged[0].sources), {"a", "b"})

    def test_invalid_interval_is_rejected(self) -> None:
        with self.assertRaises(IntervalError):
            TimeInterval(_t(10), _t(9), source="bad")

    def test_clip_interval_to_reporting_window(self) -> None:
        interval = TimeInterval(_t(23, day=1), _t(2, day=2), source="a")
        clipped = clip_interval(interval, window_start=_t(0, day=2), window_end=_t(6, day=2))
        assert clipped is not None
        self.assertEqual(clipped.start, _t(0, day=2))
        self.assertEqual(clipped.end, _t(2, day=2))
