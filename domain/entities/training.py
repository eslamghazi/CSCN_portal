from typing import List, Optional
from datetime import date
from sqlalchemy import String, Text, Integer, ForeignKey, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base, AuditMixin

class Trainer(Base, AuditMixin):
    __tablename__ = "trainers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))
    specialization: Mapped[Optional[str]] = mapped_column(String(200))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    
    programs: Mapped[List["TrainingProgram"]] = relationship(back_populates="trainer")

class Trainee(Base, AuditMixin):
    __tablename__ = "trainees"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    organization: Mapped[Optional[str]] = mapped_column(String(200))
    
    attendances: Mapped[List["SessionAttendance"]] = relationship(back_populates="trainee")

class TrainingProgram(Base, AuditMixin):
    __tablename__ = "training_programs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    program_type: Mapped[str] = mapped_column(String(50), nullable=False) # training/workshop/course
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    total_hours: Mapped[Optional[int]] = mapped_column(Integer)
    max_capacity: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="planned")
    trainer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("trainers.id"))
    
    trainer: Mapped[Optional["Trainer"]] = relationship(back_populates="programs")
    courses: Mapped[List["Course"]] = relationship(back_populates="program", cascade="all, delete-orphan")
    workshops: Mapped[List["Workshop"]] = relationship(back_populates="program", cascade="all, delete-orphan")

class Course(Base, AuditMixin):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("training_programs.id"))
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    program: Mapped["TrainingProgram"] = relationship(back_populates="courses")
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="course", cascade="all, delete-orphan")

class Workshop(Base, AuditMixin):
    __tablename__ = "workshops"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("training_programs.id"))
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    program: Mapped["TrainingProgram"] = relationship(back_populates="workshops")
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="workshop", cascade="all, delete-orphan")

class Session(Base, AuditMixin):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[Optional[int]] = mapped_column(ForeignKey("courses.id"))
    workshop_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workshops.id"))
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    duration_hours: Mapped[int] = mapped_column(Integer, default=1)
    topic: Mapped[Optional[str]] = mapped_column(String(500))
    
    course: Mapped[Optional["Course"]] = relationship(back_populates="sessions")
    workshop: Mapped[Optional["Workshop"]] = relationship(back_populates="sessions")
    attendances: Mapped[List["SessionAttendance"]] = relationship(back_populates="session", cascade="all, delete-orphan")

class SessionAttendance(Base, AuditMixin):
    __tablename__ = "session_attendance"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    trainee_id: Mapped[int] = mapped_column(ForeignKey("trainees.id"))
    is_present: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    session: Mapped["Session"] = relationship(back_populates="attendances")
    trainee: Mapped["Trainee"] = relationship(back_populates="attendances")
