from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base, utcnow

class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100))
    checksum: Mapped[Optional[str]] = mapped_column(String(64)) # SHA-256
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    uploaded_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    
    entities: Mapped[List["EntityAttachment"]] = relationship(back_populates="attachment", cascade="all, delete-orphan")

class EntityAttachment(Base):
    """
    Polymorphic link table to link an attachment to any entity
    (standard, indicator, document, etc.)
    """
    __tablename__ = "entity_attachments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    attachment_id: Mapped[int] = mapped_column(ForeignKey("attachments.id"))
    link_type: Mapped[Optional[str]] = mapped_column(String(50)) # evidence, supporting, certificate
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
    attachment: Mapped["Attachment"] = relationship(back_populates="entities")
