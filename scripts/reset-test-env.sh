#!/bin/bash
# scripts/reset-test-env.sh
# Reset test environment for Product Automation System

set -e

echo "🔄 Resetting test environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to print info message
print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Reset backend environment
reset_backend() {
    echo "🐍 Resetting backend test environment..."
    
    cd backend
    
    # Clean Python cache
    print_info "Cleaning Python cache files..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true
    
    # Clean coverage files
    print_info "Cleaning coverage files..."
    rm -f .coverage
    rm -rf htmlcov/
    rm -f coverage.xml
    
    # Clean pytest cache
    print_info "Cleaning pytest cache..."
    rm -rf .pytest_cache/
    
    # Clean mypy cache
    print_info "Cleaning mypy cache..."
    rm -rf .mypy_cache/
    
    # Clean build artifacts
    print_info "Cleaning build artifacts..."
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info/
    
    print_success "Backend environment reset"
    cd ..
}

# Reset frontend environment
reset_frontend() {
    echo "⚛️ Resetting frontend test environment..."
    
    cd frontend
    
    # Clean Jest cache
    print_info "Cleaning Jest cache..."
    if command -v npm &> /dev/null; then
        npm run test -- --clearCache 2>/dev/null || true
    fi
    
    # Clean coverage
    print_info "Cleaning coverage files..."
    rm -rf coverage/
    
    # Clean build artifacts
    print_info "Cleaning build artifacts..."
    rm -rf .next/
    rm -rf out/
    
    # Clean TypeScript cache
    print_info "Cleaning TypeScript cache..."
    rm -rf .tsbuildinfo
    
    print_success "Frontend environment reset"
    cd ..
}

# Reset test database
reset_test_database() {
    echo "🗄️ Resetting test database..."
    
    cd backend
    
    # Check if virtual environment exists and activate it
    if [ -d "venv" ]; then
        source venv/bin/activate
        print_info "Activated virtual environment"
    else
        print_warning "Virtual environment not found, using system Python"
    fi
    
    # Re-run migrations to ensure clean state
    print_info "Re-running database migrations..."
    if [ -f "run_migrations.py" ]; then
        python run_migrations.py
        print_success "Database migrations completed"
    else
        print_warning "Migration script not found, skipping database reset"
    fi
    
    cd ..
}

# Clean temporary files
clean_temp_files() {
    echo "🧹 Cleaning temporary files..."
    
    # Clean common temporary files
    print_info "Removing temporary files..."
    find . -name "*.tmp" -delete 2>/dev/null || true
    find . -name "*.temp" -delete 2>/dev/null || true
    find . -name ".DS_Store" -delete 2>/dev/null || true
    find . -name "Thumbs.db" -delete 2>/dev/null || true
    
    # Clean log files
    print_info "Cleaning log files..."
    find . -name "*.log" -delete 2>/dev/null || true
    
    print_success "Temporary files cleaned"
}

# Reset git state (optional)
reset_git_state() {
    if [ "$1" = "--git" ]; then
        echo "🔄 Resetting git state..."
        
        print_info "Cleaning git working directory..."
        git clean -fd
        git reset --hard HEAD
        
        print_success "Git state reset"
    fi
}

# Validate reset
validate_reset() {
    echo "🔍 Validating reset..."
    
    # Check that cache directories are gone
    local issues=0
    
    if [ -d "backend/__pycache__" ]; then
        print_warning "Python cache still exists"
        ((issues++))
    fi
    
    if [ -d "backend/.pytest_cache" ]; then
        print_warning "Pytest cache still exists"
        ((issues++))
    fi
    
    if [ -d "frontend/coverage" ]; then
        print_warning "Frontend coverage still exists"
        ((issues++))
    fi
    
    if [ $issues -eq 0 ]; then
        print_success "Reset validation passed"
    else
        print_warning "Reset validation found $issues issues"
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 [--git] [--help]"
    echo ""
    echo "Options:"
    echo "  --git    Also reset git working directory (removes untracked files)"
    echo "  --help   Show this help message"
    echo ""
    echo "This script will:"
    echo "  - Clean Python cache files and build artifacts"
    echo "  - Clean frontend cache and build artifacts"
    echo "  - Reset test database to clean state"
    echo "  - Remove temporary files"
}

# Main execution
main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --git)
                GIT_RESET=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    reset_backend
    reset_frontend
    reset_test_database
    clean_temp_files
    
    if [ "$GIT_RESET" = true ]; then
        reset_git_state --git
    fi
    
    validate_reset
    
    echo ""
    print_success "✅ Test environment reset completed!"
    echo ""
    echo "You can now run:"
    echo "  npm run setup:test-env    # Re-setup environment"
    echo "  npm run test:all          # Run full test suite"
    echo "  npm run test:quick        # Run quick tests"
}

# Error handling
trap 'print_error "Reset failed! Check the output above for details."; exit 1' ERR

main "$@"
