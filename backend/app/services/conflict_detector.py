"""
Conflict detection service for product deduplication.

This module provides algorithms to detect and classify conflicts between
existing and new product data during the deduplication process.
"""

import difflib
from typing import List, Optional, Any
from decimal import Decimal
import structlog

from ..models.deduplication import DataConflict, DeduplicationConfig
from ..models.product import Product, ProductCreate

logger = structlog.get_logger(__name__)


class ConflictDetector:
    """
    Service for detecting and classifying data conflicts between products.
    
    Analyzes differences between existing and new product data to determine
    if conflicts require manual review or can be auto-resolved.
    """
    
    def __init__(self, config: Optional[DeduplicationConfig] = None):
        """
        Initialize conflict detector with configuration.
        
        Args:
            config: Configuration for conflict detection thresholds.
        """
        self.config = config or DeduplicationConfig()
        logger.info("ConflictDetector initialized", config=self.config.dict())
    
    async def detect_conflicts(
        self, 
        existing_product: Product, 
        new_data: ProductCreate
    ) -> List[DataConflict]:
        """
        Detect conflicts between existing product and new data.
        
        Args:
            existing_product: Current product in database.
            new_data: New product data being processed.
            
        Returns:
            List of detected conflicts.
        """
        conflicts = []
        
        try:
            # Price conflict detection
            price_conflict = self._detect_price_conflict(
                existing_product.supplier_price_usd,
                new_data.supplier_price_usd
            )
            if price_conflict:
                conflicts.append(price_conflict)
            
            # Name conflict detection
            name_conflict = self._detect_name_conflict(
                existing_product.supplier_name,
                new_data.supplier_name
            )
            if name_conflict:
                conflicts.append(name_conflict)
            
            # Category conflict detection (if available)
            if hasattr(new_data, 'category'):
                category_conflict = self._detect_category_conflict(
                    getattr(existing_product, 'category', None),
                    new_data.category
                )
                if category_conflict:
                    conflicts.append(category_conflict)
            
            # Manufacturer conflict detection (if available)
            if hasattr(new_data, 'manufacturer'):
                manufacturer_conflict = self._detect_manufacturer_conflict(
                    getattr(existing_product, 'manufacturer', None),
                    new_data.manufacturer
                )
                if manufacturer_conflict:
                    conflicts.append(manufacturer_conflict)
            
            # Description conflict detection
            description_conflict = self._detect_description_conflict(
                getattr(existing_product, 'supplier_description', None),
                getattr(new_data, 'description', None)
            )
            if description_conflict:
                conflicts.append(description_conflict)
            
            logger.info(
                "Conflict detection completed",
                supplier_sku=existing_product.supplier_sku,
                conflicts_found=len(conflicts)
            )
            
            return conflicts
            
        except Exception as e:
            logger.error(
                "Error during conflict detection",
                supplier_sku=existing_product.supplier_sku,
                error=str(e)
            )
            raise
    
    def _detect_price_conflict(
        self, 
        existing_price: Optional[Decimal], 
        new_price: Optional[Decimal]
    ) -> Optional[DataConflict]:
        """
        Detect price conflicts based on percentage difference.
        
        Args:
            existing_price: Current price in database.
            new_price: New price from incoming data.
            
        Returns:
            DataConflict if significant price difference detected.
        """
        # Handle None values
        if existing_price is None and new_price is None:
            return None
        
        if existing_price is None or new_price is None:
            # One price is missing - this is a minor conflict
            return DataConflict(
                field="supplier_price_usd",
                existing_value=existing_price,
                new_value=new_price,
                severity="minor",
                auto_resolvable=True
            )
        
        # Calculate percentage difference
        if existing_price == 0:
            # Avoid division by zero
            if new_price != 0:
                return DataConflict(
                    field="supplier_price_usd",
                    existing_value=float(existing_price),
                    new_value=float(new_price),
                    severity="major",
                    auto_resolvable=False
                )
            return None
        
        percentage_diff = abs(float(new_price - existing_price)) / float(existing_price)
        
        if percentage_diff > self.config.price_difference_threshold:
            severity = "critical" if percentage_diff > 0.5 else "major"
            return DataConflict(
                field="supplier_price_usd",
                existing_value=float(existing_price),
                new_value=float(new_price),
                severity=severity,
                auto_resolvable=False
            )
        
        return None
    
    def _detect_name_conflict(
        self, 
        existing_name: Optional[str], 
        new_name: Optional[str]
    ) -> Optional[DataConflict]:
        """
        Detect name conflicts using fuzzy string matching.
        
        Args:
            existing_name: Current product name in database.
            new_name: New product name from incoming data.
            
        Returns:
            DataConflict if names are significantly different.
        """
        # Handle None values
        if existing_name is None and new_name is None:
            return None
        
        if existing_name is None or new_name is None:
            return DataConflict(
                field="supplier_name",
                existing_value=existing_name,
                new_value=new_name,
                severity="minor",
                auto_resolvable=True
            )
        
        # Normalize strings for comparison
        existing_normalized = existing_name.lower().strip()
        new_normalized = new_name.lower().strip()
        
        if existing_normalized == new_normalized:
            return None
        
        # Use fuzzy matching if enabled
        if self.config.enable_fuzzy_matching:
            similarity = difflib.SequenceMatcher(
                None, existing_normalized, new_normalized
            ).ratio()
            
            if similarity >= self.config.name_similarity_threshold:
                # Names are similar enough - minor conflict
                return DataConflict(
                    field="supplier_name",
                    existing_value=existing_name,
                    new_value=new_name,
                    severity="minor",
                    auto_resolvable=self.config.auto_resolve_minor_conflicts
                )
            else:
                # Names are significantly different
                return DataConflict(
                    field="supplier_name",
                    existing_value=existing_name,
                    new_value=new_name,
                    severity="major",
                    auto_resolvable=False
                )
        else:
            # Exact matching only
            return DataConflict(
                field="supplier_name",
                existing_value=existing_name,
                new_value=new_name,
                severity="major",
                auto_resolvable=False
            )
    
    def _detect_category_conflict(
        self, 
        existing_category: Optional[str], 
        new_category: Optional[str]
    ) -> Optional[DataConflict]:
        """
        Detect category conflicts.
        
        Args:
            existing_category: Current category in database.
            new_category: New category from incoming data.
            
        Returns:
            DataConflict if categories are different.
        """
        if existing_category == new_category:
            return None
        
        # Handle None values
        if existing_category is None or new_category is None:
            return DataConflict(
                field="category",
                existing_value=existing_category,
                new_value=new_category,
                severity="minor",
                auto_resolvable=True
            )
        
        # Categories are different - this is usually a minor conflict
        return DataConflict(
            field="category",
            existing_value=existing_category,
            new_value=new_category,
            severity="minor",
            auto_resolvable=self.config.auto_resolve_minor_conflicts
        )
    
    def _detect_manufacturer_conflict(
        self, 
        existing_manufacturer: Optional[str], 
        new_manufacturer: Optional[str]
    ) -> Optional[DataConflict]:
        """
        Detect manufacturer conflicts.
        
        Args:
            existing_manufacturer: Current manufacturer in database.
            new_manufacturer: New manufacturer from incoming data.
            
        Returns:
            DataConflict if manufacturers are different.
        """
        if existing_manufacturer == new_manufacturer:
            return None
        
        # Handle None values
        if existing_manufacturer is None or new_manufacturer is None:
            return DataConflict(
                field="manufacturer",
                existing_value=existing_manufacturer,
                new_value=new_manufacturer,
                severity="minor",
                auto_resolvable=True
            )
        
        # Normalize for comparison
        existing_norm = existing_manufacturer.lower().strip()
        new_norm = new_manufacturer.lower().strip()
        
        if existing_norm == new_norm:
            return None
        
        # Different manufacturers for same SKU is a major conflict
        return DataConflict(
            field="manufacturer",
            existing_value=existing_manufacturer,
            new_value=new_manufacturer,
            severity="major",
            auto_resolvable=False
        )
    
    def _detect_description_conflict(
        self, 
        existing_description: Optional[str], 
        new_description: Optional[str]
    ) -> Optional[DataConflict]:
        """
        Detect description conflicts.
        
        Args:
            existing_description: Current description in database.
            new_description: New description from incoming data.
            
        Returns:
            DataConflict if descriptions are significantly different.
        """
        # Handle None values
        if existing_description is None and new_description is None:
            return None
        
        if existing_description is None or new_description is None:
            # Missing description is usually not critical
            return None
        
        # Normalize for comparison
        existing_norm = existing_description.lower().strip()
        new_norm = new_description.lower().strip()
        
        if existing_norm == new_norm:
            return None
        
        # Use fuzzy matching for descriptions
        if self.config.enable_fuzzy_matching:
            similarity = difflib.SequenceMatcher(
                None, existing_norm, new_norm
            ).ratio()
            
            if similarity < 0.5:  # Less than 50% similar
                return DataConflict(
                    field="description",
                    existing_value=existing_description,
                    new_value=new_description,
                    severity="minor",
                    auto_resolvable=self.config.auto_resolve_minor_conflicts
                )
        
        return None
    
    def classify_conflict_severity(self, conflicts: List[DataConflict]) -> str:
        """
        Classify overall severity based on individual conflicts.
        
        Args:
            conflicts: List of detected conflicts.
            
        Returns:
            Overall severity: minor, major, or critical.
        """
        if not conflicts:
            return "none"
        
        severities = [conflict.severity for conflict in conflicts]
        
        if "critical" in severities:
            return "critical"
        elif "major" in severities:
            return "major"
        else:
            return "minor"
    
    def can_auto_resolve(self, conflicts: List[DataConflict]) -> bool:
        """
        Determine if conflicts can be automatically resolved.
        
        Args:
            conflicts: List of detected conflicts.
            
        Returns:
            True if all conflicts are auto-resolvable.
        """
        return all(conflict.auto_resolvable for conflict in conflicts)


def get_conflict_detector(config: Optional[DeduplicationConfig] = None) -> ConflictDetector:
    """
    Get a conflict detector instance.
    
    Args:
        config: Optional configuration for conflict detection.
        
    Returns:
        ConflictDetector instance.
    """
    return ConflictDetector(config)
