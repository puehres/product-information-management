#!/bin/bash
# scripts/setup-test-env.sh
# Comprehensive test environment setup for Product Automation System

set -e

echo "🔧 Setting up comprehensive test environment..."

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

# Check prerequisites
check_prerequisites() {
    echo "📋 Checking prerequisites..."
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
            print_success "Python $PYTHON_VERSION found (3.9+ required)"
        else
            print_error "Python 3.9+ required, found $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 not found"
        exit 1
    fi
    
    # Check Node.js version
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        if node -e "process.exit(parseInt(process.version.slice(1)) >= 18 ? 0 : 1)"; then
            print_success "Node.js $NODE_VERSION found (18+ required)"
        else
            print_error "Node.js 18+ required, found $NODE_VERSION"
            exit 1
        fi
    else
        print_error "Node.js not found"
        exit 1
    fi
    
    # Check npm
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        print_success "npm $NPM_VERSION found"
    else
        print_error "npm not found"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Setup backend environment
setup_backend_env() {
    echo "🐍 Setting up backend test environment..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv venv
        print_success "Created Python virtual environment"
    else
        print_info "Python virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    print_info "Installing backend dependencies..."
    pip install -r requirements.txt
    print_success "Installed backend dependencies"
    
    # Install development dependencies
    print_info "Installing development dependencies..."
    pip install pytest pytest-asyncio pytest-cov black isort mypy flake8 pytest-xdist python-multipart requests
    print_success "Installed development dependencies"
    
    cd ..
}

# Setup frontend environment
setup_frontend_env() {
    echo "⚛️ Setting up frontend test environment..."
    
    cd frontend
    
    # Install dependencies
    print_info "Installing frontend dependencies..."
    npm ci
    print_success "Installed frontend dependencies"
    
    cd ..
}

# Setup test database
setup_test_database() {
    echo "🗄️ Setting up test database..."
    
    # Copy environment files if they don't exist
    if [ ! -f "backend/.env" ]; then
        cp backend/.env.example backend/.env
        print_warning "Created backend/.env from example - please configure with your credentials"
    else
        print_info "backend/.env already exists"
    fi
    
    if [ ! -f "frontend/.env.local" ]; then
        cp frontend/.env.example frontend/.env.local
        print_warning "Created frontend/.env.local from example - please configure with your settings"
    else
        print_info "frontend/.env.local already exists"
    fi
    
    # Run database migrations
    print_info "Running database migrations..."
    cd backend
    source venv/bin/activate
    python run_migrations.py
    print_success "Database migrations completed"
    cd ..
}

# Validate setup
validate_setup() {
    echo "🔍 Validating test environment setup..."
    
    # Test backend environment
    print_info "Testing backend environment..."
    cd backend
    source venv/bin/activate
    
    # Check if pytest works
    if python -m pytest --version &> /dev/null; then
        print_success "pytest is working"
    else
        print_error "pytest is not working"
        exit 1
    fi
    
    # Run a quick test if available
    if [ -f "tests/unit/test_config.py" ]; then
        python -m pytest tests/unit/test_config.py -v --tb=short
        print_success "Backend test validation passed"
    else
        print_warning "No config test found, skipping backend test validation"
    fi
    
    cd ..
    
    # Test frontend environment
    print_info "Testing frontend environment..."
    cd frontend
    
    # Check TypeScript compilation
    npm run type-check
    print_success "Frontend type checking passed"
    
    cd ..
    
    print_success "Environment validation completed"
}

# Create helpful scripts
create_helper_scripts() {
    echo "📝 Creating helper scripts..."
    
    # Create a quick test script
    cat > scripts/quick-test.sh << 'EOF'
#!/bin/bash
# Quick test runner for development
echo "🚀 Running quick tests..."
cd backend && source venv/bin/activate && python -m pytest tests/unit/ -x --tb=short
EOF
    chmod +x scripts/quick-test.sh
    
    # Create a coverage report script
    cat > scripts/coverage-report.sh << 'EOF'
#!/bin/bash
# Generate comprehensive coverage report
echo "📊 Generating coverage report..."
cd backend
source venv/bin/activate
python -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
echo "Coverage report generated in backend/htmlcov/index.html"
EOF
    chmod +x scripts/coverage-report.sh
    
    print_success "Helper scripts created"
}

# Main execution
main() {
    check_prerequisites
    setup_backend_env
    setup_frontend_env
    setup_test_database
    validate_setup
    create_helper_scripts
    
    echo ""
    echo "🎉 Test environment setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Configure backend/.env with your credentials"
    echo "2. Configure frontend/.env.local with your settings"
    echo "3. Run 'npm run test:all' to execute full test suite"
    echo "4. Run 'npm run test:quick' for fast development tests"
    echo ""
    echo "Helper scripts created:"
    echo "- scripts/quick-test.sh - Quick unit tests"
    echo "- scripts/coverage-report.sh - Generate coverage report"
}

# Error handling
trap 'print_error "Setup failed! Check the output above for details."; exit 1' ERR

main "$@"
