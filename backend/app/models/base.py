"""
Base models for the Universal Product Automation System.

This module provides base classes and common types used across all database models.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class FileType(str, Enum):
    """File types supported for product data import."""
    PDF = "pdf"
    CSV = "csv"
    XLSX = "xlsx"
    MANUAL = "manual"


class BatchStatus(str, Enum):
    """Processing status for upload batches."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEW_REQUIRED = "review_required"


class ProductStatus(str, Enum):
    """Processing status for individual products."""
    DRAFT = "draft"
    PROCESSING = "processing"
    SCRAPED = "scraped"
    TRANSLATED = "translated"
    READY = "ready"
    EXPORTED = "exported"
    FAILED = "failed"


class ImageType(str, Enum):
    """Types of product images."""
    MAIN = "main"
    ADDITIONAL = "additional"
    DETAIL = "detail"
    MANUAL_UPLOAD = "manual_upload"


class ProcessingStatus(str, Enum):
    """Processing status for images and other assets."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BaseDBModel(BaseModel):
    """
    Base model for all database entities.
    
    Provides common fields and configuration for all database models.
    """
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class BaseCreateModel(BaseModel):
    """
    Base model for creating database entities.
    
    Excludes auto-generated fields like id and timestamps.
    """
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class BaseUpdateModel(BaseModel):
    """
    Base model for updating database entities.
    
    All fields are optional for partial updates.
    """
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class PaginationParams(BaseModel):
    """
    Parameters for paginated queries.
    """
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit for database queries."""
        return self.page_size


class PaginatedResponse(BaseModel):
    """
    Generic paginated response model.
    """
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    
    @classmethod
    def create(
        cls,
        items: List[Any],
        total: int,
        pagination: PaginationParams
    ) -> "PaginatedResponse":
        """
        Create a paginated response from items and pagination parameters.
        
        Args:
            items: List of items for current page.
            total: Total number of items across all pages.
            pagination: Pagination parameters used for the query.
            
        Returns:
            PaginatedResponse: Formatted paginated response.
        """
        total_pages = (total + pagination.page_size - 1) // pagination.page_size
        
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next=pagination.page < total_pages,
            has_previous=pagination.page > 1
        )


class HealthCheckResponse(BaseModel):
    """
    Health check response model.
    """
    status: str = Field(description="Overall health status")
    timestamp: datetime = Field(description="Health check timestamp")
    services: Dict[str, Any] = Field(description="Individual service health status")
    version: str = Field(description="Application version")
    environment: str = Field(description="Environment name")
