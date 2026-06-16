from pathlib import Path

from infrastructure.repositories.document_repository import (
    DocumentRepository, DocumentCategoryRepository, DocumentVersionRepository,
)
from infrastructure.repositories.attachment_repository import (
    AttachmentRepository, EntityAttachmentRepository,
)
from application.services.document_service import DocumentService, DocumentDTO
from domain.entities.document import Document


def _service(db_session, audit_service, upload_dir):
    return DocumentService(
        DocumentRepository(db_session), DocumentCategoryRepository(db_session),
        DocumentVersionRepository(db_session), audit_service,
        attachment_repo=AttachmentRepository(db_session),
        entity_attachment_repo=EntityAttachmentRepository(db_session),
        upload_dir=str(upload_dir),
    )


def test_upload_stores_recoverable_file(db_session, audit_service, tmp_path):
    src = tmp_path / "policy.txt"
    src.write_text("data", encoding="utf-8")
    svc = _service(db_session, audit_service, tmp_path / "store")

    doc = svc.upload_document(DocumentDTO(title="T", doc_type="policy"), str(src))
    path = svc.get_document_file_path(doc.id)
    assert path is not None
    assert Path(path).exists()


def test_link_evidence_points_target_at_attachment(db_session, audit_service, tmp_path):
    src = tmp_path / "policy.txt"
    src.write_text("data", encoding="utf-8")
    svc = _service(db_session, audit_service, tmp_path / "store")
    doc = svc.upload_document(DocumentDTO(title="T", doc_type="policy"), str(src))

    assert svc.link_document_as_evidence(doc.id, "standard", 7) is True
    rows = svc.entity_attachment_repo.get_by_entity("standard", 7)
    assert len(rows) == 1
    assert rows[0].link_type == "evidence"


def test_link_evidence_without_file_returns_false(db_session, audit_service, tmp_path):
    svc = _service(db_session, audit_service, tmp_path / "store")
    doc = svc.doc_repo.create(Document(title="x", doc_type="policy"))
    assert svc.link_document_as_evidence(doc.id, "standard", 1) is False
