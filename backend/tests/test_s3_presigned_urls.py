"""
Comprehensive tests for S3 presigned URL generation and validation.

This module tests the S3InvoiceManager's presigned URL functionality
to ensure URLs are generated correctly and provide proper access.
"""

import pytest
import requests
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

from app.services.s3_manager import S3InvoiceManager
from app.models.invoice import S3UploadError
from app.core.config import get_settings


class TestS3PresignedUrls:
    """Test suite for S3 presigned URL generation and validation."""
    
    @pytest.fixture
    def s3_manager(self):
        """Create S3InvoiceManager instance for testing."""
        return S3InvoiceManager()
    
    @pytest.fixture
    def test_s3_key(self):
        """Test S3 key for existing invoice."""
        return "invoices/lawnfawn/2025/07/20250706_125003_KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf"
    
    def test_presigned_url_generation_success(self, s3_manager, test_s3_key):
        """Test successful presigned URL generation."""
        # Generate URL
        download_url, expires_at = s3_manager.generate_download_url(test_s3_key)
        
        # Validate return types
        assert isinstance(download_url, str)
        assert isinstance(expires_at, datetime)
        
        # Validate URL is not empty
        assert len(download_url) > 0
        assert download_url.startswith('https://')
        
        # Validate expiration is in the future
        assert expires_at > datetime.utcnow()
    
    def test_presigned_url_format_validation(self, s3_manager, test_s3_key):
        """Test that generated URLs have correct AWS signature format."""
        download_url, _ = s3_manager.generate_download_url(test_s3_key)
        
        # Validate AWS signature components are present
        assert "X-Amz-Algorithm=AWS4-HMAC-SHA256" in download_url
        assert "X-Amz-Signature=" in download_url
        assert "X-Amz-Expires=" in download_url
        assert "X-Amz-Date=" in download_url
        assert "X-Amz-SignedHeaders=" in download_url
        
        # Validate bucket and key are in URL
        settings = get_settings()
        assert settings.s3_bucket_name in download_url
        assert test_s3_key in download_url
    
    def test_presigned_url_accessibility(self, s3_manager, test_s3_key):
        """Test that generated URLs work correctly when accessed (matches browser behavior)."""
        download_url, _ = s3_manager.generate_download_url(test_s3_key)
        
        # Test URL accessibility with GET request using Range header (matches browser behavior)
        # Note: This S3 bucket restricts HEAD requests but allows GET requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Range': 'bytes=0-1023'  # Only download first 1KB for validation
        }
        response = requests.get(download_url, headers=headers, timeout=10)
        
        # Should return 200 (full content) or 206 (partial content)
        assert response.status_code in [200, 206], f"Expected 200/206, got {response.status_code}"
        
        # Validate response headers and content
        assert 'Content-Type' in response.headers
        assert 'pdf' in response.headers.get('Content-Type', '').lower()
        assert len(response.content) > 0, "Should receive content"
    
    def test_presigned_url_custom_expiration(self, s3_manager, test_s3_key):
        """Test presigned URL generation with custom expiration time."""
        custom_expires_in = 1800  # 30 minutes
        
        download_url, expires_at = s3_manager.generate_download_url(
            test_s3_key, 
            expires_in=custom_expires_in
        )
        
        # Validate custom expiration is used
        expected_expiration = datetime.utcnow() + timedelta(seconds=custom_expires_in)
        time_diff = abs((expires_at - expected_expiration).total_seconds())
        assert time_diff < 5  # Allow 5 second tolerance
        
        # Validate URL contains correct expiration
        assert f"X-Amz-Expires={custom_expires_in}" in download_url
    
    def test_presigned_url_default_expiration(self, s3_manager, test_s3_key):
        """Test presigned URL generation with default expiration from config."""
        settings = get_settings()
        
        download_url, expires_at = s3_manager.generate_download_url(test_s3_key)
        
        # Validate default expiration is used
        expected_expiration = datetime.utcnow() + timedelta(seconds=settings.invoice_download_expiration)
        time_diff = abs((expires_at - expected_expiration).total_seconds())
        assert time_diff < 5  # Allow 5 second tolerance
        
        # Validate URL contains correct expiration
        assert f"X-Amz-Expires={settings.invoice_download_expiration}" in download_url
    
    @pytest.mark.slow
    def test_url_expiration_security(self, s3_manager, test_s3_key):
        """Test that URLs properly expire after configured time."""
        # Generate URL with short expiration (5 seconds for testing)
        download_url, expires_at = s3_manager.generate_download_url(
            test_s3_key, 
            expires_in=5
        )
        
        # Test immediately (should work) - use GET with Range header
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Range': 'bytes=0-1023'
        }
        response = requests.get(download_url, headers=headers, timeout=10)
        assert response.status_code in [200, 206], "URL should work immediately after generation"
        
        # Wait for expiration
        time.sleep(6)
        
        # Test after expiration (should fail)
        response = requests.get(download_url, headers=headers, timeout=10)
        assert response.status_code == 403, "URL should return 403 after expiration"
    
    def test_presigned_url_nonexistent_key(self, s3_manager):
        """Test presigned URL generation for non-existent S3 key."""
        nonexistent_key = "invoices/nonexistent/file.pdf"
        
        # URL generation should succeed (presigned URLs are generated without checking existence)
        download_url, expires_at = s3_manager.generate_download_url(nonexistent_key)
        
        assert isinstance(download_url, str)
        assert isinstance(expires_at, datetime)
        
        # But accessing the URL should return 404 (use GET request)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Range': 'bytes=0-1023'
        }
        response = requests.get(download_url, headers=headers, timeout=10)
        # Note: S3 may return 403 instead of 404 for non-existent files due to bucket policy
        assert response.status_code in [403, 404], f"Expected 403/404 for non-existent file, got {response.status_code}"
    
    def test_presigned_url_error_handling(self, s3_manager):
        """Test error handling in presigned URL generation."""
        with patch.object(s3_manager.s3_client, 'generate_presigned_url') as mock_generate:
            # Mock ClientError
            mock_generate.side_effect = ClientError(
                error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
                operation_name='generate_presigned_url'
            )
            
            with pytest.raises(S3UploadError) as exc_info:
                s3_manager.generate_download_url("test/key.pdf")
            
            assert "Failed to generate download URL: AccessDenied" in str(exc_info.value)
    
    def test_presigned_url_unexpected_error(self, s3_manager):
        """Test handling of unexpected errors in presigned URL generation."""
        with patch.object(s3_manager.s3_client, 'generate_presigned_url') as mock_generate:
            # Mock unexpected error
            mock_generate.side_effect = Exception("Unexpected error")
            
            with pytest.raises(S3UploadError) as exc_info:
                s3_manager.generate_download_url("test/key.pdf")
            
            assert "URL generation failed: Unexpected error" in str(exc_info.value)
    
    def test_presigned_url_logging(self, s3_manager, test_s3_key, caplog):
        """Test that presigned URL generation logs appropriately."""
        with caplog.at_level("INFO"):
            s3_manager.generate_download_url(test_s3_key)
        
        # Check that appropriate log messages are present
        log_messages = [record.message for record in caplog.records]
        assert any("Generating presigned download URL" in msg for msg in log_messages)
        assert any("Presigned URL generated successfully" in msg for msg in log_messages)
    
    def test_multiple_url_generation(self, s3_manager, test_s3_key):
        """Test generating multiple URLs for the same key."""
        # Generate multiple URLs
        url1, expires1 = s3_manager.generate_download_url(test_s3_key)
        url2, expires2 = s3_manager.generate_download_url(test_s3_key)
        
        # URLs should be different (different timestamps)
        assert url1 != url2
        
        # Both should be accessible (use GET with Range header)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Range': 'bytes=0-1023'
        }
        response1 = requests.get(url1, headers=headers, timeout=10)
        response2 = requests.get(url2, headers=headers, timeout=10)
        
        assert response1.status_code in [200, 206]
        assert response2.status_code in [200, 206]
    
    def test_url_structure_matches_aws_console(self, s3_manager, test_s3_key):
        """Test that generated URL structure matches AWS Console format."""
        download_url, _ = s3_manager.generate_download_url(test_s3_key)
        
        settings = get_settings()
        
        # Validate URL structure
        expected_base = f"https://{settings.s3_bucket_name}.s3.{settings.aws_region}.amazonaws.com/{test_s3_key}"
        assert download_url.startswith(expected_base)
        
        # Validate query parameters are present
        assert "?" in download_url
        query_part = download_url.split("?", 1)[1]
        
        # Check for required AWS signature parameters
        required_params = [
            "X-Amz-Algorithm",
            "X-Amz-Credential", 
            "X-Amz-Date",
            "X-Amz-Expires",
            "X-Amz-SignedHeaders",
            "X-Amz-Signature"
        ]
        
        for param in required_params:
            assert param in query_part, f"Missing required parameter: {param}"


class TestS3PresignedUrlsIntegration:
    """Integration tests for S3 presigned URLs with real AWS services."""
    
    @pytest.fixture
    def s3_manager(self):
        """Create S3InvoiceManager instance for integration testing."""
        return S3InvoiceManager()
    
    @pytest.fixture
    def test_s3_key(self):
        """Test S3 key for existing invoice."""
        return "invoices/lawnfawn/2025/07/20250706_125003_KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf"
    
    @pytest.mark.integration
    def test_end_to_end_download_workflow(self, s3_manager, test_s3_key):
        """Test complete end-to-end download workflow."""
        # Step 1: Check file exists
        assert s3_manager.check_invoice_exists(test_s3_key)
        
        # Step 2: Get file metadata
        metadata = s3_manager.get_invoice_metadata(test_s3_key)
        assert 'content_length' in metadata
        assert int(metadata['content_length']) > 0
        
        # Step 3: Generate download URL
        download_url, expires_at = s3_manager.generate_download_url(test_s3_key)
        
        # Step 4: Test URL accessibility
        response = requests.head(download_url, timeout=10)
        assert response.status_code == 200
        
        # Step 5: Validate response headers match metadata
        assert response.headers.get('Content-Length') == metadata['content_length']
        assert response.headers.get('Content-Type') == metadata.get('content_type', 'application/pdf')
    
    @pytest.mark.integration
    def test_download_url_with_different_regions(self, s3_manager, test_s3_key):
        """Test that presigned URLs work correctly with eu-north-1 region."""
        download_url, _ = s3_manager.generate_download_url(test_s3_key)
        
        # Validate region is correctly included in URL
        settings = get_settings()
        assert f".s3.{settings.aws_region}.amazonaws.com" in download_url
        
        # Test URL works
        response = requests.head(download_url, timeout=10)
        assert response.status_code == 200
