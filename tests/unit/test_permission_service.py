from domain.entities.user import Role, RolePermission
from application.services.permission_service import PermissionService
from application.services.auth_service import AuthService
from application.dto.user_dto import UserDTO


def _login(role_id, role_name):
    AuthService._current_user = UserDTO(
        id=1, username="u", full_name="U", role_id=role_id, role_name=role_name, is_active=True
    )


def test_superadmin_allowed_by_name(db_session):
    svc = PermissionService(db_session, AuthService(None))
    _login(99, "superadmin")
    assert svc.has_permission("users", "create") is True


def test_user_denied_when_permission_disabled(db_session):
    role = Role(name="user")
    db_session.add(role)
    db_session.commit()
    db_session.add(RolePermission(role_id=role.id, module="users", action="create", allowed=False))
    db_session.commit()

    svc = PermissionService(db_session, AuthService(None))
    _login(role.id, "user")
    assert svc.has_permission("users", "create") is False


def test_admin_allowed_when_permission_enabled(db_session):
    role = Role(name="admin")
    db_session.add(role)
    db_session.commit()
    db_session.add(RolePermission(role_id=role.id, module="documents", action="edit", allowed=True))
    db_session.commit()

    svc = PermissionService(db_session, AuthService(None))
    _login(role.id, "admin")
    assert svc.has_permission("documents", "edit") is True


def test_missing_permission_row_denies(db_session):
    role = Role(name="user")
    db_session.add(role)
    db_session.commit()
    svc = PermissionService(db_session, AuthService(None))
    _login(role.id, "user")
    assert svc.has_permission("anything", "delete") is False


def test_anonymous_denied(db_session):
    svc = PermissionService(db_session, AuthService(None))
    AuthService._current_user = None
    assert svc.has_permission("users", "create") is False
