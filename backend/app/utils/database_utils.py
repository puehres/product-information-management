"""
Database utility functions for the Universal Product Automation System.

This module provides utility functions for database operations, migrations,
and maintenance tasks.
"""

import asyncio
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import structlog
from ..core.database import get_supabase_client, supabase_manager
from ..core.config import get_settings

logger = structlog.get_logger(__name__)


async def run_migration_file(file_path: str) -> bool:
    """
    Execute a SQL migration file against the database.
    
    Args:
        file_path: Path to the SQL migration file.
        
    Returns:
        bool: True if migration was successful, False otherwise.
    """
    try:
        if not os.path.exists(file_path):
            logger.error("Migration file not found", file_path=file_path)
            return False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        if not sql_content.strip():
            logger.warning("Migration file is empty", file_path=file_path)
            return True
        
        # Split SQL content by statements (basic approach)
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        client = get_supabase_client()
        
        for i, statement in enumerate(statements):
            try:
                # Execute each statement
                result = client.rpc('exec_sql', {'sql': statement}).execute()
                logger.info(
                    "Migration statement executed",
                    file_path=file_path,
                    statement_number=i + 1,
                    total_statements=len(statements)
                )
            except Exception as stmt_error:
                logger.error(
                    "Migration statement failed",
                    file_path=file_path,
                    statement_number=i + 1,
                    statement=statement[:100] + "..." if len(statement) > 100 else statement,
                    error=str(stmt_error)
                )
                # Continue with other statements for now
                # In production, you might want to stop on first error
        
        logger.info("Migration file completed", file_path=file_path)
        return True
        
    except Exception as e:
        logger.error("Failed to run migration file", file_path=file_path, error=str(e))
        return False


async def run_all_migrations() -> bool:
    """
    Run all migration files in the migrations directory.
    
    Returns:
        bool: True if all migrations were successful, False otherwise.
    """
    try:
        migrations_dir = Path(__file__).parent.parent.parent / "migrations"
        
        if not migrations_dir.exists():
            logger.error("Migrations directory not found", path=str(migrations_dir))
            return False
        
        # Get all SQL files and sort them
        migration_files = sorted([
            f for f in migrations_dir.glob("*.sql")
            if f.is_file()
        ])
        
        if not migration_files:
            logger.info("No migration files found")
            return True
        
        logger.info("Starting migration process", total_files=len(migration_files))
        
        success_count = 0
        for migration_file in migration_files:
            logger.info("Running migration", file=migration_file.name)
            
            if await run_migration_file(str(migration_file)):
                success_count += 1
                logger.info("Migration completed successfully", file=migration_file.name)
            else:
                logger.error("Migration failed", file=migration_file.name)
        
        all_successful = success_count == len(migration_files)
        
        logger.info(
            "Migration process completed",
            successful=success_count,
            total=len(migration_files),
            all_successful=all_successful
        )
        
        return all_successful
        
    except Exception as e:
        logger.error("Failed to run migrations", error=str(e))
        return False


async def test_database_connection() -> Dict[str, Any]:
    """
    Test the database connection and return detailed status.
    
    Returns:
        Dict with connection test results.
    """
    try:
        start_time = asyncio.get_event_loop().time()
        
        # Test basic connection
        connected = await supabase_manager.test_connection()
        
        end_time = asyncio.get_event_loop().time()
        connection_time = round((end_time - start_time) * 1000, 2)
        
        if not connected:
            return {
                "status": "failed",
                "connection_time_ms": connection_time,
                "error": "Connection test failed",
                "timestamp": end_time
            }
        
        # Get comprehensive health check
        health_data = await supabase_manager.health_check()
        
        return {
            "status": "success",
            "connection_time_ms": connection_time,
            "health_data": health_data,
            "timestamp": end_time
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }


async def get_table_info(table_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a database table.
    
    Args:
        table_name: Name of the table to inspect.
        
    Returns:
        Dict with table information.
    """
    try:
        return await supabase_manager.get_table_info(table_name)
    except Exception as e:
        logger.error("Failed to get table info", table=table_name, error=str(e))
        return {
            "error": str(e),
            "table_name": table_name
        }


async def get_all_tables_info() -> List[Dict[str, Any]]:
    """
    Get information about all tables in the database.
    
    Returns:
        List of table information dictionaries.
    """
    try:
        # List of expected tables
        expected_tables = ["suppliers", "upload_batches", "products", "images"]
        
        tables_info = []
        for table_name in expected_tables:
            table_info = await get_table_info(table_name)
            tables_info.append(table_info)
        
        return tables_info
        
    except Exception as e:
        logger.error("Failed to get all tables info", error=str(e))
        return []


async def validate_database_schema() -> Dict[str, Any]:
    """
    Validate that the database schema matches expectations.
    
    Returns:
        Dict with validation results.
    """
    try:
        validation_results = {
            "status": "unknown",
            "tables": {},
            "errors": [],
            "warnings": []
        }
        
        # Expected table structure
        expected_tables = {
            "suppliers": {
                "required_columns": ["id", "name", "code", "website_url", "identifier_type", 
                                   "scraping_config", "search_url_template", "active", 
                                   "created_at", "updated_at"],
                "constraints": ["PRIMARY KEY", "UNIQUE"]
            },
            "upload_batches": {
                "required_columns": ["id", "supplier_id", "batch_name", "file_type", 
                                   "file_path", "file_size", "status", "total_products",
                                   "processed_products", "failed_products", "created_at", "updated_at"],
                "constraints": ["PRIMARY KEY", "FOREIGN KEY"]
            },
            "products": {
                "required_columns": ["id", "batch_id", "supplier_id", "supplier_sku", 
                                   "status", "created_at", "updated_at"],
                "constraints": ["PRIMARY KEY", "FOREIGN KEY", "UNIQUE"]
            },
            "images": {
                "required_columns": ["id", "product_id", "image_type", "sequence_number", 
                                   "processing_status", "created_at", "updated_at"],
                "constraints": ["PRIMARY KEY", "FOREIGN KEY", "UNIQUE"]
            }
        }
        
        all_valid = True
        
        for table_name, expected in expected_tables.items():
            table_info = await get_table_info(table_name)
            
            if "error" in table_info:
                validation_results["errors"].append(f"Table {table_name}: {table_info['error']}")
                validation_results["tables"][table_name] = {"status": "error", "error": table_info["error"]}
                all_valid = False
                continue
            
            # Check if table exists and has columns
            if not table_info.get("columns"):
                validation_results["errors"].append(f"Table {table_name}: No columns found")
                validation_results["tables"][table_name] = {"status": "missing"}
                all_valid = False
                continue
            
            # Check required columns
            existing_columns = [col["column_name"] for col in table_info["columns"]]
            missing_columns = [col for col in expected["required_columns"] if col not in existing_columns]
            
            if missing_columns:
                validation_results["errors"].append(
                    f"Table {table_name}: Missing columns: {', '.join(missing_columns)}"
                )
                all_valid = False
            
            validation_results["tables"][table_name] = {
                "status": "valid" if not missing_columns else "invalid",
                "column_count": len(existing_columns),
                "missing_columns": missing_columns,
                "constraint_count": len(table_info.get("constraints", []))
            }
        
        validation_results["status"] = "valid" if all_valid else "invalid"
        
        return validation_results
        
    except Exception as e:
        logger.error("Failed to validate database schema", error=str(e))
        return {
            "status": "error",
            "error": str(e),
            "tables": {},
            "errors": [str(e)],
            "warnings": []
        }


async def seed_test_data() -> bool:
    """
    Insert test data for development and testing.
    
    Returns:
        bool: True if seeding was successful, False otherwise.
    """
    try:
        client = get_supabase_client()
        
        # Check if Lawn Fawn supplier already exists
        existing_supplier = client.table('suppliers')\
            .select('id')\
            .eq('code', 'LF')\
            .execute()
        
        if existing_supplier.data:
            logger.info("Test data already exists, skipping seed")
            return True
        
        # Run the seed data migration
        migrations_dir = Path(__file__).parent.parent.parent / "migrations"
        seed_file = migrations_dir / "002_seed_data.sql"
        
        if seed_file.exists():
            return await run_migration_file(str(seed_file))
        else:
            logger.error("Seed data file not found", file=str(seed_file))
            return False
            
    except Exception as e:
        logger.error("Failed to seed test data", error=str(e))
        return False


async def cleanup_test_data() -> bool:
    """
    Clean up test data (for testing environments).
    
    Returns:
        bool: True if cleanup was successful, False otherwise.
    """
    try:
        client = get_supabase_client()
        
        # Delete in reverse order of dependencies
        tables_to_clean = ["images", "products", "upload_batches", "suppliers"]
        
        for table in tables_to_clean:
            try:
                result = client.table(table).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
                logger.info("Cleaned test data", table=table, deleted_count=len(result.data))
            except Exception as table_error:
                logger.warning("Failed to clean table", table=table, error=str(table_error))
        
        logger.info("Test data cleanup completed")
        return True
        
    except Exception as e:
        logger.error("Failed to cleanup test data", error=str(e))
        return False


async def get_database_stats() -> Dict[str, Any]:
    """
    Get comprehensive database statistics.
    
    Returns:
        Dict with database statistics.
    """
    try:
        client = get_supabase_client()
        stats = {}
        
        # Get row counts for each table
        tables = ["suppliers", "upload_batches", "products", "images"]
        
        for table in tables:
            try:
                result = client.table(table).select('count').execute()
                stats[f"{table}_count"] = result.count if hasattr(result, 'count') else len(result.data)
            except Exception as table_error:
                logger.warning("Failed to get count for table", table=table, error=str(table_error))
                stats[f"{table}_count"] = 0
        
        # Get additional statistics
        try:
            # Active suppliers
            active_suppliers = client.table('suppliers').select('count').eq('active', True).execute()
            stats["active_suppliers_count"] = active_suppliers.count if hasattr(active_suppliers, 'count') else len(active_suppliers.data)
            
            # Processing batches
            processing_batches = client.table('upload_batches').select('count').eq('status', 'processing').execute()
            stats["processing_batches_count"] = processing_batches.count if hasattr(processing_batches, 'count') else len(processing_batches.data)
            
        except Exception as stats_error:
            logger.warning("Failed to get additional statistics", error=str(stats_error))
        
        stats["timestamp"] = asyncio.get_event_loop().time()
        
        return stats
        
    except Exception as e:
        logger.error("Failed to get database statistics", error=str(e))
        return {"error": str(e)}


async def backup_database() -> Dict[str, Any]:
    """
    Create a backup of the database (placeholder for future implementation).
    
    Returns:
        Dict with backup information.
    """
    # This is a placeholder - actual backup would depend on Supabase backup features
    # or custom export logic
    
    logger.info("Database backup requested - feature not yet implemented")
    
    return {
        "status": "not_implemented",
        "message": "Database backup feature will be implemented in future version",
        "timestamp": asyncio.get_event_loop().time()
    }


async def initialize_database() -> Dict[str, Any]:
    """
    Initialize the database with schema and seed data.
    
    Returns:
        Dict with initialization results.
    """
    try:
        logger.info("Starting database initialization")
        
        results = {
            "status": "unknown",
            "steps": {},
            "errors": []
        }
        
        # Step 1: Test connection
        logger.info("Step 1: Testing database connection")
        connection_test = await test_database_connection()
        results["steps"]["connection_test"] = connection_test
        
        if connection_test["status"] != "success":
            results["status"] = "failed"
            results["errors"].append("Database connection failed")
            return results
        
        # Step 2: Run migrations
        logger.info("Step 2: Running database migrations")
        migrations_success = await run_all_migrations()
        results["steps"]["migrations"] = {"success": migrations_success}
        
        if not migrations_success:
            results["errors"].append("Database migrations failed")
        
        # Step 3: Validate schema
        logger.info("Step 3: Validating database schema")
        schema_validation = await validate_database_schema()
        results["steps"]["schema_validation"] = schema_validation
        
        if schema_validation["status"] != "valid":
            results["errors"].append("Database schema validation failed")
        
        # Step 4: Seed test data
        logger.info("Step 4: Seeding test data")
        seed_success = await seed_test_data()
        results["steps"]["seed_data"] = {"success": seed_success}
        
        if not seed_success:
            results["errors"].append("Test data seeding failed")
        
        # Step 5: Get final statistics
        logger.info("Step 5: Getting database statistics")
        stats = await get_database_stats()
        results["steps"]["final_stats"] = stats
        
        # Determine overall status
        if not results["errors"]:
            results["status"] = "success"
        elif len(results["errors"]) <= 1:
            results["status"] = "partial_success"
        else:
            results["status"] = "failed"
        
        logger.info("Database initialization completed", status=results["status"])
        
        return results
        
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        return {
            "status": "error",
            "error": str(e),
            "steps": {},
            "errors": [str(e)]
        }
