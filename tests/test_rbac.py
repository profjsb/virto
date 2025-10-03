"""
Tests for role-based access control.
"""

import pytest


@pytest.mark.unit
def test_assign_role_to_user(client, admin_auth_token, test_user, db_session, test_roles):
    """Test that admin can assign roles to users."""
    from src.db.models import User

    response = client.post(
        "/auth/assign-role",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
        json={"user_id": test_user, "role": "growth"},
    )
    assert response.status_code == 200

    # Verify role was assigned by fetching user from database
    user = db_session.get(User, test_user)
    db_session.refresh(user)
    role_names = [r.name for r in user.roles]
    assert "growth" in role_names


@pytest.mark.unit
def test_user_has_initial_role(test_user, db_session):
    """Test that test user has engineer role."""
    from src.db.models import User

    user = db_session.get(User, test_user)
    role_names = [r.name for r in user.roles]
    assert "engineer" in role_names


@pytest.mark.unit
def test_admin_user_has_admin_role(admin_user, db_session):
    """Test that admin user has admin role."""
    from src.db.models import User

    user = db_session.get(User, admin_user)
    role_names = [r.name for r in user.roles]
    assert "admin" in role_names
    assert user.is_admin is True
