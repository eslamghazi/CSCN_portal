"""Shared pytest fixtures: an isolated in-memory SQLite database per test
(with foreign keys enabled, matching the production engine) plus auth reset."""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from database.base import Base
import domain.entities  # noqa: F401  -- registers all models on Base.metadata
from application.services.audit_service import AuditService
from application.services.auth_service import AuthService
from application.context import clear_current_user


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_conn, _rec):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def audit_service(db_session):
    return AuditService(db_session)


@pytest.fixture(autouse=True)
def _reset_current_user():
    """AuthService stores the logged-in user in a contextvar; isolate it per test."""
    clear_current_user()
    yield
    clear_current_user()
