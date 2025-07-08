# Task 3.4: Product Deduplication System

## Overview

Implement a comprehensive product deduplication system to prevent duplicate products in the database and ensure clean Gambio exports. The system will use manufacturer SKU as the unique identifier and provide conflict detection for data mismatches.

## Business Context

**Current Problem:**
- Uploading the same invoice multiple times creates duplicate product records
- Different invoices with the same products create multiple entries for identical items
- Gambio exports contain duplicate products, causing import issues
- No way to track purchase history across multiple invoices

**Business Value:**
- Clean, deduplicated product database
- Accurate Gambio exports without duplicates
- Purchase history tracking across invoices
- Conflict detection for data quality assurance
- Reduced manual cleanup work

## Business Requirements

### Core Requirements

1. **No Duplicate Products**
   - Same manufacturer SKU = same product record in database
   - Only one product entry per unique manufacturer_sku
   - Gambio exports contain only unique products

2. **Purchase History Tracking**
   - Track which invoices contain which products
   - Query purchase history via invoice relationships
   - Maintain audit trail of product purchases

3. **Data Conflict Detection**
   - Flag products for manual review when data differs
   - Detect conflicts in product names, descriptions, prices
   - Provide clear conflict resolution workflow

4. **Duplicate Invoice Handling**
   - Re-uploading same invoice doesn't create duplicate products
   - Graceful handling of existing products in new invoices
   - Maintain data integrity across multiple uploads

### User Stories

**As a user uploading invoices:**
- I want duplicate products to be automatically detected and prevented
- I want to see conflicts when the same SKU has different product data
- I want to track which invoices contain which products
- I want clean Gambio exports without duplicate entries

**As a user managing products:**
- I want to review flagged products with data conflicts
- I want to resolve conflicts with clear guidance
- I want to see purchase history for each product
- I want confidence that my product database is clean

## Technical Requirements

### Database Schema Changes

```sql
-- Migration 006: Product deduplication system
ALTER TABLE products ADD CONSTRAINT unique_manufacturer_sku UNIQUE (manufacturer_sku);
ALTER TABLE products ADD COLUMN requires_review BOOLEAN DEFAULT FALSE;
ALTER TABLE products ADD COLUMN review_notes TEXT;
```

### Core Components

1. **Deduplication Logic**
   - Check manufacturer_sku uniqueness before product creation
   - Handle existing products gracefully
   - Skip creation for duplicates, optionally flag conflicts

2. **Conflict Detection**
   - Compare product data for same manufacturer_sku
   - Flag significant differences for manual review
   - Store conflict details in review_notes

3. **Review Workflow**
   - Mark products requiring review
   - Provide conflict resolution interface
   - Track review status and decisions

4. **Purchase History**
   - Maintain products.batch_id → upload_batches.id relationship
   - Query products by invoice/batch
   - Track product purchase timeline

## Functional Specifications

### Deduplication Algorithm

```python
def process_product_with_deduplication(product_data, batch_id):
    """
    Process product with deduplication logic.
    
    Args:
        product_data: Parsed product information
        batch_id: Current invoice batch ID
        
    Returns:
        ProcessingResult with status and actions taken
    """
    manufacturer_sku = product_data.manufacturer_sku
    
    # Check if product already exists
    existing_product = get_product_by_manufacturer_sku(manufacturer_sku)
    
    if existing_product:
        # Product exists - check for conflicts
        conflicts = detect_data_conflicts(existing_product, product_data)
        
        if conflicts:
            # Flag for review
            flag_product_for_review(existing_product, conflicts, batch_id)
            return ProcessingResult(
                status="conflict_detected",
                product_id=existing_product.id,
                action="flagged_for_review",
                conflicts=conflicts
            )
        else:
            # No conflicts - product already exists, skip creation
            return ProcessingResult(
                status="duplicate_skipped",
                product_id=existing_product.id,
                action="skipped_existing"
            )
    else:
        # New product - create normally
        new_product = create_product(product_data, batch_id)
        return ProcessingResult(
            status="created",
            product_id=new_product.id,
            action="created_new"
        )
```

### Conflict Detection Rules

**Significant Conflicts (require review):**
- Product name differs by more than minor variations
- Price differences > 10%
- Category/description major differences
- Currency mismatches

**Minor Differences (auto-resolve):**
- Whitespace variations
- Case differences
- Minor punctuation changes
- Equivalent currency amounts

### Data Structures

```python
class DeduplicationResult:
    """Result of deduplication processing."""
    status: str  # "created", "duplicate_skipped", "conflict_detected"
    product_id: UUID
    action: str
    conflicts: Optional[List[DataConflict]] = None
    
class DataConflict:
    """Represents a data conflict between products."""
    field: str
    existing_value: Any
    new_value: Any
    severity: str  # "minor", "major", "critical"
    auto_resolvable: bool
```

## API Changes

### Invoice Processor Updates

```python
class InvoiceProcessorService:
    async def process_products_with_deduplication(self, products_data, batch_id):
        """Process products with deduplication logic."""
        results = []
        
        for product_data in products_data:
            result = await self.process_single_product(product_data, batch_id)
            results.append(result)
            
        return DeduplicationSummary(
            total_products=len(products_data),
            created_new=len([r for r in results if r.status == "created"]),
            duplicates_skipped=len([r for r in results if r.status == "duplicate_skipped"]),
            conflicts_detected=len([r for r in results if r.status == "conflict_detected"]),
            results=results
        )
```

### Response Models

```python
class InvoiceUploadResponse(BaseModel):
    """Enhanced response with deduplication info."""
    success: bool
    batch_id: str
    supplier: str
    total_products: int
    deduplication_summary: DeduplicationSummary
    conflicts_requiring_review: int
    
class DeduplicationSummary(BaseModel):
    """Summary of deduplication processing."""
    total_products: int
    created_new: int
    duplicates_skipped: int
    conflicts_detected: int
    results: List[DeduplicationResult]
```

## User Interface Requirements

### Upload Response Display

```
✅ Invoice processed successfully
📊 Products: 31 total
   • 12 new products created
   • 15 duplicates skipped (already exist)
   • 4 conflicts detected - requires review

⚠️ Review Required: 4 products need attention
   • LF1234: Price difference detected
   • LF5678: Product name mismatch
   • LF9012: Category conflict
   • LF3456: Description differs significantly
```

### Review Interface (Future Enhancement)

- List products requiring review
- Side-by-side comparison of conflicting data
- Resolution options (keep existing, use new, manual edit)
- Bulk resolution capabilities

## Testing Strategy

### Unit Tests

1. **Deduplication Logic Tests**
   - Test unique constraint enforcement
   - Test conflict detection algorithms
   - Test various data comparison scenarios

2. **Edge Cases**
   - Empty manufacturer_sku handling
   - Null value comparisons
   - Unicode and special character handling

### Integration Tests

1. **Duplicate Invoice Scenarios**
   - Upload same invoice twice
   - Verify only one set of products created
   - Confirm no database constraint violations

2. **Conflict Detection Scenarios**
   - Same SKU with different product names
   - Price variations within/outside tolerance
   - Mixed currency scenarios

3. **Purchase History Tests**
   - Query products by invoice
   - Verify relationship integrity
   - Test cross-invoice product tracking

### Performance Tests

1. **Large Dataset Handling**
   - Process invoices with 100+ products
   - Measure deduplication performance
   - Test database query efficiency

2. **Concurrent Processing**
   - Multiple invoice uploads simultaneously
   - Race condition handling
   - Database lock management

## Success Criteria

### Functional Success

- [ ] Uploading same invoice twice creates 1 invoice record + unique products (not duplicates)
- [ ] Gambio CSV export contains only unique products
- [ ] Purchase history queryable via invoice relationships
- [ ] Clear conflict resolution workflow for data mismatches
- [ ] Database constraint prevents duplicate manufacturer_sku entries

### Performance Success

- [ ] Deduplication processing adds <10% overhead to invoice processing
- [ ] Conflict detection completes within 100ms per product
- [ ] Database queries remain sub-second with 10,000+ products

### User Experience Success

- [ ] Clear feedback on deduplication results
- [ ] Intuitive conflict resolution interface
- [ ] Minimal user intervention required for common scenarios
- [ ] Comprehensive audit trail for all deduplication actions

## Implementation Phases

### Phase 1: Core Deduplication (MVP)
- Database schema changes
- Basic deduplication logic
- Conflict detection framework
- Updated invoice processor

### Phase 2: Enhanced Conflict Resolution
- Detailed conflict analysis
- Auto-resolution rules
- Review workflow implementation
- User interface enhancements

### Phase 3: Advanced Features
- Bulk conflict resolution
- Machine learning conflict detection
- Advanced purchase history analytics
- Performance optimizations

## Risk Mitigation

### Technical Risks

1. **Database Constraint Violations**
   - Risk: Existing duplicate data prevents constraint addition
   - Mitigation: Pre-migration data cleanup, gradual constraint rollout

2. **Performance Impact**
   - Risk: Deduplication slows invoice processing
   - Mitigation: Efficient algorithms, database indexing, async processing

3. **Data Loss**
   - Risk: Aggressive deduplication loses important variations
   - Mitigation: Conservative conflict detection, comprehensive review workflow

### Business Risks

1. **False Conflict Detection**
   - Risk: System flags legitimate product variations as conflicts
   - Mitigation: Tunable sensitivity settings, user feedback loop

2. **User Workflow Disruption**
   - Risk: Review requirements slow down processing
   - Mitigation: Smart auto-resolution, batch review capabilities

## Dependencies

- **Prerequisite**: Task 3.3 (Invoice Management API completed)
- **Database**: Migration system must be stable and tested
- **Testing**: Reliable test infrastructure for validation

## Deliverables

1. **Database Migration**: 006_product_deduplication_system.sql
2. **Core Logic**: Enhanced InvoiceProcessorService with deduplication
3. **API Updates**: Modified response models and endpoints
4. **Test Suite**: Comprehensive deduplication test coverage
5. **Documentation**: Updated API documentation and user guides

## Future Enhancements

1. **Machine Learning**: AI-powered conflict detection and resolution
2. **Bulk Operations**: Mass product review and resolution tools
3. **Analytics**: Deduplication metrics and insights dashboard
4. **Integration**: Real-time conflict notifications and alerts
5. **Advanced Matching**: Fuzzy matching for similar but not identical SKUs
