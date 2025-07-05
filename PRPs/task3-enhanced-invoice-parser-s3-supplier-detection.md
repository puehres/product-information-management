name: "Enhanced Invoice Parser with S3 Storage & Supplier Detection"
description: |
  Comprehensive PDF invoice processing system with automatic supplier detection from invoice headers, 
  S3-based cloud storage for original invoices, intelligent product data extraction from supplier-specific formats, 
  invoice metadata parsing, presigned URL download capability, comprehensive error handling for unknown suppliers, 
  supplier/manufacturer distinction tracking, single upload workflow, and real-time status reporting with parsing success rates.

## Goal
Build a production-ready invoice processing system that automatically detects suppliers (LawnFawn, Craftlines, Mama Elephant) from PDF invoice headers, stores original invoices securely in AWS S3, extracts product data using supplier-specific parsing strategies, tracks supplier vs manufacturer distinction, and provides comprehensive status reporting with download capabilities for processed invoices.

## Why
- **Business Value**: Eliminates manual invoice data entry, reducing 5+ hours of work to 30 minutes
- **User Impact**: Enables automatic processing of LawnFawn invoices with CP-Summer25 format as primary use case
- **Integration**: Builds foundation for Task 4 (web scraping) by providing structured product data with SKUs
- **Problems Solved**: Manual PDF parsing, file storage management, supplier identification, currency handling

## What
User uploads PDF invoice → System detects supplier → Parses product data → Stores in S3 → Returns structured results with download capability

### Success Criteria
- [ ] Automatically detect LawnFawn supplier from invoice header with 95% confidence
- [ ] Parse LawnFawn invoice table extracting SKU, category, product name, prices, quantities
- [ ] Store original PDF in S3 with organized folder structure (invoices/lawnfawn/2025/01/)
- [ ] Generate presigned URLs for secure invoice downloads (1-hour expiration)
- [ ] Handle unknown suppliers with clear error messages listing supported suppliers
- [ ] Track supplier (invoice issuer) vs manufacturer (product maker) distinction
- [ ] Store USD prices without conversion, extract invoice metadata (number, date)
- [ ] Provide real-time status reporting with parsing success rates
- [ ] Support single upload workflow with comprehensive error handling

## S3 Setup Completion Status ✅

### AWS S3 Infrastructure (COMPLETED)
- **Bucket Name**: `sw-product-processing-bucket`
- **Region**: `eu-north-1` (Stockholm, Sweden)
- **Bucket ARN**: `arn:aws:s3:::sw-product-processing-bucket`
- **IAM User**: `product-automation-s3-user`
- **Access Key ID**: `${AWS_ACCESS_KEY_ID}` (configured in backend/.env)
- **Secret Access Key**: `${AWS_SECRET_ACCESS_KEY}` (configured in backend/.env)
- **Bucket Configuration**: Private bucket with block public access enabled
- **Encryption**: Amazon S3 managed keys (SSE-S3)
- **Versioning**: Enabled for backup and recovery

### S3 Setup Validation
- [x] Bucket created successfully in eu-north-1
- [x] IAM user created with programmatic access
- [x] Access keys generated and secured
- [x] Bucket permissions configured (private)
- [x] Ready for invoice storage with organized folder structure

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://pdfplumber.readthedocs.io/en/latest/reference.html#table-extraction
  why: Core PDF table extraction methods for invoice parsing
  
- url: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html
  why: Secure file access with time-limited URLs for invoice downloads
  
- url: https://fastapi.tiangolo.com/tutorial/request-files/
  why: Handling multipart file uploads for PDF invoices
  
- file: backend/app/models/upload_batch.py
  why: Existing upload batch model patterns and validation to extend
  
- file: backend/app/core/config.py
  why: Configuration patterns for S3 credentials and file processing settings
  
- file: backend/app/models/base.py
  why: Base model patterns, enums (FileType, BatchStatus), and validation approaches
  
- doc: https://docs.python.org/3/library/re.html
  section: Pattern matching for supplier detection from invoice headers
  critical: Use re.IGNORECASE for case-insensitive supplier name matching

- docfile: features/task3-enhanced-invoice-parser-s3-supplier-detection.md
  why: Complete feature specification with supplier detection patterns and API design
```

### Current Codebase tree
```bash
backend/
├── app/
│   ├── core/
│   │   ├── config.py          # Settings with Pydantic, add S3 config here
│   │   ├── database.py        # Supabase client patterns
│   │   └── logging.py         # Structured logging patterns
│   ├── models/
│   │   ├── base.py           # FileType.PDF, BatchStatus enums, BaseDBModel
│   │   ├── upload_batch.py   # UploadBatch model to extend with S3 fields
│   │   ├── product.py        # Product model to extend with manufacturer tracking
│   │   └── supplier.py       # Supplier model for detection patterns
│   ├── services/
│   │   └── database_service.py # Database operations patterns
│   ├── api/
│   │   └── __init__.py       # Empty - need to create upload endpoints
│   └── main.py              # FastAPI app - add invoice router here
├── requirements.txt          # Add pdfplumber, boto3 dependencies
└── migrations/
    └── 001_initial_schema.sql # Database schema with upload_batches, products tables
```

### Desired Codebase tree with files to be added
```bash
backend/
├── app/
│   ├── services/
│   │   ├── pdf_parser.py           # PDF parsing with pdfplumber
│   │   ├── supplier_detector.py    # Supplier detection from headers
│   │   ├── s3_manager.py          # S3 upload/download operations
│   │   └── invoice_processor.py   # Main processing pipeline
│   ├── api/
│   │   └── upload.py              # FastAPI endpoints for invoice upload
│   ├── models/
│   │   └── invoice.py             # Invoice-specific Pydantic models
│   └── parsers/
│       ├── __init__.py
│       ├── base.py               # Base parsing strategy
│       ├── lawnfawn.py          # LawnFawn-specific parsing
│       ├── craftlines.py        # Craftlines parsing (future)
│       └── mama_elephant.py     # Mama Elephant parsing (future)
├── tests/
│   ├── test_pdf_parser.py        # PDF parsing unit tests
│   ├── test_supplier_detector.py # Supplier detection tests
│   ├── test_s3_manager.py       # S3 operations tests
│   └── test_upload_api.py       # API endpoint tests
└── requirements.txt              # Add: pdfplumber==0.10.3, boto3==1.34.0
```

### Known Gotchas of our codebase & Library Quirks
```python
# CRITICAL: Supabase client requires async operations
# Example: await supabase.table('upload_batches').insert(data).execute()

# CRITICAL: pdfplumber requires file path, not bytes
# Must save uploaded bytes to temp file: with tempfile.NamedTemporaryFile() as tmp

# CRITICAL: FastAPI UploadFile.read() is async
# Example: file_content = await file.read()

# CRITICAL: S3 presigned URLs expire - store expiration time
# Example: expires_in=3600 for 1-hour expiration

# CRITICAL: Use Pydantic validators for data validation
# Example: @validator('supplier_sku') def validate_sku(cls, v): ...

# CRITICAL: Follow existing enum patterns from base.py
# Example: FileType.PDF, BatchStatus.PROCESSING

# CRITICAL: Use structured logging from core.logging
# Example: logger.info("Processing invoice", batch_id=batch_id, supplier=supplier)

# CRITICAL: Configuration via Pydantic Settings in core/config.py
# Example: s3_bucket_name: str = Field(default="product-processing-bucket")
```

## Implementation Blueprint

### Data models and structure

Create the core data models to ensure type safety and consistency.
```python
# backend/app/models/invoice.py - New invoice-specific models
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime

class InvoiceUploadRequest(BaseModel):
    """Request model for invoice upload - handled by FastAPI File upload"""
    pass

class SupplierDetectionResult(BaseModel):
    """Result of supplier detection from PDF content"""
    supplier_code: str = Field(..., description="Detected supplier code")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence 0-1")
    matched_patterns: List[str] = Field(..., description="Patterns that matched")
    detection_method: str = Field(..., description="How supplier was detected")

class InvoiceMetadata(BaseModel):
    """Extracted invoice metadata"""
    invoice_number: Optional[str] = Field(None, description="Invoice number")
    invoice_date: Optional[str] = Field(None, description="Invoice date")
    ship_date: Optional[str] = Field(None, description="Ship date")
    currency: str = Field(default="USD", description="Invoice currency")
    total_amount: Optional[Decimal] = Field(None, description="Total invoice amount")

class ParsedProduct(BaseModel):
    """Single product parsed from invoice"""
    supplier_sku: str = Field(..., description="SKU from invoice")
    manufacturer: str = Field(..., description="Product manufacturer")
    manufacturer_sku: str = Field(..., description="Original manufacturer SKU")
    category: str = Field(..., description="Product category")
    product_name: str = Field(..., description="Product name")
    quantity: int = Field(..., ge=1, description="Quantity ordered")
    price_usd: Decimal = Field(..., ge=0, description="USD price per unit")
    line_total_usd: Decimal = Field(..., ge=0, description="Total line amount USD")
    origin_country: Optional[str] = Field(None, description="Country of origin")
    tariff_code: Optional[str] = Field(None, description="Tariff code")
    raw_description: str = Field(..., description="Original description from invoice")
    line_number: int = Field(..., ge=1, description="Line number in invoice")

class InvoiceParsingResult(BaseModel):
    """Complete result of invoice parsing"""
    supplier: str = Field(..., description="Detected supplier")
    metadata: InvoiceMetadata = Field(..., description="Invoice metadata")
    products: List[ParsedProduct] = Field(..., description="Parsed products")
    total_products: int = Field(..., ge=0, description="Total products found")
    parsing_success_rate: float = Field(..., ge=0, le=100, description="Success rate percentage")
    parsing_errors: List[str] = Field(default_factory=list, description="Parsing errors")

class InvoiceUploadResponse(BaseModel):
    """Response for invoice upload API"""
    success: bool = Field(..., description="Upload success status")
    batch_id: Optional[str] = Field(None, description="Created batch ID")
    supplier: Optional[str] = Field(None, description="Detected supplier")
    products_found: Optional[int] = Field(None, description="Number of products found")
    parsing_success_rate: Optional[float] = Field(None, description="Parsing success rate")
    invoice_metadata: Optional[Dict[str, Any]] = Field(None, description="Invoice metadata")
    s3_key: Optional[str] = Field(None, description="S3 storage key")
    download_url: Optional[str] = Field(None, description="Download URL")
    error: Optional[str] = Field(None, description="Error type if failed")
    message: str = Field(..., description="Response message")
    supported_suppliers: Optional[List[str]] = Field(None, description="Supported suppliers if error")
```

### List of tasks to be completed to fulfill the PRP in order

```yaml
Task 1: Add Required Dependencies
MODIFY backend/requirements.txt:
  - ADD: pdfplumber==0.10.3  # PDF table extraction
  - ADD: boto3==1.34.0       # AWS S3 operations
  - PRESERVE: existing dependencies

Task 2: Extend Configuration for S3 and Invoice Processing
MODIFY backend/app/core/config.py:
  - FIND pattern: "class Settings(BaseSettings):"
  - ADD after existing fields:
    # AWS S3 Configuration (ACTUAL VALUES FROM SETUP)
    aws_access_key_id: Optional[str] = Field(None, description="AWS access key")
    aws_secret_access_key: Optional[str] = Field(None, description="AWS secret key")
    aws_region: str = Field(default="eu-north-1", description="AWS region - Stockholm")
    s3_bucket_name: str = Field(default="sw-product-processing-bucket", description="S3 bucket name")
    s3_invoice_prefix: str = Field(default="invoices", description="S3 prefix for invoices")
    
    # Invoice Processing Configuration
    invoice_download_expiration: int = Field(default=3600, description="Download URL expiration seconds")
    temp_file_cleanup: bool = Field(default=True, description="Auto-cleanup temp files")
  - PRESERVE: existing configuration patterns

Task 3: Create Invoice-Specific Models
CREATE backend/app/models/invoice.py:
  - MIRROR pattern from: backend/app/models/upload_batch.py
  - IMPLEMENT: InvoiceUploadResponse, SupplierDetectionResult, InvoiceMetadata, ParsedProduct, InvoiceParsingResult
  - USE: Pydantic validators for data validation
  - FOLLOW: BaseModel patterns from base.py

Task 4: Create Supplier Detection Service
CREATE backend/app/services/supplier_detector.py:
  - IMPLEMENT: SupplierDetectionService class
  - PATTERN: Use regex patterns for header matching
  - CONFIDENCE: LawnFawn 95%, Craftlines 90%, Mama Elephant 85%
  - ERROR: Raise UnknownSupplierError for unsupported suppliers
  - LOGGING: Use structured logging from core.logging

Task 5: Create S3 Management Service
CREATE backend/app/services/s3_manager.py:
  - IMPLEMENT: S3InvoiceManager class
  - METHODS: upload_invoice(), generate_download_url(), delete_invoice()
  - PATTERN: Use boto3 client with error handling
  - SECURITY: Private bucket with presigned URLs
  - ORGANIZATION: invoices/{supplier}/{year}/{month}/ structure

Task 6: Create PDF Parser Service
CREATE backend/app/services/pdf_parser.py:
  - IMPLEMENT: PDFParserService class
  - LIBRARY: Use pdfplumber for table extraction
  - PATTERN: Extract text for supplier detection, tables for products
  - TEMP FILES: Use tempfile.NamedTemporaryFile for pdfplumber
  - ERROR: Handle malformed PDFs gracefully

Task 7: Create Parsing Strategy Base Classes
CREATE backend/app/parsers/base.py:
  - IMPLEMENT: InvoiceParsingStrategy abstract base class
  - METHODS: parse_invoice(), extract_metadata(), parse_product_table()
  - PATTERN: Strategy pattern for supplier-specific parsing

CREATE backend/app/parsers/lawnfawn.py:
  - IMPLEMENT: LawnFawnParsingStrategy
  - FORMAT: "LF1142 - Lawn Cuts - Stitched Rectangle Frames Dies"
  - METADATA: Extract invoice number, ship date from header
  - VALIDATION: Ensure LF SKU format, handle parsing errors

Task 8: Create Main Invoice Processor
CREATE backend/app/services/invoice_processor.py:
  - IMPLEMENT: InvoiceProcessorService class
  - PIPELINE: detect_supplier() → parse_invoice() → upload_to_s3() → store_in_db()
  - PATTERN: Use existing database_service patterns
  - TRANSACTIONS: Wrap in database transactions
  - PROGRESS: Update batch status throughout processing

Task 9: Extend Database Models for Invoice Fields
MODIFY backend/app/models/upload_batch.py:
  - ADD fields: s3_key, s3_url, original_filename, file_size_bytes
  - ADD fields: supplier_detection_method, supplier_detection_confidence
  - ADD fields: invoice_number, invoice_date, currency_code, total_amount_original
  - ADD fields: parsing_success_rate, download_count, last_downloaded_at
  - PRESERVE: existing field patterns and validators

MODIFY backend/app/models/product.py:
  - ADD fields: manufacturer, manufacturer_sku, manufacturer_website
  - ADD fields: quantity_ordered, line_total_usd, line_total_eur
  - ADD fields: origin_country, tariff_code, raw_description, line_number
  - CONSTRAINT: manufacturer required when manufacturer_sku present

Task 10: Create Upload API Endpoints
CREATE backend/app/api/upload.py:
  - IMPLEMENT: FastAPI router with upload_invoice endpoint
  - PATTERN: Use FastAPI File upload with UploadFile
  - VALIDATION: PDF file type, file size limits
  - ASYNC: Handle file.read() and background processing
  - RESPONSES: Use InvoiceUploadResponse model
  - ERROR: Handle UnknownSupplierError, S3UploadError

Task 11: Integrate Upload Router into Main App
MODIFY backend/app/main.py:
  - FIND pattern: "# TODO: Add API routers"
  - ADD: from app.api import upload
  - ADD: app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
  - PRESERVE: existing middleware and configuration

Task 12: Create Database Migration for New Fields
CREATE backend/migrations/003_invoice_processing_fields.sql:
  - ALTER TABLE upload_batches: Add S3 and invoice-specific fields
  - ALTER TABLE products: Add manufacturer and invoice-specific fields
  - CREATE INDEX: On s3_key, invoice_number, manufacturer fields
  - CONSTRAINT: Add manufacturer consistency constraint
```

### Per task pseudocode with CRITICAL details

```python
# Task 4: Supplier Detection Service
class SupplierDetectionService:
    SUPPLIER_PATTERNS = {
        'lawnfawn': {
            'company_names': ['Lawn Fawn', 'lawnfawn.com', 'Rancho Santa Margarita, CA 92688'],
            'confidence_weight': 0.95
        }
        # ... other suppliers
    }
    
    def detect_supplier(self, pdf_text: str) -> SupplierDetectionResult:
        # PATTERN: Use re.search with re.IGNORECASE
        for supplier_code, patterns in self.SUPPLIER_PATTERNS.items():
            confidence = 0
            matched_patterns = []
            
            for pattern in patterns['company_names']:
                if pattern.lower() in pdf_text.lower():
                    confidence += 0.4
                    matched_patterns.append(f"company_name: {pattern}")
            
            # CRITICAL: Apply confidence weight
            confidence *= patterns['confidence_weight']
            
            if confidence > 0.5:  # Minimum threshold
                return SupplierDetectionResult(
                    supplier_code=supplier_code,
                    confidence=confidence,
                    matched_patterns=matched_patterns,
                    detection_method="header_pattern"
                )
        
        # CRITICAL: Raise specific exception for unknown suppliers
        raise UnknownSupplierError("No supported supplier detected")

# Task 5: S3 Manager Service
class S3InvoiceManager:
    def __init__(self, bucket_name: str, region: str):
        # CRITICAL: Use boto3 client with proper error handling
        self.s3_client = boto3.client('s3', region_name=region)
        self.bucket_name = bucket_name
    
    def upload_invoice(self, file_data: bytes, supplier: str, filename: str) -> Dict[str, str]:
        # PATTERN: Generate organized S3 key
        now = datetime.now()
        s3_key = f"invoices/{supplier}/{now.year}/{now.month:02d}/{filename}"
        
        try:
            # CRITICAL: Set proper content type and metadata
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_data,
                ContentType='application/pdf',
                Metadata={'supplier': supplier, 'upload_timestamp': now.isoformat()}
            )
            return {'s3_key': s3_key, 's3_url': f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"}
        except Exception as e:
            raise S3UploadError(f"Failed to upload to S3: {e}")

# Task 6: PDF Parser Service  
class PDFParserService:
    def extract_text_and_tables(self, file_data: bytes) -> Tuple[str, List[List[List[str]]]]:
        # CRITICAL: pdfplumber requires file path, not bytes
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(file_data)
            tmp_file.flush()
            
            try:
                with pdfplumber.open(tmp_file.name) as pdf:
                    # Extract full text for supplier detection
                    full_text = ""
                    all_tables = []
                    
                    for page in pdf.pages:
                        full_text += page.extract_text() or ""
                        tables = page.extract_tables()
                        if tables:
                            all_tables.extend(tables)
                    
                    return full_text, all_tables
            finally:
                # CRITICAL: Always cleanup temp file
                os.unlink(tmp_file.name)

# Task 8: Invoice Processor Pipeline
class InvoiceProcessorService:
    async def process_invoice(self, file_data: bytes, filename: str) -> InvoiceUploadResponse:
        try:
            # Step 1: Extract PDF content
            pdf_text, tables = self.pdf_parser.extract_text_and_tables(file_data)
            
            # Step 2: Detect supplier (CRITICAL: Can raise UnknownSupplierError)
            detection_result = self.supplier_detector.detect_supplier(pdf_text)
            
            # Step 3: Parse using supplier-specific strategy
            parsing_strategy = self.get_parsing_strategy(detection_result.supplier_code)
            parsing_result = parsing_strategy.parse_invoice(pdf_text, tables)
            
            # Step 4: Upload to S3
            s3_info = self.s3_manager.upload_invoice(file_data, detection_result.supplier_code, filename)
            
            # Step 5: Store in database (CRITICAL: Use transaction)
            async with self.db.transaction():
                batch = await self.create_upload_batch(detection_result, parsing_result, s3_info, filename)
                await self.create_products(batch.id, parsing_result.products)
            
            return InvoiceUploadResponse(
                success=True,
                batch_id=str(batch.id),
                supplier=detection_result.supplier_code,
                products_found=len(parsing_result.products),
                parsing_success_rate=parsing_result.parsing_success_rate,
                s3_key=s3_info['s3_key'],
                message="Invoice processed successfully"
            )
            
        except UnknownSupplierError as e:
            return InvoiceUploadResponse(
                success=False,
                error="unknown_supplier",
                message=str(e),
                supported_suppliers=list(self.SUPPORTED_SUPPLIERS)
            )

# Task 10: Upload API Endpoint
@router.post("/upload/invoice", response_model=InvoiceUploadResponse)
async def upload_invoice(file: UploadFile = File(...)) -> InvoiceUploadResponse:
    # CRITICAL: Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files supported")
    
    # CRITICAL: Read file content asynchronously
    file_content = await file.read()
    
    if len(file_content) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    
    # Process invoice
    processor = InvoiceProcessorService()
    result = await processor.process_invoice(file_content, file.filename)
    
    return result
```

### Integration Points
```yaml
DATABASE:
  - migration: "003_invoice_processing_fields.sql - Add S3 and invoice fields"
  - tables: "upload_batches, products - extend with new columns"
  
CONFIG:
  - add to: backend/app/core/config.py
  - pattern: "aws_access_key_id, s3_bucket_name, invoice_download_expiration"
  
ROUTES:
  - add to: backend/app/main.py  
  - pattern: "app.include_router(upload.router, prefix='/api/v1', tags=['upload'])"
  
DEPENDENCIES:
  - add to: backend/requirements.txt
  - pattern: "pdfplumber==0.10.3, boto3==1.34.0"

ENVIRONMENT_VARIABLES:
  - add to: backend/.env
  - secure_configuration: |
    # AWS S3 Configuration (CONFIGURED IN .env)
    AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
    AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    AWS_REGION=eu-north-1
    S3_BUCKET_NAME=sw-product-processing-bucket
    S3_INVOICE_PREFIX=invoices
    INVOICE_DOWNLOAD_EXPIRATION=3600
    TEMP_FILE_CLEANUP=true
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
cd backend
python -m ruff check app/services/pdf_parser.py --fix
python -m mypy app/services/pdf_parser.py
python -m ruff check app/api/upload.py --fix  
python -m mypy app/api/upload.py

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests
```python
# CREATE backend/tests/test_supplier_detector.py
def test_lawnfawn_detection():
    """Test LawnFawn supplier detection from header"""
    detector = SupplierDetectionService()
    pdf_text = "Lawn Fawn\nRancho Santa Margarita, CA 92688\nInvoice # CP-Summer25"
    
    result = detector.detect_supplier(pdf_text)
    assert result.supplier_code == "lawnfawn"
    assert result.confidence >= 0.9
    assert "Lawn Fawn" in str(result.matched_patterns)

def test_unknown_supplier_error():
    """Test unknown supplier raises proper error"""
    detector = SupplierDetectionService()
    pdf_text = "Unknown Company\nSome Address"
    
    with pytest.raises(UnknownSupplierError):
        detector.detect_supplier(pdf_text)

# CREATE backend/tests/test_pdf_parser.py  
def test_lawnfawn_table_parsing():
    """Test parsing LawnFawn invoice table format"""
    # Use sample table data matching screenshot format
    table_data = [
        ["Qty", "Description", "Price", "Origin", "Tariff Code", "Amount"],
        ["3", "LF1142 - Lawn Cuts - Stitched Rectangle Frames Dies", "12.40", "China", "8441.90.0000", "37.20T"]
    ]
    
    parser = LawnFawnParsingStrategy()
    products = parser._parse_product_table(table_data)
    
    assert len(products) == 1
    product = products[0]
    assert product['supplier_sku'] == "LF1142"
    assert product['category'] == "Lawn Cuts"
    assert product['product_name'] == "Stitched Rectangle Frames Dies"
    assert product['quantity'] == 3
    assert product['price_usd'] == 12.40
```

```bash
# Run and iterate until passing:
cd backend
python -m pytest tests/test_supplier_detector.py -v
python -m pytest tests/test_pdf_parser.py -v
# If failing: Read error, understand root cause, fix code, re-run
```

### Level 3: Integration Test
```bash
# Start the service
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Test the endpoint with sample PDF
curl -X POST http://localhost:8000/api/v1/upload/invoice \
  -F "file=@sample_lawnfawn_invoice.pdf" \
  -H "Accept: application/json"

# Expected: {"success": true, "supplier": "lawnfawn", "products_found": 12, ...}
# If error: Check logs for stack trace, verify S3 credentials
```

## Testing Strategy (MANDATORY)

### Backend Tests
- [ ] Unit tests for SupplierDetectionService with all supplier patterns
- [ ] Unit tests for PDFParserService with malformed PDF handling  
- [ ] Unit tests for S3InvoiceManager with mocked boto3 client
- [ ] Unit tests for LawnFawnParsingStrategy with table variations
- [ ] Integration tests for upload API endpoint with sample PDFs
- [ ] Error handling tests for unknown suppliers and S3 failures

### Test Execution Plan
- [ ] Run existing tests to ensure no regression: `pytest tests/ -v`
- [ ] Add new tests for all invoice processing components
- [ ] Test with actual LawnFawn invoice PDF (CP-Summer25 format)
- [ ] Validate S3 upload/download cycle with presigned URLs
- [ ] Test error scenarios: unknown supplier, malformed PDF, S3 failures

## Documentation Updates Required (MANDATORY)

### Core Documentation
- [ ] Update README.md with invoice processing setup (S3 credentials)
- [ ] Update API documentation for new upload endpoints
- [ ] Document supported invoice formats and supplier detection
- [ ] Create troubleshooting guide for common parsing issues

### Code Documentation
- [ ] Add docstrings to all new services (Google style)
- [ ] Document supplier detection patterns and confidence scoring
- [ ] Document S3 bucket organization and lifecycle policies
- [ ] Add inline comments for complex PDF parsing logic

## Final validation Checklist
- [ ] All tests pass: `python -m pytest tests/ -v`
- [ ] No linting errors: `python -m ruff check app/`
- [ ] No type errors: `python -m mypy app/`
- [ ] Manual test successful: Upload sample LawnFawn PDF via API
- [ ] S3 upload/download cycle works with presigned URLs
- [ ] Unknown supplier error handling works correctly
- [ ] Database records created with proper supplier/manufacturer distinction
- [ ] Invoice metadata extracted correctly (number, date, currency)
- [ ] Parsing success rate calculated and reported accurately
- [ ] All testing requirements met
- [ ] All documentation updated as specified above
- [ ] Ready for PRP completion workflow

---

## Anti-Patterns to Avoid
- ❌ Don't hardcode supplier patterns - use configuration
- ❌ Don't store files locally - use S3 for all file storage
- ❌ Don't ignore PDF parsing errors - handle gracefully with clear messages
- ❌ Don't use sync file operations - FastAPI requires async patterns
- ❌ Don't skip temp file cleanup - always use try/finally or context managers
- ❌ Don't expose S3 credentials in logs - use structured logging carefully
- ❌ Don't skip supplier detection validation - always verify confidence scores
- ❌ Don't mix supplier and manufacturer concepts - track both separately
