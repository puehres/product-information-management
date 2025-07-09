"""
Main product enrichment service.

This module orchestrates the complete product enrichment workflow, integrating
with the database service, LawnFawn matcher, and Firecrawl client to provide
comprehensive product enrichment capabilities.
"""

import asyncio
import time
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import structlog

from ..models.product import Product
from ..models.base import ProductStatus
from ..models.enrichment import (
    EnrichmentResult, ProductEnrichmentResult, EnrichmentData,
    ScrapingAttempt, EnrichmentMethod, ScrapingStatus,
    EnrichmentConfig
)
from ..exceptions.enrichment import (
    EnrichmentError, SKUExtractionError, SearchError, ScrapingError,
    DatabaseError, ConfigurationError
)
from ..services.database_service import get_database_service
from ..services.lawnfawn_matcher import get_lawnfawn_matcher
from ..services.firecrawl_client import get_firecrawl_client

logger = structlog.get_logger(__name__)


class ProductEnrichmentService:
    """
    Orchestrates the complete product enrichment workflow.
    
    Responsibilities:
    - Coordinate enrichment process for batches or individual products
    - Manage enrichment status and progress tracking
    - Handle errors and retry logic
    - Update product records with enriched data
    """
    
    def __init__(self, config: Optional[EnrichmentConfig] = None):
        """
        Initialize the product enrichment service.
        
        Args:
            config: Optional enrichment configuration
        """
        self.config = config
        self.database_service = get_database_service()
        self.lawnfawn_matcher = get_lawnfawn_matcher(config)
        self.firecrawl_client = get_firecrawl_client(config)
        
        # Concurrency control
        import os
        self.max_concurrent = int(os.getenv('ENRICHMENT_MAX_CONCURRENT', '5'))
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        
        logger.info(
            "Product enrichment service initialized",
            max_concurrent=self.max_concurrent
        )
    
    async def enrich_batch(self, batch_id: UUID, max_concurrent: Optional[int] = None) -> EnrichmentResult:
        """
        Enrich all products in a batch.
        
        Args:
            batch_id: Upload batch ID
            max_concurrent: Optional override for max concurrent enrichments
            
        Returns:
            EnrichmentResult: Summary of enrichment process
        """
        start_time = time.time()
        
        logger.info("Starting batch enrichment", batch_id=str(batch_id))
        
        try:
            # Get products that need enrichment
            products = await self._get_products_for_enrichment(batch_id)
            
            if not products:
                logger.info("No products found for enrichment", batch_id=str(batch_id))
                return EnrichmentResult(
                    batch_id=batch_id,
                    total_products=0,
                    successful_enrichments=0,
                    failed_enrichments=0,
                    results=[],
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
            
            # Update concurrency limit if provided
            if max_concurrent:
                self.semaphore = asyncio.Semaphore(max_concurrent)
            
            # Create enrichment tasks
            tasks = [
                self._enrich_product_with_semaphore(product.id)
                for product in products
            ]
            
            logger.info(
                "Starting concurrent enrichment",
                batch_id=str(batch_id),
                total_products=len(products),
                max_concurrent=max_concurrent or self.max_concurrent
            )
            
            # Execute with concurrency control
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            successful = 0
            failed = 0
            processed_results = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        "Product enrichment task failed with exception",
                        product_id=str(products[i].id),
                        error=str(result),
                        error_type=type(result).__name__
                    )
                    failed += 1
                    processed_results.append(ProductEnrichmentResult(
                        product_id=products[i].id,
                        success=False,
                        error_message=str(result)
                    ))
                elif result.success:
                    successful += 1
                    processed_results.append(result)
                else:
                    failed += 1
                    processed_results.append(result)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                "Batch enrichment completed",
                batch_id=str(batch_id),
                total_products=len(products),
                successful=successful,
                failed=failed,
                processing_time_ms=processing_time_ms
            )
            
            return EnrichmentResult(
                batch_id=batch_id,
                total_products=len(products),
                successful_enrichments=successful,
                failed_enrichments=failed,
                results=processed_results,
                processing_time_ms=processing_time_ms
            )
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "Batch enrichment failed",
                batch_id=str(batch_id),
                error=str(e),
                processing_time_ms=processing_time_ms
            )
            raise EnrichmentError(
                f"Batch enrichment failed: {str(e)}"
            )
    
    async def enrich_products(self, product_ids: List[UUID], max_concurrent: Optional[int] = None) -> List[ProductEnrichmentResult]:
        """
        Enrich specific products by ID.
        
        Args:
            product_ids: List of product IDs to enrich
            max_concurrent: Optional override for max concurrent enrichments
            
        Returns:
            List[ProductEnrichmentResult]: Individual enrichment results
        """
        logger.info("Starting product enrichment", product_count=len(product_ids))
        
        try:
            # Update concurrency limit if provided
            if max_concurrent:
                self.semaphore = asyncio.Semaphore(max_concurrent)
            
            # Create enrichment tasks
            tasks = [
                self._enrich_product_with_semaphore(product_id)
                for product_id in product_ids
            ]
            
            # Execute with concurrency control
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            processed_results = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        "Product enrichment task failed with exception",
                        product_id=str(product_ids[i]),
                        error=str(result)
                    )
                    processed_results.append(ProductEnrichmentResult(
                        product_id=product_ids[i],
                        success=False,
                        error_message=str(result)
                    ))
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error(
                "Product enrichment failed",
                product_ids=[str(pid) for pid in product_ids],
                error=str(e)
            )
            raise EnrichmentError(
                f"Product enrichment failed: {str(e)}"
            )
    
    async def _enrich_product_with_semaphore(self, product_id: UUID) -> ProductEnrichmentResult:
        """Enrich product with semaphore control."""
        async with self.semaphore:
            return await self.enrich_product(product_id)
    
    async def enrich_product(self, product_id: UUID) -> ProductEnrichmentResult:
        """
        Enrich a single product with web-scraped data.
        
        Args:
            product_id: Product ID to enrich
            
        Returns:
            ProductEnrichmentResult: Enrichment result with confidence score
        """
        start_time = time.time()
        
        logger.info("Starting product enrichment", product_id=str(product_id))
        
        try:
            # Get product from database
            product = await self.database_service.get_product_by_id(product_id)
            if not product:
                raise EnrichmentError(f"Product not found: {product_id}")
            
            if not product.supplier_sku or not product.supplier_sku.strip():
                raise EnrichmentError("No supplier SKU available for enrichment")
            
            # Update status to processing
            await self._update_product_status(
                product_id, 
                ProductStatus.PROCESSING,
                enrichment_status="processing"
            )
            
            # Perform enrichment based on manufacturer
            if product.manufacturer and product.manufacturer.lower() == "lawnfawn":
                enrichment_data = await self.lawnfawn_matcher.match_product(product)
            else:
                raise EnrichmentError(f"Unsupported manufacturer: {product.manufacturer}")
            
            # Store successful scraping attempt
            scraping_attempt = await self._create_scraping_attempt(
                product_id=product_id,
                search_url=enrichment_data.search_url,
                method=enrichment_data.method,
                status=ScrapingStatus.SUCCESS,
                confidence_score=enrichment_data.confidence_score,
                firecrawl_response=enrichment_data.raw_response,
                processing_time_ms=enrichment_data.processing_time_ms
            )
            
            # Update product with enriched data
            await self._update_product_enrichment(
                product_id=product_id,
                scraped_name=enrichment_data.product_name,
                scraped_description=enrichment_data.description,
                scraped_url=enrichment_data.product_url,
                scraped_images_urls=enrichment_data.image_urls,
                scraped_images_metadata=enrichment_data.image_metadata,
                scraping_confidence=enrichment_data.confidence_score,
                successful_scraping_attempt_id=scraping_attempt.id,
                status=ProductStatus.READY,
                enrichment_status="completed"
            )
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                "Product enrichment completed successfully",
                product_id=str(product_id),
                confidence_score=enrichment_data.confidence_score,
                images_found=len(enrichment_data.image_urls),
                processing_time_ms=processing_time_ms
            )
            
            return ProductEnrichmentResult(
                product_id=product_id,
                success=True,
                confidence_score=enrichment_data.confidence_score,
                method=enrichment_data.method,
                product_url=enrichment_data.product_url,
                images_found=len(enrichment_data.image_urls),
                processing_time_ms=processing_time_ms,
                scraping_attempt_id=scraping_attempt.id
            )
            
        except (SKUExtractionError, SearchError, ScrapingError) as e:
            # Handle specific enrichment errors
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Store failed attempt
            await self._create_scraping_attempt(
                product_id=product_id,
                search_url=getattr(e, 'search_url', None),
                method=getattr(e, 'method', None) or EnrichmentMethod.FALLBACK.value,
                status=ScrapingStatus.FAILED,
                confidence_score=0,
                error_message=str(e),
                processing_time_ms=processing_time_ms
            )
            
            # Update product status to failed
            await self._update_product_status(
                product_id, 
                ProductStatus.FAILED,
                enrichment_status="failed",
                processing_notes=str(e)
            )
            
            logger.error(
                "Product enrichment failed",
                product_id=str(product_id),
                error=str(e),
                error_type=type(e).__name__,
                processing_time_ms=processing_time_ms
            )
            
            return ProductEnrichmentResult(
                product_id=product_id,
                success=False,
                error_message=str(e),
                processing_time_ms=processing_time_ms
            )
            
        except Exception as e:
            # Handle unexpected errors
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Store failed attempt
            await self._create_scraping_attempt(
                product_id=product_id,
                method=EnrichmentMethod.FALLBACK.value,
                status=ScrapingStatus.FAILED,
                confidence_score=0,
                error_message=f"Unexpected error: {str(e)}",
                processing_time_ms=processing_time_ms
            )
            
            # Update product status to failed
            await self._update_product_status(
                product_id, 
                ProductStatus.FAILED,
                enrichment_status="failed",
                processing_notes=f"Unexpected error: {str(e)}"
            )
            
            logger.error(
                "Unexpected error during product enrichment",
                product_id=str(product_id),
                error=str(e),
                error_type=type(e).__name__,
                processing_time_ms=processing_time_ms
            )
            
            return ProductEnrichmentResult(
                product_id=product_id,
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                processing_time_ms=processing_time_ms
            )
    
    async def _get_products_for_enrichment(self, batch_id: UUID) -> List[Product]:
        """
        Get products that need enrichment from a batch.
        
        Args:
            batch_id: Batch ID
            
        Returns:
            List[Product]: Products that need enrichment
        """
        try:
            # Get all products in batch that are in DRAFT status
            products = await self.database_service.get_products(
                batch_id=batch_id,
                status=ProductStatus.DRAFT.value
            )
            
            # Filter for products with manufacturer_sku (required for enrichment)
            enrichable_products = [
                product for product in products 
                if product.supplier_sku and product.manufacturer
            ]
            
            logger.debug(
                "Found products for enrichment",
                batch_id=str(batch_id),
                total_products=len(products),
                enrichable_products=len(enrichable_products)
            )
            
            return enrichable_products
            
        except Exception as e:
            logger.error(
                "Error getting products for enrichment",
                batch_id=str(batch_id),
                error=str(e)
            )
            raise DatabaseError(
                f"Failed to get products for enrichment: {str(e)}",
                operation="select",
                table="products"
            )
    
    async def _create_scraping_attempt(
        self,
        product_id: UUID,
        method: str,
        status: ScrapingStatus,
        confidence_score: int = 0,
        search_url: Optional[str] = None,
        firecrawl_response: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        processing_time_ms: Optional[int] = None
    ) -> ScrapingAttempt:
        """
        Create a scraping attempt record.
        
        Args:
            product_id: Product ID
            method: Scraping method used
            status: Attempt status
            confidence_score: Confidence score achieved
            search_url: Search URL used
            firecrawl_response: Raw Firecrawl response
            error_message: Error message if failed
            processing_time_ms: Processing time in milliseconds
            
        Returns:
            ScrapingAttempt: Created scraping attempt record
        """
        try:
            # Create scraping attempt data
            attempt_data = {
                'product_id': str(product_id),
                'search_url': search_url,
                'method': method,
                'status': status.value,
                'confidence_score': confidence_score,
                'firecrawl_response': firecrawl_response,
                'error_message': error_message,
                'credits_used': 1,  # Default to 1 credit per attempt
                'processing_time_ms': processing_time_ms
            }
            
            # Insert into database
            result = self.database_service.client.table('scraping_attempts').insert(attempt_data).execute()
            
            if result.data:
                attempt_record = result.data[0]
                logger.debug(
                    "Scraping attempt created",
                    product_id=str(product_id),
                    attempt_id=attempt_record['id'],
                    status=status.value
                )
                
                return ScrapingAttempt(
                    id=UUID(attempt_record['id']),
                    product_id=product_id,
                    attempt_number=attempt_record['attempt_number'],
                    search_url=search_url,
                    method=EnrichmentMethod(method),
                    status=status,
                    confidence_score=confidence_score,
                    firecrawl_response=firecrawl_response,
                    error_message=error_message,
                    credits_used=1,
                    processing_time_ms=processing_time_ms,
                    created_at=datetime.fromisoformat(attempt_record['created_at']),
                    updated_at=datetime.fromisoformat(attempt_record['updated_at'])
                )
            else:
                raise DatabaseError("Failed to create scraping attempt record")
                
        except Exception as e:
            logger.error(
                "Error creating scraping attempt",
                product_id=str(product_id),
                error=str(e)
            )
            raise DatabaseError(
                f"Failed to create scraping attempt: {str(e)}",
                operation="insert",
                table="scraping_attempts"
            )
    
    async def _update_product_status(
        self,
        product_id: UUID,
        status: ProductStatus,
        enrichment_status: Optional[str] = None,
        processing_notes: Optional[str] = None
    ) -> None:
        """
        Update product status and enrichment information.
        
        Args:
            product_id: Product ID
            status: New product status
            enrichment_status: Enrichment status
            processing_notes: Optional processing notes
        """
        try:
            update_data = {
                'status': status.value,
                'last_enrichment_attempt': datetime.utcnow().isoformat()
            }
            
            if enrichment_status:
                update_data['enrichment_status'] = enrichment_status
            
            if processing_notes:
                update_data['enrichment_notes'] = processing_notes
            
            result = self.database_service.client.table('products')\
                .update(update_data)\
                .eq('id', str(product_id))\
                .execute()
            
            if not result.data:
                raise DatabaseError(f"Product not found: {product_id}")
                
            logger.debug(
                "Product status updated",
                product_id=str(product_id),
                status=status.value,
                enrichment_status=enrichment_status
            )
            
        except Exception as e:
            logger.error(
                "Error updating product status",
                product_id=str(product_id),
                status=status.value,
                error=str(e)
            )
            raise DatabaseError(
                f"Failed to update product status: {str(e)}",
                operation="update",
                table="products"
            )
    
    async def _update_product_enrichment(
        self,
        product_id: UUID,
        scraped_name: str,
        scraped_description: str,
        scraped_url: str,
        scraped_images_urls: List[str],
        scraped_images_metadata: List[Dict[str, Any]],
        scraping_confidence: int,
        successful_scraping_attempt_id: UUID,
        status: ProductStatus,
        enrichment_status: str
    ) -> None:
        """
        Update product with enriched data.
        
        Args:
            product_id: Product ID
            scraped_name: Scraped product name
            scraped_description: Scraped description
            scraped_url: Scraped product URL
            scraped_images_urls: List of scraped image URLs
            scraped_images_metadata: Enhanced image metadata
            scraping_confidence: Confidence score
            successful_scraping_attempt_id: ID of successful scraping attempt
            status: New product status
            enrichment_status: Enrichment status
        """
        try:
            update_data = {
                'scraped_name': scraped_name,
                'scraped_description': scraped_description,
                'scraped_url': scraped_url,
                'scraped_images_urls': scraped_images_urls,
                'scraped_images_metadata': scraped_images_metadata,
                'scraping_confidence': scraping_confidence,
                'successful_scraping_attempt_id': str(successful_scraping_attempt_id),
                'status': status.value,
                'enrichment_status': enrichment_status,
                'last_enrichment_attempt': datetime.utcnow().isoformat()
            }
            
            result = self.database_service.client.table('products')\
                .update(update_data)\
                .eq('id', str(product_id))\
                .execute()
            
            if not result.data:
                raise DatabaseError(f"Product not found: {product_id}")
                
            logger.debug(
                "Product enrichment data updated",
                product_id=str(product_id),
                scraped_name=scraped_name,
                confidence=scraping_confidence,
                images_count=len(scraped_images_urls)
            )
            
        except Exception as e:
            logger.error(
                "Error updating product enrichment data",
                product_id=str(product_id),
                error=str(e)
            )
            raise DatabaseError(
                f"Failed to update product enrichment data: {str(e)}",
                operation="update",
                table="products"
            )
    
    async def get_enrichment_status(self, batch_id: UUID) -> Dict[str, Any]:
        """
        Get enrichment status for a batch.
        
        Args:
            batch_id: Batch ID
            
        Returns:
            Dict[str, Any]: Enrichment status information
        """
        try:
            # Get products in batch
            products = await self.database_service.get_products(batch_id=batch_id)
            
            if not products:
                return {
                    "batch_id": str(batch_id),
                    "total_products": 0,
                    "completed_products": 0,
                    "failed_products": 0,
                    "processing_products": 0,
                    "pending_products": 0,
                    "avg_confidence_score": 0.0,
                    "last_updated": datetime.utcnow().isoformat()
                }
            
            # Count products by status
            total_products = len(products)
            completed_products = len([p for p in products if p.status == ProductStatus.READY])
            failed_products = len([p for p in products if p.status == ProductStatus.FAILED])
            processing_products = len([p for p in products if p.status == ProductStatus.PROCESSING])
            pending_products = len([p for p in products if p.status == ProductStatus.DRAFT])
            
            # Calculate average confidence score
            enriched_products = [p for p in products if p.status == ProductStatus.READY and hasattr(p, 'scraping_confidence')]
            avg_confidence = sum(p.scraping_confidence for p in enriched_products) / len(enriched_products) if enriched_products else 0.0
            
            return {
                "batch_id": str(batch_id),
                "total_products": total_products,
                "completed_products": completed_products,
                "failed_products": failed_products,
                "processing_products": processing_products,
                "pending_products": pending_products,
                "avg_confidence_score": round(avg_confidence, 2),
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(
                "Error getting enrichment status",
                batch_id=str(batch_id),
                error=str(e)
            )
            raise EnrichmentError(f"Failed to get enrichment status: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of enrichment service.
        
        Returns:
            Dict[str, Any]: Health check results
        """
        try:
            # Check database connectivity
            db_health = await self.database_service.health_check()
            
            # Check Firecrawl API connectivity
            firecrawl_health = await self.firecrawl_client.health_check()
            
            # Overall health status
            overall_healthy = (
                db_health.get("status") == "healthy" and
                firecrawl_health.get("status") == "healthy"
            )
            
            return {
                "status": "healthy" if overall_healthy else "unhealthy",
                "service": "product-enrichment",
                "components": {
                    "database": db_health,
                    "firecrawl_api": firecrawl_health
                },
                "max_concurrent": self.max_concurrent,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Enrichment service health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "service": "product-enrichment",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global service instance
_enrichment_service: Optional[ProductEnrichmentService] = None


def get_product_enrichment_service(config: Optional[EnrichmentConfig] = None) -> ProductEnrichmentService:
    """
    Get the global product enrichment service instance.
    
    Args:
        config: Optional enrichment configuration
        
    Returns:
        ProductEnrichmentService: Configured enrichment service instance
    """
    global _enrichment_service
    
    if _enrichment_service is None:
        _enrichment_service = ProductEnrichmentService(config)
    
    return _enrichment_service


def reset_product_enrichment_service() -> None:
    """Reset the global enrichment service instance (useful for testing)."""
    global _enrichment_service
    _enrichment_service = None
