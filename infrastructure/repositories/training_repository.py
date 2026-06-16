from typing import List
from sqlalchemy import or_
from infrastructure.repositories.base_repository_impl import SQLAlchemyRepository
from domain.entities.training import (
    TrainingProgram,
    Session as TrainingSession,
    SessionAttendance,
    Course,
    Workshop,
    Trainee,
)
from sqlalchemy.orm import Session

class TrainingProgramRepository(SQLAlchemyRepository[TrainingProgram]):
    def __init__(self, session: Session):
        super().__init__(session, TrainingProgram)

class CourseRepository(SQLAlchemyRepository[Course]):
    def __init__(self, session: Session):
        super().__init__(session, Course)

    def get_by_program(self, program_id: int) -> List[Course]:
        return self.session.query(Course).filter(Course.program_id == program_id).all()

class WorkshopRepository(SQLAlchemyRepository[Workshop]):
    def __init__(self, session: Session):
        super().__init__(session, Workshop)

    def get_by_program(self, program_id: int) -> List[Workshop]:
        return self.session.query(Workshop).filter(
            Workshop.program_id == program_id).all()

class TraineeRepository(SQLAlchemyRepository[Trainee]):
    def __init__(self, session: Session):
        super().__init__(session, Trainee)

class TrainingSessionRepository(SQLAlchemyRepository[TrainingSession]):
    def __init__(self, session: Session):
        super().__init__(session, TrainingSession)
        
    def get_by_program(self, program_id: int) -> List[TrainingSession]:
        # A session links to a Course or a Workshop, each of which belongs to a
        # TrainingProgram. Resolve both paths and return only this program's sessions.
        course_ids = self.session.query(Course.id).filter(Course.program_id == program_id)
        workshop_ids = self.session.query(Workshop.id).filter(Workshop.program_id == program_id)
        return self.session.query(TrainingSession).filter(
            or_(
                TrainingSession.course_id.in_(course_ids),
                TrainingSession.workshop_id.in_(workshop_ids),
            )
        ).all()

class AttendanceRepository(SQLAlchemyRepository[SessionAttendance]):
    def __init__(self, session: Session):
        super().__init__(session, SessionAttendance)
        
    def get_by_session(self, session_id: int) -> List[SessionAttendance]:
        return self.session.query(SessionAttendance).filter(
            SessionAttendance.session_id == session_id
        ).all()

