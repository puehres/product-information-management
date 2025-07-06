-- Migration tracking table for Universal Product Automation System
-- This migration creates the infrastructure to track applied migrations
-- and prevent duplicate executions with integrity validation

-- Create migration tracking table
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
CREATE INDEX IF NOT EXISTS idx_schema_migrations_version ON schema_migrations(version);

-- Comment for documentation
COMMENT ON TABLE schema_migrations IS 'Tracks applied database migrations with checksums and execution metadata';
COMMENT ON COLUMN schema_migrations.version IS 'Migration filename without extension (e.g., 001_initial_schema)';
COMMENT ON COLUMN schema_migrations.applied_at IS 'Timestamp when migration was applied';
COMMENT ON COLUMN schema_migrations.execution_time_ms IS 'Migration execution time in milliseconds';
COMMENT ON COLUMN schema_migrations.checksum IS 'SHA-256 checksum of migration file for integrity validation';
COMMENT ON COLUMN schema_migrations.rollback_sql IS 'Future: SQL commands to rollback this migration';
COMMENT ON COLUMN schema_migrations.created_by IS 'System or user that applied the migration';
