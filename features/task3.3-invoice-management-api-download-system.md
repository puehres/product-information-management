# Task 3.3: Invoice Management API & Download System

## Overview

Complete the missing invoice management functionality by implementing the `/api/invoices` list endpoint and enhancing the download system. This provides users with a complete workflow to discover, manage, and download their processed invoices.

## Business Context

Currently, users can upload invoices but have no way to:
- See what invoices they've uploaded previously
- Find batch_ids to generate download URLs
- Browse their invoice processing history
- Filter invoices by supplier or date
- Search for specific invoices

This creates a poor user experience where invoices are "fire and forget" with no management capabilities.

## Success Criteria

- [ ] Users can list all their processed invoices with pagination
- [ ] Filtering by supplier, date range, and search terms works correctly
- [ ] Download URLs are generated successfully for any processed invoice
- [ ] Complete user workflow tested: list → find → download
- [ ] API endpoints are properly documented with examples
- [ ] System handles edge cases (expired URLs, missing invoices) gracefully

## Core Requirements

### 1. Invoice List Endpoint

**Endpoint**: `GET /api/invoices`

**Query Parameters**:
- `limit` (int, default: 50, max: 100): Number of invoices to return
- `offset` (int, default: 0): Number of invoices to skip for pagination
- `supplier` (string, optional): Filter by supplier code (lawnfawn, craftlines, mama-elephant)
- `date_from` (ISO date, optional): Filter invoices processed after this date
- `date_to` (ISO date, optional): Filter invoices processed before this date
- `search` (string, optional): Search in invoice number, filename, or supplier

**Response Format**:
```json
{
  "success": true,
  "invoices": [
    {
      "batch_id": "uuid-here",
      "supplier": "lawnfawn",
      "invoice_number": "CPSummer25",
      "invoice_date": "2025-07-06",
      "products_found": 31,
      "processing_date": "2025-07-06T12:50:03Z",
      "original_filename": "KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf",
      "parsing_success_rate": 91.7,
      "file_size_mb": 2.4,
      "currency": "USD",
      "total_amount": 247.20
    }
  ],
  "total_count": 1,
  "has_more": false,
  "pagination": {
    "limit": 50,
    "offset": 0,
    "next_offset": null
  },
  "error": null
}
```

### 2. Enhanced Download System

**Current State**: Download endpoint exists but requires knowing the batch_id
**Enhancement**: Integrate with list endpoint for complete workflow

**Workflow**:
1. User calls `GET /api/invoices` to see available invoices
2. User finds desired invoice and gets `batch_id`
3. User calls `GET /api/invoices/{batch_id}/download` to get download URL
4. User downloads file using presigned URL

### 3. Search and Filtering

**Search Functionality**:
- Search across invoice numbers, filenames, and supplier names
- Case-insensitive partial matching
- Support for multiple search terms

**Filtering Options**:
- **Supplier**: Filter by specific supplier codes
- **Date Range**: Process date filtering (not invoice date)
- **Status**: Future enhancement for processing status
- **File Size**: Future enhancement for large/small files

### 4. Sorting Options

**Default Sort**: Processing date descending (newest first)

**Available Sorts**:
- `processing_date` (asc/desc)
- `supplier` (asc/desc)
- `invoice_number` (asc/desc)
- `products_found` (asc/desc)
- `parsing_success_rate` (asc/desc)

## Technical Implementation

### 1. Database Service Extensions

Add new methods to `DatabaseService`:

```python
async def list_upload_batches(
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
    List upload batches with filtering, pagination, and sorting.
    
    Returns:
        Tuple of (batches_list, total_count)
    """

async def search_upload_batches(
    self,
    search_term: str,
    limit: int = 50
) -> List[UploadBatch]:
    """Search upload batches by invoice number, filename, or supplier."""

async def get_upload_batch_summary(
    self,
    batch_id: UUID
) -> Optional[Dict[str, Any]]:
    """Get summary information for a specific batch."""
```

### 2. Response Models

Create new Pydantic models in `app/models/invoice.py`:

```python
class InvoiceSummary(BaseModel):
    """Summary information for invoice list display."""
    batch_id: str
    supplier: str
    invoice_number: Optional[str]
    invoice_date: Optional[str]
    products_found: int
    processing_date: datetime
    original_filename: str
    parsing_success_rate: float
    file_size_mb: float
    currency: Optional[str]
    total_amount: Optional[float]

class PaginationInfo(BaseModel):
    """Pagination metadata."""
    limit: int
    offset: int
    next_offset: Optional[int]
    has_more: bool

class InvoiceListResponse(BaseModel):
    """Response for invoice list endpoint."""
    success: bool
    invoices: List[InvoiceSummary]
    total_count: int
    has_more: bool
    pagination: PaginationInfo
    error: Optional[str]

class InvoiceSearchResponse(BaseModel):
    """Response for invoice search endpoint."""
    success: bool
    results: List[InvoiceSummary]
    search_term: str
    total_matches: int
    error: Optional[str]
```

### 3. API Endpoint Implementation

Complete the existing `/api/invoices` endpoint in `app/api/upload.py`:

```python
@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    supplier: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("processing_date"),
    sort_order: str = Query("desc")
) -> InvoiceListResponse:
    """List processed invoices with pagination and filtering."""

@router.get("/invoices/search", response_model=InvoiceSearchResponse)
async def search_invoices(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=100)
) -> InvoiceSearchResponse:
    """Search invoices by invoice number, filename, or supplier."""
```

### 4. Database Query Optimization

Add database indexes for efficient querying:

```sql
-- Migration 005: Invoice management indexes
CREATE INDEX IF NOT EXISTS idx_upload_batches_supplier ON upload_batches(supplier_code);
CREATE INDEX IF NOT EXISTS idx_upload_batches_created_at ON upload_batches(created_at);
CREATE INDEX IF NOT EXISTS idx_upload_batches_invoice_number ON upload_batches(invoice_number);
CREATE INDEX IF NOT EXISTS idx_upload_batches_filename ON upload_batches(original_filename);

-- Full-text search index for search functionality
CREATE INDEX IF NOT EXISTS idx_upload_batches_search ON upload_batches 
USING gin(to_tsvector('english', 
    COALESCE(invoice_number, '') || ' ' || 
    COALESCE(original_filename, '') || ' ' || 
    COALESCE(supplier_code, '')
));
```

## Testing Strategy

### 1. Test Data Setup

Use existing invoice for testing:
- **S3 URL**: `https://sw-product-processing-bucket.s3.eu-north-1.amazonaws.com/invoices/lawnfawn/2025/07/20250706_125003_KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf`
- **Expected Data**: Lawn Fawn invoice "CPSummer25" with ~31 products

### 2. API Testing

**List Endpoint Tests**:
```bash
# Basic list
GET /api/invoices

# Pagination
GET /api/invoices?limit=10&offset=0

# Supplier filtering
GET /api/invoices?supplier=lawnfawn

# Date filtering
GET /api/invoices?date_from=2025-07-01&date_to=2025-07-31

# Search
GET /api/invoices?search=CPSummer25

# Combined filters
GET /api/invoices?supplier=lawnfawn&search=CPSummer25&limit=5
```

**Download Workflow Test**:
```bash
# 1. List invoices to find batch_id
GET /api/invoices?supplier=lawnfawn

# 2. Get specific invoice details
GET /api/invoices/{batch_id}/details

# 3. Generate download URL
GET /api/invoices/{batch_id}/download

# 4. Test download URL works
curl -I {presigned_url}
```

### 3. Integration Testing

**Complete User Workflow**:
1. Upload invoice → get batch_id
2. List invoices → find uploaded invoice
3. Generate download URL → verify URL works
4. Download file → verify file integrity
5. Test URL expiration → verify security

**Edge Case Testing**:
- Empty invoice list
- Invalid batch_id for download
- Expired download URLs
- Large result sets (pagination)
- Invalid filter parameters
- SQL injection attempts in search

### 4. Performance Testing

**Database Performance**:
- Test with 100+ invoice records
- Verify index usage in query plans
- Test pagination performance
- Measure search query response times

**S3 Performance**:
- Test presigned URL generation speed
- Verify download URL accessibility
- Test concurrent download requests

## Error Handling

### 1. Validation Errors

```json
{
  "success": false,
  "error": "validation_error",
  "message": "Invalid parameters",
  "details": {
    "limit": "Must be between 1 and 100",
    "date_from": "Invalid date format, use YYYY-MM-DD"
  }
}
```

### 2. Not Found Errors

```json
{
  "success": false,
  "error": "not_found",
  "message": "Invoice not found",
  "batch_id": "uuid-here"
}
```

### 3. S3 Errors

```json
{
  "success": false,
  "error": "download_unavailable",
  "message": "Unable to generate download URL",
  "details": "S3 object may have been deleted or moved"
}
```

## API Documentation

### 1. OpenAPI Specification

Add comprehensive OpenAPI docs with:
- Parameter descriptions and validation rules
- Response schema examples
- Error response examples
- Usage examples for common workflows

### 2. Usage Examples

**Basic Invoice Management**:
```python
# List recent invoices
response = requests.get("/api/invoices?limit=10")
invoices = response.json()["invoices"]

# Find specific invoice
lawn_fawn_invoices = requests.get("/api/invoices?supplier=lawnfawn")

# Download invoice
batch_id = invoices[0]["batch_id"]
download_response = requests.get(f"/api/invoices/{batch_id}/download")
download_url = download_response.json()["download_url"]

# Download file
file_response = requests.get(download_url)
with open("invoice.pdf", "wb") as f:
    f.write(file_response.content)
```

## Security Considerations

### 1. Access Control

- All endpoints require proper authentication (future enhancement)
- Users can only see their own invoices (future enhancement)
- Rate limiting on search endpoints to prevent abuse

### 2. Download Security

- Presigned URLs expire after 1 hour (configurable)
- URLs are single-use for sensitive documents (future enhancement)
- S3 bucket is private with no public access

### 3. Input Validation

- Strict parameter validation to prevent SQL injection
- Search term length limits to prevent DoS
- Pagination limits to prevent resource exhaustion

## Future Enhancements

### 1. Advanced Filtering

- Filter by processing status (success/failed/partial)
- Filter by file size ranges
- Filter by product count ranges
- Filter by parsing success rate

### 2. Bulk Operations

- Bulk download multiple invoices as ZIP
- Bulk delete old invoices
- Bulk re-processing of failed invoices

### 3. Analytics

- Invoice processing statistics
- Supplier performance metrics
- Processing time trends
- Error rate analysis

## Dependencies

- **Task 3.1**: Migration System Fix (completed) - Need stable database operations
- **Database**: Existing upload_batches table with proper schema
- **S3**: Existing S3Manager service for download URL generation
- **API**: Existing FastAPI application structure

## Deliverables

1. **Database Service Extensions**: New query methods for listing and searching
2. **API Endpoints**: Complete `/api/invoices` implementation
3. **Response Models**: Proper Pydantic models for all responses
4. **Database Indexes**: Optimized queries for performance
5. **Integration Tests**: Complete workflow testing
6. **API Documentation**: Comprehensive endpoint documentation
7. **Error Handling**: Robust error responses for all edge cases

## Acceptance Criteria

- [ ] `/api/invoices` returns properly formatted invoice list
- [ ] Pagination works correctly with large datasets
- [ ] Filtering by supplier, date, and search works as specified
- [ ] Download workflow tested end-to-end with real invoice
- [ ] All API responses follow consistent error handling patterns
- [ ] Performance is acceptable with 100+ invoice records
- [ ] API documentation is complete with examples
- [ ] Integration tests cover all major workflows
- [ ] Edge cases are handled gracefully with proper error messages
