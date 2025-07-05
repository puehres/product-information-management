"""
Main invoice processing service.

This module orchestrates the complete invoice processing pipeline from
PDF upload to database storage, integrating all components.
"""

import uuid
import structlog
from datetime import datetime
from typing import Dict, Any, Optional
from app.models.invoice import (
    InvoiceUploadResponse, 
    InvoiceParsingResult,
    UnknownSupplierError,
    S3UploadError,
    PDFParsingError
)
from app.services.pdf_parser import PDFParserService
from app.services.supplier_detector import SupplierDetectionService
from app.services.s3_manager import S3InvoiceManager
from app.parsers import LawnFawnParsingStrategy
from app.services.database_service import DatabaseService
from app.core.config import get_settings

logger = structlog.get_logger(__name__)


class InvoiceProcessorService:
    """
    Main service for processing invoice uploads.
    
    Orchestrates the complete pipeline:
    1. PDF parsing and text extraction
    2. Supplier detection from content
    3. Supplier-specific invoice parsing
    4. S3 upload for storage
    5. Database storage of results
    """
    
    def __init__(self):
        """Initialize invoice processor with all required services."""
        self.settings = get_settings()
        
        # Initialize services
        self.pdf_parser = PDFParserService()
        self.supplier_detector = SupplierDetectionService()
        self.s3_manager = S3InvoiceManager()
        self.db_service = DatabaseService()
        
        # Initialize parsing strategies
        self.parsing_strategies = {
            'lawnfawn': LawnFawnParsingStrategy()
        }
        
        logger.info("Invoice processor initialized")
    
    async def process_invoice(self, file_data: bytes, filename: str) -> InvoiceUploadResponse:
        """
        Process uploaded invoice through complete pipeline.
        
        Args:
            file_data: PDF file content as bytes
            filename: Original filename
            
        Returns:
            InvoiceUploadResponse: Complete processing result
        """
        batch_id = str(uuid.uuid4())
        
        logger.info(
            "Starting invoice processing",
            batch_id=batch_id,
            filename=filename,
            file_size=len(file_data)
        )
        
        try:
            # Step 1: Validate PDF file
            if not self.pdf_parser.validate_pdf_file(file_data):
                return InvoiceUploadResponse(
                    success=False,
                    error="invalid_file",
                    message="File is not a valid PDF document"
                )
            
            # Step 2: Extract PDF content
            logger.info("Extracting PDF content", batch_id=batch_id)
            pdf_text, tables = self.pdf_parser.extract_text_and_tables(file_data)
            
            if not pdf_text.strip():
                return InvoiceUploadResponse(
                    success=False,
                    error="empty_pdf",
                    message="PDF contains no readable text content"
                )
            
            # Step 3: Detect supplier
            logger.info("Detecting supplier", batch_id=batch_id)
            try:
                detection_result = self.supplier_detector.detect_supplier(pdf_text)
            except UnknownSupplierError as e:
                logger.warning("Unknown supplier detected", batch_id=batch_id, error=str(e))
                return InvoiceUploadResponse(
                    success=False,
                    error="unknown_supplier",
                    message=e.message,
                    supported_suppliers=e.supported_suppliers
                )
            
            # Step 4: Parse invoice using supplier-specific strategy
            logger.info(
                "Parsing invoice content",
                batch_id=batch_id,
                supplier=detection_result.supplier_code
            )
            
            parsing_strategy = self.get_parsing_strategy(detection_result.supplier_code)
            if not parsing_strategy:
                return InvoiceUploadResponse(
                    success=False,
                    error="unsupported_supplier",
                    message=f"No parsing strategy available for supplier: {detection_result.supplier_code}"
                )
            
            parsing_result = parsing_strategy.parse_invoice(pdf_text, tables)
            
            # Step 5: Upload to S3
            logger.info("Uploading to S3", batch_id=batch_id)
            try:
                s3_info = self.s3_manager.upload_invoice(
                    file_data, 
                    detection_result.supplier_code, 
                    filename
                )
            except S3UploadError as e:
                logger.error("S3 upload failed", batch_id=batch_id, error=str(e))
                return InvoiceUploadResponse(
                    success=False,
                    error="s3_upload_failed",
                    message=f"Failed to store invoice: {e.message}"
                )
            
            # Step 6: Store in database
            logger.info("Storing in database", batch_id=batch_id)
            try:
                await self.store_processing_results(
                    batch_id,
                    detection_result,
                    parsing_result,
                    s3_info,
                    filename,
                    len(file_data)
                )
            except Exception as e:
                logger.error("Database storage failed", batch_id=batch_id, error=str(e))
                # Try to cleanup S3 file on database failure
                try:
                    self.s3_manager.delete_invoice(s3_info['s3_key'])
                except Exception:
                    pass  # Don't fail if cleanup fails
                
                return InvoiceUploadResponse(
                    success=False,
                    error="database_error",
                    message=f"Failed to store processing results: {e}"
                )
            
            # Step 7: Generate download URL
            try:
                download_url, expires_at = self.s3_manager.generate_download_url(s3_info['s3_key'])
            except S3UploadError as e:
                logger.warning("Failed to generate download URL", batch_id=batch_id, error=str(e))
                download_url = None
            
            # Success response
            logger.info(
                "Invoice processing completed successfully",
                batch_id=batch_id,
                supplier=detection_result.supplier_code,
                products_found=len(parsing_result.products),
                success_rate=parsing_result.parsing_success_rate
            )
            
            return InvoiceUploadResponse(
                success=True,
                batch_id=batch_id,
                supplier=detection_result.supplier_code,
                products_found=len(parsing_result.products),
                parsing_success_rate=parsing_result.parsing_success_rate,
                invoice_metadata={
                    'invoice_number': parsing_result.metadata.invoice_number,
                    'invoice_date': parsing_result.metadata.invoice_date,
                    'currency': parsing_result.metadata.currency,
                    'total_amount': str(parsing_result.metadata.total_amount) if parsing_result.metadata.total_amount else None
                },
                s3_key=s3_info['s3_key'],
                download_url=download_url,
                message="Invoice processed successfully"
            )
            
        except PDFParsingError as e:
            logger.error("PDF parsing error", batch_id=batch_id, error=str(e))
            return InvoiceUploadResponse(
                success=False,
                error="pdf_parsing_failed",
                message=f"Failed to parse PDF: {e.message}"
            )
        
        except Exception as e:
            logger.error("Unexpected processing error", batch_id=batch_id, error=str(e))
            return InvoiceUploadResponse(
                success=False,
                error="processing_failed",
                message=f"Unexpected error during processing: {e}"
            )
    
    def get_parsing_strategy(self, supplier_code: str):
        """
        Get parsing strategy for supplier.
        
        Args:
            supplier_code: Supplier code
            
        Returns:
            Parsing strategy instance or None
        """
        return self.parsing_strategies.get(supplier_code)
    
    async def store_processing_results(
        self,
        batch_id: str,
        detection_result,
        parsing_result: InvoiceParsingResult,
        s3_info: Dict[str, Any],
        original_filename: str,
        file_size: int
    ) -> None:
        """
        Store processing results in database.
        
        Args:
            batch_id: Unique batch identifier
            detection_result: Supplier detection result
            parsing_result: Invoice parsing result
            s3_info: S3 upload information
            original_filename: Original filename
            file_size: File size in bytes
        """
        # Create upload batch record
        batch_data = {
            'id': batch_id,
            'file_type': 'PDF',
            'status': 'COMPLETED',
            'original_filename': original_filename,
            'file_size_bytes': file_size,
            's3_key': s3_info['s3_key'],
            's3_url': s3_info['s3_url'],
            'supplier_code': detection_result.supplier_code,
            'supplier_detection_method': detection_result.detection_method.value,
            'supplier_detection_confidence': float(detection_result.confidence),
            'invoice_number': parsing_result.metadata.invoice_number,
            'invoice_date': parsing_result.metadata.invoice_date,
            'currency_code': parsing_result.metadata.currency,
            'total_amount_original': float(parsing_result.metadata.total_amount) if parsing_result.metadata.total_amount else None,
            'parsing_success_rate': parsing_result.parsing_success_rate,
            'products_found': len(parsing_result.products),
            'parsing_errors': parsing_result.parsing_errors,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Store batch record
        await self.db_service.create_upload_batch(batch_data)
        
        # Store product records
        for product in parsing_result.products:
            product_data = {
                'id': str(uuid.uuid4()),
                'upload_batch_id': batch_id,
                'supplier_sku': product.supplier_sku,
                'manufacturer': product.manufacturer,
                'manufacturer_sku': product.manufacturer_sku,
                'category': product.category,
                'name': product.product_name,
                'quantity_ordered': product.quantity,
                'price_usd': float(product.price_usd),
                'line_total_usd': float(product.line_total_usd),
                'origin_country': product.origin_country,
                'tariff_code': product.tariff_code,
                'raw_description': product.raw_description,
                'line_number': product.line_number,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            await self.db_service.create_product(product_data)
        
        logger.info(
            "Processing results stored",
            batch_id=batch_id,
            products_stored=len(parsing_result.products)
        )
    
    async def get_invoice_details(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed invoice processing results.
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            Dict with invoice details or None if not found
        """
        try:
            # Get batch information
            batch = await self.db_service.get_upload_batch(batch_id)
            if not batch:
                return None
            
            # Get associated products
            products = await self.db_service.get_products_by_batch(batch_id)
            
            return {
                'batch': batch,
                'products': products,
                'summary': {
                    'total_products': len(products),
                    'parsing_success_rate': batch.get('parsing_success_rate', 0),
                    'supplier': batch.get('supplier_code'),
                    'invoice_number': batch.get('invoice_number'),
                    'processing_date': batch.get('created_at')
                }
            }
            
        except Exception as e:
            logger.error("Failed to get invoice details", batch_id=batch_id, error=str(e))
            return None
    
    async def generate_invoice_download_url(self, batch_id: str) -> Optional[str]:
        """
        Generate download URL for invoice.
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            Download URL or None if failed
        """
        try:
            # Get batch to find S3 key
            batch = await self.db_service.get_upload_batch(batch_id)
            if not batch or not batch.get('s3_key'):
                return None
            
            # Generate presigned URL
            download_url, expires_at = self.s3_manager.generate_download_url(batch['s3_key'])
            
            # Update download count
            await self.db_service.increment_download_count(batch_id)
            
            return download_url
            
        except Exception as e:
            logger.error("Failed to generate download URL", batch_id=batch_id, error=str(e))
            return None
