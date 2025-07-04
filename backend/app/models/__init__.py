"""
Models package for the Universal Product Automation System.

This package contains all Pydantic models for database entities and API operations.
"""

# Base models and enums
from .base import (
    BaseDBModel,
    BaseCreateModel,
    BaseUpdateModel,
    FileType,
    BatchStatus,
    ProductStatus,
    ImageType,
    ProcessingStatus,
    PaginationParams,
    PaginatedResponse,
    HealthCheckResponse
)

# Supplier models
from .supplier import (
    Supplier,
    SupplierCreate,
    SupplierUpdate,
    SupplierSummary,
    SupplierStats,
    SupplierConfigValidation
)

# Upload batch models
from .upload_batch import (
    UploadBatch,
    UploadBatchCreate,
    UploadBatchUpdate,
    UploadBatchSummary,
    UploadBatchStats,
    BatchProcessingProgress
)

# Product models
from .product import (
    Product,
    ProductCreate,
    ProductUpdate,
    ProductSummary,
    ProductStats,
    ProductExportData,
    ProductReviewItem
)

# Image models
from .image import (
    Image,
    ImageCreate,
    ImageUpdate,
    ImageSummary,
    ImageProcessingRequest,
    ImageProcessingResult,
    ImageStats,
    ImageBatchOperation,
    ImageQualityReport
)

__all__ = [
    # Base models and enums
    "BaseDBModel",
    "BaseCreateModel", 
    "BaseUpdateModel",
    "FileType",
    "BatchStatus",
    "ProductStatus",
    "ImageType",
    "ProcessingStatus",
    "PaginationParams",
    "PaginatedResponse",
    "HealthCheckResponse",
    
    # Supplier models
    "Supplier",
    "SupplierCreate",
    "SupplierUpdate",
    "SupplierSummary",
    "SupplierStats",
    "SupplierConfigValidation",
    
    # Upload batch models
    "UploadBatch",
    "UploadBatchCreate",
    "UploadBatchUpdate",
    "UploadBatchSummary",
    "UploadBatchStats",
    "BatchProcessingProgress",
    
    # Product models
    "Product",
    "ProductCreate",
    "ProductUpdate",
    "ProductSummary",
    "ProductStats",
    "ProductExportData",
    "ProductReviewItem",
    
    # Image models
    "Image",
    "ImageCreate",
    "ImageUpdate",
    "ImageSummary",
    "ImageProcessingRequest",
    "ImageProcessingResult",
    "ImageStats",
    "ImageBatchOperation",
    "ImageQualityReport",
]
