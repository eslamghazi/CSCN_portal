import sys

from ui.app import CSCN_portalApp
from ui.main_window import MainWindow
from config.logging_config import setup_logging
from database.session import db_session as scoped_db_session
from infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from application.services.auth_service import AuthService

# Modules covered by the role-permission matrix. superadmin is granted everything
# by role name in PermissionService, so only admin and user get explicit rows.
PERMISSION_MODULES = [
    "quality", "documents", "records", "training",
    "hr", "financial", "partnership", "reports", "users",
]

# Normal-"user" policy (enforced every startup via reconcile_permissions, so it
# applies to existing DBs too):
#   - DENIED view entirely: these pages are hidden.
#   - ENTRY modules: the data-entry pages a user CAN view AND add/edit on.
#   - Delete is never granted to a normal user (admin/superadmin only).
USER_DENIED_VIEW = {"quality", "hr", "financial", "partnership", "reports", "users"}
USER_ENTRY_MODULES = {"documents", "records", "training"}


def _user_allows(module: str, action: str) -> bool:
    if action == "view":
        return module not in USER_DENIED_VIEW
    if action == "delete":
        return False
    # create / edit
    return module in USER_ENTRY_MODULES


def reconcile_permissions(db_session) -> None:
    """Enforce the current 'user' role policy on startup (updates existing DBs):
    data-entry users can view/add/edit their pages but never delete, and cannot
    see restricted pages."""
    from domain.entities.user import Role, RolePermission
    user_role = db_session.query(Role).filter(Role.name == "user").first()
    if not user_role:
        return
    changed = False
    for module in PERMISSION_MODULES:
        for action in ("view", "create", "edit", "delete"):
            allowed = _user_allows(module, action)
            perm = (db_session.query(RolePermission)
                    .filter(RolePermission.role_id == user_role.id,
                            RolePermission.module == module,
                            RolePermission.action == action).first())
            if perm is None:
                db_session.add(RolePermission(
                    role_id=user_role.id, module=module, action=action, allowed=allowed))
                changed = True
            elif perm.allowed != allowed:
                perm.allowed = allowed
                changed = True
    if changed:
        db_session.commit()


# Default accounts created automatically in the database (no external file). These
# are fixed, known credentials baked in at creation time. The superadmin password
# can be overridden via the CSCN_portal_SUPERADMIN_PASSWORD env var.
# (username, full_name, role, default_password)
DEFAULT_ACCOUNTS = [
    ("superadmin", "مدير النظام", "superadmin", "superadmin123"),
    ("admin", "مدير المركز", "admin", "admin123"),
    ("user1", "مستخدم 1", "user", "user123"),
    ("user2", "مستخدم 2", "user", "user123"),
]


def _default_password(username: str, fallback: str) -> str:
    import os
    if username == "superadmin":
        return os.environ.get("CSCN_portal_SUPERADMIN_PASSWORD") or fallback
    return fallback


def ensure_default_accounts(db_session) -> None:
    """Idempotently guarantee the default roles and accounts exist in the DATABASE,
    creating any that are missing (e.g. on first creation or after an accidental
    wipe). Runs on EVERY startup so the portal can never end up with zero login
    accounts. Uses the fixed default passwords in DEFAULT_ACCOUNTS — no external
    credentials file is written."""
    import bcrypt
    from loguru import logger
    from domain.entities.user import Role, User, RolePermission

    def _hash(pw: str) -> str:
        return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

    # Roles (get-or-create by name).
    role_defs = {
        "superadmin": "صلاحيات كاملة لإدارة النظام",
        "admin": "صلاحيات إدارة المستخدمين والمحتوى",
        "user": "مستخدم عادي",
    }
    roles = {}
    created_role = False
    for name, desc in role_defs.items():
        role = db_session.query(Role).filter(Role.name == name).first()
        if not role:
            role = Role(name=name, description=desc)
            db_session.add(role)
            created_role = True
        roles[name] = role
    if created_role:
        db_session.commit()

    # Default accounts (get-or-create by username) with fixed default passwords.
    created = []
    for username, full_name, role_name, default_pw in DEFAULT_ACCOUNTS:
        if db_session.query(User).filter(User.username == username).first():
            continue
        password = _default_password(username, default_pw)
        db_session.add(User(
            username=username, password_hash=_hash(password),
            full_name=full_name, role_id=roles[role_name].id, is_active=True))
        created.append(username)
    if created:
        db_session.commit()
        # Make sure the admin role has its permission rows (the 'user' role is
        # handled by reconcile_permissions; superadmin is allowed by name).
        admin_role = roles["admin"]
        content_modules = {m for m in PERMISSION_MODULES if m != "users"}
        for module in PERMISSION_MODULES:
            for action in ("view", "create", "edit", "delete"):
                exists = (db_session.query(RolePermission)
                          .filter(RolePermission.role_id == admin_role.id,
                                  RolePermission.module == module,
                                  RolePermission.action == action).first())
                if not exists:
                    allowed = True if action != "delete" else (module in content_modules)
                    db_session.add(RolePermission(role_id=admin_role.id, module=module,
                                                  action=action, allowed=allowed))
        db_session.commit()
        logger.info("Auto-created {} default account(s) in the database: {}",
                    len(created), ", ".join(created))


def seed_initial_data(db_session) -> None:
    """Seed roles, the superadmin user, and the role-permission matrix on a fresh
    database. No-op once an admin user already exists."""
    user_repo = UserRepositoryImpl(db_session)
    if user_repo.has_admin_user():
        return

    from domain.entities.user import Role, RolePermission

    # 1./2. Roles + default accounts (fixed default passwords, baked into the DB —
    # no external credentials file). This is the single source of account creation.
    ensure_default_accounts(db_session)

    # 3. Regular-"user" role permission matrix (admin perms are set inside
    # ensure_default_accounts; superadmin is allowed by name).
    user_role = db_session.query(Role).filter(Role.name == "user").first()
    perms = []
    for module in PERMISSION_MODULES:
        perms.append(RolePermission(
            role_id=user_role.id, module=module, action="view",
            allowed=module not in USER_DENIED_VIEW))
        for action in ("create", "edit", "delete"):
            perms.append(RolePermission(role_id=user_role.id, module=module, action=action, allowed=False))
    db_session.add_all(perms)
    db_session.commit()


def build_services(db_session) -> dict:
    """Construct every repository and service and return the UI services dict.

    Delegates to the shared service factory (single wiring definition reused by
    the web server's per-request factory)."""
    from api.service_factory import build_request_services
    return build_request_services(db_session)


def _install_excepthook():
    """Log any uncaught exception (vital for windowed/frozen builds with no console)."""
    from loguru import logger

    def _hook(exc_type, exc, tb):
        logger.opt(exception=(exc_type, exc, tb)).error("Uncaught exception")
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _hook


def main():
    from loguru import logger
    setup_logging()
    _install_excepthook()

    try:
        # Schema is created from the models via create_all (single runtime source
        # of truth); Alembic remains available for explicit, versioned migrations.
        from database.base import Base
        from database.engine import engine
        import domain.entities  # noqa: F401  -- registers all models on Base.metadata

        Base.metadata.create_all(engine)
        # Thread-safe scoped session shared by the repositories for this app run.
        db_session = scoped_db_session()

        seed_initial_data(db_session)
        reconcile_permissions(db_session)
        services = build_services(db_session)

        # Start the LAN peer server so this portal can be reached remotely by the
        # superadmin portal (download data / view logs). Daemon thread; never fatal.
        from application.services.peer_server import PeerServer
        PeerServer().start()

        app = CSCN_portalApp(sys.argv)
        window = MainWindow(services)
        window.show()
        window.raise_()
        window.activateWindow()
        logger.info("Main window shown; entering Qt event loop.")

        exit_code = app.exec()
        logger.info(f"Qt event loop returned {exit_code}.")
        db_session.close()
        sys.exit(exit_code)
    except SystemExit:
        raise
    except Exception:
        logger.exception("Fatal error during application startup")
        raise


if __name__ == "__main__":
    main()
