from typing import List
from infrastructure.repositories.base_repository_impl import SQLAlchemyRepository
from domain.entities.document import Document, DocumentCategory, DocumentVersion, DocumentRevision
from sqlalchemy.orm import Session

class DocumentCategoryRepository(SQLAlchemyRepository[DocumentCategory]):
    def __init__(self, session: Session):
        super().__init__(session, DocumentCategory)

class DocumentRepository(SQLAlchemyRepository[Document]):
    def __init__(self, session: Session):
        super().__init__(session, Document)
        
    def get_by_category(self, category_id: int) -> List[Document]:
        return self.session.query(Document).filter(Document.category_id == category_id).all()

class DocumentVersionRepository(SQLAlchemyRepository[DocumentVersion]):
    def __init__(self, session: Session):
        super().__init__(session, DocumentVersion)

class DocumentRevisionRepository(SQLAlchemyRepository[DocumentRevision]):
    def __init__(self, session: Session):
        super().__init__(session, DocumentRevision)
