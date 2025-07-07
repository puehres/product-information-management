name: "Task 3.3: Invoice Management API & Download System"
description: |
  Complete the missing invoice management functionality by implementing the `/api/invoices` list endpoint 
  and enhancing the download system. This provides users with a complete workflow to discover, manage, 
  and download their processed invoices.

---

## Goal
Implement a complete invoice management API that allows users to list, search, filter, and download their processed invoices. The system should provide pagination, filtering by supplier/date/search terms, and seamless integration with the existing S3 download functionality.

## Why
- **User Experience**: Currently users can upload invoices but have no way to see what they've uploaded or manage their invoice history
- **Business Value**: Complete workflow from upload → list → find → download enables proper invoice management
- **System Integration**: Connects existing upload/processing functionality with download capabilities
- **Data Discovery**: Users need to find batch_ids to generate download URLs, currently impossible without direct database access

## What
A comprehensive invoice management system with:
- Paginated invoice listing with filtering and search
- Integration with existing S3 download system
- Proper error handling and validation
- Complete API documentation
- Full test coverage

### Success Criteria
- [ ] Users can list all their processed invoices with pagination
- [ ] Filtering by supplier, date range, and search terms works correctly
- [ ] Download URLs are generated successfully for any processed invoice
- [ ] Complete user workflow tested: list → find → download
- [ ] API endpoints are properly documented with examples
- [ ] System handles edge cases (expired URLs, missing invoices) gracefully

## All Needed Context

### Documentation & References
```yaml
- file: backend/app/api/upload.py
  why: Existing API patterns, error handling, and response models to follow
  critical: Uses structlog for logging, HTTPException for errors, FastAPI Query params

- file: backend/app/services/database_service.py
  why: Database service patterns for CRUD operations and pagination
  critical: Uses Supabase client, PaginationParams, async/await patterns

- file: backend/app/models/invoice.py
  why: Existing response models and validation patterns
  critical: InvoiceListResponse exists but incomplete, need new models

- file: backend/app/models/upload_batch.py
  why: Database model structure and field names
  critical: Contains invoice-specific fields like supplier_code, invoice_number, s3_key

- file: backend/tests/integration/test_invoice_download_system.py
  why: Testing patterns and existing test data for validation
  critical: Uses existing Lawn Fawn invoice for testing, shows database query patterns

- url: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
  why: Date filtering and parsing for API parameters
  section: strftime format codes for ISO date validation

- url: https://fastapi.tiangolo.com/tutorial/query-params-str-validations/
  why: FastAPI Query parameter validation patterns
  section: Query validation, optional parameters, and constraints
```

### Current Codebase Structure
```bash
backend/
├── app/
│   ├── api/
│   │   └── upload.py              # Existing API with incomplete /invoices endpoint
│   ├── models/
│   │   ├── invoice.py             # Response models (InvoiceListResponse exists)
│   │   └── upload_batch.py        # Database model with invoice fields
│   ├── services/
│   │   ├── database_service.py    # Database operations (needs extension)
│   │   └── invoice_processor.py   # Invoice processing (has download methods)
│   └── core/
│       └── database.py            # Supabase client setup
├── tests/
│   ├── integration/
│   │   └── test_invoice_download_system.py  # Existing test patterns
│   └── connectivity/
└── migrations/
```

### Desired Codebase Structure (additions)
```bash
backend/
├── app/
│   ├── models/
│   │   └── invoice.py             # ADD: InvoiceSummary, PaginationInfo models
│   ├── services/
│   │   └── database_service.py    # ADD: list_upload_batches_with_filters method
│   └── api/
│       └── upload.py              # COMPLETE: /invoices endpoint implementation
├── tests/
│   └── test_invoice_management_api.py  # NEW: Comprehensive API tests
└── migrations/
    └── 005_invoice_management_indexes.sql  # NEW: Performance indexes
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Supabase client uses .execute() and returns .data array
result = supabase.table('upload_batches').select('*').execute()
invoices = [UploadBatch(**item) for item in result.data]

# CRITICAL: FastAPI Query params need proper validation
from fastapi import Query
limit: int = Query(50, ge=1, le=100)  # Validates range

# CRITICAL: Date filtering requires proper ISO format validation
from datetime import datetime
date_from = datetime.fromisoformat(date_string) if date_string else None

# CRITICAL: Pagination requires total count for has_more calculation
count_result = supabase.table('upload_batches').select('count').execute()
total = count_result.count

# CRITICAL: Search requires case-insensitive partial matching
query = query.ilike('original_filename', f'%{search}%')

# GOTCHA: UUID fields in database are strings, need str() conversion
query = query.eq('id', str(batch_id))

# GOTCHA: Supabase range() is inclusive on both ends
query = query.range(offset, offset + limit - 1)
```

## Implementation Blueprint

### Data Models and Structure

Create enhanced response models for invoice management API:
```python
# ADD to backend/app/models/invoice.py

class InvoiceSummary(BaseModel):
    """Summary information for invoice list display."""
    batch_id: str = Field(..., description="Batch identifier")
    supplier: str = Field(..., description="Supplier code")
    invoice_number: Optional[str] = Field(None, description="Invoice number")
    invoice_date: Optional[str] = Field(None, description="Invoice date")
    products_found: int = Field(0, description="Number of products found")
    processing_date: datetime = Field(..., description="When invoice was processed")
    original_filename: str = Field(..., description="Original uploaded filename")
    parsing_success_rate: float = Field(0.0, description="Parsing success rate percentage")
    file_size_mb: float = Field(0.0, description="File size in megabytes")
    currency: Optional[str] = Field(None, description="Invoice currency")
    total_amount: Optional[float] = Field(None, description="Total invoice amount")

class PaginationInfo(BaseModel):
    """Pagination metadata for API responses."""
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Items skipped")
    next_offset: Optional[int] = Field(None, description="Next page offset")
    has_more: bool = Field(..., description="More items available")

# MODIFY existing InvoiceListResponse
class InvoiceListResponse(BaseModel):
    """Enhanced response for invoice list endpoint."""
    success: bool = Field(..., description="Request success status")
    invoices: List[InvoiceSummary] = Field(..., description="List of invoice summaries")
    total_count: int = Field(..., description="Total number of invoices")
    has_more: bool = Field(..., description="More invoices available")
    pagination: PaginationInfo = Field(..., description="Pagination metadata")
    error: Optional[str] = Field(None, description="Error message if failed")
```

### List of Tasks to Complete (in order)

```yaml
Task 1: Extend Database Service
MODIFY backend/app/services/database_service.py:
  - ADD list_upload_batches_with_filters method
  - IMPLEMENT pagination, filtering, and search
  - FOLLOW existing async patterns and error handling
  - USE Supabase client patterns from existing methods

Task 2: Create Database Indexes
CREATE backend/migrations/005_invoice_management_indexes.sql:
  - ADD indexes for supplier_code, created_at, invoice_number
  - ADD full-text search index for search functionality
  - OPTIMIZE query performance for filtering operations

Task 3: Enhance Response Models
MODIFY backend/app/models/invoice.py:
  - ADD InvoiceSummary and PaginationInfo models
  - ENHANCE InvoiceListResponse with pagination
  - FOLLOW existing validation patterns

Task 4: Complete API Endpoint
MODIFY backend/app/api/upload.py:
  - COMPLETE /invoices endpoint implementation
  - ADD proper Query parameter validation
  - IMPLEMENT filtering, pagination, and search
  - FOLLOW existing error handling patterns

Task 5: Create Comprehensive Tests
CREATE backend/tests/test_invoice_management_api.py:
  - TEST all API endpoints with various parameters
  - TEST pagination, filtering, and search functionality
  - TEST error cases and edge conditions
  - USE existing test patterns and fixtures

Task 6: Integration Testing
MODIFY backend/tests/integration/test_invoice_download_system.py:
  - ADD complete workflow testing (list → download)
  - TEST with existing Lawn Fawn invoice data
  - VALIDATE API responses match expected format
```

### Task 1: Database Service Extension
```python
# ADD to backend/app/services/database_service.py

async def list_upload_batches_with_filters(
    self,
    limit: int = 50,
    offset: int = 0,
    supplier: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Tuple[List[UploadBatch], int]:
    """
    List upload batches with comprehensive filtering and pagination.
    
    PATTERN: Follow existing get_upload_batches method structure
    CRITICAL: Must return both results and total count for pagination
    """
    try:
        # Build base query
        query = self.client.table('upload_batches').select('*')
        count_query = self.client.table('upload_batches').select('count')
        
        # Apply filters to both queries
        if supplier:
            query = query.eq('supplier_code', supplier)
            count_query = count_query.eq('supplier_code', supplier)
        
        if date_from:
            query = query.gte('created_at', date_from.isoformat())
            count_query = count_query.gte('created_at', date_from.isoformat())
            
        if date_to:
            query = query.lte('created_at', date_to.isoformat())
            count_query = count_query.lte('created_at', date_to.isoformat())
        
        if search:
            # CRITICAL: Use ilike for case-insensitive search
            search_pattern = f'%{search}%'
            search_filter = f'original_filename.ilike.{search_pattern},invoice_number.ilike.{search_pattern}'
            query = query.or_(search_filter)
            count_query = count_query.or_(search_filter)
        
        # Get total count first
        total_result = count_query.execute()
        total_count = total_result.count
        
        # Apply sorting and pagination
        desc = sort_order.lower() == 'desc'
        query = query.order(sort_by, desc=desc)
        query = query.range(offset, offset + limit - 1)
        
        # Execute query
        result = query.execute()
        batches = [UploadBatch(**item) for item in result.data]
        
        logger.info(
            "Listed upload batches with filters",
            total_count=total_count,
            returned_count=len(batches),
            filters={'supplier': supplier, 'search': search}
        )
        
        return batches, total_count
        
    except Exception as e:
        logger.error("Failed to list upload batches with filters", error=str(e))
        raise
```

### Task 4: Complete API Endpoint
```python
# MODIFY backend/app/api/upload.py - replace existing /invoices endpoint

@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    limit: int = Query(50, ge=1, le=100, description="Number of invoices to return"),
    offset: int = Query(0, ge=0, description="Number of invoices to skip"),
    supplier: Optional[str] = Query(None, description="Filter by supplier code"),
    date_from: Optional[str] = Query(None, description="Filter invoices after this date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter invoices before this date (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, min_length=1, description="Search in filename or invoice number"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
) -> InvoiceListResponse:
    """
    List processed invoices with comprehensive filtering and pagination.
    
    PATTERN: Follow existing endpoint structure with try/catch and logging
    CRITICAL: Validate date parameters and handle parsing errors
    """
    logger.info(
        "Invoice list request received",
        limit=limit,
        offset=offset,
        supplier=supplier,
        date_from=date_from,
        date_to=date_to,
        search=search
    )
    
    try:
        # Validate and parse date parameters
        parsed_date_from = None
        parsed_date_to = None
        
        if date_from:
            try:
                parsed_date_from = datetime.fromisoformat(date_from)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date_from format. Use YYYY-MM-DD"
                )
        
        if date_to:
            try:
                parsed_date_to = datetime.fromisoformat(date_to)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date_to format. Use YYYY-MM-DD"
                )
        
        # Get database service
        db_service = get_database_service()
        
        # Query with filters
        batches, total_count = await db_service.list_upload_batches_with_filters(
            limit=limit,
            offset=offset,
            supplier=supplier,
            date_from=parsed_date_from,
            date_to=parsed_date_to,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Convert to response format
        invoice_summaries = []
        for batch in batches:
            # CRITICAL: Handle missing fields gracefully
            summary = InvoiceSummary(
                batch_id=str(batch.id),
                supplier=batch.supplier_code or "unknown",
                invoice_number=getattr(batch, 'invoice_number', None),
                invoice_date=getattr(batch, 'invoice_date', None),
                products_found=batch.total_products,
                processing_date=batch.created_at,
                original_filename=batch.original_filename or "unknown",
                parsing_success_rate=getattr(batch, 'parsing_success_rate', 0.0),
                file_size_mb=round((batch.file_size or 0) / (1024 * 1024), 2),
                currency=getattr(batch, 'currency_code', None),
                total_amount=float(getattr(batch, 'total_amount_original', 0)) if getattr(batch, 'total_amount_original') else None
            )
            invoice_summaries.append(summary)
        
        # Calculate pagination info
        has_more = (offset + limit) < total_count
        next_offset = offset + limit if has_more else None
        
        pagination = PaginationInfo(
            limit=limit,
            offset=offset,
            next_offset=next_offset,
            has_more=has_more
        )
        
        logger.info(
            "Invoice list request completed",
            total_count=total_count,
            returned_count=len(invoice_summaries),
            has_more=has_more
        )
        
        return InvoiceListResponse(
            success=True,
            invoices=invoice_summaries,
            total_count=total_count,
            has_more=has_more,
            pagination=pagination,
            error=None
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            "Error listing invoices",
            error=str(e),
            limit=limit,
            offset=offset
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list invoices: {str(e)}"
        )
```

### Integration Points
```yaml
DATABASE:
  - migration: "005_invoice_management_indexes.sql"
  - indexes: "supplier_code, created_at, invoice_number, full-text search"
  
API:
  - modify: "backend/app/api/upload.py"
  - pattern: "Follow existing endpoint structure and error handling"
  
MODELS:
  - enhance: "backend/app/models/invoice.py"
  - pattern: "Follow existing Pydantic model patterns"
  
SERVICES:
  - extend: "backend/app/services/database_service.py"
  - pattern: "Follow existing async database service methods"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
cd backend
ruff check app/api/upload.py app/services/database_service.py app/models/invoice.py --fix
mypy app/api/upload.py app/services/database_service.py app/models/invoice.py

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests
```python
# CREATE backend/tests/test_invoice_management_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_invoices_basic():
    """Test basic invoice listing functionality"""
    response = client.get("/api/invoices")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "invoices" in data
    assert "total_count" in data
    assert "pagination" in data

def test_list_invoices_pagination():
    """Test pagination parameters"""
    response = client.get("/api/invoices?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["limit"] == 10
    assert data["pagination"]["offset"] == 0

def test_list_invoices_invalid_limit():
    """Test invalid limit parameter"""
    response = client.get("/api/invoices?limit=200")
    assert response.status_code == 422  # Validation error

def test_list_invoices_supplier_filter():
    """Test supplier filtering"""
    response = client.get("/api/invoices?supplier=lawnfawn")
    assert response.status_code == 200
    data = response.json()
    # All returned invoices should be from lawnfawn
    for invoice in data["invoices"]:
        assert invoice["supplier"] == "lawnfawn"

def test_list_invoices_date_filter():
    """Test date range filtering"""
    response = client.get("/api/invoices?date_from=2025-01-01&date_to=2025-12-31")
    assert response.status_code == 200

def test_list_invoices_invalid_date():
    """Test invalid date format"""
    response = client.get("/api/invoices?date_from=invalid-date")
    assert response.status_code == 400

def test_list_invoices_search():
    """Test search functionality"""
    response = client.get("/api/invoices?search=CPSummer25")
    assert response.status_code == 200
    data = response.json()
    # Should find the test invoice
    assert any("CPSummer25" in (inv.get("invoice_number", "") or "") for inv in data["invoices"])
```

```bash
# Run and iterate until passing:
cd backend
uv run pytest tests/test_invoice_management_api.py -v
# If failing: Read error, understand root cause, fix code, re-run
```

### Level 3: Integration Test
```bash
# Start the service
cd backend
uv run python -m app.main

# Test the complete workflow
curl -X GET "http://localhost:8000/api/invoices?limit=5" \
  -H "Accept: application/json"

# Expected: {"success": true, "invoices": [...], "total_count": N, ...}

# Test with existing Lawn Fawn invoice
curl -X GET "http://localhost:8000/api/invoices?supplier=lawnfawn&search=CPSummer25" \
  -H "Accept: application/json"

# Test download workflow
# 1. Get batch_id from list response
# 2. Generate download URL
curl -X GET "http://localhost:8000/api/invoices/{batch_id}/download" \
  -H "Accept: application/json"

# Expected: {"success": true, "download_url": "https://...", ...}
```

## Testing Strategy (MANDATORY)

### Backend Tests
- [ ] Unit tests for database service filtering methods
- [ ] Unit tests for API endpoint parameter validation
- [ ] Integration tests for complete list → download workflow
- [ ] Error handling tests for invalid parameters
- [ ] Performance tests with large datasets

### Test Data Requirements
- [ ] Use existing Lawn Fawn invoice: `invoices/lawnfawn/2025/07/20250706_125003_KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf`
- [ ] Test with multiple suppliers if available
- [ ] Test pagination with various limits and offsets
- [ ] Test search with different terms

### Test Execution Plan
- [ ] Run existing tests to ensure no regression: `uv run pytest tests/ -v`
- [ ] Add new API tests: `uv run pytest tests/test_invoice_management_api.py -v`
- [ ] Run integration tests: `cd backend && python tests/integration/test_invoice_download_system.py`
- [ ] Test complete workflow manually with curl commands

## Documentation Updates Required (MANDATORY)

### API Documentation
- [ ] Update OpenAPI/Swagger documentation for enhanced /invoices endpoint
- [ ] Document all query parameters with examples
- [ ] Add response schema examples
- [ ] Document error responses and status codes

### Code Documentation
- [ ] Add comprehensive docstrings to new database methods (Google style)
- [ ] Document API endpoint parameters and responses
- [ ] Add inline comments for complex filtering logic
- [ ] Update type hints for all new functions

### Integration Documentation
- [ ] Update README.md with new API endpoints
- [ ] Document complete user workflow examples
- [ ] Add troubleshooting guide for common issues

## Final Validation Checklist
- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] No linting errors: `uv run ruff check app/`
- [ ] No type errors: `uv run mypy app/`
- [ ] Manual API test successful: `curl -X GET "http://localhost:8000/api/invoices"`
- [ ] Complete workflow tested: list → find batch_id → download
- [ ] Error cases handled gracefully (invalid dates, missing invoices)
- [ ] Logs are informative and structured
- [ ] Database indexes created for performance
- [ ] API documentation updated
- [ ] All testing requirements met
- [ ] Ready for PRP completion workflow

---

## Anti-Patterns to Avoid
- ❌ Don't create new database connection patterns - use existing Supabase client
- ❌ Don't skip parameter validation - use FastAPI Query with constraints
- ❌ Don't ignore pagination performance - implement proper counting
- ❌ Don't hardcode field mappings - handle missing fields gracefully
- ❌ Don't skip error logging - use structured logging with context
- ❌ Don't return raw database objects - convert to proper response models
- ❌ Don't skip testing with real data - use existing Lawn Fawn invoice
- ❌ Don't ignore database indexes - create them for filtered fields
