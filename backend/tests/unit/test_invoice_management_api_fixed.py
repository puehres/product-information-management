"""
Test suite for invoice management API endpoints.

This module tests the complete invoice listing, filtering, and pagination
functionality with comprehensive coverage of edge cases and error scenarios.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime
from uuid import uuid4
from app.main import app
from app.models.upload_batch import UploadBatch
from app.models.invoice import InvoiceSummary, PaginationInfo
from app.models.base import FileType, BatchStatus

# Create test client
client = TestClient(app)


class TestInvoiceListAPI:
    """Test cases for the /api/v1/invoices endpoint."""
    
    def test_list_invoices_basic(self):
        """Test basic invoice listing functionality."""
        with patch('app.services.database_service.get_database_service') as mock_get_db:
            # Mock database service
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
            # Mock response data with proper UUIDs and enum values
            batch_id = str(uuid4())
            mock_batch = UploadBatch(
                id=batch_id,
                supplier_id=str(uuid4()),
                batch_name="test-batch",
                file_type=FileType.PDF,
                status=BatchStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                supplier_code="lawnfawn",
                original_filename="test_invoice.pdf",
                total_products=5,
                parsing_success_rate=95.0,
                file_size_bytes=1024000,
                invoice_number="TEST123",
                currency_code="USD",
                total_amount_original=100.50
            )
            
            mock_db.list_upload_batches_with_filters.return_value = ([mock_batch], 1)
            
            # Make request with correct API prefix
            response = client.get("/api/v1/invoices")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "invoices" in data
            assert "total_count" in data
            assert "pagination" in data
            assert len(data["invoices"]) == 1
            assert data["total_count"] == 1
            
            # Check invoice data
            invoice = data["invoices"][0]
            assert invoice["batch_id"] == batch_id
            assert invoice["supplier"] == "lawnfawn"
            assert invoice["original_filename"] == "test_invoice.pdf"
            assert invoice["total_products"] == 5
            assert invoice["parsing_success_rate"] == 95.0
            assert invoice["file_size_mb"] == 1.0  # 1024000 bytes = 1MB
    
    def test_list_invoices_pagination(self):
        """Test pagination parameters."""
        with patch('app.services.database_service.get_database_service') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_db.list_upload_batches_with_filters.return_value = ([], 0)
            
            response = client.get("/api/v1/invoices?limit=10&offset=5")
            
            assert response.status_code == 200
            data = response.json()
            assert data["pagination"]["limit"] == 10
            assert data["pagination"]["offset"] == 5
            
            # Verify database service was called with correct parameters
            mock_db.list_upload_batches_with_filters.assert_called_once()
            call_args = mock_db.list_upload_batches_with_filters.call_args
            assert call_args[1]["limit"] == 10
            assert call_args[1]["offset"] == 5
    
    def test_list_invoices_invalid_limit(self):
        """Test invalid limit parameter validation."""
        # Test limit too high
        response = client.get("/api/v1/invoices?limit=200")
        assert response.status_code == 422  # Validation error
        
        # Test limit too low
        response = client.get("/api/v1/invoices?limit=0")
        assert response.status_code == 422  # Validation error
    
    def test_list_invoices_invalid_offset(self):
        """Test invalid offset parameter validation."""
        response = client.get("/api/v1/invoices?offset=-1")
        assert response.status_code == 422  # Validation error
    
    def test_list_invoices_supplier_filter(self):
        """Test supplier filtering."""
        with patch('app.services.database_service.get_database_service') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_db.list_upload_batches_with_filters.return_value = ([], 0)
            
            response = client.get("/api/v1/invoices?supplier=lawnfawn")
            
            assert response.status_code == 200
            
            # Verify supplier filter was passed to database service
            call_args = mock_db.list_upload_batches_with_filters.call_args
            assert call_args[1]["supplier"] == "lawnfawn"
    
    def test_list_invoices_date_filter(self):
        """Test date range filtering."""
        with patch('app.services.database_service.get_database_service') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_db.list_upload_batches_with_filters.return_value = ([], 0)
            
            response = client.get("/api/v1/invoices?date_from=2025-01-01&date_to=2025-12-31")
            
            assert response.status_code == 200
            
            # Verify date filters were parsed and passed correctly
            call_args = mock_db.list_upload_batches_with_filters.call_args
            assert call_args[1]["date_from"] == datetime(2025, 1, 1)
            assert call_args[1]["date_to"] == datetime(2025, 12, 31)
    
    def test_list_invoices_invalid_date_format(self):
        """Test invalid date format handling."""
        response = client.get("/api/v1/invoices?date_from=invalid-date")
        assert response.status_code == 400
        assert "Invalid date_from format" in response.json()["detail"]
        
        response = client.get("/api/v1/invoices?date_to=2025/01/01")
        assert response.status_code == 400
        assert "Invalid date_to format" in response.json()["detail"]
    
    def test_list_invoices_search(self):
        """Test search functionality."""
        with patch('app.services.database_service.get_database_service') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
            # Mock batch with search term in invoice number
            batch_id = str(uuid4())
            mock_batch = UploadBatch(
                id=batch_id,
                supplier_id=str(uuid4()),
                batch_name="test-batch",
                file_type=FileType.PDF,
                status=BatchStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                supplier_code="lawnfawn",
                original_filename="test_invoice.pdf",
                total_products=5,
                invoice_number="CPSummer25"
            )
            
            mock_db.list_upload_batches_with_filters.return_value = ([mock_batch], 1)
            
            response = client.get("/api/v1/invoices?search=CPSummer25")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify search was passed to database service
            call_args = mock_db.list_upload_batches_with_filters.call_args
            assert call_args[1]["search"] == "CPSummer25"
            
            # Verify response contains the matching invoice
            assert len(data["invoices"]) == 1
            assert data["invoices"][0]["invoice_number"] == "CPSummer25"
    
    def test_list_invoices_sort_parameters(self):
        """Test sorting parameters."""
        with patch('app.services.database_service.get_database_service') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_db.list_upload_batches_with_filters.return_value = ([], 0)
            
            response = client.get("/api/v1/invoices?sort_by=supplier_code&sort_order=asc")
            
            assert response.status_code == 200
            
            # Verify sort parameters were passed correctly
            call_args = mock_db.list_upload_batches_with_filters.call_args
            assert call_args[1]["sort_by"] == "supplier_code"
            assert call_args[1]["sort_order"] == "asc"
    
    def test_list_invoices_invalid_sort_order(self):
        """Test invalid sort order validation."""
        response = client.get("/api/v1/invoices?sort_order=invalid")
        assert response.status_code == 422  # Validation error
    
    def test_list_invoices_empty_search(self):
        """Test empty search parameter validation."""
        response = client.get("/api/v1/invoices?search=")
        assert response.status_code == 422  # Validation error (min_length=1)
    
    def test_list_invoices_pagination_calculation(self):
        """Test pagination metadata calculation."""
        with patch('app.services.database_service.get_database_service') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
            # Mock 150 total items, requesting 50 items starting at offset 0
            mock_db.list_upload_batches_with_filters.return_value = ([], 150)
            
            response = client.get("/api/v1/invoices?limit=50&offset=0")
            
            assert response.status_code == 200
            data = response.json()
            
            # Check pagination metadata
            pagination = data["pagination"]
            assert pagination["limit"] == 50
            assert pagination["offset"] == 0
            assert pagination["has_more"] is True
            assert pagination["next_offset"] == 50
            assert data["has_more"] is True
            assert data["total_count"] == 150
    
    def test_list_invoices_no_more_pages(self):
        """Test pagination when no more pages available."""
        with patch('app.services.database_service.get_database_service') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
            # Mock 25 total items, requesting 50 items
            mock_db.list_upload_batches_with_filters.return_value = ([], 25)
            
            response = client.get("/api/v1/invoices?limit=50&offset=0")
            
            assert response.status_code == 200
            data = response.json()
            
            # Check pagination metadata
            pagination = data["pagination"]
            assert pagination["has_more"] is False
            assert pagination["next_offset"] is None
            assert data["has_more"] is False
    
    def test_list_invoices_missing_fields_handling(self):
        """Test graceful handling of missing fields in batch data."""
        with patch('app.services.database_service.get_database_service') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
            # Mock batch with minimal required fields
            batch_id = str(uuid4())
            mock_batch = UploadBatch(
                id=batch_id,
                supplier_id=str(uuid4()),
                batch_name="test-batch",
                file_type=FileType.PDF,
                status=BatchStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now()
                # Missing optional fields like supplier_code, invoice_number, etc.
            )
            
            mock_db.list_upload_batches_with_filters.return_value = ([mock_batch], 1)
            
            response = client.get("/api/v1/invoices")
            
            assert response.status_code == 200
            data = response.json()
            
            # Check that missing fields are handled gracefully
            invoice = data["invoices"][0]
            assert invoice["supplier"] == "unknown"  # Default for missing supplier_code
            assert invoice["invoice_number"] is None
            assert invoice["total_products"] == 0  # Default for missing total_products
            assert invoice["parsing_success_rate"] == 0.0
            assert invoice["file_size_mb"] == 0.0
    
    def test_list_invoices_database_error(self):
        """Test handling of database errors."""
        with patch('app.services.database_service.get_database_service') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
            # Mock database error
            mock_db.list_upload_batches_with_filters.side_effect = Exception("Database connection failed")
            
            response = client.get("/api/v1/invoices")
            
            assert response.status_code == 500
            assert "Failed to list invoices" in response.json()["detail"]
    
    def test_list_invoices_combined_filters(self):
        """Test multiple filters combined."""
        with patch('app.services.database_service.get_database_service') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_db.list_upload_batches_with_filters.return_value = ([], 0)
            
            response = client.get(
                "/api/v1/invoices?"
                "supplier=lawnfawn&"
                "date_from=2025-01-01&"
                "date_to=2025-12-31&"
                "search=CPSummer&"
                "limit=25&"
                "offset=10&"
                "sort_by=created_at&"
                "sort_order=desc"
            )
            
            assert response.status_code == 200
            
            # Verify all filters were passed correctly
            call_args = mock_db.list_upload_batches_with_filters.call_args
            assert call_args[1]["supplier"] == "lawnfawn"
            assert call_args[1]["date_from"] == datetime(2025, 1, 1)
            assert call_args[1]["date_to"] == datetime(2025, 12, 31)
            assert call_args[1]["search"] == "CPSummer"
            assert call_args[1]["limit"] == 25
            assert call_args[1]["offset"] == 10
            assert call_args[1]["sort_by"] == "created_at"
            assert call_args[1]["sort_order"] == "desc"


class TestInvoiceListIntegration:
    """Integration tests for the complete invoice management workflow."""
    
    def test_complete_workflow_simulation(self):
        """Test the complete list → find → download workflow."""
        with patch('app.services.database_service.get_database_service') as mock_get_db:
            with patch('app.services.invoice_processor.InvoiceProcessorService') as mock_processor_class:
                # Setup mocks
                mock_db = AsyncMock()
                mock_get_db.return_value = mock_db
                
                mock_processor = AsyncMock()
                mock_processor_class.return_value = mock_processor
                
                # Mock batch data
                test_batch_id = str(uuid4())
                mock_batch = UploadBatch(
                    id=test_batch_id,
                    supplier_id=str(uuid4()),
                    batch_name="test-batch",
                    file_type=FileType.PDF,
                    status=BatchStatus.COMPLETED,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    supplier_code="lawnfawn",
                    original_filename="CPSummer25_invoice.pdf",
                    invoice_number="CPSummer25"
                )
                
                mock_db.list_upload_batches_with_filters.return_value = ([mock_batch], 1)
                
                # Mock download functionality
                mock_processor.get_invoice_details.return_value = {
                    'batch': {'original_filename': 'CPSummer25_invoice.pdf'}
                }
                mock_processor.generate_invoice_download_url.return_value = "https://s3.amazonaws.com/presigned-url"
                
                # Step 1: List invoices to find the batch_id
                list_response = client.get("/api/v1/invoices?search=CPSummer25")
                assert list_response.status_code == 200
                
                list_data = list_response.json()
                assert len(list_data["invoices"]) == 1
                found_batch_id = list_data["invoices"][0]["batch_id"]
                assert found_batch_id == test_batch_id
                
                # Step 2: Generate download URL using the found batch_id
                download_response = client.get(f"/api/v1/invoices/{found_batch_id}/download")
                assert download_response.status_code == 200
                
                download_data = download_response.json()
                assert download_data["success"] is True
                assert download_data["download_url"] == "https://s3.amazonaws.com/presigned-url"
                assert download_data["filename"] == "CPSummer25_invoice.pdf"
                
                # Verify the complete workflow called the right services
                mock_db.list_upload_batches_with_filters.assert_called_once()
                mock_processor.get_invoice_details.assert_called_once_with(test_batch_id)
                mock_processor.generate_invoice_download_url.assert_called_once_with(test_batch_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
