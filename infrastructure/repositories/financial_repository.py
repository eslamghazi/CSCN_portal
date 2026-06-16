from typing import List
from infrastructure.repositories.base_repository_impl import SQLAlchemyRepository
from domain.entities.financial import Revenue, Expense, BudgetItem, FiscalYear
from sqlalchemy.orm import Session

class FiscalYearRepository(SQLAlchemyRepository[FiscalYear]):
    def __init__(self, session: Session):
        super().__init__(session, FiscalYear)

class RevenueRepository(SQLAlchemyRepository[Revenue]):
    def __init__(self, session: Session):
        super().__init__(session, Revenue)

class ExpenseRepository(SQLAlchemyRepository[Expense]):
    def __init__(self, session: Session):
        super().__init__(session, Expense)

class BudgetItemRepository(SQLAlchemyRepository[BudgetItem]):
    def __init__(self, session: Session):
        super().__init__(session, BudgetItem)

    def get_by_fiscal_year(self, fiscal_year_id: int) -> List[BudgetItem]:
        return self.session.query(BudgetItem).filter(
            BudgetItem.fiscal_year_id == fiscal_year_id).all()
