# Task 3.1: Migration System Fix & Tracking

## Overview
Fix the broken migration system that currently fails when re-running migrations, particularly the first migration (001_initial_schema.sql). Implement proper migration state tracking to ensure migrations are idempotent and only run once.

## Problem Statement
The current migration system has critical flaws:
- **Migration 001 fails on re-run**: Attempts to create existing extensions, enums, and tables
- **No state tracking**: All migrations run every time, causing errors and potential data corruption
- **Non-idempotent operations**: Migrations assume clean database state
- **Poor error handling**: Unclear error messages and no rollback guidance

## Business Impact
- **Blocks deployments**: Cannot safely run migrations in production
- **Development friction**: Developers cannot reset/update database schema
- **Risk of data corruption**: Failed migrations leave database in inconsistent state
- **Prevents schema evolution**: Cannot add new migrations safely

## Technical Requirements

### 1. Migration Tracking System
- Create `schema_migrations` table to track applied migrations
- Store migration version, timestamp, execution time, and checksum
- Query tracking table before running migrations
- Only execute unapplied migrations

### 2. Idempotent Migration Fixes
- Fix `001_initial_schema.sql` with proper `IF NOT EXISTS` checks
- Handle enum type creation safely (PostgreSQL doesn't support `CREATE TYPE IF NOT EXISTS`)
- Convert all table creation to `CREATE TABLE IF NOT EXISTS`
- Add constraint existence checking before creation
- Implement safe index creation

### 3. Enhanced Migration Runner
- Update `run_migrations.py` with state tracking logic
- Add migration validation and integrity checking
- Implement proper error handling and rollback guidance
- Add detailed logging and status reporting
- Support for migration dependencies and ordering

### 4. Testing & Validation
- Test on clean database (all migrations from scratch)
- Test on existing database (only new migrations)
- Test re-running migrations (should be no-op)
- Validate rollback procedures
- Performance testing for large migration sets

## Implementation Plan

### Phase 1: Migration Tracking Infrastructure
1. **Create Migration Tracking Table**
   ```sql
   CREATE TABLE IF NOT EXISTS schema_migrations (
       version VARCHAR(255) PRIMARY KEY,
       applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
       execution_time_ms INTEGER,
       checksum VARCHAR(64)
   );
   ```

2. **Update Migration Runner Core Logic**
   ```python
   def get_applied_migrations() -> Set[str]:
       """Query database for already applied migrations"""
   
   def calculate_migration_checksum(file_path: Path) -> str:
       """Calculate SHA-256 checksum of migration file"""
   
   def apply_migration(file_path: Path) -> bool:
       """Apply single migration and record in tracking table"""
   
   def validate_migration_integrity() -> bool:
       """Verify applied migrations haven't been modified"""
   ```

### Phase 2: Fix Existing Migrations
1. **Fix 001_initial_schema.sql**
   - Add `CREATE EXTENSION IF NOT EXISTS` for uuid-ossp
   - Handle enum types with DO blocks and existence checks
   - Convert all tables to `CREATE TABLE IF NOT EXISTS`
   - Add constraint existence checking
   - Implement safe index creation

2. **Verify Other Migrations**
   - Ensure 002_seed_data.sql remains idempotent
   - Verify 003_invoice_processing_fields.sql idempotency
   - Test all migrations work with new tracking system

### Phase 3: Enhanced Error Handling
1. **Comprehensive Error Messages**
   - Clear error descriptions for common failures
   - Troubleshooting guidance for migration issues
   - Connection health checks and diagnostics

2. **Rollback Foundation**
   - Document rollback procedures for each migration
   - Add rollback validation and safety checks
   - Prepare for future automated rollback capability

### Phase 4: Testing & Documentation
1. **Comprehensive Testing**
   - Unit tests for migration runner functions
   - Integration tests with real database
   - Performance tests with multiple migrations
   - Error scenario testing

2. **Documentation Updates**
   - Update migration workflow documentation
   - Add troubleshooting guide
   - Document best practices for new migrations

## Technical Specifications

### Migration Tracking Schema
```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(255) PRIMARY KEY,           -- Migration filename (001_initial_schema)
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER,                  -- Execution time in milliseconds
    checksum VARCHAR(64),                       -- SHA-256 checksum of migration file
    rollback_sql TEXT                          -- Future: rollback SQL for this migration
);
```

### Idempotent Enum Creation Pattern
```sql
-- Safe enum creation for PostgreSQL
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'file_type') THEN
        CREATE TYPE file_type AS ENUM ('pdf', 'csv', 'xlsx', 'manual');
    END IF;
END $$;
```

### Safe Constraint Addition
```sql
-- Check constraint existence before creation
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_confidence_score') THEN
        ALTER TABLE products ADD CONSTRAINT chk_confidence_score 
            CHECK (scraping_confidence >= 0 AND scraping_confidence <= 100);
    END IF;
END $$;
```

### Migration Runner Workflow
```python
def run_migrations():
    """Enhanced migration runner with state tracking"""
    
    # 1. Ensure migration tracking table exists
    ensure_migration_tracking_table()
    
    # 2. Get applied migrations from database
    applied_migrations = get_applied_migrations()
    
    # 3. Find migration files and determine order
    migration_files = get_migration_files_ordered()
    
    # 4. Validate integrity of applied migrations
    validate_applied_migrations_integrity(applied_migrations)
    
    # 5. Execute only new migrations
    for migration_file in migration_files:
        if migration_file.stem not in applied_migrations:
            apply_migration_with_tracking(migration_file)
    
    # 6. Report final status
    report_migration_status()
```

## Success Criteria

### Functional Requirements
- [ ] Migration 001 runs successfully on existing databases without errors
- [ ] Re-running migrations multiple times produces no errors or changes
- [ ] New migrations are tracked and only applied once
- [ ] Clear status reporting shows which migrations have been applied
- [ ] All existing migrations work with new tracking system

### Performance Requirements
- [ ] Migration tracking adds <100ms overhead per migration
- [ ] Large migration sets (10+ files) complete in reasonable time
- [ ] Database connection pooling prevents connection exhaustion

### Reliability Requirements
- [ ] Failed migrations don't corrupt tracking state
- [ ] Partial migration failures are clearly reported
- [ ] Database state remains consistent after any failure
- [ ] Rollback procedures are documented and tested

### Usability Requirements
- [ ] Clear error messages for common migration issues
- [ ] Status reporting shows progress and completion
- [ ] Documentation enables independent troubleshooting
- [ ] Development workflow is smooth and predictable

## Risk Mitigation

### Technical Risks
- **Migration corruption**: Comprehensive testing and validation
- **Performance impact**: Lightweight tracking with minimal overhead
- **Compatibility issues**: Test with all existing migrations
- **Rollback complexity**: Start with documentation, build automation later

### Operational Risks
- **Production deployment**: Thorough testing in staging environment
- **Data loss**: Backup procedures and rollback documentation
- **Downtime**: Fast migration execution and clear status reporting
- **Team adoption**: Clear documentation and training

## Dependencies
- **Task 3 completed**: Enhanced Invoice Parser provides stable foundation
- **Database access**: Requires working Supabase connection
- **Python environment**: psycopg2-binary for direct PostgreSQL access

## Deliverables
1. **Enhanced Migration Runner** (`run_migrations.py`)
2. **Fixed Initial Migration** (`001_initial_schema.sql`)
3. **Migration Tracking System** (database table and utilities)
4. **Comprehensive Tests** (unit and integration tests)
5. **Updated Documentation** (workflow and troubleshooting guides)
6. **Rollback Procedures** (documentation and validation)

## Timeline
- **Phase 1**: Migration tracking infrastructure (2-3 hours)
- **Phase 2**: Fix existing migrations (2-3 hours)
- **Phase 3**: Enhanced error handling (1-2 hours)
- **Phase 4**: Testing and documentation (2-3 hours)
- **Total**: 7-11 hours of development work

## Future Enhancements
- **Automated Rollback**: Implement automatic rollback capability
- **Migration Dependencies**: Support for complex migration dependencies
- **Parallel Execution**: Run independent migrations in parallel
- **Migration Validation**: Pre-flight checks for migration safety
- **Monitoring Integration**: Connect to application monitoring systems
