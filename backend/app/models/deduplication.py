"""
Deduplication models for the Universal Product Automation System.

This module defines Pydantic models for product deduplication responses,
conflict detection, and processing summaries.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any
from uuid import UUID


class DataConflict(BaseModel):
    """
    Represents a data conflict between existing and new product data.
    
    Used when the same manufacturer_sku has different product information
    that requires manual review or resolution.
    """
    field: str = Field(..., description="Field name with conflict")
    existing_value: Any = Field(..., description="Current database value")
    new_value: Any = Field(..., description="New incoming value")
    severity: str = Field(..., description="Conflict severity: minor, major, critical")
    auto_resolvable: bool = Field(..., description="Can be auto-resolved")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            # Handle None values in JSON serialization
            type(None): lambda v: None
        }


class DeduplicationResult(BaseModel):
    """
    Result of processing a single product with deduplication logic.
    
    Contains the outcome of checking whether a product should be created,
    skipped, or flagged for review based on manufacturer_sku uniqueness.
    """
    status: str = Field(..., description="Processing status: created, duplicate_skipped, conflict_detected")
    product_id: UUID = Field(..., description="Product ID (existing or newly created)")
    action: str = Field(..., description="Action taken during processing")
    conflicts: Optional[List[DataConflict]] = Field(None, description="List of detected conflicts")
    manufacturer_sku: str = Field(..., description="Manufacturer SKU that was processed")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class DeduplicationSummary(BaseModel):
    """
    Summary of deduplication processing for an entire invoice batch.
    
    Provides aggregate statistics about how many products were created,
    skipped, or flagged for review during batch processing.
    """
    total_products: int = Field(..., description="Total products processed")
    created_new: int = Field(..., description="Number of new products created")
    duplicates_skipped: int = Field(..., description="Number of duplicate products skipped")
    conflicts_detected: int = Field(..., description="Number of products flagged for review")
    results: List[DeduplicationResult] = Field(..., description="Detailed results for each product")
    
    @property
    def success_rate(self) -> float:
        """Calculate the percentage of products processed without conflicts."""
        if self.total_products == 0:
            return 100.0
        successful = self.created_new + self.duplicates_skipped
        return round((successful / self.total_products) * 100, 2)
    
    @property
    def conflict_rate(self) -> float:
        """Calculate the percentage of products requiring review."""
        if self.total_products == 0:
            return 0.0
        return round((self.conflicts_detected / self.total_products) * 100, 2)
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class ProductConflictInfo(BaseModel):
    """
    Detailed information about a product that requires review.
    
    Used for displaying conflict information to users for manual resolution.
    """
    product_id: UUID = Field(..., description="Product ID requiring review")
    manufacturer_sku: str = Field(..., description="Manufacturer SKU with conflicts")
    supplier_name: Optional[str] = Field(None, description="Product name from supplier")
    conflicts: List[DataConflict] = Field(..., description="List of detected conflicts")
    created_at: str = Field(..., description="When the product was first created")
    last_conflict_at: str = Field(..., description="When the latest conflict was detected")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class DeduplicationConfig(BaseModel):
    """
    Configuration settings for deduplication and conflict detection.
    
    Allows customization of thresholds and rules for conflict detection.
    """
    price_difference_threshold: float = Field(0.10, description="Price difference threshold (10% default)")
    name_similarity_threshold: float = Field(0.80, description="Name similarity threshold (80% default)")
    auto_resolve_minor_conflicts: bool = Field(True, description="Automatically resolve minor conflicts")
    enable_fuzzy_matching: bool = Field(True, description="Enable fuzzy string matching")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
