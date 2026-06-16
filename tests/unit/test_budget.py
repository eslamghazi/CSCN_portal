from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from infrastructure.repositories.financial_repository import (
    RevenueRepository, ExpenseRepository, BudgetItemRepository, FiscalYearRepository,
)
from application.services.financial_service import (
    FinancialService, FiscalYearDTO, BudgetItemDTO, TransactionDTO,
)


def _service(db_session, audit_service):
    return FinancialService(
        RevenueRepository(db_session), ExpenseRepository(db_session),
        BudgetItemRepository(db_session), audit_service,
        fiscal_year_repo=FiscalYearRepository(db_session),
    )


def test_fiscal_year_crud(db_session, audit_service):
    svc = _service(db_session, audit_service)
    fy = svc.create_fiscal_year(FiscalYearDTO(
        name="2026", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)))
    assert len(svc.list_fiscal_years()) == 1
    updated = svc.update_fiscal_year(FiscalYearDTO(
        id=fy.id, name="2026-محدثة", start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31), status="closed"))
    assert updated.name == "2026-محدثة" and updated.status == "closed"


def test_budget_item_crud_and_usage(db_session, audit_service):
    svc = _service(db_session, audit_service)
    fy = svc.create_fiscal_year(FiscalYearDTO(
        name="2026", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)))
    item = svc.create_budget_item(BudgetItemDTO(
        fiscal_year_id=fy.id, name="بند عام", allocated_amount=1000))
    assert len(svc.list_budget_items(fy.id)) == 1

    # charge an expense to the budget item -> used amount reflects it
    svc.add_transaction(TransactionDTO(
        transaction_type="expense", amount=300, date=date(2026, 2, 1),
        description="مصروف", budget_id=item.id))
    assert svc.budget_item_used(item.id) == 300.0

    # FK-aware: a budget item that has expenses cannot be deleted
    with pytest.raises(IntegrityError):
        svc.delete_budget_item(item.id)

    # a fresh budget item with no expenses can be deleted
    fresh = svc.create_budget_item(BudgetItemDTO(
        fiscal_year_id=fy.id, name="بند فارغ", allocated_amount=0))
    assert svc.delete_budget_item(fresh.id) is True
