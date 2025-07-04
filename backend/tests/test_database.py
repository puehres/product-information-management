"""
Tests for database functionality in the Universal Product Automation System.

This module contains tests for database connections, models, and operations.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from uuid import uuid4

from app.core.database import SupabaseManager, test_database_connection
from app.models import (
    Supplier, SupplierCreate, SupplierUpdate,
    UploadBatch, UploadBatchCreate,
    Product, ProductCreate,
    Image, ImageCreate
)
from app.services.database_service import DatabaseService
from app.utils.database_utils import (
    test_database_connection as utils_test_connection,
    validate_database_schema,
    get_database_stats
)


class TestSupabaseManager:
    """Test cases for SupabaseManager class."""
    
    def test_supabase_manager_initialization(self):
        """Test SupabaseManager can be initialized."""
        manager = SupabaseManager()
        assert manager is not None
        assert manager.url is not None
        assert manager.service_key is not None
    
    @patch('app.core.database.create_client')
    def test_client_property(self, mock_create_client):
        """Test client property creates and returns Supabase client."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        manager = SupabaseManager()
        client = manager.client
        
        assert client == mock_client
        mock_create_client.assert_called_once()
        
        # Test client is cached
        client2 = manager.client
        assert client2 == mock_client
        # Should not call create_client again
        assert mock_create_client.call_count == 1
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, mock_supabase_client):
        """Test successful connection test."""
        manager = SupabaseManager()
        
        # Mock successful response
        mock_result = Mock()
        mock_result.data = [{"count": 1}]
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = mock_result
        
        # Mock the _client attribute directly to avoid property issues
        with patch.object(manager, '_client', mock_supabase_client):
            result = await manager.test_connection()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_test_connection_failure(self, mock_supabase_client):
        """Test failed connection test."""
        manager = SupabaseManager()
        
        # Configure mock to raise exception
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = Exception("Connection failed")
        
        # Mock the _client attribute directly to avoid property issues
        with patch.object(manager, '_client', mock_supabase_client):
            result = await manager.test_connection()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_supabase_client, mock_async_supabase_manager):
        """Test health check functionality."""
        manager = SupabaseManager()
        
        # Configure mock for table access check
        mock_result = Mock()
        mock_result.data = [{"table_name": "suppliers"}]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        # Mock both the test_connection method and client property
        with patch.object(manager, 'test_connection', return_value=True):
            with patch.object(manager, '_client', mock_supabase_client):
                health_data = await manager.health_check()
                
                assert health_data["status"] == "healthy"
                assert "connection_time_ms" in health_data
                assert "timestamp" in health_data


class TestDatabaseModels:
    """Test cases for database models."""
    
    def test_supplier_create_model(self):
        """Test SupplierCreate model validation."""
        supplier_data = {
            "name": "Test Supplier",
            "code": "TEST",
            "website_url": "https://test.com",
            "identifier_type": "sku",
            "active": True
        }
        
        supplier = SupplierCreate(**supplier_data)
        
        assert supplier.name == "Test Supplier"
        assert supplier.code == "TEST"
        assert supplier.website_url == "https://test.com"
        assert supplier.active is True
    
    def test_supplier_create_validation(self):
        """Test SupplierCreate model validation errors."""
        # Test empty name
        with pytest.raises(ValueError, match="Supplier name cannot be empty"):
            SupplierCreate(name="", code="TEST")
        
        # Test empty code
        with pytest.raises(ValueError, match="Supplier code cannot be empty"):
            SupplierCreate(name="Test", code="")
        
        # Test invalid URL
        with pytest.raises(ValueError, match="Website URL must start with http"):
            SupplierCreate(name="Test", code="TEST", website_url="invalid-url")
    
    def test_supplier_update_model(self):
        """Test SupplierUpdate model with partial updates."""
        update_data = {
            "name": "Updated Name",
            "active": False
        }
        
        supplier_update = SupplierUpdate(**update_data)
        
        assert supplier_update.name == "Updated Name"
        assert supplier_update.active is False
        assert supplier_update.code is None  # Not provided
    
    def test_upload_batch_create_model(self):
        """Test UploadBatchCreate model."""
        batch_data = {
            "supplier_id": str(uuid4()),
            "batch_name": "Test Batch",
            "file_type": "csv",
            "file_size": 1024
        }
        
        batch = UploadBatchCreate(**batch_data)
        
        assert batch.batch_name == "Test Batch"
        assert batch.file_type == "csv"
        assert batch.file_size == 1024
    
    def test_product_create_model(self):
        """Test ProductCreate model."""
        from decimal import Decimal
        
        product_data = {
            "batch_id": str(uuid4()),
            "supplier_id": str(uuid4()),
            "supplier_sku": "TEST-001",
            "supplier_name": "Test Product",
            "supplier_price_usd": 19.99
        }
        
        product = ProductCreate(**product_data)
        
        assert product.supplier_sku == "TEST-001"
        assert product.supplier_name == "Test Product"
        # Handle Decimal type returned by Pydantic
        assert float(product.supplier_price_usd) == 19.99
    
    def test_image_create_model(self):
        """Test ImageCreate model."""
        image_data = {
            "product_id": str(uuid4()),
            "original_url": "https://example.com/image.jpg",
            "image_type": "main",
            "sequence_number": 1
        }
        
        image = ImageCreate(**image_data)
        
        assert image.original_url == "https://example.com/image.jpg"
        assert image.image_type == "main"
        assert image.sequence_number == 1


class TestDatabaseService:
    """Test cases for DatabaseService class."""
    
    def test_database_service_initialization(self):
        """Test DatabaseService can be initialized."""
        service = DatabaseService()
        assert service is not None
        assert service.client is not None
    
    @pytest.mark.asyncio
    async def test_get_suppliers_empty(self):
        """Test getting suppliers when none exist."""
        service = DatabaseService()
        
        mock_result = Mock()
        mock_result.data = []
        
        with patch.object(service.client, 'table') as mock_table:
            mock_table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_result
            
            suppliers = await service.get_suppliers()
            
            assert suppliers == []
    
    @pytest.mark.asyncio
    async def test_get_supplier_by_id_not_found(self):
        """Test getting supplier by ID when not found."""
        service = DatabaseService()
        
        mock_result = Mock()
        mock_result.data = []
        
        with patch.object(service.client, 'table') as mock_table:
            mock_table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
            
            supplier = await service.get_supplier_by_id(uuid4())
            
            assert supplier is None
    
    @pytest.mark.asyncio
    async def test_create_supplier_success(self):
        """Test successful supplier creation."""
        service = DatabaseService()
        
        supplier_data = SupplierCreate(
            name="Test Supplier",
            code="TEST",
            website_url="https://test.com"
        )
        
        mock_result = Mock()
        mock_result.data = [{
            "id": str(uuid4()),
            "name": "Test Supplier",
            "code": "TEST",
            "website_url": "https://test.com",
            "identifier_type": "sku",
            "scraping_config": {},
            "search_url_template": None,
            "active": True,
            "created_at": "2025-01-07T22:50:00Z",
            "updated_at": "2025-01-07T22:50:00Z"
        }]
        
        with patch.object(service.client, 'table') as mock_table:
            mock_table.return_value.insert.return_value.execute.return_value = mock_result
            
            supplier = await service.create_supplier(supplier_data)
            
            assert supplier is not None
            assert supplier.name == "Test Supplier"
            assert supplier.code == "TEST"


class TestDatabaseUtils:
    """Test cases for database utility functions."""
    
    @pytest.mark.asyncio
    async def test_utils_test_connection(self, mock_async_supabase_manager):
        """Test database connection test utility."""
        with patch('app.utils.database_utils.supabase_manager', mock_async_supabase_manager):
            result = await utils_test_connection()
            
            assert result["status"] == "success"
            assert "connection_time_ms" in result
    
    @pytest.mark.asyncio
    async def test_validate_database_schema(self):
        """Test database schema validation."""
        with patch('app.utils.database_utils.supabase_manager') as mock_manager:
            # Mock the get_table_info method to return valid table info for all expected tables
            mock_manager.get_table_info.return_value = {
                "table_name": "suppliers",
                "columns": [
                    {"column_name": "id"},
                    {"column_name": "name"},
                    {"column_name": "code"},
                    {"column_name": "website_url"},
                    {"column_name": "identifier_type"},
                    {"column_name": "scraping_config"},
                    {"column_name": "search_url_template"},
                    {"column_name": "active"},
                    {"column_name": "created_at"},
                    {"column_name": "updated_at"}
                ],
                "constraints": []
            }
            
            result = await validate_database_schema()
            
            assert result["status"] == "valid"
            assert "tables" in result
    
    @pytest.mark.asyncio
    async def test_get_database_stats(self):
        """Test getting database statistics."""
        with patch('app.utils.database_utils.get_supabase_client') as mock_get_client:
            mock_client = Mock()
            mock_result = Mock()
            mock_result.count = 5
            mock_result.data = [{"count": 5}]
            
            mock_client.table.return_value.select.return_value.execute.return_value = mock_result
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
            
            mock_get_client.return_value = mock_client
            
            stats = await get_database_stats()
            
            assert "suppliers_count" in stats
            assert "upload_batches_count" in stats
            assert "products_count" in stats
            assert "images_count" in stats
            assert "timestamp" in stats


class TestIntegration:
    """Integration tests for database functionality."""
    
    @pytest.mark.asyncio
    async def test_full_database_workflow(self):
        """Test a complete database workflow."""
        # This would be a more comprehensive test that would require
        # actual database connection or more sophisticated mocking
        
        # For now, just test that the components can work together
        service = DatabaseService()
        assert service is not None
        
        # Test model creation
        supplier_data = SupplierCreate(
            name="Integration Test Supplier",
            code="INTEG",
            website_url="https://integration-test.com"
        )
        
        assert supplier_data.name == "Integration Test Supplier"
        assert supplier_data.code == "INTEG"


# Test fixtures and utilities

@pytest.fixture
def sample_supplier_data():
    """Fixture providing sample supplier data."""
    return {
        "name": "Sample Supplier",
        "code": "SAMPLE",
        "website_url": "https://sample.com",
        "identifier_type": "sku",
        "active": True
    }


@pytest.fixture
def sample_product_data():
    """Fixture providing sample product data."""
    return {
        "batch_id": str(uuid4()),
        "supplier_id": str(uuid4()),
        "supplier_sku": "SAMPLE-001",
        "supplier_name": "Sample Product",
        "supplier_price_usd": 29.99
    }


# Async test utilities

def run_async_test(coro):
    """Helper function to run async tests."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# Performance tests

class TestPerformance:
    """Performance tests for database operations."""
    
    @pytest.mark.asyncio
    async def test_connection_performance(self, mock_async_supabase_manager):
        """Test that database connection is fast enough."""
        import time
        from unittest.mock import AsyncMock
        
        start_time = time.time()
        
        with patch('app.core.database.supabase_manager', mock_async_supabase_manager):
            result = await test_database_connection()
            
        end_time = time.time()
        duration = end_time - start_time
        
        # Connection should be fast (under 2 seconds for mocked test)
        assert duration < 2.0
        assert result is True


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])
