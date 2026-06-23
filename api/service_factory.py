"""Build a fresh set of application services bound to a single DB session.

On the web server this is called once PER REQUEST (with that request's session)
so services never share state across concurrent requests. ``main.build_services``
delegates here too, so there is a single wiring definition.
"""


def build_request_services(db_session) -> dict:
    """Construct every repository and service bound to ``db_session`` and return
    the services dict used by both the web routers and the (legacy) Qt UI."""
    from infrastructure.repositories.standard_repository import (
        StandardRepository, StandardCategoryRepository,
    )
    from infrastructure.repositories.indicator_repository import IndicatorRepository
    from infrastructure.repositories.document_repository import (
        DocumentRepository, DocumentCategoryRepository, DocumentVersionRepository,
    )
    from infrastructure.repositories.attachment_repository import (
        AttachmentRepository, EntityAttachmentRepository,
    )
    from infrastructure.repositories.hr_repository import (
        EmployeeRepository, JobPositionRepository,
    )
    from infrastructure.repositories.training_repository import (
        TrainingProgramRepository, TrainingSessionRepository, AttendanceRepository,
        CourseRepository, WorkshopRepository, TraineeRepository,
    )
    from infrastructure.repositories.financial_repository import (
        RevenueRepository, ExpenseRepository, BudgetItemRepository, FiscalYearRepository,
    )
    from infrastructure.repositories.partnership_repository import (
        PartnershipRepository, AgreementRepository,
    )
    from infrastructure.repositories.record_repository import RecordRepository
    from infrastructure.repositories.user_repository_impl import UserRepositoryImpl

    from application.services.auth_service import AuthService
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
    from config.settings import UPLOADS_DIR, EXPORTS_DIR

    auth_service = AuthService(UserRepositoryImpl(db_session))
    audit_service = AuditService(db_session)

    quality_service = QualityService(
        StandardRepository(db_session), StandardCategoryRepository(db_session),
        IndicatorRepository(db_session), audit_service,
    )
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
