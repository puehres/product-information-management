"""
Unit tests for ProductEnrichmentService.

Tests the main enrichment orchestrator with mocked dependencies,
following patterns from existing test_product_deduplication.py.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4, UUID
from datetime import datetime

from app.services.product_enrichment import ProductEnrichmentService, get_product_enrichment_service
from app.models.product import Product
from app.models.base import ProductStatus
from app.models.enrichment import (
    EnrichmentData, EnrichmentMethod, ProductEnrichmentResult, 
    EnrichmentResult, ScrapingAttempt, ScrapingStatus
)
from app.exceptions.enrichment import EnrichmentError, SKUExtractionError, SearchError


class TestProductEnrichmentService:
    """Test suite for ProductEnrichmentService."""
    
    @pytest.fixture(autouse=True)
    def mock_environment_variables(self, monkeypatch):
        """Mock required environment variables for testing."""
        monkeypatch.setenv("FIRECRAWL_API_KEY", "test-api-key")
        monkeypatch.setenv("FIRECRAWL_BASE_URL", "https://api.firecrawl.dev")
        monkeypatch.setenv("FIRECRAWL_TIMEOUT", "30")
        monkeypatch.setenv("FIRECRAWL_MAX_RETRIES", "3")
        monkeypatch.setenv("FIRECRAWL_RETRY_DELAY", "2")
    
    @pytest.fixture
    def mock_database_service(self):
        """Mock database service with common methods."""
        mock_service = Mock()
        mock_service.get_product_by_id = AsyncMock()
        mock_service.get_products = AsyncMock()
        mock_service.client = Mock()
        mock_service.client.table.return_value.insert.return_value.execute.return_value.data = [
            {'id': str(uuid4()), 'attempt_number': 1, 'created_at': datetime.utcnow().isoformat(), 'updated_at': datetime.utcnow().isoformat()}
        ]
        mock_service.client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{}]
        return mock_service
    
    @pytest.fixture
    def mock_lawnfawn_matcher(self):
        """Mock LawnFawn matcher service."""
        mock_matcher = Mock()
        mock_matcher.match_product = AsyncMock()
        return mock_matcher
    
    @pytest.fixture
    def mock_firecrawl_client(self):
        """Mock Firecrawl client service."""
        mock_client = Mock()
        mock_client.health_check = AsyncMock(return_value={"status": "healthy"})
        mock_client.get_credits_info = AsyncMock(return_value={"credits": 100})
        return mock_client
    
    @pytest.fixture
    def sample_product(self):
        """Sample product for testing."""
        return Product(
            id=uuid4(),
            batch_id=uuid4(),
            supplier_id=uuid4(),
            supplier_sku="LF2538",
            manufacturer="lawnfawn",
            supplier_price_usd=12.99,
            status=ProductStatus.DRAFT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_enrichment_data(self):
        """Sample enrichment data for testing."""
        return EnrichmentData(
            search_url="https://www.lawnfawn.com/search?q=2538",
            product_url="https://www.lawnfawn.com/products/lf2538",
            product_name="Stitched Rectangle Frames Dies",
            description="A set of rectangle frame dies",
            image_urls=["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
            confidence_score=90,
            method=EnrichmentMethod.SEARCH_FIRST_RESULT,
            raw_response={"success": True},
            image_metadata=[{"url": "https://example.com/image1.jpg", "alt": "Product image"}],
            processing_time_ms=1500
        )
    
    @pytest.fixture
    def enrichment_service(self, mock_database_service, mock_lawnfawn_matcher, mock_firecrawl_client):
        """Create enrichment service with mocked dependencies."""
        with patch('app.services.product_enrichment.get_database_service', return_value=mock_database_service), \
             patch('app.services.product_enrichment.get_lawnfawn_matcher', return_value=mock_lawnfawn_matcher), \
             patch('app.services.product_enrichment.get_firecrawl_client', return_value=mock_firecrawl_client):
            return ProductEnrichmentService()
    
    @pytest.mark.asyncio
    async def test_enrich_product_success(self, enrichment_service, mock_database_service, 
                                        mock_lawnfawn_matcher, sample_product, sample_enrichment_data):
        """Test successful product enrichment."""
        # Setup mocks
        mock_database_service.get_product_by_id.return_value = sample_product
        mock_lawnfawn_matcher.match_product.return_value = sample_enrichment_data
        
        # Execute
        result = await enrichment_service.enrich_product(sample_product.id)
        
        # Verify
        assert result.success is True
        assert result.confidence_score == 90
        assert result.method == EnrichmentMethod.SEARCH_FIRST_RESULT
        assert result.product_url == "https://www.lawnfawn.com/products/lf2538"
        assert result.images_found == 2
        
        # Verify database calls
        mock_database_service.get_product_by_id.assert_called_once_with(sample_product.id)
        mock_lawnfawn_matcher.match_product.assert_called_once_with(sample_product)
    
    @pytest.mark.asyncio
    async def test_enrich_product_not_found(self, enrichment_service, mock_database_service):
        """Test enrichment when product not found."""
        # Setup
        product_id = uuid4()
        mock_database_service.get_product_by_id.return_value = None
        
        # Execute
        result = await enrichment_service.enrich_product(product_id)
        
        # Verify
        assert result.success is False
        assert "Product not found" in result.error_message
    
    @pytest.mark.asyncio
    async def test_enrich_product_no_supplier_sku(self, enrichment_service, mock_database_service):
        """Test enrichment when product has no supplier SKU."""
        # Setup
        product = Product(
            id=uuid4(),
            batch_id=uuid4(),
            supplier_id=uuid4(),
            supplier_sku="",  # Empty SKU
            manufacturer="lawnfawn",
            status=ProductStatus.DRAFT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_database_service.get_product_by_id.return_value = product
        
        # Execute
        result = await enrichment_service.enrich_product(product.id)
        
        # Verify
        assert result.success is False
        assert "No supplier SKU available" in result.error_message
    
    @pytest.mark.asyncio
    async def test_enrich_product_sku_extraction_error(self, enrichment_service, mock_database_service, 
                                                      mock_lawnfawn_matcher, sample_product):
        """Test handling of SKU extraction errors."""
        # Setup
        mock_database_service.get_product_by_id.return_value = sample_product
        mock_lawnfawn_matcher.match_product.side_effect = SKUExtractionError("Invalid SKU format")
        
        # Execute
        result = await enrichment_service.enrich_product(sample_product.id)
        
        # Verify
        assert result.success is False
        assert "Invalid SKU format" in result.error_message
    
    @pytest.mark.asyncio
    async def test_enrich_product_search_error(self, enrichment_service, mock_database_service, 
                                             mock_lawnfawn_matcher, sample_product):
        """Test handling of search errors."""
        # Setup
        mock_database_service.get_product_by_id.return_value = sample_product
        mock_lawnfawn_matcher.match_product.side_effect = SearchError("No search results found")
        
        # Execute
        result = await enrichment_service.enrich_product(sample_product.id)
        
        # Verify
        assert result.success is False
        assert "No search results found" in result.error_message
    
    @pytest.mark.asyncio
    async def test_enrich_product_unexpected_error(self, enrichment_service, mock_database_service, 
                                                  mock_lawnfawn_matcher, sample_product):
        """Test handling of unexpected errors."""
        # Setup
        mock_database_service.get_product_by_id.return_value = sample_product
        mock_lawnfawn_matcher.match_product.side_effect = Exception("Unexpected error")
        
        # Execute
        result = await enrichment_service.enrich_product(sample_product.id)
        
        # Verify
        assert result.success is False
        assert "Unexpected error" in result.error_message
    
    @pytest.mark.asyncio
    async def test_enrich_batch_success(self, enrichment_service, mock_database_service, 
                                       mock_lawnfawn_matcher, sample_enrichment_data):
        """Test successful batch enrichment."""
        # Setup
        batch_id = uuid4()
        products = [
            Product(id=uuid4(), batch_id=batch_id, supplier_id=uuid4(), supplier_sku="LF2538", manufacturer="lawnfawn", status=ProductStatus.DRAFT, created_at=datetime.utcnow(), updated_at=datetime.utcnow()),
            Product(id=uuid4(), batch_id=batch_id, supplier_id=uuid4(), supplier_sku="LF2539", manufacturer="lawnfawn", status=ProductStatus.DRAFT, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
        ]
        
        mock_database_service.get_products.return_value = products
        # Mock get_product_by_id to return the products when called individually
        mock_database_service.get_product_by_id.side_effect = lambda pid: next((p for p in products if p.id == pid), None)
        mock_lawnfawn_matcher.match_product.return_value = sample_enrichment_data
        
        # Execute
        result = await enrichment_service.enrich_batch(batch_id)
        
        # Verify
        assert result.batch_id == batch_id
        assert result.total_products == 2
        assert result.successful_enrichments == 2
        assert result.failed_enrichments == 0
        assert len(result.results) == 2
        assert all(r.success for r in result.results)
    
    @pytest.mark.asyncio
    async def test_enrich_batch_empty(self, enrichment_service, mock_database_service):
        """Test batch enrichment with no products."""
        # Setup
        batch_id = uuid4()
        mock_database_service.get_products.return_value = []
        
        # Execute
        result = await enrichment_service.enrich_batch(batch_id)
        
        # Verify
        assert result.batch_id == batch_id
        assert result.total_products == 0
        assert result.successful_enrichments == 0
        assert result.failed_enrichments == 0
        assert len(result.results) == 0
    
    @pytest.mark.asyncio
    async def test_enrich_batch_mixed_results(self, enrichment_service, mock_database_service, 
                                            mock_lawnfawn_matcher, sample_enrichment_data):
        """Test batch enrichment with mixed success/failure results."""
        # Setup
        batch_id = uuid4()
        products = [
            Product(id=uuid4(), batch_id=batch_id, supplier_id=uuid4(), supplier_sku="LF2538", manufacturer="lawnfawn", status=ProductStatus.DRAFT, created_at=datetime.utcnow(), updated_at=datetime.utcnow()),
            Product(id=uuid4(), batch_id=batch_id, supplier_id=uuid4(), supplier_sku="INVALID", manufacturer="lawnfawn", status=ProductStatus.DRAFT, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
        ]
        
        mock_database_service.get_products.return_value = products
        # Mock get_product_by_id to return the products when called individually
        mock_database_service.get_product_by_id.side_effect = lambda pid: next((p for p in products if p.id == pid), None)
        
        # First product succeeds, second fails
        mock_lawnfawn_matcher.match_product.side_effect = [
            sample_enrichment_data,
            SKUExtractionError("Invalid SKU")
        ]
        
        # Execute
        result = await enrichment_service.enrich_batch(batch_id)
        
        # Verify
        assert result.batch_id == batch_id
        assert result.total_products == 2
        assert result.successful_enrichments == 1
        assert result.failed_enrichments == 1
        assert len(result.results) == 2
        assert result.results[0].success is True
        assert result.results[1].success is False
    
    @pytest.mark.asyncio
    async def test_enrich_products_by_ids(self, enrichment_service, mock_database_service, 
                                        mock_lawnfawn_matcher, sample_enrichment_data):
        """Test enriching specific products by ID."""
        # Setup
        product_ids = [uuid4(), uuid4()]
        products = [
            Product(id=product_ids[0], batch_id=uuid4(), supplier_id=uuid4(), supplier_sku="LF2538", manufacturer="lawnfawn", status=ProductStatus.DRAFT, created_at=datetime.utcnow(), updated_at=datetime.utcnow()),
            Product(id=product_ids[1], batch_id=uuid4(), supplier_id=uuid4(), supplier_sku="LF2539", manufacturer="lawnfawn", status=ProductStatus.DRAFT, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
        ]
        
        mock_database_service.get_product_by_id.side_effect = products
        mock_lawnfawn_matcher.match_product.return_value = sample_enrichment_data
        
        # Execute
        results = await enrichment_service.enrich_products(product_ids)
        
        # Verify
        assert len(results) == 2
        assert all(r.success for r in results)
        assert results[0].product_id == product_ids[0]
        assert results[1].product_id == product_ids[1]
    
    @pytest.mark.asyncio
    async def test_get_enrichment_status(self, enrichment_service, mock_database_service):
        """Test getting enrichment status for a batch."""
        # Setup
        batch_id = uuid4()
        products = [
            Product(id=uuid4(), batch_id=batch_id, supplier_id=uuid4(), supplier_sku="LF2538", status=ProductStatus.READY, scraping_confidence=90, created_at=datetime.utcnow(), updated_at=datetime.utcnow()),
            Product(id=uuid4(), batch_id=batch_id, supplier_id=uuid4(), supplier_sku="LF2539", status=ProductStatus.FAILED, created_at=datetime.utcnow(), updated_at=datetime.utcnow()),
            Product(id=uuid4(), batch_id=batch_id, supplier_id=uuid4(), supplier_sku="LF2540", status=ProductStatus.PROCESSING, created_at=datetime.utcnow(), updated_at=datetime.utcnow()),
            Product(id=uuid4(), batch_id=batch_id, supplier_id=uuid4(), supplier_sku="LF2541", status=ProductStatus.DRAFT, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
        ]
        mock_database_service.get_products.return_value = products
        
        # Execute
        status = await enrichment_service.get_enrichment_status(batch_id)
        
        # Verify
        assert status["batch_id"] == str(batch_id)
        assert status["total_products"] == 4
        assert status["completed_products"] == 1
        assert status["failed_products"] == 1
        assert status["processing_products"] == 1
        assert status["pending_products"] == 1
        assert status["avg_confidence_score"] == 90.0
    
    @pytest.mark.asyncio
    async def test_health_check(self, enrichment_service, mock_database_service, mock_firecrawl_client):
        """Test service health check."""
        # Setup - make sure these are async mocks
        mock_database_service.health_check = AsyncMock(return_value={"status": "healthy"})
        mock_firecrawl_client.health_check = AsyncMock(return_value={"status": "healthy"})
        
        # Execute
        health = await enrichment_service.health_check()
        
        # Verify
        assert health["status"] == "healthy"
        assert health["service"] == "product-enrichment"
        assert "components" in health
        assert health["components"]["database"]["status"] == "healthy"
        assert health["components"]["firecrawl_api"]["status"] == "healthy"


class TestProductEnrichmentServiceSingleton:
    """Test singleton pattern for enrichment service."""
    
    @pytest.fixture(autouse=True)
    def mock_environment_variables(self, monkeypatch):
        """Mock required environment variables for testing."""
        monkeypatch.setenv("FIRECRAWL_API_KEY", "test-api-key")
        monkeypatch.setenv("FIRECRAWL_BASE_URL", "https://api.firecrawl.dev")
        monkeypatch.setenv("FIRECRAWL_TIMEOUT", "30")
        monkeypatch.setenv("FIRECRAWL_MAX_RETRIES", "3")
        monkeypatch.setenv("FIRECRAWL_RETRY_DELAY", "2")
    
    def test_get_product_enrichment_service_singleton(self):
        """Test that get_product_enrichment_service returns same instance."""
        service1 = get_product_enrichment_service()
        service2 = get_product_enrichment_service()
        assert service1 is service2
    
    def test_reset_product_enrichment_service(self):
        """Test resetting the singleton instance."""
        from app.services.product_enrichment import reset_product_enrichment_service
        
        service1 = get_product_enrichment_service()
        reset_product_enrichment_service()
        service2 = get_product_enrichment_service()
        assert service1 is not service2


class TestEnrichmentResultProperties:
    """Test EnrichmentResult calculated properties."""
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        result = EnrichmentResult(
            batch_id=uuid4(),
            total_products=10,
            successful_enrichments=8,
            failed_enrichments=2,
            results=[]
        )
        assert result.success_rate == 80.0
    
    def test_failure_rate_calculation(self):
        """Test failure rate calculation."""
        result = EnrichmentResult(
            batch_id=uuid4(),
            total_products=10,
            successful_enrichments=7,
            failed_enrichments=3,
            results=[]
        )
        assert result.failure_rate == 30.0
    
    def test_rates_with_zero_products(self):
        """Test rate calculations with zero products."""
        result = EnrichmentResult(
            batch_id=uuid4(),
            total_products=0,
            successful_enrichments=0,
            failed_enrichments=0,
            results=[]
        )
        assert result.success_rate == 0.0
        assert result.failure_rate == 0.0
