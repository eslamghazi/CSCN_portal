from typing import List, Optional
from sqlalchemy import String, Text, DECIMAL, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base, AuditMixin
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities.standard import Standard

class Indicator(Base, AuditMixin):
    __tablename__ = "indicators"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    standard_id: Mapped[Optional[int]] = mapped_column(ForeignKey("standards.id"))
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("indicators.id"))
    weight: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2))
    status: Mapped[str] = mapped_column(String(20), default="active")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    standard: Mapped[Optional["Standard"]] = relationship("Standard", back_populates="indicators")
    parent: Mapped[Optional["Indicator"]] = relationship("Indicator", remote_side=[id], back_populates="sub_indicators")
    sub_indicators: Mapped[List["Indicator"]] = relationship("Indicator", back_populates="parent")
