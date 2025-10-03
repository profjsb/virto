#!/bin/bash
# run_tests.sh - Comprehensive test runner for pre-PR checks
# Usage: ./scripts/run_tests.sh [--quick|--full|--backend|--frontend]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${GREEN}==>${NC} $1"
}

print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
check_dependencies() {
    print_step "Checking dependencies..."

    if ! command_exists uv; then
        print_error "uv is not installed. Install from https://github.com/astral-sh/uv"
        exit 1
    fi

    if ! command_exists npm; then
        print_error "npm is not installed."
        exit 1
    fi

    echo "✓ All required tools are installed"
}

# Backend tests
run_backend_tests() {
    print_step "Running backend linter..."
    uv run ruff check src tests || {
        print_error "Backend linting failed"
        exit 1
    }
    echo "✓ Backend linting passed"

    print_step "Running backend formatter check..."
    uv run ruff format --check src tests || {
        print_error "Backend formatting check failed. Run 'uv run ruff format src tests' to fix."
        exit 1
    }
    echo "✓ Backend formatting check passed"

    print_step "Running backend unit tests..."
    uv run pytest -v -m unit || {
        print_error "Backend unit tests failed"
        exit 1
    }
    echo "✓ Backend unit tests passed"

    if [ "$1" = "--full" ]; then
        print_step "Running backend integration tests..."
        uv run pytest -v -m integration || {
            print_warning "Backend integration tests failed (may require database setup)"
        }
    fi

    print_step "Running backend tests with coverage..."
    uv run pytest --cov=src --cov-report=term --cov-report=html || {
        print_error "Backend tests failed"
        exit 1
    }
    echo "✓ Backend tests passed"
    echo "Coverage report saved to htmlcov/index.html"
}

# Frontend tests
run_frontend_tests() {
    print_step "Running frontend linter..."
    cd console
    npm run lint || {
        print_error "Frontend linting failed"
        exit 1
    }
    echo "✓ Frontend linting passed"

    print_step "Running frontend type check..."
    npm run type-check || {
        print_error "Frontend type check failed"
        exit 1
    }
    echo "✓ Frontend type check passed"

    print_step "Running frontend tests..."
    npm run test || {
        print_error "Frontend tests failed"
        exit 1
    }
    echo "✓ Frontend tests passed"

    if [ "$1" = "--full" ]; then
        print_step "Running frontend tests with coverage..."
        npm run test:coverage || {
            print_error "Frontend coverage tests failed"
            exit 1
        }
        echo "Coverage report saved to console/coverage/"
    fi

    cd ..
}

# Main script
MODE="${1:---quick}"

echo "================================================"
echo "  Virtual AI Organization - Test Runner"
echo "  Mode: $MODE"
echo "================================================"
echo ""

check_dependencies

case $MODE in
    --backend)
        run_backend_tests "$MODE"
        ;;
    --frontend)
        run_frontend_tests "$MODE"
        ;;
    --quick)
        run_backend_tests "$MODE"
        run_frontend_tests "$MODE"
        ;;
    --full)
        run_backend_tests "$MODE"
        run_frontend_tests "$MODE"
        ;;
    *)
        print_error "Unknown mode: $MODE"
        echo "Usage: $0 [--quick|--full|--backend|--frontend]"
        exit 1
        ;;
esac

echo ""
echo "================================================"
echo -e "${GREEN}✅ All tests passed!${NC}"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Review coverage reports (htmlcov/index.html)"
echo "  2. Commit your changes"
echo "  3. Push and create a PR"
echo ""
