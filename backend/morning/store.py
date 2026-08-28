from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, time
from typing import Any, Iterator
from uuid import uuid4

import psycopg
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation
from psycopg.rows import dict_row

from .models import (
    AttendanceEntry,
    CardObservation,
    ControlRoomObservation,
    Crew,
    Machine,
    MachineEvent,
    MachineStateDeclaration,
    OtherActivity,
    Person,
    ShiftPolicy,
    ShiftReport,
    StopFixRecord,
)


class MorningError(ValueError):
    pass


class UnknownRecordError(MorningError):
    pass


class InvalidTransitionError(MorningError):
    pass


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def _psycopg_dsn(database_url: str) -> str:
    """Accept the SQLAlchemy-style URL used by Alembic/CI as a psycopg DSN."""

    return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _hhmm(value: Any) -> str:
    if isinstance(value, time):
        return value.strftime("%H:%M")
    text = str(value)
    return text[:5]


def _json_safe_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: _iso(value) if isinstance(value, (datetime, date, time)) else value for key, value in row.items()}


class MorningStore:
    """Morning-owned PostgreSQL persistence.

    The public method contract deliberately follows the proven SQLite
    MorningStore so MorningRuntime can move without a business-logic rewrite.
    The database itself launches fresh; this class contains no legacy-data
    migration path.
    """

    def __init__(self, database_url: str) -> None:
        if not database_url:
            raise ValueError("database_url is required")
        self.database_url = database_url
        self._dsn = _psycopg_dsn(database_url)

    def _connect(self) -> Connection[dict[str, Any]]:
        return psycopg.connect(self._dsn, row_factory=dict_row)

    @contextmanager
    def _db(self) -> Iterator[Connection[dict[str, Any]]]:
        with self._connect() as db:
            with db.transaction():
                yield db

    # -- principals -------------------------------------------------------

    def create_principal(
        self,
        *,
        principal_id: str,
        display_name: str,
        role: str = "supervisor",
        status: str = "active",
    ) -> dict[str, Any]:
        try:
            with self._db() as db:
                row = db.execute(
                    """INSERT INTO morning_principals (id, display_name, role, status)
                       VALUES (%s, %s, %s, %s)
                       RETURNING *""",
                    (principal_id, display_name, role, status),
                ).fetchone()
        except (UniqueViolation, psycopg.errors.CheckViolation) as exc:
            raise MorningError(f"invalid or duplicate principal: {principal_id}") from exc
        return _json_safe_row(row)

    def principal_by_id(self, principal_id: str) -> dict[str, Any] | None:
        with self._db() as db:
            row = db.execute("SELECT * FROM morning_principals WHERE id=%s", (principal_id,)).fetchone()
        return None if row is None else _json_safe_row(row)

    def set_principal_status(self, principal_id: str, status: str) -> dict[str, Any]:
        with self._db() as db:
            row = db.execute(
                """UPDATE morning_principals
                   SET status=%s, updated_at=CURRENT_TIMESTAMP
                   WHERE id=%s RETURNING *""",
                (status, principal_id),
            ).fetchone()
        if row is None:
            raise UnknownRecordError(f"unknown principal: {principal_id}")
        return _json_safe_row(row)

    # -- shift policy -----------------------------------------------------

    def get_shift_policy(self) -> ShiftPolicy | None:
        with self._db() as db:
            row = db.execute("SELECT * FROM morning_shift_policy WHERE id='default'").fetchone()
        return None if row is None else self._policy_from_row(row)

    def set_shift_policy(self, *, timezone: str, day_shift_start: str, night_shift_start: str) -> ShiftPolicy:
        with self._db() as db:
            row = db.execute(
                """INSERT INTO morning_shift_policy
                       (id, timezone, day_shift_start, night_shift_start, updated_at)
                   VALUES ('default', %s, %s, %s, CURRENT_TIMESTAMP)
                   ON CONFLICT (id) DO UPDATE SET
                       timezone=EXCLUDED.timezone,
                       day_shift_start=EXCLUDED.day_shift_start,
                       night_shift_start=EXCLUDED.night_shift_start,
                       updated_at=CURRENT_TIMESTAMP
                   RETURNING *""",
                (timezone, day_shift_start, night_shift_start),
            ).fetchone()
        return self._policy_from_row(row)

    @staticmethod
    def _policy_from_row(row: dict[str, Any]) -> ShiftPolicy:
        return ShiftPolicy(
            timezone=row["timezone"],
            day_shift_start=_hhmm(row["day_shift_start"]),
            night_shift_start=_hhmm(row["night_shift_start"]),
            updated_at=_iso(row["updated_at"]) or "",
        )

    # -- machines ---------------------------------------------------------

    def create_machine(
        self,
        *,
        machine_id: str,
        machine_type: str | None,
        section: str | None,
        control_room_scope: bool = False,
    ) -> Machine:
        row_id = new_id("machine")
        try:
            with self._db() as db:
                row = db.execute(
                    """INSERT INTO morning_machines
                       (id, machine_id, machine_type, section, active, control_room_scope)
                       VALUES (%s, %s, %s, %s, true, %s)
                       RETURNING *""",
                    (row_id, machine_id, machine_type, section, control_room_scope),
                ).fetchone()
        except UniqueViolation as exc:
            raise MorningError(f"machine_id already exists: {machine_id}") from exc
        return self._machine_from_row(row)

    def update_machine(
        self,
        machine_id_internal: str,
        *,
        machine_id: str | None = None,
        machine_type: str | None = ...,
        section: str | None = ...,
    ) -> Machine:
        current = self.get_machine(machine_id_internal)
        try:
            with self._db() as db:
                db.execute(
                    "UPDATE morning_machines SET machine_id=%s, machine_type=%s, section=%s WHERE id=%s",
                    (
                        machine_id if machine_id is not None else current.machine_id,
                        current.machine_type if machine_type is ... else machine_type,
                        current.section if section is ... else section,
                        machine_id_internal,
                    ),
                )
        except UniqueViolation as exc:
            raise MorningError(f"machine_id already exists: {machine_id}") from exc
        return self.get_machine(machine_id_internal)

    def set_machine_active(self, machine_id_internal: str, *, active: bool) -> Machine:
        self.get_machine(machine_id_internal)
        with self._db() as db:
            if active:
                db.execute(
                    "UPDATE morning_machines SET active=true, retired_at=NULL WHERE id=%s",
                    (machine_id_internal,),
                )
            else:
                db.execute(
                    "UPDATE morning_machines SET active=false, retired_at=CURRENT_TIMESTAMP WHERE id=%s",
                    (machine_id_internal,),
                )
        return self.get_machine(machine_id_internal)

    def set_machine_control_room_scope(self, machine_id_internal: str, *, in_scope: bool) -> Machine:
        self.get_machine(machine_id_internal)
        with self._db() as db:
            db.execute(
                "UPDATE morning_machines SET control_room_scope=%s WHERE id=%s",
                (in_scope, machine_id_internal),
            )
        return self.get_machine(machine_id_internal)

    def get_machine(self, machine_id_internal: str) -> Machine:
        with self._db() as db:
            row = db.execute("SELECT * FROM morning_machines WHERE id=%s", (machine_id_internal,)).fetchone()
        if row is None:
            raise UnknownRecordError(f"unknown machine: {machine_id_internal}")
        return self._machine_from_row(row)

    def list_machines(
        self,
        *,
        active_only: bool = False,
        control_room_scope_only: bool = False,
    ) -> tuple[Machine, ...]:
        clauses: list[str] = []
        if active_only:
            clauses.append("active=true")
        if control_room_scope_only:
            clauses.append("control_room_scope=true")
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._db() as db:
            rows = db.execute(f"SELECT * FROM morning_machines{where} ORDER BY machine_id").fetchall()
        return tuple(self._machine_from_row(row) for row in rows)

    @staticmethod
    def _machine_from_row(row: dict[str, Any]) -> Machine:
        return Machine(
            id=row["id"],
            machine_id=row["machine_id"],
            machine_type=row["machine_type"],
            section=row["section"],
            active=bool(row["active"]),
            created_at=_iso(row["created_at"]) or "",
            retired_at=_iso(row["retired_at"]),
            control_room_scope=bool(row["control_room_scope"]),
        )

    # -- crews ------------------------------------------------------------

    def create_crew(self, *, name: str) -> Crew:
        row_id = new_id("crew")
        with self._db() as db:
            row = db.execute(
                "INSERT INTO morning_crews (id, name) VALUES (%s, %s) RETURNING *",
                (row_id, name),
            ).fetchone()
        return self._crew_from_row(row)

    def update_crew(self, crew_id: str, *, name: str | None = None) -> Crew:
        current = self.get_crew(crew_id)
        with self._db() as db:
            db.execute(
                "UPDATE morning_crews SET name=%s WHERE id=%s",
                (name if name is not None else current.name, crew_id),
            )
        return self.get_crew(crew_id)

    def get_crew(self, crew_id: str) -> Crew:
        with self._db() as db:
            row = db.execute("SELECT * FROM morning_crews WHERE id=%s", (crew_id,)).fetchone()
        if row is None:
            raise UnknownRecordError(f"unknown crew: {crew_id}")
        return self._crew_from_row(row)

    def list_crews(self) -> tuple[Crew, ...]:
        with self._db() as db:
            rows = db.execute("SELECT * FROM morning_crews ORDER BY name").fetchall()
        return tuple(self._crew_from_row(row) for row in rows)

    @staticmethod
    def _crew_from_row(row: dict[str, Any]) -> Crew:
        return Crew(id=row["id"], name=row["name"], created_at=_iso(row["created_at"]) or "")

    # -- personnel --------------------------------------------------------

    def create_person(
        self,
        *,
        name: str,
        employee_number: str | None,
        role: str | None,
        crew_id: str | None,
    ) -> Person:
        row_id = new_id("person")
        try:
            with self._db() as db:
                row = db.execute(
                    """INSERT INTO morning_persons (id, name, employee_number, role, active, crew_id)
                       VALUES (%s, %s, %s, %s, true, %s) RETURNING *""",
                    (row_id, name, employee_number, role, crew_id),
                ).fetchone()
        except ForeignKeyViolation as exc:
            raise UnknownRecordError(f"unknown crew: {crew_id}") from exc
        return self._person_from_row(row)

    def update_person(
        self,
        person_id: str,
        *,
        name: str | None = None,
        employee_number: str | None = ...,
        role: str | None = ...,
        crew_id: str | None = ...,
    ) -> Person:
        current = self.get_person(person_id)
        try:
            with self._db() as db:
                db.execute(
                    "UPDATE morning_persons SET name=%s, employee_number=%s, role=%s, crew_id=%s WHERE id=%s",
                    (
                        name if name is not None else current.name,
                        current.employee_number if employee_number is ... else employee_number,
                        current.role if role is ... else role,
                        current.crew_id if crew_id is ... else crew_id,
                        person_id,
                    ),
                )
        except ForeignKeyViolation as exc:
            raise UnknownRecordError(f"unknown crew: {crew_id}") from exc
        return self.get_person(person_id)

    def set_person_active(self, person_id: str, *, active: bool) -> Person:
        self.get_person(person_id)
        with self._db() as db:
            db.execute("UPDATE morning_persons SET active=%s WHERE id=%s", (active, person_id))
        return self.get_person(person_id)

    def get_person(self, person_id: str) -> Person:
        with self._db() as db:
            row = db.execute("SELECT * FROM morning_persons WHERE id=%s", (person_id,)).fetchone()
        if row is None:
            raise UnknownRecordError(f"unknown person: {person_id}")
        return self._person_from_row(row)

    def list_persons(self, *, active_only: bool = False) -> tuple[Person, ...]:
        where = " WHERE active=true" if active_only else ""
        with self._db() as db:
            rows = db.execute(f"SELECT * FROM morning_persons{where} ORDER BY name").fetchall()
        return tuple(self._person_from_row(row) for row in rows)

    def persons_by_ids(self, person_ids: tuple[str, ...]) -> tuple[Person, ...]:
        if not person_ids:
            return ()
        with self._db() as db:
            rows = db.execute(
                "SELECT * FROM morning_persons WHERE id = ANY(%s) ORDER BY name",
                (list(person_ids),),
            ).fetchall()
        return tuple(self._person_from_row(row) for row in rows)

    def roster_for_crew(self, crew_id: str) -> tuple[Person, ...]:
        with self._db() as db:
            rows = db.execute(
                "SELECT * FROM morning_persons WHERE active=true AND crew_id=%s ORDER BY name",
                (crew_id,),
            ).fetchall()
        return tuple(self._person_from_row(row) for row in rows)

    @staticmethod
    def _person_from_row(row: dict[str, Any]) -> Person:
        return Person(
            id=row["id"],
            name=row["name"],
            employee_number=row["employee_number"],
            role=row["role"],
            active=bool(row["active"]),
            crew_id=row["crew_id"],
            created_at=_iso(row["created_at"]) or "",
        )

    # -- accounts ---------------------------------------------------------

    def create_account(self, *, principal_id: str, username: str, password_hash: str, password_salt: str) -> None:
        try:
            with self._db() as db:
                db.execute(
                    """INSERT INTO morning_accounts (principal_id, username, password_hash, password_salt)
                       VALUES (%s, %s, %s, %s)""",
                    (principal_id, username.strip().casefold(), password_hash, password_salt),
                )
        except UniqueViolation as exc:
            raise MorningError(f"username already registered: {username}") from exc
        except ForeignKeyViolation as exc:
            raise UnknownRecordError(f"unknown principal: {principal_id}") from exc

    def account_by_username(self, username: str) -> dict[str, Any] | None:
        with self._db() as db:
            row = db.execute(
                "SELECT * FROM morning_accounts WHERE username=%s",
                (username.strip().casefold(),),
            ).fetchone()
        return None if row is None else _json_safe_row(row)

    def account_by_principal(self, principal_id: str) -> dict[str, Any] | None:
        with self._db() as db:
            row = db.execute("SELECT * FROM morning_accounts WHERE principal_id=%s", (principal_id,)).fetchone()
        return None if row is None else _json_safe_row(row)

    def approve_account(self, principal_id: str) -> dict[str, Any]:
        with self._db() as db:
            row = db.execute(
                """UPDATE morning_accounts SET approved_at=CURRENT_TIMESTAMP
                   WHERE principal_id=%s RETURNING *""",
                (principal_id,),
            ).fetchone()
        if row is None:
            raise UnknownRecordError(f"unknown morning account: {principal_id}")
        return _json_safe_row(row)

    def link_account_person(self, principal_id: str, person_id: str | None) -> dict[str, Any]:
        if person_id is not None:
            self.get_person(person_id)
        with self._db() as db:
            row = db.execute(
                "UPDATE morning_accounts SET person_id=%s WHERE principal_id=%s RETURNING *",
                (person_id, principal_id),
            ).fetchone()
        if row is None:
            raise UnknownRecordError(f"unknown morning account: {principal_id}")
        return _json_safe_row(row)

    def list_accounts(self, *, pending_only: bool = False) -> tuple[dict[str, Any], ...]:
        where = " WHERE approved_at IS NULL" if pending_only else ""
        with self._db() as db:
            rows = db.execute(f"SELECT * FROM morning_accounts{where} ORDER BY created_at").fetchall()
        return tuple(_json_safe_row(row) for row in rows)

    # -- shift reports ----------------------------------------------------

    def get_or_create_draft(
        self,
        *,
        supervisor_principal_id: str,
        shift_date: str,
        shift_kind: str,
        crew_id: str | None,
    ) -> ShiftReport:
        row_id = new_id("shiftreport")
        try:
            with self._db() as db:
                db.execute(
                    """INSERT INTO morning_reports
                       (id, shift_date, shift_kind, supervisor_principal_id, crew_id, status)
                       VALUES (%s, %s, %s, %s, %s, 'draft')
                       ON CONFLICT (shift_date, shift_kind, supervisor_principal_id)
                       WHERE status <> 'abandoned'
                       DO NOTHING""",
                    (row_id, shift_date, shift_kind, supervisor_principal_id, crew_id),
                )
                row = db.execute(
                    """SELECT id FROM morning_reports
                       WHERE shift_date=%s AND shift_kind=%s AND supervisor_principal_id=%s
                         AND status <> 'abandoned'""",
                    (shift_date, shift_kind, supervisor_principal_id),
                ).fetchone()
        except ForeignKeyViolation as exc:
            raise MorningError("supervisor principal or crew does not exist") from exc
        if row is None:
            raise MorningError("could not create or resolve shift report")
        return self._load_report(row["id"])

    def current_draft(self, supervisor_principal_id: str) -> ShiftReport | None:
        with self._db() as db:
            row = db.execute(
                """SELECT id FROM morning_reports
                   WHERE supervisor_principal_id=%s AND status='draft'
                   ORDER BY updated_at DESC, created_at DESC, id DESC LIMIT 1""",
                (supervisor_principal_id,),
            ).fetchone()
        return None if row is None else self._load_report(row["id"])

    def get_report(self, report_id: str) -> ShiftReport:
        return self._load_report(report_id)

    def list_reports(
        self,
        *,
        shift_date: str | None = None,
        status: str | None = None,
        supervisor_principal_id: str | None = None,
    ) -> tuple[ShiftReport, ...]:
        clauses: list[str] = []
        args: list[Any] = []
        if shift_date is not None:
            clauses.append("shift_date=%s")
            args.append(shift_date)
        if status is not None:
            clauses.append("status=%s")
            args.append(status)
        if supervisor_principal_id is not None:
            clauses.append("supervisor_principal_id=%s")
            args.append(supervisor_principal_id)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._db() as db:
            rows = db.execute(
                f"SELECT id FROM morning_reports{where} ORDER BY shift_date DESC, shift_kind, created_at DESC",
                args,
            ).fetchall()
        return tuple(self._load_report(row["id"]) for row in rows)

    def _require_draft(self, db: Connection[dict[str, Any]], report_id: str) -> dict[str, Any]:
        row = db.execute("SELECT * FROM morning_reports WHERE id=%s FOR UPDATE", (report_id,)).fetchone()
        if row is None:
            raise UnknownRecordError(f"unknown shift report: {report_id}")
        if row["status"] != "draft":
            raise InvalidTransitionError("shift report is already submitted and can no longer be edited")
        return row

    @staticmethod
    def _touch_report(db: Connection[dict[str, Any]], report_id: str) -> None:
        db.execute("UPDATE morning_reports SET updated_at=CURRENT_TIMESTAMP WHERE id=%s", (report_id,))

    def replace_attendance(self, report_id: str, entries: tuple[AttendanceEntry, ...]) -> ShiftReport:
        with self._db() as db:
            self._require_draft(db, report_id)
            db.execute("DELETE FROM morning_attendance WHERE report_id=%s", (report_id,))
            if entries:
                with db.cursor() as cursor:
                    cursor.executemany(
                        "INSERT INTO morning_attendance (report_id, person_id, present) VALUES (%s, %s, %s)",
                        [(report_id, item.person_id, item.present) for item in entries],
                    )
            self._touch_report(db, report_id)
        return self._load_report(report_id)

    def add_stop_fix(self, report_id: str, record: StopFixRecord) -> ShiftReport:
        with self._db() as db:
            self._require_draft(db, report_id)
            db.execute(
                """INSERT INTO morning_stop_fix
                   (id, report_id, number, issued_at, area_of_concern, location, reason, instruction, status, rectified_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    record.id,
                    report_id,
                    record.number,
                    record.issued_at,
                    record.area_of_concern,
                    record.location,
                    record.reason,
                    record.instruction,
                    record.status,
                    record.rectified_at,
                ),
            )
            self._touch_report(db, report_id)
        return self._load_report(report_id)

    def update_stop_fix(self, report_id: str, record: StopFixRecord) -> ShiftReport:
        with self._db() as db:
            self._require_draft(db, report_id)
            cursor = db.execute(
                """UPDATE morning_stop_fix SET number=%s, issued_at=%s, area_of_concern=%s, location=%s,
                   reason=%s, instruction=%s, status=%s, rectified_at=%s
                   WHERE id=%s AND report_id=%s""",
                (
                    record.number,
                    record.issued_at,
                    record.area_of_concern,
                    record.location,
                    record.reason,
                    record.instruction,
                    record.status,
                    record.rectified_at,
                    record.id,
                    report_id,
                ),
            )
            if cursor.rowcount == 0:
                raise UnknownRecordError(f"unknown stop & fix record: {record.id}")
            self._touch_report(db, report_id)
        return self._load_report(report_id)

    def delete_stop_fix(self, report_id: str, stop_fix_id: str) -> ShiftReport:
        with self._db() as db:
            self._require_draft(db, report_id)
            db.execute("DELETE FROM morning_stop_fix WHERE id=%s AND report_id=%s", (stop_fix_id, report_id))
            self._touch_report(db, report_id)
        return self._load_report(report_id)

    def add_card(self, report_id: str, record: CardObservation) -> ShiftReport:
        with self._db() as db:
            self._require_draft(db, report_id)
            db.execute(
                "INSERT INTO morning_cards (id, report_id, card_type, reason) VALUES (%s, %s, %s, %s)",
                (record.id, report_id, record.card_type, record.reason),
            )
            self._touch_report(db, report_id)
        return self._load_report(report_id)

    def delete_card(self, report_id: str, card_id: str) -> ShiftReport:
        with self._db() as db:
            self._require_draft(db, report_id)
            db.execute("DELETE FROM morning_cards WHERE id=%s AND report_id=%s", (card_id, report_id))
            self._touch_report(db, report_id)
        return self._load_report(report_id)

    def add_machine_event(self, report_id: str, record: MachineEvent) -> ShiftReport:
        with self._db() as db:
            self._require_draft(db, report_id)
            db.execute(
                """INSERT INTO morning_machine_events (id, report_id, machine_id, start_time, end_time, issue)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (record.id, report_id, record.machine_id, record.start_time, record.end_time, record.issue),
            )
            self._touch_report(db, report_id)
        return self._load_report(report_id)

    def update_machine_event(self, report_id: str, record: MachineEvent) -> ShiftReport:
        with self._db() as db:
            self._require_draft(db, report_id)
            cursor = db.execute(
                """UPDATE morning_machine_events SET machine_id=%s, start_time=%s, end_time=%s, issue=%s
                   WHERE id=%s AND report_id=%s""",
                (record.machine_id, record.start_time, record.end_time, record.issue, record.id, report_id),
            )
            if cursor.rowcount == 0:
                raise UnknownRecordError(f"unknown machine event: {record.id}")
            self._touch_report(db, report_id)
        return self._load_report(report_id)

    def delete_machine_event(self, report_id: str, event_id: str) -> ShiftReport:
        with self._db() as db:
            self._require_draft(db, report_id)
            db.execute("DELETE FROM morning_machine_events WHERE id=%s AND report_id=%s", (event_id, report_id))
            self._touch_report(db, report_id)
        return self._load_report(report_id)

    def add_other_activity(self, report_id: str, record: OtherActivity) -> ShiftReport:
        with self._db() as db:
            self._require_draft(db, report_id)
            db.execute(
                "INSERT INTO morning_other_activities (id, report_id, category, description) VALUES (%s, %s, %s, %s)",
                (record.id, report_id, record.category, record.description),
            )
            self._touch_report(db, report_id)
        return self._load_report(report_id)

    def delete_other_activity(self, report_id: str, activity_id: str) -> ShiftReport:
        with self._db() as db:
            self._require_draft(db, report_id)
            db.execute(
                "DELETE FROM morning_other_activities WHERE id=%s AND report_id=%s",
                (activity_id, report_id),
            )
            self._touch_report(db, report_id)
        return self._load_report(report_id)

    def submit_report(self, report_id: str) -> ShiftReport:
        with self._db() as db:
            self._require_draft(db, report_id)
            db.execute(
                """UPDATE morning_reports SET status='submitted', submitted_at=CURRENT_TIMESTAMP,
                   updated_at=CURRENT_TIMESTAMP WHERE id=%s""",
                (report_id,),
            )
        return self._load_report(report_id)

    def abandon_report(self, report_id: str) -> ShiftReport:
        with self._db() as db:
            self._require_draft(db, report_id)
            db.execute(
                "UPDATE morning_reports SET status='abandoned', updated_at=CURRENT_TIMESTAMP WHERE id=%s",
                (report_id,),
            )
        return self._load_report(report_id)

    def _load_report(self, report_id: str) -> ShiftReport:
        with self._db() as db:
            row = db.execute("SELECT * FROM morning_reports WHERE id=%s", (report_id,)).fetchone()
            if row is None:
                raise UnknownRecordError(f"unknown shift report: {report_id}")
            attendance_rows = db.execute(
                "SELECT * FROM morning_attendance WHERE report_id=%s ORDER BY person_id",
                (report_id,),
            ).fetchall()
            stop_fix_rows = db.execute(
                "SELECT * FROM morning_stop_fix WHERE report_id=%s ORDER BY issued_at, id",
                (report_id,),
            ).fetchall()
            card_rows = db.execute(
                "SELECT * FROM morning_cards WHERE report_id=%s ORDER BY created_at, id",
                (report_id,),
            ).fetchall()
            machine_event_rows = db.execute(
                "SELECT * FROM morning_machine_events WHERE report_id=%s ORDER BY start_time, id",
                (report_id,),
            ).fetchall()
            other_rows = db.execute(
                "SELECT * FROM morning_other_activities WHERE report_id=%s ORDER BY created_at, id",
                (report_id,),
            ).fetchall()

        attendance = tuple(
            AttendanceEntry(person_id=item["person_id"], present=bool(item["present"])) for item in attendance_rows
        )
        stop_fix = tuple(
            StopFixRecord(
                id=item["id"],
                number=item["number"],
                issued_at=_iso(item["issued_at"]) or "",
                area_of_concern=item["area_of_concern"],
                location=item["location"],
                reason=item["reason"],
                instruction=item["instruction"],
                status=item["status"],
                rectified_at=_iso(item["rectified_at"]),
            )
            for item in stop_fix_rows
        )
        cards = tuple(
            CardObservation(id=item["id"], card_type=item["card_type"], reason=item["reason"])
            for item in card_rows
        )
        machine_events = tuple(
            MachineEvent(
                id=item["id"],
                machine_id=item["machine_id"],
                start_time=_iso(item["start_time"]) or "",
                end_time=_iso(item["end_time"]) or "",
                issue=item["issue"],
            )
            for item in machine_event_rows
        )
        other_activities = tuple(
            OtherActivity(id=item["id"], category=item["category"], description=item["description"])
            for item in other_rows
        )
        return ShiftReport(
            id=row["id"],
            shift_date=_iso(row["shift_date"]) or "",
            shift_kind=row["shift_kind"],
            supervisor_principal_id=row["supervisor_principal_id"],
            crew_id=row["crew_id"],
            status=row["status"],
            attendance=attendance,
            stop_fix=stop_fix,
            cards=cards,
            machine_events=machine_events,
            other_activities=other_activities,
            created_at=_iso(row["created_at"]) or "",
            updated_at=_iso(row["updated_at"]) or "",
            submitted_at=_iso(row["submitted_at"]),
        )

    # -- machine state ----------------------------------------------------

    def add_machine_state(self, declaration: MachineStateDeclaration) -> MachineStateDeclaration:
        try:
            with self._db() as db:
                row = db.execute(
                    """INSERT INTO morning_machine_state_declarations
                       (id, machine_id, report_id, declared_at, state, state_note, provenance,
                        source_state_id, follow_up)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                       RETURNING *""",
                    (
                        declaration.id,
                        declaration.machine_id,
                        declaration.report_id,
                        declaration.declared_at,
                        declaration.state,
                        declaration.state_note,
                        declaration.provenance,
                        declaration.source_state_id,
                        declaration.follow_up,
                    ),
                ).fetchone()
        except ForeignKeyViolation as exc:
            raise MorningError("machine-state declaration references an unknown source record") from exc
        except psycopg.errors.CheckViolation as exc:
            raise MorningError("invalid machine-state declaration") from exc
        return self._machine_state_from_row(row)

    def list_machine_states(
        self,
        *,
        machine_id: str | None = None,
        report_id: str | None = None,
    ) -> tuple[MachineStateDeclaration, ...]:
        clauses: list[str] = []
        args: list[Any] = []
        if machine_id is not None:
            clauses.append("machine_id=%s")
            args.append(machine_id)
        if report_id is not None:
            clauses.append("report_id=%s")
            args.append(report_id)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._db() as db:
            rows = db.execute(
                f"""SELECT * FROM morning_machine_state_declarations{where}
                    ORDER BY declared_at, created_at, id""",
                args,
            ).fetchall()
        return tuple(self._machine_state_from_row(row) for row in rows)

    def latest_machine_state(self, machine_id: str) -> MachineStateDeclaration | None:
        with self._db() as db:
            row = db.execute(
                """SELECT * FROM morning_machine_state_declarations
                   WHERE machine_id=%s ORDER BY declared_at DESC, created_at DESC, id DESC LIMIT 1""",
                (machine_id,),
            ).fetchone()
        return None if row is None else self._machine_state_from_row(row)

    @staticmethod
    def _machine_state_from_row(row: dict[str, Any]) -> MachineStateDeclaration:
        return MachineStateDeclaration(
            id=row["id"],
            machine_id=row["machine_id"],
            report_id=row["report_id"],
            declared_at=_iso(row["declared_at"]) or "",
            state=row["state"],
            provenance=row["provenance"],
            state_note=row["state_note"],
            source_state_id=row["source_state_id"],
            follow_up=row["follow_up"],
            created_at=_iso(row["created_at"]),
        )

    # -- control-room observations ---------------------------------------

    def add_observation(self, observation: ControlRoomObservation) -> ControlRoomObservation:
        try:
            with self._db() as db:
                row = db.execute(
                    """INSERT INTO morning_control_room_observations
                       (id, reporting_date, machine_id, raw_machine_label, start_time, end_time, description,
                        source_message_id, source_artifact_id)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                       RETURNING *""",
                    (
                        observation.id,
                        observation.reporting_date,
                        observation.machine_id,
                        observation.raw_machine_label,
                        observation.start_time,
                        observation.end_time,
                        observation.description,
                        observation.source_message_id,
                        observation.source_artifact_id,
                    ),
                ).fetchone()
        except ForeignKeyViolation as exc:
            raise UnknownRecordError(f"unknown machine: {observation.machine_id}") from exc
        return self._observation_from_row(row)

    def list_observations(self, *, reporting_date: str) -> tuple[ControlRoomObservation, ...]:
        with self._db() as db:
            rows = db.execute(
                """SELECT * FROM morning_control_room_observations
                   WHERE reporting_date=%s ORDER BY extracted_at, id""",
                (reporting_date,),
            ).fetchall()
        return tuple(self._observation_from_row(row) for row in rows)

    @staticmethod
    def _observation_from_row(row: dict[str, Any]) -> ControlRoomObservation:
        return ControlRoomObservation(
            id=row["id"],
            reporting_date=_iso(row["reporting_date"]) or "",
            machine_id=row["machine_id"],
            raw_machine_label=row["raw_machine_label"],
            start_time=_iso(row["start_time"]),
            end_time=_iso(row["end_time"]),
            description=row["description"],
            source_message_id=row["source_message_id"],
            source_artifact_id=row["source_artifact_id"],
            extracted_at=_iso(row["extracted_at"]) or "",
        )
