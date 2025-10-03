"""
Tests for authentication and authorization.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_health_endpoint(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.unit
def test_register_user(client: TestClient, test_roles):
    """Test user registration."""
    response = client.post(
        "/auth/register", json={"email": "newuser@example.com", "password": "securepass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "password" not in data


@pytest.mark.unit
def test_login_success(client: TestClient, test_user):
    """Test successful login."""
    response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "testpass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.unit
def test_login_wrong_password(client: TestClient, test_user):
    """Test login with wrong password."""
    response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401


@pytest.mark.unit
def test_login_nonexistent_user(client: TestClient, test_roles):
    """Test login with non-existent user."""
    response = client.post(
        "/auth/login", json={"email": "nonexistent@example.com", "password": "somepassword"}
    )
    assert response.status_code == 401
