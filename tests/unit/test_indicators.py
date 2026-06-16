from infrastructure.repositories.standard_repository import (
    StandardRepository, StandardCategoryRepository,
)
from infrastructure.repositories.indicator_repository import IndicatorRepository
from application.services.quality_service import QualityService, StandardDTO, IndicatorDTO


def _service(db_session, audit_service):
    return QualityService(
        StandardRepository(db_session), StandardCategoryRepository(db_session),
        IndicatorRepository(db_session), audit_service,
    )


def test_indicator_crud_and_tree(db_session, audit_service):
    svc = _service(db_session, audit_service)
    std = svc.create_standard(StandardDTO(code="S1", name="معيار"))
    root = svc.create_indicator(IndicatorDTO(
        code="I1", name="مؤشر", standard_id=std.id, weight=50, status="active"))
    svc.create_indicator(IndicatorDTO(
        code="I1-1", name="فرعي", standard_id=std.id, parent_id=root.id))

    roots = svc.get_indicators(std.id)
    assert len(roots) == 1
    assert len(roots[0].sub_indicators) == 1

    updated = svc.update_indicator(IndicatorDTO(
        id=root.id, code="I1", name="مؤشر محدث", status="compliant"))
    assert updated.name == "مؤشر محدث"
    assert updated.status == "compliant"


def test_compliance_uses_indicator_status(db_session, audit_service):
    svc = _service(db_session, audit_service)
    std = svc.create_standard(StandardDTO(code="S2", name="معيار"))
    svc.create_indicator(IndicatorDTO(code="A", name="a", standard_id=std.id, status="compliant"))
    svc.create_indicator(IndicatorDTO(code="B", name="b", standard_id=std.id, status="active"))
    assert svc.calculate_compliance(std.id) == 50.0


def test_delete_indicator(db_session, audit_service):
    svc = _service(db_session, audit_service)
    std = svc.create_standard(StandardDTO(code="S3", name="معيار"))
    ind = svc.create_indicator(IndicatorDTO(code="X", name="x", standard_id=std.id))
    assert svc.delete_indicator(ind.id) is True
    assert svc.get_indicators(std.id) == []
