from typing import List, Optional
from datetime import date
from sqlalchemy import String, Text, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base, AuditMixin

class DocumentCategory(Base, AuditMixin):
    __tablename__ = "document_categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    documents: Mapped[List["Document"]] = relationship(back_populates="category")

class Document(Base, AuditMixin):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False) # policy/procedure/etc
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("document_categories.id"))
    current_version: Mapped[str] = mapped_column(String(20), default="1.0")
    content_summary: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    effective_date: Mapped[Optional[date]] = mapped_column(Date)
    review_date: Mapped[Optional[date]] = mapped_column(Date)
    
    category: Mapped[Optional["DocumentCategory"]] = relationship(back_populates="documents")
    versions: Mapped[List["DocumentVersion"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    revisions: Mapped[List["DocumentRevision"]] = relationship(back_populates="document", cascade="all, delete-orphan")

class DocumentVersion(Base, AuditMixin):
    __tablename__ = "document_versions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    version_number: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    document: Mapped["Document"] = relationship(back_populates="versions")

class DocumentRevision(Base, AuditMixin):
    __tablename__ = "document_revisions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    revision_date: Mapped[date] = mapped_column(Date, nullable=False)
    changes_summary: Mapped[str] = mapped_column(Text, nullable=False)
    
    document: Mapped["Document"] = relationship(back_populates="revisions")
