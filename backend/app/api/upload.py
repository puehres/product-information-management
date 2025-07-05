"""
Upload API endpoints for invoice processing.

This module provides FastAPI endpoints for uploading and processing
PDF invoices with comprehensive error handling and validation.
"""

import structlog
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
from app.models.invoice import (
    InvoiceUploadResponse,
    InvoiceDownloadResponse,
    InvoiceListResponse
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
                products_found=result.products_found
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
    limit: int = 50,
    offset: int = 0,
    supplier: Optional[str] = None
) -> InvoiceListResponse:
    """
    List processed invoices with pagination.
    
    Args:
        limit: Maximum number of invoices to return (default: 50)
        offset: Number of invoices to skip (default: 0)
        supplier: Filter by supplier code (optional)
        
    Returns:
        InvoiceListResponse: List of invoice summaries
        
    Raises:
        HTTPException: For invalid parameters or database errors
    """
    logger.info(
        "Invoice list request",
        limit=limit,
        offset=offset,
        supplier=supplier
    )
    
    # Validate parameters
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100"
        )
    
    if offset < 0:
        raise HTTPException(
            status_code=400,
            detail="Offset must be non-negative"
        )
    
    try:
        # TODO: Implement database query for listing invoices
        # This would require extending the database service
        
        # For now, return empty list
        return InvoiceListResponse(
            success=True,
            invoices=[],
            total_count=0,
            error=None
        )
        
    except Exception as e:
        logger.error(
            "Error listing invoices",
            error=str(e)
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
