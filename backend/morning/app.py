from __future__ import annotations

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from .accounts import MorningAccounts
from .auth import CookiePolicy, MorningSessionService
from .config import Settings
from .routes import routes as morning_routes
from .runtime import MorningRuntime
from .store import MorningStore


async def healthz(request: Request) -> JSONResponse:
    settings: Settings = request.app.state.settings
    return JSONResponse(
        {
            "status": "ok",
            "service": "morning",
            "environment": settings.environment,
            "application_ready": bool(getattr(request.app.state, "morning_runtime", None)),
        }
    )


def create_app(settings: Settings | None = None) -> Starlette:
    resolved = settings or Settings.from_env()
    application_routes = [Route("/healthz", healthz, methods=["GET"])]
    ready = bool(resolved.database_url and resolved.session_secret)
    if ready:
        application_routes.extend(morning_routes)

    application = Starlette(routes=application_routes)
    application.state.settings = resolved

    if ready:
        store = MorningStore(resolved.database_url)
        accounts = MorningAccounts(store)
        auth = MorningSessionService(
            secret=resolved.session_secret,
            cookie_policy=CookiePolicy.for_environment(resolved.environment),
        )
        application.state.morning_store = store
        application.state.morning_accounts = accounts
        application.state.morning_auth = auth
        application.state.morning_runtime = MorningRuntime(store, accounts)
    else:
        application.state.morning_store = None
        application.state.morning_accounts = None
        application.state.morning_auth = None
        application.state.morning_runtime = None

    return application


app = create_app()
