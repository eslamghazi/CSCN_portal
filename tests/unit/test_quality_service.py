from infrastructure.repositories.standard_repository import (
    StandardRepository, StandardCategoryRepository,
)
from infrastructure.repositories.indicator_repository import IndicatorRepository
from application.services.quality_service import QualityService, StandardDTO


def _service(db_session, audit_service):
    return QualityService(
        StandardRepository(db_session), StandardCategoryRepository(db_session),
        IndicatorRepository(db_session), audit_service,
    )


def test_create_and_update_standard(db_session, audit_service):
    svc = _service(db_session, audit_service)
    created = svc.create_standard(StandardDTO(code="STD-1", name="معيار", status="active"))
    assert created.id is not None

    updated = svc.update_standard(StandardDTO(
        id=created.id, code="STD-1", name="معيار محدث", status="inactive"))
    assert updated.name == "معيار محدث"
    assert updated.status == "inactive"


def test_update_unknown_standard_returns_none(db_session, audit_service):
    svc = _service(db_session, audit_service)
    assert svc.update_standard(StandardDTO(id=999, code="X", name="Y")) is None
