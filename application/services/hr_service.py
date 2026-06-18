from typing import List, Optional
from pydantic import BaseModel
from datetime import date
from infrastructure.repositories.hr_repository import EmployeeRepository, JobPositionRepository
from domain.entities.employee import (
    Employee, Position, Qualification, ExperienceRecord, EmployeeEvaluation
)
from application.services.audit_service import AuditService

class EmployeeDTO(BaseModel):
    id: Optional[int] = None
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    position_id: Optional[int] = None
    hire_date: Optional[date] = None
    status: str = "active"

class HRService:
    def __init__(
        self,
        employee_repo: EmployeeRepository,
        position_repo: JobPositionRepository,
        audit_service: AuditService
    ):
        self.employee_repo = employee_repo
        self.position_repo = position_repo
        self.audit_service = audit_service
        
    def add_employee(self, data: EmployeeDTO) -> Employee:
        emp = Employee(
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            position_id=data.position_id,
            hire_date=data.hire_date,
            status=data.status
        )
        
        created = self.employee_repo.create(emp)
        
        self.audit_service.log_action(
            module="hr",
            action="add_employee",
            entity_type="Employee",
            entity_id=created.id,
            new_values={"name": created.full_name}
        )
        
        return created

    def get_all_employees(self) -> List[Employee]:
        return self.employee_repo.get_all()
        
    def get_all_positions(self) -> List[Position]:
        return self.position_repo.get_all()

    def create_position(self, title: str, description: str = None) -> Position:
        return self.position_repo.create(Position(title=title, description=description))

    def update_position(self, position_id: int, title: str,
                        description: str = None) -> Optional[Position]:
        position = self.position_repo.get_by_id(position_id)
        if not position:
            return None
        position.title = title
        position.description = description
        return self.position_repo.update(position)

    def delete_position(self, position_id: int) -> bool:
        return self.position_repo.delete(position_id)
        
    def update_employee(self, data: EmployeeDTO) -> Optional[Employee]:
        if not data.id:
            return None
            
        emp = self.employee_repo.get_by_id(data.id)
        if not emp:
            return None
            
        old_values = {"name": emp.full_name, "status": emp.status}
        
        emp.full_name = data.full_name
        emp.email = data.email
        emp.phone = data.phone
        emp.position_id = data.position_id
        emp.hire_date = data.hire_date
        emp.status = data.status
        
        updated = self.employee_repo.update(emp)
        
        self.audit_service.log_action(
            module="hr",
            action="update_employee",
            entity_type="Employee",
            entity_id=updated.id,
            old_values=old_values,
            new_values={"name": updated.full_name, "status": updated.status}
        )

        return updated

    def delete_employee(self, employee_id: int) -> bool:
        deleted = self.employee_repo.delete(employee_id)
        if deleted:
            self.audit_service.log_action(
                module="hr", action="delete_employee",
                entity_type="Employee", entity_id=employee_id)
        return deleted

    # ---------------------------------------------------------------- helpers
    @property
    def _session(self):
        return self.employee_repo.session

    def _add(self, entity, action: str, entity_type: str):
        session = self._session
        try:
            session.add(entity)
            session.commit()
            session.refresh(entity)
        except Exception:
            session.rollback()
            raise
        self.audit_service.log_action(
            module="hr", action=action, entity_type=entity_type, entity_id=entity.id)
        return entity

    def _delete(self, model, entity_id: int, action: str) -> bool:
        session = self._session
        obj = session.get(model, entity_id)
        if not obj:
            return False
        try:
            session.delete(obj)
            session.commit()
        except Exception:
            session.rollback()
            raise
        self.audit_service.log_action(
            module="hr", action=action, entity_type=model.__name__, entity_id=entity_id)
        return True

    def _update(self, model, entity_id: int, fields: dict, action: str):
        session = self._session
        obj = session.get(model, entity_id)
        if not obj:
            return None
        try:
            for key, value in fields.items():
                setattr(obj, key, value)
            session.commit()
            session.refresh(obj)
        except Exception:
            session.rollback()
            raise
        self.audit_service.log_action(
            module="hr", action=action, entity_type=model.__name__, entity_id=entity_id)
        return obj

    # ------------------------------------------------------- qualifications
    def get_qualifications(self, employee_id: int) -> List[Qualification]:
        return (self._session.query(Qualification)
                .filter(Qualification.employee_id == employee_id).all())

    def add_qualification(self, employee_id: int, degree: str, institution: str,
                          year_obtained: Optional[int] = None) -> Qualification:
        return self._add(
            Qualification(employee_id=employee_id, degree=degree,
                          institution=institution, year_obtained=year_obtained),
            "add_qualification", "Qualification")

    def update_qualification(self, qualification_id: int, degree: str, institution: str,
                             year_obtained: Optional[int] = None):
        return self._update(
            Qualification, qualification_id,
            {"degree": degree, "institution": institution, "year_obtained": year_obtained},
            "update_qualification")

    def delete_qualification(self, qualification_id: int) -> bool:
        return self._delete(Qualification, qualification_id, "delete_qualification")

    # --------------------------------------------------------- experience
    def get_experience(self, employee_id: int) -> List[ExperienceRecord]:
        return (self._session.query(ExperienceRecord)
                .filter(ExperienceRecord.employee_id == employee_id).all())

    def add_experience(self, employee_id: int, job_title: str, company: str,
                       start_date: Optional[date] = None,
                       end_date: Optional[date] = None,
                       description: Optional[str] = None) -> ExperienceRecord:
        return self._add(
            ExperienceRecord(employee_id=employee_id, job_title=job_title,
                             company=company, start_date=start_date,
                             end_date=end_date, description=description),
            "add_experience", "ExperienceRecord")

    def update_experience(self, experience_id: int, job_title: str, company: str,
                          start_date: Optional[date] = None,
                          end_date: Optional[date] = None,
                          description: Optional[str] = None):
        return self._update(
            ExperienceRecord, experience_id,
            {"job_title": job_title, "company": company, "start_date": start_date,
             "end_date": end_date, "description": description},
            "update_experience")

    def delete_experience(self, experience_id: int) -> bool:
        return self._delete(ExperienceRecord, experience_id, "delete_experience")

    # --------------------------------------------------------- evaluations
    def get_evaluations(self, employee_id: int) -> List[EmployeeEvaluation]:
        return (self._session.query(EmployeeEvaluation)
                .filter(EmployeeEvaluation.employee_id == employee_id).all())

    def add_evaluation(self, employee_id: int, evaluation_date: date,
                       score: Optional[float] = None,
                       notes: Optional[str] = None) -> EmployeeEvaluation:
        return self._add(
            EmployeeEvaluation(employee_id=employee_id, evaluation_date=evaluation_date,
                               score=score, notes=notes),
            "add_evaluation", "EmployeeEvaluation")

    def update_evaluation(self, evaluation_id: int, evaluation_date: date,
                          score: Optional[float] = None,
                          notes: Optional[str] = None):
        return self._update(
            EmployeeEvaluation, evaluation_id,
            {"evaluation_date": evaluation_date, "score": score, "notes": notes},
            "update_evaluation")

    def delete_evaluation(self, evaluation_id: int) -> bool:
        return self._delete(EmployeeEvaluation, evaluation_id, "delete_evaluation")

