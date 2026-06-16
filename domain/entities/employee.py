from typing import List, Optional
from datetime import date
from sqlalchemy import String, Text, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base, AuditMixin

class Position(Base, AuditMixin):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    employees: Mapped[List["Employee"]] = relationship(back_populates="position")

class Employee(Base, AuditMixin):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    position_id: Mapped[Optional[int]] = mapped_column(ForeignKey("positions.id"))
    hire_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="active")
    
    position: Mapped[Optional["Position"]] = relationship(back_populates="employees")
    qualifications: Mapped[List["Qualification"]] = relationship(back_populates="employee", cascade="all, delete-orphan")
    experience_records: Mapped[List["ExperienceRecord"]] = relationship(back_populates="employee", cascade="all, delete-orphan")
    evaluations: Mapped[List["EmployeeEvaluation"]] = relationship(back_populates="employee", cascade="all, delete-orphan")

class Qualification(Base, AuditMixin):
    __tablename__ = "qualifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    degree: Mapped[str] = mapped_column(String(200), nullable=False)
    institution: Mapped[str] = mapped_column(String(200), nullable=False)
    year_obtained: Mapped[Optional[int]] = mapped_column()
    
    employee: Mapped["Employee"] = relationship(back_populates="qualifications")

class ExperienceRecord(Base, AuditMixin):
    __tablename__ = "experience_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    job_title: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    employee: Mapped["Employee"] = relationship(back_populates="experience_records")

class EmployeeEvaluation(Base, AuditMixin):
    __tablename__ = "employee_evaluations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    evaluation_date: Mapped[date] = mapped_column(Date, nullable=False)
    score: Mapped[Optional[float]] = mapped_column()
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    employee: Mapped["Employee"] = relationship(back_populates="evaluations")
