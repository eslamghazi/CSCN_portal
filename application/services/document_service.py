from typing import List, Optional
from datetime import date
from pydantic import BaseModel
import shutil
import hashlib
from pathlib import Path

from infrastructure.repositories.document_repository import (
    DocumentRepository, DocumentCategoryRepository, DocumentVersionRepository
)
from infrastructure.repositories.attachment_repository import (
    AttachmentRepository, EntityAttachmentRepository
)
from domain.entities.document import Document, DocumentCategory, DocumentVersion
from domain.entities.attachment import Attachment, EntityAttachment
from application.services.audit_service import AuditService
from application.services.auth_service import AuthService

class DocumentDTO(BaseModel):
    id: Optional[int] = None
    title: str
    doc_type: str
    category_id: Optional[int] = None
    status: str = "draft"
    effective_date: Optional[date] = None
    review_date: Optional[date] = None
    file_path: Optional[str] = None # Transient for upload

class DocumentService:
    # link_type markers used on EntityAttachment rows.
    FILE_LINK = "document_file"
    EVIDENCE_LINK = "evidence"

    def __init__(
        self,
        doc_repo: DocumentRepository,
        category_repo: DocumentCategoryRepository,
        version_repo: DocumentVersionRepository,
        audit_service: AuditService,
        attachment_repo: Optional[AttachmentRepository] = None,
        entity_attachment_repo: Optional[EntityAttachmentRepository] = None,
        upload_dir: str = "data/uploads/documents"
    ):
        self.doc_repo = doc_repo
        self.category_repo = category_repo
        self.version_repo = version_repo
        self.audit_service = audit_service
        self.attachment_repo = attachment_repo
        self.entity_attachment_repo = entity_attachment_repo
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _find_document_file_link(self, doc_id: int) -> Optional[EntityAttachment]:
        """Return the EntityAttachment row that links a document to its stored file."""
        if not self.entity_attachment_repo:
            return None
        links = self.entity_attachment_repo.get_by_entity("document", doc_id)
        for link in links:
            if link.link_type == self.FILE_LINK:
                return link
        return None
        
    def upload_document(self, dto: DocumentDTO, source_file_path: str) -> Document:
        """
        Uploads a physical file and creates a new Document record with version 1.0.
        """
        # Create Document Entity
        doc = Document(
            title=dto.title,
            doc_type=dto.doc_type,
            category_id=dto.category_id,
            status=dto.status,
            current_version="1.0",
            effective_date=dto.effective_date,
            review_date=dto.review_date
        )
        created_doc = self.doc_repo.create(doc)
        
        # Handle file copy
        source_path = Path(source_file_path)
        ext = source_path.suffix
        filename = f"doc_{created_doc.id}_v1_0{ext}"
        dest_path = self.upload_dir / filename
        
        shutil.copy2(source_file_path, dest_path)

        # Create Version Record
        version = DocumentVersion(
            document_id=created_doc.id,
            version_number="1.0",
            notes=f"Initial upload from {source_path.name}"
        )
        self.version_repo.create(version)

        # Register the physical file as an Attachment and link it to the document
        # via the polymorphic EntityAttachment table, so the stored path is
        # recoverable from the database.
        if self.attachment_repo and self.entity_attachment_repo:
            current_user = AuthService.get_current_user()
            attachment = Attachment(
                file_name=source_path.name,
                file_path=str(dest_path),
                file_type=(ext.lstrip(".") or "bin")[:20],
                file_size=dest_path.stat().st_size,
                checksum=self._sha256(dest_path),
                uploaded_by=current_user.id if current_user else None,
            )
            created_att = self.attachment_repo.create(attachment)
            self.entity_attachment_repo.create(EntityAttachment(
                entity_type="document",
                entity_id=created_doc.id,
                attachment_id=created_att.id,
                link_type=self.FILE_LINK,
            ))

        # Audit
        self.audit_service.log_action(
            module="documents",
            action="upload_document",
            entity_type="Document",
            entity_id=created_doc.id,
            new_values={"title": created_doc.title, "file": filename}
        )
        
        return created_doc

    def get_all_documents(self) -> List[Document]:
        return self.doc_repo.get_all()
        
    def update_document(self, dto: DocumentDTO) -> Optional[Document]:
        if not dto.id:
            return None
            
        doc = self.doc_repo.get_by_id(dto.id)
        if not doc:
            return None
            
        old_values = {"title": doc.title, "status": doc.status}
        
        doc.title = dto.title
        doc.doc_type = dto.doc_type
        doc.category_id = dto.category_id
        doc.status = dto.status
        doc.effective_date = dto.effective_date
        doc.review_date = dto.review_date
        
        updated = self.doc_repo.update(doc)
        
        self.audit_service.log_action(
            module="documents",
            action="update_document",
            entity_type="Document",
            entity_id=updated.id,
            old_values=old_values,
            new_values={"title": updated.title, "status": updated.status}
        )
        
        return updated
        
    def get_categories(self) -> List[DocumentCategory]:
        return self.category_repo.get_all()

    def create_category(self, name: str, description: str = None) -> DocumentCategory:
        return self.category_repo.create(
            DocumentCategory(name=name, description=description))

    def update_category(self, category_id: int, name: str,
                        description: str = None) -> Optional[DocumentCategory]:
        category = self.category_repo.get_by_id(category_id)
        if not category:
            return None
        category.name = name
        category.description = description
        return self.category_repo.update(category)

    def delete_category(self, category_id: int) -> bool:
        return self.category_repo.delete(category_id)

    def delete_document(self, doc_id: int) -> bool:
        deleted = self.doc_repo.delete(doc_id)
        if deleted:
            self.audit_service.log_action(
                module="documents", action="delete_document",
                entity_type="Document", entity_id=doc_id)
        return deleted
        
    def approve_document(self, doc_id: int) -> bool:
        doc = self.doc_repo.get_by_id(doc_id)
        if doc:
            old_status = doc.status
            doc.status = "approved"
            self.doc_repo.update(doc)
            self.audit_service.log_action(
                module="documents",
                action="approve_document",
                entity_type="Document",
                entity_id=doc.id,
                old_values={"status": old_status},
                new_values={"status": "approved"}
            )
            return True
        return False
        
    def get_document_file_path(self, doc_id: int) -> Optional[str]:
        """Return the stored file path for a document, or None if not found."""
        link = self._find_document_file_link(doc_id)
        if not link or not self.attachment_repo:
            return None
        attachment = self.attachment_repo.get_by_id(link.attachment_id)
        return attachment.file_path if attachment else None

    def link_document_as_evidence(self, doc_id: int, entity_type: str, entity_id: int) -> bool:
        """Link a document's stored file to another entity (e.g. a Standard) as
        evidence, by creating an EntityAttachment row that points the target
        entity at the same underlying Attachment.

        Returns False if the document has no stored file to link.
        """
        if not self.entity_attachment_repo:
            return False

        file_link = self._find_document_file_link(doc_id)
        if not file_link:
            return False

        self.entity_attachment_repo.create(EntityAttachment(
            entity_type=entity_type,
            entity_id=entity_id,
            attachment_id=file_link.attachment_id,
            link_type=self.EVIDENCE_LINK,
        ))

        self.audit_service.log_action(
            module="documents",
            action="link_evidence",
            entity_type=entity_type,
            entity_id=entity_id,
            new_values={"document_id": doc_id, "attachment_id": file_link.attachment_id}
        )
        return True
