"""
Tests for service layer components.
"""

import pytest

from src.services.auth import hash_password, verify_password
from src.services.policy import spend_threshold


@pytest.mark.unit
def test_password_hashing():
    """Test password hashing and verification."""
    password = "mypass123"
    hashed = hash_password(password)

    # Hash should not be the same as password
    assert hashed != password

    # Verification should work
    assert verify_password(password, hashed) is True

    # Wrong password should not verify
    assert verify_password("wrongpassword", hashed) is False


@pytest.mark.unit
def test_password_hash_is_different_each_time():
    """Test that same password produces different hashes (salt)."""
    password = "samepass"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    # Hashes should be different (bcrypt uses salt)
    assert hash1 != hash2

    # But both should verify
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True


@pytest.mark.unit
def test_spend_threshold_extraction(sample_policy):
    """Test extracting spend threshold from policy."""
    threshold = spend_threshold(sample_policy)
    assert threshold == 100.0


@pytest.mark.unit
def test_spend_threshold_missing_policy():
    """Test spend threshold with missing policy."""
    threshold = spend_threshold(None)
    assert threshold == 50.0  # Default value


@pytest.mark.unit
def test_spend_threshold_invalid_policy():
    """Test spend threshold with invalid policy structure."""
    invalid_policy = {"version": "1.0"}  # Missing spending section
    threshold = spend_threshold(invalid_policy)
    assert threshold == 50.0  # Default value
