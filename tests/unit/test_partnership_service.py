from datetime import date

from infrastructure.repositories.partnership_repository import (
    PartnershipRepository, AgreementRepository,
)
from application.services.partnership_service import PartnershipService, PartnershipDTO


def _service(db_session, audit_service):
    return PartnershipService(
        PartnershipRepository(db_session), AgreementRepository(db_session), audit_service
    )


def test_add_agreement_uses_organization_id_and_type(db_session, audit_service):
    svc = _service(db_session, audit_service)
    partner = svc.add_partner(PartnershipDTO(name="جهة"))
    agr = svc.add_agreement(partner.id, "بروتوكول", date(2026, 1, 1), date(2026, 12, 31))
    assert agr.organization_id == partner.id
    assert agr.agreement_type == "agreement"


def test_add_partner_persists_address(db_session, audit_service):
    svc = _service(db_session, audit_service)
    partner = svc.add_partner(PartnershipDTO(name="جهة", address="العنوان التجريبي"))
    assert partner.address == "العنوان التجريبي"


def test_get_by_partner_filters_by_organization(db_session, audit_service):
    svc = _service(db_session, audit_service)
    p1 = svc.add_partner(PartnershipDTO(name="A"))
    p2 = svc.add_partner(PartnershipDTO(name="B"))
    svc.add_agreement(p1.id, "x", date(2026, 1, 1), date(2026, 2, 1))
    svc.add_agreement(p1.id, "y", date(2026, 1, 1), date(2026, 2, 1))
    svc.add_agreement(p2.id, "z", date(2026, 1, 1), date(2026, 2, 1))
    assert len(svc.agreement_repo.get_by_partner(p1.id)) == 2
    assert len(svc.agreement_repo.get_by_partner(p2.id)) == 1
