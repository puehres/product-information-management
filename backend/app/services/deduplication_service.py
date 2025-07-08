"""
Product deduplication service for the Universal Product Automation System.

This module provides the core deduplication logic to prevent duplicate products
from being created in the database based on manufacturer_sku uniqueness.
"""

from typing import List, Optional
from uuid import UUID
import structlog

from ..models.deduplication import (
    DeduplicationResult, 
    DeduplicationSummary, 
    DeduplicationConfig
)
from ..models.product import Product, ProductCreate
from ..services.database_service import get_database_service
from ..services.conflict_detector import get_conflict_detector

logger = structlog.get_logger(__name__)


class DeduplicationService:
    """
    Service for handling product deduplication during invoice processing.
    
    Prevents duplicate products from being created by checking manufacturer_sku
    uniqueness and detecting data conflicts that require manual review.
    """
    
    def __init__(self, config: Optional[DeduplicationConfig] = None):
        """
        Initialize deduplication service.
        
        Args:
            config: Configuration for deduplication behavior.
        """
        self.config = config or DeduplicationConfig()
        self.db = get_database_service()
        self.conflict_detector = get_conflict_detector(config)
        logger.info("DeduplicationService initialized")
    
    async def process_product_with_deduplication(
        self, 
        product_data: ProductCreate, 
        batch_id: UUID
    ) -> DeduplicationResult:
        """
        Process a single product with deduplication logic.
        
        Args:
            product_data: Product data to process.
            batch_id: ID of the batch this product belongs to.
            
        Returns:
            DeduplicationResult indicating what action was taken.
        """
        try:
            # Validate manufacturer_sku is present
            if not product_data.manufacturer_sku:
                raise ValueError("manufacturer_sku is required for deduplication")
            
            # Check if product with this manufacturer_sku already exists
            existing_product = await self.db.get_product_by_manufacturer_sku(
                product_data.manufacturer_sku
            )
            
            if existing_product:
                # Product exists - check for conflicts
                return await self._handle_existing_product(
                    existing_product, product_data, batch_id
                )
            else:
                # New product - create it
                return await self._create_new_product(product_data, batch_id)
                
        except Exception as e:
            logger.error(
                "Error during product deduplication",
                manufacturer_sku=product_data.manufacturer_sku,
                error=str(e)
            )
            raise
    
    async def process_batch_with_deduplication(
        self, 
        products_data: List[ProductCreate], 
        batch_id: UUID
    ) -> DeduplicationSummary:
        """
        Process multiple products with deduplication logic.
        
        Args:
            products_data: List of product data to process.
            batch_id: ID of the batch these products belong to.
            
        Returns:
            DeduplicationSummary with aggregate results.
        """
        results = []
        created_new = 0
        duplicates_skipped = 0
        conflicts_detected = 0
        
        logger.info(
            "Starting batch deduplication",
            batch_id=str(batch_id),
            total_products=len(products_data)
        )
        
        for product_data in products_data:
            try:
                result = await self.process_product_with_deduplication(
                    product_data, batch_id
                )
                results.append(result)
                
                # Update counters
                if result.status == "created":
                    created_new += 1
                elif result.status == "duplicate_skipped":
                    duplicates_skipped += 1
                elif result.status == "conflict_detected":
                    conflicts_detected += 1
                    
            except Exception as e:
                logger.error(
                    "Failed to process product in batch",
                    manufacturer_sku=getattr(product_data, 'manufacturer_sku', 'unknown'),
                    batch_id=str(batch_id),
                    error=str(e)
                )
                # Continue processing other products
                continue
        
        summary = DeduplicationSummary(
            total_products=len(products_data),
            created_new=created_new,
            duplicates_skipped=duplicates_skipped,
            conflicts_detected=conflicts_detected,
            results=results
        )
        
        logger.info(
            "Batch deduplication completed",
            batch_id=str(batch_id),
            summary=summary.dict()
        )
        
        return summary
    
    async def _handle_existing_product(
        self, 
        existing_product: Product, 
        new_data: ProductCreate, 
        batch_id: UUID
    ) -> DeduplicationResult:
        """
        Handle case where product with same manufacturer_sku already exists.
        
        Args:
            existing_product: Existing product in database.
            new_data: New product data being processed.
            batch_id: ID of the current batch.
            
        Returns:
            DeduplicationResult indicating action taken.
        """
        # Detect conflicts between existing and new data
        conflicts = await self.conflict_detector.detect_conflicts(
            existing_product, new_data
        )
        
        if conflicts:
            # Conflicts detected - flag for review
            severity = self.conflict_detector.classify_conflict_severity(conflicts)
            can_auto_resolve = self.conflict_detector.can_auto_resolve(conflicts)
            
            if can_auto_resolve and self.config.auto_resolve_minor_conflicts:
                # Auto-resolve minor conflicts
                logger.info(
                    "Auto-resolving minor conflicts",
                    manufacturer_sku=existing_product.manufacturer_sku,
                    conflicts_count=len(conflicts)
                )
                
                # Update existing product with new data (for auto-resolvable fields)
                await self._auto_resolve_conflicts(existing_product, new_data, conflicts)
                
                return DeduplicationResult(
                    status="duplicate_skipped",
                    product_id=existing_product.id,
                    action="auto_resolved_conflicts",
                    conflicts=conflicts,
                    manufacturer_sku=existing_product.manufacturer_sku
                )
            else:
                # Flag for manual review
                review_notes = f"Conflicts detected from batch {batch_id}: {severity} severity"
                await self.db.update_product_review_status(
                    existing_product.id,
                    requires_review=True,
                    review_notes=review_notes
                )
                
                logger.warning(
                    "Product flagged for review due to conflicts",
                    manufacturer_sku=existing_product.manufacturer_sku,
                    severity=severity,
                    conflicts_count=len(conflicts)
                )
                
                return DeduplicationResult(
                    status="conflict_detected",
                    product_id=existing_product.id,
                    action="flagged_for_review",
                    conflicts=conflicts,
                    manufacturer_sku=existing_product.manufacturer_sku
                )
        else:
            # No conflicts - skip creation
            logger.info(
                "Duplicate product skipped (no conflicts)",
                manufacturer_sku=existing_product.manufacturer_sku
            )
            
            return DeduplicationResult(
                status="duplicate_skipped",
                product_id=existing_product.id,
                action="skipped_existing",
                conflicts=None,
                manufacturer_sku=existing_product.manufacturer_sku
            )
    
    async def _create_new_product(
        self, 
        product_data: ProductCreate, 
        batch_id: UUID
    ) -> DeduplicationResult:
        """
        Create a new product.
        
        Args:
            product_data: Product data to create.
            batch_id: ID of the current batch.
            
        Returns:
            DeduplicationResult for the created product.
        """
        try:
            # Ensure batch_id is set
            if hasattr(product_data, 'batch_id'):
                product_data.batch_id = batch_id
            
            new_product = await self.db.create_product(product_data)
            
            logger.info(
                "New product created",
                product_id=str(new_product.id),
                manufacturer_sku=new_product.manufacturer_sku
            )
            
            return DeduplicationResult(
                status="created",
                product_id=new_product.id,
                action="created_new",
                conflicts=None,
                manufacturer_sku=new_product.manufacturer_sku
            )
            
        except Exception as e:
            logger.error(
                "Failed to create new product",
                manufacturer_sku=product_data.manufacturer_sku,
                error=str(e)
            )
            raise
    
    async def _auto_resolve_conflicts(
        self, 
        existing_product: Product, 
        new_data: ProductCreate, 
        conflicts: List
    ) -> None:
        """
        Automatically resolve minor conflicts by updating existing product.
        
        Args:
            existing_product: Existing product to update.
            new_data: New data to merge.
            conflicts: List of conflicts to resolve.
        """
        # For now, we'll just log that auto-resolution would happen
        # In a full implementation, you'd update specific fields based on conflict type
        logger.info(
            "Auto-resolving conflicts (placeholder implementation)",
            manufacturer_sku=existing_product.manufacturer_sku,
            conflicts_count=len(conflicts)
        )
        
        # Example: Update description if it was missing
        # if existing_product.description is None and new_data.description:
        #     await self.db.update_product(existing_product.id, {"description": new_data.description})
    
    async def get_products_requiring_review(
        self, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Product]:
        """
        Get products that require manual review due to conflicts.
        
        Args:
            limit: Maximum number of products to return.
            offset: Number of products to skip.
            
        Returns:
            List of products requiring review.
        """
        try:
            # This would need to be implemented in database_service
            # For now, return empty list
            logger.info("Getting products requiring review", limit=limit, offset=offset)
            return []
            
        except Exception as e:
            logger.error("Failed to get products requiring review", error=str(e))
            raise
    
    async def resolve_product_conflicts(
        self, 
        product_id: UUID, 
        resolution_data: dict
    ) -> Product:
        """
        Manually resolve conflicts for a product.
        
        Args:
            product_id: ID of product to resolve.
            resolution_data: Data to update the product with.
            
        Returns:
            Updated product.
        """
        try:
            # Update product with resolution data
            updated_product = await self.db.update_product(product_id, resolution_data)
            
            # Clear review flag
            await self.db.update_product_review_status(
                product_id,
                requires_review=False,
                review_notes="Conflicts resolved manually"
            )
            
            logger.info(
                "Product conflicts resolved manually",
                product_id=str(product_id)
            )
            
            return updated_product
            
        except Exception as e:
            logger.error(
                "Failed to resolve product conflicts",
                product_id=str(product_id),
                error=str(e)
            )
            raise


def get_deduplication_service(config: Optional[DeduplicationConfig] = None) -> DeduplicationService:
    """
    Get a deduplication service instance.
    
    Args:
        config: Optional configuration for deduplication behavior.
        
    Returns:
        DeduplicationService instance.
    """
    return DeduplicationService(config)
