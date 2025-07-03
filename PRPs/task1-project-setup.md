name: "Universal Product Automation System - Project Setup & Environment"
description: |

## Purpose
Set up the complete development environment for the Universal Product Automation System including Python + Node.js development environment, project repository structure with universal architecture, virtual environment and dependencies, PostgreSQL + Redis database configuration, basic Docker setup, environment variable templates, and universal logging system initialization.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in .clinerules/CLAUDE.md

---

## Goal
Create a working development environment for the Universal Product Automation System that supports multiple suppliers (Craftlines, Lawn Fawn, Mama Elephant) with different data formats and matching strategies. The environment must be ready for Phase 1 development tasks including database schema implementation, supplier framework development, and file processing systems.

## Why
- **Business value**: Enables development of automated product import system for Stempelwunderwelt.at
- **Integration**: Foundation for universal supplier framework supporting any number of suppliers
- **Problems solved**: Eliminates manual product data entry, image handling, and translation workflows

## What
A complete development environment with:
- Python 3.9+ backend with FastAPI framework
- Node.js 18+ frontend with React TypeScript
- PostgreSQL database for structured data storage
- Redis for caching and session management
- Docker development environment
- Environment variable management
- Universal logging system
- Project structure following universal architecture patterns

### Success Criteria
- [ ] Python and Node.js development environments working
- [ ] Project structure created following universal architecture
- [ ] Virtual environment activated with all dependencies installed
- [ ] PostgreSQL and Redis running and accessible
- [ ] Docker development containers operational
- [ ] Environment variables template created and configured
- [ ] Basic logging system initialized and working
- [ ] Git repository initialized with proper .gitignore
- [ ] README.md with setup instructions completed
- [ ] Health checks for all services passing

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://docs.python.org/3/tutorial/venv.html
  why: Virtual environment setup and dependency management patterns
  
- url: https://fastapi.tiangolo.com/tutorial/first-steps/
  why: FastAPI project structure and basic setup
  
- url: https://react.dev/learn/start-a-new-react-project
  why: React TypeScript project setup with Vite
  
- url: https://www.postgresql.org/docs/current/tutorial-start.html
  why: PostgreSQL installation and initial configuration
  
- url: https://redis.io/docs/getting-started/
  why: Redis setup for development environment
  
- url: https://docs.docker.com/compose/gettingstarted/
  why: Docker Compose for development services
  
- file: PLANNING.md
  why: Universal architecture requirements and technology stack
  
- file: TASK.md
  why: Specific Task 1 requirements and dependencies
  
- file: .clinerules/CLAUDE.md
  why: Project-specific coding standards and conventions
```

### Current Codebase tree
```bash
.
├── .gitattributes
├── .gitignore
├── INITIAL_EXAMPLE.md
├── INITIAL.md
├── LICENSE
├── PLANNING.md
├── README.md
├── TASK.md
├── examples/
│   └── .gitkeep
├── features/
│   └── task1-project-setup.md
├── PRPs/
│   ├── EXAMPLE_multi_agent_prp.md
│   ├── task1-project-setup.md
│   └── templates/
│       └── prp_base.md
└── .clinerules/
    └── CLAUDE.md
```

### Desired Codebase tree with files to be added
```bash
.
├── backend/                          # Python FastAPI backend
│   ├── app/
│   │   ├── __init__.py              # Package init
│   │   ├── main.py                  # FastAPI application entry point
│   │   ├── core/                    # Universal core functionality (placeholder)
│   │   │   ├── __init__.py
│   │   │   ├── config.py            # Configuration management
│   │   │   └── logging.py           # Logging configuration
│   │   ├── suppliers/               # Supplier-specific configurations (placeholder)
│   │   │   └── __init__.py
│   │   ├── models/                  # Database models (placeholder for Task 2)
│   │   │   └── __init__.py
│   │   ├── services/                # Business logic services (placeholder)
│   │   │   └── __init__.py
│   │   ├── api/                     # FastAPI endpoints (placeholder)
│   │   │   ├── __init__.py
│   │   │   └── health.py            # Health check endpoints
│   │   └── utils/                   # Utility functions (placeholder)
│   │       └── __init__.py
│   ├── tests/                       # Backend tests (placeholder)
│   │   ├── __init__.py
│   │   └── test_health.py           # Health endpoint tests
│   ├── migrations/                  # Database migrations (placeholder for Task 2)
│   │   └── .gitkeep
│   ├── requirements.txt             # Python dependencies
│   ├── pyproject.toml              # Python project configuration
│   └── .env.example                # Backend environment variables
├── frontend/                        # React TypeScript frontend
│   ├── src/
│   │   ├── components/              # Universal UI components (placeholder)
│   │   │   └── .gitkeep
│   │   ├── pages/                   # Application pages (placeholder)
│   │   │   └── .gitkeep
│   │   ├── services/                # API integration (placeholder)
│   │   │   └── .gitkeep
│   │   ├── types/                   # TypeScript definitions (placeholder)
│   │   │   └── .gitkeep
│   │   ├── utils/                   # Frontend utilities (placeholder)
│   │   │   └── .gitkeep
│   │   ├── App.tsx                  # Main React component
│   │   ├── main.tsx                 # React entry point
│   │   └── index.css                # Global styles
│   ├── public/
│   │   └── vite.svg                 # Default Vite icon
│   ├── tests/                       # Frontend tests (placeholder)
│   │   └── .gitkeep
│   ├── package.json                 # Node.js dependencies
│   ├── tsconfig.json               # TypeScript configuration
│   ├── vite.config.ts              # Vite configuration
│   ├── tailwind.config.js          # Tailwind CSS configuration
│   ├── postcss.config.js           # PostCSS configuration
│   └── .env.example                # Frontend environment variables
├── docs/                           # Documentation
│   └── setup.md                    # Detailed setup instructions
├── examples/                       # Sample configurations and data
│   ├── .env.example               # Complete environment variables template
│   ├── docker-compose.yml         # Development environment setup
│   └── sample-data/               # Sample CSV files (placeholder)
│       └── .gitkeep
├── .env.example                   # Root environment variables template
├── docker-compose.yml             # Development services (PostgreSQL + Redis)
├── .gitignore                     # Updated Git ignore configuration
└── README.md                      # Updated project setup instructions
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Python 3.9+ required for modern type hints and async features
# CRITICAL: Node.js 18+ required for latest React and TypeScript support
# CRITICAL: PostgreSQL must be version 12+ for JSON column support
# CRITICAL: Redis 6+ required for modern caching features
# CRITICAL: FastAPI requires async/await throughout - no sync functions in async context
# CRITICAL: React 18+ uses strict mode - components may render twice in development
# CRITICAL: Vite requires ES modules - use import/export, not require()
# CRITICAL: SQLAlchemy 2.0+ has breaking changes from 1.x - use new syntax
# CRITICAL: Tailwind CSS requires PostCSS configuration for proper compilation
# CRITICAL: Environment variables must be prefixed with VITE_ for frontend access
# CRITICAL: Docker volumes need proper permissions on macOS/Linux
# CRITICAL: PostgreSQL default port 5432 may conflict with existing installations
# CRITICAL: Redis default port 6379 may conflict with existing installations
```

## Implementation Blueprint

### Data models and structure

```python
# backend/app/core/config.py - Configuration management
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/product_automation"
    redis_url: str = "redis://localhost:6379"
    
    # API Keys (for future tasks)
    firecrawl_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # Development
    debug: bool = True
    log_level: str = "DEBUG"
    environment: str = "development"
    
    # Server
    backend_port: int = 8000
    frontend_port: int = 3000
    
    class Config:
        env_file = ".env"

# backend/app/core/logging.py - Logging configuration
import logging
import structlog
from typing import Any, Dict

def configure_logging(log_level: str = "INFO") -> None:
    """Configure structured logging for the application."""
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
    )
```

### List of tasks to be completed

```yaml
Task 1: Setup Project Structure and Git
CREATE project directory structure:
  - Follow universal architecture from PLANNING.md
  - Create all placeholder directories with __init__.py files
  - Set up proper .gitignore for Python and Node.js
  - Initialize git repository if not already done

Task 2: Backend Environment Setup
CREATE backend/requirements.txt:
  - PATTERN: Include all dependencies from PLANNING.md technology stack
  - Pin versions for reproducible builds
  - Include development dependencies (pytest, black, mypy)

CREATE backend/pyproject.toml:
  - PATTERN: Modern Python project configuration
  - Include build system and tool configurations
  - Set up black, isort, and mypy configurations

CREATE backend/app/main.py:
  - PATTERN: FastAPI application with health endpoints
  - Include CORS configuration for frontend
  - Set up structured logging
  - Include basic error handling

Task 3: Frontend Environment Setup
CREATE frontend/package.json:
  - PATTERN: React TypeScript with Vite
  - Include all dependencies from PLANNING.md
  - Set up scripts for development and build

CREATE frontend configuration files:
  - vite.config.ts: Vite configuration with proxy for backend
  - tsconfig.json: TypeScript strict configuration
  - tailwind.config.js: Tailwind CSS with Shadcn/UI setup
  - postcss.config.js: PostCSS for Tailwind processing

CREATE frontend/src/App.tsx:
  - PATTERN: Basic React component with health check
  - Include Tailwind CSS styling
  - Set up routing structure (placeholder)

Task 4: Database and Redis Setup
CREATE docker-compose.yml:
  - PATTERN: PostgreSQL and Redis services
  - Include persistent volumes for data
  - Set up networking for service communication
  - Include environment variable configuration

CREATE database initialization:
  - Set up connection testing utilities
  - Create basic health check queries
  - Prepare for future migration system

Task 5: Environment Configuration
CREATE .env.example files:
  - Root level with all required variables
  - Backend specific variables
  - Frontend specific variables (VITE_ prefixed)
  - Include documentation for each variable

CREATE configuration management:
  - backend/app/core/config.py: Pydantic settings
  - Environment validation and defaults
  - Type-safe configuration access

Task 6: Logging and Monitoring
CREATE logging system:
  - backend/app/core/logging.py: Structured logging
  - Log format standardization
  - Development vs production configurations
  - Health check endpoints for monitoring

Task 7: Development Scripts and Documentation
CREATE development utilities:
  - Backend startup scripts
  - Frontend development server setup
  - Database connection testing
  - Service health checks

CREATE documentation:
  - README.md: Complete setup instructions
  - docs/setup.md: Detailed development guide
  - Include troubleshooting section

Task 8: Testing Framework Setup
CREATE test structure:
  - backend/tests/: pytest configuration
  - frontend/tests/: Jest/Vitest setup
  - Basic health endpoint tests
  - Test utilities and fixtures

Task 9: Code Quality Tools
SETUP development tools:
  - Black for Python formatting
  - ESLint for TypeScript linting
  - Mypy for Python type checking
  - Pre-commit hooks (optional)

Task 10: Validation and Health Checks
CREATE validation system:
  - Service startup verification
  - Database connection testing
  - Redis connection testing
  - Cross-service communication testing
```

### Per task pseudocode

```python
# Task 2: Backend Setup
# backend/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import Settings
from app.core.logging import configure_logging
import structlog

# PATTERN: FastAPI app factory pattern
def create_app() -> FastAPI:
    """Create FastAPI application with all configurations."""
    
    settings = Settings()
    configure_logging(settings.log_level)
    logger = structlog.get_logger()
    
    app = FastAPI(
        title="Universal Product Automation System",
        description="Backend API for product import automation",
        version="1.0.0",
        debug=settings.debug
    )
    
    # CRITICAL: CORS for frontend communication
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # Frontend URL
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Basic health check endpoint."""
        return {"status": "healthy", "service": "backend"}
    
    # Database health check
    @app.get("/health/db")
    async def database_health():
        """Database connection health check."""
        # TODO: Implement in Task 2 (database setup)
        return {"status": "healthy", "database": "postgresql"}
    
    return app

app = create_app()

# Task 3: Frontend Setup
# frontend/src/App.tsx
import React, { useEffect, useState } from 'react';
import './index.css';

interface HealthStatus {
  status: string;
  service: string;
}

function App() {
  const [backendHealth, setBackendHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // PATTERN: Health check on component mount
    const checkBackendHealth = async () => {
      try {
        const response = await fetch('http://localhost:8000/health');
        const data = await response.json();
        setBackendHealth(data);
      } catch (error) {
        console.error('Backend health check failed:', error);
        setBackendHealth({ status: 'error', service: 'backend' });
      } finally {
        setLoading(false);
      }
    };

    checkBackendHealth();
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-md">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          Universal Product Automation System
        </h1>
        
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium">Frontend:</span>
            <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm">
              Running
            </span>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium">Backend:</span>
            {loading ? (
              <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-sm">
                Checking...
              </span>
            ) : backendHealth?.status === 'healthy' ? (
              <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm">
                Healthy
              </span>
            ) : (
              <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-sm">
                Error
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;

# Task 4: Docker Setup
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: product_automation
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d product_automation"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

### Integration Points
```yaml
ENVIRONMENT:
  - Root .env.example: All variables with documentation
  - Backend .env: Database, API keys, server config
  - Frontend .env: VITE_ prefixed variables for build-time access
  
SERVICES:
  - PostgreSQL: Port 5432, persistent volume, health checks
  - Redis: Port 6379, persistent volume, health checks
  - Backend: Port 8000, CORS enabled, structured logging
  - Frontend: Port 3000, Vite dev server, proxy to backend
  
DEVELOPMENT:
  - Hot reload: Both backend (uvicorn) and frontend (Vite)
  - Code quality: Black, ESLint, Mypy, type checking
  - Testing: pytest (backend), Jest/Vitest (frontend)
  - Documentation: README.md, docs/setup.md
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Backend validation
cd backend
python -m black app/ --check          # Code formatting
python -m isort app/ --check-only     # Import sorting
python -m mypy app/                   # Type checking
python -m flake8 app/                 # Style checking

# Frontend validation
cd frontend
npm run lint                          # ESLint checking
npm run type-check                    # TypeScript checking

# Expected: No errors. If errors, fix them before proceeding.
```

### Level 2: Service Health Checks
```bash
# Start services
docker-compose up -d postgres redis

# Wait for services to be healthy
docker-compose ps

# Start backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Start frontend (in new terminal)
cd frontend
npm run dev

# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/health/db

# Expected: All return {"status": "healthy", ...}
```

### Level 3: Integration Tests
```bash
# Backend tests
cd backend
python -m pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Manual integration test
# 1. Open http://localhost:3000
# 2. Verify frontend shows "Backend: Healthy"
# 3. Check browser console for no errors
# 4. Verify backend logs show structured JSON output

# Expected: All tests pass, frontend connects to backend successfully
```

### Level 4: Environment Validation
```bash
# Test environment variable loading
cd backend
python -c "from app.core.config import Settings; s = Settings(); print(f'DB: {s.database_url}')"

# Test database connection
python -c "
import asyncpg
import asyncio
async def test():
    conn = await asyncpg.connect('postgresql://user:password@localhost:5432/product_automation')
    result = await conn.fetchval('SELECT 1')
    await conn.close()
    print(f'DB test: {result}')
asyncio.run(test())
"

# Test Redis connection
python -c "
import redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
r.set('test', 'value')
result = r.get('test')
print(f'Redis test: {result}')
"

# Expected: All connections successful, environment variables loaded correctly
```

## Final Validation Checklist
- [ ] All syntax/style checks pass: `black`, `isort`, `mypy`, `eslint`
- [ ] Docker services healthy: `docker-compose ps`
- [ ] Backend starts successfully: `uvicorn app.main:app --reload`
- [ ] Frontend starts successfully: `npm run dev`
- [ ] Health endpoints respond: `/health`, `/health/db`
- [ ] Frontend connects to backend: UI shows "Backend: Healthy"
- [ ] Database connection works: PostgreSQL accessible
- [ ] Redis connection works: Redis accessible
- [ ] Environment variables load correctly
- [ ] All tests pass: `pytest` and `npm test`
- [ ] Documentation complete: README.md with setup instructions
- [ ] Git repository clean: proper .gitignore, no secrets committed

---

## Anti-Patterns to Avoid
- ❌ Don't hardcode database credentials - use environment variables
- ❌ Don't skip health checks - they're critical for debugging
- ❌ Don't use sync functions in FastAPI async context
- ❌ Don't forget CORS configuration for frontend communication
- ❌ Don't commit .env files with real credentials
- ❌ Don't use different port numbers than specified (3000, 8000, 5432, 6379)
- ❌ Don't skip Docker volume configuration - data will be lost
- ❌ Don't ignore TypeScript errors in frontend
- ❌ Don't skip structured logging setup - needed for debugging
- ❌ Don't create files longer than 500 lines (per .clinerules/CLAUDE.md)

## Confidence Score: 9/10

High confidence due to:
- Clear technology stack defined in PLANNING.md
- Established patterns from project template
- Well-documented setup procedures
- Comprehensive validation gates
- Standard development tools and practices

Minor uncertainty on specific Docker configuration details for the development environment, but documentation provides clear guidance.
