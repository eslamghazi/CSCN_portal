from typing import List
from sqlalchemy.orm import Session
from infrastructure.repositories.base_repository_impl import SQLAlchemyRepository
from domain.entities.record import Record, RecordType


class RecordRepository(SQLAlchemyRepository[Record]):
    """Records share the generic CRUD of SQLAlchemyRepository
    (get_all / get_by_id / create / update / delete / count) and add a couple
    of RecordType helpers, since record types are a small related lookup table."""

    def __init__(self, session: Session):
        super().__init__(session, Record)

    def get_all_record_types(self) -> List[RecordType]:
        return self.session.query(RecordType).all()

    def create_record_type(self, record_type: RecordType) -> RecordType:
        try:
            self.session.add(record_type)
            self.session.commit()
            self.session.refresh(record_type)
            return record_type
        except Exception:
            self.session.rollback()
            raise

    def update_record_type(self, type_id: int, name: str,
                           description: str = None) -> RecordType:
        obj = self.session.get(RecordType, type_id)
        if not obj:
            return None
        obj.name = name
        obj.description = description
        try:
            self.session.commit()
            self.session.refresh(obj)
            return obj
        except Exception:
            self.session.rollback()
            raise

    def delete_record_type(self, type_id: int) -> bool:
        obj = self.session.get(RecordType, type_id)
        if not obj:
            return False
        try:
            self.session.delete(obj)
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            raise
