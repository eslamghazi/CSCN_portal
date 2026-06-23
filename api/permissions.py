"""Permission helpers shared by routers: build the permission map sent to the
SPA and a guard for role-gated (not module-gated) pages."""
from fastapi import Depends, HTTPException, status

from api.deps import require_login
from application.dto.user_dto import UserDTO

# Modules covered by the role-permission matrix (mirrors main.PERMISSION_MODULES).
PERMISSION_MODULES = [
    "quality", "documents", "records", "training",
    "hr", "financial", "partnership", "reports", "users",
]
ACTIONS = ("view", "create", "edit", "delete")

# Pages gated purely by role (no module/action row).
SUPERADMIN_ONLY = {"admin", "backup", "remote"}
ADMIN_OR_SUPERADMIN = {"lookups"}


def build_permission_map(permission_service) -> dict:
    """Return {module: {action: bool}} for the current user, for the SPA to gate
    nav items and buttons. superadmin resolves to all-True via the service."""
    return {
        module: {action: permission_service.has_permission(module, action)
                 for action in ACTIONS}
        for module in PERMISSION_MODULES
    }


def require_role(*roles: str):
    """Dependency: allow only the given role names (superadmin always allowed)."""
    allowed = set(roles) | {"superadmin"}

    def _dep(user: UserDTO = Depends(require_login)) -> UserDTO:
        if (user.role_name or "") not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="ليس لديك صلاحية للوصول لهذه الصفحة.")
        return user
    return _dep
