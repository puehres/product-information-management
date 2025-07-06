name: "Migration System Fix & Tracking - Production-Ready Database Migrations"
description: |
  Fix the broken migration system that fails on re-runs and implement proper migration state tracking
  to ensure idempotent operations and reliable database schema evolution.

---

## Goal
Implement a robust, production-ready migration system with state tracking that prevents duplicate executions,
handles idempotent operations correctly, and provides clear error reporting. Fix the current issue where
migration 001 fails when re-run due to attempting to create existing database objects.

## Why
- **Deployment Blocker**: Current migration system prevents safe deployments and schema updates
- **Development Friction**: Developers cannot reset/update database schema reliably
- **Production Risk**: Failed migrations leave database in inconsistent state
- **Schema Evolution**: Cannot safely add new migrations without fixing foundation

## What
A complete migration tracking system with:
- Migration state tracking table to record applied migrations
- Idempotent migration fixes for all existing migrations
- Enhanced migration runner with validation and error handling
- Comprehensive testing for clean and existing database scenarios
- Foundation for future rollback capabilities

### Success Criteria
- [ ] Migration 001 runs successfully on existing databases without errors
- [ ] Re-running migrations multiple times produces no errors or changes
- [ ] New migrations are tracked and only applied once
- [ ] Clear status reporting shows which migrations have been applied
- [ ] All existing migrations work with the new tracking system
- [ ] Migration runner provides detailed error messages and troubleshooting guidance
- [ ] Foundation established for future rollback capabilities

## All Needed Context

### Documentation & References
```yaml
# PostgreSQL Migration Patterns
- url: https://www.postgresql.org/docs/current/ddl-schemas.html
  why: Understanding schema management and IF NOT EXISTS patterns
  
- url: https://www.postgresql.org/docs/current/sql-createtype.html
  why: Safe enum type creation patterns for PostgreSQL
  
- url: https://docs.python.org/3/library/hashlib.html
  why: SHA-256 checksum calculation for migration integrity validation

# Supabase Connection Patterns  
- file: backend/app/core/database.py
  why: Existing Supabase client patterns and connection management
  
- file: backend/run_migrations.py
  why: Current migration runner implementation to enhance
  
- file: backend/app/core/config.py
  why: Configuration patterns for database connection strings

# Migration File Patterns
- file: backend/migrations/001_initial_schema.sql
  why: Current problematic migration that needs idempotent fixes
  
- file: backend/migrations/002_seed_data.sql
  why: Example of idempotent migration with ON CONFLICT handling
  
- file: backend/migrations/003_invoice_processing_fields.sql
  why: Example of safe ALTER TABLE with IF NOT EXISTS patterns

# Testing Patterns
- file: backend/tests/connectivity/test_supabase_connectivity.py
  why: Database connectivity testing patterns to follow
  
- file: backend/conftest.py
  why: Test configuration and fixture patterns
```

### Current Codebase Structure
```bash
backend/
├── run_migrations.py              # Current migration runner (needs enhancement)
├── migrations/
│   ├── 001_initial_schema.sql     # Problematic migration (needs fixes)
│   ├── 002_seed_data.sql          # Good idempotent example
│   └── 003_invoice_processing_fields.sql  # Good IF NOT EXISTS example
├── app/
│   ├── core/
│   │   ├── database.py            # Supabase client management
│   │   └── config.py              # Configuration management
│   └── utils/
│       └── database_utils.py      # Database utility functions
└── tests/
    ├── connectivity/
    │   └── test_supabase_connectivity.py  # Connection testing patterns
    └── test_database.py           # Database testing patterns
```

### Desired Codebase Structure (additions)
```bash
backend/
├── run_migrations.py              # Enhanced with state tracking
├── migrations/
│   ├── 000_migration_tracking.sql # NEW: Migration tracking table
│   ├── 001_initial_schema.sql     # FIXED: Idempotent operations
│   ├── 002_seed_data.sql          # UNCHANGED: Already idempotent
│   └── 003_invoice_processing_fields.sql  # UNCHANGED: Already idempotent
├── app/
│   ├── core/
│   │   └── migration_manager.py   # NEW: Migration management utilities
│   └── utils/
│       └── migration_utils.py     # NEW: Migration helper functions
└── tests/
    ├── test_migration_system.py   # NEW: Migration system tests
    └── test_migration_tracking.py # NEW: Migration tracking tests
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: PostgreSQL enum type creation
# PostgreSQL doesn't support CREATE TYPE IF NOT EXISTS directly
# Must use DO blocks with existence checks:
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_name') THEN
        CREATE TYPE enum_name AS ENUM ('value1', 'value2');
    END IF;
END $$;

# CRITICAL: psycopg2 connection requirements
# Must use SUPABASE_DATABASE_URL with pooler hostname:
# aws-0-eu-central-1.pooler.supabase.com:6543
# NOT the standard db.project.supabase.co:5432

# CRITICAL: Migration file naming convention
# Files must be named with zero-padded numbers: 001_, 002_, etc.
# Sorted alphabetically to ensure correct execution order

# CRITICAL: Supabase transaction handling
# Set autocommit=True for DDL statements
# Use proper SSL configuration for pooler connections

# GOTCHA: SHA-256 checksums for file integrity
# Calculate checksums of migration files to detect modifications
# Store in tracking table to prevent execution of modified migrations
```

## Implementation Blueprint

### Data Models and Structure

Migration tracking table to record applied migrations:
```sql
-- Migration tracking table (000_migration_tracking.sql)
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(255) PRIMARY KEY,           -- Migration filename without extension
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER,                  -- Execution time in milliseconds
    checksum VARCHAR(64),                       -- SHA-256 checksum of migration file
    rollback_sql TEXT,                          -- Future: rollback SQL for this migration
    created_by VARCHAR(100) DEFAULT 'migration_script'
);

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_schema_migrations_applied_at ON schema_migrations(applied_at);

-- Comment for documentation
COMMENT ON TABLE schema_migrations IS 'Tracks applied database migrations with checksums and execution metadata';
```

Migration manager utility class:
```python
# app/core/migration_manager.py
from typing import Set, Dict, Any, Optional
from pathlib import Path
import hashlib
import time
import psycopg2
from .config import get_settings

class MigrationManager:
    """Manages database migrations with state tracking and validation."""
    
    def __init__(self):
        self.settings = get_settings()
        self.migrations_dir = Path(__file__).parent.parent.parent / "migrations"
    
    def get_applied_migrations(self) -> Set[str]:
        """Get set of already applied migration versions."""
    
    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of migration file."""
    
    def validate_migration_integrity(self) -> bool:
        """Verify applied migrations haven't been modified."""
    
    def apply_migration_with_tracking(self, file_path: Path) -> bool:
        """Apply migration and record in tracking table."""
```

### List of Tasks to Complete the PRP

```yaml
Task 1: Create Migration Tracking Infrastructure
MODIFY backend/run_migrations.py:
  - IMPORT new migration manager utilities
  - ADD migration tracking table creation
  - IMPLEMENT state checking before migration execution
  - PRESERVE existing error handling patterns

CREATE backend/migrations/000_migration_tracking.sql:
  - MIRROR pattern from existing migrations
  - CREATE schema_migrations table with proper constraints
  - ADD indexes for performance optimization
  - INCLUDE comprehensive comments

CREATE backend/app/core/migration_manager.py:
  - IMPLEMENT MigrationManager class with state tracking
  - ADD checksum calculation and validation
  - INCLUDE proper error handling and logging
  - FOLLOW existing database connection patterns

Task 2: Fix Existing Migration Idempotency
MODIFY backend/migrations/001_initial_schema.sql:
  - REPLACE CREATE TYPE with safe DO block patterns
  - CONVERT CREATE TABLE to CREATE TABLE IF NOT EXISTS
  - ADD constraint existence checking before creation
  - PRESERVE all existing table structures and relationships

VERIFY backend/migrations/002_seed_data.sql:
  - CONFIRM ON CONFLICT handling is correct
  - ENSURE idempotent INSERT operations
  - VALIDATE supplier data consistency

VERIFY backend/migrations/003_invoice_processing_fields.sql:
  - CONFIRM ADD COLUMN IF NOT EXISTS usage
  - VALIDATE constraint creation safety
  - ENSURE proper DO block patterns

Task 3: Enhanced Migration Runner
MODIFY backend/run_migrations.py:
  - ADD migration tracking table initialization
  - IMPLEMENT applied migration checking
  - ADD migration file validation and ordering
  - INCLUDE detailed progress reporting and error messages
  - PRESERVE existing psycopg2 connection patterns

CREATE backend/app/utils/migration_utils.py:
  - IMPLEMENT helper functions for file operations
  - ADD checksum calculation utilities
  - INCLUDE migration file discovery and sorting
  - FOLLOW existing utility function patterns

Task 4: Comprehensive Testing
CREATE backend/tests/test_migration_system.py:
  - TEST migration runner on clean database
  - TEST migration runner on existing database
  - TEST re-running migrations (should be no-op)
  - TEST migration tracking table functionality
  - FOLLOW existing test patterns from test_database.py

CREATE backend/tests/test_migration_tracking.py:
  - TEST migration state tracking
  - TEST checksum validation
  - TEST error handling for modified migrations
  - TEST migration ordering and dependencies
  - MIRROR patterns from connectivity tests

Task 5: Documentation and Validation
UPDATE backend/README.md:
  - ADD migration system documentation
  - INCLUDE troubleshooting guide
  - DOCUMENT new migration workflow
  - PRESERVE existing documentation structure

CREATE migration workflow documentation:
  - DOCUMENT best practices for new migrations
  - INCLUDE idempotent operation patterns
  - ADD rollback preparation guidelines
  - FOLLOW existing documentation style
```

### Per Task Pseudocode

```python
# Task 1: Migration Tracking Infrastructure
class MigrationManager:
    def ensure_tracking_table(self):
        """Ensure migration tracking table exists."""
        # PATTERN: Use direct psycopg2 connection like run_migrations.py
        with psycopg2.connect(self.database_url) as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                # CRITICAL: Use IF NOT EXISTS for safety
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version VARCHAR(255) PRIMARY KEY,
                        applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        execution_time_ms INTEGER,
                        checksum VARCHAR(64)
                    )
                """)
    
    def get_applied_migrations(self) -> Set[str]:
        """Get applied migration versions from tracking table."""
        # PATTERN: Query tracking table and return set of versions
        # GOTCHA: Handle case where tracking table doesn't exist yet
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version FROM schema_migrations")
                    return {row[0] for row in cursor.fetchall()}
        except psycopg2.ProgrammingError:
            # Table doesn't exist yet, return empty set
            return set()

# Task 2: Idempotent Migration Fixes
# Fix enum creation in 001_initial_schema.sql
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'file_type') THEN
        CREATE TYPE file_type AS ENUM ('pdf', 'csv', 'xlsx', 'manual');
    END IF;
END $$;

# Fix table creation
CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    -- ... rest of table definition
);

# Task 3: Enhanced Migration Runner
def run_migrations_with_tracking():
    """Enhanced migration runner with state tracking."""
    # PATTERN: Follow existing run_migrations.py structure
    migration_manager = MigrationManager()
    
    # 1. Ensure tracking table exists
    migration_manager.ensure_tracking_table()
    
    # 2. Get applied migrations
    applied = migration_manager.get_applied_migrations()
    
    # 3. Find and sort migration files
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    # 4. Execute only unapplied migrations
    for file_path in migration_files:
        version = file_path.stem
        if version not in applied:
            # CRITICAL: Calculate checksum before execution
            checksum = migration_manager.calculate_checksum(file_path)
            start_time = time.time()
            
            success = execute_sql_file(file_path)
            
            if success:
                execution_time = int((time.time() - start_time) * 1000)
                migration_manager.record_migration(version, checksum, execution_time)
```

### Integration Points
```yaml
DATABASE:
  - table: "schema_migrations for tracking applied migrations"
  - index: "CREATE INDEX idx_schema_migrations_applied_at ON schema_migrations(applied_at)"
  
CONFIG:
  - use: "existing SUPABASE_DATABASE_URL from backend/.env"
  - pattern: "Follow database.py connection patterns"
  
MIGRATION_FILES:
  - add: "000_migration_tracking.sql as first migration"
  - modify: "001_initial_schema.sql for idempotency"
  - preserve: "002_seed_data.sql and 003_invoice_processing_fields.sql"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
cd backend
python -m ruff check app/ --fix          # Auto-fix style issues
python -m mypy app/                      # Type checking
python -m ruff check run_migrations.py --fix  # Check migration runner

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests
```python
# CREATE tests/test_migration_system.py with these test cases:
def test_migration_tracking_table_creation():
    """Migration tracking table is created correctly."""
    manager = MigrationManager()
    manager.ensure_tracking_table()
    # Verify table exists and has correct structure

def test_applied_migrations_detection():
    """Applied migrations are detected correctly."""
    # Insert test migration record
    # Verify get_applied_migrations() returns correct set

def test_checksum_calculation():
    """Migration file checksums are calculated correctly."""
    # Create test migration file
    # Verify checksum calculation is consistent

def test_idempotent_migration_execution():
    """Migrations can be run multiple times safely."""
    # Run migration twice
    # Verify no errors and no duplicate data

def test_migration_ordering():
    """Migrations are executed in correct order."""
    # Verify file sorting and execution order
```

```bash
# Run and iterate until passing:
cd backend
python -m pytest tests/test_migration_system.py -v
python -m pytest tests/test_migration_tracking.py -v
# If failing: Read error, understand root cause, fix code, re-run
```

### Level 3: Integration Test
```bash
# Test on clean database (all migrations from scratch)
cd backend
python run_migrations.py

# Expected: All migrations execute successfully
# Verify: Check schema_migrations table has all entries

# Test on existing database (should be no-op)
python run_migrations.py

# Expected: "All migrations already applied" message
# Verify: No errors, no duplicate executions

# Test specific migration file
python -c "
from app.core.migration_manager import MigrationManager
manager = MigrationManager()
print('Applied migrations:', manager.get_applied_migrations())
print('Tracking table health:', manager.validate_migration_integrity())
"
```

## Testing Strategy (MANDATORY)

### Backend Tests
- [ ] Unit tests for MigrationManager class methods
- [ ] Integration tests for migration runner execution
- [ ] Idempotency tests for all migration files
- [ ] Error handling tests for various failure scenarios
- [ ] Checksum validation tests for file integrity
- [ ] Database state validation tests

### Migration Tests
- [ ] Clean database migration execution (all from scratch)
- [ ] Existing database migration execution (only new ones)
- [ ] Re-run migration tests (should be no-op)
- [ ] Modified migration file detection tests
- [ ] Migration ordering and dependency tests

### Test Execution Plan
- [ ] Run existing tests to ensure no regression: `pytest tests/ -v`
- [ ] Add new migration system tests with comprehensive coverage
- [ ] Validate test coverage meets project standards (>90%)
- [ ] Test error scenarios and edge cases thoroughly
- [ ] Performance test with multiple migration files

## Documentation Updates Required (MANDATORY)

### Core Documentation
- [ ] Update backend/README.md with new migration workflow
- [ ] Create migration best practices guide
- [ ] Document troubleshooting procedures for common issues
- [ ] Update architecture docs with migration system design

### Code Documentation
- [ ] Add comprehensive docstrings to MigrationManager class (Google style)
- [ ] Add inline comments for complex migration logic
- [ ] Document migration file naming conventions
- [ ] Create examples of idempotent migration patterns

### Migration Documentation
- [ ] Document safe enum creation patterns
- [ ] Create template for new migration files
- [ ] Document rollback preparation guidelines
- [ ] Add troubleshooting guide for migration failures

## Final Validation Checklist
- [ ] All tests pass: `python -m pytest tests/ -v`
- [ ] No linting errors: `python -m ruff check app/ run_migrations.py`
- [ ] No type errors: `python -m mypy app/`
- [ ] Migration runner works on clean database: `python run_migrations.py`
- [ ] Migration runner works on existing database (no-op): `python run_migrations.py`
- [ ] All migration files are idempotent
- [ ] Migration tracking table created and populated correctly
- [ ] Checksum validation prevents modified migration execution
- [ ] Error messages are clear and actionable
- [ ] Documentation updated as specified above
- [ ] All testing requirements met
- [ ] Ready for PRP completion workflow

---

## Anti-Patterns to Avoid
- ❌ Don't create new database connection patterns - use existing psycopg2 approach
- ❌ Don't skip checksum validation - it prevents dangerous modified migrations
- ❌ Don't ignore migration ordering - files must execute in correct sequence
- ❌ Don't use CREATE TYPE without existence checks - PostgreSQL will error
- ❌ Don't hardcode database URLs - use configuration management
- ❌ Don't catch all exceptions - be specific about error handling
- ❌ Don't skip testing requirements - migration system must be bulletproof
- ❌ Don't modify existing migration files after they're applied in production
- ❌ Don't skip documentation updates - future developers need clear guidance
