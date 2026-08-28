from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from .aggregate import MachineAggregate, ReportBundle
from .models import Machine, MachineStateDeclaration, Person, ShiftReport

STATE_LABELS = {
    "running": "Running / operational",
    "not_tested": "Not tested",
    "under_repair": "Still under repair / standing",
    "awaiting_parts": "Awaiting parts",
    "other": "Other",
}


def _hhmm(value: str, timezone: str) -> str:
    try:
        moment = datetime.fromisoformat(value)
        if moment.tzinfo is not None:
            moment = moment.astimezone(ZoneInfo(timezone))
        return moment.strftime("%H:%M")
    except (ValueError, KeyError):
        return value


def _duration_label(total_seconds: float) -> str:
    minutes = round(total_seconds / 60)
    hours, minutes = divmod(minutes, 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def _shift_label(shift_kind: str) -> str:
    return "Day Shift" if shift_kind == "day" else "Night Shift"


def _state_label(state: MachineStateDeclaration) -> str:
    label = STATE_LABELS.get(state.state, state.state)
    if state.state == "other" and state.state_note:
        label = f"{label}: {state.state_note}"
    if state.provenance == "carried":
        label += " [carried from prior declaration]"
    return label


def _latest_states(states: tuple[MachineStateDeclaration, ...]) -> dict[str, MachineStateDeclaration]:
    latest: dict[str, MachineStateDeclaration] = {}
    for state in sorted(states, key=lambda item: (item.declared_at, item.created_at or "", item.id)):
        latest[state.machine_id] = state
    return latest


def render_whatsapp_report(
    report: ShiftReport,
    *,
    supervisor_name: str,
    persons_by_id: dict[str, Person],
    machines_by_id: dict[str, Machine],
    timezone: str,
    machine_states: tuple[MachineStateDeclaration, ...] = (),
) -> str:
    """Deterministic WhatsApp-ready text for one submitted or draft shift."""

    def person_name(person_id: str) -> str:
        person = persons_by_id.get(person_id)
        return person.name if person is not None else person_id

    def machine_label(machine_id: str) -> str:
        machine = machines_by_id.get(machine_id)
        return machine.machine_id if machine is not None else machine_id

    lines: list[str] = [
        f"*{_shift_label(report.shift_kind)} Report — {report.shift_date}*",
        f"Supervisor: {supervisor_name}",
        "",
        "*Attendance*",
    ]
    present = [person_name(entry.person_id) for entry in report.attendance if entry.present]
    absent = [person_name(entry.person_id) for entry in report.attendance if not entry.present]
    lines.append(f"Present: {len(present)}/{len(report.attendance)}")
    if absent:
        lines.append(f"Absent: {', '.join(absent)}")

    lines += ["", "*Safety*"]
    open_count = sum(1 for item in report.stop_fix if item.status == "open")
    rectified_count = sum(1 for item in report.stop_fix if item.status == "rectified")
    lines.append(f"Stop & Fix: {open_count} open, {rectified_count} rectified")
    for item in report.stop_fix:
        lines.append(f"  - {item.number} ({item.area_of_concern}) at {item.location}: {item.reason} [{item.status}]")
    green = sum(1 for card in report.cards if card.card_type == "green")
    red = sum(1 for card in report.cards if card.card_type == "red")
    lines.append(f"Cards: {green} green, {red} red")
    for card in report.cards:
        lines.append(f"  - {card.card_type.capitalize()}: {card.reason}")

    lines += ["", "*Machine Activity*"]
    if report.machine_events:
        for event in report.machine_events:
            lines.append(
                f"{machine_label(event.machine_id)}: {_hhmm(event.start_time, timezone)}-"
                f"{_hhmm(event.end_time, timezone)} {event.issue}"
            )
    else:
        lines.append("No machine activity reported.")

    latest = _latest_states(machine_states)
    if latest:
        lines += ["", "*Machine State at Handover*"]
        for machine_id in sorted(latest, key=machine_label):
            lines.append(f"{machine_label(machine_id)}: {_state_label(latest[machine_id])}")

    lines += ["", "*Other Activities*"]
    if report.other_activities:
        for activity in report.other_activities:
            prefix = f"{activity.category}: " if activity.category else ""
            lines.append(f"- {prefix}{activity.description}")
    else:
        lines.append("None.")
    return "\n".join(lines)


def render_detailed_report(bundle: ReportBundle) -> str:
    lines: list[str] = [f"*24-Hour Departmental Report — {bundle.reporting_date}*", "", "Expected inputs:"]
    for item in bundle.expected_inputs:
        lines.append(f"  - {item.label}: {'present' if item.present else 'MISSING'}")

    lines += ["", f"Attendance: {bundle.attendance.present_count} present, {bundle.attendance.absent_count} absent"]
    if bundle.attendance.absent_names:
        lines.append(f"  Absent: {', '.join(bundle.attendance.absent_names)}")

    lines += [
        "",
        "Safety:",
        f"  Stop & Fix: {bundle.safety.stop_fix_open} open, {bundle.safety.stop_fix_rectified} rectified",
        f"  Cards issued: {bundle.safety.green_cards} green, {bundle.safety.red_cards} red",
    ]
    for card_type, reason in bundle.safety.card_reasons:
        lines.append(f"    - {card_type.capitalize()}: {reason}")

    latest_states = _latest_states(bundle.machine_states)
    lines += ["", "Machine activity:"]
    if not bundle.machine_aggregates:
        lines.append("  No machine activity reported.")
    for aggregate in bundle.machine_aggregates:
        flag = "" if aggregate.matched else "  [unmatched machine label - needs review]"
        lines.append(f"  {aggregate.machine_display_id}{flag}")
        if aggregate.work_event_count:
            lines.append(
                f"    Engineering work time recorded: {_duration_label(aggregate.total_work_interval_seconds)} "
                f"across {aggregate.work_event_count} work event(s)"
            )
        if aggregate.machine_internal_id and aggregate.machine_internal_id in latest_states:
            lines.append(f"    Reported state: {_state_label(latest_states[aggregate.machine_internal_id])}")
        else:
            lines.append("    Reported state: not declared")
        for event in aggregate.events:
            origin = "shift report" if event.origin == "shift_report" else "control room"
            when = (
                f"{event.start.astimezone(ZoneInfo(bundle.timezone)).strftime('%H:%M')}-"
                f"{event.end.astimezone(ZoneInfo(bundle.timezone)).strftime('%H:%M')}"
                if event.start and event.end
                else "no times given"
            )
            lines.append(f"    - [{origin}] {when}: {event.description}")

    lines += ["", "Other activities:"]
    if not bundle.other_activities:
        lines.append("  None reported.")
    for activity in bundle.other_activities:
        prefix = f"{activity.category}: " if activity.category else ""
        lines.append(f"  [{_shift_label(activity.shift_kind)}] {prefix}{activity.description}")

    if bundle.observations:
        lines += ["", "Control-room observations:"]
        for observation in bundle.observations:
            lines.append(f"  {observation.raw_machine_label}: {observation.description}")
    return "\n".join(lines)


@dataclass(frozen=True)
class CompactMachineRow:
    machine_display_id: str
    matched: bool
    work_time_label: str
    key_issues: str
    status: str


def compact_rows(bundle: ReportBundle) -> tuple[CompactMachineRow, ...]:
    latest_states = _latest_states(bundle.machine_states)

    def status_for(aggregate: MachineAggregate) -> str:
        if aggregate.machine_internal_id and aggregate.machine_internal_id in latest_states:
            return _state_label(latest_states[aggregate.machine_internal_id])
        return "No machine state declared."

    return tuple(
        CompactMachineRow(
            machine_display_id=aggregate.machine_display_id,
            matched=aggregate.matched,
            work_time_label=_duration_label(aggregate.total_work_interval_seconds),
            key_issues="; ".join(aggregate.key_issues) if aggregate.key_issues else "No issues logged.",
            status=status_for(aggregate),
        )
        for aggregate in bundle.machine_aggregates
    )


def render_compact_report(bundle: ReportBundle) -> str:
    """Brief meeting projection without inventing downtime from engineering activity."""

    lines = [f"*Department Meeting Summary — {bundle.reporting_date}*"]
    if bundle.status != "complete":
        missing = [item.label for item in bundle.expected_inputs if not item.present]
        lines += ["", f"INCOMPLETE - missing: {', '.join(missing)}"]
    lines.append("")
    rows = compact_rows(bundle)
    if not rows:
        lines.append("No machine activity reported.")
    for row in rows:
        flag = "" if row.matched else " [unmatched]"
        lines.append(
            f"{row.machine_display_id}{flag}: work recorded {row.work_time_label}; "
            f"state {row.status}; {row.key_issues}"
        )
    return "\n".join(lines)
