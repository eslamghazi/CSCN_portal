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


def seed_initial_data(db_session) -> None:
    """Seed roles, the superadmin user, and the role-permission matrix on a fresh
    database. No-op once an admin user already exists."""
    user_repo = UserRepositoryImpl(db_session)
    if user_repo.has_admin_user():
        return

    import os
    import secrets
    import bcrypt
    from loguru import logger
    from domain.entities.user import Role, User, RolePermission

    # 1. Roles
    superadmin_role = Role(name="superadmin", description="صلاحيات كاملة لإدارة النظام")
    admin_role = Role(name="admin", description="صلاحيات إدارة المستخدمين والمحتوى")
    user_role = Role(name="user", description="مستخدم عادي")
    db_session.add_all([superadmin_role, admin_role, user_role])
    db_session.commit()

    # 2. Superadmin user. Password comes from CSCN_portal_SUPERADMIN_PASSWORD (loaded
    # from the .env file, which is bundled INTO the exe at build time so no
    # external .env is needed). If unset, generate a strong random one and log it.
    superadmin_password = os.environ.get("CSCN_portal_SUPERADMIN_PASSWORD")
    generated = not superadmin_password
    if generated:
        superadmin_password = secrets.token_urlsafe(12)

    salt = bcrypt.gensalt(rounds=12)
    hashed_pw = bcrypt.hashpw(superadmin_password.encode("utf-8"), salt).decode("utf-8")

    if generated:
        logger.warning(
            "Seeded superadmin with a generated password (no "
            "CSCN_portal_SUPERADMIN_PASSWORD set). Sign in and change it now: {}",
            superadmin_password,
        )

    db_session.add(User(
        username="superadmin",
        password_hash=hashed_pw,
        full_name="مدير النظام",
        role_id=superadmin_role.id,
        is_active=True,
    ))
    db_session.commit()

    # 2b. Default admin + regular users (for the center PC). These are starter
    # credentials meant to be changed after first login.
    def _hash(pw: str) -> str:
        return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

    default_accounts = [
        ("admin", "admin123", "مدير المركز", admin_role.id),
        ("user1", "user123", "مستخدم 1", user_role.id),
        ("user2", "user123", "مستخدم 2", user_role.id),
    ]
    for username, password, full_name, role_id in default_accounts:
        db_session.add(User(
            username=username, password_hash=_hash(password),
            full_name=full_name, role_id=role_id, is_active=True,
        ))
    db_session.commit()
    logger.warning(
        "Seeded default accounts (CHANGE THESE PASSWORDS): "
        "admin/admin123, user1/user123, user2/user123"
    )

    # 3. Role permissions for admin and user.
    content_modules = {m for m in PERMISSION_MODULES if m != "users"}
    perms = []
    for module in PERMISSION_MODULES:
        # Regular user: read-only, and only on permitted modules.
        perms.append(RolePermission(
            role_id=user_role.id, module=module, action="view",
            allowed=module not in USER_DENIED_VIEW))
        for action in ("create", "edit", "delete"):
            perms.append(RolePermission(role_id=user_role.id, module=module, action=action, allowed=False))
        # Admin: view/create/edit everywhere; delete only on content modules.
        for action in ("view", "create", "edit"):
            perms.append(RolePermission(role_id=admin_role.id, module=module, action=action, allowed=True))
        perms.append(RolePermission(
            role_id=admin_role.id, module=module, action="delete",
            allowed=module in content_modules,
        ))
    db_session.add_all(perms)
    db_session.commit()


def build_services(db_session) -> dict:
    """Construct every repository and service and return the UI services dict."""
    from infrastructure.repositories.standard_repository import StandardRepository, StandardCategoryRepository
    from infrastructure.repositories.indicator_repository import IndicatorRepository
    from infrastructure.repositories.document_repository import DocumentRepository, DocumentCategoryRepository, DocumentVersionRepository
    from infrastructure.repositories.attachment_repository import AttachmentRepository, EntityAttachmentRepository
    from infrastructure.repositories.hr_repository import EmployeeRepository, JobPositionRepository
    from infrastructure.repositories.training_repository import (
        TrainingProgramRepository, TrainingSessionRepository, AttendanceRepository,
        CourseRepository, WorkshopRepository, TraineeRepository,
    )
    from infrastructure.repositories.financial_repository import (
        RevenueRepository, ExpenseRepository, BudgetItemRepository, FiscalYearRepository,
    )
    from infrastructure.repositories.partnership_repository import PartnershipRepository, AgreementRepository
    from infrastructure.repositories.record_repository import RecordRepository

    from application.services.audit_service import AuditService
    from application.services.quality_service import QualityService
    from application.services.document_service import DocumentService
    from application.services.hr_service import HRService
    from application.services.training_service import TrainingService
    from application.services.financial_service import FinancialService
    from application.services.partnership_service import PartnershipService
    from application.services.permission_service import PermissionService
    from application.services.report_engine import ReportEngine
    from application.services.record_service import RecordService

    auth_service = AuthService(UserRepositoryImpl(db_session))
    audit_service = AuditService(db_session)

    quality_service = QualityService(
        StandardRepository(db_session), StandardCategoryRepository(db_session),
        IndicatorRepository(db_session), audit_service,
    )
    from config.settings import UPLOADS_DIR, EXPORTS_DIR
    doc_service = DocumentService(
        DocumentRepository(db_session), DocumentCategoryRepository(db_session),
        DocumentVersionRepository(db_session), audit_service,
        attachment_repo=AttachmentRepository(db_session),
        entity_attachment_repo=EntityAttachmentRepository(db_session),
        upload_dir=str(UPLOADS_DIR / "documents"),
    )
    hr_service = HRService(
        EmployeeRepository(db_session), JobPositionRepository(db_session), audit_service,
    )
    training_service = TrainingService(
        TrainingProgramRepository(db_session), TrainingSessionRepository(db_session),
        AttendanceRepository(db_session), audit_service,
        course_repo=CourseRepository(db_session),
        workshop_repo=WorkshopRepository(db_session),
        trainee_repo=TraineeRepository(db_session),
    )
    financial_service = FinancialService(
        RevenueRepository(db_session), ExpenseRepository(db_session),
        BudgetItemRepository(db_session), audit_service,
        fiscal_year_repo=FiscalYearRepository(db_session),
    )
    partnership_service = PartnershipService(
        PartnershipRepository(db_session), AgreementRepository(db_session), audit_service,
    )
    record_service = RecordService(RecordRepository(db_session))
    permission_service = PermissionService(db_session, auth_service)

    return {
        "auth": auth_service,
        "audit": audit_service,
        "quality": quality_service,
        "document": doc_service,
        "hr": hr_service,
        "training": training_service,
        "financial": financial_service,
        "partnership": partnership_service,
        "report": ReportEngine(export_dir=str(EXPORTS_DIR)),
        "record": record_service,
        "permission": permission_service,
    }


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
