"""
Upload batch models for the Universal Product Automation System.

This module defines Pydantic models for upload batch tracking and management.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from pydantic import Field, validator
from .base import BaseDBModel, BaseCreateModel, BaseUpdateModel, FileType, BatchStatus


class UploadBatchBase(BaseCreateModel):
    """
    Base upload batch model with common fields.
    """
    supplier_id: UUID = Field(..., description="Supplier ID")
    batch_name: str = Field(..., max_length=255, description="Batch name")
    file_type: FileType = Field(..., description="Type of uploaded file")
    file_path: Optional[str] = Field(None, max_length=500, description="Path to uploaded file")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional batch metadata")
    
    @validator('batch_name')
    def validate_batch_name(cls, v):
        """Validate batch name."""
        if not v or not v.strip():
            raise ValueError('Batch name cannot be empty')
        return v.strip()
    
    @validator('file_size')
    def validate_file_size(cls, v):
        """Validate file size is reasonable."""
        if v is not None and v > 100 * 1024 * 1024:  # 100MB limit
            raise ValueError('File size cannot exceed 100MB')
        return v


class UploadBatchCreate(UploadBatchBase):
    """
    Model for creating a new upload batch.
    """
    pass


class UploadBatchUpdate(BaseUpdateModel):
    """
    Model for updating an existing upload batch.
    
    All fields are optional for partial updates.
    """
    batch_name: Optional[str] = Field(None, max_length=255, description="Batch name")
    file_type: Optional[FileType] = Field(None, description="Type of uploaded file")
    file_path: Optional[str] = Field(None, max_length=500, description="Path to uploaded file")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    status: Optional[BatchStatus] = Field(None, description="Processing status")
    total_products: Optional[int] = Field(None, ge=0, description="Total products in batch")
    processed_products: Optional[int] = Field(None, ge=0, description="Number of processed products")
    failed_products: Optional[int] = Field(None, ge=0, description="Number of failed products")
    processing_started_at: Optional[datetime] = Field(None, description="Processing start timestamp")
    processing_completed_at: Optional[datetime] = Field(None, description="Processing completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional batch metadata")
    
    @validator('batch_name')
    def validate_batch_name(cls, v):
        """Validate batch name."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Batch name cannot be empty')
            return v.strip()
        return v
    
    @validator('file_size')
    def validate_file_size(cls, v):
        """Validate file size is reasonable."""
        if v is not None and v > 100 * 1024 * 1024:  # 100MB limit
            raise ValueError('File size cannot exceed 100MB')
        return v
    
    @validator('processed_products')
    def validate_processed_products(cls, v, values):
        """Validate processed products doesn't exceed total."""
        if v is not None and 'total_products' in values and values['total_products'] is not None:
            if v > values['total_products']:
                raise ValueError('Processed products cannot exceed total products')
        return v
    
    @validator('failed_products')
    def validate_failed_products(cls, v, values):
        """Validate failed products doesn't exceed total."""
        if v is not None and 'total_products' in values and values['total_products'] is not None:
            if v > values['total_products']:
                raise ValueError('Failed products cannot exceed total products')
        return v


class UploadBatch(BaseDBModel):
    """
    Complete upload batch model with all database fields.
    """
    supplier_id: UUID = Field(..., description="Supplier ID")
    batch_name: str = Field(..., description="Batch name")
    file_type: FileType = Field(..., description="Type of uploaded file")
    file_path: Optional[str] = Field(None, description="Path to uploaded file")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    status: BatchStatus = Field(..., description="Processing status")
    total_products: int = Field(default=0, description="Total products in batch")
    processed_products: int = Field(default=0, description="Number of processed products")
    failed_products: int = Field(default=0, description="Number of failed products")
    processing_started_at: Optional[datetime] = Field(None, description="Processing start timestamp")
    processing_completed_at: Optional[datetime] = Field(None, description="Processing completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional batch metadata")
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_products == 0:
            return 0.0
        successful = self.total_products - self.failed_products
        return round((successful / self.total_products) * 100, 2)
    
    @property
    def processing_duration_minutes(self) -> Optional[float]:
        """Calculate processing duration in minutes."""
        if self.processing_started_at and self.processing_completed_at:
            duration = self.processing_completed_at - self.processing_started_at
            return round(duration.total_seconds() / 60, 2)
        return None
    
    @property
    def is_completed(self) -> bool:
        """Check if batch processing is completed."""
        return self.status in [BatchStatus.COMPLETED, BatchStatus.FAILED]
    
    @property
    def is_processing(self) -> bool:
        """Check if batch is currently being processed."""
        return self.status == BatchStatus.PROCESSING


class UploadBatchSummary(BaseCreateModel):
    """
    Summary upload batch model for list views.
    """
    id: UUID = Field(..., description="Batch ID")
    supplier_id: UUID = Field(..., description="Supplier ID")
    batch_name: str = Field(..., description="Batch name")
    file_type: FileType = Field(..., description="Type of uploaded file")
    status: BatchStatus = Field(..., description="Processing status")
    total_products: int = Field(..., description="Total products in batch")
    processed_products: int = Field(..., description="Number of processed products")
    failed_products: int = Field(..., description="Number of failed products")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_products == 0:
            return 0.0
        successful = self.total_products - self.failed_products
        return round((successful / self.total_products) * 100, 2)
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class UploadBatchStats(BaseCreateModel):
    """
    Upload batch statistics model.
    """
    batch_id: UUID = Field(..., description="Batch ID")
    total_products: int = Field(..., description="Total products in batch")
    processed_products: int = Field(..., description="Successfully processed products")
    failed_products: int = Field(..., description="Failed products")
    pending_products: int = Field(..., description="Products pending processing")
    success_rate: float = Field(..., description="Success rate percentage")
    avg_processing_time_seconds: Optional[float] = Field(None, description="Average processing time per product")
    estimated_completion_minutes: Optional[float] = Field(None, description="Estimated time to completion")
    
    @validator('success_rate')
    def calculate_success_rate(cls, v, values):
        """Calculate success rate from processed and total products."""
        total = values.get('total_products', 0)
        processed = values.get('processed_products', 0)
        
        if total > 0:
            return round((processed / total) * 100, 2)
        return 0.0
    
    @validator('pending_products')
    def calculate_pending_products(cls, v, values):
        """Calculate pending products from total and processed."""
        total = values.get('total_products', 0)
        processed = values.get('processed_products', 0)
        failed = values.get('failed_products', 0)
        
        return max(0, total - processed - failed)


class BatchProcessingProgress(BaseCreateModel):
    """
    Real-time batch processing progress model.
    """
    batch_id: UUID = Field(..., description="Batch ID")
    current_product: int = Field(..., description="Currently processing product number")
    total_products: int = Field(..., description="Total products to process")
    current_step: str = Field(..., description="Current processing step")
    progress_percentage: float = Field(..., description="Overall progress percentage")
    estimated_remaining_minutes: Optional[float] = Field(None, description="Estimated remaining time")
    last_updated: datetime = Field(..., description="Last progress update timestamp")
    
    @validator('progress_percentage')
    def calculate_progress_percentage(cls, v, values):
        """Calculate progress percentage from current and total products."""
        current = values.get('current_product', 0)
        total = values.get('total_products', 1)
        
        if total > 0:
            return round((current / total) * 100, 2)
        return 0.0
