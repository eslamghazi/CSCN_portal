from typing import List, Optional
from pydantic import BaseModel
from datetime import date
from infrastructure.repositories.training_repository import (
    TrainingProgramRepository, TrainingSessionRepository, AttendanceRepository,
    CourseRepository, WorkshopRepository, TraineeRepository,
)
from domain.entities.training import (
    TrainingProgram, Session as TrainingSession, Course, Workshop, Trainee,
    SessionAttendance,
)
from application.services.audit_service import AuditService

class TrainingProgramDTO(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    program_type: str = "training"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_hours: Optional[int] = None
    status: str = "active"

class TrainingService:
    def __init__(
        self,
        program_repo: TrainingProgramRepository,
        session_repo: TrainingSessionRepository,
        attendance_repo: AttendanceRepository,
        audit_service: AuditService,
        course_repo: CourseRepository = None,
        workshop_repo: WorkshopRepository = None,
        trainee_repo: TraineeRepository = None,
    ):
        self.program_repo = program_repo
        self.session_repo = session_repo
        self.attendance_repo = attendance_repo
        self.audit_service = audit_service
        self.course_repo = course_repo
        self.workshop_repo = workshop_repo
        self.trainee_repo = trainee_repo
        
    def create_program(self, data: TrainingProgramDTO) -> TrainingProgram:
        prog = TrainingProgram(
            name=data.name,
            description=data.description,
            program_type=data.program_type,
            start_date=data.start_date,
            end_date=data.end_date,
            total_hours=data.total_hours,
            status=data.status
        )
        
        created = self.program_repo.create(prog)
        
        self.audit_service.log_action(
            module="training",
            action="create_program",
            entity_type="TrainingProgram",
            entity_id=created.id,
            new_values={"name": created.name}
        )
        
        return created

    def get_all_programs(self) -> List[TrainingProgram]:
        return self.program_repo.get_all()
        
    def update_program(self, data: TrainingProgramDTO) -> Optional[TrainingProgram]:
        if not data.id:
            return None
            
        prog = self.program_repo.get_by_id(data.id)
        if not prog:
            return None
            
        old_values = {"name": prog.name, "status": prog.status}
        
        prog.name = data.name
        prog.description = data.description
        prog.program_type = data.program_type
        prog.start_date = data.start_date
        prog.end_date = data.end_date
        prog.total_hours = data.total_hours
        prog.status = data.status
        
        updated = self.program_repo.update(prog)
        
        self.audit_service.log_action(
            module="training",
            action="update_program",
            entity_type="TrainingProgram",
            entity_id=updated.id,
            old_values=old_values,
            new_values={"name": updated.name, "status": updated.status}
        )
        
        return updated
        
    def delete_program(self, program_id: int) -> bool:
        deleted = self.program_repo.delete(program_id)
        if deleted:
            self.audit_service.log_action(
                module="training", action="delete_program",
                entity_type="TrainingProgram", entity_id=program_id)
        return deleted

    def schedule_session(
        self,
        session_date: date,
        duration_hours: int = 1,
        topic: Optional[str] = None,
        course_id: Optional[int] = None,
        workshop_id: Optional[int] = None,
    ) -> TrainingSession:
        """Create a training session under a course or a workshop.

        A Session belongs to exactly one of (course, workshop); pass the
        relevant id. ``duration_hours`` is the session length in hours.
        """
        session = TrainingSession(
            session_date=session_date,
            duration_hours=duration_hours,
            topic=topic,
            course_id=course_id,
            workshop_id=workshop_id,
        )

        created = self.session_repo.create(session)

        self.audit_service.log_action(
            module="training",
            action="schedule_session",
            entity_type="Session",
            entity_id=created.id,
            new_values={"session_date": session.session_date.isoformat()}
        )

        return created

    # ---------------------------------------------------- courses/workshops
    def get_program_courses(self, program_id: int) -> List[Course]:
        return self.course_repo.get_by_program(program_id)

    def get_program_workshops(self, program_id: int) -> List[Workshop]:
        return self.workshop_repo.get_by_program(program_id)

    def create_course(self, program_id: int, name: str,
                      description: str = None) -> Course:
        course = self.course_repo.create(
            Course(program_id=program_id, name=name, description=description))
        self.audit_service.log_action(
            module="training", action="create_course",
            entity_type="Course", entity_id=course.id)
        return course

    def create_workshop(self, program_id: int, name: str,
                        description: str = None) -> Workshop:
        workshop = self.workshop_repo.create(
            Workshop(program_id=program_id, name=name, description=description))
        self.audit_service.log_action(
            module="training", action="create_workshop",
            entity_type="Workshop", entity_id=workshop.id)
        return workshop

    # ------------------------------------------------------------ sessions
    def get_program_sessions(self, program_id: int) -> List[TrainingSession]:
        return self.session_repo.get_by_program(program_id)

    def update_session(self, session_id: int, session_date: date,
                       duration_hours: int, topic: str = None) -> Optional[TrainingSession]:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            return None
        session.session_date = session_date
        session.duration_hours = duration_hours
        session.topic = topic
        return self.session_repo.update(session)

    def delete_session(self, session_id: int) -> bool:
        deleted = self.session_repo.delete(session_id)
        if deleted:
            self.audit_service.log_action(
                module="training", action="delete_session",
                entity_type="Session", entity_id=session_id)
        return deleted

    # ------------------------------------------------------------ trainees
    def get_all_trainees(self) -> List[Trainee]:
        # Return ALL trainees ordered by id (the repo's get_all() caps at 100,
        # which would hide the rest after a bulk add of e.g. 500).
        return self.trainee_repo.session.query(Trainee).order_by(Trainee.id).all()

    def create_trainee(self, full_name: str, email: str = None, phone: str = None,
                       organization: str = None) -> Trainee:
        trainee = self.trainee_repo.create(Trainee(
            full_name=full_name, email=email, phone=phone, organization=organization))
        self.audit_service.log_action(
            module="training", action="create_trainee",
            entity_type="Trainee", entity_id=trainee.id)
        return trainee

    def bulk_create_trainees(self, prefix: str, count: int, start: int = 1,
                             organization: str = None) -> int:
        """Create `count` trainees named "<prefix> <n>" (n from `start`), e.g.
        "طالب 1 … طالب 500". Inserted in a single transaction for speed.
        Returns the number created."""
        prefix = (prefix or "").strip() or "متدرب"
        session = self.trainee_repo.session
        trainees = [
            Trainee(full_name=f"{prefix} {start + i}", organization=organization)
            for i in range(count)
        ]
        try:
            session.add_all(trainees)
            session.commit()
        except Exception:
            session.rollback()
            raise
        self.audit_service.log_action(
            module="training", action="bulk_create_trainees", entity_type="Trainee",
            new_values={"count": count, "prefix": prefix, "organization": organization})
        return len(trainees)

    def import_trainees(self, records) -> int:
        """Create trainees from imported rows (dicts with full_name / email /
        phone / organization). Rows without a name are skipped. One transaction.
        Returns the number created."""
        session = self.trainee_repo.session
        objs = []
        for r in records:
            name = (r.get("full_name") or "").strip()
            if not name:
                continue
            objs.append(Trainee(
                full_name=name, email=r.get("email") or None,
                phone=r.get("phone") or None, organization=r.get("organization") or None))
        if not objs:
            return 0
        session.add_all(objs)
        session.commit()
        self.audit_service.log_action(
            module="training", action="import_trainees", entity_type="Trainee",
            new_values={"count": len(objs)})
        return len(objs)

    # ---------------------------------------------------------- attendance
    def get_session_attendances(self, session_id: int) -> List[SessionAttendance]:
        return self.attendance_repo.get_by_session(session_id)

    def record_attendance(self, session_id: int, trainee_id: int,
                          is_present: bool, notes: str = None) -> SessionAttendance:
        """Create or update the attendance record for a trainee in a session."""
        existing = [
            a for a in self.attendance_repo.get_by_session(session_id)
            if a.trainee_id == trainee_id
        ]
        if existing:
            record = existing[0]
            record.is_present = is_present
            record.notes = notes
            return self.attendance_repo.update(record)
        return self.attendance_repo.create(SessionAttendance(
            session_id=session_id, trainee_id=trainee_id,
            is_present=is_present, notes=notes))
