"""
Migration management utilities for the Universal Product Automation System.

This module provides the MigrationManager class for handling database migrations
with state tracking, checksum validation, and idempotent operations.
"""

import hashlib
import time
from pathlib import Path
from typing import Set, Dict, Any, Optional, List, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

from .config import get_settings

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manages database migrations with state tracking and validation.
    
    This class provides functionality to:
    - Track applied migrations in a database table
    - Calculate and validate migration file checksums
    - Execute migrations with proper error handling
    - Prevent duplicate migration execution
    - Provide detailed status reporting
    """
    
    def __init__(self):
        """Initialize the migration manager with configuration."""
        self.settings = get_settings()
        self.migrations_dir = Path(__file__).parent.parent.parent / "migrations"
        self.database_url = self.settings.supabase_database_url
        
        if not self.database_url:
            raise ValueError("SUPABASE_DATABASE_URL not found in configuration")
    
    def get_database_connection(self) -> psycopg2.extensions.connection:
        """
        Create and return a PostgreSQL database connection.
        
        Returns:
            psycopg2.extensions.connection: Database connection with autocommit enabled
            
        Raises:
            psycopg2.OperationalError: If connection fails
        """
        try:
            conn = psycopg2.connect(
                self.database_url,
                connect_timeout=30,
                application_name="migration_manager"
            )
            conn.autocommit = True
            return conn
        except psycopg2.OperationalError as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def ensure_tracking_table(self) -> bool:
        """
        Ensure the migration tracking table exists.
        
        Returns:
            bool: True if table exists or was created successfully
            
        Raises:
            psycopg2.Error: If table creation fails
        """
        try:
            with self.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    # Check if table exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'schema_migrations'
                        )
                    """)
                    
                    table_exists = cursor.fetchone()[0]
                    
                    if not table_exists:
                        logger.info("Creating schema_migrations tracking table...")
                        
                        # Read and execute the tracking table migration
                        tracking_migration_path = self.migrations_dir / "000_migration_tracking.sql"
                        if tracking_migration_path.exists():
                            with open(tracking_migration_path, 'r', encoding='utf-8') as f:
                                sql_content = f.read()
                            cursor.execute(sql_content)
                            logger.info("✅ Migration tracking table created successfully")
                        else:
                            # Fallback: create table directly
                            cursor.execute("""
                                CREATE TABLE schema_migrations (
                                    version VARCHAR(255) PRIMARY KEY,
                                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                                    execution_time_ms INTEGER,
                                    checksum VARCHAR(64),
                                    rollback_sql TEXT,
                                    created_by VARCHAR(100) DEFAULT 'migration_script'
                                );
                                
                                CREATE INDEX idx_schema_migrations_applied_at ON schema_migrations(applied_at);
                                CREATE INDEX idx_schema_migrations_version ON schema_migrations(version);
                            """)
                            logger.info("✅ Migration tracking table created (fallback)")
                    else:
                        logger.debug("Migration tracking table already exists")
                    
                    return True
                    
        except psycopg2.Error as e:
            logger.error(f"Failed to ensure tracking table: {e}")
            raise
    
    def get_applied_migrations(self) -> Set[str]:
        """
        Get set of already applied migration versions.
        
        Returns:
            Set[str]: Set of migration versions that have been applied
        """
        try:
            with self.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version FROM schema_migrations ORDER BY applied_at")
                    return {row[0] for row in cursor.fetchall()}
        except psycopg2.ProgrammingError:
            # Table doesn't exist yet, return empty set
            logger.debug("schema_migrations table doesn't exist yet")
            return set()
        except psycopg2.Error as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return set()
    
    def calculate_checksum(self, file_path: Path) -> str:
        """
        Calculate SHA-256 checksum of migration file.
        
        Args:
            file_path (Path): Path to the migration file
            
        Returns:
            str: SHA-256 checksum as hexadecimal string
            
        Raises:
            FileNotFoundError: If migration file doesn't exist
            IOError: If file cannot be read
        """
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            return hashlib.sha256(content).hexdigest()
        except (FileNotFoundError, IOError) as e:
            logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            raise
    
    def validate_migration_integrity(self) -> Tuple[bool, List[str]]:
        """
        Verify applied migrations haven't been modified.
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_issues)
        """
        issues = []
        
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT version, checksum 
                        FROM schema_migrations 
                        WHERE checksum IS NOT NULL
                        ORDER BY version
                    """)
                    
                    applied_migrations = cursor.fetchall()
                    
                    for migration in applied_migrations:
                        version = migration['version']
                        stored_checksum = migration['checksum']
                        
                        # Find the migration file
                        migration_file = self.migrations_dir / f"{version}.sql"
                        
                        if not migration_file.exists():
                            issues.append(f"Migration file missing: {version}.sql")
                            continue
                        
                        # Calculate current checksum
                        try:
                            current_checksum = self.calculate_checksum(migration_file)
                            if current_checksum != stored_checksum:
                                issues.append(f"Migration file modified: {version}.sql (checksum mismatch)")
                        except Exception as e:
                            issues.append(f"Cannot validate {version}.sql: {e}")
                    
                    return len(issues) == 0, issues
                    
        except psycopg2.Error as e:
            issues.append(f"Database error during integrity check: {e}")
            return False, issues
    
    def record_migration(self, version: str, checksum: str, execution_time_ms: int) -> bool:
        """
        Record a successfully applied migration in the tracking table.
        
        Args:
            version (str): Migration version (filename without extension)
            checksum (str): SHA-256 checksum of the migration file
            execution_time_ms (int): Execution time in milliseconds
            
        Returns:
            bool: True if recorded successfully
        """
        try:
            with self.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO schema_migrations (version, checksum, execution_time_ms)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (version) DO UPDATE SET
                            checksum = EXCLUDED.checksum,
                            execution_time_ms = EXCLUDED.execution_time_ms,
                            applied_at = CURRENT_TIMESTAMP
                    """, (version, checksum, execution_time_ms))
                    
                    logger.info(f"✅ Recorded migration: {version} ({execution_time_ms}ms)")
                    return True
                    
        except psycopg2.Error as e:
            logger.error(f"Failed to record migration {version}: {e}")
            return False
    
    def get_migration_files(self) -> List[Path]:
        """
        Get sorted list of migration files.
        
        Returns:
            List[Path]: Sorted list of migration file paths
        """
        if not self.migrations_dir.exists():
            logger.warning(f"Migrations directory not found: {self.migrations_dir}")
            return []
        
        migration_files = sorted([
            f for f in self.migrations_dir.glob("*.sql") 
            if f.is_file()
        ])
        
        logger.debug(f"Found {len(migration_files)} migration files")
        return migration_files
    
    def get_pending_migrations(self) -> List[Path]:
        """
        Get list of migrations that haven't been applied yet.
        
        Returns:
            List[Path]: List of pending migration file paths
        """
        all_migrations = self.get_migration_files()
        applied_migrations = self.get_applied_migrations()
        
        pending = []
        for migration_file in all_migrations:
            version = migration_file.stem  # filename without extension
            if version not in applied_migrations:
                pending.append(migration_file)
        
        logger.info(f"Found {len(pending)} pending migrations")
        return pending
    
    def get_migration_status(self) -> Dict[str, Any]:
        """
        Get comprehensive migration status information.
        
        Returns:
            Dict[str, Any]: Status information including applied/pending counts
        """
        all_migrations = self.get_migration_files()
        applied_migrations = self.get_applied_migrations()
        pending_migrations = self.get_pending_migrations()
        
        # Check integrity
        is_valid, integrity_issues = self.validate_migration_integrity()
        
        return {
            'total_migrations': len(all_migrations),
            'applied_count': len(applied_migrations),
            'pending_count': len(pending_migrations),
            'applied_migrations': sorted(list(applied_migrations)),
            'pending_migrations': [m.stem for m in pending_migrations],
            'integrity_valid': is_valid,
            'integrity_issues': integrity_issues,
            'migrations_dir': str(self.migrations_dir),
            'tracking_table_exists': len(applied_migrations) > 0 or self._tracking_table_exists()
        }
    
    def _tracking_table_exists(self) -> bool:
        """
        Check if the migration tracking table exists.
        
        Returns:
            bool: True if table exists
        """
        try:
            with self.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'schema_migrations'
                        )
                    """)
                    return cursor.fetchone()[0]
        except psycopg2.Error:
            return False
