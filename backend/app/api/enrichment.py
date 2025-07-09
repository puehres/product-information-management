"""
FastAPI endpoints for product enrichment.

This module provides REST API endpoints for managing product enrichment,
including batch processing, status monitoring, and health checks.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
import structlog

from ..models.enrichment import (
    EnrichmentRequest, EnrichmentResponse, EnrichmentStatus,
    ProductEnrichmentDetail, EnrichmentAnalytics
)
from ..services.product_enrichment import get_product_enrichment_service
from ..exceptions.enrichment import (
    EnrichmentError, ConfigurationError, DatabaseError
)

logger = structlog.get_logger(__name__)

# Create router
router = APIRouter(prefix="/enrichment", tags=["enrichment"])


@router.post("/batch", response_model=EnrichmentResponse)
async def enrich_batch(
    batch_id: UUID,
    background_tasks: BackgroundTasks,
    max_concurrent: Optional[int] = Query(default=5, ge=1, le=20),
    force_retry: bool = Query(default=False)
):
    """
    Start enrichment process for all products in a batch.
    
    Args:
        batch_id: Upload batch ID
        background_tasks: FastAPI background tasks
        max_concurrent: Maximum concurrent enrichments (1-20)
        force_retry: Force retry of previously failed products
        
    Returns:
        EnrichmentResponse: Enrichment process status
    """
    logger.info(
        "Batch enrichment requested",
        batch_id=str(batch_id),
        max_concurrent=max_concurrent,
        force_retry=force_retry
    )
    
    try:
        enrichment_service = get_product_enrichment_service()
        
        # Get products count for estimation
        products = await enrichment_service._get_products_for_enrichment(batch_id)
        total_products = len(products)
        
        if total_products == 0:
            return EnrichmentResponse(
                success=True,
                message="No products found for enrichment",
                batch_id=batch_id,
                total_products=0,
                processing_started=False
            )
        
        # Start background enrichment process
        background_tasks.add_task(
            enrichment_service.enrich_batch,
            batch_id=batch_id,
            max_concurrent=max_concurrent
        )
        
        # Estimate completion time (rough calculation)
        estimated_time_per_product = 10  # seconds
        estimated_total_seconds = (total_products * estimated_time_per_product) // max_concurrent
        estimated_completion = f"{estimated_total_seconds // 60}m {estimated_total_seconds % 60}s"
        
        logger.info(
            "Batch enrichment started",
            batch_id=str(batch_id),
            total_products=total_products,
            estimated_completion=estimated_completion
        )
        
        return EnrichmentResponse(
            success=True,
            message=f"Enrichment started for {total_products} products",
            batch_id=batch_id,
            total_products=total_products,
            processing_started=True,
            estimated_completion_time=estimated_completion
        )
        
    except Exception as e:
        logger.error(
            "Batch enrichment request failed",
            batch_id=str(batch_id),
            error=str(e),
            error_type=type(e).__name__
        )
        
        if isinstance(e, (EnrichmentError, ConfigurationError, DatabaseError)):
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/products", response_model=EnrichmentResponse)
async def enrich_products(
    request: EnrichmentRequest,
    background_tasks: BackgroundTasks
):
    """
    Start enrichment process for specific products.
    
    Args:
        request: Enrichment request with product IDs or batch ID
        background_tasks: FastAPI background tasks
        
    Returns:
        EnrichmentResponse: Enrichment process status
    """
    logger.info(
        "Product enrichment requested",
        product_ids=request.product_ids,
        batch_id=request.batch_id,
        max_concurrent=request.max_concurrent
    )
    
    try:
        enrichment_service = get_product_enrichment_service()
        
        if request.product_ids:
            # Enrich specific products
            total_products = len(request.product_ids)
            
            background_tasks.add_task(
                enrichment_service.enrich_products,
                product_ids=request.product_ids,
                max_concurrent=request.max_concurrent
            )
            
            return EnrichmentResponse(
                success=True,
                message=f"Enrichment started for {total_products} products",
                total_products=total_products,
                processing_started=True
            )
            
        elif request.batch_id:
            # Enrich batch
            products = await enrichment_service._get_products_for_enrichment(request.batch_id)
            total_products = len(products)
            
            if total_products == 0:
                return EnrichmentResponse(
                    success=True,
                    message="No products found for enrichment",
                    batch_id=request.batch_id,
                    total_products=0,
                    processing_started=False
                )
            
            background_tasks.add_task(
                enrichment_service.enrich_batch,
                batch_id=request.batch_id,
                max_concurrent=request.max_concurrent
            )
            
            return EnrichmentResponse(
                success=True,
                message=f"Enrichment started for {total_products} products",
                batch_id=request.batch_id,
                total_products=total_products,
                processing_started=True
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Must specify either product_ids or batch_id"
            )
            
    except Exception as e:
        logger.error(
            "Product enrichment request failed",
            error=str(e),
            error_type=type(e).__name__
        )
        
        if isinstance(e, (EnrichmentError, ConfigurationError, DatabaseError)):
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status/{batch_id}", response_model=EnrichmentStatus)
async def get_enrichment_status(batch_id: UUID):
    """
    Get enrichment status for a batch.
    
    Args:
        batch_id: Batch ID
        
    Returns:
        EnrichmentStatus: Current enrichment status
    """
    logger.debug("Enrichment status requested", batch_id=str(batch_id))
    
    try:
        enrichment_service = get_product_enrichment_service()
        status_data = await enrichment_service.get_enrichment_status(batch_id)
        
        return EnrichmentStatus(**status_data)
        
    except Exception as e:
        logger.error(
            "Failed to get enrichment status",
            batch_id=str(batch_id),
            error=str(e)
        )
        
        if isinstance(e, (EnrichmentError, DatabaseError)):
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/products/{product_id}/details", response_model=ProductEnrichmentDetail)
async def get_product_enrichment_details(product_id: UUID):
    """
    Get detailed enrichment information for a specific product.
    
    Args:
        product_id: Product ID
        
    Returns:
        ProductEnrichmentDetail: Detailed enrichment information
    """
    logger.debug("Product enrichment details requested", product_id=str(product_id))
    
    try:
        enrichment_service = get_product_enrichment_service()
        
        # Get product details from database
        product = await enrichment_service.database_service.get_product_by_id(product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Get scraping attempts count
        attempts_result = enrichment_service.database_service.client.table('scraping_attempts')\
            .select('*', count='exact')\
            .eq('product_id', str(product_id))\
            .execute()
        
        attempt_count = len(attempts_result.data) if attempts_result.data else 0
        
        # Get latest attempt for error message
        latest_attempt = None
        if attempts_result.data:
            latest_attempt = max(attempts_result.data, key=lambda x: x['created_at'])
        
        return ProductEnrichmentDetail(
            product_id=product_id,
            supplier_sku=product.supplier_sku or "",
            status=product.status.value if hasattr(product.status, 'value') else str(product.status),
            enrichment_status=getattr(product, 'enrichment_status', 'pending'),
            confidence_score=getattr(product, 'scraping_confidence', None),
            scraped_name=getattr(product, 'scraped_name', None),
            scraped_url=getattr(product, 'scraped_url', None),
            images_found=len(getattr(product, 'scraped_images_urls', [])),
            last_attempt=getattr(product, 'last_enrichment_attempt', None),
            error_message=latest_attempt.get('error_message') if latest_attempt else None,
            requires_review=getattr(product, 'requires_manual_review', False),
            attempt_count=attempt_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get product enrichment details",
            product_id=str(product_id),
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analytics", response_model=List[EnrichmentAnalytics])
async def get_enrichment_analytics(
    batch_id: Optional[UUID] = Query(default=None),
    manufacturer: Optional[str] = Query(default=None)
):
    """
    Get enrichment analytics and performance metrics.
    
    Args:
        batch_id: Optional batch ID filter
        manufacturer: Optional manufacturer filter
        
    Returns:
        List[EnrichmentAnalytics]: Analytics data
    """
    logger.debug(
        "Enrichment analytics requested",
        batch_id=str(batch_id) if batch_id else None,
        manufacturer=manufacturer
    )
    
    try:
        enrichment_service = get_product_enrichment_service()
        
        # Build query for enrichment analytics view
        query = enrichment_service.database_service.client.table('enrichment_analytics').select('*')
        
        if batch_id:
            query = query.eq('batch_id', str(batch_id))
        
        if manufacturer:
            query = query.eq('manufacturer', manufacturer)
        
        result = query.execute()
        
        analytics_data = []
        for row in result.data or []:
            analytics_data.append(EnrichmentAnalytics(
                batch_id=UUID(row['batch_id']) if row['batch_id'] else None,
                manufacturer=row['manufacturer'],
                total_products=row['total_products'] or 0,
                enriched_count=row['enriched_count'] or 0,
                failed_count=row['failed_count'] or 0,
                review_required_count=row['review_required_count'] or 0,
                avg_confidence_score=float(row['avg_confidence_score'] or 0),
                avg_processing_time_ms=float(row['avg_processing_time_ms'] or 0),
                total_credits_used=row['total_credits_used'] or 0
            ))
        
        return analytics_data
        
    except Exception as e:
        logger.error(
            "Failed to get enrichment analytics",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/retry/{product_id}")
async def retry_product_enrichment(
    product_id: UUID,
    background_tasks: BackgroundTasks
):
    """
    Retry enrichment for a specific product.
    
    Args:
        product_id: Product ID to retry
        background_tasks: FastAPI background tasks
        
    Returns:
        JSONResponse: Retry status
    """
    logger.info("Product enrichment retry requested", product_id=str(product_id))
    
    try:
        enrichment_service = get_product_enrichment_service()
        
        # Check if product exists
        product = await enrichment_service.database_service.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Start background retry
        background_tasks.add_task(
            enrichment_service.enrich_product,
            product_id=product_id
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Retry started for product {product_id}",
                "product_id": str(product_id)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Product enrichment retry failed",
            product_id=str(product_id),
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for enrichment service.
    
    Returns:
        JSONResponse: Health status
    """
    try:
        enrichment_service = get_product_enrichment_service()
        health_data = await enrichment_service.health_check()
        
        status_code = 200 if health_data.get("status") == "healthy" else 503
        
        return JSONResponse(
            status_code=status_code,
            content=health_data
        )
        
    except Exception as e:
        logger.error("Enrichment health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "product-enrichment",
                "error": str(e)
            }
        )


@router.get("/credits")
async def get_credits_info():
    """
    Get Firecrawl API credits information.
    
    Returns:
        JSONResponse: Credits information
    """
    try:
        enrichment_service = get_product_enrichment_service()
        credits_info = await enrichment_service.firecrawl_client.get_credits_info()
        
        return JSONResponse(
            status_code=200,
            content=credits_info
        )
        
    except Exception as e:
        logger.error("Failed to get credits info", error=str(e))
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e)
            }
        )


# Error handlers are registered at the app level in main.py
# This router only contains endpoint definitions
