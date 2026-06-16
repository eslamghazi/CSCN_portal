from typing import List, Optional
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base, AuditMixin

class FormTemplate(Base, AuditMixin):
    __tablename__ = "form_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    
    sections: Mapped[List["FormSection"]] = relationship(back_populates="template", cascade="all, delete-orphan", order_by="FormSection.sort_order")

class FormSection(Base, AuditMixin):
    __tablename__ = "form_sections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("form_templates.id"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    template: Mapped["FormTemplate"] = relationship(back_populates="sections")
    fields: Mapped[List["FormField"]] = relationship(back_populates="section", cascade="all, delete-orphan", order_by="FormField.sort_order")

class FormField(Base, AuditMixin):
    __tablename__ = "form_fields"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("form_sections.id"))
    label: Mapped[str] = mapped_column(String(500), nullable=False)
    field_type: Mapped[str] = mapped_column(String(50), nullable=False) # text, boolean, multiline
    is_required: Mapped[bool] = mapped_column(default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    section: Mapped["FormSection"] = relationship(back_populates="fields")
