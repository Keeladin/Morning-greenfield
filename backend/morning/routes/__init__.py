from .admin import routes as admin_routes
from .auth import routes as auth_routes
from .export import routes as export_routes
from .supervisor import routes as supervisor_routes

routes = [*auth_routes, *supervisor_routes, *admin_routes, *export_routes]

__all__ = ["routes"]
