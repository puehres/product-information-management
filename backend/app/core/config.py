"""
Configuration management for the Universal Product Automation System.

This module provides type-safe configuration management using Pydantic settings
with environment variable support.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden via environment variables.
    For example, DATABASE_URL environment variable will override database_url.
    """
    
    # Database Configuration (Legacy - kept for compatibility)
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/product_automation",
        description="PostgreSQL database connection URL"
    )
    
    # Supabase Configuration
    supabase_url: str = Field(
        default="https://your-project-ref.supabase.co",
        description="Supabase project URL"
    )
    
    supabase_anon_key: str = Field(
        default="your-anon-key-here",
        description="Supabase anonymous key for client-side operations"
    )
    
    supabase_service_key: str = Field(
        default="your-service-key-here",
        description="Supabase service role key for server-side operations"
    )
    
    supabase_database_url: str = Field(
        default="postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres",
        description="Direct PostgreSQL connection URL for Supabase database"
    )
    
    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL for caching"
    )
    
    # API Keys (for future tasks)
    firecrawl_api_key: Optional[str] = Field(
        default=None,
        description="Firecrawl API key for web scraping"
    )
    
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for translations and content generation"
    )
    
    # Development Configuration
    debug: bool = Field(
        default=True,
        description="Enable debug mode for development"
    )
    
    log_level: str = Field(
        default="DEBUG",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    environment: str = Field(
        default="development",
        description="Application environment (development, staging, production)"
    )
    
    # Server Configuration
    backend_port: int = Field(
        default=8000,
        description="Backend server port"
    )
    
    frontend_port: int = Field(
        default=3000,
        description="Frontend development server port"
    )
    
    # CORS Configuration
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins for frontend communication"
    )
    
    # Application Configuration
    app_name: str = Field(
        default="Universal Product Automation System",
        description="Application name"
    )
    
    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )
    
    # File Processing Configuration
    max_file_size: int = Field(
        default=50 * 1024 * 1024,  # 50MB
        description="Maximum file size for uploads in bytes"
    )
    
    supported_file_types: list[str] = Field(
        default=[".csv", ".xlsx", ".xls", ".pdf"],
        description="Supported file types for product data import"
    )
    
    # Image Processing Configuration
    min_image_dimension: int = Field(
        default=1000,
        description="Minimum image dimension (longest edge) for quality validation"
    )
    
    image_formats: list[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".webp", ".gif"],
        description="Supported image formats for processing"
    )
    
    # Scraping Configuration
    scraping_delay: float = Field(
        default=1.0,
        description="Delay between scraping requests in seconds"
    )
    
    scraping_timeout: int = Field(
        default=30,
        description="Timeout for scraping requests in seconds"
    )
    
    # Tax Configuration (MVP - hardcoded)
    gambio_default_tax_class_id: int = Field(
        default=1,
        description="Default tax class ID for Gambio exports"
    )
    
    # Currency Configuration
    default_currency_from: str = Field(
        default="USD",
        description="Default source currency for conversions"
    )
    
    default_currency_to: str = Field(
        default="EUR",
        description="Default target currency for conversions"
    )
    
    default_exchange_rate: float = Field(
        default=0.85,
        description="Default USD to EUR exchange rate"
    )
    
    # AWS S3 Configuration
    aws_access_key_id: Optional[str] = Field(
        default=None,
        description="AWS access key ID for S3 operations"
    )
    
    aws_secret_access_key: Optional[str] = Field(
        default=None,
        description="AWS secret access key for S3 operations"
    )
    
    aws_region: str = Field(
        default="eu-north-1",
        description="AWS region - Stockholm for EU compliance"
    )
    
    s3_bucket_name: str = Field(
        default="sw-product-processing-bucket",
        description="S3 bucket name for file storage"
    )
    
    s3_invoice_prefix: str = Field(
        default="invoices",
        description="S3 prefix for invoice storage"
    )
    
    # Invoice Processing Configuration
    invoice_download_expiration: int = Field(
        default=3600,
        description="Download URL expiration time in seconds (1 hour)"
    )
    
    temp_file_cleanup: bool = Field(
        default=True,
        description="Automatically cleanup temporary files after processing"
    )
    
    # Supplier Detection Configuration
    supplier_detection_confidence_threshold: float = Field(
        default=0.5,
        description="Minimum confidence threshold for supplier detection"
    )
    
    supported_suppliers: list[str] = Field(
        default=["lawnfawn", "craftlines", "mama-elephant"],
        description="List of supported supplier codes for invoice processing"
    )
    
    # Product Enrichment Configuration
    firecrawl_base_url: str = Field(
        default="https://api.firecrawl.dev",
        description="Firecrawl API base URL"
    )
    
    firecrawl_timeout: int = Field(
        default=30,
        description="Firecrawl API timeout in seconds"
    )
    
    firecrawl_max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for Firecrawl API"
    )
    
    firecrawl_retry_delay: int = Field(
        default=2,
        description="Retry delay for Firecrawl API in seconds"
    )
    
    enrichment_max_concurrent: int = Field(
        default=5,
        description="Maximum concurrent enrichment processes"
    )
    
    enrichment_batch_size: int = Field(
        default=10,
        description="Batch size for enrichment processing"
    )
    
    enrichment_timeout: int = Field(
        default=300,
        description="Enrichment process timeout in seconds"
    )
    
    enrichment_retry_attempts: int = Field(
        default=3,
        description="Number of retry attempts for failed enrichments"
    )
    
    enrichment_retry_delay: int = Field(
        default=5,
        description="Delay between enrichment retry attempts in seconds"
    )
    
    # LawnFawn Specific Configuration
    lawnfawn_base_url: str = Field(
        default="https://www.lawnfawn.com",
        description="LawnFawn website base URL"
    )
    
    lawnfawn_search_delay: int = Field(
        default=2,
        description="Delay between LawnFawn search requests in seconds"
    )
    
    lawnfawn_page_timeout: int = Field(
        default=15,
        description="Timeout for LawnFawn page loading in seconds"
    )
    
    # Confidence Score Configuration
    confidence_exact_match: int = Field(
        default=100,
        description="Confidence score for exact SKU matches"
    )
    
    confidence_first_result_match: int = Field(
        default=90,
        description="Confidence score for first result with SKU match"
    )
    
    confidence_first_result_no_match: int = Field(
        default=60,
        description="Confidence score for first result without SKU match"
    )
    
    confidence_fallback: int = Field(
        default=30,
        description="Fallback confidence score"
    )
    
    confidence_minimum_threshold: int = Field(
        default=30,
        description="Minimum confidence threshold for accepting results"
    )
    
    # Rate Limiting Configuration
    scraping_requests_per_minute: int = Field(
        default=30,
        description="Maximum scraping requests per minute"
    )
    
    scraping_burst_limit: int = Field(
        default=10,
        description="Maximum burst requests for scraping"
    )
    
    # Image Download Configuration (for future Task 5)
    image_download_enabled: bool = Field(
        default=False,
        description="Enable automatic image downloading"
    )
    
    image_download_max_concurrent: int = Field(
        default=3,
        description="Maximum concurrent image downloads"
    )
    
    image_download_timeout: int = Field(
        default=30,
        description="Image download timeout in seconds"
    )
    
    image_download_retry_attempts: int = Field(
        default=3,
        description="Number of retry attempts for failed image downloads"
    )
    
    image_download_max_file_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum image file size for downloads in bytes"
    )
    
    image_download_allowed_formats: str = Field(
        default="jpg,jpeg,png,webp,gif",
        description="Allowed image formats for downloads (comma-separated)"
    )
    
    image_storage_path: str = Field(
        default="products/{product_id}/images/",
        description="S3 storage path pattern for product images"
    )
    
    image_quality_check: bool = Field(
        default=True,
        description="Enable image quality validation"
    )
    
    image_resize_enabled: bool = Field(
        default=True,
        description="Enable automatic image resizing"
    )
    
    image_max_dimension: int = Field(
        default=2048,
        description="Maximum image dimension for resizing"
    )
    
    class Config:
        """Pydantic configuration."""
        # Only load .env file if not running tests
        env_file = ".env" if not os.getenv("PYTEST_RUNNING") else None
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings instance.
    
    Returns:
        Settings: Application settings instance.
    """
    return settings
