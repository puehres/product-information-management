"""
Image models for the Universal Product Automation System.

This module defines Pydantic models for image processing and management.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import Field, validator
from .base import BaseDBModel, BaseCreateModel, BaseUpdateModel, ImageType, ProcessingStatus


class ImageBase(BaseCreateModel):
    """
    Base image model with common fields.
    """
    product_id: UUID = Field(..., description="Product ID")
    original_url: Optional[str] = Field(None, max_length=1000, description="Original image URL")
    image_type: ImageType = Field(default=ImageType.MAIN, description="Type of image")
    sequence_number: int = Field(default=1, ge=1, description="Sequence number for ordering")
    
    @validator('original_url')
    def validate_original_url(cls, v):
        """Validate original URL format."""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Original URL must start with http:// or https://')
        return v
    
    @validator('sequence_number')
    def validate_sequence_number(cls, v):
        """Validate sequence number is positive."""
        if v < 1:
            raise ValueError('Sequence number must be positive')
        return v


class ImageCreate(ImageBase):
    """
    Model for creating a new image.
    """
    pass


class ImageUpdate(BaseUpdateModel):
    """
    Model for updating an existing image.
    
    All fields are optional for partial updates.
    """
    original_url: Optional[str] = Field(None, max_length=1000, description="Original image URL")
    s3_key: Optional[str] = Field(None, max_length=500, description="S3 object key")
    s3_url: Optional[str] = Field(None, max_length=1000, description="S3 URL")
    filename: Optional[str] = Field(None, max_length=255, description="Standardized filename")
    image_type: Optional[ImageType] = Field(None, description="Type of image")
    sequence_number: Optional[int] = Field(None, ge=1, description="Sequence number for ordering")
    width: Optional[int] = Field(None, gt=0, description="Image width in pixels")
    height: Optional[int] = Field(None, gt=0, description="Image height in pixels")
    file_size: Optional[int] = Field(None, gt=0, description="File size in bytes")
    format: Optional[str] = Field(None, max_length=10, description="Image format")
    processing_status: Optional[ProcessingStatus] = Field(None, description="Processing status")
    processing_error: Optional[str] = Field(None, description="Processing error message")
    quality_check_passed: Optional[bool] = Field(None, description="Quality check result")
    quality_warnings: Optional[List[str]] = Field(None, description="Quality warnings")
    
    @validator('original_url', 's3_url')
    def validate_urls(cls, v):
        """Validate URL formats."""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('URLs must start with http:// or https://')
        return v
    
    @validator('sequence_number')
    def validate_sequence_number(cls, v):
        """Validate sequence number is positive."""
        if v is not None and v < 1:
            raise ValueError('Sequence number must be positive')
        return v
    
    @validator('width', 'height')
    def validate_dimensions(cls, v):
        """Validate image dimensions are positive."""
        if v is not None and v <= 0:
            raise ValueError('Image dimensions must be positive')
        return v
    
    @validator('file_size')
    def validate_file_size(cls, v):
        """Validate file size is reasonable."""
        if v is not None:
            if v <= 0:
                raise ValueError('File size must be positive')
            if v > 50 * 1024 * 1024:  # 50MB limit
                raise ValueError('File size cannot exceed 50MB')
        return v


class Image(BaseDBModel):
    """
    Complete image model with all database fields.
    """
    product_id: UUID = Field(..., description="Product ID")
    
    # Image source and processing
    original_url: Optional[str] = Field(None, description="Original image URL")
    s3_key: Optional[str] = Field(None, description="S3 object key")
    s3_url: Optional[str] = Field(None, description="S3 URL")
    filename: Optional[str] = Field(None, description="Standardized filename")
    
    # Image properties
    image_type: ImageType = Field(..., description="Type of image")
    sequence_number: int = Field(..., description="Sequence number for ordering")
    width: Optional[int] = Field(None, description="Image width in pixels")
    height: Optional[int] = Field(None, description="Image height in pixels")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    format: Optional[str] = Field(None, description="Image format")
    
    # Processing status
    processing_status: ProcessingStatus = Field(..., description="Processing status")
    processing_error: Optional[str] = Field(None, description="Processing error message")
    quality_check_passed: bool = Field(default=False, description="Quality check result")
    quality_warnings: Optional[List[str]] = Field(None, description="Quality warnings")
    
    @property
    def is_processed(self) -> bool:
        """Check if image has been successfully processed."""
        return self.processing_status == ProcessingStatus.COMPLETED and self.s3_url is not None
    
    @property
    def meets_quality_standards(self) -> bool:
        """Check if image meets quality standards."""
        return (
            self.quality_check_passed and
            self.width is not None and
            self.height is not None and
            min(self.width, self.height) >= 1000
        )
    
    @property
    def aspect_ratio(self) -> Optional[float]:
        """Calculate image aspect ratio."""
        if self.width and self.height:
            return round(self.width / self.height, 2)
        return None
    
    @property
    def file_size_mb(self) -> Optional[float]:
        """Get file size in megabytes."""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return None
    
    @property
    def gambio_filename(self) -> str:
        """Generate Gambio-compatible filename."""
        if self.filename:
            return self.filename
        
        # Generate filename based on product and sequence
        base_name = f"product_{str(self.product_id)[:8]}_{self.image_type.value}_{self.sequence_number:02d}"
        extension = "jpeg"  # Default to JPEG for Gambio compatibility
        
        if self.format:
            extension = self.format.lower()
            if extension == "jpg":
                extension = "jpeg"
        
        return f"{base_name}.{extension}"


class ImageSummary(BaseCreateModel):
    """
    Summary image model for list views.
    """
    id: UUID = Field(..., description="Image ID")
    product_id: UUID = Field(..., description="Product ID")
    image_type: ImageType = Field(..., description="Type of image")
    sequence_number: int = Field(..., description="Sequence number")
    width: Optional[int] = Field(None, description="Image width")
    height: Optional[int] = Field(None, description="Image height")
    processing_status: ProcessingStatus = Field(..., description="Processing status")
    quality_check_passed: bool = Field(..., description="Quality check result")
    s3_url: Optional[str] = Field(None, description="S3 URL")
    
    @property
    def dimensions_text(self) -> str:
        """Get formatted dimensions text."""
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return "Unknown"
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class ImageProcessingRequest(BaseCreateModel):
    """
    Image processing request model.
    """
    image_id: UUID = Field(..., description="Image ID")
    original_url: str = Field(..., description="Original image URL")
    target_format: str = Field(default="jpeg", description="Target image format")
    target_quality: int = Field(default=85, ge=1, le=100, description="Target image quality")
    min_dimension: int = Field(default=1000, ge=100, description="Minimum dimension requirement")
    max_file_size_mb: float = Field(default=5.0, gt=0, description="Maximum file size in MB")


class ImageProcessingResult(BaseCreateModel):
    """
    Image processing result model.
    """
    image_id: UUID = Field(..., description="Image ID")
    success: bool = Field(..., description="Processing success status")
    s3_key: Optional[str] = Field(None, description="S3 object key")
    s3_url: Optional[str] = Field(None, description="S3 URL")
    filename: Optional[str] = Field(None, description="Generated filename")
    width: Optional[int] = Field(None, description="Processed image width")
    height: Optional[int] = Field(None, description="Processed image height")
    file_size: Optional[int] = Field(None, description="Processed file size")
    format: Optional[str] = Field(None, description="Processed image format")
    quality_check_passed: bool = Field(default=False, description="Quality check result")
    quality_warnings: List[str] = Field(default_factory=list, description="Quality warnings")
    processing_time_seconds: Optional[float] = Field(None, description="Processing time")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class ImageStats(BaseCreateModel):
    """
    Image statistics model.
    """
    total_images: int = Field(..., description="Total images")
    by_status: dict = Field(..., description="Images grouped by processing status")
    by_type: dict = Field(..., description="Images grouped by type")
    quality_passed: int = Field(..., description="Images passing quality check")
    avg_file_size_mb: float = Field(..., description="Average file size in MB")
    avg_dimensions: dict = Field(..., description="Average width and height")
    processed_images: int = Field(..., description="Successfully processed images")
    failed_images: int = Field(..., description="Failed processing images")


class ImageBatchOperation(BaseCreateModel):
    """
    Batch image operation model.
    """
    product_ids: List[UUID] = Field(..., description="Product IDs to process")
    operation: str = Field(..., description="Operation type (process, reprocess, delete)")
    parameters: dict = Field(default_factory=dict, description="Operation parameters")
    
    @validator('operation')
    def validate_operation(cls, v):
        """Validate operation type."""
        allowed_operations = ['process', 'reprocess', 'delete', 'quality_check']
        if v not in allowed_operations:
            raise ValueError(f'Operation must be one of: {", ".join(allowed_operations)}')
        return v


class ImageQualityReport(BaseCreateModel):
    """
    Image quality assessment report.
    """
    image_id: UUID = Field(..., description="Image ID")
    overall_score: int = Field(..., ge=0, le=100, description="Overall quality score")
    dimension_score: int = Field(..., ge=0, le=100, description="Dimension quality score")
    file_size_score: int = Field(..., ge=0, le=100, description="File size quality score")
    format_score: int = Field(..., ge=0, le=100, description="Format quality score")
    warnings: List[str] = Field(default_factory=list, description="Quality warnings")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    meets_standards: bool = Field(..., description="Whether image meets quality standards")
