"""
Supabase database manager for the Universal Product Automation System.

This module provides a centralized Supabase client manager with connection testing,
health checks, and error handling for database operations.
"""

import asyncio
from typing import Optional, Dict, Any
from supabase import create_client, Client
import structlog
from .config import get_settings

logger = structlog.get_logger(__name__)


class SupabaseManager:
    """
    Supabase client manager with connection testing and error handling.
    
    This class provides a singleton-like interface to the Supabase client
    with built-in health checks and connection management.
    """
    
    def __init__(self):
        """Initialize the Supabase manager with configuration."""
        self.settings = get_settings()
        self.url = self.settings.supabase_url
        self.service_key = self.settings.supabase_service_key
        self._client: Optional[Client] = None
        self._connection_tested = False
    
    @property
    def client(self) -> Client:
        """
        Get or create Supabase client instance.
        
        Returns:
            Client: Supabase client instance.
        """
        if self._client is None:
            try:
                self._client = create_client(self.url, self.service_key)
                logger.info("Supabase client initialized", url=self.url)
            except Exception as e:
                logger.error("Failed to initialize Supabase client", error=str(e))
                raise
        return self._client
    
    async def test_connection(self) -> bool:
        """
        Test database connection with health check.
        
        Returns:
            bool: True if connection is successful, False otherwise.
        """
        try:
            # Test connection by querying the suppliers table
            # This will fail gracefully if the table doesn't exist yet
            result = self.client.table('suppliers').select('count').execute()
            self._connection_tested = True
            logger.info("Supabase connection test successful")
            return True
        except Exception as e:
            logger.error("Supabase connection test failed", error=str(e))
            self._connection_tested = False
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check with metrics.
        
        Returns:
            Dict[str, Any]: Health check results with status and metrics.
        """
        health_data = {
            "status": "unknown",
            "connection_tested": self._connection_tested,
            "url": self.url,
            "timestamp": None,
            "error": None
        }
        
        try:
            # Test basic connection
            start_time = asyncio.get_event_loop().time()
            connected = await self.test_connection()
            end_time = asyncio.get_event_loop().time()
            
            health_data.update({
                "status": "healthy" if connected else "unhealthy",
                "connection_time_ms": round((end_time - start_time) * 1000, 2),
                "timestamp": end_time
            })
            
            if connected:
                # Additional health checks if connection is successful
                try:
                    # Test table access
                    tables_result = self.client.table('information_schema.tables')\
                        .select('table_name')\
                        .eq('table_schema', 'public')\
                        .execute()
                    
                    health_data["tables_accessible"] = len(tables_result.data) > 0
                    health_data["table_count"] = len(tables_result.data)
                    
                except Exception as table_error:
                    logger.warning("Table access check failed", error=str(table_error))
                    health_data["tables_accessible"] = False
                    health_data["table_error"] = str(table_error)
            
        except Exception as e:
            health_data.update({
                "status": "error",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            })
            logger.error("Health check failed", error=str(e))
        
        return health_data
    
    async def execute_query(self, table: str, operation: str, **kwargs) -> Any:
        """
        Execute a database query with error handling.
        
        Args:
            table (str): Table name to query.
            operation (str): Operation type (select, insert, update, delete).
            **kwargs: Additional arguments for the operation.
            
        Returns:
            Any: Query result.
            
        Raises:
            Exception: If query execution fails.
        """
        try:
            table_client = self.client.table(table)
            
            if operation == "select":
                columns = kwargs.get("columns", "*")
                result = table_client.select(columns)
                
                # Apply filters if provided
                if "filters" in kwargs:
                    for filter_item in kwargs["filters"]:
                        result = result.eq(filter_item["column"], filter_item["value"])
                
                # Apply limit if provided
                if "limit" in kwargs:
                    result = result.limit(kwargs["limit"])
                
                return result.execute()
            
            elif operation == "insert":
                data = kwargs.get("data", {})
                return table_client.insert(data).execute()
            
            elif operation == "update":
                data = kwargs.get("data", {})
                filters = kwargs.get("filters", [])
                result = table_client.update(data)
                
                for filter_item in filters:
                    result = result.eq(filter_item["column"], filter_item["value"])
                
                return result.execute()
            
            elif operation == "delete":
                filters = kwargs.get("filters", [])
                result = table_client.delete()
                
                for filter_item in filters:
                    result = result.eq(filter_item["column"], filter_item["value"])
                
                return result.execute()
            
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            logger.error(
                "Database query failed",
                table=table,
                operation=operation,
                error=str(e)
            )
            raise
    
    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get information about a specific table.
        
        Args:
            table_name (str): Name of the table to inspect.
            
        Returns:
            Dict[str, Any]: Table information including columns and constraints.
        """
        try:
            # Get column information
            columns_result = self.client.table('information_schema.columns')\
                .select('column_name, data_type, is_nullable, column_default')\
                .eq('table_schema', 'public')\
                .eq('table_name', table_name)\
                .execute()
            
            # Get constraint information
            constraints_result = self.client.table('information_schema.table_constraints')\
                .select('constraint_name, constraint_type')\
                .eq('table_schema', 'public')\
                .eq('table_name', table_name)\
                .execute()
            
            return {
                "table_name": table_name,
                "columns": columns_result.data,
                "constraints": constraints_result.data,
                "column_count": len(columns_result.data)
            }
            
        except Exception as e:
            logger.error("Failed to get table info", table=table_name, error=str(e))
            raise


# Global Supabase manager instance
supabase_manager = SupabaseManager()


def get_supabase_client() -> Client:
    """
    Get the global Supabase client instance.
    
    Returns:
        Client: Supabase client instance.
    """
    return supabase_manager.client


async def test_database_connection() -> bool:
    """
    Test the database connection.
    
    Returns:
        bool: True if connection is successful, False otherwise.
    """
    return await supabase_manager.test_connection()


async def get_database_health() -> Dict[str, Any]:
    """
    Get comprehensive database health information.
    
    Returns:
        Dict[str, Any]: Database health status and metrics.
    """
    return await supabase_manager.health_check()
