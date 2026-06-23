"""Per-request current-user state.

The desktop app stored the logged-in user in a class variable on ``AuthService``
(fine for a single-user app). The web server is multi-user and concurrent, so the
current user must be a *per-request* value or audit attribution would leak between
requests. A ``contextvars.ContextVar`` gives us exactly that: it is local to the
current execution context (request/task/thread), and ``AuthService`` reads it via
its ``get_current_user`` / ``is_authenticated`` helpers.

The desktop code path keeps working: it simply sets and reads the same contextvar.
"""
import contextvars
from typing import Optional

# Holds a UserDTO (or None). ``default=None`` => no user logged in for this context.
_current_user_ctx: "contextvars.ContextVar[Optional[object]]" = contextvars.ContextVar(
    "cscn_current_user", default=None
)


def set_current_user(user) -> None:
    _current_user_ctx.set(user)


def get_current_user_ctx():
    return _current_user_ctx.get()


def clear_current_user() -> None:
    _current_user_ctx.set(None)
