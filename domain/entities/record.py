from typing import List, Optional
from datetime import date
from sqlalchemy import String, Text, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base, AuditMixin

class RecordType(Base, AuditMixin):
    __tablename__ = "record_types"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    records: Mapped[List["Record"]] = relationship(back_populates="record_type")

class Record(Base, AuditMixin):
    __tablename__ = "records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    record_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    record_type_id: Mapped[Optional[int]] = mapped_column(ForeignKey("record_types.id"))
    storage_location: Mapped[Optional[str]] = mapped_column(String(500))
    retention_period_months: Mapped[Optional[int]] = mapped_column()
    retention_expiry_date: Mapped[Optional[date]] = mapped_column(Date)
    disposal_method: Mapped[Optional[str]] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="active")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    record_type: Mapped[Optional["RecordType"]] = relationship(back_populates="records")
