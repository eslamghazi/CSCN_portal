"""FastAPI dependencies: per-request DB session, per-request services, and the
current-user / permission guards."""
from typing import Optional

from fastapi import Depends, Request, HTTPException, status

from database.session import db_session as _scoped_session
from application.dto.user_dto import UserDTO
from api.service_factory import build_request_services


def get_db():
    """Yield a request-scoped SQLAlchemy session. ``remove()`` (not ``close()``)
    clears the thread-local scoped registry so no identity map leaks into the
    next request handled by the same worker thread."""
    db = _scoped_session()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        _scoped_session.remove()


def get_services(db=Depends(get_db)) -> dict:
    """Build the services dict bound to this request's session."""
    return build_request_services(db)


def load_current_user(request: Request) -> Optional[UserDTO]:
    """Return the current user resolved by CurrentUserMiddleware (which also set
    the per-request contextvar so AuditService/DocumentService attribute the
    correct user). Returns None when not logged in."""
    return request.scope.get("state", {}).get("current_user")


def require_login(user: Optional[UserDTO] = Depends(load_current_user)) -> UserDTO:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="يجب تسجيل الدخول.")
    return user


def require_perm(module: str, action: str):
    """Dependency factory enforcing a module/action permission. superadmin is
    always allowed (handled inside PermissionService)."""
    def _dep(user: UserDTO = Depends(require_login),
             services: dict = Depends(get_services)) -> UserDTO:
        if not services["permission"].has_permission(module, action):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="ليس لديك صلاحية لهذا الإجراء.")
        return user
    return _dep
