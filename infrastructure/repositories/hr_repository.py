from typing import List
from infrastructure.repositories.base_repository_impl import SQLAlchemyRepository
from domain.entities.employee import Employee, Position
from sqlalchemy.orm import Session

class EmployeeRepository(SQLAlchemyRepository[Employee]):
    def __init__(self, session: Session):
        super().__init__(session, Employee)
        
    def get_active_employees(self) -> List[Employee]:
        return self.session.query(Employee).filter(Employee.status == "active").all()

class JobPositionRepository(SQLAlchemyRepository[Position]):
    def __init__(self, session: Session):
        super().__init__(session, Position)

