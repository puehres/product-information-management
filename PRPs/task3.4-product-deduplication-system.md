name: "Task 3.4: Product Deduplication System"
description: |
  Implement comprehensive product deduplication system to prevent duplicate products 
  in database and ensure clean Gambio exports using manufacturer_sku as unique identifier.

---

## Goal
Implement a product deduplication system that prevents duplicate products from being created in the database when processing invoices. The system will use `manufacturer_sku` as the unique identifier and provide conflict detection for data mismatches, ensuring clean Gambio exports and proper purchase history tracking.

## Why
- **Business Value**: Eliminates duplicate products in Gambio exports, reducing manual cleanup work
- **Data Quality**: Ensures one product record per manufacturer SKU with conflict detection
- **Purchase History**: Enables tracking which invoices contain which products across multiple uploads
- **User Experience**: Prevents confusion from duplicate entries and provides clear conflict resolution

## What
A deduplication system that:
- Adds unique constraint on `products.manufacturer_sku` 
- Implements deduplication logic in invoice processor
- Detects and flags data conflicts for manual review
- Handles duplicate invoice uploads gracefully
- Maintains purchase history via invoice relationships

### Success Criteria
- [ ] Uploading same invoice twice creates 1 invoice record + unique products (not duplicates)
- [ ] Gambio CSV export contains only unique products
- [ ] Purchase history queryable via invoice relationships
- [ ] Clear conflict resolution workflow for data mismatches
- [ ] Database constraint prevents duplicate manufacturer_sku entries

## All Needed Context

### Documentation & References
```yaml
- file: backend/app/services/database_service.py
  why: Existing CRUD patterns and error handling to follow
  
- file: backend/app/services/invoice_processor.py
  why: Current product creation logic that needs deduplication enhancement
  
- file: backend/app/models/product.py
  why: Product model structure and validation patterns
  
- file: backend/migrations/005_invoice_management_indexes.sql
  why: Migration pattern and index creation approach
  
- file: backend/tests/unit/test_invoice_management_api_fixed.py
  why: Testing patterns with mocking and comprehensive coverage
  
- url: https://docs.python.org/3/library/difflib.html
  why: Text comparison for conflict detection algorithms
  
- url: https://www.postgresql.org/docs/current/ddl-constraints.html
  section: Unique Constraints
  critical: Understanding UNIQUE constraint behavior and error handling
```

### Current Codebase Tree (Relevant Files)
```bash
backend/
├── app/
│   ├── models/
│   │   ├── product.py              # Product Pydantic models
│   │   ├── upload_batch.py         # Batch models for invoice tracking
│   │   └── invoice.py              # Invoice response models
│   ├── services/
│   │   ├── database_service.py     # CRUD operations
│   │   └── invoice_processor.py    # Current product creation logic
│   └── api/
│       └── upload.py               # Upload endpoints
├── migrations/
│   └── 006_product_deduplication_system.sql  # NEW
└── tests/
    └── unit/
        └── test_product_deduplication.py     # NEW
```

### Desired Codebase Tree with New Files
```bash
backend/
├── app/
│   ├── services/
│   │   ├── deduplication_service.py    # NEW: Core deduplication logic
│   │   └── conflict_detector.py        # NEW: Data conflict detection
│   └── models/
│       └── deduplication.py            # NEW: Deduplication response models
├── migrations/
│   └── 006_product_deduplication_system.sql  # NEW: Database constraints
└── tests/
    └── unit/
        └── test_product_deduplication.py     # NEW: Comprehensive test suite
```

### Known Gotchas of Our Codebase & Library Quirks
```python
# CRITICAL: Supabase uses PostgreSQL constraints - unique violations raise IntegrityError
# Example: psycopg2.errors.UniqueViolation wrapped in supabase exceptions

# CRITICAL: manufacturer_sku can be None/empty - need validation before constraint
# Current code: manufacturer_sku: Optional[str] in Product model

# CRITICAL: Database service uses async/await pattern consistently
# Pattern: All database operations must be async and use proper error handling

# CRITICAL: Invoice processor creates products in batch - need transaction handling
# Pattern: Use database transactions for atomic operations

# CRITICAL: Pydantic models use Field() with validation - follow existing patterns
# Example: manufacturer_sku: str = Field(..., min_length=1, description="...")

# CRITICAL: Test patterns use AsyncMock and patch decorators
# Pattern: Mock database_service.get_database_service() for unit tests
```

## Implementation Blueprint

### Data Models and Structure

Create deduplication-specific models for responses and conflict tracking:
```python
# app/models/deduplication.py
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from uuid import UUID

class DataConflict(BaseModel):
    """Represents a data conflict between products."""
    field: str = Field(..., description="Field name with conflict")
    existing_value: Any = Field(..., description="Current database value")
    new_value: Any = Field(..., description="New incoming value")
    severity: str = Field(..., description="Conflict severity: minor, major, critical")
    auto_resolvable: bool = Field(..., description="Can be auto-resolved")

class DeduplicationResult(BaseModel):
    """Result of processing a single product with deduplication."""
    status: str = Field(..., description="created, duplicate_skipped, conflict_detected")
    product_id: UUID = Field(..., description="Product ID (existing or new)")
    action: str = Field(..., description="Action taken")
    conflicts: Optional[List[DataConflict]] = None

class DeduplicationSummary(BaseModel):
    """Summary of deduplication processing for entire batch."""
    total_products: int
    created_new: int
    duplicates_skipped: int
    conflicts_detected: int
    results: List[DeduplicationResult]
```

### List of Tasks to be Completed

```yaml
Task 1: Create Database Migration
CREATE backend/migrations/006_product_deduplication_system.sql:
  - ADD unique constraint on products.manufacturer_sku
  - ADD requires_review BOOLEAN DEFAULT FALSE column
  - ADD review_notes TEXT column
  - HANDLE existing duplicate data gracefully

Task 2: Create Deduplication Service
CREATE backend/app/services/deduplication_service.py:
  - IMPLEMENT get_product_by_manufacturer_sku() method
  - IMPLEMENT deduplication logic with conflict detection
  - MIRROR error handling patterns from database_service.py
  - USE async/await consistently

Task 3: Create Conflict Detection Service  
CREATE backend/app/services/conflict_detector.py:
  - IMPLEMENT data comparison algorithms
  - DEFINE conflict severity rules (price >10%, name differences, etc.)
  - IMPLEMENT auto-resolution for minor differences
  - RETURN structured conflict information

Task 4: Create Deduplication Models
CREATE backend/app/models/deduplication.py:
  - DEFINE DataConflict, DeduplicationResult, DeduplicationSummary
  - FOLLOW existing Pydantic patterns from invoice.py
  - ADD proper validation and field descriptions

Task 5: Enhance Invoice Processor
MODIFY backend/app/services/invoice_processor.py:
  - INTEGRATE deduplication service into product creation flow
  - REPLACE direct product creation with deduplication logic
  - UPDATE response models to include deduplication summary
  - PRESERVE existing error handling patterns

Task 6: Update Database Service
MODIFY backend/app/services/database_service.py:
  - ADD get_product_by_manufacturer_sku() method
  - ADD update_product_review_status() method
  - FOLLOW existing CRUD patterns and error handling

Task 7: Update API Response Models
MODIFY backend/app/models/invoice.py:
  - ADD deduplication_summary field to InvoiceUploadResponse
  - ADD conflicts_requiring_review field
  - MAINTAIN backward compatibility

Task 8: Create Comprehensive Test Suite
CREATE backend/tests/unit/test_product_deduplication.py:
  - TEST deduplication logic with various scenarios
  - TEST conflict detection algorithms
  - TEST database constraint handling
  - FOLLOW existing test patterns with AsyncMock
```

### Per Task Pseudocode

```python
# Task 2: Deduplication Service Core Logic
class DeduplicationService:
    async def process_product_with_deduplication(self, product_data, batch_id):
        # PATTERN: Always validate input first
        if not product_data.manufacturer_sku:
            raise ValueError("manufacturer_sku required for deduplication")
        
        # Check if product exists
        existing = await self.db.get_product_by_manufacturer_sku(
            product_data.manufacturer_sku
        )
        
        if existing:
            # Detect conflicts using conflict_detector service
            conflicts = await self.conflict_detector.detect_conflicts(
                existing, product_data
            )
            
            if conflicts:
                # Flag for review and return conflict result
                await self.db.update_product_review_status(
                    existing.id, requires_review=True, 
                    review_notes=f"Conflicts detected: {conflicts}"
                )
                return DeduplicationResult(
                    status="conflict_detected",
                    product_id=existing.id,
                    action="flagged_for_review",
                    conflicts=conflicts
                )
            else:
                # No conflicts - skip creation
                return DeduplicationResult(
                    status="duplicate_skipped",
                    product_id=existing.id,
                    action="skipped_existing"
                )
        else:
            # New product - create normally
            new_product = await self.db.create_product(product_data)
            return DeduplicationResult(
                status="created",
                product_id=new_product.id,
                action="created_new"
            )

# Task 3: Conflict Detection Logic
class ConflictDetector:
    async def detect_conflicts(self, existing_product, new_data):
        conflicts = []
        
        # Price conflict detection (>10% difference)
        if self._price_differs_significantly(existing_product.supplier_price_usd, 
                                           new_data.supplier_price_usd):
            conflicts.append(DataConflict(
                field="supplier_price_usd",
                existing_value=existing_product.supplier_price_usd,
                new_value=new_data.supplier_price_usd,
                severity="major",
                auto_resolvable=False
            ))
        
        # Name conflict detection (fuzzy matching)
        if not self._names_similar(existing_product.supplier_name, 
                                 new_data.supplier_name):
            conflicts.append(DataConflict(
                field="supplier_name",
                existing_value=existing_product.supplier_name,
                new_value=new_data.supplier_name,
                severity="major",
                auto_resolvable=False
            ))
        
        return conflicts
```

### Integration Points
```yaml
DATABASE:
  - migration: "006_product_deduplication_system.sql"
  - constraint: "ALTER TABLE products ADD CONSTRAINT unique_manufacturer_sku UNIQUE (manufacturer_sku)"
  - fields: "requires_review BOOLEAN, review_notes TEXT"
  
SERVICES:
  - enhance: "invoice_processor.py - integrate deduplication logic"
  - create: "deduplication_service.py - core deduplication logic"
  - create: "conflict_detector.py - data conflict detection"
  
MODELS:
  - enhance: "invoice.py - add deduplication summary to responses"
  - create: "deduplication.py - deduplication-specific models"
  
API:
  - enhance: "upload.py - return deduplication information in responses"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
ruff check backend/app/services/deduplication_service.py --fix
ruff check backend/app/services/conflict_detector.py --fix
ruff check backend/app/models/deduplication.py --fix
mypy backend/app/services/deduplication_service.py
mypy backend/app/services/conflict_detector.py
mypy backend/app/models/deduplication.py

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests
```python
# CREATE backend/tests/unit/test_product_deduplication.py
class TestDeduplicationService:
    async def test_new_product_creation(self):
        """New product with unique manufacturer_sku gets created"""
        # Mock database to return None (no existing product)
        # Call deduplication service
        # Assert status="created" and new product created
        
    async def test_duplicate_product_skipped(self):
        """Existing product with same data gets skipped"""
        # Mock database to return existing product
        # Mock conflict detector to return no conflicts
        # Assert status="duplicate_skipped"
        
    async def test_conflict_detection_and_flagging(self):
        """Product with conflicts gets flagged for review"""
        # Mock existing product with different price
        # Mock conflict detector to return price conflict
        # Assert status="conflict_detected" and review flag set
        
    async def test_database_constraint_violation(self):
        """Handle unique constraint violations gracefully"""
        # Mock database to raise IntegrityError
        # Assert proper error handling and user-friendly message

class TestConflictDetector:
    def test_price_conflict_detection(self):
        """Detects significant price differences (>10%)"""
        
    def test_name_similarity_matching(self):
        """Detects similar vs different product names"""
        
    def test_auto_resolvable_conflicts(self):
        """Minor differences marked as auto-resolvable"""
```

```bash
# Run and iterate until passing:
cd backend && uv run pytest tests/unit/test_product_deduplication.py -v
# If failing: Read error, understand root cause, fix code, re-run
```

### Level 3: Integration Test
```bash
# Test database migration
cd backend && python run_migrations.py

# Test duplicate invoice upload scenario
curl -X POST http://localhost:8000/api/upload/invoice \
  -F "file=@tests/fixtures/test_invoice.pdf"

# Upload same invoice again - should show deduplication results
curl -X POST http://localhost:8000/api/upload/invoice \
  -F "file=@tests/fixtures/test_invoice.pdf"

# Expected: Second upload shows duplicates_skipped > 0, created_new = 0
```

## Testing Strategy (MANDATORY)

### Backend Tests
- [ ] Unit tests for deduplication service core logic
- [ ] Unit tests for conflict detection algorithms  
- [ ] Integration tests for database constraint handling
- [ ] Integration tests for complete invoice processing workflow
- [ ] Edge case tests (empty manufacturer_sku, null values)
- [ ] Performance tests with large product datasets

### Test Scenarios
- [ ] New product creation (unique manufacturer_sku)
- [ ] Duplicate product skipping (identical data)
- [ ] Conflict detection and flagging (different data, same SKU)
- [ ] Database constraint violation handling
- [ ] Batch processing with mixed scenarios
- [ ] Purchase history tracking across invoices

### Test Execution Plan
- [ ] Run existing tests to ensure no regression: `uv run pytest tests/ -v`
- [ ] Add new deduplication tests: `uv run pytest tests/unit/test_product_deduplication.py -v`
- [ ] Test database migration: `python run_migrations.py`
- [ ] Manual integration testing with duplicate invoice uploads

## Documentation Updates Required (MANDATORY)

### Core Documentation
- [ ] Update README.md with deduplication feature description
- [ ] Update API documentation for enhanced upload response format
- [ ] Document conflict resolution workflow for users
- [ ] Update database schema documentation

### Code Documentation
- [ ] Add comprehensive docstrings to all new functions (Google style)
- [ ] Document deduplication algorithm and conflict detection rules
- [ ] Add inline comments for complex conflict detection logic
- [ ] Document database migration and constraint behavior

## Final Validation Checklist
- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] No linting errors: `uv run ruff check backend/`
- [ ] No type errors: `uv run mypy backend/`
- [ ] Database migration runs successfully: `python run_migrations.py`
- [ ] Duplicate invoice upload test successful
- [ ] Conflict detection working as expected
- [ ] API responses include deduplication summary
- [ ] Purchase history tracking functional
- [ ] Documentation updated as specified above
- [ ] All testing requirements met
- [ ] Ready for PRP completion workflow

---

## Anti-Patterns to Avoid
- ❌ Don't ignore unique constraint violations - handle them gracefully
- ❌ Don't create products without checking for duplicates first
- ❌ Don't skip conflict detection for "minor" differences
- ❌ Don't use synchronous database calls in async context
- ❌ Don't hardcode conflict detection thresholds - make them configurable
- ❌ Don't skip testing edge cases like null manufacturer_sku
- ❌ Don't break existing invoice processing workflow
- ❌ Don't skip documentation - deduplication logic needs clear explanation

## Confidence Score: 8/10
High confidence due to:
- Clear existing patterns to follow in codebase
- Well-defined database constraint approach
- Comprehensive testing strategy
- Detailed conflict detection specification
- Proper integration with existing invoice processor

Potential risks:
- Database migration on existing data with duplicates
- Performance impact of deduplication checks on large batches
