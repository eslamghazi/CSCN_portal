from datetime import date

from infrastructure.repositories.hr_repository import EmployeeRepository, JobPositionRepository
from application.services.hr_service import HRService, EmployeeDTO


def _service(db_session, audit_service):
    return HRService(
        EmployeeRepository(db_session), JobPositionRepository(db_session), audit_service)


def test_qualifications_crud(db_session, audit_service):
    hr = _service(db_session, audit_service)
    emp = hr.add_employee(EmployeeDTO(full_name="موظف"))
    q = hr.add_qualification(emp.id, "بكالوريوس", "جامعة", 2019)
    assert len(hr.get_qualifications(emp.id)) == 1
    assert q.year_obtained == 2019
    assert hr.delete_qualification(q.id) is True
    assert hr.get_qualifications(emp.id) == []


def test_experience_crud(db_session, audit_service):
    hr = _service(db_session, audit_service)
    emp = hr.add_employee(EmployeeDTO(full_name="موظف"))
    x = hr.add_experience(emp.id, "ممرض", "مستشفى", date(2019, 1, 1), date(2022, 1, 1), "ملاحظة")
    assert len(hr.get_experience(emp.id)) == 1
    assert x.company == "مستشفى"
    assert hr.delete_experience(x.id) is True
    assert hr.get_experience(emp.id) == []


def test_evaluations_crud(db_session, audit_service):
    hr = _service(db_session, audit_service)
    emp = hr.add_employee(EmployeeDTO(full_name="موظف"))
    ev = hr.add_evaluation(emp.id, date(2026, 1, 1), 92.5, "ممتاز")
    assert len(hr.get_evaluations(emp.id)) == 1
    assert ev.score == 92.5
    assert hr.delete_evaluation(ev.id) is True
    assert hr.get_evaluations(emp.id) == []


def test_delete_missing_returns_false(db_session, audit_service):
    hr = _service(db_session, audit_service)
    assert hr.delete_qualification(999) is False
