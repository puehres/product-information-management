#!/usr/bin/env python3
"""
Enhanced migration runner for the Universal Product Automation System.

This script provides robust database migration management with:
- State tracking to prevent duplicate executions
- Checksum validation for migration integrity
- Detailed progress reporting and error handling
- Idempotent operations for safe re-runs
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

# Import our new migration management utilities
from app.core.migration_manager import MigrationManager
from app.utils.migration_utils import (
    discover_migration_files,
    format_migration_summary,
    validate_migration_content,
    extract_migration_version
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_environment():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment from {env_path}")
    else:
        print(f"❌ Environment file not found: {env_path}")
        return False
    return True


def execute_sql_with_psycopg2(sql_content: str) -> bool:
    """Execute SQL using direct PostgreSQL connection with proper SSL configuration."""
    try:
        import psycopg2
        
        print("🔄 Connecting directly to PostgreSQL database...")
        
        # Get the database URL from environment
        database_url = os.getenv("SUPABASE_DATABASE_URL")
        if not database_url:
            print("❌ SUPABASE_DATABASE_URL not found in environment")
            return False
        
        print(f"🔗 Using connection: {database_url.replace(database_url.split('@')[0].split(':')[-1], '***')}")
        
        # Connect with proper SSL configuration
        conn = psycopg2.connect(
            database_url,
            connect_timeout=30,
            application_name="migration_script"
        )
        
        # Set autocommit for DDL statements
        conn.autocommit = True
        
        print("✅ Database connection established")
        
        with conn.cursor() as cursor:
            print("🔄 Executing SQL content...")
            
            # Execute the SQL content
            cursor.execute(sql_content)
            
            print("  ✅ SQL executed successfully")
        
        conn.close()
        print("🔌 Database connection closed")
        return True
        
    except ImportError:
        print("❌ psycopg2 not available. Please install it: pip install psycopg2-binary")
        return False
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("🔧 Troubleshooting tips:")
        print("   1. Check if SUPABASE_DATABASE_URL is correct")
        print("   2. Verify the database password is up to date")
        print("   3. Ensure SSL is properly configured")
        print("   4. Check if the Supabase project is active")
        return False
    except psycopg2.Error as e:
        print(f"❌ SQL execution failed: {e}")
        print("🔧 This might be due to:")
        print("   1. Invalid SQL syntax")
        print("   2. Missing permissions")
        print("   3. Database schema conflicts")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def run_migrations_with_tracking():
    """
    Enhanced migration runner with state tracking and validation.
    
    Returns:
        bool: True if all migrations completed successfully
    """
    print("🚀 Starting enhanced database migration process...")
    
    # Load environment
    if not load_environment():
        return False
    
    try:
        # Initialize migration manager
        print("🔧 Initializing migration manager...")
        migration_manager = MigrationManager()
        
        # Ensure tracking table exists
        print("📋 Ensuring migration tracking table exists...")
        migration_manager.ensure_tracking_table()
        
        # Get migration status
        print("📊 Checking migration status...")
        status = migration_manager.get_migration_status()
        
        print(f"📈 Migration Status:")
        print(f"  Total migrations: {status['total_migrations']}")
        print(f"  Applied: {status['applied_count']}")
        print(f"  Pending: {status['pending_count']}")
        print(f"  Integrity valid: {status['integrity_valid']}")
        
        if status['integrity_issues']:
            print("⚠️  Integrity issues found:")
            for issue in status['integrity_issues']:
                print(f"    - {issue}")
            return False
        
        # Get pending migrations
        pending_migrations = migration_manager.get_pending_migrations()
        
        if not pending_migrations:
            print("✅ All migrations are already applied!")
            return True
        
        print(f"\n🔄 Found {len(pending_migrations)} pending migrations:")
        for migration_file in pending_migrations:
            print(f"  - {migration_file.name}")
        
        # Validate migration content before execution
        print("\n🔍 Validating migration content...")
        for migration_file in pending_migrations:
            try:
                with open(migration_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                is_valid, warnings = validate_migration_content(content, migration_file)
                if warnings:
                    print(f"⚠️  Warnings for {migration_file.name}:")
                    for warning in warnings:
                        print(f"    - {warning}")
                
                if not is_valid:
                    print(f"❌ Migration validation failed: {migration_file.name}")
                    return False
                    
            except Exception as e:
                print(f"❌ Failed to validate {migration_file.name}: {e}")
                return False
        
        # Execute pending migrations
        print(f"\n🚀 Executing {len(pending_migrations)} pending migrations...")
        success_count = 0
        
        for migration_file in pending_migrations:
            version = extract_migration_version(migration_file)
            print(f"\n📄 Executing migration: {migration_file.name}")
            
            # Calculate checksum before execution
            try:
                checksum = migration_manager.calculate_checksum(migration_file)
                print(f"🔐 Checksum: {checksum[:16]}...")
            except Exception as e:
                print(f"❌ Failed to calculate checksum: {e}")
                continue
            
            # Execute migration with timing
            start_time = time.time()
            
            if execute_migration_file(migration_file):
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                # Record successful migration
                if migration_manager.record_migration(version, checksum, execution_time_ms):
                    success_count += 1
                    print(f"✅ Migration {version} completed in {execution_time_ms}ms")
                else:
                    print(f"⚠️  Migration {version} executed but failed to record in tracking table")
            else:
                print(f"❌ Migration {version} failed")
                break  # Stop on first failure
        
        # Final summary
        print(f"\n📊 Migration Execution Summary:")
        print(f"  Pending migrations: {len(pending_migrations)}")
        print(f"  Successfully executed: {success_count}")
        print(f"  Failed: {len(pending_migrations) - success_count}")
        
        if success_count == len(pending_migrations):
            print("🎉 All pending migrations completed successfully!")
            
            # Show final status
            final_status = migration_manager.get_migration_status()
            print(f"\n📈 Final Migration Status:")
            print(f"  Total migrations: {final_status['total_migrations']}")
            print(f"  Applied: {final_status['applied_count']}")
            print(f"  Pending: {final_status['pending_count']}")
            
            return True
        else:
            print("❌ Some migrations failed. Database may be in inconsistent state.")
            return False
            
    except Exception as e:
        print(f"❌ Migration process failed: {e}")
        logger.exception("Migration process error")
        return False


def execute_migration_file(file_path: Path) -> bool:
    """
    Execute a single migration file using direct PostgreSQL connection.
    
    Args:
        file_path (Path): Path to the migration file
        
    Returns:
        bool: True if migration executed successfully
    """
    try:
        print(f"📄 Reading migration file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        if not sql_content.strip():
            print(f"⚠️  Migration file is empty: {file_path}")
            return True
        
        # Execute using direct PostgreSQL connection
        return execute_sql_with_psycopg2(sql_content)
        
    except Exception as e:
        print(f"❌ Failed to execute migration {file_path}: {e}")
        logger.exception(f"Migration execution error: {file_path}")
        return False


def run_migrations():
    """Legacy migration runner - redirects to enhanced version."""
    return run_migrations_with_tracking()

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
