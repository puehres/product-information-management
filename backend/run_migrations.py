#!/usr/bin/env python3
"""
Script to run database migrations for the Universal Product Automation System.

This script connects to Supabase and executes the SQL migration files.
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

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

def create_supabase_client() -> Client:
    """Create and return a Supabase client."""
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not service_key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
    
    print(f"🔗 Connecting to Supabase: {url}")
    return create_client(url, service_key)

def execute_sql_file(client: Client, file_path: Path) -> bool:
    """Execute a SQL file against the database using direct PostgreSQL connection."""
    try:
        print(f"📄 Reading SQL file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        if not sql_content.strip():
            print(f"⚠️  SQL file is empty: {file_path}")
            return True
        
        # Use direct PostgreSQL connection - skip Supabase REST API entirely
        return execute_sql_with_psycopg2(sql_content)
        
    except Exception as e:
        print(f"❌ Failed to execute {file_path}: {e}")
        return False

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

def run_migrations():
    """Run all migration files in order."""
    print("🚀 Starting database migration process...")
    
    # Load environment
    if not load_environment():
        return False
    
    # Create Supabase client
    try:
        client = create_supabase_client()
        print("✅ Supabase client created successfully")
    except Exception as e:
        print(f"❌ Failed to create Supabase client: {e}")
        return False
    
    # Find migration files
    migrations_dir = Path(__file__).parent / "migrations"
    if not migrations_dir.exists():
        print(f"❌ Migrations directory not found: {migrations_dir}")
        return False
    
    migration_files = sorted([f for f in migrations_dir.glob("*.sql") if f.is_file()])
    
    if not migration_files:
        print("⚠️  No migration files found")
        return True
    
    print(f"📋 Found {len(migration_files)} migration files:")
    for file in migration_files:
        print(f"  - {file.name}")
    
    # Execute each migration file
    success_count = 0
    for migration_file in migration_files:
        print(f"\n🔄 Processing migration: {migration_file.name}")
        if execute_sql_file(client, migration_file):
            success_count += 1
        else:
            print(f"❌ Migration failed: {migration_file.name}")
    
    # Summary
    print(f"\n📊 Migration Summary:")
    print(f"  Total files: {len(migration_files)}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {len(migration_files) - success_count}")
    
    if success_count == len(migration_files):
        print("🎉 All migrations completed successfully!")
        return True
    else:
        print("⚠️  Some migrations failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
