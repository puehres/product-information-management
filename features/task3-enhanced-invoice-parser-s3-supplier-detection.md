## FEATURE:

Enhanced Invoice Parser with S3 Storage & Supplier Detection - Comprehensive PDF invoice processing system with automatic supplier detection from invoice headers, S3-based cloud storage for original invoices, intelligent product data extraction from supplier-specific formats, invoice metadata parsing, presigned URL download capability, comprehensive error handling for unknown suppliers, supplier/manufacturer distinction tracking, single upload workflow, and real-time status reporting with parsing success rates.

## EXAMPLES:

[Reference examples in the `examples/` folder - will include:]
- LawnFawn invoice PDF samples with table structure and product data
- Supplier detection patterns and header identification examples
- S3 bucket organization and file naming conventions
- PDF parsing results with extracted product data and metadata
- API request/response examples for upload, status, and download endpoints
- Error handling scenarios for unknown suppliers and parsing failures
- Database records showing supplier vs manufacturer distinction
- Invoice status dashboard mockups with parsing results
- Presigned URL generation examples for secure downloads
- Currency handling examples (USD/EUR price storage)

## DOCUMENTATION:

### PDF Processing & Table Extraction
- **pdfplumber Documentation**: https://pdfplumber.readthedocs.io/en/latest/ - PDF table extraction and text parsing
- **PyPDF2 Documentation**: https://pypdf2.readthedocs.io/en/latest/ - Alternative PDF processing library
- **PDF Table Extraction**: https://pdfplumber.readthedocs.io/en/latest/reference.html#table-extraction - Table detection and parsing
- **Text Extraction**: https://pdfplumber.readthedocs.io/en/latest/reference.html#text-extraction - Raw text extraction from PDFs
- **PDF Structure Analysis**: https://pdfplumber.readthedocs.io/en/latest/reference.html#page-analysis - Understanding PDF layout

### AWS S3 Storage & File Management
- **boto3 Documentation**: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html - AWS SDK for Python
- **S3 Client**: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html - S3 service operations
- **Presigned URLs**: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html - Secure file access
- **S3 Lifecycle Policies**: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html - Automatic file cleanup
- **S3 Security**: https://docs.aws.amazon.com/AmazonS3/latest/userguide/security.html - Access control and encryption

### FastAPI File Upload & Processing
- **FastAPI File Uploads**: https://fastapi.tiangolo.com/tutorial/request-files/ - Handling multipart file uploads
- **Background Tasks**: https://fastapi.tiangolo.com/tutorial/background-tasks/ - Async processing workflows
- **Request Validation**: https://fastapi.tiangolo.com/tutorial/request-validation/ - Input validation and error handling
- **Response Models**: https://fastapi.tiangolo.com/tutorial/response-model/ - Structured API responses
- **Error Handling**: https://fastapi.tiangolo.com/tutorial/handling-errors/ - Custom exception handling

### Supplier Detection & Pattern Matching
- **Regular Expressions**: https://docs.python.org/3/library/re.html - Pattern matching for supplier identification
- **Text Processing**: https://docs.python.org/3/library/string.html - String manipulation and cleaning
- **Fuzzy Matching**: https://github.com/seatgeek/fuzzywuzzy - Approximate string matching
- **PDF Text Extraction**: https://pdfplumber.readthedocs.io/en/latest/reference.html#text-extraction - Header/footer text extraction
- **Confidence Scoring**: Custom algorithms for match quality assessment

### Database Integration & Data Modeling
- **Supabase Python Client**: https://supabase.com/docs/reference/python/introduction - Database operations
- **SQLAlchemy Models**: https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html - ORM model definitions
- **Pydantic Models**: https://docs.pydantic.dev/latest/ - Data validation and serialization
- **Database Transactions**: https://supabase.com/docs/reference/python/database-transactions - ACID compliance
- **JSON Storage**: https://www.postgresql.org/docs/current/datatype-json.html - Metadata and configuration storage

### Currency Handling & Financial Data
- **Decimal Precision**: https://docs.python.org/3/library/decimal.html - Accurate financial calculations
- **Currency Conversion**: https://exchangerate-api.com/ - Real-time exchange rates (future enhancement)
- **Price Validation**: Custom validation for USD/EUR price formats
- **Financial Data Types**: PostgreSQL DECIMAL type for precise monetary values
- **Tax Calculations**: VAT and tax class handling for different regions

## OTHER CONSIDERATIONS:

### Supplier Detection Strategy

#### Header-Based Detection Patterns
```python
class SupplierDetectionService:
    """Service for detecting invoice suppliers from PDF content."""
    
    SUPPLIER_PATTERNS = {
        'lawnfawn': {
            'company_names': [
                'Lawn Fawn',
                'lawnfawn.com',
                'Rancho Santa Margarita, CA 92688'
            ],
            'invoice_signatures': [
                'Invoice #.*Ship Date',
                'Qty.*Description.*Price.*Origin.*Tariff Code.*Amount'
            ],
            'confidence_weight': 0.95
        },
        'craftlines': {
            'company_names': [
                'Craftlines',
                'craftlines.eu',
                'Craft Lines Europe',
                'Craft Lines GmbH'
            ],
            'invoice_signatures': [
                'VAT.*BTW',
                'EUR.*€'
            ],
            'confidence_weight': 0.90
        },
        'mama-elephant': {
            'company_names': [
                'Mama Elephant',
                'mamaelephant.com',
                'Mama Elephant LLC'
            ],
            'invoice_signatures': [
                'Clear Stamps',
                'Creative Cuts'
            ],
            'confidence_weight': 0.85
        }
    }
    
    def detect_supplier(self, pdf_text: str, table_data: List[Dict]) -> Dict[str, Any]:
        """
        Detect supplier from PDF content with confidence scoring.
        
        Args:
            pdf_text: Raw text extracted from PDF
            table_data: Parsed table data from invoice
            
        Returns:
            Detection result with supplier code and confidence
        """
        detection_results = {}
        
        for supplier_code, patterns in self.SUPPLIER_PATTERNS.items():
            confidence = 0
            matched_patterns = []
            
            # Check company name patterns
            for pattern in patterns['company_names']:
                if pattern.lower() in pdf_text.lower():
                    confidence += 0.4
                    matched_patterns.append(f"company_name: {pattern}")
            
            # Check invoice signature patterns
            for pattern in patterns['invoice_signatures']:
                if re.search(pattern, pdf_text, re.IGNORECASE):
                    confidence += 0.3
                    matched_patterns.append(f"signature: {pattern}")
            
            # Apply supplier-specific confidence weight
            confidence *= patterns['confidence_weight']
            
            if confidence > 0:
                detection_results[supplier_code] = {
                    'confidence': min(confidence, 1.0),
                    'matched_patterns': matched_patterns
                }
        
        # Return highest confidence match
        if detection_results:
            best_match = max(detection_results.items(), key=lambda x: x[1]['confidence'])
            return {
                'supplier_code': best_match[0],
                'confidence': best_match[1]['confidence'],
                'matched_patterns': best_match[1]['matched_patterns'],
                'all_results': detection_results
            }
        
        raise UnknownSupplierError("No supported supplier detected in invoice")
```

#### Supplier-Specific Parsing Strategies
```python
class InvoiceParsingStrategy:
    """Base class for supplier-specific invoice parsing."""
    
    def parse_invoice(self, pdf_path: str) -> Dict[str, Any]:
        """Parse invoice and return structured data."""
        raise NotImplementedError

class LawnFawnParsingStrategy(InvoiceParsingStrategy):
    """Parsing strategy for LawnFawn direct invoices."""
    
    def parse_invoice(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parse LawnFawn invoice format:
        - Header: "Lawn Fawn, Rancho Santa Margarita, CA 92688"
        - Table: Qty | Description | Price | Origin | Tariff Code | Amount
        - Description format: "LF1142 - Lawn Cuts - Stitched Rectangle Frames Dies"
        """
        with pdfplumber.open(pdf_path) as pdf:
            # Extract invoice metadata from first page
            first_page = pdf.pages[0]
            text = first_page.extract_text()
            
            metadata = self._extract_metadata(text)
            products = []
            
            # Extract table data from all pages
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if self._is_product_table(table):
                        products.extend(self._parse_product_table(table))
            
            return {
                'supplier': 'lawnfawn',
                'metadata': metadata,
                'products': products,
                'currency': 'USD',
                'total_products': len(products)
            }
    
    def _extract_metadata(self, text: str) -> Dict[str, Any]:
        """Extract invoice metadata from header text."""
        metadata = {}
        
        # Extract invoice number
        invoice_match = re.search(r'Invoice\s*#\s*([A-Z0-9-]+)', text)
        if invoice_match:
            metadata['invoice_number'] = invoice_match.group(1)
        
        # Extract ship date
        date_match = re.search(r'Ship Date\s*(\d{1,2}/\d{1,2}/\d{4})', text)
        if date_match:
            metadata['ship_date'] = date_match.group(1)
        
        # Extract company information
        if 'Rancho Santa Margarita, CA 92688' in text:
            metadata['supplier_address'] = 'Rancho Santa Margarita, CA 92688'
        
        return metadata
    
    def _parse_product_table(self, table: List[List[str]]) -> List[Dict[str, Any]]:
        """Parse product table rows into structured data."""
        products = []
        
        for row in table[1:]:  # Skip header row
            if len(row) >= 6 and row[1]:  # Ensure we have description
                try:
                    product = self._parse_product_row(row)
                    if product:
                        products.append(product)
                except Exception as e:
                    # Log parsing error but continue
                    print(f"Error parsing row {row}: {e}")
        
        return products
    
    def _parse_product_row(self, row: List[str]) -> Dict[str, Any]:
        """Parse individual product row."""
        description = row[1].strip()
        
        # Parse LawnFawn description format: "LF1142 - Lawn Cuts - Stitched Rectangle Frames Dies"
        parts = description.split(' - ')
        if len(parts) >= 3:
            return {
                'supplier_sku': parts[0].strip(),  # LF1142
                'manufacturer': 'lawnfawn',
                'manufacturer_sku': parts[0].strip(),  # Same as supplier for direct sales
                'category': parts[1].strip(),  # Lawn Cuts
                'product_name': parts[2].strip(),  # Stitched Rectangle Frames Dies
                'quantity': int(row[0]) if row[0].isdigit() else 1,
                'price_usd': float(row[2]) if row[2] else 0.0,
                'origin': row[3] if len(row) > 3 else None,
                'tariff_code': row[4] if len(row) > 4 else None,
                'line_total_usd': float(row[5]) if len(row) > 5 and row[5] else 0.0,
                'raw_description': description
            }
        
        return None

class CraftlinesParsingStrategy(InvoiceParsingStrategy):
    """Parsing strategy for Craftlines wholesaler invoices."""
    
    def parse_invoice(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parse Craftlines invoice format:
        - Header: "Craftlines" or "Craft Lines Europe"
        - Mixed manufacturer products
        - EUR pricing
        """
        # Implementation for Craftlines format
        # Handle multi-manufacturer product detection
        pass

class MamaElephantParsingStrategy(InvoiceParsingStrategy):
    """Parsing strategy for Mama Elephant direct invoices."""
    
    def parse_invoice(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parse Mama Elephant invoice format:
        - Header: "Mama Elephant"
        - Product names only (no SKUs)
        - USD pricing
        """
        # Implementation for Mama Elephant format
        # Handle name-only product identification
        pass
```

### S3 Storage Architecture

#### Bucket Organization Strategy
```python
class S3InvoiceManager:
    """Manages invoice storage in AWS S3."""
    
    def __init__(self, bucket_name: str, region: str = 'eu-central-1'):
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = boto3.client('s3', region_name=region)
    
    def generate_invoice_key(self, supplier: str, filename: str) -> str:
        """
        Generate S3 key for invoice storage.
        Format: invoices/{supplier}/{year}/{month}/{filename}
        """
        now = datetime.now()
        return f"invoices/{supplier}/{now.year}/{now.month:02d}/{filename}"
    
    def upload_invoice(self, file_data: bytes, supplier: str, original_filename: str) -> Dict[str, str]:
        """
        Upload invoice to S3 and return storage information.
        
        Args:
            file_data: PDF file content as bytes
            supplier: Detected supplier code
            original_filename: Original uploaded filename
            
        Returns:
            Storage information with S3 key and URL
        """
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = self._sanitize_filename(original_filename)
        s3_filename = f"{supplier}_invoice_{timestamp}_{safe_filename}"
        
        # Generate S3 key
        s3_key = self.generate_invoice_key(supplier, s3_filename)
        
        # Upload to S3
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_data,
                ContentType='application/pdf',
                Metadata={
                    'supplier': supplier,
                    'original_filename': original_filename,
                    'upload_timestamp': timestamp
                }
            )
            
            # Generate S3 URL
            s3_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            return {
                's3_key': s3_key,
                's3_url': s3_url,
                'bucket': self.bucket_name,
                'filename': s3_filename
            }
            
        except Exception as e:
            raise S3UploadError(f"Failed to upload invoice to S3: {e}")
    
    def generate_download_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate presigned URL for invoice download.
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL for secure download
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key,
                    'ResponseContentDisposition': f'attachment; filename="{os.path.basename(s3_key)}"'
                },
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            raise S3AccessError(f"Failed to generate download URL: {e}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for S3 storage."""
        # Remove unsafe characters and limit length
        safe_chars = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        return safe_chars[:100]  # Limit length

# S3 Lifecycle Policy Configuration
S3_LIFECYCLE_POLICY = {
    "Rules": [
        {
            "ID": "InvoiceRetentionPolicy",
            "Status": "Enabled",
            "Filter": {"Prefix": "invoices/"},
            "Transitions": [
                {
                    "Days": 90,
                    "StorageClass": "STANDARD_IA"  # Move to cheaper storage after 3 months
                },
                {
                    "Days": 365,
                    "StorageClass": "GLACIER"  # Archive after 1 year
                }
            ]
        },
        {
            "ID": "ProcessingCleanup",
            "Status": "Enabled",
            "Filter": {"Prefix": "processing/"},
            "Expiration": {"Days": 7}  # Delete processing files after 7 days
        },
        {
            "ID": "ExportCleanup",
            "Status": "Enabled",
            "Filter": {"Prefix": "exports/"},
            "Expiration": {"Days": 30}  # Delete export packages after 30 days
        }
    ]
}
```

### Database Schema Enhancements

#### Enhanced Upload Batches Table
```sql
-- Enhanced upload_batches table for invoice processing
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS s3_key VARCHAR(500);
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS s3_url VARCHAR(1000);
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS original_filename VARCHAR(255);
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS file_size_bytes INTEGER;
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS supplier_detection_method VARCHAR(50);
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS supplier_detection_confidence DECIMAL(3,2);
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS invoice_number VARCHAR(100);
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS invoice_date DATE;
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS currency_code VARCHAR(3) DEFAULT 'USD';
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS total_amount_original DECIMAL(10,2);
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS parsing_success_rate DECIMAL(5,2);
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS download_count INTEGER DEFAULT 0;
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS last_downloaded_at TIMESTAMP WITH TIME ZONE;

-- Add indexes for new columns
CREATE INDEX IF NOT EXISTS idx_upload_batches_s3_key ON upload_batches(s3_key);
CREATE INDEX IF NOT EXISTS idx_upload_batches_invoice_number ON upload_batches(invoice_number);
CREATE INDEX IF NOT EXISTS idx_upload_batches_invoice_date ON upload_batches(invoice_date);
CREATE INDEX IF NOT EXISTS idx_upload_batches_currency ON upload_batches(currency_code);
```

#### Enhanced Products Table for Supplier/Manufacturer Distinction
```sql
-- Enhanced products table with supplier/manufacturer tracking
ALTER TABLE products ADD COLUMN IF NOT EXISTS manufacturer VARCHAR(100);
ALTER TABLE products ADD COLUMN IF NOT EXISTS manufacturer_sku VARCHAR(100);
ALTER TABLE products ADD COLUMN IF NOT EXISTS manufacturer_website VARCHAR(255);
ALTER TABLE products ADD COLUMN IF NOT EXISTS quantity_ordered INTEGER DEFAULT 1;
ALTER TABLE products ADD COLUMN IF NOT EXISTS line_total_usd DECIMAL(10,2);
ALTER TABLE products ADD COLUMN IF NOT EXISTS line_total_eur DECIMAL(10,2);
ALTER TABLE products ADD COLUMN IF NOT EXISTS origin_country VARCHAR(100);
ALTER TABLE products ADD COLUMN IF NOT EXISTS tariff_code VARCHAR(50);
ALTER TABLE products ADD COLUMN IF NOT EXISTS raw_description TEXT;
ALTER TABLE products ADD COLUMN IF NOT EXISTS parsing_notes JSONB;
ALTER TABLE products ADD COLUMN IF NOT EXISTS line_number INTEGER;

-- Add indexes for manufacturer tracking
CREATE INDEX IF NOT EXISTS idx_products_manufacturer ON products(manufacturer);
CREATE INDEX IF NOT EXISTS idx_products_manufacturer_sku ON products(manufacturer_sku);
CREATE INDEX IF NOT EXISTS idx_products_line_number ON products(batch_id, line_number);

-- Add constraint to ensure manufacturer is set when manufacturer_sku is present
ALTER TABLE products ADD CONSTRAINT chk_manufacturer_consistency 
    CHECK ((manufacturer_sku IS NULL) OR (manufacturer IS NOT NULL));
```

### API Endpoint Design

#### Invoice Upload Endpoint
```python
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class InvoiceUploadResponse(BaseModel):
    """Response model for invoice upload."""
    success: bool
    batch_id: Optional[str] = None
    supplier: Optional[str] = None
    products_found: Optional[int] = None
    parsing_success_rate: Optional[float] = None
    invoice_metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: str
    supported_suppliers: Optional[List[str]] = None

class InvoiceListResponse(BaseModel):
    """Response model for invoice listing."""
    invoices: List[Dict[str, Any]]
    total_count: int
    page: int
    page_size: int

class InvoiceDetailsResponse(BaseModel):
    """Response model for invoice details."""
    batch: Dict[str, Any]
    products: List[Dict[str, Any]]
    parsing_summary: Dict[str, Any]
    download_url: Optional[str] = None

@app.post("/api/upload/invoice", response_model=InvoiceUploadResponse)
async def upload_invoice(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
) -> InvoiceUploadResponse:
    """
    Upload and process PDF invoice.
    
    Args:
        file: PDF invoice file
        
    Returns:
        Processing results with supplier detection and parsing status
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file uploaded"
            )
        
        # Process invoice in background
        background_tasks.add_task(
            process_invoice_async,
            file_content,
            file.filename
        )
        
        # Return immediate response
        return InvoiceUploadResponse(
            success=True,
            message="Invoice uploaded successfully. Processing started.",
            batch_id=None  # Will be updated when processing completes
        )
        
    except UnknownSupplierError as e:
        return InvoiceUploadResponse(
            success=False,
            error="unknown_supplier",
            message=str(e),
            supported_suppliers=list(SUPPLIER_PATTERNS.keys())
        )
    except Exception as e:
        return InvoiceUploadResponse(
            success=False,
            error="processing_failed",
            message=f"Invoice processing failed: {str(e)}"
        )

@app.get("/api/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    page: int = 1,
    page_size: int = 20,
    supplier: Optional[str] = None,
    status: Optional[str] = None
) -> InvoiceListResponse:
    """
    List uploaded invoices with filtering and pagination.
    
    Args:
        page: Page number (1-based)
        page_size: Number of items per page
        supplier: Filter by supplier code
        status: Filter by processing status
        
    Returns:
        Paginated list of invoices
    """
    try:
        # Build query with filters
        query = supabase.table('upload_batches').select('*')
        
        if supplier:
            # Join with suppliers table to filter by supplier code
            query = query.eq('suppliers.code', supplier)
        
        if status:
            query = query.eq('status', status)
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)
        query = query.order('uploaded_at', desc=True)
        
        result = query.execute()
        
        # Get total count for pagination
        count_result = supabase.table('upload_batches').select('count').execute()
        total_count = len(count_result.data) if count_result.data else 0
        
        return InvoiceListResponse(
            invoices=result.data or [],
            total_count=total_count,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list invoices: {str(e)}"
        )

@app.get("/api/invoices/{batch_id}/download")
async def download_invoice(batch_id: str) -> JSONResponse:
    """
    Generate presigned URL for invoice download.
    
    Args:
        batch_id: Upload batch ID
        
    Returns:
        Redirect to presigned S3 URL
    """
    try:
        # Get batch information
        result = supabase.table('upload_batches').select('*').eq('id', batch_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        batch = result.data
        s3_key = batch.get('s3_key')
        
        if not s3_key:
            raise HTTPException(status_code=404, detail="Invoice file not found in storage")
        
        # Generate presigned URL
        s3_manager = S3InvoiceManager(bucket_name=S3_BUCKET_NAME)
        download_url = s3_manager.generate_download_url(s3_key, expiration=3600)
        
        # Update download count
        supabase.table('upload_batches').update({
            'download_count': batch.get('download_count', 0) + 1,
            'last_downloaded_at': datetime.now().isoformat()
        }).eq('id', batch_id).execute()
        
        # Return redirect response
        return JSONResponse(
            content={"download_url": download_url},
            headers={"Location": download_url}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate download URL: {str(e)}"
        )

@app.get("/api/invoices/{batch_id}/details", response_model=InvoiceDetailsResponse)
async def get_invoice_details(batch_id: str) -> InvoiceDetailsResponse:
    """
    Get detailed invoice information including products and parsing results.
    
    Args:
        batch_id: Upload batch ID
        
    Returns:
        Comprehensive invoice details
    """
    try:
        # Get batch information
        batch_result = supabase.table('upload_batches').select('*').eq('id', batch_id).single().execute()
        
        if not batch_result.data:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        batch = batch_result.data
        
        # Get products for this batch
        products_result = supabase.table('products').select('*').eq('batch_id', batch_id).order('line_number').execute()
        products = products_result.data or []
        
        # Calculate parsing summary
        total_products = len(products)
        successful_products = len([p for p in products if p['status'] not in ['failed', 'draft']])
        parsing_success_rate = (successful_products / total_products * 100) if total_products > 0 else 0
        
        parsing_summary = {
            'total_products': total_products,
            'successful_products': successful_products,
            'failed_products': total_products - successful_products,
            'parsing_success_rate': round(parsing_success_rate, 1),
            'status_breakdown': {}
        }
        
        # Calculate status breakdown
        for product in products:
            status = product['status']
            parsing_summary['status_breakdown'][status] = parsing_summary['status_breakdown'].get(status, 0) + 1
        
        # Generate download URL if available
        download_url = None
        if batch.get('s3_key'):
            try:
                s3_manager = S3InvoiceManager(bucket_name=S3_BUCKET_NAME)
                download_url = s3_manager.generate_download_url(batch['s3_key'], expiration=3600)
            except Exception:
                pass  # Download URL generation failed, but don't fail the whole request
        
        return InvoiceDetailsResponse(
            batch=batch,
            products=products,
            parsing_summary=parsing_summary,
            download_url=download_url
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get invoice details: {str(e)}"
        )
```

### Background Processing Pipeline

#### Async Invoice Processing
```python
import asyncio
from celery import Celery
from typing import Dict, Any, List

# Celery configuration for background processing
celery_app = Celery(
    'invoice_processor',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

@celery_app.task
def process_invoice_async(file_content: bytes, filename: str) -> Dict[str, Any]:
    """
    Process invoice asynchronously in background.
    
    Args:
        file_content: PDF file content as bytes
        filename: Original filename
        
    Returns:
        Processing results
    """
    try:
        # Initialize services
        supplier_detector = SupplierDetectionService()
        s3_manager = S3InvoiceManager(bucket_name=S3_BUCKET_NAME)
        
        # Step 1: Extract PDF text for supplier detection
        pdf_text = extract_pdf_text(file_content)
        
        # Step 2: Detect supplier
        detection_result = supplier_detector.detect_supplier(pdf_text, [])
        supplier_code = detection_result['supplier_code']
        
        # Step 3: Upload to S3
        s3_info = s3_manager.upload_invoice(file_content, supplier_code, filename)
        
        # Step 4: Parse invoice using supplier-specific strategy
        parsing_strategy = get_parsing_strategy(supplier_code)
        
        # Save file temporarily for parsing
        temp_path = f"/tmp/{uuid.uuid4()}.pdf"
        with open(temp_path, 'wb') as f:
            f.write(file_content)
        
        try:
            parsing_result = parsing_strategy.parse_invoice(temp_path)
        finally:
            os.unlink(temp_path)  # Clean up temp file
