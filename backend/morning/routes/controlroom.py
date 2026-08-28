from __future__ import annotations

import base64
import binascii
import json

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from ..auth import require_admin
from ..controlroom import extract_observations
from ..models import ControlRoomObservation
from ..pdf_text import PdfTextError, extract_pdf_text
from ..store import MorningError, UnknownRecordError, new_id


def _runtime(request: Request):
    return request.app.state.morning_runtime


def _error_status(exc: MorningError) -> int:
    return 404 if isinstance(exc, UnknownRecordError) else 400


async def ingest_control_room(request: Request) -> JSONResponse:
    gate = require_admin(request, mutation=True)
    if isinstance(gate, JSONResponse):
        return gate

    runtime = _runtime(request)
    try:
        body = await request.json() or {}
        reporting_date = str(body.get("reporting_date") or "")
        if len(reporting_date) != 10:
            return JSONResponse({"error": "reporting_date (YYYY-MM-DD) is required"}, status_code=400)

        text = body.get("text")
        if not text and body.get("pdf_base64"):
            try:
                pdf_bytes = base64.b64decode(str(body["pdf_base64"]), validate=True)
                text = extract_pdf_text(pdf_bytes)
            except (binascii.Error, PdfTextError) as exc:
                return JSONResponse({"error": f"could not read control-room PDF: {exc}"}, status_code=400)

        if not text or not str(text).strip():
            return JSONResponse({"error": "text or pdf_base64 is required"}, status_code=400)

        source_message_id = str(body.get("source_message_id") or f"manual_{new_id('upload')}")
        machines = runtime.store.list_machines(control_room_scope_only=True)
        extracted = extract_observations(str(text), machines=machines, reporting_date=reporting_date)
        saved = tuple(
            runtime.store.add_observation(
                ControlRoomObservation(
                    id=new_id("cro"),
                    reporting_date=reporting_date,
                    machine_id=item.machine_id,
                    raw_machine_label=item.raw_machine_label,
                    start_time=item.start_time,
                    end_time=item.end_time,
                    description=item.description,
                    source_message_id=source_message_id,
                    source_artifact_id=None,
                    extracted_at="",
                )
            )
            for item in extracted
        )
    except json.JSONDecodeError:
        return JSONResponse({"error": "invalid json"}, status_code=400)
    except (MorningError, ValueError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=_error_status(exc) if isinstance(exc, MorningError) else 400)

    return JSONResponse({"observations": [observation.as_dict() for observation in saved]}, status_code=201)


async def list_control_room_observations(request: Request) -> JSONResponse:
    gate = require_admin(request)
    if isinstance(gate, JSONResponse):
        return gate
    reporting_date = request.query_params.get("reporting_date") or ""
    if len(reporting_date) != 10:
        return JSONResponse({"error": "reporting_date (YYYY-MM-DD) is required"}, status_code=400)
    observations = _runtime(request).store.list_observations(reporting_date=reporting_date)
    return JSONResponse({"observations": [observation.as_dict() for observation in observations]})


routes = [
    Route("/api/morning/admin/control-room/ingest", ingest_control_room, methods=["POST"]),
    Route("/api/morning/admin/control-room/observations", list_control_room_observations, methods=["GET"]),
]
