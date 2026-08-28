from __future__ import annotations

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from morning.models import ShiftIdentity, ShiftPolicy
from morning.shift import ShiftError, anchor_time_to_shift, reporting_window, resolve_shift, shift_window

TZ = "Africa/Johannesburg"
ZONE = ZoneInfo(TZ)


def _policy(day: str = "06:00", night: str = "18:00") -> ShiftPolicy:
    return ShiftPolicy(timezone=TZ, day_shift_start=day, night_shift_start=night, updated_at="now")


class ShiftResolutionTests(unittest.TestCase):
    def test_mid_morning_is_day_shift_today(self) -> None:
        identity = resolve_shift(_policy(), at=datetime(2026, 3, 25, 10, 0, tzinfo=ZONE))
        self.assertEqual(identity.shift_kind, "day")
        self.assertEqual(identity.shift_date, "2026-03-25")

    def test_evening_is_night_shift_starting_today(self) -> None:
        identity = resolve_shift(_policy(), at=datetime(2026, 3, 25, 20, 0, tzinfo=ZONE))
        self.assertEqual(identity.shift_kind, "night")
        self.assertEqual(identity.shift_date, "2026-03-25")

    def test_just_after_midnight_stays_on_the_night_shift_that_started_yesterday(self) -> None:
        identity = resolve_shift(_policy(), at=datetime(2026, 3, 26, 0, 30, tzinfo=ZONE))
        self.assertEqual(identity.shift_kind, "night")
        self.assertEqual(identity.shift_date, "2026-03-25")

    def test_just_before_day_shift_start_is_still_the_prior_night_shift(self) -> None:
        identity = resolve_shift(_policy(), at=datetime(2026, 3, 26, 5, 59, tzinfo=ZONE))
        self.assertEqual(identity.shift_kind, "night")
        self.assertEqual(identity.shift_date, "2026-03-25")

    def test_exact_boundary_moment_belongs_to_the_shift_that_starts(self) -> None:
        day_start = resolve_shift(_policy(), at=datetime(2026, 3, 25, 6, 0, tzinfo=ZONE))
        self.assertEqual((day_start.shift_kind, day_start.shift_date), ("day", "2026-03-25"))
        night_start = resolve_shift(_policy(), at=datetime(2026, 3, 25, 18, 0, tzinfo=ZONE))
        self.assertEqual((night_start.shift_kind, night_start.shift_date), ("night", "2026-03-25"))

    def test_naive_datetime_is_treated_as_policy_local_time(self) -> None:
        identity = resolve_shift(_policy(), at=datetime(2026, 3, 25, 10, 0))
        self.assertEqual((identity.shift_kind, identity.shift_date), ("day", "2026-03-25"))

    def test_unknown_timezone_is_rejected(self) -> None:
        with self.assertRaises(ShiftError):
            resolve_shift(
                ShiftPolicy(
                    timezone="Not/AZone",
                    day_shift_start="06:00",
                    night_shift_start="18:00",
                    updated_at="now",
                ),
                at=datetime(2026, 3, 25, 10, 0),
            )

    def test_identical_boundaries_are_rejected(self) -> None:
        with self.assertRaises(ShiftError):
            resolve_shift(_policy("06:00", "06:00"), at=datetime(2026, 3, 25, 10, 0))

    def test_shift_window_round_trips_with_resolve_shift(self) -> None:
        policy = _policy()
        for moment in (
            datetime(2026, 3, 25, 6, 0, tzinfo=ZONE),
            datetime(2026, 3, 25, 17, 59, tzinfo=ZONE),
            datetime(2026, 3, 25, 18, 0, tzinfo=ZONE),
            datetime(2026, 3, 26, 5, 59, tzinfo=ZONE),
        ):
            identity = resolve_shift(policy, at=moment)
            start, end = shift_window(policy, identity)
            self.assertTrue(start <= moment < end, f"{moment} not within [{start},{end})")

    def test_reporting_window_spans_day_shift_start_to_next_day_shift_start(self) -> None:
        start, end = reporting_window(_policy(), "2026-03-25")
        self.assertEqual(start, datetime(2026, 3, 25, 6, 0, tzinfo=ZONE))
        self.assertEqual(end, datetime(2026, 3, 26, 6, 0, tzinfo=ZONE))

    def test_inverted_boundary_configuration_still_resolves_deterministically(self) -> None:
        policy = _policy(day="14:00", night="02:00")
        identity = resolve_shift(policy, at=datetime(2026, 3, 25, 20, 0, tzinfo=ZONE))
        self.assertEqual((identity.shift_kind, identity.shift_date), ("day", "2026-03-25"))
        start, end = shift_window(policy, identity)
        self.assertTrue(start <= datetime(2026, 3, 25, 20, 0, tzinfo=ZONE) < end)


class AnchorTimeToShiftTests(unittest.TestCase):
    def test_spec_example_night_shift_events_anchor_across_midnight(self) -> None:
        policy = _policy()
        identity = ShiftIdentity(shift_date="2026-03-25", shift_kind="night")
        first = anchor_time_to_shift(policy, identity, "22:00")
        second = anchor_time_to_shift(policy, identity, "00:15")
        third = anchor_time_to_shift(policy, identity, "03:00")
        self.assertEqual(first, datetime(2026, 3, 25, 22, 0, tzinfo=ZONE))
        self.assertEqual(second, datetime(2026, 3, 26, 0, 15, tzinfo=ZONE))
        self.assertEqual(third, datetime(2026, 3, 26, 3, 0, tzinfo=ZONE))
        self.assertLess(first, second)
        self.assertLess(second, third)

    def test_day_shift_never_wraps(self) -> None:
        policy = _policy()
        identity = ShiftIdentity(shift_date="2026-03-25", shift_kind="day")
        morning = anchor_time_to_shift(policy, identity, "07:00")
        afternoon = anchor_time_to_shift(policy, identity, "17:00")
        self.assertEqual(morning.date().isoformat(), "2026-03-25")
        self.assertEqual(afternoon.date().isoformat(), "2026-03-25")

    def test_an_end_time_slightly_past_the_nominal_boundary_still_advances_forward(self) -> None:
        policy = _policy()
        identity = ShiftIdentity(shift_date="2026-03-25", shift_kind="night")
        end = anchor_time_to_shift(policy, identity, "06:31")
        self.assertEqual(end, datetime(2026, 3, 26, 6, 31, tzinfo=ZONE))


if __name__ == "__main__":
    unittest.main()
