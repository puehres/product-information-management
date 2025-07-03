#!/bin/bash

# Frontend Environment Validation Script
# Universal Product Automation System
# 
# This script validates the frontend development environment
# and provides troubleshooting guidance for common issues.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_header() {
    echo -e "\n${BLUE}🔍 $1${NC}"
    echo "=================================="
}

# Performance tracking
start_time=$(date +%s)

# Validation functions
validate_prerequisites() {
    log_header "Environment Prerequisites Validation"
    
    # Check Node.js version
    if command -v node >/dev/null 2>&1; then
        NODE_VERSION=$(node --version | sed 's/v//')
        REQUIRED_NODE="18.0.0"
        if [ "$(printf '%s\n' "$REQUIRED_NODE" "$NODE_VERSION" | sort -V | head -n1)" = "$REQUIRED_NODE" ]; then
            log_success "Node.js $NODE_VERSION (>= $REQUIRED_NODE required)"
        else
            log_error "Node.js $NODE_VERSION is below required version $REQUIRED_NODE"
            echo "  💡 Install Node.js $REQUIRED_NODE or higher from https://nodejs.org/"
            exit 1
        fi
    else
        log_error "Node.js not found"
        echo "  💡 Install Node.js from https://nodejs.org/"
        exit 1
    fi
    
    # Check npm version
    if command -v npm >/dev/null 2>&1; then
        NPM_VERSION=$(npm --version)
        REQUIRED_NPM="8.0.0"
        if [ "$(printf '%s\n' "$REQUIRED_NPM" "$NPM_VERSION" | sort -V | head -n1)" = "$REQUIRED_NPM" ]; then
            log_success "npm $NPM_VERSION (>= $REQUIRED_NPM required)"
        else
            log_error "npm $NPM_VERSION is below required version $REQUIRED_NPM"
            echo "  💡 Update npm: npm install -g npm@latest"
            exit 1
        fi
    else
        log_error "npm not found"
        echo "  💡 npm should be installed with Node.js"
        exit 1
    fi
    
    # Check for conflicting package managers
    if command -v yarn >/dev/null 2>&1; then
        log_warning "Yarn detected - may cause conflicts with npm"
        echo "  💡 Consider using only npm for this project"
    fi
    
    if command -v pnpm >/dev/null 2>&1; then
        log_warning "pnpm detected - may cause conflicts with npm"
        echo "  💡 Consider using only npm for this project"
    fi
}

validate_dependencies() {
    log_header "Dependency Installation Validation"
    
    # Check if we're in the frontend directory
    if [ ! -f "package.json" ]; then
        log_error "package.json not found. Are you in the frontend directory?"
        exit 1
    fi
    
    # Install dependencies
    log_info "Installing dependencies..."
    install_start=$(date +%s)
    
    if npm install; then
        install_end=$(date +%s)
        install_time=$((install_end - install_start))
        log_success "Dependencies installed successfully in ${install_time}s"
        
        if [ $install_time -gt 120 ]; then
            log_warning "Installation took longer than expected (${install_time}s > 120s)"
            echo "  💡 Consider clearing npm cache: npm cache clean --force"
        fi
    else
        log_error "Failed to install dependencies"
        echo "  💡 Try: rm -rf node_modules package-lock.json && npm install"
        echo "  💡 Check npm cache: npm cache clean --force"
        echo "  💡 Check Node.js version compatibility"
        exit 1
    fi
    
    # Security audit
    log_info "Running security audit..."
    if npm audit --audit-level=moderate; then
        log_success "No moderate or higher security vulnerabilities found"
    else
        log_warning "Security vulnerabilities detected"
        echo "  💡 Run: npm audit fix"
        echo "  💡 For force fixes: npm audit fix --force"
    fi
    
    # Check for peer dependency warnings
    if npm ls --depth=0 2>&1 | grep -i "peer dep" >/dev/null; then
        log_warning "Peer dependency warnings detected"
        echo "  💡 Review warnings and install missing peer dependencies"
    else
        log_success "No peer dependency issues"
    fi
}

validate_typescript() {
    log_header "TypeScript Compilation Validation"
    
    # Check TypeScript configuration
    if [ ! -f "tsconfig.json" ]; then
        log_error "tsconfig.json not found"
        exit 1
    fi
    
    # Run type checking
    log_info "Running TypeScript type checking..."
    type_start=$(date +%s)
    
    if npm run type-check; then
        type_end=$(date +%s)
        type_time=$((type_end - type_start))
        log_success "TypeScript compilation passed in ${type_time}s"
        
        if [ $type_time -gt 30 ]; then
            log_warning "Type checking took longer than expected (${type_time}s > 30s)"
            echo "  💡 Consider enabling incremental compilation in tsconfig.json"
        fi
    else
        log_error "TypeScript compilation failed"
        echo "  💡 Fix type errors shown above"
        echo "  💡 Check tsconfig.json configuration"
        echo "  💡 Verify path mappings are correct"
        exit 1
    fi
    
    # Verify TypeScript configuration
    log_info "Verifying TypeScript configuration..."
    if npx tsc --showConfig >/dev/null 2>&1; then
        log_success "TypeScript configuration is valid"
    else
        log_error "Invalid TypeScript configuration"
        echo "  💡 Check tsconfig.json syntax"
        exit 1
    fi
}

validate_testing() {
    log_header "Testing Framework Validation"
    
    # Check Jest configuration
    if [ ! -f "jest.config.js" ]; then
        log_error "jest.config.js not found"
        exit 1
    fi
    
    # Run tests
    log_info "Running test suite..."
    test_start=$(date +%s)
    
    if npm test -- --watchAll=false; then
        test_end=$(date +%s)
        test_time=$((test_end - test_start))
        log_success "All tests passed in ${test_time}s"
        
        if [ $test_time -gt 60 ]; then
            log_warning "Tests took longer than expected (${test_time}s > 60s)"
            echo "  💡 Consider optimizing test performance"
        fi
    else
        log_error "Tests failed"
        echo "  💡 Fix failing tests shown above"
        echo "  💡 Check Jest configuration"
        echo "  💡 Verify test setup files"
        exit 1
    fi
    
    # Run tests with coverage
    log_info "Running coverage analysis..."
    if npm run test:coverage -- --watchAll=false >/dev/null 2>&1; then
        log_success "Coverage analysis completed"
    else
        log_warning "Coverage analysis failed"
        echo "  💡 Check coverage configuration in jest.config.js"
    fi
    
    # Verify Jest configuration
    log_info "Verifying Jest configuration..."
    if npx jest --showConfig >/dev/null 2>&1; then
        log_success "Jest configuration is valid"
    else
        log_error "Invalid Jest configuration"
        echo "  💡 Check jest.config.js syntax"
        exit 1
    fi
}

validate_dev_server() {
    log_header "Development Server Validation"
    
    # Start development server in background
    log_info "Starting development server..."
    server_start=$(date +%s)
    
    npm run dev &
    DEV_PID=$!
    
    # Wait for server to start
    log_info "Waiting for server startup..."
    sleep 10
    
    # Test server response
    if curl -f http://localhost:3000 >/dev/null 2>&1; then
        server_end=$(date +%s)
        server_time=$((server_end - server_start))
        log_success "Development server responding in ${server_time}s"
        
        if [ $server_time -gt 10 ]; then
            log_warning "Server startup took longer than expected (${server_time}s > 10s)"
            echo "  💡 Check for configuration issues"
            echo "  💡 Clear .next cache: rm -rf .next"
        fi
    else
        log_error "Development server not responding"
        echo "  💡 Check if port 3000 is available: lsof -ti:3000"
        echo "  💡 Try different port: npm run dev -- --port 3001"
        echo "  💡 Check Next.js configuration"
        kill $DEV_PID 2>/dev/null || true
        exit 1
    fi
    
    # Kill development server
    kill $DEV_PID 2>/dev/null || true
    log_info "Development server stopped"
}

validate_build() {
    log_header "Build Process Validation"
    
    # Run production build
    log_info "Running production build..."
    build_start=$(date +%s)
    
    if npm run build; then
        build_end=$(date +%s)
        build_time=$((build_end - build_start))
        log_success "Production build completed in ${build_time}s"
        
        if [ $build_time -gt 120 ]; then
            log_warning "Build took longer than expected (${build_time}s > 120s)"
            echo "  💡 Consider optimizing build performance"
            echo "  💡 Check for large dependencies"
        fi
    else
        log_error "Production build failed"
        echo "  💡 Fix build errors shown above"
        echo "  💡 Check Next.js configuration"
        echo "  💡 Verify all dependencies are installed"
        exit 1
    fi
    
    # Verify build artifacts
    if [ -d ".next" ]; then
        log_success "Build artifacts created successfully"
        
        # Check build size
        BUILD_SIZE=$(du -sh .next 2>/dev/null | cut -f1)
        log_info "Build size: $BUILD_SIZE"
    else
        log_error "Build artifacts not found"
        exit 1
    fi
}

validate_code_quality() {
    log_header "Code Quality Tools Validation"
    
    # Run ESLint
    log_info "Running ESLint..."
    if npm run lint; then
        log_success "ESLint checks passed"
    else
        log_error "ESLint checks failed"
        echo "  💡 Fix linting errors shown above"
        echo "  💡 Run auto-fix: npm run lint:fix"
        echo "  💡 Check .eslintrc.json configuration"
        exit 1
    fi
    
    # Run Prettier check
    log_info "Running Prettier format check..."
    if npm run format:check; then
        log_success "Code formatting is correct"
    else
        log_warning "Code formatting issues found"
        echo "  💡 Run auto-format: npm run format"
        echo "  💡 Check .prettierrc configuration"
        
        # Auto-format and recheck
        log_info "Auto-formatting code..."
        if npm run format && npm run format:check; then
            log_success "Code formatted successfully"
        else
            log_error "Failed to format code"
            exit 1
        fi
    fi
}

validate_configuration() {
    log_header "Configuration Files Validation"
    
    # Check required configuration files
    REQUIRED_FILES=(
        "package.json"
        "tsconfig.json"
        "next.config.js"
        "tailwind.config.js"
        "postcss.config.js"
        "jest.config.js"
        "jest.setup.js"
        ".eslintrc.json"
    )
    
    for file in "${REQUIRED_FILES[@]}"; do
        if [ -f "$file" ]; then
            log_success "$file exists"
        else
            log_error "$file missing"
            echo "  💡 Create $file with proper configuration"
        fi
    done
    
    # Validate JSON files
    JSON_FILES=("package.json" "tsconfig.json" ".eslintrc.json")
    for file in "${JSON_FILES[@]}"; do
        if [ -f "$file" ]; then
            if node -e "JSON.parse(require('fs').readFileSync('$file', 'utf8'))" 2>/dev/null; then
                log_success "$file has valid JSON syntax"
            else
                log_error "$file has invalid JSON syntax"
                echo "  💡 Fix JSON syntax errors in $file"
                exit 1
            fi
        fi
    done
}

generate_report() {
    log_header "Validation Summary"
    
    end_time=$(date +%s)
    total_time=$((end_time - start_time))
    
    echo "🎉 Frontend environment validation completed successfully!"
    echo ""
    echo "📊 Performance Summary:"
    echo "  • Total validation time: ${total_time}s"
    echo "  • All validation steps passed"
    echo "  • Environment ready for development"
    echo ""
    echo "🚀 Next Steps:"
    echo "  • Start development server: npm run dev"
    echo "  • Run tests in watch mode: npm run test:watch"
    echo "  • Build for production: npm run build"
    echo ""
    echo "📚 Documentation:"
    echo "  • Frontend README: ./README.md"
    echo "  • Troubleshooting: ./docs/troubleshooting.md"
    echo ""
    
    # Save validation report
    REPORT_FILE="validation-report-$(date +%Y%m%d-%H%M%S).txt"
    {
        echo "Frontend Environment Validation Report"
        echo "Generated: $(date)"
        echo "Total time: ${total_time}s"
        echo "Status: SUCCESS"
        echo ""
        echo "Environment:"
        echo "  Node.js: $(node --version)"
        echo "  npm: $(npm --version)"
        echo "  OS: $(uname -s)"
        echo ""
        echo "All validation steps completed successfully."
    } > "$REPORT_FILE"
    
    log_success "Validation report saved: $REPORT_FILE"
}

# Main execution
main() {
    echo "🔍 Frontend Environment Validation"
    echo "Universal Product Automation System"
    echo "=================================="
    echo ""
    
    # Change to frontend directory if not already there
    if [ ! -f "package.json" ] && [ -d "frontend" ]; then
        log_info "Changing to frontend directory..."
        cd frontend
    fi
    
    # Run all validation steps
    validate_prerequisites
    validate_dependencies
    validate_typescript
    validate_testing
    validate_dev_server
    validate_build
    validate_code_quality
    validate_configuration
    generate_report
}

# Error handling
trap 'log_error "Validation failed. Check the output above for details."; exit 1' ERR

# Run main function
main "$@"
