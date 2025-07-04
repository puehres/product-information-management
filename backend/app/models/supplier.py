"""
Supplier models for the Universal Product Automation System.

This module defines Pydantic models for supplier configuration and management.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import Field, validator
from .base import BaseDBModel, BaseCreateModel, BaseUpdateModel


class SupplierBase(BaseCreateModel):
    """
    Base supplier model with common fields.
    """
    name: str = Field(..., max_length=100, description="Supplier name")
    code: str = Field(..., max_length=10, description="Unique supplier code")
    website_url: Optional[str] = Field(None, max_length=255, description="Supplier website URL")
    identifier_type: str = Field(default="sku", max_length=50, description="Product identifier type")
    scraping_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Scraping configuration")
    search_url_template: Optional[str] = Field(None, max_length=500, description="Search URL template")
    active: bool = Field(default=True, description="Whether supplier is active")
    
    @validator('code')
    def validate_code(cls, v):
        """Validate supplier code format."""
        if not v or not v.strip():
            raise ValueError('Supplier code cannot be empty')
        return v.upper().strip()
    
    @validator('name')
    def validate_name(cls, v):
        """Validate supplier name."""
        if not v or not v.strip():
            raise ValueError('Supplier name cannot be empty')
        return v.strip()
    
    @validator('website_url')
    def validate_website_url(cls, v):
        """Validate website URL format."""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Website URL must start with http:// or https://')
        return v
    
    @validator('search_url_template')
    def validate_search_url_template(cls, v):
        """Validate search URL template contains placeholder."""
        if v and '{sku}' not in v:
            raise ValueError('Search URL template must contain {sku} placeholder')
        return v


class SupplierCreate(SupplierBase):
    """
    Model for creating a new supplier.
    """
    pass


class SupplierUpdate(BaseUpdateModel):
    """
    Model for updating an existing supplier.
    
    All fields are optional for partial updates.
    """
    name: Optional[str] = Field(None, max_length=100, description="Supplier name")
    code: Optional[str] = Field(None, max_length=10, description="Unique supplier code")
    website_url: Optional[str] = Field(None, max_length=255, description="Supplier website URL")
    identifier_type: Optional[str] = Field(None, max_length=50, description="Product identifier type")
    scraping_config: Optional[Dict[str, Any]] = Field(None, description="Scraping configuration")
    search_url_template: Optional[str] = Field(None, max_length=500, description="Search URL template")
    active: Optional[bool] = Field(None, description="Whether supplier is active")
    
    @validator('code')
    def validate_code(cls, v):
        """Validate supplier code format."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Supplier code cannot be empty')
            return v.upper().strip()
        return v
    
    @validator('name')
    def validate_name(cls, v):
        """Validate supplier name."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Supplier name cannot be empty')
            return v.strip()
        return v
    
    @validator('website_url')
    def validate_website_url(cls, v):
        """Validate website URL format."""
        if v is not None and v and not v.startswith(('http://', 'https://')):
            raise ValueError('Website URL must start with http:// or https://')
        return v
    
    @validator('search_url_template')
    def validate_search_url_template(cls, v):
        """Validate search URL template contains placeholder."""
        if v is not None and v and '{sku}' not in v:
            raise ValueError('Search URL template must contain {sku} placeholder')
        return v


class Supplier(BaseDBModel):
    """
    Complete supplier model with all database fields.
    """
    name: str = Field(..., description="Supplier name")
    code: str = Field(..., description="Unique supplier code")
    website_url: Optional[str] = Field(None, description="Supplier website URL")
    identifier_type: str = Field(..., description="Product identifier type")
    scraping_config: Dict[str, Any] = Field(default_factory=dict, description="Scraping configuration")
    search_url_template: Optional[str] = Field(None, description="Search URL template")
    active: bool = Field(..., description="Whether supplier is active")


class SupplierSummary(BaseCreateModel):
    """
    Summary supplier model for list views.
    """
    id: UUID = Field(..., description="Supplier ID")
    name: str = Field(..., description="Supplier name")
    code: str = Field(..., description="Unique supplier code")
    website_url: Optional[str] = Field(None, description="Supplier website URL")
    active: bool = Field(..., description="Whether supplier is active")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class SupplierStats(BaseCreateModel):
    """
    Supplier statistics model.
    """
    supplier_id: UUID = Field(..., description="Supplier ID")
    total_batches: int = Field(default=0, description="Total upload batches")
    total_products: int = Field(default=0, description="Total products processed")
    successful_products: int = Field(default=0, description="Successfully processed products")
    failed_products: int = Field(default=0, description="Failed products")
    avg_processing_time_minutes: Optional[float] = Field(None, description="Average processing time in minutes")
    last_batch_date: Optional[str] = Field(None, description="Date of last batch upload")
    success_rate: float = Field(default=0.0, description="Success rate percentage")
    
    @validator('success_rate')
    def calculate_success_rate(cls, v, values):
        """Calculate success rate from successful and total products."""
        total = values.get('total_products', 0)
        successful = values.get('successful_products', 0)
        
        if total > 0:
            return round((successful / total) * 100, 2)
        return 0.0


class SupplierConfigValidation(BaseCreateModel):
    """
    Model for validating supplier configuration.
    """
    supplier_id: UUID = Field(..., description="Supplier ID")
    config_valid: bool = Field(..., description="Whether configuration is valid")
    validation_errors: list[str] = Field(default_factory=list, description="Validation error messages")
    test_results: Dict[str, Any] = Field(default_factory=dict, description="Configuration test results")
    
    @property
    def is_ready_for_processing(self) -> bool:
        """Check if supplier is ready for product processing."""
        return self.config_valid and len(self.validation_errors) == 0
