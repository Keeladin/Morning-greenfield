from __future__ import annotations

import pytest

from morning.controlroom import ControlRoomMatchCriteria, extract_observations, is_control_room_email
from morning.models import Machine
from morning.pdf_text import PdfTextError, extract_pdf_text


def _machine(internal_id: str, display: str, *, active: bool = True, in_scope: bool = True) -> Machine:
    return Machine(
        id=internal_id,
        machine_id=display,
        machine_type=None,
        section=None,
        active=active,
        created_at="now",
        control_room_scope=in_scope,
    )


def test_extracts_known_in_scope_machine() -> None:
    text = "11:49Other - specify Mining OperationalSlipping 12:30 00:41 Belt slippingOperational DelaysNPC2 conveyor"
    observations = extract_observations(text, machines=(_machine("m1", "NPC2"),), reporting_date="2026-08-13")
    assert len(observations) == 1
    assert observations[0].machine_id == "m1"
    assert observations[0].raw_machine_label == "NPC2 conveyor"
    assert observations[0].start_time == "2026-08-13T11:49:00"
    assert observations[0].end_time == "2026-08-13T12:30:00"


def test_scope_is_explicit_and_independent_of_active_state() -> None:
    text = "22:45Starter MechanicalBroken 23:47 01:02 Wont StartEngineRLH-04"
    in_scope = extract_observations(
        text,
        machines=(_machine("m1", "RLH-04", active=False, in_scope=True),),
        reporting_date="2026-08-13",
    )
    out_scope = extract_observations(
        text,
        machines=(_machine("m1", "RLH-04", active=True, in_scope=False),),
        reporting_date="2026-08-13",
    )
    assert len(in_scope) == 1
    assert out_scope == ()


def test_normalizes_machine_code_variants_and_night_shift_dates() -> None:
    text = "3. NightShift:\n00:10Brakes MechanicalBroken 01:07 00:57 Brake faultAxleSTC- 14"
    observations = extract_observations(text, machines=(_machine("m1", "STC14"),), reporting_date="2026-08-13")
    assert observations[0].start_time == "2026-08-14T00:10:00"
    assert observations[0].end_time == "2026-08-14T01:07:00"


def test_control_room_email_match_fails_closed() -> None:
    criteria = ControlRoomMatchCriteria(
        approved_senders=("controlroom@mine.example",),
        subject_pattern="Control Room Report",
    )
    assert is_control_room_email(
        sender="ControlRoom@Mine.Example",
        subject="Daily Control Room Report",
        has_pdf_attachment=True,
        criteria=criteria,
    )
    assert not is_control_room_email(
        sender="someone@mine.example",
        subject="Daily Control Room Report",
        has_pdf_attachment=True,
        criteria=criteria,
    )
    assert not is_control_room_email(
        sender="controlroom@mine.example",
        subject="Daily Control Room Report",
        has_pdf_attachment=False,
        criteria=criteria,
    )


def test_malformed_pdf_fails_closed() -> None:
    with pytest.raises(PdfTextError):
        extract_pdf_text(b"not a real pdf")
