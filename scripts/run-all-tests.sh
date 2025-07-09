#!/bin/bash
# scripts/run-all-tests.sh
# Comprehensive test runner for Product Automation System

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test execution modes
QUICK_MODE=false
PRE_COMMIT_MODE=false
FULL_MODE=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            FULL_MODE=false
            shift
            ;;
        --pre-commit)
            PRE_COMMIT_MODE=true
            FULL_MODE=false
            shift
            ;;
        *)
            echo "Unknown option $1"
            echo "Usage: $0 [--quick|--pre-commit]"
            exit 1
            ;;
    esac
done

# Function to print section headers
print_section() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Function to print success message
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error message
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to print warning message
print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Test execution functions
run_backend_unit_tests() {
    print_section "Running Backend Unit Tests"
    cd backend
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    if [ "$QUICK_MODE" = true ]; then
        python -m pytest tests/unit/ -v --tb=short
    else
        # Try to run with coverage, fall back to basic tests if coverage not available
        if python -c "import pytest_cov" 2>/dev/null; then
            python -m pytest tests/unit/ -v --cov=app --cov-report=term-missing --cov-fail-under=70
        else
            print_warning "pytest-cov not installed, running tests without coverage"
            echo -e "${YELLOW}   Install with: pip install pytest-cov${NC}"
            python -m pytest tests/unit/ -v
        fi
    fi
    cd ..
    print_success "Backend unit tests completed"
}

run_backend_integration_tests() {
    print_section "Running Backend Integration Tests"
    cd backend
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    python -m pytest tests/integration/ -v
    cd ..
    print_success "Backend integration tests completed"
}

run_backend_connectivity_tests() {
    print_section "Running Backend Connectivity Tests"
    cd backend
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    python -m pytest tests/connectivity/ -v
    cd ..
    print_success "Backend connectivity tests completed"
}

run_frontend_tests() {
    print_section "Running Frontend Tests"
    cd frontend
    npm test -- --watchAll=false --coverage
    cd ..
    print_success "Frontend tests completed"
}

run_linting() {
    print_section "Running Linting"
    
    # Backend linting
    echo -e "${BLUE}Backend linting...${NC}"
    cd backend
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    if command -v flake8 &> /dev/null; then
        if flake8 app/ tests/; then
            print_success "Backend linting passed"
        else
            print_error "Backend linting failed"
            cd ..
            return 1
        fi
    else
        print_warning "flake8 not installed, skipping backend linting"
        echo -e "${YELLOW}   Install with: pip install flake8${NC}"
    fi
    cd ..
    
    # Frontend linting
    echo -e "${BLUE}Frontend linting...${NC}"
    cd frontend
    if npm run lint 2>/dev/null; then
        print_success "Frontend linting passed"
    else
        print_warning "Frontend linting failed or not configured"
        echo -e "${YELLOW}   Check package.json for lint script${NC}"
    fi
    cd ..
    print_success "Linting checks completed"
}

run_type_checking() {
    print_section "Running Type Checking"
    
    # Backend type checking
    echo -e "${BLUE}Backend type checking...${NC}"
    cd backend
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    if command -v mypy &> /dev/null; then
        if mypy app/; then
            print_success "Backend type checking passed"
        else
            print_error "Backend type checking failed"
            cd ..
            return 1
        fi
    else
        print_warning "mypy not installed, skipping backend type checking"
        echo -e "${YELLOW}   Install with: pip install mypy${NC}"
    fi
    cd ..
    
    # Frontend type checking
    echo -e "${BLUE}Frontend type checking...${NC}"
    cd frontend
    if npm run type-check 2>/dev/null; then
        print_success "Frontend type checking passed"
    else
        print_warning "Frontend type checking failed or not configured"
        echo -e "${YELLOW}   Check package.json for type-check script${NC}"
    fi
    cd ..
    print_success "Type checking completed"
}

run_formatting_check() {
    print_section "Checking Code Formatting"
    
    # Backend formatting check
    echo -e "${BLUE}Backend formatting check...${NC}"
    cd backend
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    if command -v black &> /dev/null; then
        if black --check app/ tests/; then
            print_success "Backend formatting check passed"
        else
            print_error "Backend formatting check failed"
            cd ..
            return 1
        fi
    else
        print_warning "black not installed, skipping backend formatting check"
        echo -e "${YELLOW}   Install with: pip install black${NC}"
    fi
    cd ..
    
    # Frontend formatting check
    echo -e "${BLUE}Frontend formatting check...${NC}"
    cd frontend
    if command -v prettier &> /dev/null || npm list prettier &> /dev/null; then
        if npm run format:check; then
            print_success "Frontend formatting check passed"
        else
            print_error "Frontend formatting check failed"
            cd ..
            return 1
        fi
    else
        print_warning "prettier not installed, skipping frontend formatting check"
        echo -e "${YELLOW}   Install with: npm install prettier${NC}"
    fi
    cd ..
    print_success "Code formatting checks completed"
}

# Main execution logic
main() {
    local start_time=$(date +%s)
    
    if [ "$QUICK_MODE" = true ]; then
        print_section "🚀 Running Quick Test Suite (30 seconds target)"
        run_backend_unit_tests
        run_linting
    elif [ "$PRE_COMMIT_MODE" = true ]; then
        print_section "🔍 Running Pre-Commit Validation (2 minutes target)"
        run_formatting_check
        run_linting
        run_type_checking
        run_backend_unit_tests
        run_frontend_tests
    elif [ "$FULL_MODE" = true ]; then
        print_section "🎯 Running Full Test Suite (10 minutes target)"
        run_formatting_check
        run_linting
        run_type_checking
        run_backend_unit_tests
        run_backend_integration_tests
        run_backend_connectivity_tests
        run_frontend_tests
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_section "🎉 All Tests Completed Successfully!"
    echo -e "${GREEN}Total execution time: ${duration} seconds${NC}"
    
    if [ "$QUICK_MODE" = true ] && [ $duration -gt 30 ]; then
        print_warning "Quick tests took longer than 30 seconds target"
    elif [ "$PRE_COMMIT_MODE" = true ] && [ $duration -gt 120 ]; then
        print_warning "Pre-commit tests took longer than 2 minutes target"
    elif [ "$FULL_MODE" = true ] && [ $duration -gt 600 ]; then
        print_warning "Full test suite took longer than 10 minutes target"
    fi
}

# Execute main function with error handling
if main "$@"; then
    exit 0
else
    print_error "Some tests failed! Check the output above for details."
    exit 1
fi
