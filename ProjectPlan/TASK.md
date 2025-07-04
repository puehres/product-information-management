# Product Automation System Tasks

## Development Strategy: Lean & Iterative

Build value-delivering iterations that progressively expand from single supplier MVP to complete multi-supplier automation system. Each phase delivers immediate, measurable value while building foundation for the next phase.

## Phase 1: MVP - Lawn Fawn → Gambio

**Goal**: Prove core automation value with single supplier
**Success Criteria**: Process 50 Lawn Fawn products in 30 minutes vs 5 hours manually (90% time reduction)

### Task 1: Project Setup & Environment ✅ COMPLETED (2025-01-07)

- [x] Set up development environment (Python + Node.js)
- [x] Create project repository structure
- [x] Set up virtual environment and dependencies
- [x] Configure development database (PostgreSQL + Redis)
- [x] Create `.env` template with required API keys
- [x] Initialize logging and monitoring system

**Completion Notes**: Development environment established with FastAPI backend, Next.js frontend, and comprehensive testing frameworks.
**Next**: Dependencies met for Task 1.5

### Task 1.5: Frontend Environment Validation ✅ COMPLETED (2025-01-07)

- [x] Install frontend dependencies (npm install)
- [x] Verify TypeScript compilation (npm run type-check)
- [x] Run frontend tests (npm test)
- [x] Validate development server (npm run dev)
- [x] Fix any configuration or dependency issues
- [x] Document troubleshooting steps for future reference

**Completion Notes**: Frontend environment fully validated with 100% test coverage and all performance targets exceeded.
**Next**: Dependencies met for Task 2

### Task 2: MVP Database Design (Supabase) - Simplified

- [ ] Set up Supabase project in eu-central-1 (Frankfurt) region
- [ ] Configure Supabase client and connection strings
- [ ] Design simple database schema for MVP
- [ ] Create core tables: suppliers, upload_batches, products, images
- [ ] Set up database relationships and constraints
- [ ] Create Lawn Fawn supplier seed data
- [ ] Write database utility functions with Supabase client
- [ ] Add indexing for performance
- [ ] Configure local development with Supabase

**Supabase Configuration:**
- **Region**: eu-central-1 (Frankfurt) for German users
- **Free Tier**: 500MB database, 2GB bandwidth/month (perfect for MVP)
- **Features**: PostgreSQL + Real-time + Auth + Storage included
- **Cost**: $0/month for MVP vs $28/month AWS RDS

**MVP Tables (Essential Only):**
- `suppliers`: Basic supplier information
- `upload_batches`: Track invoice/CSV uploads and processing
- `products`: Core product data with Gambio fields
- `images`: Image metadata and S3 URLs

**Tax Handling (Deferred to Phase 2):**
- **MVP Approach**: Use hardcoded tax class ID in Gambio export
- **Future Enhancement**: Add tax_classes table for multi-country VAT support
- **Rationale**: Focus on core workflow validation first, add tax complexity later

**Environment Setup:**
```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres

# Redis (Upstash free tier)
REDIS_URL=rediss://default:password@region.upstash.io:6380

# Tax Configuration (MVP - hardcoded)
GAMBIO_DEFAULT_TAX_CLASS_ID=1
```

**Technology Stack:**
- **Supabase**: PostgreSQL database with real-time features
- **Python SDK**: supabase-py for Python integration
- **SQLAlchemy**: Standard PostgreSQL ORM (works with Supabase)
- **Alembic**: Database migrations (standard PostgreSQL)

**MVP Benefits:**
- **Faster Development**: Focus on core product processing workflow
- **Simpler Testing**: Fewer tables and relationships to manage
- **Iterative Approach**: Add tax complexity when workflow is validated
- **Quick Value**: Get to product automation faster

**Dependencies**: Task 1
**Output**: Simplified, focused Supabase database setup for MVP validation

### Task 3: Lawn Fawn Invoice Parser (PDF + CSV Support)

- [ ] Build flexible file upload system (PDF primary, CSV fallback)
- [ ] Create PDF invoice parser using pdfplumber for table extraction
- [ ] Extract LF SKU numbers (format: "LF3242") from PDF invoices
- [ ] Parse product names, USD prices, and quantities from invoices
- [ ] Implement USD to EUR currency conversion
- [ ] Create Lawn Fawn CSV parser for product release lists (fallback)
- [ ] Validate file formats and required fields
- [ ] Create batch tracking for uploads with invoice metadata
- [ ] Add basic error handling for malformed files
- [ ] Store parsed data in database with proper field mapping
- [ ] Create simple progress tracking

**Primary Input: PDF Invoices (Business Workflow):**
- **LF SKU**: Primary identifier (e.g., "LF3242")
- **Product Names**: Basic product names from invoice
- **USD Prices**: Actual purchase prices in USD
- **Quantities**: Ordered quantities for inventory tracking
- **Invoice Metadata**: Invoice number, date, line items

**Fallback Input: CSV Product Release Lists:**
- **LF SKU**: Primary identifier (e.g., "LF3242")
- **product_name**: Complete product names for translation
- **description**: Detailed product descriptions
- **MSRP**: Pricing information for comparison
- **tags**: Category/classification data
- **barcode**: Additional validation identifier

**Invoice Parser Implementation:**
```python
class LawnFawnInvoiceParser:
    def __init__(self):
        self.supported_formats = ['pdf', 'csv']
        self.usd_to_eur_rate = 0.85  # Configurable conversion rate
    
    def parse_file(self, file_path):
        if file_path.endswith('.pdf'):
            return self.parse_pdf_invoice(file_path)
        elif file_path.endswith('.csv'):
            return self.parse_csv_release_list(file_path)
    
    def parse_pdf_invoice(self, pdf_path):
        # Extract table data from PDF invoice
        # Look for LF SKU, product name, USD price, quantity
        # Return structured invoice data
        pass
    
    def convert_usd_to_eur(self, usd_price):
        return round(usd_price * self.usd_to_eur_rate, 2)
    
    def extract_sku_number(self, lf_sku):
        # "LF3242" → "3242" for search
        return lf_sku.replace("LF", "").replace("-", "").strip()
```

**Technology Stack:**
- **pdfplumber**: PDF table extraction (primary)
- **PyPDF2**: Fallback for simple text extraction
- **pandas**: Data processing and validation
- **Currency conversion**: USD → EUR with configurable rates

**Key Features:**
- Primary PDF invoice processing (business-aligned workflow)
- Fallback CSV support for product release lists
- USD to EUR currency conversion
- LF SKU extraction and validation
- Invoice metadata tracking (number, date, quantities)
- Flexible input format detection
- Batch processing with status tracking
- Basic error handling and validation

**Data Enrichment Strategy:**
```python
# Invoice data (minimal from PDF)
invoice_data = {
    'sku': 'LF3242',
    'name': 'Capybaras',
    'usd_price': 15.99,
    'eur_price': 13.59,  # Converted
    'quantity': 2,
    'invoice_number': 'INV-2025-001'
}

# Same SKU search strategy enriches with full product details
```

**Dependencies**: Task 2
**Output**: Flexible invoice-driven parsing with PDF support and currency conversion

### Task 4: SKU-Search-Based Product Matching (Lawn Fawn)

- [ ] Implement SKU extraction from LF numbers (LF3242 → 3242)
- [ ] Build Lawn Fawn search URL construction
- [ ] Implement search results parsing to extract product URLs
- [ ] Build web scraping with Firecrawl API for product pages
- [ ] Extract product details (name, description, images) from product pages
- [ ] Handle scraping errors and retries with exponential backoff
- [ ] Store scraped data in products table with confidence scoring
- [ ] Add confidence scoring for search matches
- [ ] Create fallback strategies for failed searches
- [ ] Log scraping results and issues for debugging

**Lawn Fawn Search Strategy:**
- **Step 1**: Extract numeric SKU from LF number (LF3242 → 3242)
- **Step 2**: Use SKU in Lawn Fawn search URL
- **Step 3**: Parse search results to find product URLs
- **Step 4**: Scrape actual product pages for details
- **Step 5**: Store with confidence scoring

**Search Implementation:**
```python
class LawnFawnMatcher:
    def __init__(self):
        self.search_base = "https://www.lawnfawn.com/search"
    
    def extract_sku(self, lf_number):
        # "LF3242" → "3242", handle variations like "LF-3242"
        return lf_number.upper().replace("LF", "").replace("-", "").strip()
    
    def build_search_url(self, sku):
        # Use actual Lawn Fawn search pattern
        return f"{self.search_base}?options%5Bprefix%5D=last&q={sku}&filter.p.product_type="
    
    async def find_product_url(self, lf_number):
        # Complete search → parse → extract workflow
        pass
```

**Confidence Scoring:**
- **95%**: Unique SKU search result
- **80%**: Multiple search results (take first)
- **60%**: Fallback search methods
- **0%**: No search results (flag for manual review)

**Error Handling:**
- Invalid LF number format
- Search returns no results
- Multiple ambiguous results
- Scraping failures with retry logic

**Dependencies**: Task 3
**Output**: Reliable SKU-search-based product matching for Lawn Fawn

### Task 5: Cloud Image Processing Pipeline

- [ ] Set up AWS S3 bucket (eu-central-1, Frankfurt) for image processing
- [ ] Configure boto3 SDK and S3 client with proper credentials
- [ ] Implement S3-based image processing workflow (download → process → upload)
- [ ] Download images from scraped URLs and upload to S3 raw folder
- [ ] Implement in-memory JPEG conversion using Pillow (no local storage)
- [ ] Add image dimension validation (≥1000px preferred) with quality warnings
- [ ] Create standardized naming: {SKU}_{type}_{sequence}.jpeg
- [ ] Store processed images in S3 organized folder structure
- [ ] Update database with S3 URLs and image metadata
- [ ] Implement S3 lifecycle policies for automatic cleanup (7/30 days)
- [ ] Create export package generation (ZIP with CSV + images)
- [ ] Generate time-limited presigned URLs for download packages
- [ ] Add Gambio import instructions generation

**S3 Configuration:**
- **Region**: eu-central-1 (Frankfurt)
- **Bucket Structure**: processing/{batch_id}/ and exports/{export_date}/
- **Access**: Private bucket with presigned URLs for downloads
- **Lifecycle**: Auto-delete processing (7 days), exports (30 days)

**Processing Pipeline:**
```python
# 1. Download from supplier URL
image_data = download_image(supplier_url)

# 2. Process in memory (no local storage)
processed_image = convert_to_jpeg(image_data, quality=85, min_dimension=1000)

# 3. Upload to S3 processing folder
s3_url = upload_to_s3(processed_image, f"processing/{batch_id}/processed/{sku}_main_01.jpeg")

# 4. Store S3 URL and metadata in database
save_image_metadata(product_id, s3_url, dimensions, quality_check)
```

**Export Package Generation:**
- **ZIP Format**: gambio_import.csv + images/ folder + import_instructions.md
- **Download**: 24-hour presigned URLs for user download
- **User Workflow**: Download → Import CSV to Gambio → FTP images to server
- **Instructions**: Auto-generated step-by-step Gambio import guide

**Technology Stack:**
- **boto3**: AWS SDK for Python S3 integration
- **Pillow**: In-memory image processing and JPEG conversion
- **asyncio**: Parallel processing for multiple images
- **zipfile**: Export package creation

**Quality Standards:**
- Convert all formats to JPEG for Gambio compatibility
- Validate minimum dimensions with quality warnings
- Generate quality warnings for substandard images
- Standardized naming convention for Gambio CSV references

**Dependencies**: Task 4
**Output**: Cloud-based image processing with S3 storage and export package generation

### Task 6: German Translation

- [ ] Set up OpenAI API integration
- [ ] Create translation functions for product names
- [ ] Implement description translation with context
- [ ] Add translation caching to avoid duplicate costs
- [ ] Handle translation errors and fallbacks
- [ ] Store both original and translated content
- [ ] Add translation quality validation
- [ ] Create simple review interface for translations

**Translation Features:**
- Context-aware German translations
- Caching to reduce API costs
- Quality validation and review
- Fallback error handling

**Dependencies**: Task 5
**Output**: Reliable German translation system

### Task 7: Gambio CSV Export

- [ ] Implement exact Gambio 4.4.0.4 CSV format
- [ ] Create comprehensive field mapping
- [ ] Add "Neu: LawnFawn > PD-neu" category assignment
- [ ] Include EUR pricing with tax class assignment
- [ ] Generate JPEG image filename references
- [ ] Create UTF-8 encoding with pipe delimiters
- [ ] Add all required fields (XTSOL, p_model, p_shortdesc.de/en)
- [ ] Generate export package with images and instructions

**Gambio Requirements:**
- UTF-8 without BOM, pipe delimiter, double quote qualifier
- Required fields: XTSOL, p_model, p_shortdesc.de, p_shortdesc.en
- Category format: "Neu: LawnFawn > PD-neu"
- Image references: p_image, p_image.1, p_image.2, p_image.3
- SEO URLs: rewrite_url.de with friendly slugs

**Dependencies**: Task 6
**Output**: Complete Gambio-compatible export system

### Task 8: Simple Web Interface

- [ ] Create basic React frontend
- [ ] Build file upload component for CSV
- [ ] Add processing status display
- [ ] Create export download interface
- [ ] Show processing progress and results
- [ ] Add basic error display and handling
- [ ] Create simple product review list
- [ ] Add export package download

**MVP UI Features:**
- CSV upload with drag-and-drop
- Processing status and progress
- Results display with export download
- Basic error handling and feedback

**Dependencies**: Task 7
**Output**: Functional web interface for MVP

## Phase 2: Multi-Supplier Expansion

**Goal**: Complete supplier coverage with intelligent matching
**Success Criteria**: Handle all 3 suppliers with different data formats and matching strategies

### Task 9: Supplier Abstraction Layer

- [ ] Create supplier configuration system
- [ ] Build pluggable matching strategies
- [ ] Implement supplier-specific parsers
- [ ] Add confidence scoring framework
- [ ] Create supplier management interface
- [ ] Build universal processing pipeline
- [ ] Add supplier-specific error handling
- [ ] Test framework with multiple suppliers

**Abstraction Features:**
- Configuration-driven supplier setup
- Pluggable matching algorithms
- Universal confidence scoring
- Supplier-specific customization

**Dependencies**: Task 8
**Output**: Flexible supplier framework

### Task 10: Craftlines Integration

- [ ] Add Craftlines supplier configuration
- [ ] Implement code/EAN-based matching
- [ ] Build direct code lookup strategy
- [ ] Add search fallback for failed lookups
- [ ] Handle German/English content
- [ ] Set confidence scoring thresholds
- [ ] Test with Craftlines data
- [ ] Add Craftlines-specific error handling

**Craftlines Strategy:**
- Primary: Direct code lookup
- Fallback: Search with product code
- Confidence: Code match (95%), Search (80%), Name (60%)

**Dependencies**: Task 9
**Output**: Working Craftlines integration

### Task 11: Mama Elephant Integration

- [ ] Add Mama Elephant supplier configuration
- [ ] Implement name-based fuzzy matching
- [ ] Build website search functionality
- [ ] Add similarity scoring algorithms
- [ ] Create manual review workflow for uncertain matches
- [ ] Handle invoice format parsing
- [ ] Set lower confidence thresholds
- [ ] Add extensive fallback strategies

**Mama Elephant Strategy:**
- Primary: Website search with exact name
- Secondary: Fuzzy name matching
- Tertiary: Manual URL entry
- Confidence: Exact (75%), Fuzzy (40-70%), Manual (100%)

**Dependencies**: Task 10
**Output**: Working Mama Elephant integration with review workflow

### Task 12: Enhanced Review System

- [ ] Create unified review dashboard
- [ ] Build confidence score visualization
- [ ] Add manual URL entry capability
- [ ] Implement bulk review operations
- [ ] Create image quality review interface
- [ ] Add manual image upload functionality
- [ ] Build review queue management
- [ ] Add user feedback and learning system

**Review Features:**
- Confidence-based flagging
- Manual override capabilities
- Bulk operations for efficiency
- Image quality assessment
- User feedback loop

**Dependencies**: Task 11
**Output**: Comprehensive review and validation system

### Task 13: Cross-Supplier Features

- [ ] Implement duplicate detection across suppliers
- [ ] Build similarity scoring for products
- [ ] Create duplicate resolution interface
- [ ] Add cross-supplier analytics
- [ ] Implement unified export system
- [ ] Create supplier comparison tools
- [ ] Add batch processing optimizations
- [ ] Test with mixed supplier data

**Cross-Supplier Features:**
- Duplicate detection and resolution
- Unified processing pipeline
- Supplier performance analytics
- Mixed batch processing

**Dependencies**: Task 12
**Output**: Complete multi-supplier system

## Phase 3: Production Ready

**Goal**: Business-ready system with reliability and polish
**Success Criteria**: Dependable automation suitable for daily operations

### Task 14: Error Handling & Resilience

- [ ] Implement comprehensive error handling
- [ ] Add retry mechanisms for failed operations
- [ ] Create detailed error logging and monitoring
- [ ] Build graceful degradation for API failures
- [ ] Add data backup and recovery procedures
- [ ] Implement error notification system
- [ ] Create error recovery workflows
- [ ] Test system resilience under failure scenarios

**Resilience Features:**
- Automatic retry with exponential backoff
- Graceful degradation for service failures
- Comprehensive error logging
- Data backup and recovery

**Dependencies**: Task 13
**Output**: Robust, resilient system

### Task 15: Performance Optimization

- [ ] Optimize database queries and indexing
- [ ] Implement comprehensive caching strategies
- [ ] Add batch processing optimizations
- [ ] Optimize image processing pipeline
- [ ] Add progress indicators and async processing
- [ ] Implement connection pooling
- [ ] Optimize frontend performance
- [ ] Add performance monitoring and metrics

**Performance Features:**
- Database query optimization
- Redis caching for frequently accessed data
- Async processing for long-running tasks
- Performance monitoring and alerting

**Dependencies**: Task 14
**Output**: High-performance, scalable system

### Task 16: Documentation & Deployment

- [ ] Create comprehensive user documentation
- [ ] Write API documentation with examples
- [ ] Create deployment guides
- [ ] Set up production environment
- [ ] Create backup and disaster recovery procedures
- [ ] Write system administration guides
- [ ] Create troubleshooting documentation
- [ ] Add system monitoring and alerting

**Documentation Features:**
- User guides with screenshots
- Technical documentation
- Deployment and operations guides
- Troubleshooting resources

**Dependencies**: Task 15
**Output**: Production-ready system with complete documentation

## Success Criteria by Phase

### Phase 1 Success Metrics
- [ ] Process 50 Lawn Fawn products in under 30 minutes
- [ ] 90%+ time reduction vs manual process
- [ ] All images converted to JPEG with quality validation
- [ ] German translations with 95%+ accuracy
- [ ] Gambio CSV import works without errors
- [ ] Simple web interface functional and intuitive

### Phase 2 Success Metrics
- [ ] All 3 suppliers supported with appropriate matching strategies
- [ ] Confidence scoring accurately identifies uncertain matches
- [ ] Review workflow efficiently handles edge cases
- [ ] Cross-supplier duplicate detection prevents duplicates
- [ ] System handles mixed supplier batches reliably
- [ ] Processing accuracy >95% across all suppliers

### Phase 3 Success Metrics
- [ ] System handles 100+ products per batch reliably
- [ ] Error recovery works for all failure scenarios
- [ ] Performance acceptable for daily production use
- [ ] Documentation enables independent operation
- [ ] Monitoring provides visibility into system health
- [ ] Backup and recovery procedures tested and verified

## Value Delivery Timeline

### Phase 1 Value
- **Immediate**: First Lawn Fawn batch processed successfully
- **Short-term**: Reliable daily Lawn Fawn automation
- **Measurable**: 90% time reduction for Lawn Fawn products

### Phase 2 Value
- **Immediate**: Craftlines and Mama Elephant support
- **Short-term**: Complete supplier coverage
- **Measurable**: All suppliers automated with quality review

### Phase 3 Value
- **Immediate**: Production reliability and performance
- **Short-term**: Business-ready daily operations
- **Measurable**: Dependable automation for all workflows

## Risk Mitigation

### Technical Risks
- **Supplier website changes**: Flexible scraping with fallbacks
- **API rate limits**: Respectful scraping with delays and caching
- **Translation quality**: Review workflow and quality validation
- **Image quality**: Validation with manual upload fallback

### Business Risks
- **Supplier relations**: Compliant scraping practices
- **Data accuracy**: Comprehensive validation and review
- **System reliability**: Robust error handling and monitoring
- **User adoption**: Intuitive interface and comprehensive documentation

## Architecture Principles

### Build for Iteration
- Start simple, add complexity as needed
- Modular design for easy extension
- Configuration over hardcoding
- Test early and often

### Focus on Value
- Deliver working features over perfect architecture
- Prioritize user feedback and iteration
- Measure success by time savings and accuracy
- Build for the current phase, design for the future

### Quality Standards
- Maintain image quality standards (≥1000px)
- Ensure translation accuracy and review
- Validate all data before export
- Provide clear error messages and recovery
