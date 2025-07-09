"""
Unit tests for FirecrawlClient.

Tests the Firecrawl API wrapper with mocked HTTP requests,
following patterns from existing connectivity tests.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx
from datetime import datetime

from app.services.firecrawl_client import FirecrawlClient, get_firecrawl_client
from app.models.enrichment import FirecrawlResponse, EnrichmentConfig
from app.exceptions.enrichment import FirecrawlAPIError, ConfigurationError


class TestFirecrawlClient:
    """Test suite for FirecrawlClient."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock enrichment configuration."""
        return EnrichmentConfig(
            firecrawl_api_key="test-api-key",
            firecrawl_base_url="https://api.firecrawl.dev",
            firecrawl_timeout=30,
            max_concurrent_requests=5,
            retry_attempts=3,
            retry_delay=2
        )
    
    @pytest.fixture
    def firecrawl_client(self, mock_config):
        """Create FirecrawlClient with test configuration."""
        return FirecrawlClient(mock_config)
    
    @pytest.fixture
    def sample_firecrawl_response(self):
        """Sample successful Firecrawl API response."""
        return {
            "success": True,
            "data": {
                "content": "<html><body><h1>Test Product</h1><p>Product description</p></body></html>",
                "markdown": "# Test Product\n\nProduct description",
                "metadata": {
                    "title": "Test Product - LawnFawn",
                    "description": "Product description",
                    "statusCode": 200,
                    "error": ""
                }
            },
            "credits_used": 1
        }
    
    @pytest.mark.asyncio
    async def test_scrape_page_success(self, firecrawl_client, sample_firecrawl_response):
        """Test successful page scraping."""
        url = "https://www.lawnfawn.com/products/test-product"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_firecrawl_response
            mock_response.raise_for_status = Mock()
            mock_client.post.return_value = mock_response
            
            # Execute
            result = await firecrawl_client.scrape_page(url)
            
            # Verify
            assert isinstance(result, FirecrawlResponse)
            assert result.url == url
            assert result.success is True
            assert "Test Product" in result.content
            assert "# Test Product" in result.markdown
            assert result.metadata["title"] == "Test Product - LawnFawn"
            assert result.credits_used == 1
            
            # Verify API call
            mock_client.post.assert_called_once_with(
                "https://api.firecrawl.dev/v0/scrape",
                headers={"Authorization": "Bearer test-api-key"},
                json={
                    "url": url,
                    "formats": ["html", "markdown"],
                    "onlyMainContent": True
                },
                timeout=30
            )
    
    @pytest.mark.asyncio
    async def test_scrape_page_api_error(self, firecrawl_client):
        """Test handling of Firecrawl API errors."""
        url = "https://www.lawnfawn.com/products/test-product"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "success": False,
                "error": "Invalid URL format"
            }
            mock_client.post.return_value = mock_response
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Bad Request", request=Mock(), response=mock_response
            )
            
            # Execute and verify exception
            with pytest.raises(FirecrawlAPIError) as exc_info:
                await firecrawl_client.scrape_page(url)
            
            assert "Bad Request" in str(exc_info.value)
            assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_scrape_page_timeout(self, firecrawl_client):
        """Test handling of timeout errors."""
        url = "https://www.lawnfawn.com/products/test-product"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = httpx.TimeoutException("Request timeout")
            
            # Execute and verify exception
            with pytest.raises(FirecrawlAPIError) as exc_info:
                await firecrawl_client.scrape_page(url)
            
            assert "Request timeout" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_scrape_page_connection_error(self, firecrawl_client):
        """Test handling of connection errors."""
        url = "https://www.lawnfawn.com/products/test-product"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = httpx.ConnectError("Connection failed")
            
            # Execute and verify exception
            with pytest.raises(FirecrawlAPIError) as exc_info:
                await firecrawl_client.scrape_page(url)
            
            assert "Connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_scrape_page_unsuccessful_response(self, firecrawl_client):
        """Test handling of unsuccessful Firecrawl responses."""
        url = "https://www.lawnfawn.com/products/test-product"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": False,
                "error": "Page not found or blocked"
            }
            mock_response.raise_for_status = Mock()
            mock_client.post.return_value = mock_response
            
            # Execute
            result = await firecrawl_client.scrape_page(url)
            
            # Verify
            assert isinstance(result, FirecrawlResponse)
            assert result.success is False
            assert result.error_message == "Page not found or blocked"
    
    @pytest.mark.asyncio
    async def test_scrape_page_with_custom_options(self, firecrawl_client):
        """Test scraping with custom options."""
        url = "https://www.lawnfawn.com/products/test-product"
        options = {
            "waitFor": 2000,
            "screenshot": True,
            "formats": ["html"]
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "data": {"content": "<html>test</html>"},
                "credits_used": 1
            }
            mock_response.raise_for_status = Mock()
            mock_client.post.return_value = mock_response
            
            # Execute
            await firecrawl_client.scrape_page(url, options)
            
            # Verify custom options were passed
            expected_payload = {
                "url": url,
                "waitFor": 2000,
                "screenshot": True,
                "formats": ["html"]
            }
            mock_client.post.assert_called_once_with(
                "https://api.firecrawl.dev/v0/scrape",
                headers={"Authorization": "Bearer test-api-key"},
                json=expected_payload,
                timeout=30
            )
    
    @pytest.mark.asyncio
    async def test_search_pages_success(self, firecrawl_client):
        """Test successful search functionality."""
        query = "LF2538"
        base_url = "https://www.lawnfawn.com"
        
        search_response = {
            "success": True,
            "data": [
                {
                    "url": "https://www.lawnfawn.com/products/lf2538-dies",
                    "content": "<html><body>Product LF2538</body></html>",
                    "metadata": {"title": "LF2538 Dies"}
                },
                {
                    "url": "https://www.lawnfawn.com/products/lf2538-stamps",
                    "content": "<html><body>Stamps LF2538</body></html>",
                    "metadata": {"title": "LF2538 Stamps"}
                }
            ],
            "credits_used": 2
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = search_response
            mock_response.raise_for_status = Mock()
            mock_client.post.return_value = mock_response
            
            # Execute
            results = await firecrawl_client.search_pages(query, base_url)
            
            # Verify
            assert len(results) == 2
            assert all(isinstance(r, FirecrawlResponse) for r in results)
            assert results[0].url == "https://www.lawnfawn.com/products/lf2538-dies"
            assert results[1].url == "https://www.lawnfawn.com/products/lf2538-stamps"
            assert all(r.success for r in results)
    
    @pytest.mark.asyncio
    async def test_get_credits_info_success(self, firecrawl_client):
        """Test getting credits information."""
        credits_response = {
            "success": True,
            "data": {
                "total": 1000,
                "used": 250,
                "remaining": 750
            }
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = credits_response
            mock_response.raise_for_status = Mock()
            mock_client.get.return_value = mock_response
            
            # Execute
            result = await firecrawl_client.get_credits_info()
            
            # Verify
            assert result["total"] == 1000
            assert result["used"] == 250
            assert result["remaining"] == 750
            
            # Verify API call
            mock_client.get.assert_called_once_with(
                "https://api.firecrawl.dev/v0/credits",
                headers={"Authorization": "Bearer test-api-key"},
                timeout=30
            )
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, firecrawl_client):
        """Test health check functionality."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_response.raise_for_status = Mock()
            mock_client.get.return_value = mock_response
            
            # Execute
            result = await firecrawl_client.health_check()
            
            # Verify
            assert result["status"] == "healthy"
            assert result["service"] == "firecrawl-api"
            assert "response_time_ms" in result
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, firecrawl_client):
        """Test health check when API is down."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.side_effect = httpx.ConnectError("Connection failed")
            
            # Execute
            result = await firecrawl_client.health_check()
            
            # Verify
            assert result["status"] == "unhealthy"
            assert result["service"] == "firecrawl-api"
            assert "Connection failed" in result["error"]
    
    def test_client_initialization_missing_api_key(self):
        """Test client initialization without API key."""
        config = EnrichmentConfig(
            firecrawl_api_key="",  # Empty API key
            firecrawl_base_url="https://api.firecrawl.dev"
        )
        
        with pytest.raises(ConfigurationError) as exc_info:
            FirecrawlClient(config)
        
        assert "Firecrawl API key is required" in str(exc_info.value)
    
    def test_client_initialization_invalid_base_url(self):
        """Test client initialization with invalid base URL."""
        config = EnrichmentConfig(
            firecrawl_api_key="test-key",
            firecrawl_base_url="invalid-url"
        )
        
        with pytest.raises(ConfigurationError) as exc_info:
            FirecrawlClient(config)
        
        assert "Invalid Firecrawl base URL" in str(exc_info.value)


class TestFirecrawlClientSingleton:
    """Test singleton pattern for Firecrawl client."""
    
    def test_get_firecrawl_client_singleton(self):
        """Test that get_firecrawl_client returns same instance."""
        client1 = get_firecrawl_client()
        client2 = get_firecrawl_client()
        assert client1 is client2
    
    def test_get_firecrawl_client_with_config(self):
        """Test getting client with custom configuration."""
        config = EnrichmentConfig(
            firecrawl_api_key="custom-key",
            firecrawl_base_url="https://custom.api.com"
        )
        
        client = get_firecrawl_client(config)
        assert client.api_key == "custom-key"
        assert client.base_url == "https://custom.api.com"


class TestFirecrawlResponseModel:
    """Test FirecrawlResponse model validation."""
    
    def test_firecrawl_response_creation(self):
        """Test creating FirecrawlResponse from API data."""
        data = {
            "url": "https://example.com",
            "content": "<html>test</html>",
            "markdown": "# Test",
            "metadata": {"title": "Test Page"},
            "raw_data": {"extra": "data"},
            "success": True,
            "credits_used": 1,
            "processing_time_ms": 1500
        }
        
        response = FirecrawlResponse(**data)
        
        assert response.url == "https://example.com"
        assert response.content == "<html>test</html>"
        assert response.markdown == "# Test"
        assert response.metadata["title"] == "Test Page"
        assert response.success is True
        assert response.credits_used == 1
        assert response.processing_time_ms == 1500
    
    def test_firecrawl_response_defaults(self):
        """Test FirecrawlResponse with default values."""
        response = FirecrawlResponse(
            url="https://example.com",
            content="<html>test</html>",
            success=True
        )
        
        assert response.markdown == ""
        assert response.metadata == {}
        assert response.raw_data == {}
        assert response.error_message is None
        assert response.credits_used == 1
        assert response.processing_time_ms is None
    
    def test_firecrawl_response_failed(self):
        """Test FirecrawlResponse for failed scraping."""
        response = FirecrawlResponse(
            url="https://example.com",
            content="",
            success=False,
            error_message="Page not found"
        )
        
        assert response.success is False
        assert response.error_message == "Page not found"
