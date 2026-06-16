from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.declarative import declared_attr


def utcnow() -> datetime:
    """Timezone-aware UTC now. Replaces the deprecated datetime.utcnow()."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass

class AuditMixin:
    """
    Mixin that adds audit columns to a model:
    created_at, updated_at, created_by, updated_by
    """

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(DateTime, default=utcnow)

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(DateTime, default=utcnow, onupdate=utcnow)
        
    @declared_attr
    def created_by(cls) -> Mapped[Optional[int]]:
        # Note: In a real implementation this would reference the users table.
        # It's an integer ID of the user who created the record.
        return mapped_column(Integer, nullable=True)

    @declared_attr
    def updated_by(cls) -> Mapped[Optional[int]]:
        return mapped_column(Integer, nullable=True)
