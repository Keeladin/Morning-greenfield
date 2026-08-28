from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .models import ShiftIdentity, ShiftPolicy


class ShiftError(ValueError):
    pass


def require_zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(str(name).strip())
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ShiftError(f"unknown timezone: {name}") from exc


def _parse_hhmm(value: str, *, field: str) -> time:
    try:
        hour, minute = str(value).strip().split(":")
        return time(int(hour), int(minute))
    except (ValueError, TypeError) as exc:
        raise ShiftError(f"{field} must be an HH:MM time") from exc


def _boundaries(policy: ShiftPolicy) -> tuple[time, time]:
    day_start = _parse_hhmm(policy.day_shift_start, field="day_shift_start")
    night_start = _parse_hhmm(policy.night_shift_start, field="night_shift_start")
    if day_start == night_start:
        raise ShiftError("day_shift_start and night_shift_start must differ")
    return day_start, night_start


def shift_window(policy: ShiftPolicy, identity: ShiftIdentity) -> tuple[datetime, datetime]:
    """Return the [start, end) instant boundaries of one configured shift."""

    zone = require_zone(policy.timezone)
    day_start, night_start = _boundaries(policy)
    shift_date = date.fromisoformat(identity.shift_date)

    start_time, end_time = (day_start, night_start) if identity.shift_kind == "day" else (night_start, day_start)
    start = datetime.combine(shift_date, start_time, tzinfo=zone)
    end_date = shift_date + timedelta(days=1) if end_time <= start_time else shift_date
    end = datetime.combine(end_date, end_time, tzinfo=zone)
    return start, end


def resolve_shift(policy: ShiftPolicy, *, at: datetime) -> ShiftIdentity:
    """Resolve an instant to the configured shift without manual inference."""

    zone = require_zone(policy.timezone)
    _boundaries(policy)
    local = at.astimezone(zone) if at.tzinfo is not None else at.replace(tzinfo=zone)

    for days_back in (1, 0):
        candidate_date = (local.date() - timedelta(days=days_back)).isoformat()
        for kind in ("day", "night"):
            identity = ShiftIdentity(shift_date=candidate_date, shift_kind=kind)
            start, end = shift_window(policy, identity)
            if start <= local < end:
                return identity
    raise ShiftError("could not resolve a shift for the given time")


def anchor_time_to_shift(policy: ShiftPolicy, identity: ShiftIdentity, hhmm: str) -> datetime:
    """Anchor a bare HH:MM value to its correct date inside a shift."""

    zone = require_zone(policy.timezone)
    clock = _parse_hhmm(hhmm, field="time")
    start, _end = shift_window(policy, identity)
    shift_date = date.fromisoformat(identity.shift_date)
    candidate = datetime.combine(shift_date, clock, tzinfo=zone)
    if candidate < start:
        candidate += timedelta(days=1)
    return candidate


def reporting_window(policy: ShiftPolicy, reporting_date: str) -> tuple[datetime, datetime]:
    """Return the 24h reporting window from one day-shift start to the next."""

    zone = require_zone(policy.timezone)
    day_start, _night_start = _boundaries(policy)
    start_date = date.fromisoformat(reporting_date)
    start = datetime.combine(start_date, day_start, tzinfo=zone)
    end = datetime.combine(start_date + timedelta(days=1), day_start, tzinfo=zone)
    return start, end
