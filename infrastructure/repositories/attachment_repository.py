from typing import List
from infrastructure.repositories.base_repository_impl import SQLAlchemyRepository
from domain.entities.attachment import Attachment, EntityAttachment
from sqlalchemy.orm import Session

class AttachmentRepository(SQLAlchemyRepository[Attachment]):
    def __init__(self, session: Session):
        super().__init__(session, Attachment)

class EntityAttachmentRepository(SQLAlchemyRepository[EntityAttachment]):
    def __init__(self, session: Session):
        super().__init__(session, EntityAttachment)
        
    def get_by_entity(self, entity_type: str, entity_id: int) -> List[EntityAttachment]:
        return self.session.query(EntityAttachment).filter(
            EntityAttachment.entity_type == entity_type,
            EntityAttachment.entity_id == entity_id
        ).all()
