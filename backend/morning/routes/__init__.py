from .admin import routes as admin_routes
from .auth import routes as auth_routes
from .supervisor import routes as supervisor_routes

routes = [*auth_routes, *supervisor_routes, *admin_routes]

__all__ = ["routes"]
