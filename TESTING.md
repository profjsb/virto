# Testing Guide

This document describes the testing infrastructure for the Virtual AI Organization project.

## Overview

The project includes comprehensive testing for both backend (Python/FastAPI) and frontend (React/TypeScript):

- **Backend**: pytest with SQLAlchemy fixtures
- **Frontend**: Vitest + React Testing Library
- **CI/CD**: GitHub Actions workflows
- **Pre-commit**: Automated linting and testing hooks

## Quick Start

```bash
# Install all dependencies
make install

# Run all tests
make test-all

# Run backend tests only
make test-backend

# Run frontend tests only
make test-frontend

# Run tests with coverage
make test-backend-cov
make test-frontend-cov

# Run linters
make lint

# Format code
make format
```

## Backend Testing (pytest)

### Setup

Backend tests use pytest with the following key features:

- In-memory SQLite database for fast tests
- Fixtures for users, roles, and authentication
- TestClient for API endpoint testing
- Markers for categorizing tests (`@pytest.mark.unit`, `@pytest.mark.integration`)

### Running Tests

```bash
# Run all backend tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_auth.py

# Run specific test
uv run pytest tests/test_auth.py::test_login_success

# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Generate coverage report
uv run pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_auth.py             # Authentication tests
├── test_rbac.py             # Role-based access control tests
├── test_approvals.py        # Approval workflow tests
├── test_services.py         # Service layer tests
└── test_orchestration.py    # DAG and orchestration tests
```

### Writing Tests

Example test using fixtures:

```python
import pytest
from fastapi.testclient import TestClient

@pytest.mark.unit
def test_login_success(client: TestClient, test_user):
    """Test successful login."""
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
```

### Available Fixtures

- `client`: FastAPI TestClient with database override
- `db_session`: SQLAlchemy session for test database
- `test_user`: Regular user with engineer role
- `admin_user`: Admin user with admin role
- `test_roles`: All role objects (admin, approver, engineer, growth, viewer)
- `auth_token`: JWT token for test_user
- `admin_auth_token`: JWT token for admin_user
- `sample_policy`: Sample policy data

### Test Markers

```python
@pytest.mark.unit         # Fast, isolated unit tests
@pytest.mark.integration  # Tests requiring database/external services
@pytest.mark.slow         # Long-running tests
@pytest.mark.requires_db  # Tests requiring PostgreSQL
@pytest.mark.requires_llm # Tests requiring LLM API keys
```

## Frontend Testing (Vitest)

### Setup

Frontend tests use Vitest with React Testing Library:

- jsdom environment for DOM simulation
- User event simulation
- Component testing with mocked API calls

### Running Tests

```bash
# Run tests
cd console && npm run test

# Run tests in watch mode
cd console && npm run test -- --watch

# Run tests with UI
cd console && npm run test:ui

# Generate coverage report
cd console && npm run test:coverage
```

### Test Structure

```
console/src/tests/
├── setup.ts          # Test setup and global configuration
├── api.test.ts       # API client tests
└── Login.test.tsx    # Login component tests
```

### Writing Tests

Example component test:

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Login from '../Login';

vi.mock('../api', () => ({
  api: {
    post: vi.fn(),
  },
}));

describe('Login Component', () => {
  it('renders login form', () => {
    render(<Login onAuthed={() => {}} />);
    expect(screen.getByPlaceholderText('Email')).toBeInTheDocument();
  });
});
```

## Integration Tests

Integration tests verify end-to-end workflows and require:

- PostgreSQL database (can use test container)
- Redis (optional, for event streaming tests)
- Real environment variables

```bash
# Setup test database
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/test_db
uv run alembic upgrade head

# Run integration tests
uv run pytest -m integration
```

## Pre-commit Hooks

Pre-commit hooks run automatically before each commit to ensure code quality.

### Installation

```bash
# Install pre-commit hooks
make pre-commit-install

# Or manually
uv run pre-commit install
```

### Manual Execution

```bash
# Run on all files
make pre-commit-run

# Or manually
uv run pre-commit run --all-files
```

### Hooks Included

1. **Trailing whitespace**: Remove trailing whitespace
2. **End of file fixer**: Ensure files end with newline
3. **YAML check**: Validate YAML syntax
4. **JSON check**: Validate JSON syntax
5. **Large files**: Prevent large files from being committed
6. **Merge conflict**: Detect merge conflict markers
7. **Private key detection**: Prevent committing private keys
8. **Ruff linting**: Auto-fix Python linting issues
9. **Ruff formatting**: Format Python code
10. **pytest**: Run backend tests

## Continuous Integration (GitHub Actions)

The project includes a comprehensive CI pipeline in `.github/workflows/test.yml`:

### Jobs

1. **backend-tests**
   - Runs on Ubuntu with PostgreSQL and Redis
   - Linting with ruff
   - Type checking
   - Full pytest suite with coverage
   - Uploads coverage to Codecov

2. **frontend-tests**
   - Node.js 20 environment
   - ESLint linting
   - TypeScript type checking
   - Vitest tests with coverage
   - Uploads coverage to Codecov

3. **integration-tests**
   - Runs after backend and frontend tests pass
   - Full database setup with migrations
   - Integration test suite

### Running CI Locally

```bash
# Run all CI checks locally
make ci

# Or step by step
make lint
make test-all
```

## Coverage Reports

### Backend Coverage

```bash
# Generate HTML coverage report
uv run pytest --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html
```

Coverage configuration in `pyproject.toml`:
- Source: `src/` directory
- Omits: tests, migrations
- Excludes: debugging code, abstract methods

### Frontend Coverage

```bash
# Generate coverage report
cd console && npm run test:coverage

# Reports generated in console/coverage/
```

## Best Practices

### Test Organization

1. **Unit tests**: Test individual functions/methods in isolation
2. **Integration tests**: Test interactions between components
3. **Use fixtures**: Reuse common setup via pytest fixtures
4. **Mock external services**: Don't call real APIs in tests
5. **Test edge cases**: Include error handling tests

### Naming Conventions

- Test files: `test_*.py` or `*.test.ts(x)`
- Test functions: `test_<what_it_tests>`
- Use descriptive names that explain what's being tested

### Database Tests

- Always use `db_session` fixture, never direct DB connections
- Clean up data after tests (fixtures handle this)
- Use SQLite for speed, PostgreSQL for integration tests
- Don't commit test data to version control

### API Tests

- Test both success and error cases
- Verify response status codes
- Check response data structure
- Test authentication/authorization
- Validate error messages

### Frontend Tests

- Test user interactions, not implementation details
- Use accessible queries (getByRole, getByLabelText)
- Mock API calls
- Test loading and error states
- Verify rendered output

## Troubleshooting

### Backend Tests Failing

```bash
# Ensure database is clean
make clean
rm -f test.db

# Reinstall dependencies
uv sync

# Run tests with verbose output
uv run pytest -v --tb=long
```

### Frontend Tests Failing

```bash
# Clear node_modules and reinstall
cd console
rm -rf node_modules
npm install

# Clear test cache
rm -rf node_modules/.vitest
```

### Pre-commit Hook Issues

```bash
# Update pre-commit hooks
uv run pre-commit autoupdate

# Skip hooks temporarily (not recommended)
git commit --no-verify
```

### CI Failures

1. Check GitHub Actions logs for detailed error messages
2. Run `make ci` locally to reproduce
3. Ensure all dependencies are in sync
4. Check environment variable requirements

## Test Data

### Default Test Users

- **Regular User**: `test@example.com` / `testpass123` (engineer role)
- **Admin User**: `admin@example.com` / `adminpass123` (admin role)
- **Approver User**: `approver@example.com` / `approverpass123` (approver role)

### Environment Variables for Tests

```bash
# Required for tests
export JWT_SECRET=test-secret-key-for-testing-only
export ALLOW_SIGNUP=true

# Optional (mocked in tests)
export OPENAI_API_KEY=  # Not needed for most tests
export ANTHROPIC_API_KEY=  # Not needed for most tests
```

## Adding New Tests

### Backend

1. Create test file in `tests/` directory
2. Import necessary fixtures from `conftest.py`
3. Add test markers (`@pytest.mark.unit`, etc.)
4. Write descriptive test functions
5. Run tests to verify

### Frontend

1. Create test file next to component or in `tests/` directory
2. Import testing utilities
3. Mock external dependencies (API, etc.)
4. Write tests using React Testing Library
5. Run tests to verify

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [Vitest documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pre-commit documentation](https://pre-commit.com/)

---

**Last Updated**: 2025-10-02
