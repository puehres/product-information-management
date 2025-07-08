"""
Test suite for product deduplication system.

This module tests the complete deduplication workflow including conflict detection,
database constraint handling, and integration with the invoice processing system.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from decimal import Decimal
from datetime import datetime

from app.services.deduplication_service import DeduplicationService, get_deduplication_service
from app.services.conflict_detector import ConflictDetector, get_conflict_detector
from app.models.deduplication import (
    DataConflict, 
    DeduplicationResult, 
    DeduplicationSummary, 
    DeduplicationConfig
)
from app.models.product import Product, ProductCreate


class TestDeduplicationService:
    """Test cases for the DeduplicationService."""
    
    @pytest.fixture
    def mock_db_service(self):
        """Mock database service."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_conflict_detector(self):
        """Mock conflict detector."""
        return AsyncMock()
    
    @pytest.fixture
    def deduplication_service(self, mock_db_service, mock_conflict_detector):
        """Create deduplication service with mocked dependencies."""
        service = DeduplicationService()
        service.db = mock_db_service
        service.conflict_detector = mock_conflict_detector
        return service
    
    @pytest.fixture
    def sample_product_create(self):
        """Sample product creation data."""
        return ProductCreate(
            batch_id=uuid4(),
            supplier_id=uuid4(),
            supplier_sku="TEST-SKU-001",
            manufacturer_sku="MFG-SKU-001",
            supplier_name="Test Product",
            manufacturer="TestMfg",
            category="test-category",
            supplier_price_usd=Decimal("19.99"),
            description="Test product description"
        )
    
    @pytest.fixture
    def sample_existing_product(self):
        """Sample existing product."""
        return Product(
            id=uuid4(),
            batch_id=uuid4(),
            supplier_id=uuid4(),
            supplier_sku="TEST-SKU-001",
            manufacturer_sku="MFG-SKU-001",
            supplier_name="Test Product",
            manufacturer="TestMfg",
            category="test-category",
            supplier_price_usd=Decimal("19.99"),
            description="Test product description",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_new_product_creation(self, deduplication_service, sample_product_create, mock_db_service):
        """Test that new product with unique manufacturer_sku gets created."""
        # Arrange
        batch_id = uuid4()
        new_product_id = uuid4()
        
        # Mock database to return None (no existing product)
        mock_db_service.get_product_by_manufacturer_sku.return_value = None
        
        # Mock product creation
        created_product = Product(
            id=new_product_id,
            **sample_product_create.dict()
        )
        mock_db_service.create_product.return_value = created_product
        
        # Act
        result = await deduplication_service.process_product_with_deduplication(
            sample_product_create, batch_id
        )
        
        # Assert
        assert result.status == "created"
        assert result.product_id == new_product_id
        assert result.action == "created_new"
        assert result.conflicts is None
        assert result.manufacturer_sku == sample_product_create.manufacturer_sku
        
        # Verify database calls
        mock_db_service.get_product_by_manufacturer_sku.assert_called_once_with(
            sample_product_create.manufacturer_sku
        )
        mock_db_service.create_product.assert_called_once_with(sample_product_create)
    
    @pytest.mark.asyncio
    async def test_duplicate_product_skipped(
        self, 
        deduplication_service, 
        sample_product_create, 
        sample_existing_product,
        mock_db_service,
        mock_conflict_detector
    ):
        """Test that existing product with same data gets skipped."""
        # Arrange
        batch_id = uuid4()
        
        # Mock database to return existing product
        mock_db_service.get_product_by_manufacturer_sku.return_value = sample_existing_product
        
        # Mock conflict detector to return no conflicts
        mock_conflict_detector.detect_conflicts.return_value = []
        
        # Act
        result = await deduplication_service.process_product_with_deduplication(
            sample_product_create, batch_id
        )
        
        # Assert
        assert result.status == "duplicate_skipped"
        assert result.product_id == sample_existing_product.id
        assert result.action == "skipped_existing"
        assert result.conflicts is None
        assert result.manufacturer_sku == sample_existing_product.manufacturer_sku
        
        # Verify no product creation
        mock_db_service.create_product.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_conflict_detection_and_flagging(
        self,
        deduplication_service,
        sample_product_create,
        sample_existing_product,
        mock_db_service,
        mock_conflict_detector
    ):
        """Test that product with conflicts gets flagged for review."""
        # Arrange
        batch_id = uuid4()
        
        # Create a conflicting product (different price)
        conflicting_product = sample_product_create.copy()
        conflicting_product.supplier_price_usd = Decimal("29.99")  # Different price
        
        # Mock database to return existing product
        mock_db_service.get_product_by_manufacturer_sku.return_value = sample_existing_product
        
        # Mock conflict detector to return price conflict
        price_conflict = DataConflict(
            field="supplier_price_usd",
            existing_value=19.99,
            new_value=29.99,
            severity="major",
            auto_resolvable=False
        )
        mock_conflict_detector.detect_conflicts.return_value = [price_conflict]
        mock_conflict_detector.classify_conflict_severity.return_value = "major"
        mock_conflict_detector.can_auto_resolve.return_value = False
        
        # Act
        result = await deduplication_service.process_product_with_deduplication(
            conflicting_product, batch_id
        )
        
        # Assert
        assert result.status == "conflict_detected"
        assert result.product_id == sample_existing_product.id
        assert result.action == "flagged_for_review"
        assert len(result.conflicts) == 1
        assert result.conflicts[0].field == "supplier_price_usd"
        assert result.conflicts[0].severity == "major"
        
        # Verify review status update
        mock_db_service.update_product_review_status.assert_called_once_with(
            sample_existing_product.id,
            requires_review=True,
            review_notes=f"Conflicts detected from batch {batch_id}: major severity"
        )
    
    @pytest.mark.asyncio
    async def test_auto_resolve_minor_conflicts(
        self,
        deduplication_service,
        sample_product_create,
        sample_existing_product,
        mock_db_service,
        mock_conflict_detector
    ):
        """Test that minor conflicts can be auto-resolved."""
        # Arrange
        batch_id = uuid4()
        
        # Mock database to return existing product
        mock_db_service.get_product_by_manufacturer_sku.return_value = sample_existing_product
        
        # Mock conflict detector to return minor conflict
        minor_conflict = DataConflict(
            field="category",
            existing_value="old-category",
            new_value="new-category",
            severity="minor",
            auto_resolvable=True
        )
        mock_conflict_detector.detect_conflicts.return_value = [minor_conflict]
        mock_conflict_detector.classify_conflict_severity.return_value = "minor"
        mock_conflict_detector.can_auto_resolve.return_value = True
        
        # Act
        result = await deduplication_service.process_product_with_deduplication(
            sample_product_create, batch_id
        )
        
        # Assert
        assert result.status == "duplicate_skipped"
        assert result.action == "auto_resolved_conflicts"
        assert len(result.conflicts) == 1
        assert result.conflicts[0].auto_resolvable is True
    
    @pytest.mark.asyncio
    async def test_missing_manufacturer_sku_error(self, deduplication_service):
        """Test that missing manufacturer_sku raises ValueError."""
        # Arrange
        batch_id = uuid4()
        product_data = ProductCreate(
            batch_id=batch_id,
            supplier_id=uuid4(),
            supplier_sku="TEST-SKU",
            manufacturer_sku=None,  # Missing!
            supplier_name="Test Product"
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="manufacturer_sku is required for deduplication"):
            await deduplication_service.process_product_with_deduplication(
                product_data, batch_id
            )
    
    @pytest.mark.asyncio
    async def test_batch_processing_with_mixed_scenarios(
        self,
        deduplication_service,
        mock_db_service,
        mock_conflict_detector
    ):
        """Test batch processing with new products, duplicates, and conflicts."""
        # Arrange
        batch_id = uuid4()
        
        # Create test products
        new_product = ProductCreate(
            batch_id=batch_id,
            supplier_id=uuid4(),
            supplier_sku="NEW-001",
            manufacturer_sku="NEW-MFG-001",
            supplier_name="New Product"
        )
        
        duplicate_product = ProductCreate(
            batch_id=batch_id,
            supplier_id=uuid4(),
            supplier_sku="DUP-001",
            manufacturer_sku="DUP-MFG-001",
            supplier_name="Duplicate Product"
        )
        
        conflict_product = ProductCreate(
            batch_id=batch_id,
            supplier_id=uuid4(),
            supplier_sku="CONF-001",
            manufacturer_sku="CONF-MFG-001",
            supplier_name="Conflict Product",
            supplier_price_usd=Decimal("99.99")
        )
        
        products_data = [new_product, duplicate_product, conflict_product]
        
        # Mock database responses
        def mock_get_by_sku(sku):
            if sku == "NEW-MFG-001":
                return None  # New product
            elif sku == "DUP-MFG-001":
                return Product(id=uuid4(), manufacturer_sku=sku, supplier_name="Duplicate Product")
            elif sku == "CONF-MFG-001":
                return Product(
                    id=uuid4(), 
                    manufacturer_sku=sku, 
                    supplier_name="Conflict Product",
                    supplier_price_usd=Decimal("49.99")  # Different price
                )
        
        mock_db_service.get_product_by_manufacturer_sku.side_effect = mock_get_by_sku
        mock_db_service.create_product.return_value = Product(id=uuid4(), manufacturer_sku="NEW-MFG-001")
        
        # Mock conflict detection
        def mock_detect_conflicts(existing, new):
            if existing.manufacturer_sku == "CONF-MFG-001":
                return [DataConflict(
                    field="supplier_price_usd",
                    existing_value=49.99,
                    new_value=99.99,
                    severity="major",
                    auto_resolvable=False
                )]
            return []
        
        mock_conflict_detector.detect_conflicts.side_effect = mock_detect_conflicts
        mock_conflict_detector.classify_conflict_severity.return_value = "major"
        mock_conflict_detector.can_auto_resolve.return_value = False
        
        # Act
        summary = await deduplication_service.process_batch_with_deduplication(
            products_data, batch_id
        )
        
        # Assert
        assert summary.total_products == 3
        assert summary.created_new == 1
        assert summary.duplicates_skipped == 1
        assert summary.conflicts_detected == 1
        assert len(summary.results) == 3
        
        # Check success and conflict rates
        assert summary.success_rate == 66.67  # 2 out of 3 successful
        assert summary.conflict_rate == 33.33  # 1 out of 3 conflicts


class TestConflictDetector:
    """Test cases for the ConflictDetector."""
    
    @pytest.fixture
    def conflict_detector(self):
        """Create conflict detector with default config."""
        return ConflictDetector()
    
    @pytest.fixture
    def custom_config(self):
        """Custom configuration for testing."""
        return DeduplicationConfig(
            price_difference_threshold=0.05,  # 5% threshold
            name_similarity_threshold=0.90,   # 90% similarity
            auto_resolve_minor_conflicts=False,
            enable_fuzzy_matching=True
        )
    
    @pytest.fixture
    def sample_existing_product(self):
        """Sample existing product for conflict testing."""
        return Product(
            id=uuid4(),
            manufacturer_sku="TEST-001",
            supplier_name="Original Product Name",
            supplier_price_usd=Decimal("20.00"),
            category="electronics",
            manufacturer="TestCorp",
            description="Original description"
        )
    
    @pytest.fixture
    def sample_new_data(self):
        """Sample new product data for conflict testing."""
        return ProductCreate(
            manufacturer_sku="TEST-001",
            supplier_name="Original Product Name",
            supplier_price_usd=Decimal("20.00"),
            category="electronics",
            manufacturer="TestCorp",
            description="Original description"
        )
    
    @pytest.mark.asyncio
    async def test_no_conflicts_identical_data(
        self, 
        conflict_detector, 
        sample_existing_product, 
        sample_new_data
    ):
        """Test that identical data produces no conflicts."""
        # Act
        conflicts = await conflict_detector.detect_conflicts(
            sample_existing_product, sample_new_data
        )
        
        # Assert
        assert len(conflicts) == 0
    
    @pytest.mark.asyncio
    async def test_price_conflict_detection(
        self, 
        conflict_detector, 
        sample_existing_product, 
        sample_new_data
    ):
        """Test detection of significant price differences."""
        # Arrange - 50% price increase
        sample_new_data.supplier_price_usd = Decimal("30.00")
        
        # Act
        conflicts = await conflict_detector.detect_conflicts(
            sample_existing_product, sample_new_data
        )
        
        # Assert
        price_conflicts = [c for c in conflicts if c.field == "supplier_price_usd"]
        assert len(price_conflicts) == 1
        
        conflict = price_conflicts[0]
        assert conflict.existing_value == 20.0
        assert conflict.new_value == 30.0
        assert conflict.severity == "major"
        assert conflict.auto_resolvable is False
    
    @pytest.mark.asyncio
    async def test_critical_price_conflict(
        self, 
        conflict_detector, 
        sample_existing_product, 
        sample_new_data
    ):
        """Test detection of critical price differences (>50%)."""
        # Arrange - 100% price increase
        sample_new_data.supplier_price_usd = Decimal("40.00")
        
        # Act
        conflicts = await conflict_detector.detect_conflicts(
            sample_existing_product, sample_new_data
        )
        
        # Assert
        price_conflicts = [c for c in conflicts if c.field == "supplier_price_usd"]
        assert len(price_conflicts) == 1
        assert price_conflicts[0].severity == "critical"
    
    @pytest.mark.asyncio
    async def test_name_similarity_matching(
        self, 
        conflict_detector, 
        sample_existing_product, 
        sample_new_data
    ):
        """Test fuzzy name matching for similar product names."""
        # Arrange - slightly different name
        sample_new_data.supplier_name = "Original Product Name v2"
        
        # Act
        conflicts = await conflict_detector.detect_conflicts(
            sample_existing_product, sample_new_data
        )
        
        # Assert
        name_conflicts = [c for c in conflicts if c.field == "supplier_name"]
        assert len(name_conflicts) == 1
        
        conflict = name_conflicts[0]
        assert conflict.severity == "minor"  # Similar names = minor conflict
        assert conflict.auto_resolvable is True
    
    @pytest.mark.asyncio
    async def test_major_name_difference(
        self, 
        conflict_detector, 
        sample_existing_product, 
        sample_new_data
    ):
        """Test detection of significantly different product names."""
        # Arrange - completely different name
        sample_new_data.supplier_name = "Completely Different Product"
        
        # Act
        conflicts = await conflict_detector.detect_conflicts(
            sample_existing_product, sample_new_data
        )
        
        # Assert
        name_conflicts = [c for c in conflicts if c.field == "supplier_name"]
        assert len(name_conflicts) == 1
        
        conflict = name_conflicts[0]
        assert conflict.severity == "major"
        assert conflict.auto_resolvable is False
    
    @pytest.mark.asyncio
    async def test_manufacturer_conflict(
        self, 
        conflict_detector, 
        sample_existing_product, 
        sample_new_data
    ):
        """Test detection of different manufacturers for same SKU."""
        # Arrange
        sample_new_data.manufacturer = "DifferentCorp"
        
        # Act
        conflicts = await conflict_detector.detect_conflicts(
            sample_existing_product, sample_new_data
        )
        
        # Assert
        mfg_conflicts = [c for c in conflicts if c.field == "manufacturer"]
        assert len(mfg_conflicts) == 1
        
        conflict = mfg_conflicts[0]
        assert conflict.severity == "major"  # Different manufacturer is major
        assert conflict.auto_resolvable is False
    
    @pytest.mark.asyncio
    async def test_category_conflict_minor(
        self, 
        conflict_detector, 
        sample_existing_product, 
        sample_new_data
    ):
        """Test that category differences are minor conflicts."""
        # Arrange
        sample_new_data.category = "gadgets"
        
        # Act
        conflicts = await conflict_detector.detect_conflicts(
            sample_existing_product, sample_new_data
        )
        
        # Assert
        cat_conflicts = [c for c in conflicts if c.field == "category"]
        assert len(cat_conflicts) == 1
        
        conflict = cat_conflicts[0]
        assert conflict.severity == "minor"
        assert conflict.auto_resolvable is True
    
    @pytest.mark.asyncio
    async def test_none_value_handling(
        self, 
        conflict_detector, 
        sample_existing_product, 
        sample_new_data
    ):
        """Test handling of None values in conflict detection."""
        # Arrange
        sample_existing_product.description = None
        sample_new_data.description = "New description"
        
        # Act
        conflicts = await conflict_detector.detect_conflicts(
            sample_existing_product, sample_new_data
        )
        
        # Assert - Description conflicts with None values should not be flagged
        desc_conflicts = [c for c in conflicts if c.field == "description"]
        assert len(desc_conflicts) == 0
    
    def test_conflict_severity_classification(self, conflict_detector):
        """Test overall conflict severity classification."""
        # Test critical severity
        critical_conflicts = [
            DataConflict(field="price", existing_value=10, new_value=20, severity="critical", auto_resolvable=False)
        ]
        assert conflict_detector.classify_conflict_severity(critical_conflicts) == "critical"
        
        # Test major severity
        major_conflicts = [
            DataConflict(field="name", existing_value="A", new_value="B", severity="major", auto_resolvable=False),
            DataConflict(field="cat", existing_value="X", new_value="Y", severity="minor", auto_resolvable=True)
        ]
        assert conflict_detector.classify_conflict_severity(major_conflicts) == "major"
        
        # Test minor severity
        minor_conflicts = [
            DataConflict(field="cat", existing_value="X", new_value="Y", severity="minor", auto_resolvable=True)
        ]
        assert conflict_detector.classify_conflict_severity(minor_conflicts) == "minor"
        
        # Test no conflicts
        assert conflict_detector.classify_conflict_severity([]) == "none"
    
    def test_auto_resolve_capability(self, conflict_detector):
        """Test auto-resolution capability detection."""
        # All auto-resolvable
        auto_conflicts = [
            DataConflict(field="cat", existing_value="X", new_value="Y", severity="minor", auto_resolvable=True),
            DataConflict(field="desc", existing_value="A", new_value="B", severity="minor", auto_resolvable=True)
        ]
        assert conflict_detector.can_auto_resolve(auto_conflicts) is True
        
        # Mixed resolvability
        mixed_conflicts = [
            DataConflict(field="cat", existing_value="X", new_value="Y", severity="minor", auto_resolvable=True),
            DataConflict(field="price", existing_value=10, new_value=20, severity="major", auto_resolvable=False)
        ]
        assert conflict_detector.can_auto_resolve(mixed_conflicts) is False
        
        # No conflicts
        assert conflict_detector.can_auto_resolve([]) is True


class TestDeduplicationIntegration:
    """Integration tests for the complete deduplication workflow."""
    
    @pytest.mark.asyncio
    async def test_database_constraint_violation_handling(self):
        """Test graceful handling of database unique constraint violations."""
        # This would test the actual database constraint behavior
        # For now, we'll test the expected error handling pattern
        
        with patch('app.services.database_service.get_database_service') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
            # Mock IntegrityError (unique constraint violation)
            from psycopg2.errors import UniqueViolation
            mock_db.create_product.side_effect = UniqueViolation("duplicate key value violates unique constraint")
            
            service = get_deduplication_service()
            service.db = mock_db
            
            product_data = ProductCreate(
                manufacturer_sku="DUPLICATE-SKU",
                supplier_name="Test Product"
            )
            
            # The service should handle this gracefully
            with pytest.raises(UniqueViolation):
                await service._create_new_product(product_data, uuid4())
    
    @pytest.mark.asyncio
    async def test_service_factory_functions(self):
        """Test that factory functions return proper instances."""
        # Test deduplication service factory
        service = get_deduplication_service()
        assert isinstance(service, DeduplicationService)
        
        # Test conflict detector factory
        detector = get_conflict_detector()
        assert isinstance(detector, ConflictDetector)
        
        # Test with custom config
        config = DeduplicationConfig(price_difference_threshold=0.05)
        custom_detector = get_conflict_detector(config)
        assert custom_detector.config.price_difference_threshold == 0.05


class TestDeduplicationModels:
    """Test the deduplication Pydantic models."""
    
    def test_data_conflict_model(self):
        """Test DataConflict model validation."""
        conflict = DataConflict(
            field="test_field",
            existing_value="old",
            new_value="new",
            severity="major",
            auto_resolvable=False
        )
        
        assert conflict.field == "test_field"
        assert conflict.severity == "major"
        assert conflict.auto_resolvable is False
    
    def test_deduplication_result_model(self):
        """Test DeduplicationResult model."""
        result = DeduplicationResult(
            status="created",
            product_id=uuid4(),
            action="created_new",
            manufacturer_sku="TEST-001"
        )
        
        assert result.status == "created"
        assert result.action == "created_new"
        assert result.conflicts is None
    
    def test_deduplication_summary_properties(self):
        """Test DeduplicationSummary calculated properties."""
        summary = DeduplicationSummary(
            total_products=10,
            created_new=6,
            duplicates_skipped=2,
            conflicts_detected=2,
            results=[]
        )
        
        assert summary.success_rate == 80.0  # (6+2)/10 * 100
        assert summary.conflict_rate == 20.0  # 2/10 * 100
    
    def test_deduplication_config_defaults(self):
        """Test DeduplicationConfig default values."""
        config = DeduplicationConfig()
        
        assert config.price_difference_threshold == 0.10
        assert config.name_similarity_threshold == 0.80
        assert config.auto_resolve_minor_conflicts is True
        assert config.enable_fuzzy_matching is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
