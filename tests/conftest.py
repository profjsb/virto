"""
Pytest configuration and shared fixtures.
"""

import os
from datetime import datetime
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.app import app
from src.db import Base
from src.db.models import Role, User, UserRole
from src.services.auth import hash_password

# Use file-based SQLite for tests to avoid connection issues
TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
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

    # Clean up test database file
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    TestSessionLocal = sessionmaker(  # noqa: N806
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
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)  # noqa: N806
    src.db.SessionLocal = TestSessionLocal

    with TestClient(app) as test_client:
        yield test_client

    # Restore original SessionLocal
    src.db.SessionLocal = original_sessionlocal


@pytest.fixture(scope="function")
def test_roles(test_engine) -> dict:
    """Create test roles and return their IDs."""
    TestSessionLocal = sessionmaker(  # noqa: N806
        autocommit=False, autoflush=False, bind=test_engine
    )
    session = TestSessionLocal()
    try:
        roles_data = ["admin", "approver", "engineer", "growth", "viewer"]
        role_ids = {}
        for role_name in roles_data:
            role = Role(name=role_name)
            session.add(role)
            session.flush()  # Get the ID
            role_ids[role_name] = role.id
        session.commit()
        return role_ids
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_user(test_engine, test_roles) -> int:
    """Create a test user with engineer role and return user ID."""
    TestSessionLocal = sessionmaker(  # noqa: N806
        autocommit=False, autoflush=False, bind=test_engine
    )
    session = TestSessionLocal()
    try:
        user = User(
            email="test@example.com",
            password_hash=hash_password("testpass"),
            is_admin=False,
            created_at=datetime.utcnow(),
        )
        session.add(user)
        session.flush()  # Get the ID

        # Add engineer role
        user_role = UserRole(user_id=user.id, role_id=test_roles["engineer"])
        session.add(user_role)
        session.commit()

        return user.id
    finally:
        session.close()


@pytest.fixture(scope="function")
def admin_user(test_engine, test_roles) -> int:
    """Create a test admin user and return user ID."""
    TestSessionLocal = sessionmaker(  # noqa: N806
        autocommit=False, autoflush=False, bind=test_engine
    )
    session = TestSessionLocal()
    try:
        user = User(
            email="admin@example.com",
            password_hash=hash_password("adminpass"),
            is_admin=True,
            created_at=datetime.utcnow(),
        )
        session.add(user)
        session.flush()  # Get the ID

        # Add admin role
        user_role = UserRole(user_id=user.id, role_id=test_roles["admin"])
        session.add(user_role)
        session.commit()

        return user.id
    finally:
        session.close()


@pytest.fixture(scope="function")
def auth_token(client, test_user) -> str:
    """Get an auth token for test user."""
    response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "testpass"}
    )
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def admin_auth_token(client, admin_user) -> str:
    """Get an auth token for admin user."""
    response = client.post(
        "/auth/login", json={"email": "admin@example.com", "password": "adminpass"}
    )
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def sample_policy():
    """Sample policy data for testing."""
    return {
        "version": "1.0",
        "spend_thresholds": {"auto_approve_usd": 100.0, "monthly_budget_usd": 10000.0},
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
