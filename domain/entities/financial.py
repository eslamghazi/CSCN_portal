from typing import List, Optional
from datetime import date
from sqlalchemy import String, Text, DECIMAL, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base, AuditMixin
from decimal import Decimal

class FiscalYear(Base, AuditMixin):
    __tablename__ = "fiscal_years"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    
    budget_items: Mapped[List["BudgetItem"]] = relationship(back_populates="fiscal_year")
    revenues: Mapped[List["Revenue"]] = relationship(back_populates="fiscal_year")

class BudgetItem(Base, AuditMixin):
    __tablename__ = "budget_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fiscal_year_id: Mapped[int] = mapped_column(ForeignKey("fiscal_years.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    allocated_amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=0.0)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    fiscal_year: Mapped["FiscalYear"] = relationship(back_populates="budget_items")
    expenses: Mapped[List["Expense"]] = relationship(back_populates="budget_item")

class Expense(Base, AuditMixin):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    budget_item_id: Mapped[int] = mapped_column(ForeignKey("budget_items.id"))
    amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    receipt_number: Mapped[Optional[str]] = mapped_column(String(100))
    
    budget_item: Mapped["BudgetItem"] = relationship(back_populates="expenses")

class Revenue(Base, AuditMixin):
    __tablename__ = "revenues"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fiscal_year_id: Mapped[int] = mapped_column(ForeignKey("fiscal_years.id"))
    amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    revenue_date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    fiscal_year: Mapped["FiscalYear"] = relationship(back_populates="revenues")
