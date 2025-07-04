name: "MVP Database Design (Supabase) - Simplified PRP"
description: |
  Comprehensive Supabase PostgreSQL database setup for the Universal Product Automation System MVP 
  including Supabase project configuration in eu-central-1 (Frankfurt) region, simplified database 
  schema with 4 core tables, Supabase client integration, database relationships and constraints, 
  Lawn Fawn supplier seed data, database utility functions, performance indexing, and local 
  development configuration with cloud database.

---

## Goal
Establish a production-ready Supabase PostgreSQL database foundation for the MVP that supports the core Lawn Fawn → Gambio automation workflow. This includes setting up the Supabase project, implementing a simplified 4-table schema, integrating Supabase clients for both Python and TypeScript, and creating comprehensive database utilities with proper error handling and performance optimization.

## Why
- **MVP Foundation**: Provide the essential database infrastructure for validating the core automation workflow
- **Cost Optimization**: Use Supabase free tier ($0/month) instead of AWS RDS ($28/month) for MVP development
- **EU Compliance**: Frankfurt region (eu-central-1) for optimal performance with German users
- **Rapid Development**: Simplified schema focuses on core functionality without premature complexity
- **Scalability Path**: Clear evolution strategy from MVP to full universal schema in Phase 2
- **Integration Ready**: Database foundation that supports both Python backend and TypeScript frontend

## What
A fully functional Supabase database setup with:
- Supabase project configured in eu-central-1 (Frankfurt) region
- Simplified 4-table MVP schema (suppliers, upload_batches, products, images)
- Supabase client integration for Python (backend) and TypeScript (frontend)
- Database relationships, constraints, and performance indexes
- Lawn Fawn supplier seed data
- Comprehensive database utility functions with error handling
- Environment configuration for development and production
- Migration strategy and backup procedures
- Testing framework for database operations

### Success Criteria
- [ ] Supabase project created and configured in eu-central-1 region
- [ ] All 4 MVP tables created with proper constraints and relationships
- [ ] Performance indexes implemented and validated
- [ ] Lawn Fawn supplier seed data inserted successfully
- [ ] Python Supabase client integrated and tested in backend
- [ ] TypeScript Supabase client integrated and tested in frontend
- [ ] Database utility functions implemented with comprehensive error handling
- [ ] Environment variables configured for all environments
- [ ] Migration workflow established and documented
- [ ] Database operations tested with validation scripts
- [ ] Backup and recovery procedures documented and tested
- [ ] Performance benchmarks established (connections < 2s, queries < 100ms)

## All Needed Context

### Documentation & References
```yaml
# Supabase Setup and Configuration
- url: https://supabase.com/dashboard
  why: Project creation and management interface for eu-central-1 setup
  
- url: https://supabase.com/docs/guides/cli
  why: Command-line tools for local development and migrations
  
- url: https://supabase.com/docs/guides/platform/regions
  why: Region selection guide for eu-central-1 (Frankfurt) configuration
  
- url: https://supabase.com/docs/guides/getting-started/architecture
  why: Database configuration, limits, and architectural best practices

# Database Schema and PostgreSQL
- url: https://supabase.com/docs/guides/database/overview
  why: PostgreSQL with Supabase extensions and features
  
- url: https://supabase.com/docs/guides/database/tables
  why: Table creation, relationships, and constraint management
  
- url: https://www.postgresql.org/docs/current/ddl-constraints.html
  why: Foreign keys, check constraints, and data integrity patterns
  
- url: https://www.postgresql.org/docs/current/indexes.html
  why: Performance optimization strategies and index types

# Client Integration
- url: https://supabase.com/docs/reference/python/introduction
  why: supabase-py SDK for Python backend integration
  
- url: https://supabase.com/docs/reference/javascript/introduction
  why: JavaScript/TypeScript SDK for frontend integration
  
- url: https://supabase.com/docs/guides/auth/row-level-security
  why: Security configuration and access control patterns

# Migration and Development Workflow
- url: https://supabase.com/docs/guides/cli/local-development
  why: Local development workflow with Supabase CLI
  
- url: https://supabase.com/docs/guides/database/migrations
  why: Schema version control and migration management
  
- url: https://supabase.com/docs/guides/platform/backups
  why: Backup strategies and point-in-time recovery procedures

# Performance and Monitoring
- url: https://supabase.com/docs/guides/database/performance
  why: Query optimization and performance tuning
  
- url: https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler
  why: PgBouncer integration and connection pooling
</yaml>

### Current Codebase Structure
```bash
backend/
├── app/
│   ├── core/
│   │   ├── config.py              # Pydantic settings with env support
│   │   └── logging.py             # Structured logging configuration
│   ├── models/                    # Empty - needs database models
│   ├── services/                  # Empty - needs database services
│   ├── api/                       # Empty - needs API endpoints
│   └── utils/                     # Empty - needs utility functions
├── requirements.txt               # Includes SQLAlchemy, asyncpg, psycopg2
├── .env.example                   # Environment template
└── migrations/                    # Empty - needs migration files

frontend/
├── src/
│   ├── types/                     # Empty - needs database types
│   ├── services/                  # Empty - needs API integration
│   └── utils/                     # Empty - needs utility functions
├── package.json                   # Includes @supabase/supabase-js
└── .env.example                   # Environment template
```

### Desired Codebase Structure After Implementation
```bash
backend/
├── app/
│   ├── core/
│   │   ├── config.py              # Updated with Supabase settings
│   │   ├── logging.py             # Existing logging
│   │   └── database.py            # NEW: Supabase client manager
│   ├── models/
│   │   ├── __init__.py            # Model exports
│   │   ├── base.py                # NEW: Base model classes
│   │   ├── supplier.py            # NEW: Supplier model
│   │   ├── upload_batch.py        # NEW: Upload batch model
│   │   ├── product.py             # NEW: Product model
│   │   └── image.py               # NEW: Image model
│   ├── services/
│   │   ├── __init__.py            # Service exports
│   │   └── database_service.py    # NEW: Database operations service
│   └── utils/
│       └── database_utils.py      # NEW: Database utility functions
├── migrations/
│   ├── 001_initial_schema.sql     # NEW: Initial table creation
│   ├── 002_seed_data.sql          # NEW: Lawn Fawn seed data
│   └── 003_performance_indexes.sql # NEW: Additional indexes
└── tests/
    ├── test_database.py           # NEW: Database tests
    └── test_models.py             # NEW: Model tests

frontend/
├── src/
│   ├── types/
│   │   └── database.ts            # NEW: Auto-generated Supabase types
│   ├── services/
│   │   └── supabase.ts            # NEW: Supabase client configuration
│   └── utils/
│       └── database.ts            # NEW: Database utility functions
└── .env.local                     # NEW: Local environment variables
```

### Known Configuration Details & Library Quirks
```python
# CRITICAL: Supabase Python Client Configuration
# - Use SUPABASE_SERVICE_KEY for backend operations (full access)
# - Use SUPABASE_ANON_KEY for frontend operations (RLS protected)
# - Connection pooling handled automatically by Supabase
# - Real-time subscriptions available but not needed for MVP

# PostgreSQL with Supabase Extensions:
# - UUID generation with gen_random_uuid() function
# - JSONB support for flexible configuration storage
# - Full-text search with tsvector indexes available
# - Row Level Security (RLS) enabled but simplified for MVP

# Environment Configuration Gotchas:
# - SUPABASE_URL format: https://[project-ref].supabase.co
# - Database URL format: postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
# - API keys are different for anon vs service access
# - Region must be specified during project creation (cannot be changed)

# Migration Strategy:
# - Supabase CLI for local development and migration management
# - Standard PostgreSQL migrations work with Supabase
# - Auto-generated TypeScript types from schema
# - Point-in-time recovery available on Pro tier only

# Performance Considerations:
# - Free tier: 500MB storage, 2GB bandwidth/month
# - Connection limit: 60 concurrent connections on free tier
# - Query timeout: 8 seconds on free tier
# - Automatic connection pooling with PgBouncer
```

## Implementation Blueprint

### Database Schema Models

```python
# Core data models ensuring type safety and consistency
from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID

class FileType(str, Enum):
    PDF = "pdf"
    CSV = "csv"
    XLSX = "xlsx"
    MANUAL = "manual"

class BatchStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEW_REQUIRED = "review_required"

class ProductStatus(str, Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    SCRAPED = "scraped"
    TRANSLATED = "translated"
    READY = "ready"
    EXPORTED = "exported"
    FAILED = "failed"

class ImageType(str, Enum):
    MAIN = "main"
    ADDITIONAL = "additional"
    DETAIL = "detail"
    MANUAL_UPLOAD = "manual_upload"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Pydantic models for API and validation
class SupplierCreate(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=10)
    website_url: Optional[str] = Field(None, max_length=255)
    identifier_type: str = Field(default="sku", max_length=50)
    scraping_config: Optional[dict] = None
    search_url_template: Optional[str] = Field(None, max_length=500)
    active: bool = Field(default=True)

class SupplierResponse(SupplierCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime
```

### Implementation Tasks in Order

```yaml
Task 1: Supabase Project Setup
CREATE Supabase project:
  - NAVIGATE to https://supabase.com/dashboard
  - CREATE new project in eu-central-1 (Frankfurt) region
  - CONFIGURE project name: "product-automation-mvp"
  - GENERATE secure database password
  - SAVE project URL and API keys

Task 2: Environment Configuration
UPDATE backend/.env.example and frontend/.env.example:
  - ADD Supabase URL and API keys
  - ADD direct PostgreSQL connection string
  - UPDATE existing Redis and API key configurations
  - CREATE .env.local files for development

Task 3: Backend Supabase Integration
CREATE backend/app/core/database.py:
  - IMPLEMENT SupabaseManager class
  - ADD connection testing and health checks
  - INCLUDE error handling and retry logic
  - FOLLOW existing config.py patterns

UPDATE backend/app/core/config.py:
  - ADD Supabase configuration settings
  - MAINTAIN existing Pydantic patterns
  - INCLUDE validation for required Supabase fields

Task 4: Database Schema Creation
CREATE migrations/001_initial_schema.sql:
  - IMPLEMENT all 4 MVP tables with constraints
  - ADD proper indexes for performance
  - INCLUDE foreign key relationships
  - FOLLOW PostgreSQL best practices

EXECUTE schema migration:
  - APPLY migration to Supabase project
  - VERIFY table creation and constraints
  - TEST foreign key relationships

Task 5: Seed Data Implementation
CREATE migrations/002_seed_data.sql:
  - INSERT Lawn Fawn supplier configuration
  - INCLUDE search URL template and scraping config
  - ADD validation data for testing

Task 6: Database Models Implementation
CREATE backend/app/models/ files:
  - IMPLEMENT Pydantic models for all tables
  - ADD validation rules and constraints
  - INCLUDE type hints and documentation
  - FOLLOW existing code patterns

Task 7: Database Service Layer
CREATE backend/app/services/database_service.py:
  - IMPLEMENT CRUD operations for all models
  - ADD batch operations and transactions
  - INCLUDE comprehensive error handling
  - FOLLOW async/await patterns

Task 8: Frontend Supabase Integration
CREATE frontend/src/services/supabase.ts:
  - CONFIGURE Supabase client for frontend
  - IMPLEMENT type-safe database operations
  - ADD error handling and loading states
  - GENERATE TypeScript types from schema

Task 9: Database Utilities
CREATE utility functions:
  - IMPLEMENT connection testing
  - ADD database health checks
  - CREATE backup and restore utilities
  - INCLUDE performance monitoring

Task 10: Testing Implementation
CREATE comprehensive test suite:
  - UNIT tests for all database operations
  - INTEGRATION tests for Supabase client
  - PERFORMANCE tests for query optimization
  - ERROR handling tests for edge cases

Task 11: Performance Optimization
IMPLEMENT performance enhancements:
  - ADD composite indexes for common queries
  - OPTIMIZE query patterns
  - IMPLEMENT connection pooling
  - ADD query performance monitoring

Task 12: Documentation and Migration Guide
CREATE comprehensive documentation:
  - DOCUMENT setup procedures
  - CREATE troubleshooting guide
  - ESTABLISH backup procedures
  - DOCUMENT evolution path to Phase 2
```

### Task Implementation Details

#### Task 1: Supabase Project Setup
```bash
# Manual setup via Supabase Dashboard
# 1. Go to https://supabase.com/dashboard
# 2. Click "New Project"
# 3. Select organization: "stempelwunderwelt"
# 4. Project name: "product-automation-mvp"
# 5. Database password: [generate secure password]
# 6. Region: Europe (Central) - eu-central-1
# 7. Pricing plan: Free tier
# 8. Click "Create new project"

# Save these values for environment configuration:
# - Project URL: https://[project-ref].supabase.co
# - Anon key: [anon-key]
# - Service role key: [service-key]
# - Database password: [password]
```

#### Task 2: Environment Configuration
```bash
# Update backend/.env.example
cat >> backend/.env.example << 'EOF'

# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-key-here
SUPABASE_DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres

# Tax Configuration (MVP - hardcoded)
GAMBIO_DEFAULT_TAX_CLASS_ID=1

# Currency Configuration
DEFAULT_CURRENCY_FROM=USD
DEFAULT_CURRENCY_TO=EUR
DEFAULT_EXCHANGE_RATE=0.85
EOF

# Update frontend/.env.example
cat >> frontend/.env.example << 'EOF'

# Supabase Configuration (Frontend)
NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
EOF
```

#### Task 3: Backend Supabase Integration
```python
# backend/app/core/database.py
import os
from typing import Optional
from supabase import create_client, Client
from ..core.config import get_settings

class SupabaseManager:
    """Supabase client manager with connection testing and error handling."""
    
    def __init__(self):
        settings = get_settings()
        self.url = settings.supabase_url
        self.service_key = settings.supabase_service_key
        self._client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """Get or create Supabase client instance."""
        if self._client is None:
            self._client = create_client(self.url, self.service_key)
        return self._client
    
    async def test_connection(self) -> bool:
        """Test database connection with health check."""
        try:
            result = self.client.table('suppliers').select('count').execute()
            return True
        except Exception as e:
            logger.error(f"Supabase connection failed: {e}")
            return False
    
    async def health_check(self) -> dict:
        """Comprehensive health check with metrics."""
        # Implementation details...
```

## Validation Loop

### Level 1: Environment Setup
```bash
# Verify Supabase project creation
curl -H "apikey: $SUPABASE_ANON_KEY" \
     -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
     "$SUPABASE_URL/rest/v1/"

# Expected: {"message": "ok"} or similar success response
# If error: Check API keys, project URL, and network connectivity
```

### Level 2: Schema Creation
```bash
# Test database connection and schema
python -c "
from backend.app.core.database import SupabaseManager
import asyncio

async def test():
    db = SupabaseManager()
    connected = await db.test_connection()
    print(f'Connection: {\"✅\" if connected else \"❌\"}')

asyncio.run(test())
"

# Expected: Connection: ✅
# If error: Check environment variables, schema creation, network access
```

### Level 3: Model Validation
```bash
# Test model creation and validation
python -c "
from backend.app.models.supplier import SupplierCreate
supplier = SupplierCreate(name='Test', code='TEST', website_url='https://test.com')
print(f'Model validation: ✅ {supplier.name}')
"

# Expected: Model validation: ✅ Test
# If error: Check Pydantic model definitions, imports, type hints
```

### Level 4: Database Operations
```bash
# Test CRUD operations
python -c "
from backend.app.services.database_service import DatabaseService
import asyncio

async def test():
    db = DatabaseService()
    suppliers = await db.get_suppliers()
    print(f'Suppliers loaded: ✅ {len(suppliers)} found')

asyncio.run(test())
"

# Expected: Suppliers loaded: ✅ 1 found (Lawn Fawn)
# If error: Check service implementation, database permissions, seed data
```

### Level 5: Frontend Integration
```bash
cd frontend/

# Test TypeScript compilation with Supabase types
npm run type-check

# Test Supabase client initialization
node -e "
const { createClient } = require('@supabase/supabase-js');
const client = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY);
console.log('Frontend client: ✅ Initialized');
"

# Expected: Frontend client: ✅ Initialized
# If error: Check environment variables, package installation, TypeScript config
```

## Testing Strategy (MANDATORY)

### Backend Database Tests
- [ ] Supabase connection and health check tests
- [ ] Model validation and serialization tests
- [ ] CRUD operation tests for all tables
- [ ] Transaction and rollback tests
- [ ] Error handling and edge case tests
- [ ] Performance and query optimization tests

### Frontend Integration Tests
- [ ] Supabase client initialization tests
- [ ] TypeScript type generation validation
- [ ] API call and error handling tests
- [ ] Real-time subscription tests (if implemented)

### Integration Tests
- [ ] End-to-end database workflow tests
- [ ] Cross-table relationship validation
- [ ] Seed data integrity tests
- [ ] Migration and rollback tests

### Performance Tests
- [ ] Connection time benchmarks (< 2 seconds)
- [ ] Query performance tests (< 100ms for basic operations)
- [ ] Batch operation performance tests
- [ ] Concurrent connection tests

### Test Execution Plan
```bash
# Backend tests
cd backend/
python -m pytest tests/test_database.py -v
python -m pytest tests/test_models.py -v

# Frontend tests
cd frontend/
npm test -- --testPathPattern=database

# Integration tests
python -m pytest tests/test_integration.py -v

# Performance tests
python -m pytest tests/test_performance.py -v --benchmark
```

## Documentation Updates Required (MANDATORY)

### Core Documentation
- [ ] Update README.md with Supabase setup instructions
- [ ] Create database schema documentation
- [ ] Document environment variable requirements
- [ ] Create migration and backup procedures guide

### API Documentation
- [ ] Document all database models with examples
- [ ] Create API endpoint documentation for database operations
- [ ] Document error codes and handling procedures
- [ ] Create integration examples for frontend and backend

### Development Documentation
- [ ] Create local development setup guide
- [ ] Document testing procedures and requirements
- [ ] Create troubleshooting guide for common issues
- [ ] Document performance optimization strategies

### Code Documentation
- [ ] Add comprehensive docstrings to all functions (Google style)
- [ ] Document complex database queries and operations
- [ ] Add inline comments for configuration and setup
- [ ] Document type definitions and validation rules

## Final Validation Checklist
- [ ] Supabase project created in eu-central-1: Manual verification in dashboard
- [ ] All environment variables configured: `env | grep SUPABASE`
- [ ] Database schema created: `python -c "from backend.app.core.database import SupabaseManager; print('✅' if SupabaseManager().test_connection() else '❌')"`
- [ ] Seed data inserted: Query suppliers table for Lawn Fawn entry
- [ ] Backend integration working: `python -m pytest tests/test_database.py -v`
- [ ] Frontend integration working: `npm run type-check && npm test`
- [ ] Performance benchmarks met: Connection < 2s, queries < 100ms
- [ ] Documentation complete: All required docs created and updated
- [ ] Migration workflow established: Test migration creation and application
- [ ] Backup procedures documented: Test backup and restore procedures
- [ ] Ready for Task 3 (Invoice Parser): Database foundation complete

---

## Anti-Patterns to Avoid
- ❌ Don't use SQLAlchemy ORM with Supabase - use native Supabase client for better integration
- ❌ Don't hardcode Supabase URLs or keys - always use environment variables
- ❌ Don't skip Row Level Security setup - even if simplified for MVP
- ❌ Don't ignore connection pooling - Supabase handles it but understand the limits
- ❌ Don't create overly complex schema for MVP - focus on 4 core tables only
- ❌ Don't skip migration strategy - establish workflow from the beginning
- ❌ Don't ignore performance indexes - they're critical for query performance
- ❌ Don't skip error handling - database operations must be robust
- ❌ Don't forget TypeScript type generation - maintain type safety across stack
- ❌ Don't skip backup procedures - data protection is essential

## Confidence Score: 9/10
This PRP provides comprehensive context for Supabase database implementation with:
- Complete Supabase setup and configuration guidance
- Detailed schema implementation with all 4 MVP tables
- Full client integration for both Python and TypeScript
- Comprehensive testing strategy with executable validation
- Performance optimization and monitoring requirements
- Complete documentation and migration workflow
- Clear evolution path to Phase 2 universal schema

The high confidence score reflects the thorough analysis of existing codebase patterns, comprehensive Supabase documentation research, and systematic approach to database foundation implementation.
