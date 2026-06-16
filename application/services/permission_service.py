from application.services.auth_service import AuthService
from sqlalchemy.orm import Session
from domain.entities.user import RolePermission

class PermissionService:
    def __init__(self, session: Session, auth_service: AuthService):
        self.session = session
        self.auth_service = auth_service
        
    def has_permission(self, module: str, action: str) -> bool:
        """
        Check if the currently logged in user has permission
        to perform `action` on `module`.
        """
        current_user = self.auth_service.get_current_user()
        if not current_user:
            return False

        # The superadmin role always has full access.
        if current_user.role_name == "superadmin":
            return True

        # A user with no assigned role has no permissions.
        if current_user.role_id is None:
            return False

        # Otherwise, query the RolePermission table.
        perm = self.session.query(RolePermission).filter(
            RolePermission.role_id == current_user.role_id,
            RolePermission.module == module,
            RolePermission.action == action
        ).first()

        return perm.allowed if perm else False
