"""
Product models for the Universal Product Automation System.

This module defines Pydantic models for product data and processing.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from pydantic import Field, validator
from .base import BaseDBModel, BaseCreateModel, BaseUpdateModel, ProductStatus


class ProductBase(BaseCreateModel):
    """
    Base product model with common fields.
    """
    batch_id: UUID = Field(..., description="Upload batch ID")
    supplier_id: UUID = Field(..., description="Supplier ID")
    supplier_sku: str = Field(..., max_length=100, description="Supplier SKU")
    supplier_name: Optional[str] = Field(None, max_length=500, description="Original supplier product name")
    supplier_description: Optional[str] = Field(None, description="Original supplier description")
    supplier_price_usd: Optional[Decimal] = Field(None, ge=0, description="Supplier price in USD")
    supplier_price_eur: Optional[Decimal] = Field(None, ge=0, description="Supplier price in EUR")
    
    # Manufacturer and invoice-specific fields
    manufacturer: Optional[str] = Field(None, max_length=50, description="Product manufacturer")
    manufacturer_sku: Optional[str] = Field(None, max_length=100, description="Original manufacturer SKU")
    manufacturer_website: Optional[str] = Field(None, max_length=255, description="Manufacturer website")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    quantity_ordered: Optional[int] = Field(None, ge=1, description="Quantity ordered from invoice")
    line_total_usd: Optional[Decimal] = Field(None, ge=0, description="Total line amount USD")
    line_total_eur: Optional[Decimal] = Field(None, ge=0, description="Total line amount EUR")
    origin_country: Optional[str] = Field(None, max_length=50, description="Country of origin")
    tariff_code: Optional[str] = Field(None, max_length=20, description="Tariff code")
    raw_description: Optional[str] = Field(None, description="Original description from invoice")
    line_number: Optional[int] = Field(None, ge=1, description="Line number in invoice")
    
    @validator('supplier_sku')
    def validate_supplier_sku(cls, v):
        """Validate supplier SKU."""
        if not v or not v.strip():
            raise ValueError('Supplier SKU cannot be empty')
        return v.strip()
    
    @validator('supplier_price_usd', 'supplier_price_eur')
    def validate_prices(cls, v):
        """Validate price values."""
        if v is not None and v < 0:
            raise ValueError('Prices cannot be negative')
        return v


class ProductCreate(ProductBase):
    """
    Model for creating a new product.
    """
    pass


class ProductUpdate(BaseUpdateModel):
    """
    Model for updating an existing product.
    
    All fields are optional for partial updates.
    """
    supplier_sku: Optional[str] = Field(None, max_length=100, description="Supplier SKU")
    supplier_name: Optional[str] = Field(None, max_length=500, description="Original supplier product name")
    supplier_description: Optional[str] = Field(None, description="Original supplier description")
    supplier_price_usd: Optional[Decimal] = Field(None, ge=0, description="Supplier price in USD")
    supplier_price_eur: Optional[Decimal] = Field(None, ge=0, description="Supplier price in EUR")
    
    # Scraped data
    scraped_name: Optional[str] = Field(None, max_length=500, description="Scraped product name")
    scraped_description: Optional[str] = Field(None, description="Scraped product description")
    scraped_url: Optional[str] = Field(None, max_length=1000, description="Scraped product URL")
    scraped_images_urls: Optional[List[str]] = Field(None, description="Scraped image URLs")
    scraping_confidence: Optional[int] = Field(None, ge=0, le=100, description="Scraping confidence score")
    
    # German translations
    german_name: Optional[str] = Field(None, max_length=500, description="German product name")
    german_description: Optional[str] = Field(None, description="German product description")
    german_short_description: Optional[str] = Field(None, max_length=255, description="German short description")
    
    # Gambio export fields
    gambio_category: Optional[str] = Field(None, max_length=255, description="Gambio category path")
    gambio_tax_class_id: Optional[int] = Field(None, description="Gambio tax class ID")
    gambio_model: Optional[str] = Field(None, max_length=100, description="Gambio model number")
    gambio_price_eur: Optional[Decimal] = Field(None, ge=0, description="Gambio price in EUR")
    gambio_seo_url: Optional[str] = Field(None, max_length=255, description="Gambio SEO URL")
    
    # Processing status
    status: Optional[ProductStatus] = Field(None, description="Processing status")
    processing_notes: Optional[str] = Field(None, description="Processing notes")
    quality_score: Optional[int] = Field(None, ge=0, le=100, description="Quality score")
    requires_review: Optional[bool] = Field(None, description="Whether product requires review")
    review_notes: Optional[str] = Field(None, description="Review notes")
    
    @validator('supplier_sku')
    def validate_supplier_sku(cls, v):
        """Validate supplier SKU."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Supplier SKU cannot be empty')
            return v.strip()
        return v
    
    @validator('supplier_price_usd', 'supplier_price_eur', 'gambio_price_eur')
    def validate_prices(cls, v):
        """Validate price values."""
        if v is not None and v < 0:
            raise ValueError('Prices cannot be negative')
        return v
    
    @validator('scraping_confidence', 'quality_score')
    def validate_scores(cls, v):
        """Validate score values are within range."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Scores must be between 0 and 100')
        return v


class Product(BaseDBModel):
    """
    Complete product model with all database fields.
    """
    batch_id: UUID = Field(..., description="Upload batch ID")
    supplier_id: UUID = Field(..., description="Supplier ID")
    
    # Supplier product identifiers
    supplier_sku: str = Field(..., description="Supplier SKU")
    supplier_name: Optional[str] = Field(None, description="Original supplier product name")
    supplier_description: Optional[str] = Field(None, description="Original supplier description")
    supplier_price_usd: Optional[Decimal] = Field(None, description="Supplier price in USD")
    supplier_price_eur: Optional[Decimal] = Field(None, description="Supplier price in EUR")
    
    # Manufacturer and invoice-specific fields
    manufacturer: Optional[str] = Field(None, max_length=50, description="Product manufacturer")
    manufacturer_sku: Optional[str] = Field(None, max_length=100, description="Original manufacturer SKU")
    manufacturer_website: Optional[str] = Field(None, max_length=255, description="Manufacturer website")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    quantity_ordered: Optional[int] = Field(None, ge=1, description="Quantity ordered from invoice")
    line_total_usd: Optional[Decimal] = Field(None, ge=0, description="Total line amount USD")
    line_total_eur: Optional[Decimal] = Field(None, ge=0, description="Total line amount EUR")
    origin_country: Optional[str] = Field(None, max_length=50, description="Country of origin")
    tariff_code: Optional[str] = Field(None, max_length=20, description="Tariff code")
    raw_description: Optional[str] = Field(None, description="Original description from invoice")
    line_number: Optional[int] = Field(None, ge=1, description="Line number in invoice")
    
    # Scraped product data
    scraped_name: Optional[str] = Field(None, description="Scraped product name")
    scraped_description: Optional[str] = Field(None, description="Scraped product description")
    scraped_url: Optional[str] = Field(None, description="Scraped product URL")
    scraped_images_urls: Optional[List[str]] = Field(None, description="Scraped image URLs")
    scraping_confidence: int = Field(default=0, description="Scraping confidence score")
    
    # German translations
    german_name: Optional[str] = Field(None, description="German product name")
    german_description: Optional[str] = Field(None, description="German product description")
    german_short_description: Optional[str] = Field(None, description="German short description")
    
    # Gambio export fields
    gambio_category: str = Field(default="Neu: LawnFawn > PD-neu", description="Gambio category path")
    gambio_tax_class_id: int = Field(default=1, description="Gambio tax class ID")
    gambio_model: Optional[str] = Field(None, description="Gambio model number")
    gambio_price_eur: Optional[Decimal] = Field(None, description="Gambio price in EUR")
    gambio_seo_url: Optional[str] = Field(None, description="Gambio SEO URL")
    
    # Processing status and metadata
    status: ProductStatus = Field(..., description="Processing status")
    processing_notes: Optional[str] = Field(None, description="Processing notes")
    quality_score: int = Field(default=0, description="Quality score")
    requires_review: bool = Field(default=False, description="Whether product requires review")
    review_notes: Optional[str] = Field(None, description="Review notes")
    
    @property
    def is_ready_for_export(self) -> bool:
        """Check if product is ready for Gambio export."""
        return (
            self.status == ProductStatus.READY and
            self.german_name is not None and
            self.gambio_price_eur is not None and
            self.quality_score >= 70 and
            not self.requires_review
        )
    
    @property
    def has_images(self) -> bool:
        """Check if product has scraped images."""
        return bool(self.scraped_images_urls and len(self.scraped_images_urls) > 0)
    
    @property
    def confidence_level(self) -> str:
        """Get confidence level description."""
        if self.scraping_confidence >= 90:
            return "High"
        elif self.scraping_confidence >= 70:
            return "Medium"
        elif self.scraping_confidence >= 50:
            return "Low"
        else:
            return "Very Low"


class ProductSummary(BaseCreateModel):
    """
    Summary product model for list views.
    """
    id: UUID = Field(..., description="Product ID")
    batch_id: UUID = Field(..., description="Upload batch ID")
    supplier_sku: str = Field(..., description="Supplier SKU")
    supplier_name: Optional[str] = Field(None, description="Original supplier product name")
    german_name: Optional[str] = Field(None, description="German product name")
    status: ProductStatus = Field(..., description="Processing status")
    scraping_confidence: int = Field(..., description="Scraping confidence score")
    quality_score: int = Field(..., description="Quality score")
    requires_review: bool = Field(..., description="Whether product requires review")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    @property
    def display_name(self) -> str:
        """Get the best available product name for display."""
        return self.german_name or self.supplier_name or self.supplier_sku
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class ProductStats(BaseCreateModel):
    """
    Product statistics model.
    """
    total_products: int = Field(..., description="Total products")
    by_status: dict = Field(..., description="Products grouped by status")
    avg_confidence_score: float = Field(..., description="Average confidence score")
    avg_quality_score: float = Field(..., description="Average quality score")
    products_requiring_review: int = Field(..., description="Products requiring review")
    ready_for_export: int = Field(..., description="Products ready for export")
    with_images: int = Field(..., description="Products with images")
    translated: int = Field(..., description="Products with German translations")


class ProductExportData(BaseCreateModel):
    """
    Product data formatted for Gambio export.
    """
    id: UUID = Field(..., description="Product ID")
    supplier_sku: str = Field(..., description="Supplier SKU")
    gambio_model: str = Field(..., description="Gambio model number")
    german_name: str = Field(..., description="German product name")
    german_description: str = Field(..., description="German product description")
    german_short_description: str = Field(..., description="German short description")
    gambio_category: str = Field(..., description="Gambio category path")
    gambio_price_eur: Decimal = Field(..., description="Gambio price in EUR")
    gambio_tax_class_id: int = Field(..., description="Gambio tax class ID")
    gambio_seo_url: str = Field(..., description="Gambio SEO URL")
    image_filenames: List[str] = Field(..., description="Image filenames for Gambio")
    
    @validator('gambio_seo_url')
    def generate_seo_url(cls, v, values):
        """Generate SEO URL if not provided."""
        if not v and 'german_name' in values:
            # Simple SEO URL generation
            name = values['german_name'].lower()
            # Replace spaces and special characters
            import re
            seo_url = re.sub(r'[^a-z0-9]+', '-', name).strip('-')
            return seo_url[:50]  # Limit length
        return v


class ProductReviewItem(BaseCreateModel):
    """
    Product review item for manual review interface.
    """
    id: UUID = Field(..., description="Product ID")
    supplier_sku: str = Field(..., description="Supplier SKU")
    supplier_name: Optional[str] = Field(None, description="Original supplier product name")
    scraped_name: Optional[str] = Field(None, description="Scraped product name")
    german_name: Optional[str] = Field(None, description="German product name")
    scraping_confidence: int = Field(..., description="Scraping confidence score")
    quality_score: int = Field(..., description="Quality score")
    review_reason: str = Field(..., description="Reason for review")
    scraped_url: Optional[str] = Field(None, description="Scraped product URL")
    image_count: int = Field(default=0, description="Number of images")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
