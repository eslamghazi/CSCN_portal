"""Integration tests exercising the SQLAlchemy repositories against a real
(in-memory) database, including generic CRUD and foreign-key enforcement."""
import pytest
from sqlalchemy.exc import IntegrityError

from domain.entities.partnership import Organization
from domain.entities.financial import Expense
from infrastructure.repositories.partnership_repository import PartnershipRepository


def test_base_repository_crud_roundtrip(db_session):
    repo = PartnershipRepository(db_session)
    created = repo.create(Organization(name="جهة"))
    assert created.id is not None
    assert repo.get_by_id(created.id).name == "جهة"
    assert repo.count() == 1

    created.name = "جهة محدثة"
    repo.update(created)
    assert repo.get_by_id(created.id).name == "جهة محدثة"

    assert repo.delete(created.id) is True
    assert repo.get_by_id(created.id) is None
    assert repo.count() == 0


def test_foreign_keys_are_enforced(db_session):
    # budget_item_id references a non-existent budget item -> must fail.
    from datetime import date
    db_session.add(Expense(budget_item_id=9999, amount=10, expense_date=date(2026, 1, 1)))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
