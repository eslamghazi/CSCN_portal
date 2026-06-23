from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import date
from infrastructure.repositories.financial_repository import (
    RevenueRepository, ExpenseRepository, BudgetItemRepository, FiscalYearRepository,
)
from domain.entities.financial import Revenue, Expense, BudgetItem, FiscalYear
from application.services.audit_service import AuditService

class TransactionDTO(BaseModel):
    id: Optional[int] = None
    transaction_type: str  # 'revenue' or 'expense'
    amount: float
    date: date
    description: str
    source: Optional[str] = None
    category: Optional[str] = None
    reference_number: Optional[str] = None
    budget_id: Optional[int] = None

class FiscalYearDTO(BaseModel):
    id: Optional[int] = None
    name: str
    start_date: date
    end_date: date
    status: str = "active"

class BudgetItemDTO(BaseModel):
    id: Optional[int] = None
    fiscal_year_id: int
    name: str
    allocated_amount: float = 0.0
    description: Optional[str] = None

class FinancialService:
    def __init__(
        self,
        revenue_repo: RevenueRepository,
        expense_repo: ExpenseRepository,
        budget_item_repo: BudgetItemRepository,
        audit_service: AuditService,
        fiscal_year_repo: FiscalYearRepository = None,
    ):
        self.revenue_repo = revenue_repo
        self.expense_repo = expense_repo
        self.budget_item_repo = budget_item_repo
        self.audit_service = audit_service
        self.fiscal_year_repo = fiscal_year_repo
        
    def _get_or_create_default_fiscal_year(self) -> FiscalYear:
        """Return an existing fiscal year (active first) or create one for the
        current calendar year. Avoids dangling foreign keys when revenues are
        added before any fiscal year has been configured."""
        session = self.revenue_repo.session
        fy = session.query(FiscalYear).filter(FiscalYear.status == "active").first()
        if fy is None:
            fy = session.query(FiscalYear).order_by(FiscalYear.id).first()
        if fy is None:
            today = date.today()
            fy = FiscalYear(
                name=str(today.year),
                start_date=date(today.year, 1, 1),
                end_date=date(today.year, 12, 31),
                status="active",
            )
            session.add(fy)
            session.commit()
            session.refresh(fy)
        return fy

    def _get_or_create_default_budget_item(self) -> BudgetItem:
        """Return an existing budget item or create a general one bound to the
        default fiscal year. Avoids dangling foreign keys for expenses."""
        session = self.budget_item_repo.session
        bi = session.query(BudgetItem).order_by(BudgetItem.id).first()
        if bi is None:
            fy = self._get_or_create_default_fiscal_year()
            bi = BudgetItem(
                fiscal_year_id=fy.id,
                name="بند عام",
                allocated_amount=0,
                description="بند ميزانية افتراضي للمصروفات العامة",
            )
            session.add(bi)
            session.commit()
            session.refresh(bi)
        return bi

    def add_transaction(self, data: TransactionDTO) -> Any:
        if data.transaction_type == "revenue":
            # data.budget_id, when supplied for a revenue, is an explicit fiscal_year_id.
            fiscal_year_id = data.budget_id or self._get_or_create_default_fiscal_year().id
            tx = Revenue(
                fiscal_year_id=fiscal_year_id,
                amount=data.amount,
                revenue_date=data.date,
                source=data.source or data.category or "General",
                description=data.description
            )
            created = self.revenue_repo.create(tx)
        else:
            # data.budget_id, when supplied for an expense, is an explicit budget_item_id.
            budget_item_id = data.budget_id or self._get_or_create_default_budget_item().id
            tx = Expense(
                budget_item_id=budget_item_id,
                amount=data.amount,
                expense_date=data.date,
                description=data.description,
                receipt_number=data.reference_number
            )
            created = self.expense_repo.create(tx)
        
        self.audit_service.log_action(
            module="financial",
            action="add_transaction",
            entity_type="Transaction",
            entity_id=created.id,
            new_values={"amount": float(created.amount)}
        )
        return created

    def get_all_transactions(self) -> List[Any]:
        # Return combined list
        revs = self.revenue_repo.get_all()
        exps = self.expense_repo.get_all()
        # Mocking a unified object for the UI table
        combined = []
        for r in revs:
            setattr(r, 'transaction_type', 'revenue')
            setattr(r, 'date', r.revenue_date)
            setattr(r, 'category', r.source)
            combined.append(r)
        for e in exps:
            setattr(e, 'transaction_type', 'expense')
            setattr(e, 'date', e.expense_date)
            setattr(e, 'category', 'Expense')
            combined.append(e)
        return sorted(combined, key=lambda x: x.date, reverse=True)
        
    def delete_revenue(self, revenue_id: int) -> bool:
        deleted = self.revenue_repo.delete(revenue_id)
        if deleted:
            self.audit_service.log_action(
                module="financial", action="delete_revenue",
                entity_type="Revenue", entity_id=revenue_id)
        return deleted

    def delete_expense(self, expense_id: int) -> bool:
        deleted = self.expense_repo.delete(expense_id)
        if deleted:
            self.audit_service.log_action(
                module="financial", action="delete_expense",
                entity_type="Expense", entity_id=expense_id)
        return deleted

    def get_financial_summary(self) -> Dict[str, float]:
        txs = self.get_all_transactions()
        total_rev = sum([float(t.amount) for t in txs if getattr(t, 'transaction_type') == "revenue"])
        total_exp = sum([float(t.amount) for t in txs if getattr(t, 'transaction_type') == "expense"])
        
        return {
            "total_revenue": total_rev,
            "total_expense": total_exp,
            "balance": total_rev - total_exp
        }

    # ----------------------------------------------------- fiscal years
    def list_fiscal_years(self) -> List[FiscalYear]:
        return self.fiscal_year_repo.get_all()

    def create_fiscal_year(self, data: FiscalYearDTO) -> FiscalYear:
        fy = self.fiscal_year_repo.create(FiscalYear(
            name=data.name, start_date=data.start_date,
            end_date=data.end_date, status=data.status))
        self.audit_service.log_action(
            module="financial", action="create_fiscal_year",
            entity_type="FiscalYear", entity_id=fy.id)
        return fy

    def update_fiscal_year(self, data: FiscalYearDTO) -> Optional[FiscalYear]:
        if not data.id:
            return None
        fy = self.fiscal_year_repo.get_by_id(data.id)
        if not fy:
            return None
        fy.name, fy.start_date, fy.end_date, fy.status = (
            data.name, data.start_date, data.end_date, data.status)
        return self.fiscal_year_repo.update(fy)

    def delete_fiscal_year(self, fiscal_year_id: int) -> bool:
        deleted = self.fiscal_year_repo.delete(fiscal_year_id)
        if deleted:
            self.audit_service.log_action(
                module="financial", action="delete_fiscal_year",
                entity_type="FiscalYear", entity_id=fiscal_year_id)
        return deleted

    # ----------------------------------------------------- budget items
    def list_budget_items(self, fiscal_year_id: int) -> List[BudgetItem]:
        return self.budget_item_repo.get_by_fiscal_year(fiscal_year_id)

    def budget_item_used(self, budget_item_id: int) -> float:
        """Sum of expenses charged to a budget item."""
        expenses = [
            e for e in self.expense_repo.get_all() if e.budget_item_id == budget_item_id
        ]
        return float(sum(float(e.amount) for e in expenses))

    def create_budget_item(self, data: BudgetItemDTO) -> BudgetItem:
        item = self.budget_item_repo.create(BudgetItem(
            fiscal_year_id=data.fiscal_year_id, name=data.name,
            allocated_amount=data.allocated_amount, description=data.description))
        self.audit_service.log_action(
            module="financial", action="create_budget_item",
            entity_type="BudgetItem", entity_id=item.id)
        return item

    def update_budget_item(self, data: BudgetItemDTO) -> Optional[BudgetItem]:
        if not data.id:
            return None
        item = self.budget_item_repo.get_by_id(data.id)
        if not item:
            return None
        item.name = data.name
        item.allocated_amount = data.allocated_amount
        item.description = data.description
        return self.budget_item_repo.update(item)

    def delete_budget_item(self, budget_item_id: int) -> bool:
        deleted = self.budget_item_repo.delete(budget_item_id)
        if deleted:
            self.audit_service.log_action(
                module="financial", action="delete_budget_item",
                entity_type="BudgetItem", entity_id=budget_item_id)
        return deleted

