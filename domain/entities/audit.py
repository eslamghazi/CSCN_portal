from typing import Optional
from datetime import datetime
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base, utcnow

class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(50))
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    old_values: Mapped[Optional[str]] = mapped_column(Text) # JSON string
    new_values: Mapped[Optional[str]] = mapped_column(Text) # JSON string
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
