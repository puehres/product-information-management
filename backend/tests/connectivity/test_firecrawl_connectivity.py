"""
Connectivity tests for Firecrawl API integration.

Tests actual connection to Firecrawl API, authentication, rate limiting,
and environment variable validation using REAL API calls.
"""

import pytest
import os
import asyncio
from datetime import datetime

from app.services.firecrawl_client import FirecrawlClient, get_firecrawl_client, reset_firecrawl_client
from app.models.enrichment import EnrichmentConfig, FirecrawlResponse
from app.exceptions.enrichment import FirecrawlAPIError, ConfigurationError, ScrapingError


class TestFirecrawlConnectivity:
    """Test Firecrawl API connectivity with real API calls."""
    
    @pytest.fixture
    def test_config(self):
        """Test configuration for Firecrawl connectivity."""
        api_key = os.getenv('FIRECRAWL_API_KEY')
        if not api_key:
            pytest.skip("FIRECRAWL_API_KEY not available for connectivity tests")
            
        return EnrichmentConfig(
            firecrawl_api_key=api_key,
            firecrawl_base_url=os.getenv('FIRECRAWL_BASE_URL', 'https://api.firecrawl.dev'),
            firecrawl_timeout=30,
            max_concurrent_requests=5,
            retry_attempts=3,
            retry_delay=2
        )
    
    @pytest.fixture(autouse=True)
    def reset_client(self):
        """Reset client before each test."""
        reset_firecrawl_client()
        yield
        reset_firecrawl_client()
    
    @pytest.mark.asyncio
    async def test_firecrawl_api_authentication(self, test_config):
        """Test Firecrawl API authentication with real API."""
        client = FirecrawlClient(test_config)
        
        # Test with a simple page scrape (this tests authentication)
        test_url = "https://httpbin.org/html"
        result = await client.scrape_page(test_url)
        
        # Verify successful authentication and scraping
        assert isinstance(result, FirecrawlResponse)
        assert result.success is True
        assert result.url == test_url
        assert len(result.content) > 0
        assert len(result.markdown) > 0
        assert result.credits_used >= 1
        assert result.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_firecrawl_api_invalid_authentication(self):
        """Test handling of invalid API key with real API."""
        # Use invalid API key
        invalid_config = EnrichmentConfig(
            firecrawl_api_key="invalid-key-12345",
            firecrawl_base_url="https://api.firecrawl.dev"
        )
        client = FirecrawlClient(invalid_config)
        
        # Execute and verify exception
        with pytest.raises(FirecrawlAPIError) as exc_info:
            await client.scrape_page("https://httpbin.org/html")
        
        # Should get 401 or similar authentication error
        assert exc_info.value.status_code in [401, 403]
        assert "401" in str(exc_info.value) or "403" in str(exc_info.value) or "Unauthorized" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_firecrawl_scraping_functionality(self, test_config):
        """Test basic scraping functionality with real Firecrawl API."""
        client = FirecrawlClient(test_config)
        test_url = "https://httpbin.org/html"
        
        # Execute real scraping
        result = await client.scrape_page(test_url)
        
        # Verify real response structure
        assert isinstance(result, FirecrawlResponse)
        assert result.success is True
        assert result.url == test_url
        assert "Herman Melville" in result.content  # httpbin.org/html contains Moby Dick text
        assert "# Herman Melville" in result.markdown
        assert result.credits_used >= 1
        assert result.processing_time_ms > 0
        assert isinstance(result.metadata, dict)
        assert isinstance(result.raw_data, dict)
        assert result.raw_data.get('success') is True
    
    @pytest.mark.asyncio
    async def test_firecrawl_timeout_handling(self, test_config):
        """Test handling of timeout scenarios."""
        # Use very short timeout to force timeout
        short_timeout_config = EnrichmentConfig(
            firecrawl_api_key=test_config.firecrawl_api_key,
            firecrawl_base_url=test_config.firecrawl_base_url,
            firecrawl_timeout=1  # 1 second timeout
        )
        client = FirecrawlClient(short_timeout_config)
        
        # Execute and verify timeout handling
        with pytest.raises(ScrapingError) as exc_info:
            await client.scrape_page("https://httpbin.org/delay/5")  # 5 second delay
        
        assert "Timeout after 1s" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_firecrawl_health_check(self, test_config):
        """Test Firecrawl service health check with real API."""
        client = FirecrawlClient(test_config)
        
        # Execute real health check
        start_time = datetime.utcnow()
        health = await client.health_check()
        end_time = datetime.utcnow()
        
        # Verify health check response structure
        assert health["status"] == "healthy"
        assert health["service"] == "firecrawl-api"
        assert "response_time_ms" in health
        assert health["api_accessible"] is True
        assert health["base_url"] == test_config.firecrawl_base_url
        
        # Verify response time is reasonable
        response_time = (end_time - start_time).total_seconds() * 1000
        assert health["response_time_ms"] <= response_time + 1000  # Allow some margin
    
    @pytest.mark.asyncio
    async def test_firecrawl_health_check_failure(self):
        """Test health check when Firecrawl is unreachable."""
        # Use invalid base URL to simulate failure
        invalid_config = EnrichmentConfig(
            firecrawl_api_key="test-key",
            firecrawl_base_url="https://invalid-firecrawl-url.com"
        )
        client = FirecrawlClient(invalid_config)
        
        # Execute health check
        health = await client.health_check()
        
        # Verify failure response
        assert health["status"] == "unhealthy"
        assert health["service"] == "firecrawl-api"
        assert health["api_accessible"] is False
        assert "error" in health
    
    def test_environment_variable_validation(self):
        """Test validation of required environment variables."""
        # Test missing API key
        with pytest.raises(ConfigurationError) as exc_info:
            config = EnrichmentConfig(
                firecrawl_api_key="",  # Empty API key
                firecrawl_base_url="https://api.firecrawl.dev"
            )
            FirecrawlClient(config)
        
        assert "FIRECRAWL_API_KEY environment variable is required" in str(exc_info.value)
    
    def test_configuration_defaults(self):
        """Test default configuration values."""
        config = EnrichmentConfig(
            firecrawl_api_key="test-key"
        )
        
        assert config.firecrawl_base_url == "https://api.firecrawl.dev"
        assert config.firecrawl_timeout == 30
        assert config.max_concurrent_requests == 5
        assert config.retry_attempts == 3
        assert config.retry_delay == 2
    
    def test_configuration_custom_values(self):
        """Test custom configuration values."""
        config = EnrichmentConfig(
            firecrawl_api_key="custom-key",
            firecrawl_base_url="https://custom.api.com",
            firecrawl_timeout=60,
            max_concurrent_requests=10,
            retry_attempts=5,
            retry_delay=5
        )
        
        assert config.firecrawl_api_key == "custom-key"
        assert config.firecrawl_base_url == "https://custom.api.com"
        assert config.firecrawl_timeout == 60
        assert config.max_concurrent_requests == 10
        assert config.retry_attempts == 5
        assert config.retry_delay == 5
    
    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, test_config):
        """Test handling of concurrent requests with real API."""
        client = FirecrawlClient(test_config)
        
        # Execute multiple concurrent requests (be gentle with real API)
        urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json", 
            "https://httpbin.org/xml"
        ]
        
        tasks = [client.scrape_page(url) for url in urls]
        results = await asyncio.gather(*tasks)
        
        # Verify all requests succeeded
        assert len(results) == 3
        assert all(isinstance(r, FirecrawlResponse) for r in results)
        assert all(r.success for r in results)
        assert all(r.credits_used >= 1 for r in results)
    
    @pytest.mark.asyncio
    async def test_get_credits_info_mock(self, test_config):
        """Test credits info returns mock data (since real endpoint doesn't exist)."""
        client = FirecrawlClient(test_config)
        
        # Execute credits info (should return mock data)
        credits_info = await client.get_credits_info()
        
        # Verify mock structure
        assert credits_info["total"] == 1000
        assert credits_info["used"] == 100
        assert credits_info["remaining"] == 900
        assert credits_info["status"] == "mock"
        assert "not available" in credits_info["message"]


class TestFirecrawlClientSingleton:
    """Test singleton behavior with real environment."""
    
    @pytest.fixture(autouse=True)
    def reset_client(self):
        """Reset client before each test."""
        reset_firecrawl_client()
        yield
        reset_firecrawl_client()
    
    def test_singleton_with_environment_config(self):
        """Test singleton behavior with environment-based configuration."""
        api_key = os.getenv('FIRECRAWL_API_KEY')
        if not api_key:
            pytest.skip("FIRECRAWL_API_KEY not available for singleton tests")
        
        # Test that singleton returns same instance
        client1 = get_firecrawl_client()
        client2 = get_firecrawl_client()
        assert client1 is client2
        assert client1.api_key == api_key
    
    def test_singleton_with_custom_config(self):
        """Test singleton behavior with custom configuration."""
        api_key = os.getenv('FIRECRAWL_API_KEY', 'test-key')
        
        config = EnrichmentConfig(
            firecrawl_api_key=api_key,
            firecrawl_base_url="https://custom.api.com"
        )
        
        client = get_firecrawl_client(config)
        assert client.api_key == api_key
        assert client.base_url == "https://custom.api.com"


class TestFirecrawlIntegrationScenarios:
    """Test realistic integration scenarios with real API."""
    
    @pytest.fixture
    def test_config(self):
        """Test configuration for integration scenarios."""
        api_key = os.getenv('FIRECRAWL_API_KEY')
        if not api_key:
            pytest.skip("FIRECRAWL_API_KEY not available for integration tests")
            
        return EnrichmentConfig(
            firecrawl_api_key=api_key,
            firecrawl_base_url=os.getenv('FIRECRAWL_BASE_URL', 'https://api.firecrawl.dev'),
            firecrawl_timeout=30
        )
    
    @pytest.fixture(autouse=True)
    def reset_client(self):
        """Reset client before each test."""
        reset_firecrawl_client()
        yield
        reset_firecrawl_client()
    
    @pytest.mark.asyncio
    async def test_lawnfawn_search_integration(self, test_config):
        """Test realistic LawnFawn search scenario with real API."""
        client = FirecrawlClient(test_config)
        
        # Test scraping a LawnFawn search page (be respectful)
        search_url = "https://www.lawnfawn.com/search?q=2538"
        
        try:
            result = await client.scrape_page(search_url)
            
            # Verify search results structure
            assert isinstance(result, FirecrawlResponse)
            assert result.success is True
            assert result.url == search_url
            assert len(result.content) > 0
            assert len(result.markdown) > 0
            assert result.credits_used >= 1
            
            # Check for search-related content (may vary based on actual results)
            content_lower = result.content.lower()
            assert any(keyword in content_lower for keyword in ['search', 'product', 'lawnfawn', 'lawn fawn'])
            
        except Exception as e:
            # If LawnFawn blocks scraping, that's expected behavior
            if "403" in str(e) or "blocked" in str(e).lower():
                pytest.skip(f"LawnFawn blocks scraping (expected): {e}")
            else:
                raise
    
    @pytest.mark.asyncio
    async def test_product_page_scraping_integration(self, test_config):
        """Test realistic product page scraping scenario with real API."""
        client = FirecrawlClient(test_config)
        
        # Use a more scraping-friendly test site
        product_url = "https://httpbin.org/html"
        
        result = await client.scrape_page(product_url)
        
        # Verify product data extraction capabilities
        assert isinstance(result, FirecrawlResponse)
        assert result.success is True
        assert result.url == product_url
        assert "Herman Melville" in result.content
        assert "Moby-Dick" in result.content
        assert "# Herman Melville" in result.markdown
        assert result.credits_used >= 1
        assert isinstance(result.metadata, dict)
        
        # Verify metadata contains useful information
        metadata = result.metadata
        assert isinstance(metadata, dict)
        # Metadata structure may vary, but should contain some useful info
        assert len(str(metadata)) > 10  # Should have some content
