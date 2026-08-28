from __future__ import annotations

import re
from dataclasses import dataclass

from .aggregate import ReportBundle, SafetySummary

# Real Teams workbook cell mapping retained from the established Morning
# implementation. This module is a deterministic projection only: it never
# becomes canonical storage.
STOP_FIX_ROWS: tuple[int, ...] = tuple(range(36, 47))
STOP_FIX_COLUMN = "A"
ENGINEERING_HSE_ROW = 52
ENGINEERING_HSE_COLUMN = "A"


@dataclass(frozen=True)
class TeamsMachineSlot:
    machine_id: str
    group: str
    row: int
    remark_column: str
    duration_column: str


TEAMS_MACHINE_SLOTS: tuple[TeamsMachineSlot, ...] = (
    TeamsMachineSlot("ARB04", "Primary Dev", 100, "B", "D"),
    TeamsMachineSlot("ARB05", "Primary Dev", 101, "B", "D"),
    TeamsMachineSlot("ADR13", "Primary Dev", 102, "B", "D"),
    TeamsMachineSlot("ADR14", "Primary Dev", 103, "B", "D"),
    TeamsMachineSlot("TRBL02", "Primary Dev", 104, "B", "D"),
    TeamsMachineSlot("TRBL03", "Primary Dev", 105, "B", "D"),
    TeamsMachineSlot("TRBL04", "Primary Dev", 106, "B", "D"),
    TeamsMachineSlot("TDR08", "Primary Dev", 107, "B", "D"),
    TeamsMachineSlot("TDR09", "Primary Dev", 108, "B", "D"),
    TeamsMachineSlot("TDR10", "Primary Dev", 109, "B", "D"),
    TeamsMachineSlot("SECL01", "Primary Dev", 110, "B", "D"),
    TeamsMachineSlot("SEC03", "Primary Dev", 111, "B", "D"),
    TeamsMachineSlot("SEC05", "Primary Dev", 112, "B", "D"),
    TeamsMachineSlot("RLH01", "Primary Dev", 113, "B", "D"),
    TeamsMachineSlot("RLH03", "Primary Dev", 114, "B", "D"),
    TeamsMachineSlot("RLH05", "Primary Dev", 115, "B", "D"),
    TeamsMachineSlot("NSC02", "Primary Dev", 116, "B", "D"),
    TeamsMachineSlot("NVM01", "Primary Dev", 117, "B", "D"),
    TeamsMachineSlot("ASR03", "Primary Dev", 118, "B", "D"),
    TeamsMachineSlot("ROCKY Nr.2", "Primary Dev", 120, "B", "D"),
    TeamsMachineSlot("ROCKY Nr.5", "Primary Dev", 121, "B", "D"),
    TeamsMachineSlot("SST12", "Utilities Dev", 100, "F", "H"),
    TeamsMachineSlot("SST15", "Utilities Dev", 101, "F", "H"),
    TeamsMachineSlot("SST16", "Utilities Dev", 102, "F", "H"),
    TeamsMachineSlot("SST17", "Utilities Dev", 103, "F", "H"),
    TeamsMachineSlot("SST19", "Utilities Dev", 104, "F", "H"),
    TeamsMachineSlot("SST20", "Utilities Dev", 105, "F", "H"),
    TeamsMachineSlot("SST21", "Utilities Dev", 106, "F", "H"),
    TeamsMachineSlot("SST22", "Utilities Dev", 107, "F", "H"),
    TeamsMachineSlot("DT4-01", "Utilities Dev", 108, "F", "H"),
    TeamsMachineSlot("DT4-02", "Utilities Dev", 109, "F", "H"),
    TeamsMachineSlot("DT3-01", "Utilities Dev", 110, "F", "H"),
    TeamsMachineSlot("L91", "Utilities Dev", 111, "F", "H"),
    TeamsMachineSlot("L95", "Utilities Dev", 112, "F", "H"),
    TeamsMachineSlot("L96", "Utilities Dev", 113, "F", "H"),
    TeamsMachineSlot("L97", "Utilities Dev", 114, "F", "H"),
    TeamsMachineSlot("L102E", "Utilities Dev", 115, "F", "H"),
    TeamsMachineSlot("L105", "Utilities Dev", 116, "F", "H"),
    TeamsMachineSlot("LWT02", "Utilities Dev", 117, "F", "H"),
    TeamsMachineSlot("ET01", "Utilities Dev", 118, "F", "H"),
    TeamsMachineSlot("ROCKY Nr.3", "Utilities Dev", 120, "F", "H"),
    TeamsMachineSlot("ROCKY Nr.6", "Utilities Dev", 121, "F", "H"),
    TeamsMachineSlot("BSL01", "LHD's", 100, "J", "L"),
    TeamsMachineSlot("BSL02", "LHD's", 101, "J", "L"),
    TeamsMachineSlot("C13-29", "LHD's", 102, "J", "L"),
    TeamsMachineSlot("C13-30", "LHD's", 103, "J", "L"),
    TeamsMachineSlot("C13-35", "LHD's", 104, "J", "L"),
    TeamsMachineSlot("C13-36", "LHD's", 105, "J", "L"),
    TeamsMachineSlot("C16-07", "LHD's", 106, "J", "L"),
    TeamsMachineSlot("C16-15", "LHD's", 107, "J", "L"),
    TeamsMachineSlot("C16-17", "LHD's", 108, "J", "L"),
    TeamsMachineSlot("C16-19", "LHD's", 109, "J", "L"),
    TeamsMachineSlot("C16-26", "LHD's", 110, "J", "L"),
    TeamsMachineSlot("STC 09", "LHD's", 111, "J", "L"),
    TeamsMachineSlot("STC 12", "LHD's", 112, "J", "L"),
    TeamsMachineSlot("STC13", "LHD's", 113, "J", "L"),
    TeamsMachineSlot("STC14", "LHD's", 114, "J", "L"),
    TeamsMachineSlot("STC15", "LHD's", 115, "J", "L"),
    TeamsMachineSlot("SLV02", "LHD's", 116, "J", "L"),
    TeamsMachineSlot("STV06", "LHD's", 117, "J", "L"),
    TeamsMachineSlot("STV GT01", "LHD's", 118, "J", "L"),
    TeamsMachineSlot("ROCKY Nr.4", "LHD's", 120, "J", "L"),
    TeamsMachineSlot("ROCKY Nr.7", "LHD's", 121, "J", "L"),
)

_NO_ISSUE_REMARK = "1"


def _normalize_code(label: str) -> str:
    return re.sub(r"[\s\-]+", "", label).upper()


@dataclass(frozen=True)
class TeamsCellValue:
    cell: str
    value: str

    def as_dict(self) -> dict[str, str]:
        return {"cell": self.cell, "value": self.value}


@dataclass(frozen=True)
class TeamsWorkbookProjection:
    stop_fix_cells: tuple[TeamsCellValue, ...]
    stop_fix_overflow_count: int
    engineering_hse_cell: TeamsCellValue
    machine_cells: tuple[TeamsCellValue, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "stop_fix_cells": [cell.as_dict() for cell in self.stop_fix_cells],
            "stop_fix_overflow_count": self.stop_fix_overflow_count,
            "engineering_hse_cell": self.engineering_hse_cell.as_dict(),
            "machine_cells": [cell.as_dict() for cell in self.machine_cells],
        }


def _stop_fix_cells(safety: SafetySummary) -> tuple[tuple[TeamsCellValue, ...], int]:
    records = safety.stop_fix_records
    fitted = records[: len(STOP_FIX_ROWS)]
    overflow = records[len(STOP_FIX_ROWS) :]
    cells = tuple(
        TeamsCellValue(
            cell=f"{STOP_FIX_COLUMN}{row}",
            value=(
                f"#{record.number} {record.location} {record.reason} "
                f"({'Closed' if record.status == 'rectified' else 'Pending'})"
            ),
        )
        for row, record in zip(STOP_FIX_ROWS, fitted)
    )
    return cells, len(overflow)


def _engineering_hse_cell(safety: SafetySummary) -> TeamsCellValue:
    green = [reason for card_type, reason in safety.card_reasons if card_type == "green"]
    red = [reason for card_type, reason in safety.card_reasons if card_type == "red"]
    parts: list[str] = []
    if green:
        parts.append(f"{len(green)}x Green card - " + "; ".join(green))
    if red:
        parts.append(f"{len(red)}x Red card - " + "; ".join(red))
    body = ". ".join(parts) if parts else "None"
    return TeamsCellValue(cell=f"{ENGINEERING_HSE_COLUMN}{ENGINEERING_HSE_ROW}", value=f"Engineering: {body}")


def _machine_cells(bundle: ReportBundle) -> tuple[TeamsCellValue, ...]:
    aggregates_by_code = {
        _normalize_code(aggregate.machine_display_id): aggregate
        for aggregate in bundle.machine_aggregates
        if aggregate.matched
    }
    cells: list[TeamsCellValue] = []
    for slot in TEAMS_MACHINE_SLOTS:
        aggregate = aggregates_by_code.get(_normalize_code(slot.machine_id))
        if aggregate is None:
            remark = _NO_ISSUE_REMARK
            delay_seconds = 0.0
        else:
            remark = "; ".join(aggregate.key_issues) if aggregate.key_issues else _NO_ISSUE_REMARK
            # The duration cell belongs to the Production Delays workbook.
            # Only control-room delay intervals feed it. Engineering work time
            # is intentionally never relabelled as downtime/delay here.
            delay_seconds = aggregate.total_control_room_delay_seconds
        cells.append(TeamsCellValue(cell=f"{slot.remark_column}{slot.row}", value=remark))
        if delay_seconds > 0:
            cells.append(
                TeamsCellValue(
                    cell=f"{slot.duration_column}{slot.row}",
                    value=f"{delay_seconds / 86400:.6f}",
                )
            )
    return tuple(cells)


def render_teams_workbook_projection(bundle: ReportBundle) -> TeamsWorkbookProjection:
    """Map canonical Morning data onto the established Teams workbook.

    Remarks can include both supervisor and control-room evidence. Duration
    cells are sourced only from control-room Production Delays intervals so
    the projection cannot regress to the old semantic error where an
    engineering work interval was labelled as machine downtime.
    """

    stop_fix_cells, overflow_count = _stop_fix_cells(bundle.safety)
    return TeamsWorkbookProjection(
        stop_fix_cells=stop_fix_cells,
        stop_fix_overflow_count=overflow_count,
        engineering_hse_cell=_engineering_hse_cell(bundle.safety),
        machine_cells=_machine_cells(bundle),
    )
