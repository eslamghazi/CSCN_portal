from typing import List
from infrastructure.repositories.base_repository_impl import SQLAlchemyRepository
from domain.entities.indicator import Indicator
from sqlalchemy.orm import Session

class IndicatorRepository(SQLAlchemyRepository[Indicator]):
    def __init__(self, session: Session):
        super().__init__(session, Indicator)
        
    def get_by_standard_id(self, standard_id: int) -> List[Indicator]:
        return self.session.query(Indicator).filter(
            Indicator.standard_id == standard_id,
            Indicator.parent_id.is_(None) # Get root indicators only
        ).order_by(Indicator.sort_order).all()
