"""
Upload API endpoints for invoice processing.

This module provides FastAPI endpoints for uploading and processing
PDF invoices with comprehensive error handling and validation.
"""

import structlog
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime
from app.models.invoice import (
    InvoiceUploadResponse,
    InvoiceDownloadResponse,
    InvoiceListResponse,
    InvoiceSummary,
    PaginationInfo
)
from app.services.invoice_processor import InvoiceProcessorService
from app.core.config import get_settings

logger = structlog.get_logger(__name__)

# Create router
router = APIRouter()

# Settings dependency
def get_settings_dep():
    return get_settings()


@router.post("/upload/invoice", response_model=InvoiceUploadResponse)
async def upload_invoice(
    file: UploadFile = File(...),
    settings = Depends(get_settings_dep)
) -> InvoiceUploadResponse:
    """
    Upload and process a PDF invoice.
    
    Args:
        file: PDF file upload
        
    Returns:
        InvoiceUploadResponse: Processing result with batch ID and metadata
        
    Raises:
        HTTPException: For validation errors and processing failures
    """
    logger.info(
        "Invoice upload request received",
        filename=file.filename,
        content_type=file.content_type,
        file_size=file.size if hasattr(file, 'size') else 'unknown'
    )
    
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided"
        )
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    # Validate content type
    if file.content_type and not file.content_type.startswith('application/pdf'):
        logger.warning(
            "Unexpected content type",
            content_type=file.content_type,
            filename=file.filename
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file uploaded"
            )
        
        # Check file size limit
        max_size = settings.max_file_size
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum limit of {max_size // (1024*1024)}MB"
            )
        
        logger.info(
            "File validation passed",
            filename=file.filename,
            file_size=len(file_content)
        )
        
        # Process invoice
        processor = InvoiceProcessorService()
        result = await processor.process_invoice(file_content, file.filename)
        
        # Log result
        if result.success:
            logger.info(
                "Invoice processing completed successfully",
                batch_id=result.batch_id,
                supplier=result.supplier,
                total_products=result.total_products
            )
        else:
            logger.warning(
                "Invoice processing failed",
                error=result.error,
                message=result.message
            )
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            "Unexpected error during invoice upload",
            filename=file.filename,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/invoices/{batch_id}/download", response_model=InvoiceDownloadResponse)
async def download_invoice(batch_id: str) -> InvoiceDownloadResponse:
    """
    Generate download URL for processed invoice.
    
    Args:
        batch_id: Batch identifier
        
    Returns:
        InvoiceDownloadResponse: Download URL and metadata
        
    Raises:
        HTTPException: If batch not found or download generation fails
    """
    logger.info("Download request received", batch_id=batch_id)
    
    try:
        processor = InvoiceProcessorService()
        
        # Get invoice details to verify existence
        invoice_details = await processor.get_invoice_details(batch_id)
        if not invoice_details:
            raise HTTPException(
                status_code=404,
                detail="Invoice not found"
            )
        
        # Generate download URL
        download_url = await processor.generate_invoice_download_url(batch_id)
        if not download_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate download URL"
            )
        
        logger.info("Download URL generated successfully", batch_id=batch_id)
        
        return InvoiceDownloadResponse(
            success=True,
            download_url=download_url,
            filename=invoice_details['batch'].get('original_filename'),
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error generating download URL",
            batch_id=batch_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate download URL: {str(e)}"
        )


@router.get("/invoices/{batch_id}/details")
async def get_invoice_details(batch_id: str):
    """
    Get detailed invoice processing results.
    
    Args:
        batch_id: Batch identifier
        
    Returns:
        Dict: Detailed invoice information including products
        
    Raises:
        HTTPException: If batch not found
    """
    logger.info("Invoice details request", batch_id=batch_id)
    
    try:
        processor = InvoiceProcessorService()
        details = await processor.get_invoice_details(batch_id)
        
        if not details:
            raise HTTPException(
                status_code=404,
                detail="Invoice not found"
            )
        
        logger.info(
            "Invoice details retrieved",
            batch_id=batch_id,
            products_count=len(details['products'])
        )
        
        return details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error retrieving invoice details",
            batch_id=batch_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve invoice details: {str(e)}"
        )


@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    limit: int = Query(50, ge=1, le=100, description="Number of invoices to return"),
    offset: int = Query(0, ge=0, description="Number of invoices to skip"),
    supplier: Optional[str] = Query(None, description="Filter by supplier code"),
    date_from: Optional[str] = Query(None, description="Filter invoices after this date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter invoices before this date (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, min_length=1, description="Search in filename or invoice number"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
) -> InvoiceListResponse:
    """
    List processed invoices with comprehensive filtering and pagination.
    
    Args:
        limit: Number of invoices to return (1-100)
        offset: Number of invoices to skip
        supplier: Filter by supplier code
        date_from: Filter invoices after this date (YYYY-MM-DD)
        date_to: Filter invoices before this date (YYYY-MM-DD)
        search: Search in filename or invoice number
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        
    Returns:
        InvoiceListResponse: List of invoice summaries with pagination
        
    Raises:
        HTTPException: For invalid parameters or database errors
    """
    logger.info(
        "Invoice list request received",
        limit=limit,
        offset=offset,
        supplier=supplier,
        date_from=date_from,
        date_to=date_to,
        search=search
    )
    
    try:
        # Validate and parse date parameters
        parsed_date_from = None
        parsed_date_to = None
        
        if date_from:
            try:
                parsed_date_from = datetime.fromisoformat(date_from)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date_from format. Use YYYY-MM-DD"
                )
        
        if date_to:
            try:
                parsed_date_to = datetime.fromisoformat(date_to)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date_to format. Use YYYY-MM-DD"
                )
        
        # Get database service
        from app.services.database_service import get_database_service
        db_service = get_database_service()
        
        # Query with filters
        batches, total_count = await db_service.list_upload_batches_with_filters(
            limit=limit,
            offset=offset,
            supplier=supplier,
            date_from=parsed_date_from,
            date_to=parsed_date_to,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Convert to response format
        invoice_summaries = []
        for batch in batches:
            # Handle missing fields gracefully
            summary = InvoiceSummary(
                batch_id=str(batch.id),
                supplier=getattr(batch, 'supplier_code', 'unknown') or "unknown",
                invoice_number=getattr(batch, 'invoice_number', None),
                invoice_date=getattr(batch, 'invoice_date', None),
                total_products=getattr(batch, 'total_products', 0),
                processing_date=batch.created_at,
                original_filename=getattr(batch, 'original_filename', 'unknown') or "unknown",
                parsing_success_rate=getattr(batch, 'parsing_success_rate', 0.0) or 0.0,
                file_size_mb=round((getattr(batch, 'file_size_bytes', 0) or 0) / (1024 * 1024), 2),
                currency=getattr(batch, 'currency_code', None),
                total_amount=float(getattr(batch, 'total_amount_original', 0)) if getattr(batch, 'total_amount_original', None) else None
            )
            invoice_summaries.append(summary)
        
        # Calculate pagination info - handle None total_count
        total_count = total_count or 0
        has_more = (offset + limit) < total_count
        next_offset = offset + limit if has_more else None
        
        pagination = PaginationInfo(
            limit=limit,
            offset=offset,
            next_offset=next_offset,
            has_more=has_more
        )
        
        logger.info(
            "Invoice list request completed",
            total_count=total_count,
            returned_count=len(invoice_summaries),
            has_more=has_more
        )
        
        return InvoiceListResponse(
            success=True,
            invoices=invoice_summaries,
            total_count=total_count,
            has_more=has_more,
            pagination=pagination,
            error=None
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            "Error listing invoices",
            error=str(e),
            limit=limit,
            offset=offset
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list invoices: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for upload service.
    
    Returns:
        Dict: Service health status
    """
    try:
        # Basic health check - could be extended to check dependencies
        return {
            "status": "healthy",
            "service": "invoice-upload",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Service unhealthy"
        )


# Note: Error handlers are implemented at the endpoint level with try/catch blocks
# APIRouter doesn't support exception_handler decorator - that's only for FastAPI app
