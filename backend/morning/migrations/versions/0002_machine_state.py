from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002_machine_state"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "morning_machine_state_declarations",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("machine_id", sa.Text(), sa.ForeignKey("morning_machines.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("report_id", sa.Text(), sa.ForeignKey("morning_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("declared_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("state_note", sa.Text()),
        sa.Column("provenance", sa.Text(), nullable=False, server_default=sa.text("'declared'")),
        sa.Column(
            "source_state_id",
            sa.Text(),
            sa.ForeignKey("morning_machine_state_declarations.id", ondelete="RESTRICT"),
        ),
        sa.Column("follow_up", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint(
            "state IN ('running','not_tested','under_repair','awaiting_parts','other')",
            name="ck_morning_machine_state_value",
        ),
        sa.CheckConstraint(
            "provenance IN ('declared','carried')",
            name="ck_morning_machine_state_provenance",
        ),
        sa.CheckConstraint(
            "state <> 'other' OR (state_note IS NOT NULL AND length(btrim(state_note)) > 0)",
            name="ck_morning_machine_state_other_note",
        ),
        sa.CheckConstraint(
            "(provenance = 'declared' AND source_state_id IS NULL) OR "
            "(provenance = 'carried' AND source_state_id IS NOT NULL)",
            name="ck_morning_machine_state_source",
        ),
    )
    op.create_index(
        "ix_morning_machine_state_machine_time",
        "morning_machine_state_declarations",
        ["machine_id", "declared_at"],
    )
    op.create_index(
        "ix_morning_machine_state_report",
        "morning_machine_state_declarations",
        ["report_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_morning_machine_state_report", table_name="morning_machine_state_declarations")
    op.drop_index("ix_morning_machine_state_machine_time", table_name="morning_machine_state_declarations")
    op.drop_table("morning_machine_state_declarations")
