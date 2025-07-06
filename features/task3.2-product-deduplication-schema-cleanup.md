# Feature Specification: Product Deduplication & Schema Cleanup

**Task ID**: 3.1  
**Priority**: High (Critical MVP Fix)  
**Estimated Effort**: 1-2 days  
**Dependencies**: Task 3 (Enhanced Invoice Parser)

## Problem Statement

Currently, uploading the same invoice twice creates duplicate product records in the database, leading to:
- **Data Duplication**: Same manufacturer SKU (e.g., LF3244) stored multiple times
- **Gambio Import Issues**: CSV exports contain duplicate products
- **Storage Waste**: Unnecessary database storage and processing overhead
- **Business Logic Confusion**: No clear way to track purchase history vs. product catalog

## Business Requirements

### Core Requirements
1. **Product Uniqueness**: Each manufacturer SKU should exist only once in the database
2. **Purchase History**: Track where and when products were purchased across multiple invoices
3. **Data Integrity**: Prevent duplicate products in Gambio CSV exports
4. **Schema Clarity**: Use business-appropriate naming (`invoices` vs `upload_batches`)

### User Stories
- **As a user**, I want to upload the same invoice multiple times without creating duplicate products
- **As a user**, I want to see purchase history for each product across different invoices
- **As a user**, I want Gambio CSV exports to contain only unique products
- **As a developer**, I want clear, business-appropriate table and field names

## Technical Requirements

### Database Schema Changes

#### 1. Table Rename: `upload_batches` → `invoices`
```sql
-- Rename table to reflect business purpose
ALTER TABLE upload_batches RENAME TO invoices;

-- Update foreign key column name
ALTER TABLE products RENAME COLUMN batch_id TO invoice_id;

-- Update constraint names
ALTER TABLE products DROP CONSTRAINT products_batch_id_fkey;
ALTER TABLE products ADD CONSTRAINT products_invoice_id_fkey 
    FOREIGN KEY (invoice_id) REFERENCES invoices(id);
```

#### 2. Product Deduplication
```sql
-- Add unique constraint on manufacturer SKU
ALTER TABLE products ADD CONSTRAINT unique_manufacturer_sku 
    UNIQUE (manufacturer_sku);

-- Add review fields for conflict detection
ALTER TABLE products ADD COLUMN requires_review BOOLEAN DEFAULT FALSE;
ALTER TABLE products ADD COLUMN review_notes TEXT;
```

### Updated Schema Relationships
```
suppliers (1) → (many) invoices (1) → (many) products
```

**Business Logic**:
- **Suppliers**: Who you buy from (Lawn Fawn, Craftlines)
- **Invoices**: Individual invoice uploads with metadata
- **Products**: Unique product catalog (one per manufacturer SKU)

### Code Changes Required

#### 1. Pydantic Models
```python
# Rename all UploadBatch classes to Invoice
UploadBatchCreate → InvoiceCreate
UploadBatchUpdate → InvoiceUpdate  
UploadBatch → Invoice
UploadBatchSummary → InvoiceSummary

# Update ProductCreate model
class ProductCreate(BaseCreateModel):
    invoice_id: UUID  # Changed from batch_id
    # ... other fields remain the same
```

#### 2. Database Service Methods
```python
# Rename methods for clarity
create_upload_batch() → create_invoice()
get_upload_batch_by_id() → get_invoice_by_id()
get_upload_batches() → get_invoices()
update_upload_batch() → update_invoice()

# Add product deduplication method
async def get_product_by_manufacturer_sku(self, sku: str) -> Optional[Product]:
    """Get existing product by manufacturer SKU."""
    pass
```

#### 3. Invoice Processor Logic
```python
async def store_product(self, product_data, invoice_id, supplier_id):
    # 1. Check if product already exists
    existing_product = await self.db.get_product_by_manufacturer_sku(
        product_data.manufacturer_sku
    )
    
    if existing_product:
        # 2. Product exists - skip creation
        logger.info(f"Product {product_data.manufacturer_sku} already exists")
        
        # 3. Optional: Check for data conflicts
        if self.has_data_conflicts(existing_product, product_data):
            await self.db.flag_product_for_review(
                existing_product.id,
                f"Data conflict from invoice {invoice_id}"
            )
        
        return existing_product
    else:
        # 4. New product - create as normal
        return await self.db.create_product(product_data)
```

#### 4. Conflict Detection Logic
```python
def has_data_conflicts(self, existing_product, new_product_data):
    """Check if new product data conflicts with existing."""
    conflicts = []
    
    # Check key fields for differences
    if existing_product.supplier_name != new_product_data.product_name:
        conflicts.append("product_name")
    
    if existing_product.supplier_price_usd != new_product_data.price_usd:
        conflicts.append("price")
    
    return len(conflicts) > 0
```

### API Response Changes
```python
# Update response field names
{
    "success": true,
    "invoice_id": "uuid",  # Changed from batch_id
    "supplier": "lawnfawn",
    "products_found": 31,
    "parsing_success_rate": 100.0
}
```

## Implementation Plan

### Phase 1: Database Migration
1. **Create Migration 004**: Schema changes and constraints
2. **Test Migration**: Verify on development database
3. **Backup Strategy**: Ensure rollback capability

### Phase 2: Model Updates
1. **Update Pydantic Models**: Rename UploadBatch → Invoice classes
2. **Update Field Names**: batch_id → invoice_id throughout
3. **Test Model Changes**: Verify serialization/deserialization

### Phase 3: Service Layer Updates
1. **Update Database Service**: Rename methods and add deduplication
2. **Update Invoice Processor**: Add product deduplication logic
3. **Add Conflict Detection**: Flag products for manual review

### Phase 4: API Updates
1. **Update Response Models**: Use new field names
2. **Update Documentation**: Reflect schema changes
3. **Test API Endpoints**: Verify all endpoints work correctly

### Phase 5: Testing & Validation
1. **Duplicate Upload Tests**: Upload same invoice twice
2. **Purchase History Queries**: Verify relationship tracking
3. **CSV Export Tests**: Ensure unique products only
4. **Conflict Detection Tests**: Verify review flagging

## Success Criteria

### Functional Requirements
- [ ] Uploading same invoice twice creates 1 invoice + 31 unique products (not 62)
- [ ] Gambio CSV export contains only unique products
- [ ] Purchase history queryable via invoice relationships
- [ ] Data conflicts flagged for manual review
- [ ] All API endpoints use consistent naming (`invoice_id`)

### Technical Requirements
- [ ] Database migration executes successfully
- [ ] All tests pass with new schema
- [ ] No breaking changes to existing functionality
- [ ] Performance maintained or improved

### Business Requirements
- [ ] Clear, intuitive schema naming throughout codebase
- [ ] Product catalog integrity maintained
- [ ] Purchase history tracking functional
- [ ] Manual review workflow for conflicts

## Testing Strategy

### Unit Tests
```python
def test_product_deduplication():
    """Test that duplicate manufacturer SKUs are not created."""
    # Upload invoice with LF3244
    # Upload same invoice again
    # Assert only one LF3244 product exists
    
def test_purchase_history():
    """Test purchase history tracking across invoices."""
    # Upload multiple invoices with same product
    # Query purchase history
    # Assert all purchases tracked correctly

def test_conflict_detection():
    """Test data conflict detection and review flagging."""
    # Create product with specific data
    # Upload invoice with conflicting data
    # Assert product flagged for review
```

### Integration Tests
```python
def test_duplicate_invoice_upload():
    """End-to-end test of duplicate invoice handling."""
    # Upload invoice via API
    # Upload same invoice again
    # Verify response and database state
    
def test_csv_export_uniqueness():
    """Test that CSV exports contain unique products only."""
    # Upload duplicate invoices
    # Generate CSV export
    # Assert no duplicate manufacturer SKUs
```

## Migration Script

```sql
-- Migration 004: Product Deduplication & Schema Cleanup
-- Date: 2025-01-07
-- Description: Rename upload_batches to invoices and add product deduplication

BEGIN;

-- 1. Rename upload_batches table to invoices
ALTER TABLE upload_batches RENAME TO invoices;

-- 2. Update foreign key column name in products table
ALTER TABLE products RENAME COLUMN batch_id TO invoice_id;

-- 3. Update foreign key constraint name
ALTER TABLE products DROP CONSTRAINT products_batch_id_fkey;
ALTER TABLE products ADD CONSTRAINT products_invoice_id_fkey 
    FOREIGN KEY (invoice_id) REFERENCES invoices(id);

-- 4. Add unique constraint on manufacturer_sku to prevent duplicates
ALTER TABLE products ADD CONSTRAINT unique_manufacturer_sku 
    UNIQUE (manufacturer_sku);

-- 5. Add review fields for conflict detection
ALTER TABLE products ADD COLUMN requires_review BOOLEAN DEFAULT FALSE;
ALTER TABLE products ADD COLUMN review_notes TEXT;

-- 6. Add comments for documentation
COMMENT ON TABLE invoices IS 'Invoice uploads and processing metadata';
COMMENT ON COLUMN products.invoice_id IS 'Reference to invoice where product was first seen';
COMMENT ON COLUMN products.requires_review IS 'Flag indicating product needs manual review';
COMMENT ON COLUMN products.review_notes IS 'Notes about data conflicts or review requirements';

COMMIT;
```

## Rollback Plan

```sql
-- Rollback Migration 004 if needed
BEGIN;

-- Remove new columns
ALTER TABLE products DROP COLUMN IF EXISTS requires_review;
ALTER TABLE products DROP COLUMN IF EXISTS review_notes;

-- Remove unique constraint
ALTER TABLE products DROP CONSTRAINT IF EXISTS unique_manufacturer_sku;

-- Revert foreign key constraint
ALTER TABLE products DROP CONSTRAINT products_invoice_id_fkey;
ALTER TABLE products ADD CONSTRAINT products_batch_id_fkey 
    FOREIGN KEY (invoice_id) REFERENCES invoices(id);

-- Revert column name
ALTER TABLE products RENAME COLUMN invoice_id TO batch_id;

-- Revert table name
ALTER TABLE invoices RENAME TO upload_batches;

COMMIT;
```

## Risk Assessment

### Low Risk
- **Schema Rename**: Straightforward table/column renames
- **Model Updates**: Simple class and field name changes
- **API Updates**: Non-breaking field name changes

### Medium Risk
- **Unique Constraint**: May fail if duplicate manufacturer SKUs exist
- **Deduplication Logic**: Could affect existing product creation flow
- **Migration Timing**: Requires brief downtime for schema changes

### Mitigation Strategies
- **Pre-Migration Check**: Identify existing duplicate manufacturer SKUs
- **Gradual Rollout**: Test on development environment first
- **Backup Strategy**: Full database backup before migration
- **Monitoring**: Watch for errors after deployment

## Documentation Updates

### Code Documentation
- [ ] Update all docstrings with new terminology
- [ ] Update variable names and comments
- [ ] Update API documentation

### User Documentation
- [ ] Update any user-facing documentation
- [ ] Update troubleshooting guides
- [ ] Update deployment instructions

## Future Enhancements

### Phase 2 Considerations
- **Cross-Supplier Deduplication**: Handle same product from different suppliers
- **Advanced Conflict Resolution**: Automated conflict resolution rules
- **Purchase Analytics**: Advanced purchase history analysis
- **Bulk Review Interface**: UI for managing flagged products

This feature specification provides the foundation for implementing product deduplication while maintaining clear, business-appropriate schema naming throughout the system.
