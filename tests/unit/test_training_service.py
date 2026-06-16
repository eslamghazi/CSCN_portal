from datetime import date


from domain.entities.training import Course, Workshop
from infrastructure.repositories.training_repository import (
    TrainingProgramRepository, TrainingSessionRepository, AttendanceRepository,
    CourseRepository, WorkshopRepository, TraineeRepository,
)
from application.services.training_service import TrainingService, TrainingProgramDTO


def _service(db_session, audit_service):
    return TrainingService(
        TrainingProgramRepository(db_session), TrainingSessionRepository(db_session),
        AttendanceRepository(db_session), audit_service,
        course_repo=CourseRepository(db_session),
        workshop_repo=WorkshopRepository(db_session),
        trainee_repo=TraineeRepository(db_session),
    )


def test_courses_workshops_sessions_attendance(db_session, audit_service):
    svc = _service(db_session, audit_service)
    p = svc.create_program(TrainingProgramDTO(name="P", program_type="course"))
    course = svc.create_course(p.id, "مقرر 1", "وصف")
    svc.create_workshop(p.id, "ورشة 1")
    assert len(svc.get_program_courses(p.id)) == 1
    assert len(svc.get_program_workshops(p.id)) == 1

    s = svc.schedule_session(session_date=date(2026, 3, 1), duration_hours=2,
                             topic="مقدمة", course_id=course.id)
    assert len(svc.get_program_sessions(p.id)) == 1
    svc.update_session(s.id, date(2026, 3, 2), 3, "محدث")
    assert svc.get_program_sessions(p.id)[0].duration_hours == 3

    t = svc.create_trainee("متدرب", organization="جهة")
    assert len(svc.get_all_trainees()) == 1
    svc.record_attendance(s.id, t.id, True, "حاضر")
    atts = svc.get_session_attendances(s.id)
    assert len(atts) == 1 and atts[0].is_present is True
    # idempotent update
    svc.record_attendance(s.id, t.id, False)
    atts = svc.get_session_attendances(s.id)
    assert len(atts) == 1 and atts[0].is_present is False

    assert svc.delete_session(s.id) is True
    assert svc.get_program_sessions(p.id) == []


def test_get_by_program_filters_via_course_and_workshop(db_session, audit_service):
    svc = _service(db_session, audit_service)
    p1 = svc.create_program(TrainingProgramDTO(name="P1", program_type="course"))
    p2 = svc.create_program(TrainingProgramDTO(name="P2", program_type="course"))
    c1 = Course(program_id=p1.id, name="c1")
    w1 = Workshop(program_id=p1.id, name="w1")
    c2 = Course(program_id=p2.id, name="c2")
    db_session.add_all([c1, w1, c2])
    db_session.commit()

    svc.schedule_session(session_date=date(2026, 3, 1), course_id=c1.id, duration_hours=2)
    svc.schedule_session(session_date=date(2026, 3, 2), workshop_id=w1.id, duration_hours=1)
    svc.schedule_session(session_date=date(2026, 3, 3), course_id=c2.id, duration_hours=1)

    assert len(svc.session_repo.get_by_program(p1.id)) == 2
    assert len(svc.session_repo.get_by_program(p2.id)) == 1


def test_schedule_session_persists_fields(db_session, audit_service):
    svc = _service(db_session, audit_service)
    p = svc.create_program(TrainingProgramDTO(name="P", program_type="course"))
    c = Course(program_id=p.id, name="c")
    db_session.add(c)
    db_session.commit()

    s = svc.schedule_session(session_date=date(2026, 3, 1), duration_hours=4, topic="t", course_id=c.id)
    assert s.duration_hours == 4
    assert s.topic == "t"
    assert s.course_id == c.id
