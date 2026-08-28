from __future__ import annotations

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from .config import Settings


async def healthz(request: Request) -> JSONResponse:
    settings: Settings = request.app.state.settings
    return JSONResponse(
        {
            "status": "ok",
            "service": "morning",
            "environment": settings.environment,
        }
    )


def create_app(settings: Settings | None = None) -> Starlette:
    resolved = settings or Settings.from_env()
    application = Starlette(routes=[Route("/healthz", healthz, methods=["GET"])])
    application.state.settings = resolved
    return application


app = create_app()
