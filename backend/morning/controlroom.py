from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from .models import Machine


@dataclass(frozen=True)
class ExtractedObservation:
    """One deterministic control-room entry before persistence."""

    raw_machine_label: str
    machine_id: str
    start_time: str
    end_time: str
    description: str


_ENTRY_PATTERN = re.compile(
    r"^(?P<start>\d{1,2}:\d{2})"
    r".+?"
    r"\s(?P<end>\d{1,2}:\d{2})\s(?P<hours>\d{1,2}:\d{2})"
    r"(?P<tail>.*)$"
)
_SHIFT_HEADER_PATTERN = re.compile(r"^\d\.\s*(Day|Afternoon|Night)Shift:\s*$", re.IGNORECASE)


def _normalize_code(label: str) -> str:
    return re.sub(r"[\s\-]+", "", label).upper()


def _code_search_pattern(code: str) -> re.Pattern[str]:
    body = r"[\s\-]*".join(re.escape(character) for character in code)
    return re.compile(body, re.IGNORECASE)


def _anchor_start_date(reporting_date: date, hour: int, *, in_night_shift: bool) -> date:
    if in_night_shift and hour < 12:
        return reporting_date + timedelta(days=1)
    return reporting_date


def extract_observations(
    text: str,
    *,
    machines: tuple[Machine, ...],
    reporting_date: str,
) -> tuple[ExtractedObservation, ...]:
    """Extract only machines explicitly curated into control-room scope.

    The source may contain many other machines. Morning never expands the
    configured scope by guessing from the PDF.
    """

    in_scope = {
        _normalize_code(machine.machine_id): machine
        for machine in machines
        if machine.control_room_scope
    }
    codes_longest_first = sorted(in_scope, key=len, reverse=True)
    patterns = {code: _code_search_pattern(code) for code in codes_longest_first}

    base_date = date.fromisoformat(reporting_date)
    in_night_shift = False
    observations: list[ExtractedObservation] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        shift_header = _SHIFT_HEADER_PATTERN.match(line)
        if shift_header:
            in_night_shift = shift_header.group(1).lower() == "night"
            continue
        match = _ENTRY_PATTERN.match(line)
        if not match:
            continue
        tail = match.group("tail")

        found: tuple[Machine, re.Match[str]] | None = None
        for code in codes_longest_first:
            code_match = patterns[code].search(tail)
            if code_match is None:
                continue
            trailing = tail[code_match.end() : code_match.end() + 1]
            if trailing and trailing.isalnum():
                continue
            found = (in_scope[code], code_match)
            break
        if found is None:
            continue

        machine, code_match = found
        start_hhmm = match.group("start")
        end_hhmm = match.group("end")
        start_date = _anchor_start_date(base_date, int(start_hhmm[:2]), in_night_shift=in_night_shift)
        end_date = start_date + timedelta(days=1) if end_hhmm <= start_hhmm else start_date
        start_dt = datetime.combine(start_date, datetime.strptime(start_hhmm, "%H:%M").time())
        end_dt = datetime.combine(end_date, datetime.strptime(end_hhmm, "%H:%M").time())

        observations.append(
            ExtractedObservation(
                raw_machine_label=tail[code_match.start() :].strip(),
                machine_id=machine.id,
                start_time=start_dt.isoformat(),
                end_time=end_dt.isoformat(),
                description=tail[: code_match.start()].strip() or tail[code_match.start() :].strip(),
            )
        )
    return tuple(observations)


@dataclass(frozen=True)
class ControlRoomMatchCriteria:
    approved_senders: tuple[str, ...]
    subject_pattern: str = ""


def is_control_room_email(
    *,
    sender: str,
    subject: str,
    has_pdf_attachment: bool,
    criteria: ControlRoomMatchCriteria,
) -> bool:
    if not has_pdf_attachment:
        return False
    sender_normalized = sender.strip().casefold()
    if not any(sender_normalized == approved.strip().casefold() for approved in criteria.approved_senders):
        return False
    pattern = criteria.subject_pattern.strip().casefold()
    return not pattern or pattern in subject.strip().casefold()
