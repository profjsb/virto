"""
Tests for service layer components.
"""

import os

import pytest

from src.services.auth import hash_password, verify_password
from src.services.policy import spend_threshold
from src.services.notion_client import search_workspace, list_pages, create_page


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


@pytest.mark.unit
def test_notion_mock_search():
    """Test Notion search in mock mode."""
    # Set mock mode
    os.environ["NOTION_MOCK"] = "true"

    results = search_workspace("test query", limit=5)

    # Should return mock data
    assert isinstance(results, list)
    assert len(results) > 0
    assert "title" in results[0]

    # Clean up
    del os.environ["NOTION_MOCK"]


@pytest.mark.unit
def test_notion_mock_list_pages():
    """Test Notion list pages in mock mode."""
    os.environ["NOTION_MOCK"] = "true"

    pages = list_pages(limit=10)

    assert isinstance(pages, list)
    assert len(pages) > 0
    assert "id" in pages[0]
    assert "title" in pages[0]

    del os.environ["NOTION_MOCK"]


@pytest.mark.unit
def test_notion_mock_create_page():
    """Test Notion create page in mock mode."""
    os.environ["NOTION_MOCK"] = "true"

    page = create_page(
        title="Test Page",
        content="# Test Content\n\nThis is a test."
    )

    assert isinstance(page, dict)
    assert "id" in page
    assert page["title"] == "Test Page"

    del os.environ["NOTION_MOCK"]
