"""Pure-ASGI middleware that resolves the logged-in user once per request and
publishes it to the per-request contextvar.

Why ASGI (not BaseHTTPMiddleware): FastAPI runs sync dependencies and the sync
endpoint in *separate* threadpool threads, and a contextvar set inside one of
them is not visible in the others. A value set here — in the request's async
task, before routing — is copied by anyio into every threadpool child, so the
AuditService/DocumentService/PermissionService calls (which read
AuthService.get_current_user()) all see the correct user. BaseHTTPMiddleware runs
the downstream app in a separate task and would NOT propagate the contextvar.
"""
from starlette.requests import Request

from application.context import set_current_user, clear_current_user


class CurrentUserMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        user = None
        request = Request(scope, receive=receive)
        # scope["session"] is populated by SessionMiddleware, which must wrap this
        # middleware (added AFTER it so it runs first).
        try:
            uid = request.session.get("uid")
        except (AssertionError, KeyError):
            uid = None

        if uid:
            user = self._load_user(uid)

        set_current_user(user)
        scope.setdefault("state", {})["current_user"] = user
        try:
            await self.app(scope, receive, send)
        finally:
            clear_current_user()

    @staticmethod
    def _load_user(uid):
        """Load a plain UserDTO (no ORM session retained) for the contextvar."""
        from database.session import db_session as scoped
        from infrastructure.repositories.user_repository_impl import UserRepositoryImpl
        from application.services.auth_service import AuthService
        db = scoped()
        try:
            return AuthService(UserRepositoryImpl(db)).restore_session(uid)
        except Exception:
            return None
        finally:
            scoped.remove()
