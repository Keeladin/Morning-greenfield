from __future__ import annotations

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from ..auth import require_admin
from ..teams_workbook import render_teams_workbook_projection


def _runtime(request: Request):
    return request.app.state.morning_runtime


async def get_teams_projection(request: Request) -> JSONResponse:
    gate = require_admin(request, mutation=False)
    if isinstance(gate, JSONResponse):
        return gate
    reporting_date = request.path_params["reporting_date"]
    require_control_room = request.query_params.get("require_control_room", "true").lower() not in {"0", "false", "no"}
    bundle = _runtime(request).daily_bundle(reporting_date, require_control_room=require_control_room)
    projection = render_teams_workbook_projection(bundle)
    return JSONResponse(
        {
            "reporting_date": reporting_date,
            "status": bundle.status,
            "expected_inputs": [
                {"key": item.key, "label": item.label, "present": item.present}
                for item in bundle.expected_inputs
            ],
            "teams_projection": projection.as_dict(),
        }
    )


routes = [
    Route("/api/morning/admin/reports/{reporting_date}/teams", get_teams_projection, methods=["GET"]),
]
