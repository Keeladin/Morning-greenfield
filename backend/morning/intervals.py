from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


class IntervalError(ValueError):
    pass


@dataclass(frozen=True)
class DowntimeInterval:
    start: datetime
    end: datetime
    source: str

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise IntervalError(f"interval end must be after start: {self.start} -> {self.end}")


@dataclass(frozen=True)
class MergedInterval:
    start: datetime
    end: datetime
    sources: tuple[str, ...]

    @property
    def duration_seconds(self) -> float:
        return (self.end - self.start).total_seconds()


def merge_intervals(intervals: tuple[DowntimeInterval, ...]) -> tuple[MergedInterval, ...]:
    """Deterministically merge overlapping or touching intervals and preserve provenance."""

    if not intervals:
        return ()
    ordered = sorted(intervals, key=lambda item: (item.start, item.end))
    merged: list[MergedInterval] = []
    current_start = ordered[0].start
    current_end = ordered[0].end
    current_sources = [ordered[0].source]
    for item in ordered[1:]:
        if item.start <= current_end:
            if item.end > current_end:
                current_end = item.end
            current_sources.append(item.source)
        else:
            merged.append(MergedInterval(current_start, current_end, tuple(current_sources)))
            current_start, current_end, current_sources = item.start, item.end, [item.source]
    merged.append(MergedInterval(current_start, current_end, tuple(current_sources)))
    return tuple(merged)


def total_downtime_seconds(intervals: tuple[DowntimeInterval, ...]) -> float:
    """Reference compatibility helper; do not infer that every input interval is genuine machine downtime."""

    return sum(item.duration_seconds for item in merge_intervals(intervals))


def clip_interval(
    interval: DowntimeInterval,
    *,
    window_start: datetime,
    window_end: datetime,
) -> DowntimeInterval | None:
    """Clip an interval to a reporting window without changing its source record."""

    start = max(interval.start, window_start)
    end = min(interval.end, window_end)
    if end <= start:
        return None
    return DowntimeInterval(start=start, end=end, source=interval.source)
