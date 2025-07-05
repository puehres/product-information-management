"""
Invoice-specific Pydantic models for PDF invoice processing.

This module provides type-safe models for invoice upload, supplier detection,
product parsing, and API responses.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from enum import Enum


class SupplierCode(str, Enum):
    """Supported supplier codes for invoice processing."""
    LAWNFAWN = "lawnfawn"
    CRAFTLINES = "craftlines"
    MAMA_ELEPHANT = "mama-elephant"


class DetectionMethod(str, Enum):
    """Methods used for supplier detection."""
    HEADER_PATTERN = "header_pattern"
    COMPANY_NAME = "company_name"
    ADDRESS_PATTERN = "address_pattern"
    WEBSITE_PATTERN = "website_pattern"


class InvoiceUploadRequest(BaseModel):
    """Request model for invoice upload - handled by FastAPI File upload."""
    pass


class SupplierDetectionResult(BaseModel):
    """Result of supplier detection from PDF content."""
    supplier_code: str = Field(..., description="Detected supplier code")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence 0-1")
    matched_patterns: List[str] = Field(..., description="Patterns that matched")
    detection_method: DetectionMethod = Field(..., description="How supplier was detected")
    
    @validator('supplier_code')
    def validate_supplier_code(cls, v):
        """Validate supplier code is supported."""
        if v not in [code.value for code in SupplierCode]:
            raise ValueError(f"Unsupported supplier code: {v}")
        return v


class InvoiceMetadata(BaseModel):
    """Extracted invoice metadata."""
    invoice_number: Optional[str] = Field(None, description="Invoice number")
    invoice_date: Optional[str] = Field(None, description="Invoice date")
    ship_date: Optional[str] = Field(None, description="Ship date")
    currency: str = Field(default="USD", description="Invoice currency")
    total_amount: Optional[Decimal] = Field(None, description="Total invoice amount")
    company_name: Optional[str] = Field(None, description="Issuing company name")
    company_address: Optional[str] = Field(None, description="Company address")
    
    @validator('currency')
    def validate_currency(cls, v):
        """Validate currency code."""
        valid_currencies = ["USD", "EUR", "GBP", "CAD"]
        if v not in valid_currencies:
            raise ValueError(f"Unsupported currency: {v}")
        return v


class ParsedProduct(BaseModel):
    """Single product parsed from invoice."""
    supplier_sku: str = Field(..., description="SKU from invoice")
    manufacturer: str = Field(..., description="Product manufacturer")
    manufacturer_sku: str = Field(..., description="Original manufacturer SKU")
    category: str = Field(..., description="Product category")
    product_name: str = Field(..., description="Product name")
    quantity: int = Field(..., ge=1, description="Quantity ordered")
    price_usd: Decimal = Field(..., ge=0, description="USD price per unit")
    line_total_usd: Decimal = Field(..., ge=0, description="Total line amount USD")
    origin_country: Optional[str] = Field(None, description="Country of origin")
    tariff_code: Optional[str] = Field(None, description="Tariff code")
    raw_description: str = Field(..., description="Original description from invoice")
    line_number: int = Field(..., ge=1, description="Line number in invoice")
    
    @validator('supplier_sku')
    def validate_supplier_sku(cls, v):
        """Validate supplier SKU format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Supplier SKU cannot be empty")
        return v.strip()
    
    @validator('manufacturer_sku')
    def validate_manufacturer_sku(cls, v):
        """Validate manufacturer SKU format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Manufacturer SKU cannot be empty")
        return v.strip()
    
    @validator('product_name')
    def validate_product_name(cls, v):
        """Validate product name."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Product name cannot be empty")
        return v.strip()


class InvoiceParsingResult(BaseModel):
    """Complete result of invoice parsing."""
    supplier: str = Field(..., description="Detected supplier")
    metadata: InvoiceMetadata = Field(..., description="Invoice metadata")
    products: List[ParsedProduct] = Field(..., description="Parsed products")
    total_products: int = Field(..., ge=0, description="Total products found")
    parsing_success_rate: float = Field(..., ge=0, le=100, description="Success rate percentage")
    parsing_errors: List[str] = Field(default_factory=list, description="Parsing errors")
    
    @validator('total_products')
    def validate_total_products(cls, v, values):
        """Validate total products matches products list length."""
        if 'products' in values and len(values['products']) != v:
            raise ValueError("Total products must match products list length")
        return v


class InvoiceUploadResponse(BaseModel):
    """Response for invoice upload API."""
    success: bool = Field(..., description="Upload success status")
    batch_id: Optional[str] = Field(None, description="Created batch ID")
    supplier: Optional[str] = Field(None, description="Detected supplier")
    products_found: Optional[int] = Field(None, description="Number of products found")
    parsing_success_rate: Optional[float] = Field(None, description="Parsing success rate")
    invoice_metadata: Optional[Dict[str, Any]] = Field(None, description="Invoice metadata")
    s3_key: Optional[str] = Field(None, description="S3 storage key")
    download_url: Optional[str] = Field(None, description="Download URL")
    error: Optional[str] = Field(None, description="Error type if failed")
    message: str = Field(..., description="Response message")
    supported_suppliers: Optional[List[str]] = Field(None, description="Supported suppliers if error")


class InvoiceDownloadResponse(BaseModel):
    """Response for invoice download API."""
    success: bool = Field(..., description="Download success status")
    download_url: Optional[str] = Field(None, description="Presigned download URL")
    expires_at: Optional[datetime] = Field(None, description="URL expiration time")
    filename: Optional[str] = Field(None, description="Original filename")
    error: Optional[str] = Field(None, description="Error message if failed")


class InvoiceListResponse(BaseModel):
    """Response for listing invoices."""
    success: bool = Field(..., description="Request success status")
    invoices: List[Dict[str, Any]] = Field(..., description="List of invoice summaries")
    total_count: int = Field(..., ge=0, description="Total number of invoices")
    error: Optional[str] = Field(None, description="Error message if failed")


class UnknownSupplierError(Exception):
    """Exception raised when supplier cannot be detected from invoice."""
    
    def __init__(self, message: str, supported_suppliers: Optional[List[str]] = None):
        self.message = message
        self.supported_suppliers = supported_suppliers or []
        super().__init__(self.message)


class S3UploadError(Exception):
    """Exception raised when S3 upload fails."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class PDFParsingError(Exception):
    """Exception raised when PDF parsing fails."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)
