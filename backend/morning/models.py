from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


ShiftKind = Literal["day", "night"]
ReportStatus = Literal["draft", "submitted", "abandoned"]
CardType = Literal["red", "green"]
StopFixStatus = Literal["open", "rectified"]
MorningReportStatus = Literal["waiting", "complete"]
MachineState = Literal["running", "not_tested", "under_repair", "awaiting_parts", "other"]
MachineStateProvenance = Literal["declared", "carried"]

SHIFT_KINDS: frozenset[str] = frozenset({"day", "night"})
CARD_TYPES: frozenset[str] = frozenset({"red", "green"})
STOP_FIX_STATUSES: frozenset[str] = frozenset({"open", "rectified"})
MACHINE_STATES: tuple[MachineState, ...] = (
    "running",
    "not_tested",
    "under_repair",
    "awaiting_parts",
    "other",
)

STOP_FIX_AREAS: tuple[str, ...] = (
    "Support",
    "A Hazard",
    "Working at height",
    "Environmental/Ventilation",
    "Transport and Tramming",
    "De-energised/Lock out",
    "Barring",
    "Lifting",
    "Guarding",
    "Other",
)


@dataclass(frozen=True)
class ShiftPolicy:
    """Configuration, not hard-coded UI logic. A singleton per deployment."""

    timezone: str
    day_shift_start: str
    night_shift_start: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "timezone": self.timezone,
            "day_shift_start": self.day_shift_start,
            "night_shift_start": self.night_shift_start,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class ShiftIdentity:
    """Stable shift/reporting-window identity across calendar boundaries."""

    shift_date: str
    shift_kind: ShiftKind

    @property
    def shift_id(self) -> str:
        return f"{self.shift_date}:{self.shift_kind}"

    def as_dict(self) -> dict[str, Any]:
        return {"shift_date": self.shift_date, "shift_kind": self.shift_kind, "shift_id": self.shift_id}


@dataclass(frozen=True)
class Machine:
    """Morning-owned machine identity. Deactivation does not erase history."""

    id: str
    machine_id: str
    machine_type: str | None
    section: str | None
    active: bool
    created_at: str
    retired_at: str | None = None
    control_room_scope: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "machine_id": self.machine_id,
            "machine_type": self.machine_type,
            "section": self.section,
            "active": self.active,
            "created_at": self.created_at,
            "retired_at": self.retired_at,
            "control_room_scope": self.control_room_scope,
        }


@dataclass(frozen=True)
class Person:
    """Roster personnel, distinct from the supervisor login account."""

    id: str
    name: str
    employee_number: str | None
    role: str | None
    active: bool
    crew_id: str | None
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "employee_number": self.employee_number,
            "role": self.role,
            "active": self.active,
            "crew_id": self.crew_id,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class Crew:
    """A configurable roster group that travels with its supervisor."""

    id: str
    name: str
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "created_at": self.created_at}


@dataclass(frozen=True)
class AttendanceEntry:
    person_id: str
    present: bool

    def as_dict(self) -> dict[str, Any]:
        return {"person_id": self.person_id, "present": self.present}


@dataclass(frozen=True)
class StopFixRecord:
    id: str
    number: str
    issued_at: str
    area_of_concern: str
    location: str
    reason: str
    instruction: str
    status: StopFixStatus
    rectified_at: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "number": self.number,
            "issued_at": self.issued_at,
            "area_of_concern": self.area_of_concern,
            "location": self.location,
            "reason": self.reason,
            "instruction": self.instruction,
            "status": self.status,
            "rectified_at": self.rectified_at,
        }


@dataclass(frozen=True)
class CardObservation:
    """Morning records that a card was issued and why, not the HSE compliance-card system."""

    id: str
    card_type: CardType
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "card_type": self.card_type, "reason": self.reason}


@dataclass(frozen=True)
class MachineEvent:
    """An engineering work interval. It is not, by itself, machine-state or downtime truth."""

    id: str
    machine_id: str
    start_time: str
    end_time: str
    issue: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "machine_id": self.machine_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "issue": self.issue,
        }


@dataclass(frozen=True)
class MachineStateDeclaration:
    """Explicit machine-state truth at a point in time.

    A carried declaration must retain the source declaration it was carried
    from so Morning never presents inherited state as freshly confirmed fact.
    """

    id: str
    machine_id: str
    report_id: str
    declared_at: str
    state: MachineState
    provenance: MachineStateProvenance
    state_note: str | None = None
    source_state_id: str | None = None
    follow_up: str | None = None
    created_at: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "machine_id": self.machine_id,
            "report_id": self.report_id,
            "declared_at": self.declared_at,
            "state": self.state,
            "provenance": self.provenance,
            "state_note": self.state_note,
            "source_state_id": self.source_state_id,
            "follow_up": self.follow_up,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class OtherActivity:
    id: str
    category: str | None
    description: str

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "category": self.category, "description": self.description}


@dataclass(frozen=True)
class ShiftReport:
    """A shift report is a draft while the shift is ongoing and autosaves incrementally."""

    id: str
    shift_date: str
    shift_kind: ShiftKind
    supervisor_principal_id: str
    crew_id: str | None
    status: ReportStatus
    attendance: tuple[AttendanceEntry, ...]
    stop_fix: tuple[StopFixRecord, ...]
    cards: tuple[CardObservation, ...]
    machine_events: tuple[MachineEvent, ...]
    other_activities: tuple[OtherActivity, ...]
    created_at: str
    updated_at: str
    submitted_at: str | None = None

    @property
    def shift_id(self) -> str:
        return f"{self.shift_date}:{self.shift_kind}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "shift_date": self.shift_date,
            "shift_kind": self.shift_kind,
            "shift_id": self.shift_id,
            "supervisor_principal_id": self.supervisor_principal_id,
            "crew_id": self.crew_id,
            "status": self.status,
            "attendance": [item.as_dict() for item in self.attendance],
            "stop_fix": [item.as_dict() for item in self.stop_fix],
            "cards": [item.as_dict() for item in self.cards],
            "machine_events": [item.as_dict() for item in self.machine_events],
            "other_activities": [item.as_dict() for item in self.other_activities],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "submitted_at": self.submitted_at,
        }


@dataclass(frozen=True)
class ControlRoomObservation:
    """Control-room observation preserved distinctly from supervisor evidence."""

    id: str
    reporting_date: str
    machine_id: str | None
    raw_machine_label: str
    start_time: str | None
    end_time: str | None
    description: str
    source_message_id: str
    source_artifact_id: str | None
    extracted_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "reporting_date": self.reporting_date,
            "machine_id": self.machine_id,
            "raw_machine_label": self.raw_machine_label,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "description": self.description,
            "source_message_id": self.source_message_id,
            "source_artifact_id": self.source_artifact_id,
            "extracted_at": self.extracted_at,
        }


@dataclass(frozen=True)
class ExpectedInputStatus:
    key: str
    label: str
    present: bool


@dataclass(frozen=True)
class MorningReportRecord:
    """A reproducible rendered projection; canonical truth remains in typed source records."""

    reporting_date: str
    status: MorningReportStatus
    expected_inputs: tuple[ExpectedInputStatus, ...]
    detailed_text: str | None
    compact_text: str | None
    generated_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "reporting_date": self.reporting_date,
            "status": self.status,
            "expected_inputs": [
                {"key": item.key, "label": item.label, "present": item.present}
                for item in self.expected_inputs
            ],
            "detailed_text": self.detailed_text,
            "compact_text": self.compact_text,
            "generated_at": self.generated_at,
        }
