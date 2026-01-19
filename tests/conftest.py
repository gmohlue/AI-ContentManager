"""Pytest configuration and fixtures."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from contentmanager.database.models import Base


@pytest.fixture(scope="function")
def db_engine():
    """Create an in-memory SQLite database for testing.

    Uses StaticPool and check_same_thread=False to allow
    the connection to be shared across threads (needed for TestClient).
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a database session for testing."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def db_session_factory(db_engine):
    """Create a session factory for API endpoint tests.

    This fixture returns a factory function that creates new sessions,
    which is needed for the FastAPI dependency override pattern.
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    return SessionLocal
