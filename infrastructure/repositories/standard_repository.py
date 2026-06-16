from typing import List, Optional
from infrastructure.repositories.base_repository_impl import SQLAlchemyRepository
from domain.entities.standard import Standard, StandardCategory
from sqlalchemy.orm import Session

class StandardCategoryRepository(SQLAlchemyRepository[StandardCategory]):
    def __init__(self, session: Session):
        super().__init__(session, StandardCategory)

class StandardRepository(SQLAlchemyRepository[Standard]):
    def __init__(self, session: Session):
        super().__init__(session, Standard)
        
    def get_by_code(self, code: str) -> Optional[Standard]:
        return self.session.query(Standard).filter(Standard.code == code).first()
        
    def get_active_standards(self) -> List[Standard]:
        return self.session.query(Standard).filter(Standard.is_archived.is_(False)).all()
