from typing import List, Optional
from pydantic import BaseModel
from datetime import date
from infrastructure.repositories.partnership_repository import PartnershipRepository, AgreementRepository
from domain.entities.partnership import Organization as Partnership, Agreement
from application.services.audit_service import AuditService

class PartnershipDTO(BaseModel):
    id: Optional[int] = None
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    status: str = "active"

class PartnershipService:
    def __init__(
        self,
        partner_repo: PartnershipRepository,
        agreement_repo: AgreementRepository,
        audit_service: AuditService
    ):
        self.partner_repo = partner_repo
        self.agreement_repo = agreement_repo
        self.audit_service = audit_service
        
    def add_partner(self, data: PartnershipDTO) -> Partnership:
        p = Partnership(
            name=data.name,
            contact_person=data.contact_person,
            email=data.email,
            phone=data.phone,
            address=data.address
        )
        
        created = self.partner_repo.create(p)
        
        self.audit_service.log_action(
            module="partnership",
            action="add_partner",
            entity_type="Organization",
            entity_id=created.id,
            new_values={"name": created.name}
        )
        
        return created

    def get_all_partners(self) -> List[Partnership]:
        return self.partner_repo.get_all()

    def get_partner(self, partner_id: int) -> Optional[Partnership]:
        return self.partner_repo.get_by_id(partner_id)

    def update_partner(self, data: PartnershipDTO) -> Optional[Partnership]:
        if not data.id:
            return None
        p = self.partner_repo.get_by_id(data.id)
        if not p:
            return None
        p.name = data.name
        p.contact_person = data.contact_person
        p.email = data.email
        p.phone = data.phone
        p.address = data.address
        updated = self.partner_repo.update(p)
        self.audit_service.log_action(
            module="partnership", action="update_partner",
            entity_type="Organization", entity_id=updated.id,
            new_values={"name": updated.name})
        return updated

    def delete_partner(self, partner_id: int) -> bool:
        deleted = self.partner_repo.delete(partner_id)
        if deleted:
            self.audit_service.log_action(
                module="partnership", action="delete_partner",
                entity_type="Organization", entity_id=partner_id)
        return deleted
        
    def add_agreement(
        self,
        partner_id: int,
        title: str,
        start_date: date,
        end_date: date,
        agreement_type: str = "agreement",
    ) -> Agreement:
        agr = Agreement(
            organization_id=partner_id,
            title=title,
            agreement_type=agreement_type,
            start_date=start_date,
            end_date=end_date,
            status="active"
        )
        created = self.agreement_repo.create(agr)
        
        self.audit_service.log_action(
            module="partnership",
            action="add_agreement",
            entity_type="Agreement",
            entity_id=created.id,
            new_values={"title": title, "partner_id": partner_id}
        )

        return created

    def list_agreements(self, partner_id: int) -> List[Agreement]:
        return self.agreement_repo.get_by_partner(partner_id)

    def delete_agreement(self, agreement_id: int) -> bool:
        deleted = self.agreement_repo.delete(agreement_id)
        if deleted:
            self.audit_service.log_action(
                module="partnership", action="delete_agreement",
                entity_type="Agreement", entity_id=agreement_id)
        return deleted
