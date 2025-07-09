"""
Data models for product enrichment system.

This module defines Pydantic models for enrichment workflow data structures,
providing type safety and validation for the complete enrichment process.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from enum import Enum


class EnrichmentMethod(str, Enum):
    """Enumeration of enrichment methods."""
    SEARCH_FIRST_RESULT = "search_first_result"
    DIRECT_URL = "direct_url"
    FALLBACK = "fallback"
    MANUAL = "manual"


class ScrapingStatus(str, Enum):
    """Enumeration of scraping attempt statuses."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"


class EnrichmentStatus(str, Enum):
    """Enumeration of product enrichment statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FirecrawlResponse(BaseModel):
    """Response from Firecrawl API."""
    url: str = Field(..., description="Scraped URL")
    content: str = Field(..., description="HTML content")
    markdown: str = Field(default="", description="Markdown content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Page metadata")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Raw API response")
    success: bool = Field(..., description="Whether scraping was successful")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    credits_used: int = Field(default=1, description="Firecrawl credits consumed")
    processing_time_ms: Optional[int] = Field(default=None, description="Processing time in milliseconds")


class SearchResults(BaseModel):
    """Search results from LawnFawn search."""
    search_url: str = Field(..., description="Search URL used")
    product_links: List[str] = Field(default_factory=list, description="Found product links")
    total_results: int = Field(..., description="Total number of results")
    raw_response: Dict[str, Any] = Field(default_factory=dict, description="Raw search response")
    
    @field_validator('total_results')
    @classmethod
    def validate_total_results(cls, v):
        """Ensure total_results is non-negative."""
        if v < 0:
            raise ValueError("total_results must be non-negative")
        return v


class ProductData(BaseModel):
    """Extracted product data from product page."""
    name: str = Field(..., description="Product name")
    description: str = Field(default="", description="Product description")
    sku: str = Field(default="", description="Found SKU on page")
    image_urls: List[str] = Field(default_factory=list, description="Product image URLs")
    product_url: str = Field(..., description="Product page URL")
    raw_response: Optional[Dict[str, Any]] = Field(default=None, description="Raw page response")
    image_metadata: List[Dict[str, Any]] = Field(default_factory=list, description="Enhanced image metadata")
    
    @field_validator('image_urls')
    @classmethod
    def validate_image_urls(cls, v):
        """Validate image URLs are properly formatted."""
        for url in v:
            if not url.startswith(('http://', 'https://')):
                raise ValueError(f"Invalid image URL format: {url}")
        return v


class EnrichmentData(BaseModel):
    """Complete enrichment data from scraping process."""
    search_url: str = Field(..., description="Search URL used")
    product_url: str = Field(..., description="Product page URL found")
    product_name: str = Field(..., description="Scraped product name")
    description: str = Field(default="", description="Scraped product description")
    image_urls: List[str] = Field(default_factory=list, description="Scraped image URLs")
    confidence_score: int = Field(..., ge=0, le=100, description="Confidence score")
    method: EnrichmentMethod = Field(..., description="Matching method used")
    raw_response: Dict[str, Any] = Field(default_factory=dict, description="Raw Firecrawl response")
    image_metadata: List[Dict[str, Any]] = Field(default_factory=list, description="Enhanced image metadata")
    processing_time_ms: Optional[int] = Field(default=None, description="Total processing time")
    
    @field_validator('confidence_score')
    @classmethod
    def validate_confidence_score(cls, v):
        """Ensure confidence score is within valid range."""
        if not 0 <= v <= 100:
            raise ValueError("confidence_score must be between 0 and 100")
        return v


class ScrapingAttempt(BaseModel):
    """Database model for scraping attempts tracking."""
    id: Optional[UUID] = None
    product_id: UUID = Field(..., description="Product ID")
    attempt_number: int = Field(..., ge=1, description="Attempt number")
    search_url: Optional[str] = Field(None, description="Search URL used")
    method: EnrichmentMethod = Field(..., description="Scraping method")
    status: ScrapingStatus = Field(..., description="Attempt status")
    confidence_score: int = Field(default=0, ge=0, le=100, description="Confidence score")
    firecrawl_response: Optional[Dict[str, Any]] = Field(None, description="Firecrawl response")
    error_message: Optional[str] = Field(None, description="Error message")
    credits_used: int = Field(default=0, ge=0, description="Firecrawl credits used")
    processing_time_ms: Optional[int] = Field(None, ge=0, description="Processing time")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProductEnrichmentResult(BaseModel):
    """Result of individual product enrichment."""
    product_id: UUID = Field(..., description="Product ID")
    success: bool = Field(..., description="Whether enrichment was successful")
    confidence_score: Optional[int] = Field(default=None, ge=0, le=100, description="Confidence score")
    method: Optional[EnrichmentMethod] = Field(default=None, description="Method used")
    product_url: Optional[str] = Field(default=None, description="Found product URL")
    images_found: int = Field(default=0, ge=0, description="Number of images found")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    processing_time_ms: Optional[int] = Field(default=None, ge=0, description="Processing time in milliseconds")
    scraping_attempt_id: Optional[UUID] = Field(default=None, description="ID of scraping attempt record")


class EnrichmentResult(BaseModel):
    """Result of batch enrichment process."""
    batch_id: UUID = Field(..., description="Batch ID")
    total_products: int = Field(..., ge=0, description="Total products processed")
    successful_enrichments: int = Field(..., ge=0, description="Successful enrichments")
    failed_enrichments: int = Field(..., ge=0, description="Failed enrichments")
    results: List[ProductEnrichmentResult] = Field(default_factory=list, description="Individual results")
    processing_time_ms: Optional[int] = Field(default=None, ge=0, description="Total processing time")
    
    # Note: Complex cross-field validation removed for Pydantic v2 compatibility
    # Will be handled at the service layer
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_products == 0:
            return 0.0
        return round((self.successful_enrichments / self.total_products) * 100, 2)
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage."""
        if self.total_products == 0:
            return 0.0
        return round((self.failed_enrichments / self.total_products) * 100, 2)


class EnrichmentRequest(BaseModel):
    """Request model for product enrichment."""
    product_ids: Optional[List[UUID]] = Field(None, description="Specific product IDs to enrich")
    batch_id: Optional[UUID] = Field(None, description="Batch ID to enrich all products")
    force_retry: bool = Field(default=False, description="Force retry of previously failed products")
    max_concurrent: int = Field(default=5, ge=1, le=20, description="Maximum concurrent enrichments")
    confidence_threshold: int = Field(default=30, ge=0, le=100, description="Minimum confidence threshold")
    
    # Note: Complex cross-field validation removed for Pydantic v2 compatibility
    # Will be handled at the API layer


class EnrichmentResponse(BaseModel):
    """Response model for enrichment requests."""
    success: bool = Field(..., description="Whether request was successful")
    message: str = Field(..., description="Response message")
    batch_id: Optional[UUID] = Field(None, description="Batch ID if applicable")
    total_products: int = Field(default=0, ge=0, description="Total products to be enriched")
    processing_started: bool = Field(default=False, description="Whether background processing started")
    estimated_completion_time: Optional[str] = Field(None, description="Estimated completion time")
    error: Optional[str] = Field(None, description="Error message if failed")


class EnrichmentStatus(BaseModel):
    """Enrichment status response."""
    batch_id: UUID = Field(..., description="Batch ID")
    total_products: int = Field(..., ge=0, description="Total products")
    completed_products: int = Field(..., ge=0, description="Completed products")
    failed_products: int = Field(..., ge=0, description="Failed products")
    processing_products: int = Field(..., ge=0, description="Currently processing products")
    pending_products: int = Field(..., ge=0, description="Pending products")
    avg_confidence_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Average confidence score")
    estimated_time_remaining: Optional[str] = Field(None, description="Estimated time remaining")
    last_updated: datetime = Field(..., description="Last status update time")
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_products == 0:
            return 100.0
        completed = self.completed_products + self.failed_products
        return round((completed / self.total_products) * 100, 2)


class ProductEnrichmentDetail(BaseModel):
    """Detailed enrichment information for a product."""
    product_id: UUID = Field(..., description="Product ID")
    supplier_sku: str = Field(..., description="Supplier SKU")
    status: str = Field(..., description="Product status")
    enrichment_status: EnrichmentStatus = Field(..., description="Enrichment status")
    confidence_score: Optional[int] = Field(None, ge=0, le=100, description="Confidence score")
    scraped_name: Optional[str] = Field(None, description="Scraped product name")
    scraped_url: Optional[str] = Field(None, description="Scraped product URL")
    images_found: int = Field(default=0, ge=0, description="Number of images found")
    last_attempt: Optional[datetime] = Field(None, description="Last enrichment attempt")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    requires_review: bool = Field(default=False, description="Whether manual review is required")
    attempt_count: int = Field(default=0, ge=0, description="Number of enrichment attempts")


class EnrichmentAnalytics(BaseModel):
    """Analytics data for enrichment performance."""
    batch_id: Optional[UUID] = Field(None, description="Batch ID filter")
    manufacturer: Optional[str] = Field(None, description="Manufacturer filter")
    total_products: int = Field(..., ge=0, description="Total products")
    enriched_count: int = Field(..., ge=0, description="Successfully enriched products")
    failed_count: int = Field(..., ge=0, description="Failed enrichment products")
    review_required_count: int = Field(..., ge=0, description="Products requiring manual review")
    avg_confidence_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Average confidence score")
    avg_processing_time_ms: float = Field(default=0.0, ge=0.0, description="Average processing time")
    total_credits_used: int = Field(default=0, ge=0, description="Total Firecrawl credits used")
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_products == 0:
            return 0.0
        return round((self.enriched_count / self.total_products) * 100, 2)
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage."""
        if self.total_products == 0:
            return 0.0
        return round((self.failed_count / self.total_products) * 100, 2)


class EnrichmentConfig(BaseModel):
    """Configuration for enrichment process."""
    firecrawl_api_key: str = Field(..., description="Firecrawl API key")
    firecrawl_base_url: str = Field(default="https://api.firecrawl.dev", description="Firecrawl base URL")
    firecrawl_timeout: int = Field(default=30, ge=1, le=300, description="Firecrawl timeout in seconds")
    max_concurrent_requests: int = Field(default=5, ge=1, le=20, description="Maximum concurrent requests")
    retry_attempts: int = Field(default=3, ge=1, le=10, description="Number of retry attempts")
    retry_delay: int = Field(default=2, ge=1, le=60, description="Retry delay in seconds")
    confidence_thresholds: Dict[str, int] = Field(
        default_factory=lambda: {
            "exact_match": 100,
            "first_result_match": 90,
            "first_result_no_match": 60,
            "fallback": 30
        },
        description="Confidence score thresholds"
    )
    rate_limit_requests_per_minute: int = Field(default=30, ge=1, le=1000, description="Rate limit per minute")
    lawnfawn_base_url: str = Field(default="https://www.lawnfawn.com", description="LawnFawn base URL")
    sku_extraction_pattern: str = Field(default=r'LF[-]?(\d+)', description="SKU extraction regex pattern")
