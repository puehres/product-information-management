"""
Integration tests for complete enrichment workflow.

Tests the end-to-end enrichment process from DRAFT products to ENRICHED status,
including API endpoints, database operations, and service orchestration.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4
from datetime import datetime
import asyncio

from app.services.product_enrichment import ProductEnrichmentService
from app.services.lawnfawn_matcher import LawnFawnMatcher
from app.services.firecrawl_client import FirecrawlClient
from app.models.product import Product
from app.models.base import ProductStatus
from app.models.enrichment import (
    EnrichmentData, EnrichmentMethod, FirecrawlResponse, 
    ProductEnrichmentResult, EnrichmentResult
)
from app.exceptions.enrichment import SKUExtractionError, SearchError


class TestEnrichmentWorkflowIntegration:
    """Integration tests for complete enrichment workflow."""
    
    @pytest.fixture
    def mock_database_service(self):
        """Mock database service for integration tests."""
        mock_service = Mock()
        mock_service.get_product_by_id = AsyncMock()
        mock_service.get_products = AsyncMock()
        mock_service.update_product_status = AsyncMock()
        mock_service.update_product_enrichment = AsyncMock()
        mock_service.create_scraping_attempt = AsyncMock()
        mock_service.health_check = AsyncMock(return_value={"status": "healthy"})
        
        # Mock Supabase client responses
        mock_service.client = Mock()
        mock_service.client.table.return_value.insert.return_value.execute.return_value.data = [
            {'id': str(uuid4()), 'attempt_number': 1, 'created_at': datetime.utcnow().isoformat()}
        ]
        mock_service.client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{}]
        
        return mock_service
    
    @pytest.fixture
    def mock_firecrawl_responses(self):
        """Mock Firecrawl API responses for testing."""
        search_response = FirecrawlResponse(
            url="https://www.lawnfawn.com/search?q=2538",
            content="""
            <html>
                <body>
                    <div class="search-results">
                        <a href="/products/lf2538-stitched-rectangle-frames">LF2538 Stitched Rectangle Frames Dies</a>
                        <a href="/products/lf2538-coordinating-stamps">LF2538 Coordinating Stamps</a>
                    </div>
                </body>
            </html>
            """,
            success=True,
            credits_used=1,
            processing_time_ms=800
        )
        
        product_response = FirecrawlResponse(
            url="https://www.lawnfawn.com/products/lf2538-stitched-rectangle-frames",
            content="""
            <html>
                <body>
                    <h1>Stitched Rectangle Frames Dies</h1>
                    <div class="product-description">
                        <p>Create beautiful stitched rectangle frames with this versatile die set. Perfect for cards, scrapbook layouts, and mixed media projects.</p>
                    </div>
                    <div class="product-images">
                        <img src="https://cdn.lawnfawn.com/images/lf2538-main.jpg" alt="Main product image">
                        <img src="https://cdn.lawnfawn.com/images/lf2538-detail.jpg" alt="Detail image">
                        <img src="https://cdn.lawnfawn.com/images/lf2538-example.jpg" alt="Example usage">
                    </div>
                    <div class="product-details">
                        <span class="sku">LF2538</span>
                        <span class="category">Lawn Cuts</span>
                    </div>
                </body>
            </html>
            """,
            success=True,
            credits_used=1,
            processing_time_ms=1200
        )
        
        return {
            "search": search_response,
            "product": product_response
        }
    
    @pytest.fixture
    def sample_products(self):
        """Sample products for batch testing."""
        batch_id = uuid4()
        return [
            Product(
                id=uuid4(),
                batch_id=batch_id,
                supplier_sku="LF2538",
                manufacturer="lawnfawn",
                supplier_price_usd=12.99,
                status=ProductStatus.DRAFT,
                product_name="Stitched Rectangle Frames Dies"
            ),
            Product(
                id=uuid4(),
                batch_id=batch_id,
                supplier_sku="LF1234",
                manufacturer="lawnfawn",
                supplier_price_usd=8.99,
                status=ProductStatus.DRAFT,
                product_name="Test Stamps"
            ),
            Product(
                id=uuid4(),
                batch_id=batch_id,
                supplier_sku="INVALID",  # This will fail
                manufacturer="lawnfawn",
                supplier_price_usd=5.99,
                status=ProductStatus.DRAFT,
                product_name="Invalid Product"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_complete_enrichment_workflow_success(self, mock_database_service, mock_firecrawl_responses):
        """Test complete successful enrichment workflow."""
        # Setup product
        product = Product(
            id=uuid4(),
            batch_id=uuid4(),
            supplier_sku="LF2538",
            manufacturer="lawnfawn",
            supplier_price_usd=12.99,
            status=ProductStatus.DRAFT
        )
        
        # Setup mocks
        mock_database_service.get_product_by_id.return_value = product
        
        with patch('app.services.product_enrichment.get_database_service', return_value=mock_database_service), \
             patch('app.services.firecrawl_client.httpx.AsyncClient') as mock_client_class:
            
            # Mock Firecrawl API calls
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # First call: search results
            search_mock_response = Mock()
            search_mock_response.status_code = 200
            search_mock_response.json.return_value = {
                "success": True,
                "data": {
                    "content": mock_firecrawl_responses["search"].content,
                    "metadata": {"title": "Search Results"}
                },
                "credits_used": 1
            }
            search_mock_response.raise_for_status = Mock()
            
            # Second call: product page
            product_mock_response = Mock()
            product_mock_response.status_code = 200
            product_mock_response.json.return_value = {
                "success": True,
                "data": {
                    "content": mock_firecrawl_responses["product"].content,
                    "metadata": {"title": "Product Page"}
                },
                "credits_used": 1
            }
            product_mock_response.raise_for_status = Mock()
            
            mock_client.post.side_effect = [search_mock_response, product_mock_response]
            
            # Execute enrichment
            enrichment_service = ProductEnrichmentService()
            result = await enrichment_service.enrich_product(product.id)
            
            # Verify result
            assert result.success is True
            assert result.product_id == product.id
            assert result.confidence_score == 100  # Exact SKU match
            assert result.method == EnrichmentMethod.SEARCH_FIRST_RESULT
            assert result.product_url == "https://www.lawnfawn.com/products/lf2538-stitched-rectangle-frames"
            assert result.images_found == 3
            assert result.processing_time_ms is not None
            
            # Verify database interactions
            mock_database_service.get_product_by_id.assert_called_once_with(product.id)
            mock_database_service.update_product_status.assert_called()
            mock_database_service.create_scraping_attempt.assert_called()
            mock_database_service.update_product_enrichment.assert_called()
    
    @pytest.mark.asyncio
    async def test_batch_enrichment_workflow(self, mock_database_service, mock_firecrawl_responses, sample_products):
        """Test batch enrichment with mixed success/failure results."""
        batch_id = sample_products[0].batch_id
        
        # Setup mocks
        mock_database_service.get_products.return_value = sample_products
        
        with patch('app.services.product_enrichment.get_database_service', return_value=mock_database_service), \
             patch('app.services.firecrawl_client.httpx.AsyncClient') as mock_client_class:
            
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock responses for successful products
            success_search_response = Mock()
            success_search_response.status_code = 200
            success_search_response.json.return_value = {
                "success": True,
                "data": {
                    "content": mock_firecrawl_responses["search"].content,
                    "metadata": {"title": "Search Results"}
                },
                "credits_used": 1
            }
            success_search_response.raise_for_status = Mock()
            
            success_product_response = Mock()
            success_product_response.status_code = 200
            success_product_response.json.return_value = {
                "success": True,
                "data": {
                    "content": mock_firecrawl_responses["product"].content,
                    "metadata": {"title": "Product Page"}
                },
                "credits_used": 1
            }
            success_product_response.raise_for_status = Mock()
            
            # Return successful responses for valid SKUs, will fail on invalid SKU before API calls
            mock_client.post.side_effect = [
                success_search_response, success_product_response,  # LF2538
                success_search_response, success_product_response   # LF1234
            ]
            
            # Execute batch enrichment
            enrichment_service = ProductEnrichmentService()
            result = await enrichment_service.enrich_batch(batch_id)
            
            # Verify batch result
            assert isinstance(result, EnrichmentResult)
            assert result.batch_id == batch_id
            assert result.total_products == 3
            assert result.successful_enrichments == 2  # LF2538 and LF1234 succeed
            assert result.failed_enrichments == 1      # INVALID fails
            assert len(result.results) == 3
            
            # Verify individual results
            successful_results = [r for r in result.results if r.success]
            failed_results = [r for r in result.results if not r.success]
            
            assert len(successful_results) == 2
            assert len(failed_results) == 1
            
            # Check failed result
            failed_result = failed_results[0]
            assert "Could not extract numeric SKU" in failed_result.error_message
            
            # Verify success rate calculation
            assert result.success_rate == 66.67  # 2/3 * 100, rounded to 2 decimals
            assert result.failure_rate == 33.33  # 1/3 * 100, rounded to 2 decimals
    
    @pytest.mark.asyncio
    async def test_concurrent_enrichment_processing(self, mock_database_service, mock_firecrawl_responses):
        """Test concurrent processing of multiple products."""
        # Create multiple products
        products = []
        for i in range(5):
            products.append(Product(
                id=uuid4(),
                batch_id=uuid4(),
                supplier_sku=f"LF{2538 + i}",
                manufacturer="lawnfawn",
                supplier_price_usd=12.99,
                status=ProductStatus.DRAFT
            ))
        
        product_ids = [p.id for p in products]
        
        # Setup mocks
        mock_database_service.get_product_by_id.side_effect = products
        
        with patch('app.services.product_enrichment.get_database_service', return_value=mock_database_service), \
             patch('app.services.firecrawl_client.httpx.AsyncClient') as mock_client_class:
            
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock successful responses for all products
            success_response = Mock()
            success_response.status_code = 200
            success_response.json.return_value = {
                "success": True,
                "data": {
                    "content": mock_firecrawl_responses["search"].content,
                    "metadata": {"title": "Search Results"}
                },
                "credits_used": 1
            }
            success_response.raise_for_status = Mock()
            
            # Return successful responses for all API calls
            mock_client.post.return_value = success_response
            
            # Execute concurrent enrichment
            enrichment_service = ProductEnrichmentService()
            start_time = datetime.utcnow()
            results = await enrichment_service.enrich_products(product_ids, max_concurrent=3)
            end_time = datetime.utcnow()
            
            # Verify results
            assert len(results) == 5
            assert all(r.success for r in results)
            
            # Verify concurrent processing (should be faster than sequential)
            processing_time = (end_time - start_time).total_seconds()
            assert processing_time < 10  # Should complete quickly with mocked responses
            
            # Verify all products were processed
            processed_product_ids = {r.product_id for r in results}
            expected_product_ids = set(product_ids)
            assert processed_product_ids == expected_product_ids
    
    @pytest.mark.asyncio
    async def test_enrichment_status_tracking(self, mock_database_service):
        """Test enrichment status tracking and reporting."""
        batch_id = uuid4()
        
        # Create products with different statuses
        products = [
            Product(id=uuid4(), batch_id=batch_id, status=ProductStatus.ENRICHED, scraping_confidence=95),
            Product(id=uuid4(), batch_id=batch_id, status=ProductStatus.ENRICHED, scraping_confidence=85),
            Product(id=uuid4(), batch_id=batch_id, status=ProductStatus.ENRICHMENT_FAILED),
            Product(id=uuid4(), batch_id=batch_id, status=ProductStatus.ENRICHING),
            Product(id=uuid4(), batch_id=batch_id, status=ProductStatus.DRAFT)
        ]
        
        mock_database_service.get_products.return_value = products
        
        with patch('app.services.product_enrichment.get_database_service', return_value=mock_database_service):
            enrichment_service = ProductEnrichmentService()
            status = await enrichment_service.get_enrichment_status(batch_id)
            
            # Verify status calculation
            assert status["batch_id"] == str(batch_id)
            assert status["total_products"] == 5
            assert status["completed_products"] == 2
            assert status["failed_products"] == 1
            assert status["processing_products"] == 1
            assert status["pending_products"] == 1
            assert status["avg_confidence_score"] == 90.0  # (95 + 85) / 2
            assert status["completion_percentage"] == 60.0  # (2 + 1) / 5 * 100
    
    @pytest.mark.asyncio
    async def test_error_recovery_and_retry(self, mock_database_service, mock_firecrawl_responses):
        """Test error recovery and retry mechanisms."""
        product = Product(
            id=uuid4(),
            batch_id=uuid4(),
            supplier_sku="LF2538",
            manufacturer="lawnfawn",
            status=ProductStatus.DRAFT
        )
        
        mock_database_service.get_product_by_id.return_value = product
        
        with patch('app.services.product_enrichment.get_database_service', return_value=mock_database_service), \
             patch('app.services.firecrawl_client.httpx.AsyncClient') as mock_client_class:
            
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # First call fails, second succeeds (simulating retry)
            failure_response = Mock()
            failure_response.status_code = 500
            failure_response.raise_for_status.side_effect = Exception("Server error")
            
            success_response = Mock()
            success_response.status_code = 200
            success_response.json.return_value = {
                "success": True,
                "data": {
                    "content": mock_firecrawl_responses["search"].content,
                    "metadata": {"title": "Search Results"}
                },
                "credits_used": 1
            }
            success_response.raise_for_status = Mock()
            
            # Simulate retry behavior
            mock_client.post.side_effect = [failure_response, success_response, success_response]
            
            # Execute with retry logic
            enrichment_service = ProductEnrichmentService()
            
            # This should eventually succeed after retry
            with patch('app.services.lawnfawn_matcher.LawnFawnMatcher.match_product') as mock_match:
                mock_match.side_effect = [
                    Exception("First attempt fails"),
                    EnrichmentData(
                        search_url="https://www.lawnfawn.com/search?q=2538",
                        product_url="https://www.lawnfawn.com/products/lf2538",
                        product_name="Test Product",
                        description="Test description",
                        image_urls=["https://example.com/image.jpg"],
                        confidence_score=90,
                        method=EnrichmentMethod.SEARCH_FIRST_RESULT,
                        raw_response={}
                    )
                ]
                
                # First attempt should fail
                result1 = await enrichment_service.enrich_product(product.id)
                assert result1.success is False
                
                # Second attempt should succeed (simulating retry)
                result2 = await enrichment_service.enrich_product(product.id)
                assert result2.success is True
    
    @pytest.mark.asyncio
    async def test_health_check_integration(self, mock_database_service):
        """Test health check integration across all services."""
        mock_database_service.health_check.return_value = {"status": "healthy"}
        
        with patch('app.services.product_enrichment.get_database_service', return_value=mock_database_service), \
             patch('app.services.firecrawl_client.httpx.AsyncClient') as mock_client_class:
            
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock healthy Firecrawl response
            health_response = Mock()
            health_response.status_code = 200
            health_response.json.return_value = {"status": "ok"}
            health_response.raise_for_status = Mock()
            mock_client.get.return_value = health_response
            
            enrichment_service = ProductEnrichmentService()
            health = await enrichment_service.health_check()
            
            # Verify overall health
            assert health["status"] == "healthy"
            assert health["service"] == "product-enrichment"
            assert "components" in health
            assert health["components"]["database"]["status"] == "healthy"
            assert health["components"]["firecrawl_api"]["status"] == "healthy"
            assert "response_time_ms" in health
    
    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self, mock_database_service, mock_firecrawl_responses):
        """Test collection of performance metrics during enrichment."""
        product = Product(
            id=uuid4(),
            batch_id=uuid4(),
            supplier_sku="LF2538",
            manufacturer="lawnfawn",
            status=ProductStatus.DRAFT
        )
        
        mock_database_service.get_product_by_id.return_value = product
        
        with patch('app.services.product_enrichment.get_database_service', return_value=mock_database_service), \
             patch('app.services.firecrawl_client.httpx.AsyncClient') as mock_client_class:
            
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock responses with timing
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "data": {
                    "content": mock_firecrawl_responses["search"].content,
                    "metadata": {"title": "Search Results"}
                },
                "credits_used": 1
            }
            mock_response.raise_for_status = Mock()
            mock_client.post.return_value = mock_response
            
            enrichment_service = ProductEnrichmentService()
            result = await enrichment_service.enrich_product(product.id)
            
            # Verify performance metrics are collected
            assert result.processing_time_ms is not None
            assert result.processing_time_ms > 0
            
            # Verify scraping attempt was recorded with metrics
            mock_database_service.create_scraping_attempt.assert_called()
            call_args = mock_database_service.create_scraping_attempt.call_args[1]
            assert "processing_time_ms" in call_args
            assert "credits_used" in call_args
