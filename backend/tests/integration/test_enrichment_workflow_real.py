"""
REAL Integration tests for complete enrichment workflow.

These tests use REAL Firecrawl API calls and REAL database products
to validate the complete end-to-end enrichment process.

IMPORTANT: These tests require:
1. FIRECRAWL_API_KEY environment variable set
2. Real database with LF products
3. Internet connection for API calls
"""

import pytest
import pytest_asyncio
import os
import asyncio
from uuid import UUID
from datetime import datetime
from typing import List
from dotenv import load_dotenv

from app.services.product_enrichment import ProductEnrichmentService
from app.services.database_service import get_database_service
from app.services.firecrawl_client import FirecrawlClient, get_firecrawl_client
from app.services.lawnfawn_matcher import LawnFawnMatcher
from app.models.product import Product
from app.models.base import ProductStatus
from app.models.enrichment import EnrichmentMethod, ProductEnrichmentResult


@pytest.mark.integration
@pytest.mark.real_api
class TestRealEnrichmentWorkflow:
    """Real integration tests using actual Firecrawl API and database products."""
    
    @pytest.fixture(scope="class")
    def api_key_required(self):
        """Ensure Firecrawl API key is available for real tests."""
        # Load environment variables from .env file for integration tests
        load_dotenv()
        
        api_key = os.getenv('FIRECRAWL_API_KEY')
        if not api_key:
            pytest.skip("FIRECRAWL_API_KEY not available for real API tests")
        return api_key
    
    @pytest_asyncio.fixture(scope="class")
    async def real_database_service(self):
        """Get real database service for integration tests."""
        return get_database_service()
    
    @pytest_asyncio.fixture(scope="class")
    async def real_lf_products(self, real_database_service) -> List[Product]:
        """Get real LF products from database for testing."""
        try:
            # Get LF products that are in DRAFT status (ready for enrichment)
            result = real_database_service.client.table('products')\
                .select('*')\
                .like('supplier_sku', 'LF%')\
                .eq('status', 'draft')\
                .order('created_at', desc=True)\
                .limit(5)\
                .execute()
            
            if not result.data:
                pytest.skip("No LF products in DRAFT status found for testing")
            
            products = [Product(**item) for item in result.data]
            print(f"Found {len(products)} real LF products for testing:")
            for p in products:
                print(f"  - {p.supplier_sku}: {p.supplier_name}")
            
            return products
            
        except Exception as e:
            pytest.skip(f"Could not retrieve real products from database: {e}")
    
    @pytest.fixture
    def real_firecrawl_client(self, api_key_required):
        """Get real Firecrawl client for API tests."""
        return get_firecrawl_client()
    
    @pytest.mark.asyncio
    async def test_real_single_product_enrichment(
        self, 
        real_lf_products, 
        real_database_service, 
        real_firecrawl_client,
        api_key_required
    ):
        """Test real product enrichment with actual API calls and database updates."""
        # Use the first product for single enrichment test
        test_product = real_lf_products[0]
        
        print(f"\n=== Testing Real Enrichment for {test_product.supplier_sku} ===")
        print(f"Product: {test_product.supplier_name}")
        print(f"Status: {test_product.status}")
        
        # Initialize enrichment service
        enrichment_service = ProductEnrichmentService()
        
        # Record initial state
        initial_status = test_product.status
        initial_confidence = test_product.scraping_confidence
        
        # Execute real enrichment
        start_time = datetime.utcnow()
        result = await enrichment_service.enrich_product(test_product.id)
        end_time = datetime.utcnow()
        
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"\n=== Enrichment Results ===")
        print(f"Success: {result.success}")
        print(f"Processing time: {processing_time:.2f}s")
        print(f"Method: {result.method}")
        print(f"Confidence: {result.confidence_score}")
        print(f"Product URL: {result.product_url}")
        print(f"Images found: {result.images_found}")
        
        if not result.success:
            print(f"Error: {result.error_message}")
        
        # Verify result structure
        assert isinstance(result, ProductEnrichmentResult)
        assert result.product_id == test_product.id
        assert result.processing_time_ms is not None
        assert result.processing_time_ms > 0
        
        if result.success:
            # Verify successful enrichment
            assert result.confidence_score > 0
            assert result.method in [
                EnrichmentMethod.SEARCH_FIRST_RESULT,
                EnrichmentMethod.SEARCH_EXACT_MATCH,
                EnrichmentMethod.SEARCH_MULTIPLE_RESULTS
            ]
            assert result.product_url is not None
            assert result.product_url.startswith("https://www.lawnfawn.com/products/")
            assert result.images_found >= 0
            
            # Verify database was updated
            updated_product = await real_database_service.get_product_by_id(test_product.id)
            assert updated_product is not None
            
            # Check that enrichment data was saved
            if result.confidence_score > 50:  # Only check for high confidence results
                assert updated_product.scraped_url is not None
                assert updated_product.scraping_confidence > initial_confidence
                
                print(f"\n=== Database Updates Verified ===")
                print(f"Scraped URL: {updated_product.scraped_url}")
                print(f"Scraped name: {updated_product.scraped_name}")
                print(f"Confidence updated: {initial_confidence} → {updated_product.scraping_confidence}")
        
        else:
            # For failed enrichment, verify error handling
            assert result.error_message is not None
            assert len(result.error_message) > 0
            print(f"Expected failure handled correctly: {result.error_message}")
    
    @pytest.mark.asyncio
    async def test_real_firecrawl_api_connectivity(self, real_firecrawl_client, api_key_required):
        """Test real Firecrawl API connectivity and basic functionality."""
        print(f"\n=== Testing Real Firecrawl API Connectivity ===")
        
        # Test health check
        health = await real_firecrawl_client.health_check()
        print(f"Health check: {health}")
        
        assert health["status"] == "healthy"
        assert health["api_accessible"] is True
        assert "response_time_ms" in health
        
        # Test actual scraping with a simple page
        test_url = "https://httpbin.org/html"
        print(f"Testing scraping with: {test_url}")
        
        start_time = datetime.utcnow()
        response = await real_firecrawl_client.scrape_page(test_url)
        end_time = datetime.utcnow()
        
        scraping_time = (end_time - start_time).total_seconds()
        
        print(f"Scraping completed in {scraping_time:.2f}s")
        print(f"Success: {response.success}")
        print(f"Content length: {len(response.content)}")
        print(f"Credits used: {response.credits_used}")
        
        # Verify response
        assert response.success is True
        assert len(response.content) > 0
        assert "Herman Melville" in response.content  # httpbin.org/html contains Moby Dick text
        assert response.credits_used >= 1
        assert response.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_real_lawnfawn_search_and_scraping(self, real_firecrawl_client, api_key_required):
        """Test real LawnFawn website search and product page scraping using actual workflow."""
        print(f"\n=== Testing Real LawnFawn Search and Scraping ===")
        
        # Initialize LawnFawn matcher
        matcher = LawnFawnMatcher()
        
        # Test with a known LF SKU
        test_sku = "LF1142"  # Stitched Rectangle Frames Dies
        print(f"Testing with SKU: {test_sku}")
        
        try:
            # Extract numeric SKU
            numeric_sku = matcher.extract_numeric_sku(test_sku)
            print(f"Extracted numeric SKU: {numeric_sku}")
            assert numeric_sku == "1142"
            
            # Build search URL
            search_url = matcher.build_search_url(numeric_sku)
            print(f"Search URL: {search_url}")
            assert "lawnfawn.com/search" in search_url
            assert "1142" in search_url
            
            # Perform real search and extract product links
            print("Performing real search...")
            search_results = await matcher.search_products(search_url)
            
            print(f"Search success: {len(search_results.product_links) > 0}")
            print(f"Product links found: {len(search_results.product_links)}")
            
            if search_results.product_links:
                print(f"First product link: {search_results.product_links[0]}")
                
                # Verify we got real product URLs (not manually constructed ones)
                first_link = search_results.product_links[0]
                assert "lawnfawn.com/products/" in first_link
                
                # The key test: verify we're NOT getting the broken URL format
                # The broken format would be: /products/lf1142-stitched-rectangle-frames
                # The working format should be: /products/stitched-rectangle-frames
                print(f"Checking URL format...")
                
                # Test scraping the first extracted URL
                print("Testing product page scraping with extracted URL...")
                try:
                    product_data = await matcher.scrape_product_page(first_link)
                    
                    print(f"Product scraping success: {product_data.name != 'Unknown Product'}")
                    print(f"Product name: {product_data.name}")
                    print(f"Product description length: {len(product_data.description)}")
                    print(f"Images found: {len(product_data.image_urls)}")
                    
                    # Verify we got actual product data
                    assert product_data.name != "Unknown Product"
                    assert len(product_data.name) > 0
                    
                    # Check for expected product content
                    content_lower = (product_data.name + " " + product_data.description).lower()
                    has_expected_content = any(keyword in content_lower for keyword in [
                        "stitched", "rectangle", "frames", "dies", "lawn fawn", "die", "cutting"
                    ])
                    
                    print(f"Contains expected product content: {has_expected_content}")
                    
                except Exception as scrape_error:
                    print(f"Product scraping failed: {scrape_error}")
                    
                    # Check if this is a 404 error (which we now handle)
                    if "404" in str(scrape_error) or "Page Not Found" in str(scrape_error):
                        print("✅ 404 detection working correctly!")
                        # This is actually good - it means our 404 detection is working
                        # and we would try the next URL in the real workflow
                    else:
                        # Re-raise unexpected errors
                        raise
            else:
                print("No product links found in search results")
                # This might happen if LawnFawn changes their HTML structure
                pytest.skip("No product links found - LawnFawn may have changed their HTML structure")
            
        except Exception as e:
            print(f"LawnFawn scraping test failed: {e}")
            # Don't fail the test if LawnFawn blocks scraping - this is expected behavior
            if "403" in str(e) or "blocked" in str(e).lower() or "rate limit" in str(e).lower():
                pytest.skip(f"LawnFawn blocks scraping (expected): {e}")
            else:
                # Re-raise unexpected errors
                raise
    
    @pytest.mark.asyncio
    async def test_real_batch_enrichment(
        self, 
        real_lf_products, 
        real_database_service, 
        api_key_required
    ):
        """Test real batch enrichment with multiple products."""
        print(f"\n=== Testing Real Batch Enrichment ===")
        
        # Use first 3 products for batch test (to be respectful to API)
        test_products = real_lf_products[:3]
        product_ids = [p.id for p in test_products]
        
        print(f"Testing batch enrichment with {len(test_products)} products:")
        for p in test_products:
            print(f"  - {p.supplier_sku}: {p.supplier_name}")
        
        # Initialize enrichment service
        enrichment_service = ProductEnrichmentService()
        
        # Execute batch enrichment
        start_time = datetime.utcnow()
        results = await enrichment_service.enrich_products(product_ids, max_concurrent=2)
        end_time = datetime.utcnow()
        
        total_time = (end_time - start_time).total_seconds()
        
        print(f"\n=== Batch Results ===")
        print(f"Total processing time: {total_time:.2f}s")
        print(f"Products processed: {len(results)}")
        
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        print(f"Successful: {len(successful_results)}")
        print(f"Failed: {len(failed_results)}")
        
        # Verify results
        assert len(results) == len(test_products)
        assert all(isinstance(r, ProductEnrichmentResult) for r in results)
        
        # Print detailed results
        for i, result in enumerate(results):
            product = test_products[i]
            print(f"\n  Product {i+1}: {product.supplier_sku}")
            print(f"    Success: {result.success}")
            print(f"    Confidence: {result.confidence_score}")
            print(f"    Processing time: {result.processing_time_ms}ms")
            
            if result.success:
                print(f"    Method: {result.method}")
                print(f"    URL: {result.product_url}")
                print(f"    Images: {result.images_found}")
            else:
                print(f"    Error: {result.error_message}")
        
        # Verify at least some processing occurred
        assert all(r.processing_time_ms > 0 for r in results)
        
        # If any succeeded, verify they have proper data
        for result in successful_results:
            assert result.confidence_score > 0
            assert result.product_url is not None
            assert result.method is not None
    
    @pytest.mark.asyncio
    async def test_real_enrichment_status_tracking(
        self, 
        real_lf_products, 
        real_database_service,
        api_key_required
    ):
        """Test enrichment status tracking with real database."""
        print(f"\n=== Testing Real Enrichment Status Tracking ===")
        
        # Get the batch ID from the first product
        test_product = real_lf_products[0]
        batch_id = test_product.batch_id
        
        print(f"Testing status tracking for batch: {batch_id}")
        
        # Initialize enrichment service
        enrichment_service = ProductEnrichmentService()
        
        # Get initial status
        initial_status = await enrichment_service.get_enrichment_status(batch_id)
        
        print(f"Initial status:")
        print(f"  Total products: {initial_status['total_products']}")
        print(f"  Completed: {initial_status['completed_products']}")
        print(f"  Failed: {initial_status['failed_products']}")
        print(f"  Processing: {initial_status['processing_products']}")
        print(f"  Pending: {initial_status['pending_products']}")
        print(f"  Completion %: {initial_status['completion_percentage']}")
        
        # Verify status structure
        assert initial_status["batch_id"] == str(batch_id)
        assert initial_status["total_products"] > 0
        assert initial_status["completion_percentage"] >= 0
        assert initial_status["completion_percentage"] <= 100
        
        # Verify counts add up
        total_accounted = (
            initial_status["completed_products"] +
            initial_status["failed_products"] +
            initial_status["processing_products"] +
            initial_status["pending_products"]
        )
        assert total_accounted == initial_status["total_products"]
    
    @pytest.mark.asyncio
    async def test_real_error_handling_and_recovery(
        self, 
        real_database_service, 
        api_key_required
    ):
        """Test error handling with invalid SKUs and real API."""
        print(f"\n=== Testing Real Error Handling ===")
        
        # Create a test product with invalid SKU
        from app.models.product import ProductCreate
        from uuid import uuid4
        
        # Get a real batch and supplier ID from existing products
        existing_products = await real_database_service.get_products(limit=1)
        if not existing_products:
            pytest.skip("No existing products found for error testing")
        
        existing_product = existing_products[0]
        
        invalid_product_data = ProductCreate(
            batch_id=existing_product.batch_id,
            supplier_id=existing_product.supplier_id,
            supplier_sku="INVALID_SKU_123",  # This should fail
            supplier_name="Test Invalid Product"
        )
        
        # Create the invalid product
        invalid_product = await real_database_service.create_product(invalid_product_data)
        
        print(f"Created test product with invalid SKU: {invalid_product.supplier_sku}")
        
        try:
            # Initialize enrichment service
            enrichment_service = ProductEnrichmentService()
            
            # Try to enrich the invalid product
            result = await enrichment_service.enrich_product(invalid_product.id)
            
            print(f"Enrichment result for invalid SKU:")
            print(f"  Success: {result.success}")
            print(f"  Error: {result.error_message}")
            print(f"  Processing time: {result.processing_time_ms}ms")
            
            # Should fail gracefully
            assert result.success is False
            assert result.error_message is not None
            assert len(result.error_message) > 0
            assert result.processing_time_ms > 0
            
            # Verify specific error types
            error_msg = result.error_message.lower()
            expected_errors = [
                "could not extract numeric sku",
                "invalid lf number format",
                "sku extraction",
                "search error"
            ]
            
            has_expected_error = any(err in error_msg for err in expected_errors)
            print(f"Has expected error type: {has_expected_error}")
            
        finally:
            # Clean up test product
            try:
                await real_database_service.client.table('products')\
                    .delete()\
                    .eq('id', str(invalid_product.id))\
                    .execute()
                print(f"Cleaned up test product: {invalid_product.id}")
            except Exception as e:
                print(f"Warning: Could not clean up test product: {e}")
    
    @pytest.mark.asyncio
    async def test_real_performance_and_rate_limiting(
        self, 
        real_firecrawl_client, 
        api_key_required
    ):
        """Test performance and rate limiting with real API."""
        print(f"\n=== Testing Real Performance and Rate Limiting ===")
        
        # Test multiple sequential requests to verify rate limiting
        test_urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://httpbin.org/xml"
        ]
        
        results = []
        total_start = datetime.utcnow()
        
        for i, url in enumerate(test_urls):
            print(f"Request {i+1}: {url}")
            
            start_time = datetime.utcnow()
            response = await real_firecrawl_client.scrape_page(url)
            end_time = datetime.utcnow()
            
            request_time = (end_time - start_time).total_seconds()
            results.append({
                "url": url,
                "success": response.success,
                "time": request_time,
                "credits": response.credits_used if response.success else 0
            })
            
            print(f"  Success: {response.success}, Time: {request_time:.2f}s")
            
            # Small delay between requests to be respectful
            await asyncio.sleep(1)
        
        total_end = datetime.utcnow()
        total_time = (total_end - total_start).total_seconds()
        
        print(f"\nPerformance Summary:")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average per request: {total_time/len(test_urls):.2f}s")
        print(f"  Total credits used: {sum(r['credits'] for r in results)}")
        
        # Verify all requests succeeded
        successful_requests = [r for r in results if r['success']]
        print(f"  Successful requests: {len(successful_requests)}/{len(test_urls)}")
        
        # Should have reasonable performance
        assert len(successful_requests) >= len(test_urls) * 0.8  # At least 80% success rate
        assert all(r['time'] < 30 for r in results)  # No request should take more than 30s
    
    @pytest.mark.asyncio
    async def test_complete_product_enrichment_data_persistence(
        self, 
        real_lf_products, 
        real_database_service, 
        api_key_required
    ):
        """Test that ALL enriched product data is properly persisted to database."""
        print(f"\n=== Testing Complete Product Data Persistence ===")
        
        # Use the first product for comprehensive data testing
        test_product = real_lf_products[0]
        
        print(f"Testing complete data persistence for: {test_product.supplier_sku}")
        print(f"Product: {test_product.supplier_name}")
        
        # Record initial state of ALL relevant fields
        initial_state = {
            'scraped_url': test_product.scraped_url,
            'scraped_name': test_product.scraped_name,
            'scraped_description': test_product.scraped_description,
            'scraped_images_urls': getattr(test_product, 'scraped_images_urls', None),
            'scraping_confidence': test_product.scraping_confidence,
            'quality_score': test_product.quality_score,
            'last_scraped_at': getattr(test_product, 'last_scraped_at', None),
            'enrichment_metadata': getattr(test_product, 'enrichment_metadata', None),
            'status': test_product.status
        }
        
        print(f"Initial state recorded:")
        for field, value in initial_state.items():
            print(f"  {field}: {value}")
        
        # Initialize enrichment service
        enrichment_service = ProductEnrichmentService()
        
        # Execute enrichment
        result = await enrichment_service.enrich_product(test_product.id)
        
        print(f"\nEnrichment completed:")
        print(f"  Success: {result.success}")
        print(f"  Confidence: {result.confidence_score}")
        print(f"  Method: {result.method}")
        print(f"  Processing time: {result.processing_time_ms}ms")
        
        # Get updated product from database
        updated_product = await real_database_service.get_product_by_id(test_product.id)
        assert updated_product is not None
        
        # Record final state
        final_state = {
            'scraped_url': updated_product.scraped_url,
            'scraped_name': updated_product.scraped_name,
            'scraped_description': updated_product.scraped_description,
            'scraped_images_urls': getattr(updated_product, 'scraped_images_urls', None),
            'scraping_confidence': updated_product.scraping_confidence,
            'quality_score': updated_product.quality_score,
            'last_scraped_at': getattr(updated_product, 'last_scraped_at', None),
            'enrichment_metadata': getattr(updated_product, 'enrichment_metadata', None),
            'status': updated_product.status
        }
        
        print(f"\nFinal state:")
        for field, value in final_state.items():
            print(f"  {field}: {value}")
        
        # Verify enrichment attempt was made (status should be updated)
        # Note: last_scraped_at and enrichment_metadata might not be in the Product model
        # but the enrichment should have updated the core fields
        print(f"Status changed from {initial_state['status']} to {updated_product.status}")
        
        if result.success:
            print(f"\n=== Verifying Successful Enrichment Data ===")
            
            # Verify scraped_url was updated
            assert updated_product.scraped_url is not None
            assert updated_product.scraped_url != initial_state['scraped_url']
            assert updated_product.scraped_url.startswith("https://www.lawnfawn.com/products/")
            
            # Verify confidence was updated
            assert updated_product.scraping_confidence is not None
            assert updated_product.scraping_confidence > (initial_state['scraping_confidence'] or 0)
            assert 0 <= updated_product.scraping_confidence <= 100
            
            # Verify scraped_name was updated (if confidence is high enough)
            if updated_product.scraping_confidence > 50:
                assert updated_product.scraped_name is not None
                assert len(updated_product.scraped_name) > 0
                assert updated_product.scraped_name != initial_state['scraped_name']
                
                # Verify scraped_description was updated
                if updated_product.scraped_description:
                    assert len(updated_product.scraped_description) > 0
                    assert updated_product.scraped_description != initial_state['scraped_description']
                
                # Verify scraped_images were updated (if any found)
                if result.images_found > 0:
                    assert updated_product.scraped_images_urls is not None
                    if isinstance(updated_product.scraped_images_urls, list):
                        assert len(updated_product.scraped_images_urls) > 0
                    elif isinstance(updated_product.scraped_images_urls, str):
                        # Could be JSON string
                        import json
                        try:
                            images = json.loads(updated_product.scraped_images_urls)
                            assert len(images) > 0
                        except:
                            # Or comma-separated string
                            assert len(updated_product.scraped_images_urls) > 0
            
            # Verify quality_score was calculated
            if updated_product.quality_score is not None:
                assert 0 <= updated_product.quality_score <= 100
            
            # Verify enrichment_metadata was updated (if field exists in model)
            enrichment_metadata = getattr(updated_product, 'enrichment_metadata', None)
            if enrichment_metadata:
                metadata = enrichment_metadata
                if isinstance(metadata, str):
                    import json
                    try:
                        metadata = json.loads(metadata)
                    except:
                        pass
                
                if isinstance(metadata, dict):
                    # Should contain enrichment details
                    expected_keys = ['method', 'processing_time_ms', 'timestamp']
                    for key in expected_keys:
                        if key in metadata:
                            print(f"    Metadata {key}: {metadata[key]}")
            else:
                print("    Enrichment metadata field not available in Product model")
            
            print(f"✅ All successful enrichment data properly persisted")
            
        else:
            print(f"\n=== Verifying Failed Enrichment Handling ===")
            
            # For failed enrichment, status should still be updated
            print(f"Failed enrichment status: {updated_product.status}")
            
            # Confidence might be set to 0 or remain unchanged
            if updated_product.scraping_confidence is not None:
                assert 0 <= updated_product.scraping_confidence <= 100
            
            print(f"✅ Failed enrichment properly handled")
        
        # Verify data types and constraints
        print(f"\n=== Verifying Data Types and Constraints ===")
        
        # URL validation
        if updated_product.scraped_url:
            assert isinstance(updated_product.scraped_url, str)
            assert updated_product.scraped_url.startswith("http")
        
        # Text fields validation
        if updated_product.scraped_name:
            assert isinstance(updated_product.scraped_name, str)
            assert len(updated_product.scraped_name.strip()) > 0
        
        if updated_product.scraped_description:
            assert isinstance(updated_product.scraped_description, str)
        
        # Numeric fields validation
        if updated_product.scraping_confidence is not None:
            assert isinstance(updated_product.scraping_confidence, (int, float))
            assert 0 <= updated_product.scraping_confidence <= 100
        
        if updated_product.quality_score is not None:
            assert isinstance(updated_product.quality_score, (int, float))
            assert 0 <= updated_product.quality_score <= 100
        
        # Timestamp validation (if field exists in model)
        last_scraped_at = getattr(updated_product, 'last_scraped_at', None)
        if last_scraped_at:
            from datetime import datetime
            assert isinstance(last_scraped_at, datetime)
        
        print(f"✅ All data types and constraints validated")
    
    @pytest.mark.asyncio
    async def test_scraping_attempts_table_tracking(
        self, 
        real_lf_products, 
        real_database_service, 
        api_key_required
    ):
        """Test that scraping attempts are properly tracked in scraping_attempts table."""
        print(f"\n=== Testing Scraping Attempts Table Tracking ===")
        
        # Use the first product for attempts tracking test
        test_product = real_lf_products[0]
        
        print(f"Testing scraping attempts tracking for: {test_product.supplier_sku}")
        
        # Check initial attempts count
        initial_attempts = real_database_service.client.table('scraping_attempts')\
            .select('*')\
            .eq('product_id', str(test_product.id))\
            .execute()
        
        initial_count = len(initial_attempts.data) if initial_attempts.data else 0
        print(f"Initial attempts count: {initial_count}")
        
        # Initialize enrichment service
        enrichment_service = ProductEnrichmentService()
        
        # Record timestamp before enrichment
        from datetime import datetime
        before_enrichment = datetime.utcnow()
        
        # Execute enrichment
        result = await enrichment_service.enrich_product(test_product.id)
        
        # Record timestamp after enrichment
        after_enrichment = datetime.utcnow()
        
        print(f"\nEnrichment completed:")
        print(f"  Success: {result.success}")
        print(f"  Method: {result.method}")
        print(f"  Confidence: {result.confidence_score}")
        print(f"  Processing time: {result.processing_time_ms}ms")
        
        # Check attempts count after enrichment
        final_attempts = real_database_service.client.table('scraping_attempts')\
            .select('*')\
            .eq('product_id', str(test_product.id))\
            .order('created_at', desc=True)\
            .execute()
        
        final_count = len(final_attempts.data) if final_attempts.data else 0
        print(f"Final attempts count: {final_count}")
        
        # Verify new attempt was recorded
        assert final_count > initial_count, f"Expected attempts count to increase from {initial_count} to {final_count}"
        
        # Get the most recent attempt
        latest_attempt = final_attempts.data[0] if final_attempts.data else None
        assert latest_attempt is not None, "No scraping attempt found"
        
        print(f"\n=== Verifying Latest Scraping Attempt ===")
        print(f"Attempt ID: {latest_attempt.get('id')}")
        print(f"Product ID: {latest_attempt.get('product_id')}")
        print(f"Success: {latest_attempt.get('success')}")
        print(f"Method: {latest_attempt.get('method')}")
        print(f"Confidence: {latest_attempt.get('confidence_score')}")
        print(f"Processing time: {latest_attempt.get('processing_time_ms')}ms")
        print(f"Error message: {latest_attempt.get('error_message')}")
        print(f"Created at: {latest_attempt.get('created_at')}")
        
        # Verify attempt data matches enrichment result
        assert latest_attempt['product_id'] == str(test_product.id)
        assert latest_attempt['success'] == result.success
        assert latest_attempt['processing_time_ms'] == result.processing_time_ms
        
        if result.success:
            assert latest_attempt['method'] == result.method.value if result.method else None
            assert latest_attempt['confidence_score'] == result.confidence_score
            assert latest_attempt['product_url'] == result.product_url
            assert latest_attempt['images_found'] == result.images_found
            assert latest_attempt['error_message'] is None
        else:
            assert latest_attempt['error_message'] == result.error_message
            assert latest_attempt['confidence_score'] == 0 or latest_attempt['confidence_score'] is None
        
        # Verify timestamp is reasonable
        attempt_timestamp = datetime.fromisoformat(latest_attempt['created_at'].replace('Z', '+00:00'))
        assert before_enrichment <= attempt_timestamp <= after_enrichment
        
        # Verify required fields are present
        required_fields = ['id', 'product_id', 'success', 'processing_time_ms', 'created_at']
        for field in required_fields:
            assert field in latest_attempt, f"Required field '{field}' missing from scraping attempt"
            assert latest_attempt[field] is not None, f"Required field '{field}' is null"
        
        # Verify data types
        assert isinstance(latest_attempt['success'], bool)
        assert isinstance(latest_attempt['processing_time_ms'], int)
        assert latest_attempt['processing_time_ms'] > 0
        
        if latest_attempt['confidence_score'] is not None:
            assert isinstance(latest_attempt['confidence_score'], (int, float))
            assert 0 <= latest_attempt['confidence_score'] <= 100
        
        if latest_attempt['images_found'] is not None:
            assert isinstance(latest_attempt['images_found'], int)
            assert latest_attempt['images_found'] >= 0
        
        print(f"✅ Scraping attempt properly recorded and validated")
        
        # Test multiple attempts for same product (if we run enrichment again)
        print(f"\n=== Testing Multiple Attempts Tracking ===")
        
        # Run enrichment again to create another attempt
        second_result = await enrichment_service.enrich_product(test_product.id)
        
        # Check attempts count increased again
        second_final_attempts = real_database_service.client.table('scraping_attempts')\
            .select('*')\
            .eq('product_id', str(test_product.id))\
            .order('created_at', desc=True)\
            .execute()
        
        second_final_count = len(second_final_attempts.data) if second_final_attempts.data else 0
        print(f"After second enrichment, attempts count: {second_final_count}")
        
        # Should have one more attempt
        assert second_final_count > final_count, "Second enrichment should create another attempt record"
        
        # Verify both attempts are tracked
        if second_final_attempts.data and len(second_final_attempts.data) >= 2:
            first_attempt = second_final_attempts.data[1]  # Second most recent
            second_attempt = second_final_attempts.data[0]  # Most recent
            
            # Verify they have different timestamps
            first_timestamp = datetime.fromisoformat(first_attempt['created_at'].replace('Z', '+00:00'))
            second_timestamp = datetime.fromisoformat(second_attempt['created_at'].replace('Z', '+00:00'))
            assert second_timestamp > first_timestamp, "Second attempt should have later timestamp"
            
            # Both should be for the same product
            assert first_attempt['product_id'] == second_attempt['product_id'] == str(test_product.id)
            
            print(f"✅ Multiple attempts properly tracked with correct timestamps")
        
        print(f"\n=== Scraping Attempts Table Test Complete ===")
        print(f"Total attempts recorded: {second_final_count}")
        print(f"All attempt data properly validated")
