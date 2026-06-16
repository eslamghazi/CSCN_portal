from typing import TypeVar, List, Optional, Type
from sqlalchemy.orm import Session
from sqlalchemy import func
from domain.interfaces.base_repository import BaseRepository

T = TypeVar('T')

class SQLAlchemyRepository(BaseRepository[T]):
    """
    Generic SQLAlchemy implementation of BaseRepository.
    """
    
    def __init__(self, session: Session, model_class: Type[T]):
        self.session = session
        self.model_class = model_class

    def get_by_id(self, id: int) -> Optional[T]:
        return self.session.query(self.model_class).filter(self.model_class.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        return self.session.query(self.model_class).offset(skip).limit(limit).all()

    def create(self, entity: T) -> T:
        try:
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(entity)
            return entity
        except Exception:
            self.session.rollback()
            raise

    def update(self, entity: T) -> T:
        # merge() returns the persistent instance managed by the session, which
        # may differ from the detached `entity` passed in — return that one.
        try:
            merged = self.session.merge(entity)
            self.session.commit()
            return merged
        except Exception:
            self.session.rollback()
            raise

    def delete(self, id: int) -> bool:
        entity = self.get_by_id(id)
        if entity:
            try:
                self.session.delete(entity)
                self.session.commit()
                return True
            except Exception:
                self.session.rollback()
                raise
        return False
        
    def count(self) -> int:
        return self.session.query(func.count(self.model_class.id)).scalar()
