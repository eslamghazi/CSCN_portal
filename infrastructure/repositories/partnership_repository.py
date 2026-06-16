from typing import List
from infrastructure.repositories.base_repository_impl import SQLAlchemyRepository
from domain.entities.partnership import Organization as Partnership, Agreement
from sqlalchemy.orm import Session

class PartnershipRepository(SQLAlchemyRepository[Partnership]):
    def __init__(self, session: Session):
        super().__init__(session, Partnership)
        
    def get_active_partnerships(self) -> List[Partnership]:
        return self.session.query(Partnership).all() # Organization doesn't have status, return all

class AgreementRepository(SQLAlchemyRepository[Agreement]):
    def __init__(self, session: Session):
        super().__init__(session, Agreement)
        
    def get_by_partner(self, partner_id: int) -> List[Agreement]:
        return self.session.query(Agreement).filter(
            Agreement.organization_id == partner_id
        ).all()
