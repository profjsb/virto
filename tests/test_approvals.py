"""
Tests for approval workflows.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_submit_approval_under_threshold(client: TestClient, auth_token, db_session):
    """Test submitting approval request under threshold auto-approves."""
    response = client.post(
        "/approvals/submit",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"description": "Small expense", "amount_usd": 25.0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["auto_approved", "approved"]
    assert data["amount_usd"] == 25.0


@pytest.mark.integration
def test_submit_approval_over_threshold(client: TestClient, auth_token, db_session):
    """Test submitting approval request over threshold requires approval."""
    response = client.post(
        "/approvals/submit",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"description": "Large expense", "amount_usd": 500.0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["amount_usd"] == 500.0


@pytest.mark.integration
def test_list_approvals(client: TestClient, auth_token, db_session):
    """Test listing approval requests."""
    # Create some approvals
    client.post(
        "/approvals/submit",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"description": "Test 1", "amount_usd": 25.0},
    )
    client.post(
        "/approvals/submit",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"description": "Test 2", "amount_usd": 200.0},
    )

    response = client.get("/ops/approvals", headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code == 200
    approvals = response.json()
    assert len(approvals) >= 2
