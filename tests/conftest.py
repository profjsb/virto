"""
Pytest configuration and shared fixtures.
"""
import os
import pytest
from datetime import datetime
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.app import app
from src.db import Base, SessionLocal
from src.db.models import User, Role, UserRole
from src.services.auth import hash_password


# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Import models to ensure they're registered
    from src.db import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    TestSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(test_engine) -> TestClient:
    """Create a test client with database override."""
    # Patch SessionLocal in the db module
    import src.db
    original_sessionlocal = src.db.SessionLocal
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    src.db.SessionLocal = TestSessionLocal

    with TestClient(app) as test_client:
        yield test_client

    # Restore original SessionLocal
    src.db.SessionLocal = original_sessionlocal


@pytest.fixture(scope="function")
def test_roles(db_session) -> dict:
    """Create test roles."""
    roles_data = ["admin", "approver", "engineer", "growth", "viewer"]
    roles = {}
    for role_name in roles_data:
        role = Role(name=role_name)
        db_session.add(role)
        roles[role_name] = role
    db_session.commit()
    return roles


@pytest.fixture(scope="function")
def test_user(db_session, test_roles) -> User:
    """Create a test user with engineer role."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("testpass"),
        is_admin=False,
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Add engineer role
    user_role = UserRole(user_id=user.id, role_id=test_roles["engineer"].id)
    db_session.add(user_role)
    db_session.commit()

    return user


@pytest.fixture(scope="function")
def admin_user(db_session, test_roles) -> User:
    """Create a test admin user."""
    user = User(
        email="admin@example.com",
        password_hash=hash_password("adminpass"),
        is_admin=True,
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Add admin role
    user_role = UserRole(user_id=user.id, role_id=test_roles["admin"].id)
    db_session.add(user_role)
    db_session.commit()

    return user


@pytest.fixture(scope="function")
def auth_token(client, test_user) -> str:
    """Get an auth token for test user."""
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "testpass"}
    )
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def admin_auth_token(client, admin_user) -> str:
    """Get an auth token for admin user."""
    response = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "adminpass"}
    )
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def sample_policy():
    """Sample policy data for testing."""
    return {
        "version": "1.0",
        "spend_thresholds": {
            "auto_approve_usd": 100.0,
            "monthly_budget_usd": 10000.0
        }
    }


# Environment variable fixtures
@pytest.fixture(scope="function", autouse=True)
def test_env_vars(monkeypatch):
    """Set test environment variables."""
    monkeypatch.setenv("JWT_SECRET", "test-secret-key-for-testing-only")
    monkeypatch.setenv("ALLOW_SIGNUP", "true")
    monkeypatch.setenv("STORE_TO_S3", "false")
    # Don't set real API keys in tests by default
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("LINEAR_API_KEY", raising=False)
