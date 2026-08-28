from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Callable

from .accounts import MorningAccounts
from .aggregate import ReportBundle, build_report_bundle
from .models import (
    MACHINE_STATES,
    SHIFT_KINDS,
    AttendanceEntry,
    CardObservation,
    MachineEvent,
    MachineStateDeclaration,
    OtherActivity,
    Person,
    ShiftIdentity,
    ShiftPolicy,
    ShiftReport,
    StopFixRecord,
)
from .renderers import render_compact_report, render_detailed_report, render_whatsapp_report
from .shift import anchor_time_to_shift, require_zone, resolve_shift
from .store import MorningError, MorningStore, UnknownRecordError, new_id

DEFAULT_POLICY = ShiftPolicy(
    timezone="Africa/Johannesburg",
    day_shift_start="06:00",
    night_shift_start="18:00",
    updated_at="",
)

Clock = Callable[[], datetime]


class MorningRuntime:
    """Standalone Morning business logic for shift capture and reporting."""

    def __init__(self, store: MorningStore, accounts: MorningAccounts, *, clock: Clock | None = None) -> None:
        self.store = store
        self.accounts = accounts
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def shift_policy(self) -> ShiftPolicy:
        return self.store.get_shift_policy() or DEFAULT_POLICY

    def current_shift(self, *, now: datetime | None = None) -> ShiftIdentity:
        return resolve_shift(self.shift_policy(), at=now or self._clock())

    def default_reporting_date(self, *, now: datetime | None = None) -> str:
        zone = require_zone(self.shift_policy().timezone)
        moment = now or self._clock()
        local = moment.astimezone(zone) if moment.tzinfo is not None else moment.replace(tzinfo=zone)
        return (local.date() - timedelta(days=1)).isoformat()

    def supervisor_crew_id(self, supervisor_principal_id: str) -> str | None:
        account = self.store.account_by_principal(supervisor_principal_id)
        if account is None or account.get("person_id") is None:
            return None
        try:
            person = self.store.get_person(account["person_id"])
        except UnknownRecordError:
            return None
        return person.crew_id

    def expected_attendance(self, crew_id: str | None) -> tuple[Person, ...]:
        if crew_id is None:
            return ()
        return self.store.roster_for_crew(crew_id)

    def current_draft(self, supervisor_principal_id: str) -> ShiftReport | None:
        return self.store.current_draft(supervisor_principal_id)

    def start_draft(self, supervisor_principal_id: str, *, shift_date: str, shift_kind: str) -> ShiftReport:
        if shift_kind not in SHIFT_KINDS:
            raise MorningError(f"unsupported shift kind: {shift_kind}")
        crew_id = self.supervisor_crew_id(supervisor_principal_id)
        return self.store.get_or_create_draft(
            supervisor_principal_id=supervisor_principal_id,
            shift_date=shift_date,
            shift_kind=shift_kind,
            crew_id=crew_id,
        )

    def abandon_draft(self, report_id: str) -> ShiftReport:
        return self.store.abandon_report(report_id)

    def get_report(self, report_id: str) -> ShiftReport:
        return self.store.get_report(report_id)

    def report_participants(self, report_id: str) -> tuple[Person, ...]:
        report = self.store.get_report(report_id)
        person_ids = tuple(dict.fromkeys(entry.person_id for entry in report.attendance))
        return self.store.persons_by_ids(person_ids)

    def my_reports(self, supervisor_principal_id: str) -> tuple[ShiftReport, ...]:
        return self.store.list_reports(supervisor_principal_id=supervisor_principal_id)

    # Stage 1: attendance
    def set_attendance(self, report_id: str, entries: tuple[AttendanceEntry, ...]) -> ShiftReport:
        return self.store.replace_attendance(report_id, entries)

    # Stage 2: safety
    def add_stop_fix(
        self,
        report_id: str,
        *,
        number: str,
        issued_at: str,
        area_of_concern: str,
        location: str,
        reason: str,
        instruction: str,
    ) -> ShiftReport:
        record = StopFixRecord(
            id=new_id("stopfix"),
            number=number,
            issued_at=issued_at,
            area_of_concern=area_of_concern,
            location=location,
            reason=reason,
            instruction=instruction,
            status="open",
        )
        return self.store.add_stop_fix(report_id, record)

    def update_stop_fix(self, report_id: str, stop_fix_id: str, **fields) -> ShiftReport:
        current = self._find(self.store.get_report(report_id).stop_fix, stop_fix_id, "stop & fix record")
        return self.store.update_stop_fix(report_id, replace(current, **fields))

    def delete_stop_fix(self, report_id: str, stop_fix_id: str) -> ShiftReport:
        return self.store.delete_stop_fix(report_id, stop_fix_id)

    def add_card(self, report_id: str, *, card_type: str, reason: str) -> ShiftReport:
        if card_type not in {"red", "green"}:
            raise MorningError(f"unsupported card type: {card_type}")
        return self.store.add_card(report_id, CardObservation(id=new_id("card"), card_type=card_type, reason=reason))

    def delete_card(self, report_id: str, card_id: str) -> ShiftReport:
        return self.store.delete_card(report_id, card_id)

    # Stage 3: machine activity
    def add_machine_event(
        self,
        report_id: str,
        *,
        machine_id: str,
        start_hhmm: str,
        end_hhmm: str,
        issue: str,
    ) -> ShiftReport:
        report = self.store.get_report(report_id)
        start_time, end_time = self._anchor_event_times(report, start_hhmm, end_hhmm)
        return self.store.add_machine_event(
            report_id,
            MachineEvent(
                id=new_id("event"),
                machine_id=machine_id,
                start_time=start_time,
                end_time=end_time,
                issue=issue,
            ),
        )

    def update_machine_event(
        self,
        report_id: str,
        event_id: str,
        *,
        machine_id: str | None = None,
        start_hhmm: str | None = None,
        end_hhmm: str | None = None,
        issue: str | None = None,
    ) -> ShiftReport:
        report = self.store.get_report(report_id)
        current = self._find(report.machine_events, event_id, "machine event")
        if start_hhmm is not None or end_hhmm is not None:
            policy = self.shift_policy()
            start_time, end_time = self._anchor_event_times(
                report,
                start_hhmm or self._as_hhmm(current.start_time, policy.timezone),
                end_hhmm or self._as_hhmm(current.end_time, policy.timezone),
            )
        else:
            start_time, end_time = current.start_time, current.end_time
        updated = replace(
            current,
            machine_id=machine_id or current.machine_id,
            start_time=start_time,
            end_time=end_time,
            issue=issue if issue is not None else current.issue,
        )
        return self.store.update_machine_event(report_id, updated)

    def delete_machine_event(self, report_id: str, event_id: str) -> ShiftReport:
        return self.store.delete_machine_event(report_id, event_id)

    def declare_machine_state(
        self,
        report_id: str,
        *,
        machine_id: str,
        declared_hhmm: str,
        state: str,
        state_note: str | None = None,
        follow_up: str | None = None,
    ) -> MachineStateDeclaration:
        if state not in MACHINE_STATES:
            raise MorningError(f"unsupported machine state: {state}")
        if state == "other" and not (state_note or "").strip():
            raise MorningError("other machine state requires an explanatory note")
        report = self.store.get_report(report_id)
        declared_at = anchor_time_to_shift(
            self.shift_policy(),
            ShiftIdentity(shift_date=report.shift_date, shift_kind=report.shift_kind),
            declared_hhmm,
        ).isoformat()
        return self.store.add_machine_state(
            MachineStateDeclaration(
                id=new_id("state"),
                machine_id=machine_id,
                report_id=report_id,
                declared_at=declared_at,
                state=state,
                provenance="declared",
                state_note=state_note,
                follow_up=follow_up,
            )
        )

    def carry_machine_state(
        self,
        report_id: str,
        *,
        machine_id: str,
        declared_hhmm: str,
    ) -> MachineStateDeclaration:
        source = self.store.latest_machine_state(machine_id)
        if source is None:
            raise MorningError(f"no prior machine state exists for: {machine_id}")
        report = self.store.get_report(report_id)
        declared_at = anchor_time_to_shift(
            self.shift_policy(),
            ShiftIdentity(shift_date=report.shift_date, shift_kind=report.shift_kind),
            declared_hhmm,
        ).isoformat()
        return self.store.add_machine_state(
            MachineStateDeclaration(
                id=new_id("state"),
                machine_id=machine_id,
                report_id=report_id,
                declared_at=declared_at,
                state=source.state,
                provenance="carried",
                state_note=source.state_note,
                source_state_id=source.id,
                follow_up=source.follow_up,
            )
        )

    def machine_states_for_report(self, report_id: str) -> tuple[MachineStateDeclaration, ...]:
        return self.store.list_machine_states(report_id=report_id)

    def _anchor_event_times(self, report: ShiftReport, start_hhmm: str, end_hhmm: str) -> tuple[str, str]:
        policy = self.shift_policy()
        identity = ShiftIdentity(shift_date=report.shift_date, shift_kind=report.shift_kind)
        start = anchor_time_to_shift(policy, identity, start_hhmm)
        end = anchor_time_to_shift(policy, identity, end_hhmm)
        if end <= start:
            raise MorningError("machine event end time must be after its start time")
        return start.isoformat(), end.isoformat()

    @staticmethod
    def _as_hhmm(iso_value: str, timezone_name: str) -> str:
        moment = datetime.fromisoformat(iso_value)
        if moment.tzinfo is not None:
            moment = moment.astimezone(require_zone(timezone_name))
        return moment.strftime("%H:%M")

    # Stage 4: other activities
    def add_other_activity(self, report_id: str, *, category: str | None, description: str) -> ShiftReport:
        return self.store.add_other_activity(
            report_id,
            OtherActivity(id=new_id("activity"), category=category, description=description),
        )

    def delete_other_activity(self, report_id: str, activity_id: str) -> ShiftReport:
        return self.store.delete_other_activity(report_id, activity_id)

    def submit_report(self, report_id: str) -> ShiftReport:
        return self.store.submit_report(report_id)

    def whatsapp_text(self, report_id: str) -> str:
        report = self.store.get_report(report_id)
        supervisor = self.accounts.principal_for(report.supervisor_principal_id)
        persons_by_id = {person.id: person for person in self.store.list_persons()}
        machines_by_id = {machine.id: machine for machine in self.store.list_machines()}
        return render_whatsapp_report(
            report,
            supervisor_name=supervisor.display_name,
            persons_by_id=persons_by_id,
            machines_by_id=machines_by_id,
            timezone=self.shift_policy().timezone,
            machine_states=self.store.list_machine_states(report_id=report_id),
        )

    def daily_bundle(self, reporting_date: str, *, require_control_room: bool = True) -> ReportBundle:
        reports = tuple(
            report for report in self.store.list_reports(shift_date=reporting_date) if report.status == "submitted"
        )
        observations = self.store.list_observations(reporting_date=reporting_date)
        machine_states = tuple(
            state for report in reports for state in self.store.list_machine_states(report_id=report.id)
        )
        machines_by_id = {machine.id: machine for machine in self.store.list_machines()}
        persons_by_id = {person.id: person for person in self.store.list_persons()}
        return build_report_bundle(
            reporting_date=reporting_date,
            timezone=self.shift_policy().timezone,
            shift_reports=reports,
            observations=observations,
            machine_states=machine_states,
            machines_by_id=machines_by_id,
            persons_by_id=persons_by_id,
            require_control_room=require_control_room,
        )

    def detailed_text(self, reporting_date: str, *, require_control_room: bool = True) -> str:
        return render_detailed_report(self.daily_bundle(reporting_date, require_control_room=require_control_room))

    def compact_text(self, reporting_date: str, *, require_control_room: bool = True) -> str:
        return render_compact_report(self.daily_bundle(reporting_date, require_control_room=require_control_room))

    @staticmethod
    def _find(items, item_id: str, label: str):
        found = next((item for item in items if item.id == item_id), None)
        if found is None:
            raise UnknownRecordError(f"unknown {label}: {item_id}")
        return found
