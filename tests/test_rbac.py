"""
Tests for role-based access control.
"""
import pytest
from src.db.models import User, UserRole


@pytest.mark.unit
def test_assign_role_to_user(client, admin_auth_token, test_user, db_session, test_roles):
    """Test that admin can assign roles to users."""
    response = client.post(
        "/auth/assign-role",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
        json={"user_id": test_user.id, "role": "growth"}
    )
    assert response.status_code == 200

    # Verify role was assigned
    db_session.refresh(test_user)
    role_names = [r.name for r in test_user.roles]
    assert "growth" in role_names


@pytest.mark.unit
def test_user_has_initial_role(test_user):
    """Test that test user has engineer role."""
    role_names = [r.name for r in test_user.roles]
    assert "engineer" in role_names


@pytest.mark.unit
def test_admin_user_has_admin_role(admin_user):
    """Test that admin user has admin role."""
    role_names = [r.name for r in admin_user.roles]
    assert "admin" in role_names
    assert admin_user.is_admin is True
