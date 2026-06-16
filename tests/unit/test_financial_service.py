from datetime import date

from infrastructure.repositories.financial_repository import (
    RevenueRepository, ExpenseRepository, BudgetItemRepository,
)
from application.services.financial_service import FinancialService, TransactionDTO
from domain.entities.financial import FiscalYear, BudgetItem


def _service(db_session, audit_service):
    return FinancialService(
        RevenueRepository(db_session), ExpenseRepository(db_session),
        BudgetItemRepository(db_session), audit_service,
    )


def test_revenue_creates_default_fiscal_year(db_session, audit_service):
    svc = _service(db_session, audit_service)
    rev = svc.add_transaction(TransactionDTO(
        transaction_type="revenue", amount=100, date=date(2026, 1, 1), description="d"))
    assert rev.fiscal_year_id is not None
    assert db_session.query(FiscalYear).count() == 1


def test_expense_creates_default_budget_item(db_session, audit_service):
    svc = _service(db_session, audit_service)
    exp = svc.add_transaction(TransactionDTO(
        transaction_type="expense", amount=50, date=date(2026, 1, 1), description="d"))
    assert exp.budget_item_id is not None
    assert db_session.query(BudgetItem).count() == 1


def test_summary_balances_revenue_minus_expense(db_session, audit_service):
    svc = _service(db_session, audit_service)
    svc.add_transaction(TransactionDTO(
        transaction_type="revenue", amount=1000, date=date(2026, 1, 1), description="r"))
    svc.add_transaction(TransactionDTO(
        transaction_type="expense", amount=400, date=date(2026, 1, 2), description="e"))
    summary = svc.get_financial_summary()
    assert summary == {"total_revenue": 1000.0, "total_expense": 400.0, "balance": 600.0}


def test_default_fiscal_year_reused_across_revenues(db_session, audit_service):
    svc = _service(db_session, audit_service)
    r1 = svc.add_transaction(TransactionDTO(
        transaction_type="revenue", amount=1, date=date(2026, 1, 1), description="a"))
    r2 = svc.add_transaction(TransactionDTO(
        transaction_type="revenue", amount=2, date=date(2026, 1, 2), description="b"))
    assert r1.fiscal_year_id == r2.fiscal_year_id
    assert db_session.query(FiscalYear).count() == 1
