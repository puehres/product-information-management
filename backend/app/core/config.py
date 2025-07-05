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
