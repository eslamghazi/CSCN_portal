"""Verify the application bootstrap (seeding + service wiring) that main() runs,
without launching the Qt GUI."""
from domain.entities.user import Role, User, RolePermission
from application.services.auth_service import AuthService
from application.dto.user_dto import UserDTO
import main as app_main


def test_seed_initial_data_creates_roles_users_and_permissions(db_session):
    app_main.seed_initial_data(db_session)

    assert db_session.query(Role).count() == 3
    assert db_session.query(User).filter(User.username == "superadmin").count() == 1
    # superadmin + admin + user1 + user2
    assert db_session.query(User).count() == 4
    # admin + user rows across all modules and 4 actions each.
    expected = len(app_main.PERMISSION_MODULES) * 4 * 2
    assert db_session.query(RolePermission).count() == expected


def test_seed_initial_data_is_idempotent(db_session):
    app_main.seed_initial_data(db_session)
    app_main.seed_initial_data(db_session)  # second run must be a no-op
    assert db_session.query(Role).count() == 3
    assert db_session.query(User).count() == 4


def test_build_services_returns_all_expected_services(db_session):
    app_main.seed_initial_data(db_session)
    services = app_main.build_services(db_session)
    for key in ["auth", "audit", "quality", "document", "hr", "training",
                "financial", "partnership", "report", "record", "permission"]:
        assert key in services and services[key] is not None


def test_seeded_permissions_enforce_admin_vs_user(db_session):
    app_main.seed_initial_data(db_session)
    services = app_main.build_services(db_session)
    perm = services["permission"]

    admin_role = db_session.query(Role).filter(Role.name == "admin").one()
    user_role = db_session.query(Role).filter(Role.name == "user").one()

    AuthService._current_user = UserDTO(
        id=1, username="a", full_name="A", role_id=admin_role.id, role_name="admin", is_active=True)
    assert perm.has_permission("users", "create") is True

    AuthService._current_user = UserDTO(
        id=2, username="u", full_name="U", role_id=user_role.id, role_name="user", is_active=True)
    assert perm.has_permission("users", "create") is False
    assert perm.has_permission("documents", "view") is True


def test_reconcile_blocks_user_from_restricted_pages(db_session):
    app_main.seed_initial_data(db_session)
    app_main.reconcile_permissions(db_session)
    services = app_main.build_services(db_session)
    perm = services["permission"]

    user_role = db_session.query(Role).filter(Role.name == "user").one()
    AuthService._current_user = UserDTO(
        id=3, username="u", full_name="U", role_id=user_role.id, role_name="user", is_active=True)

    # Entry pages: data-entry users can view + add + edit, but never delete.
    for module in ("documents", "records", "training"):
        assert perm.has_permission(module, "view") is True, module
        assert perm.has_permission(module, "create") is True, module
        assert perm.has_permission(module, "edit") is True, module
        assert perm.has_permission(module, "delete") is False, module
    # Restricted pages: not even viewable.
    for module in ("financial", "hr", "reports", "quality", "partnership"):
        assert perm.has_permission(module, "view") is False, module
        assert perm.has_permission(module, "create") is False, module
