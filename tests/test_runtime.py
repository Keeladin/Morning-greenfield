from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text

from morning.accounts import MorningAccounts
from morning.db import create_database_engine
from morning.models import AttendanceEntry
from morning.runtime import MorningRuntime
from morning.store import InvalidTransitionError, MorningError, MorningStore

TZ = "Africa/Johannesburg"
ZONE = ZoneInfo(TZ)


def _config() -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", os.environ["MORNING_DATABASE_URL"])
    return config


@pytest.fixture(scope="module", autouse=True)
def schema() -> None:
    if "MORNING_DATABASE_URL" not in os.environ:
        pytest.skip("MORNING_DATABASE_URL is required for runtime tests")
    command.upgrade(_config(), "head")


@pytest.fixture()
def runtime() -> tuple[MorningRuntime, MorningStore, object]:
    database_url = os.environ["MORNING_DATABASE_URL"]
    engine = create_database_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE morning_principals, morning_crews, morning_machines CASCADE"))
        connection.execute(text("DELETE FROM morning_shift_policy"))
    engine.dispose()
    store = MorningStore(database_url)
    store.set_shift_policy(timezone=TZ, day_shift_start="06:00", night_shift_start="18:00")
    accounts = MorningAccounts(store)
    supervisor = accounts.register(username="jurie", password="correct-horse", display_name="Jurie Venter")
    return MorningRuntime(store, accounts, clock=lambda: datetime(2026, 3, 25, 20, 0, tzinfo=ZONE)), store, supervisor


def test_shift_draft_roster_and_submission_semantics(runtime) -> None:
    app, store, supervisor = runtime
    assert app.current_shift().shift_kind == "night"
    assert app.default_reporting_date() == "2026-03-24"
    crew = store.create_crew(name="Crew A")
    person = store.create_person(name="Jurie", employee_number=None, role="Supervisor", crew_id=crew.id)
    store.link_account_person(supervisor.principal_id, person.id)
    first = app.start_draft(supervisor.principal_id, shift_date="2026-03-25", shift_kind="night")
    second = app.start_draft(supervisor.principal_id, shift_date="2026-03-25", shift_kind="night")
    assert first.id == second.id
    assert first.crew_id == crew.id
    app.set_attendance(first.id, (AttendanceEntry(person.id, True),))
    submitted = app.submit_report(first.id)
    assert submitted.status == "submitted"
    with pytest.raises(InvalidTransitionError):
        app.add_other_activity(first.id, category=None, description="too late")


def test_machine_event_round_trip_keeps_operational_wall_clock_for_edits(runtime) -> None:
    app, store, supervisor = runtime
    report = app.start_draft(supervisor.principal_id, shift_date="2026-03-25", shift_kind="night")
    machine = store.create_machine(machine_id="RLH1", machine_type="LHD", section=None)
    updated = app.add_machine_event(
        report.id,
        machine_id=machine.id,
        start_hhmm="22:00",
        end_hhmm="22:40",
        issue="hydraulic hose",
    )
    event = updated.machine_events[0]
    corrected = app.update_machine_event(report.id, event.id, end_hhmm="22:45", issue="corrected")
    end = datetime.fromisoformat(corrected.machine_events[0].end_time).astimezone(ZONE)
    assert end.strftime("%H:%M") == "22:45"


def test_machine_state_is_explicit_and_carry_keeps_provenance(runtime) -> None:
    app, store, supervisor = runtime
    first = app.start_draft(supervisor.principal_id, shift_date="2026-03-25", shift_kind="day")
    machine = store.create_machine(machine_id="RLH1", machine_type="LHD", section=None)
    declared = app.declare_machine_state(
        first.id,
        machine_id=machine.id,
        declared_hhmm="17:55",
        state="not_tested",
        follow_up="Test next shift",
    )
    app.submit_report(first.id)
    second = app.start_draft(supervisor.principal_id, shift_date="2026-03-25", shift_kind="night")
    carried = app.carry_machine_state(second.id, machine_id=machine.id, declared_hhmm="18:00")
    assert carried.provenance == "carried"
    assert carried.source_state_id == declared.id
    assert carried.state == "not_tested"


def test_other_machine_state_requires_note(runtime) -> None:
    app, store, supervisor = runtime
    report = app.start_draft(supervisor.principal_id, shift_date="2026-03-25", shift_kind="night")
    machine = store.create_machine(machine_id="RLH1", machine_type=None, section=None)
    with pytest.raises(MorningError, match="explanatory note"):
        app.declare_machine_state(
            report.id,
            machine_id=machine.id,
            declared_hhmm="22:00",
            state="other",
        )


def test_whatsapp_output_includes_explicit_handover_state(runtime) -> None:
    app, store, supervisor = runtime
    report = app.start_draft(supervisor.principal_id, shift_date="2026-03-25", shift_kind="night")
    machine = store.create_machine(machine_id="RLH1", machine_type=None, section=None)
    app.add_machine_event(
        report.id,
        machine_id=machine.id,
        start_hhmm="22:00",
        end_hhmm="22:40",
        issue="hydraulic hose",
    )
    app.declare_machine_state(
        report.id,
        machine_id=machine.id,
        declared_hhmm="22:40",
        state="not_tested",
    )
    text_output = app.whatsapp_text(report.id)
    assert "22:00-22:40" in text_output
    assert "Machine State at Handover" in text_output
    assert "Not tested" in text_output
