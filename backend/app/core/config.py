"""
Configuration management for the Universal Product Automation System.

This module provides type-safe configuration management using Pydantic settings
with environment variable support.
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden via environment variables.
    For example, DATABASE_URL environment variable will override database_url.
    """
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/product_automation",
        description="PostgreSQL database connection URL"
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
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
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
