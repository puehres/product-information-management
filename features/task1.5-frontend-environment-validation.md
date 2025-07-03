## FEATURE:

Frontend Environment Validation - Comprehensive validation and troubleshooting of the frontend development environment for the Universal Product Automation System including dependency installation verification, TypeScript compilation validation, testing framework execution, development server startup validation, configuration file verification, and documentation of troubleshooting procedures for future reference.

## EXAMPLES:

[Reference examples in the `examples/` folder - will include:]
- Frontend validation scripts for automated environment checking
- Common error scenarios and their solutions
- Configuration validation checklists
- Troubleshooting workflows for dependency conflicts
- Performance benchmarking scripts for build times
- IDE configuration examples for optimal development experience
- Environment-specific setup guides (macOS, Windows, Linux)
- Automated health check scripts for continuous validation

## DOCUMENTATION:

### Frontend Dependency Management
- **npm/yarn**: https://docs.npmjs.com/cli/v10/commands/npm-install - Package installation and dependency resolution
- **Package Lock Files**: https://docs.npmjs.com/cli/v10/configuring-npm/package-lock-json - Dependency version locking and security
- **Node.js Compatibility**: https://nodejs.org/en/about/releases/ - Node.js version requirements and LTS support
- **Dependency Auditing**: https://docs.npmjs.com/cli/v10/commands/npm-audit - Security vulnerability scanning
- **Package Resolution**: https://docs.npmjs.com/cli/v10/using-npm/dependency-resolution - Understanding dependency conflicts

### TypeScript Configuration & Validation
- **TypeScript Compiler**: https://www.typescriptlang.org/docs/handbook/compiler-options.html - Compiler configuration and options
- **Next.js TypeScript**: https://nextjs.org/docs/app/building-your-application/configuring/typescript - Next.js specific TypeScript setup
- **Type Checking**: https://www.typescriptlang.org/docs/handbook/2/everyday-types.html - Common type checking patterns
- **TSConfig Reference**: https://www.typescriptlang.org/tsconfig - Complete tsconfig.json reference
- **Type Declaration Files**: https://www.typescriptlang.org/docs/handbook/2/type-declarations.html - Managing type definitions

### Testing Framework Validation
- **Jest Configuration**: https://jestjs.io/docs/configuration - Jest setup and configuration options
- **React Testing Library**: https://testing-library.com/docs/react-testing-library/intro/ - Component testing best practices
- **Testing Environment**: https://jestjs.io/docs/configuration#testenvironment-string - jsdom and testing environment setup
- **Coverage Reports**: https://jestjs.io/docs/code-coverage - Test coverage configuration and reporting
- **Mock Functions**: https://jestjs.io/docs/mock-functions - Mocking external dependencies in tests

### Next.js Development Server
- **Development Server**: https://nextjs.org/docs/app/api-reference/next-cli#development - Next.js dev server configuration
- **Hot Reload**: https://nextjs.org/docs/architecture/fast-refresh - Fast Refresh and hot module replacement
- **Environment Variables**: https://nextjs.org/docs/app/building-your-application/configuring/environment-variables - Environment configuration
- **Port Configuration**: https://nextjs.org/docs/app/api-reference/next-cli#development - Custom port and host settings
- **Performance Optimization**: https://nextjs.org/docs/app/building-your-application/optimizing - Development performance tuning

### Build Tools & Configuration
- **Tailwind CSS**: https://tailwindcss.com/docs/installation - CSS framework setup and configuration
- **PostCSS**: https://postcss.org/docs/ - CSS processing and plugin configuration
- **ESLint**: https://eslint.org/docs/latest/use/getting-started - Code linting and style enforcement
- **Prettier**: https://prettier.io/docs/en/configuration.html - Code formatting configuration
- **Build Process**: https://nextjs.org/docs/app/building-your-application/deploying - Production build validation

### UI Component Libraries
- **Radix UI**: https://www.radix-ui.com/primitives/docs/overview/introduction - Headless UI component setup
- **Shadcn/UI**: https://ui.shadcn.com/docs/installation/next - Component library integration
- **Lucide React**: https://lucide.dev/guide/packages/lucide-react - Icon library setup
- **Class Variance Authority**: https://cva.style/docs - Component variant management
- **Tailwind Merge**: https://github.com/dcastil/tailwind-merge - CSS class merging utilities

## OTHER CONSIDERATIONS:

### Frontend Validation Checklist

#### 1. Dependency Installation Validation
```bash
# Navigate to frontend directory
cd frontend/

# Clean install dependencies
rm -rf node_modules package-lock.json
npm install

# Verify installation success
npm list --depth=0
npm audit --audit-level=moderate

# Check for peer dependency warnings
npm ls --depth=0 2>&1 | grep -i "peer dep"
```

#### 2. TypeScript Compilation Validation
```bash
# Run TypeScript type checking
npm run type-check

# Verify TypeScript configuration
npx tsc --showConfig

# Check for type errors in specific files
npx tsc --noEmit --skipLibCheck src/app/page.tsx

# Validate TypeScript version compatibility
npx tsc --version
```

#### 3. Testing Framework Validation
```bash
# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode (for development)
npm run test:watch

# Validate Jest configuration
npx jest --showConfig

# Run specific test file
npm test -- src/app/__tests__/page.test.tsx
```

#### 4. Development Server Validation
```bash
# Start development server
npm run dev

# Test server on different port (if 3000 is occupied)
npm run dev -- --port 3001

# Verify server accessibility
curl http://localhost:3000

# Check for hot reload functionality
# (modify a file and verify browser updates)
```

#### 5. Build Process Validation
```bash
# Create production build
npm run build

# Start production server
npm start

# Analyze build output
npm run build -- --analyze

# Verify build artifacts
ls -la .next/
```

#### 6. Code Quality Validation
```bash
# Run ESLint
npm run lint

# Fix ESLint issues automatically
npm run lint:fix

# Check code formatting
npm run format:check

# Apply code formatting
npm run format
```

### Configuration File Validation

#### TypeScript Configuration (tsconfig.json)
```json
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "es6"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

#### Jest Configuration (jest.config.js)
```javascript
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jsdom',
  testPathIgnorePatterns: ['<rootDir>/.next/', '<rootDir>/node_modules/'],
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
}

module.exports = createJestConfig(customJestConfig)
```

#### Tailwind Configuration (tailwind.config.js)
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate"), require("@tailwindcss/forms"), require("@tailwindcss/typography")],
}
```

### Common Issues & Troubleshooting

#### Dependency Installation Issues

**Issue: npm install fails with permission errors**
```bash
# Solution 1: Use npm with --unsafe-perm flag
npm install --unsafe-perm

# Solution 2: Fix npm permissions (macOS/Linux)
sudo chown -R $(whoami) ~/.npm
sudo chown -R $(whoami) /usr/local/lib/node_modules

# Solution 3: Use node version manager (recommended)
# Install nvm and use it to manage Node.js versions
```

**Issue: Package version conflicts**
```bash
# Check for conflicting dependencies
npm ls

# Force resolution of peer dependencies
npm install --legacy-peer-deps

# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Issue: Slow npm install on macOS**
```bash
# Use faster DNS servers
echo "nameserver 8.8.8.8" | sudo tee /etc/resolver/npmjs.org

# Use npm ci for faster installs in CI/CD
npm ci

# Use yarn as alternative package manager
npm install -g yarn
yarn install
```

#### TypeScript Compilation Issues

**Issue: TypeScript compilation errors**
```bash
# Check TypeScript version compatibility
npm list typescript

# Update TypeScript to latest compatible version
npm update typescript

# Skip library type checking for faster compilation
npx tsc --noEmit --skipLibCheck

# Generate TypeScript declaration files
npx tsc --declaration --emitDeclarationOnly
```

**Issue: Module resolution errors**
```bash
# Verify path mapping in tsconfig.json
cat tsconfig.json | grep -A 5 "paths"

# Check if files exist at specified paths
ls -la src/components/

# Clear Next.js cache
rm -rf .next/
npm run dev
```

**Issue: Type definition conflicts**
```bash
# Check for duplicate type definitions
npm ls @types/react

# Remove conflicting type packages
npm uninstall @types/react @types/react-dom
npm install @types/react@latest @types/react-dom@latest

# Use TypeScript's skipLibCheck option
# Add to tsconfig.json: "skipLibCheck": true
```

#### Testing Framework Issues

**Issue: Jest tests fail to run**
```bash
# Verify Jest configuration
npx jest --showConfig

# Clear Jest cache
npx jest --clearCache

# Run tests with verbose output
npm test -- --verbose

# Check for missing test dependencies
npm install --save-dev @testing-library/jest-dom
```

**Issue: React Testing Library setup issues**
```bash
# Verify jest.setup.js exists and is configured
cat jest.setup.js

# Check if setupFilesAfterEnv is configured in Jest
grep -r "setupFilesAfterEnv" jest.config.js

# Install missing testing utilities
npm install --save-dev @testing-library/user-event
```

**Issue: Test coverage issues**
```bash
# Generate detailed coverage report
npm run test:coverage -- --verbose

# Check coverage thresholds
grep -A 10 "coverageThreshold" jest.config.js

# Exclude files from coverage
# Update collectCoverageFrom in jest.config.js
```

#### Development Server Issues

**Issue: Port 3000 already in use**
```bash
# Find process using port 3000
lsof -ti:3000

# Kill process using port 3000
kill -9 $(lsof -ti:3000)

# Start server on different port
npm run dev -- --port 3001

# Set default port in package.json
# "dev": "next dev --port 3001"
```

**Issue: Hot reload not working**
```bash
# Check file system limits (Linux)
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Restart development server
npm run dev

# Check for file watching issues
# Verify files are being watched correctly
```

**Issue: Environment variables not loading**
```bash
# Verify .env.local file exists
ls -la .env*

# Check environment variable naming (must start with NEXT_PUBLIC_ for client-side)
grep NEXT_PUBLIC_ .env.local

# Restart development server after env changes
npm run dev
```

#### Build Process Issues

**Issue: Production build fails**
```bash
# Run build with verbose output
npm run build -- --debug

# Check for build errors in specific files
npx next build --profile

# Analyze bundle size
npm run build -- --analyze

# Clear build cache
rm -rf .next/
npm run build
```

**Issue: Static export issues**
```bash
# Check next.config.js for export configuration
cat next.config.js

# Verify all pages are statically exportable
npm run build && npm run export

# Check for dynamic imports that need loading components
grep -r "dynamic(" src/
```

### Performance Optimization

#### Build Performance
```bash
# Enable SWC compiler (faster than Babel)
# Verify in next.config.js: swcMinify: true

# Use incremental TypeScript compilation
# In tsconfig.json: "incremental": true

# Optimize bundle analysis
npm install --save-dev @next/bundle-analyzer
```

#### Development Performance
```bash
# Reduce TypeScript checking frequency
# In next.config.js:
# typescript: { ignoreBuildErrors: true }

# Use faster refresh
# Ensure Fast Refresh is enabled in Next.js

# Optimize file watching
# Exclude unnecessary directories from watching
```

#### Memory Usage Optimization
```bash
# Increase Node.js memory limit
export NODE_OPTIONS="--max-old-space-size=4096"

# Monitor memory usage during build
npm run build -- --profile

# Use heap snapshots for memory debugging
node --inspect npm run build
```

### IDE Integration & Development Experience

#### VSCode Configuration (.vscode/settings.json)
```json
{
  "typescript.preferences.importModuleSpecifier": "relative",
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true,
    "source.organizeImports": true
  },
  "files.associations": {
    "*.css": "tailwindcss"
  },
  "tailwindCSS.includeLanguages": {
    "typescript": "javascript",
    "typescriptreact": "javascript"
  },
  "tailwindCSS.experimental.classRegex": [
    ["cva\\(([^)]*)\\)", "[\"'`]([^\"'`]*).*?[\"'`]"],
    ["cx\\(([^)]*)\\)", "(?:'|\"|`)([^']*)(?:'|\"|`)"]
  ]
}
```

#### VSCode Extensions Recommendations (.vscode/extensions.json)
```json
{
  "recommendations": [
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "ms-vscode.vscode-typescript-next",
    "formulahendry.auto-rename-tag",
    "christian-kohler.path-intellisense",
    "ms-vscode.vscode-json"
  ]
}
```

### Automated Validation Scripts

#### Frontend Health Check Script (scripts/validate-frontend.sh)
```bash
#!/bin/bash

echo "🔍 Frontend Environment Validation"
echo "=================================="

# Check Node.js version
echo "📦 Checking Node.js version..."
node --version
npm --version

# Navigate to frontend directory
cd frontend/

# Install dependencies
echo "📥 Installing dependencies..."
npm install

# Run type checking
echo "🔍 Running TypeScript type check..."
npm run type-check

# Run tests
echo "🧪 Running tests..."
npm test -- --watchAll=false

# Run linting
echo "🔧 Running ESLint..."
npm run lint

# Check formatting
echo "💅 Checking code formatting..."
npm run format:check

# Start development server (background)
echo "🚀 Starting development server..."
npm run dev &
DEV_PID=$!

# Wait for server to start
sleep 10

# Test server response
echo "🌐 Testing server response..."
curl -f http://localhost:3000 > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ Development server is responding"
else
    echo "❌ Development server is not responding"
fi

# Kill development server
kill $DEV_PID

echo "✅ Frontend validation complete!"
```

### Success Criteria for Task 1.5

#### Environment Validation Checklist
- [ ] **Dependencies Installed**: All npm packages installed without errors
- [ ] **TypeScript Compilation**: Type checking passes without errors
- [ ] **Testing Framework**: All tests pass and coverage meets thresholds
- [ ] **Development Server**: Server starts and responds on localhost:3000
- [ ] **Build Process**: Production build completes successfully
- [ ] **Code Quality**: ESLint and Prettier checks pass
- [ ] **Configuration Files**: All config files are valid and properly formatted
- [ ] **Hot Reload**: File changes trigger automatic browser updates
- [ ] **Environment Variables**: Environment configuration loads correctly
- [ ] **IDE Integration**: VSCode/IDE provides proper TypeScript and linting support

#### Performance Benchmarks
- [ ] **Install Time**: npm install completes in under 2 minutes
- [ ] **Type Check Time**: TypeScript compilation completes in under 30 seconds
- [ ] **Test Execution**: All tests complete in under 1 minute
- [ ] **Dev Server Startup**: Development server starts in under 10 seconds
- [ ] **Build Time**: Production build completes in under 2 minutes
- [ ] **Hot Reload Speed**: File changes reflect in browser within 2 seconds

#### Troubleshooting Documentation
- [ ] **Common Issues**: Documented solutions for frequent problems
- [ ] **Error Messages**: Clear explanations for common error scenarios
- [ ] **Recovery Procedures**: Step-by-step recovery from broken states
- [ ] **Performance Issues**: Solutions for slow build/dev server performance
- [ ] **Environment Differences**: Platform-specific considerations documented
- [ ] **Dependency Conflicts**: Resolution strategies for package conflicts

#### Quality Assurance
- [ ] **Code Standards**: ESLint configuration enforces project standards
- [ ] **Type Safety**: TypeScript strict mode enabled and passing
- [ ] **Test Coverage**: Minimum 70% code coverage achieved
- [ ] **Accessibility**: Basic accessibility linting rules enabled
- [ ] **Security**: npm audit shows no high-severity vulnerabilities
- [ ] **Bundle Size**: Production bundle size within acceptable limits

### Integration with Universal System

#### Preparation for Future Tasks
- [ ] **API Integration Ready**: Axios and React Query configured for backend communication
- [ ] **Form Handling Ready**: React Hook Form and Zod validation configured
- [ ] **File Upload Ready**: React Dropzone configured for file processing features
- [ ] **UI Components Ready**: Shadcn/UI and Radix components available for interface development
- [ ] **State Management Ready**: React Query configured for server state management
- [ ] **Routing Ready**: Next.js App Router configured for multi-page application
- [ ] **Styling Ready**: Tailwind CSS configured with design system tokens
- [ ] **Testing Ready**: Testing utilities configured for component and integration testing

#### Backend Integration Preparation
- [ ] **API Client**: Axios configured with base URL and interceptors
- [ ] **Authentication**: Token handling and refresh logic prepared
- [ ] **Error Handling**: Global error handling for API responses
- [ ] **Loading States**: Loading and error state management configured
- [ ] **Real-time Updates**: WebSocket client preparation for live updates
- [ ] **File Upload**: Multipart form data handling for file uploads

### Continuous Validation

#### Automated Checks
- [ ] **Pre-commit Hooks**: Git hooks for linting and type checking
- [ ] **CI/CD Pipeline**: Automated validation in continuous integration
- [ ] **Dependency Updates**: Automated dependency vulnerability scanning
- [ ] **Performance Monitoring**: Build time and bundle size tracking
- [ ] **Health Checks**: Regular validation of development environment
- [ ] **Documentation Updates**: Automatic documentation generation from code
