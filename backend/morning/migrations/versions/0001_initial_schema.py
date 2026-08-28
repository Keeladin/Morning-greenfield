from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "morning_shift_policy",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("timezone", sa.Text(), nullable=False),
        sa.Column("day_shift_start", sa.Time(), nullable=False),
        sa.Column("night_shift_start", sa.Time(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("id = 'default'", name="ck_morning_shift_policy_singleton"),
    )

    op.create_table(
        "morning_machines",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("machine_id", sa.Text(), nullable=False),
        sa.Column("machine_type", sa.Text()),
        sa.Column("section", sa.Text()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("retired_at", sa.DateTime(timezone=True)),
        sa.Column("control_room_scope", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("machine_id", name="uq_morning_machines_machine_id"),
    )

    op.create_table(
        "morning_crews",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "morning_persons",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("employee_number", sa.Text()),
        sa.Column("role", sa.Text()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("crew_id", sa.Text(), sa.ForeignKey("morning_crews.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "morning_principals",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'active'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("role IN ('admin','supervisor')", name="ck_morning_principals_role"),
        sa.CheckConstraint("status IN ('active','suspended')", name="ck_morning_principals_status"),
    )

    op.create_table(
        "morning_accounts",
        sa.Column(
            "principal_id",
            sa.Text(),
            sa.ForeignKey("morning_principals.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("password_salt", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("person_id", sa.Text(), sa.ForeignKey("morning_persons.id", ondelete="SET NULL")),
        sa.UniqueConstraint("username", name="uq_morning_accounts_username"),
    )

    op.create_table(
        "morning_reports",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("shift_date", sa.Date(), nullable=False),
        sa.Column("shift_kind", sa.Text(), nullable=False),
        sa.Column(
            "supervisor_principal_id",
            sa.Text(),
            sa.ForeignKey("morning_principals.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("crew_id", sa.Text(), sa.ForeignKey("morning_crews.id", ondelete="SET NULL")),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("shift_kind IN ('day','night')", name="ck_morning_reports_shift_kind"),
        sa.CheckConstraint("status IN ('draft','submitted','abandoned')", name="ck_morning_reports_status"),
    )
    op.create_index("ix_morning_reports_shift", "morning_reports", ["shift_date", "shift_kind"])
    op.create_index(
        "uq_morning_reports_open_slot",
        "morning_reports",
        ["shift_date", "shift_kind", "supervisor_principal_id"],
        unique=True,
        postgresql_where=sa.text("status <> 'abandoned'"),
    )

    op.create_table(
        "morning_attendance",
        sa.Column("report_id", sa.Text(), sa.ForeignKey("morning_reports.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("person_id", sa.Text(), sa.ForeignKey("morning_persons.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("present", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "morning_stop_fix",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("report_id", sa.Text(), sa.ForeignKey("morning_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("number", sa.Text(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("area_of_concern", sa.Text(), nullable=False),
        sa.Column("location", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'open'")),
        sa.Column("rectified_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("status IN ('open','rectified')", name="ck_morning_stop_fix_status"),
    )
    op.create_index("ix_morning_stop_fix_report", "morning_stop_fix", ["report_id"])

    op.create_table(
        "morning_cards",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("report_id", sa.Text(), sa.ForeignKey("morning_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("card_type", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.CheckConstraint("card_type IN ('red','green')", name="ck_morning_cards_type"),
    )
    op.create_index("ix_morning_cards_report", "morning_cards", ["report_id"])

    op.create_table(
        "morning_machine_events",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("report_id", sa.Text(), sa.ForeignKey("morning_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("machine_id", sa.Text(), sa.ForeignKey("morning_machines.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("issue", sa.Text(), nullable=False),
        sa.CheckConstraint("end_time > start_time", name="ck_morning_machine_events_positive_interval"),
    )
    op.create_index("ix_morning_machine_events_report", "morning_machine_events", ["report_id"])
    op.create_index("ix_morning_machine_events_machine", "morning_machine_events", ["machine_id"])

    op.create_table(
        "morning_other_activities",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("report_id", sa.Text(), sa.ForeignKey("morning_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.Text()),
        sa.Column("description", sa.Text(), nullable=False),
    )
    op.create_index("ix_morning_other_activities_report", "morning_other_activities", ["report_id"])

    op.create_table(
        "morning_control_room_observations",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("reporting_date", sa.Date(), nullable=False),
        sa.Column("machine_id", sa.Text(), sa.ForeignKey("morning_machines.id", ondelete="SET NULL")),
        sa.Column("raw_machine_label", sa.Text(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True)),
        sa.Column("end_time", sa.DateTime(timezone=True)),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source_message_id", sa.Text(), nullable=False),
        sa.Column("source_artifact_id", sa.Text()),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint(
            "end_time IS NULL OR start_time IS NULL OR end_time > start_time",
            name="ck_morning_control_room_positive_interval",
        ),
    )
    op.create_index(
        "ix_morning_control_room_reporting_date",
        "morning_control_room_observations",
        ["reporting_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_morning_control_room_reporting_date", table_name="morning_control_room_observations")
    op.drop_table("morning_control_room_observations")
    op.drop_index("ix_morning_other_activities_report", table_name="morning_other_activities")
    op.drop_table("morning_other_activities")
    op.drop_index("ix_morning_machine_events_machine", table_name="morning_machine_events")
    op.drop_index("ix_morning_machine_events_report", table_name="morning_machine_events")
    op.drop_table("morning_machine_events")
    op.drop_index("ix_morning_cards_report", table_name="morning_cards")
    op.drop_table("morning_cards")
    op.drop_index("ix_morning_stop_fix_report", table_name="morning_stop_fix")
    op.drop_table("morning_stop_fix")
    op.drop_table("morning_attendance")
    op.drop_index("uq_morning_reports_open_slot", table_name="morning_reports")
    op.drop_index("ix_morning_reports_shift", table_name="morning_reports")
    op.drop_table("morning_reports")
    op.drop_table("morning_accounts")
    op.drop_table("morning_principals")
    op.drop_table("morning_persons")
    op.drop_table("morning_crews")
    op.drop_table("morning_machines")
    op.drop_table("morning_shift_policy")
