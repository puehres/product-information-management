#!/bin/bash
# scripts/validate-env.sh
# Validate test environment for Product Automation System

set -e

echo "🔍 Validating test environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Function to print success message
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED_CHECKS++))
}

# Function to print error message
print_error() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED_CHECKS++))
}

# Function to print warning message
print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
    ((WARNING_CHECKS++))
}

# Function to print info message
print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Function to run a check
run_check() {
    local description="$1"
    local command="$2"
    
    ((TOTAL_CHECKS++))
    print_info "Checking: $description"
    
    if eval "$command" &>/dev/null; then
        print_success "$description"
        return 0
    else
        print_error "$description"
        return 1
    fi
}

# Function to run a check with warning
run_check_warning() {
    local description="$1"
    local command="$2"
    
    ((TOTAL_CHECKS++))
    print_info "Checking: $description"
    
    if eval "$command" &>/dev/null; then
        print_success "$description"
        return 0
    else
        print_warning "$description (optional)"
        return 1
    fi
}

# Validate system prerequisites
validate_system() {
    echo "🖥️ Validating system prerequisites..."
    
    run_check "Python 3.9+ installed" "python3 -c 'import sys; exit(0 if sys.version_info >= (3, 9) else 1)'"
    run_check "Node.js 18+ installed" "node -e 'process.exit(parseInt(process.version.slice(1)) >= 18 ? 0 : 1)'"
    run_check "npm installed" "command -v npm"
    run_check "git installed" "command -v git"
}

# Validate backend environment
validate_backend() {
    echo "🐍 Validating backend environment..."
    
    run_check "Backend directory exists" "[ -d 'backend' ]"
    run_check "Backend requirements.txt exists" "[ -f 'backend/requirements.txt' ]"
    run_check "Backend pytest.ini exists" "[ -f 'backend/pytest.ini' ]"
    run_check "Backend pyproject.toml exists" "[ -f 'backend/pyproject.toml' ]"
    
    # Check virtual environment
    if [ -d "backend/venv" ]; then
        print_success "Python virtual environment exists"
        ((PASSED_CHECKS++))
        
        # Test virtual environment
        cd backend
        source venv/bin/activate
        
        run_check "pytest installed in venv" "python -m pytest --version"
        run_check_warning "black installed in venv" "python -m black --version"
        run_check_warning "mypy installed in venv" "python -m mypy --version"
        run_check_warning "flake8 installed in venv" "python -m flake8 --version"
        
        cd ..
    else
        print_error "Python virtual environment missing"
        ((FAILED_CHECKS++))
    fi
    
    ((TOTAL_CHECKS += 5))
}

# Validate frontend environment
validate_frontend() {
    echo "⚛️ Validating frontend environment..."
    
    run_check "Frontend directory exists" "[ -d 'frontend' ]"
    run_check "Frontend package.json exists" "[ -f 'frontend/package.json' ]"
    run_check "Frontend jest.config.js exists" "[ -f 'frontend/jest.config.js' ]"
    run_check "Frontend tsconfig.json exists" "[ -f 'frontend/tsconfig.json' ]"
    
    # Check node_modules
    if [ -d "frontend/node_modules" ]; then
        print_success "Frontend dependencies installed"
        ((PASSED_CHECKS++))
        
        # Test frontend tools
        cd frontend
        run_check "Jest available" "npm run test -- --version"
        run_check "TypeScript compiler available" "npm run type-check -- --version"
        run_check_warning "ESLint available" "npm run lint -- --version"
        cd ..
    else
        print_error "Frontend dependencies not installed"
        ((FAILED_CHECKS++))
    fi
    
    ((TOTAL_CHECKS += 4))
}

# Validate test structure
validate_test_structure() {
    echo "🧪 Validating test structure..."
    
    run_check "Backend tests directory exists" "[ -d 'backend/tests' ]"
    run_check "Backend unit tests directory exists" "[ -d 'backend/tests/unit' ]"
    run_check "Backend integration tests directory exists" "[ -d 'backend/tests/integration' ]"
    run_check "Backend connectivity tests directory exists" "[ -d 'backend/tests/connectivity' ]"
    run_check "Backend test fixtures directory exists" "[ -d 'backend/tests/fixtures' ]"
    
    # Check for conftest.py files
    run_check "Backend unit conftest.py exists" "[ -f 'backend/tests/unit/conftest.py' ]"
    
    # Check for some test files
    run_check "Backend has unit tests" "find backend/tests/unit -name 'test_*.py' | head -1"
    run_check_warning "Backend has integration tests" "find backend/tests/integration -name 'test_*.py' | head -1"
    run_check_warning "Backend has connectivity tests" "find backend/tests/connectivity -name 'test_*.py' | head -1"
    
    # Frontend test structure
    run_check_warning "Frontend has test files" "find frontend/src -name '*.test.*' -o -name '__tests__' | head -1"
}

# Validate configuration files
validate_configuration() {
    echo "⚙️ Validating configuration files..."
    
    run_check "Root package.json exists" "[ -f 'package.json' ]"
    run_check "Scripts directory exists" "[ -d 'scripts' ]"
    run_check "Test runner script exists" "[ -f 'scripts/run-all-tests.sh' ]"
    run_check "Setup script exists" "[ -f 'scripts/setup-test-env.sh' ]"
    run_check "Reset script exists" "[ -f 'scripts/reset-test-env.sh' ]"
    
    # Check script permissions
    run_check "Test runner script is executable" "[ -x 'scripts/run-all-tests.sh' ]"
    run_check "Setup script is executable" "[ -x 'scripts/setup-test-env.sh' ]"
    run_check "Reset script is executable" "[ -x 'scripts/reset-test-env.sh' ]"
    
    # Check environment files
    run_check_warning "Backend .env exists" "[ -f 'backend/.env' ]"
    run_check_warning "Frontend .env.local exists" "[ -f 'frontend/.env.local' ]"
}

# Validate database connectivity
validate_database() {
    echo "🗄️ Validating database connectivity..."
    
    if [ -f "backend/.env" ]; then
        cd backend
        if [ -d "venv" ]; then
            source venv/bin/activate
            
            # Try to run a simple database test
            run_check_warning "Database connectivity test" "python -c 'from app.core.database import supabase_manager; import asyncio; asyncio.run(supabase_manager.test_connection())'"
        else
            print_warning "Cannot test database - virtual environment missing"
            ((WARNING_CHECKS++))
            ((TOTAL_CHECKS++))
        fi
        cd ..
    else
        print_warning "Cannot test database - .env file missing"
        ((WARNING_CHECKS++))
        ((TOTAL_CHECKS++))
    fi
}

# Run sample tests
validate_sample_tests() {
    echo "🧪 Running sample tests..."
    
    # Backend unit test sample
    if [ -d "backend/venv" ] && [ -d "backend/tests/unit" ]; then
        cd backend
        source venv/bin/activate
        
        # Find a simple test to run
        if [ -f "tests/unit/test_config.py" ]; then
            run_check "Sample backend unit test" "python -m pytest tests/unit/test_config.py -v --tb=short"
        else
            print_warning "No config test found for validation"
            ((WARNING_CHECKS++))
            ((TOTAL_CHECKS++))
        fi
        cd ..
    else
        print_warning "Cannot run backend tests - environment not ready"
        ((WARNING_CHECKS++))
        ((TOTAL_CHECKS++))
    fi
    
    # Frontend test sample
    if [ -d "frontend/node_modules" ]; then
        cd frontend
        run_check_warning "Sample frontend test" "npm run type-check"
        cd ..
    else
        print_warning "Cannot run frontend tests - dependencies not installed"
        ((WARNING_CHECKS++))
        ((TOTAL_CHECKS++))
    fi
}

# Generate validation report
generate_report() {
    echo ""
    echo "📊 Validation Report"
    echo "===================="
    echo -e "Total checks: ${BLUE}$TOTAL_CHECKS${NC}"
    echo -e "Passed: ${GREEN}$PASSED_CHECKS${NC}"
    echo -e "Failed: ${RED}$FAILED_CHECKS${NC}"
    echo -e "Warnings: ${YELLOW}$WARNING_CHECKS${NC}"
    echo ""
    
    local success_rate=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "${GREEN}🎉 Environment validation passed! ($success_rate% success rate)${NC}"
        echo ""
        echo "✅ Your test environment is ready!"
        echo "You can now run:"
        echo "  npm run test:all          # Full test suite"
        echo "  npm run test:quick        # Quick tests"
        echo "  npm run test:pre-commit   # Pre-commit validation"
        return 0
    elif [ $FAILED_CHECKS -le 2 ]; then
        echo -e "${YELLOW}⚠️ Environment validation completed with minor issues ($success_rate% success rate)${NC}"
        echo ""
        echo "Some optional components are missing, but core functionality should work."
        echo "Consider running: npm run setup:test-env"
        return 1
    else
        echo -e "${RED}❌ Environment validation failed ($success_rate% success rate)${NC}"
        echo ""
        echo "Critical issues found. Please run: npm run setup:test-env"
        return 2
    fi
}

# Main execution
main() {
    validate_system
    validate_backend
    validate_frontend
    validate_test_structure
    validate_configuration
    validate_database
    validate_sample_tests
    
    generate_report
}

# Error handling for the main validation (don't exit on individual check failures)
set +e
main
exit_code=$?
set -e

exit $exit_code
