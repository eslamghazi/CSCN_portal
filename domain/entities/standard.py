from typing import List, Optional
from sqlalchemy import String, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base, AuditMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities.indicator import Indicator

class StandardCategory(Base, AuditMixin):
    __tablename__ = "standard_categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    standards: Mapped[List["Standard"]] = relationship(back_populates="category")

class Standard(Base, AuditMixin):
    __tablename__ = "standards"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("standard_categories.id"))
    status: Mapped[str] = mapped_column(String(20), default="active")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    
    category: Mapped[Optional["StandardCategory"]] = relationship(back_populates="standards")
    indicators: Mapped[List["Indicator"]] = relationship("Indicator", back_populates="standard")
    compliance_records: Mapped[List["ComplianceRecord"]] = relationship("ComplianceRecord", back_populates="standard")

class ComplianceRecord(Base, AuditMixin):
    __tablename__ = "compliance_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    standard_id: Mapped[int] = mapped_column(ForeignKey("standards.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    standard: Mapped["Standard"] = relationship(back_populates="compliance_records")
