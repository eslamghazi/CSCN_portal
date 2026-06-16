from typing import List, Optional
from datetime import date
from sqlalchemy import String, Text, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base, AuditMixin

class Organization(Base, AuditMixin):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    contact_person: Mapped[Optional[str]] = mapped_column(String(200))
    email: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[str]] = mapped_column(Text)
    
    agreements: Mapped[List["Agreement"]] = relationship(back_populates="organization")

class Agreement(Base, AuditMixin):
    __tablename__ = "agreements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    agreement_type: Mapped[str] = mapped_column(String(50)) # agreement/mou/contract
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    description: Mapped[Optional[str]] = mapped_column(Text)
    terms: Mapped[Optional[str]] = mapped_column(Text)
    
    organization: Mapped["Organization"] = relationship(back_populates="agreements")
