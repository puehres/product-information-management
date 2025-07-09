"""
Unit tests for LawnFawnMatcher.

Tests SKU extraction, search URL construction, and product matching logic
with mocked Firecrawl responses.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from app.services.lawnfawn_matcher import LawnFawnMatcher, get_lawnfawn_matcher
from app.models.product import Product
from app.models.base import ProductStatus
from app.models.enrichment import (
    EnrichmentData, EnrichmentMethod, SearchResults, ProductData, FirecrawlResponse
)
from app.exceptions.enrichment import SKUExtractionError, SearchError, ScrapingError


class TestLawnFawnMatcher:
    """Test suite for LawnFawnMatcher."""
    
    @pytest.fixture
    def mock_firecrawl_client(self):
        """Mock Firecrawl client."""
        mock_client = Mock()
        mock_client.scrape_page = AsyncMock()
        mock_client.search_pages = AsyncMock()
        return mock_client
    
    @pytest.fixture
    def lawnfawn_matcher(self, mock_firecrawl_client):
        """Create LawnFawnMatcher with mocked dependencies."""
        with patch('app.services.lawnfawn_matcher.get_firecrawl_client', return_value=mock_firecrawl_client):
            return LawnFawnMatcher()
    
    @pytest.fixture
    def sample_product(self):
        """Sample product for testing."""
        return Product(
            id=uuid4(),
            batch_id=uuid4(),
            supplier_sku="LF2538",
            manufacturer="lawnfawn",
            supplier_price_usd=12.99,
            status=ProductStatus.DRAFT
        )
    
    @pytest.fixture
    def sample_search_response(self):
        """Sample search results from Firecrawl."""
        return FirecrawlResponse(
            url="https://www.lawnfawn.com/search?q=2538",
            content="""
            <html>
                <body>
                    <div class="search-results">
                        <a href="/products/lf2538-stitched-rectangle-frames">LF2538 Stitched Rectangle Frames</a>
                        <a href="/products/lf2538-coordinating-stamps">LF2538 Coordinating Stamps</a>
                    </div>
                </body>
            </html>
            """,
            success=True,
            credits_used=1
        )
    
    @pytest.fixture
    def sample_product_page_response(self):
        """Sample product page response from Firecrawl."""
        return FirecrawlResponse(
            url="https://www.lawnfawn.com/products/lf2538-stitched-rectangle-frames",
            content="""
            <html>
                <body>
                    <h1>Stitched Rectangle Frames Dies</h1>
                    <div class="product-description">
                        <p>A set of rectangle frame dies with stitched edges for creating beautiful frames.</p>
                    </div>
                    <div class="product-images">
                        <img src="https://cdn.lawnfawn.com/images/lf2538-1.jpg" alt="Product image 1">
                        <img src="https://cdn.lawnfawn.com/images/lf2538-2.jpg" alt="Product image 2">
                    </div>
                    <div class="product-details">
                        <span class="sku">LF2538</span>
                    </div>
                </body>
            </html>
            """,
            success=True,
            credits_used=1
        )


class TestSKUExtraction:
    """Test SKU extraction functionality."""
    
    def test_extract_numeric_sku_standard_format(self):
        """Test extracting SKU from standard LF format."""
        matcher = LawnFawnMatcher()
        
        # Test various standard formats
        assert matcher.extract_numeric_sku("LF2538") == "2538"
        assert matcher.extract_numeric_sku("LF1234") == "1234"
        assert matcher.extract_numeric_sku("LF0001") == "0001"
    
    def test_extract_numeric_sku_with_hyphen(self):
        """Test extracting SKU from LF format with hyphen."""
        matcher = LawnFawnMatcher()
        
        assert matcher.extract_numeric_sku("LF-2538") == "2538"
        assert matcher.extract_numeric_sku("LF-1234") == "1234"
    
    def test_extract_numeric_sku_lowercase(self):
        """Test extracting SKU from lowercase format."""
        matcher = LawnFawnMatcher()
        
        assert matcher.extract_numeric_sku("lf2538") == "2538"
        assert matcher.extract_numeric_sku("lf-1234") == "1234"
    
    def test_extract_numeric_sku_with_spaces(self):
        """Test extracting SKU with surrounding spaces."""
        matcher = LawnFawnMatcher()
        
        assert matcher.extract_numeric_sku(" LF2538 ") == "2538"
        assert matcher.extract_numeric_sku("  LF-1234  ") == "1234"
    
    def test_extract_numeric_sku_invalid_format(self):
        """Test handling of invalid SKU formats."""
        matcher = LawnFawnMatcher()
        
        # Should return None for invalid formats
        assert matcher.extract_numeric_sku("2538") is None  # Missing LF prefix
        assert matcher.extract_numeric_sku("LF") is None    # No number
        assert matcher.extract_numeric_sku("LFABC") is None # Non-numeric
        assert matcher.extract_numeric_sku("") is None      # Empty string
        assert matcher.extract_numeric_sku("XY1234") is None # Wrong prefix
    
    def test_extract_numeric_sku_edge_cases(self):
        """Test edge cases for SKU extraction."""
        matcher = LawnFawnMatcher()
        
        # Test with additional text
        assert matcher.extract_numeric_sku("LF2538 - Dies") == "2538"
        assert matcher.extract_numeric_sku("Product LF1234 Stamps") == "1234"
        
        # Test with multiple numbers (should get first)
        assert matcher.extract_numeric_sku("LF2538LF1234") == "2538"


class TestSearchURLConstruction:
    """Test search URL construction."""
    
    def test_build_search_url_standard(self):
        """Test building search URL with standard SKU."""
        matcher = LawnFawnMatcher()
        
        url = matcher.build_search_url("2538")
        expected = "https://www.lawnfawn.com/search?options%5Bprefix%5D=last&q=2538&filter.p.product_type="
        assert url == expected
    
    def test_build_search_url_with_leading_zeros(self):
        """Test building search URL preserving leading zeros."""
        matcher = LawnFawnMatcher()
        
        url = matcher.build_search_url("0001")
        expected = "https://www.lawnfawn.com/search?options%5Bprefix%5D=last&q=0001&filter.p.product_type="
        assert url == expected
    
    def test_build_search_url_custom_base(self):
        """Test building search URL with custom base URL."""
        config = Mock()
        config.lawnfawn_base_url = "https://custom.lawnfawn.com"
        matcher = LawnFawnMatcher(config)
        
        url = matcher.build_search_url("2538")
        expected = "https://custom.lawnfawn.com/search?options%5Bprefix%5D=last&q=2538&filter.p.product_type="
        assert url == expected


class TestSearchResultsParsing:
    """Test parsing of search results."""
    
    @pytest.mark.asyncio
    async def test_parse_search_results_success(self, lawnfawn_matcher, sample_search_response):
        """Test successful parsing of search results."""
        search_results = lawnfawn_matcher.parse_search_results(sample_search_response)
        
        assert isinstance(search_results, SearchResults)
        assert search_results.search_url == "https://www.lawnfawn.com/search?q=2538"
        assert len(search_results.product_links) == 2
        assert "https://www.lawnfawn.com/products/lf2538-stitched-rectangle-frames" in search_results.product_links
        assert "https://www.lawnfawn.com/products/lf2538-coordinating-stamps" in search_results.product_links
        assert search_results.total_results == 2
    
    def test_parse_search_results_no_results(self, lawnfawn_matcher):
        """Test parsing when no search results found."""
        empty_response = FirecrawlResponse(
            url="https://www.lawnfawn.com/search?q=9999",
            content="<html><body><div class='no-results'>No products found</div></body></html>",
            success=True
        )
        
        search_results = lawnfawn_matcher.parse_search_results(empty_response)
        
        assert search_results.total_results == 0
        assert len(search_results.product_links) == 0
    
    def test_parse_search_results_relative_urls(self, lawnfawn_matcher):
        """Test parsing search results with relative URLs."""
        response_with_relative_urls = FirecrawlResponse(
            url="https://www.lawnfawn.com/search?q=2538",
            content="""
            <html>
                <body>
                    <div class="search-results">
                        <a href="/products/lf2538-dies">LF2538 Dies</a>
                        <a href="/products/lf2538-stamps">LF2538 Stamps</a>
                    </div>
                </body>
            </html>
            """,
            success=True
        )
        
        search_results = lawnfawn_matcher.parse_search_results(response_with_relative_urls)
        
        # Should convert relative URLs to absolute
        assert "https://www.lawnfawn.com/products/lf2538-dies" in search_results.product_links
        assert "https://www.lawnfawn.com/products/lf2538-stamps" in search_results.product_links


class TestProductPageScraping:
    """Test product page scraping and data extraction."""
    
    @pytest.mark.asyncio
    async def test_scrape_product_page_success(self, lawnfawn_matcher, sample_product_page_response):
        """Test successful product page scraping."""
        product_data = lawnfawn_matcher.extract_product_data(sample_product_page_response)
        
        assert isinstance(product_data, ProductData)
        assert product_data.name == "Stitched Rectangle Frames Dies"
        assert "rectangle frame dies with stitched edges" in product_data.description
        assert product_data.sku == "LF2538"
        assert len(product_data.image_urls) == 2
        assert "https://cdn.lawnfawn.com/images/lf2538-1.jpg" in product_data.image_urls
        assert "https://cdn.lawnfawn.com/images/lf2538-2.jpg" in product_data.image_urls
        assert product_data.product_url == "https://www.lawnfawn.com/products/lf2538-stitched-rectangle-frames"
    
    def test_extract_product_data_missing_elements(self, lawnfawn_matcher):
        """Test extracting data when some elements are missing."""
        minimal_response = FirecrawlResponse(
            url="https://www.lawnfawn.com/products/test-product",
            content="""
            <html>
                <body>
                    <h1>Test Product</h1>
                    <!-- No description, images, or SKU -->
                </body>
            </html>
            """,
            success=True
        )
        
        product_data = lawnfawn_matcher.extract_product_data(minimal_response)
        
        assert product_data.name == "Test Product"
        assert product_data.description == ""
        assert product_data.sku == ""
        assert len(product_data.image_urls) == 0
    
    def test_extract_product_data_multiple_titles(self, lawnfawn_matcher):
        """Test extracting data when multiple title elements exist."""
        response_with_multiple_titles = FirecrawlResponse(
            url="https://www.lawnfawn.com/products/test-product",
            content="""
            <html>
                <head><title>Page Title</title></head>
                <body>
                    <h1>Main Product Title</h1>
                    <h2>Subtitle</h2>
                </body>
            </html>
            """,
            success=True
        )
        
        product_data = lawnfawn_matcher.extract_product_data(response_with_multiple_titles)
        
        # Should use the first h1 as the main title
        assert product_data.name == "Main Product Title"


class TestConfidenceScoring:
    """Test confidence scoring algorithm."""
    
    def test_calculate_confidence_exact_sku_match(self, lawnfawn_matcher):
        """Test confidence scoring for exact SKU match."""
        product = Product(supplier_sku="LF2538", manufacturer="lawnfawn")
        product_data = ProductData(
            name="Stitched Rectangle Frames Dies",
            sku="LF2538",  # Exact match
            product_url="https://www.lawnfawn.com/products/lf2538"
        )
        
        confidence = lawnfawn_matcher.calculate_confidence_score(
            product, product_data, EnrichmentMethod.SEARCH_FIRST_RESULT, is_first_result=True
        )
        
        assert confidence == 100  # Exact SKU match
    
    def test_calculate_confidence_first_result_no_sku_match(self, lawnfawn_matcher):
        """Test confidence scoring for first result without SKU match."""
        product = Product(supplier_sku="LF2538", manufacturer="lawnfawn")
        product_data = ProductData(
            name="Stitched Rectangle Frames Dies",
            sku="",  # No SKU found on page
            product_url="https://www.lawnfawn.com/products/lf2538"
        )
        
        confidence = lawnfawn_matcher.calculate_confidence_score(
            product, product_data, EnrichmentMethod.SEARCH_FIRST_RESULT, is_first_result=True
        )
        
        assert confidence == 90  # First result, no SKU match
    
    def test_calculate_confidence_first_result_sku_mismatch(self, lawnfawn_matcher):
        """Test confidence scoring for first result with SKU mismatch."""
        product = Product(supplier_sku="LF2538", manufacturer="lawnfawn")
        product_data = ProductData(
            name="Different Product",
            sku="LF1234",  # Different SKU
            product_url="https://www.lawnfawn.com/products/lf1234"
        )
        
        confidence = lawnfawn_matcher.calculate_confidence_score(
            product, product_data, EnrichmentMethod.SEARCH_FIRST_RESULT, is_first_result=True
        )
        
        assert confidence == 60  # First result, SKU mismatch
    
    def test_calculate_confidence_fallback_method(self, lawnfawn_matcher):
        """Test confidence scoring for fallback method."""
        product = Product(supplier_sku="LF2538", manufacturer="lawnfawn")
        product_data = ProductData(
            name="Fallback Product",
            sku="LF2538",
            product_url="https://www.lawnfawn.com/products/fallback"
        )
        
        confidence = lawnfawn_matcher.calculate_confidence_score(
            product, product_data, EnrichmentMethod.FALLBACK, is_first_result=False
        )
        
        assert confidence == 30  # Fallback method


class TestCompleteMatchingWorkflow:
    """Test complete product matching workflow."""
    
    @pytest.mark.asyncio
    async def test_match_product_success(self, lawnfawn_matcher, mock_firecrawl_client, 
                                       sample_product, sample_search_response, sample_product_page_response):
        """Test successful complete product matching."""
        # Setup mocks
        mock_firecrawl_client.scrape_page.side_effect = [
            sample_search_response,  # Search results
            sample_product_page_response  # Product page
        ]
        
        # Execute
        enrichment_data = await lawnfawn_matcher.match_product(sample_product)
        
        # Verify
        assert isinstance(enrichment_data, EnrichmentData)
        assert enrichment_data.search_url == "https://www.lawnfawn.com/search?options%5Bprefix%5D=last&q=2538&filter.p.product_type="
        assert enrichment_data.product_url == "https://www.lawnfawn.com/products/lf2538-stitched-rectangle-frames"
        assert enrichment_data.product_name == "Stitched Rectangle Frames Dies"
        assert "rectangle frame dies" in enrichment_data.description
        assert len(enrichment_data.image_urls) == 2
        assert enrichment_data.confidence_score == 100  # Exact SKU match
        assert enrichment_data.method == EnrichmentMethod.SEARCH_FIRST_RESULT
        
        # Verify Firecrawl calls
        assert mock_firecrawl_client.scrape_page.call_count == 2
    
    @pytest.mark.asyncio
    async def test_match_product_invalid_sku(self, lawnfawn_matcher, sample_product):
        """Test matching with invalid SKU format."""
        # Product with invalid SKU
        sample_product.supplier_sku = "INVALID123"
        
        # Execute and verify exception
        with pytest.raises(SKUExtractionError) as exc_info:
            await lawnfawn_matcher.match_product(sample_product)
        
        assert "Could not extract numeric SKU" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_match_product_no_search_results(self, lawnfawn_matcher, mock_firecrawl_client, sample_product):
        """Test matching when search returns no results."""
        # Setup mock for empty search results
        empty_search_response = FirecrawlResponse(
            url="https://www.lawnfawn.com/search?q=2538",
            content="<html><body><div class='no-results'>No products found</div></body></html>",
            success=True
        )
        mock_firecrawl_client.scrape_page.return_value = empty_search_response
        
        # Execute and verify exception
        with pytest.raises(SearchError) as exc_info:
            await lawnfawn_matcher.match_product(sample_product)
        
        assert "No search results found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_match_product_scraping_failure(self, lawnfawn_matcher, mock_firecrawl_client, 
                                                 sample_product, sample_search_response):
        """Test matching when product page scraping fails."""
        # Setup mocks
        mock_firecrawl_client.scrape_page.side_effect = [
            sample_search_response,  # Search succeeds
            FirecrawlResponse(  # Product page fails
                url="https://www.lawnfawn.com/products/lf2538",
                content="",
                success=False,
                error_message="Page not accessible"
            )
        ]
        
        # Execute and verify exception
        with pytest.raises(ScrapingError) as exc_info:
            await lawnfawn_matcher.match_product(sample_product)
        
        assert "Failed to scrape product page" in str(exc_info.value)


class TestLawnFawnMatcherSingleton:
    """Test singleton pattern for LawnFawn matcher."""
    
    def test_get_lawnfawn_matcher_singleton(self):
        """Test that get_lawnfawn_matcher returns same instance."""
        matcher1 = get_lawnfawn_matcher()
        matcher2 = get_lawnfawn_matcher()
        assert matcher1 is matcher2
    
    def test_get_lawnfawn_matcher_with_config(self):
        """Test getting matcher with custom configuration."""
        config = Mock()
        config.lawnfawn_base_url = "https://custom.lawnfawn.com"
        
        matcher = get_lawnfawn_matcher(config)
        assert matcher.base_url == "https://custom.lawnfawn.com"


class TestErrorHandling:
    """Test error handling in various scenarios."""
    
    @pytest.mark.asyncio
    async def test_handle_firecrawl_timeout(self, lawnfawn_matcher, mock_firecrawl_client, sample_product):
        """Test handling of Firecrawl timeout errors."""
        from app.exceptions.enrichment import FirecrawlAPIError
        
        mock_firecrawl_client.scrape_page.side_effect = FirecrawlAPIError("Request timeout")
        
        with pytest.raises(ScrapingError) as exc_info:
            await lawnfawn_matcher.match_product(sample_product)
        
        assert "Scraping failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_handle_invalid_html(self, lawnfawn_matcher, mock_firecrawl_client, sample_product):
        """Test handling of invalid HTML content."""
        # Setup mock with malformed HTML
        malformed_response = FirecrawlResponse(
            url="https://www.lawnfawn.com/search?q=2538",
            content="<html><body><div>Unclosed div</body></html>",  # Malformed HTML
            success=True
        )
        mock_firecrawl_client.scrape_page.return_value = malformed_response
        
        # Should handle gracefully and return empty results
        with pytest.raises(SearchError):
            await lawnfawn_matcher.match_product(sample_product)
