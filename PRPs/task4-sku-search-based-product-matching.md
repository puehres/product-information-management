name: "Task 4: SKU-Search-Based Product Matching (Lawn Fawn) - PRP"
description: |
  Comprehensive product enrichment system that extracts numeric SKUs from LawnFawn product codes,
  performs intelligent web searches using Firecrawl API, validates product matches through cross-referencing,
  scrapes detailed product information including names, descriptions, and images, implements confidence
  scoring based on match quality, handles multiple search results with fallback strategies, stores complete
  scraping history for debugging and analytics, integrates seamlessly with existing invoice processing
  workflow, and provides robust error handling with retry mechanisms for failed attempts.

---

## Goal
Build a comprehensive SKU-based product enrichment system that takes products parsed from invoices (Task 3) and enriches them with detailed information scraped from LawnFawn's website using Firecrawl API. The system must extract numeric SKUs, perform intelligent searches, validate matches, scrape product details, implement confidence scoring, and provide complete audit trails for all scraping attempts.

## Why
- **Business Value**: Automatically enrich product data with accurate names, descriptions, and images from manufacturer websites
- **User Impact**: Reduces manual data entry and improves product catalog completeness and accuracy
- **Integration**: Seamlessly extends existing invoice processing workflow (Task 3) with enrichment capabilities
- **Problems Solved**: Eliminates manual product research, provides consistent data quality, enables automated product matching

## What
A two-phase processing system where Phase 1 (existing Task 3) parses invoices and creates DRAFT products, and Phase 2 (new Task 4) enriches those products with web-scraped data and updates them to ENRICHED status.

### Success Criteria
- [ ] Extract numeric SKUs from LawnFawn product codes (LF2538 → 2538)
- [ ] Successfully scrape product information using Firecrawl API
- [ ] Implement confidence scoring system (100% exact match, 90% first result, 60% no match, 30% fallback)
- [ ] Store complete scraping attempt history with full audit trail
- [ ] Provide REST API endpoints for enrichment management
- [ ] Handle errors gracefully with retry mechanisms
- [ ] Achieve 95%+ test coverage with comprehensive test suite
- [ ] Integrate seamlessly with existing invoice processing workflow

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://docs.firecrawl.dev/
  why: Enterprise web scraping API with JavaScript rendering capabilities
  
- url: https://docs.firecrawl.dev/api-reference/endpoint/scrape
  why: Single page scraping endpoint for product pages and search results
  
- url: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
  why: HTML parsing and data extraction patterns
  
- url: https://tenacity.readthedocs.io/en/latest/
  why: Robust retry mechanisms for failed scraping attempts
  
- url: https://limits.readthedocs.io/en/stable/
  why: Request rate limiting to respect website policies
  
- file: backend/app/services/database_service.py
  why: Existing service patterns, error handling, and database operations
  
- file: backend/app/api/upload.py
  why: FastAPI endpoint patterns, error handling, and response models
  
- file: backend/tests/unit/test_product_deduplication.py
  why: Comprehensive testing patterns with mocks and fixtures
  
- file: backend/app/services/invoice_processor.py
  why: Background task processing and service orchestration patterns
  
- file: features/task4-sku-search-based-product-matching.md
  why: Complete feature specification with technical details and examples
```

### Current Codebase Tree
```bash
backend/
├── app/
│   ├── api/
│   │   └── upload.py                    # FastAPI endpoint patterns
│   ├── services/
│   │   ├── database_service.py          # Database operations
│   │   ├── invoice_processor.py         # Background processing
│   │   ├── supplier_detector.py         # Service patterns
│   │   └── deduplication_service.py     # Complex service logic
│   ├── models/
│   │   ├── product.py                   # Product data models
│   │   ├── base.py                      # Base model patterns
│   │   └── deduplication.py             # Complex model examples
│   ├── core/
│   │   ├── config.py                    # Configuration management
│   │   └── database.py                  # Database connections
│   └── parsers/
│       ├── base.py                      # Parser base classes
│       └── lawnfawn.py                  # LawnFawn-specific parsing
├── tests/
│   ├── unit/
│   │   └── test_product_deduplication.py # Comprehensive test patterns
│   ├── integration/
│   │   └── test_end_to_end_invoice.py   # Integration test patterns
│   └── connectivity/
│       └── test_s3_connectivity.py      # External service tests
├── migrations/
│   └── 006_product_deduplication_system.sql # Migration patterns
└── requirements.txt                     # Dependencies
```

### Desired Codebase Tree with New Files
```bash
backend/
├── app/
│   ├── api/
│   │   └── enrichment.py                # NEW: Product enrichment endpoints
│   ├── services/
│   │   ├── product_enrichment.py        # NEW: Main enrichment orchestrator
│   │   ├── firecrawl_client.py          # NEW: Firecrawl API wrapper
│   │   └── lawnfawn_matcher.py          # NEW: LawnFawn-specific matching
│   ├── models/
│   │   └── enrichment.py                # NEW: Enrichment data models
│   └── exceptions/
│       └── enrichment.py                # NEW: Custom exceptions
├── tests/
│   ├── unit/
│   │   ├── test_product_enrichment.py   # NEW: Service unit tests
│   │   ├── test_firecrawl_client.py     # NEW: API client tests
│   │   └── test_lawnfawn_matcher.py     # NEW: Matcher logic tests
│   ├── integration/
│   │   └── test_enrichment_workflow.py  # NEW: End-to-end tests
│   └── connectivity/
│       └── test_firecrawl_connectivity.py # NEW: API connectivity tests
└── migrations/
    └── 007_product_enrichment_system.sql # NEW: Database schema
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Firecrawl API requires Bearer token authentication
# Example: headers = {"Authorization": f"Bearer {api_key}"}

# CRITICAL: BeautifulSoup requires explicit parser specification
# Example: soup = BeautifulSoup(html_content, 'html.parser')

# CRITICAL: httpx AsyncClient must be used in async context manager
# Example: async with httpx.AsyncClient(timeout=30) as client:

# CRITICAL: Tenacity retry decorator must be applied to async functions correctly
# Example: @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))

# CRITICAL: Supabase client expects string UUIDs, not UUID objects
# Example: .eq('id', str(uuid_value))

# CRITICAL: FastAPI BackgroundTasks must be used for long-running operations
# Example: background_tasks.add_task(enrichment_service.enrich_batch, batch_id)

# CRITICAL: Pydantic v2 uses model_dump() not dict()
# Example: data = model.model_dump(mode='json')

# CRITICAL: Our project uses structlog for logging with context
# Example: logger.info("Message", key=value, error=str(e))
```

## Implementation Blueprint

### Data Models and Structure

Create comprehensive data models for enrichment workflow with proper validation and type safety.

```python
# app/models/enrichment.py - Core enrichment data models
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class EnrichmentData(BaseModel):
    """Complete enrichment data from scraping process."""
    search_url: str = Field(..., description="Search URL used")
    product_url: str = Field(..., description="Product page URL found")
    product_name: str = Field(..., description="Scraped product name")
    description: str = Field(..., description="Scraped product description")
    image_urls: List[str] = Field(default_factory=list, description="Scraped image URLs")
    confidence_score: int = Field(..., ge=0, le=100, description="Confidence score")
    method: str = Field(..., description="Matching method used")
    raw_response: Dict[str, Any] = Field(default_factory=dict, description="Raw Firecrawl response")

class ScrapingAttempt(BaseModel):
    """Database model for scraping attempts tracking."""
    id: Optional[UUID] = None
    product_id: UUID = Field(..., description="Product ID")
    attempt_number: int = Field(..., description="Attempt number")
    search_url: Optional[str] = Field(None, description="Search URL used")
    method: str = Field(..., description="Scraping method")
    status: str = Field(..., description="Attempt status")
    confidence_score: int = Field(default=0, description="Confidence score")
    firecrawl_response: Optional[Dict[str, Any]] = Field(None, description="Firecrawl response")
    error_message: Optional[str] = Field(None, description="Error message")
    credits_used: int = Field(default=0, description="Firecrawl credits used")
    processing_time_ms: Optional[int] = Field(None, description="Processing time")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### List of Tasks to Complete (In Order)

```yaml
Task 1: Database Schema Migration
CREATE backend/migrations/007_product_enrichment_system.sql:
  - CREATE scraping_attempts table with proper indexes
  - ALTER products table to add enrichment fields
  - ADD enrichment status enum values
  - CREATE enrichment analytics view

Task 2: Custom Exceptions
CREATE backend/app/exceptions/enrichment.py:
  - DEFINE EnrichmentError base exception
  - DEFINE SKUExtractionError, SearchError, ScrapingError
  - DEFINE FirecrawlAPIError with status code handling
  - FOLLOW existing exception patterns in codebase

Task 3: Firecrawl API Client
CREATE backend/app/services/firecrawl_client.py:
  - IMPLEMENT FirecrawlClient with async httpx
  - ADD retry logic with tenacity decorator
  - HANDLE rate limiting and timeout errors
  - MIRROR pattern from existing service classes

Task 4: LawnFawn Matcher Service
CREATE backend/app/services/lawnfawn_matcher.py:
  - IMPLEMENT SKU extraction with regex patterns
  - BUILD search URL construction logic
  - ADD product page scraping with BeautifulSoup
  - IMPLEMENT confidence scoring algorithm

Task 5: Main Enrichment Service
CREATE backend/app/services/product_enrichment.py:
  - ORCHESTRATE complete enrichment workflow
  - INTEGRATE with existing database_service patterns
  - HANDLE batch processing with concurrency control
  - FOLLOW existing service initialization patterns

Task 6: API Endpoints
CREATE backend/app/api/enrichment.py:
  - IMPLEMENT FastAPI router with proper error handling
  - ADD background task processing for batch operations
  - MIRROR patterns from existing upload.py endpoints
  - INCLUDE comprehensive request/response models

Task 7: Unit Tests
CREATE backend/tests/unit/test_*.py files:
  - TEST all service methods with proper mocking
  - FOLLOW existing test patterns from test_product_deduplication.py
  - INCLUDE edge cases and error scenarios
  - ACHIEVE 95%+ code coverage

Task 8: Integration Tests
CREATE backend/tests/integration/test_enrichment_workflow.py:
  - TEST complete workflow from invoice to enriched products
  - VALIDATE API endpoints with real database
  - FOLLOW existing integration test patterns
  - INCLUDE performance and concurrency testing

Task 9: Connectivity Tests
CREATE backend/tests/connectivity/test_firecrawl_connectivity.py:
  - TEST Firecrawl API connection and authentication
  - VALIDATE rate limiting and error handling
  - FOLLOW existing connectivity test patterns
  - INCLUDE configuration validation

Task 10: API Integration
MODIFY backend/app/main.py:
  - INCLUDE enrichment router in FastAPI app
  - FOLLOW existing router inclusion patterns
  - ENSURE proper error handling middleware
```

### Per Task Pseudocode

```python
# Task 3: Firecrawl API Client
class FirecrawlClient:
    def __init__(self):
        # PATTERN: Get config from environment like existing services
        self.api_key = os.getenv('FIRECRAWL_API_KEY')
        self.base_url = os.getenv('FIRECRAWL_BASE_URL', 'https://api.firecrawl.dev')
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def scrape_page(self, url: str) -> FirecrawlResponse:
        # CRITICAL: Use async context manager for httpx
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/v0/scrape",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"url": url, "formats": ["html"]}
            )
            # PATTERN: Proper error handling like existing services
            response.raise_for_status()
            return FirecrawlResponse(**response.json())

# Task 4: LawnFawn Matcher
class LawnFawnMatcher:
    def extract_numeric_sku(self, supplier_sku: str) -> Optional[str]:
        # PATTERN: Use regex for SKU extraction
        match = re.search(r'LF[-]?(\d+)', supplier_sku.upper())
        return match.group(1) if match else None
    
    async def match_product(self, product: Product) -> EnrichmentData:
        # PATTERN: Multi-step process with validation
        numeric_sku = self.extract_numeric_sku(product.supplier_sku)
        if not numeric_sku:
            raise SKUExtractionError(f"Could not extract SKU from: {product.supplier_sku}")
        
        search_url = self.build_search_url(numeric_sku)
        search_results = await self.search_products(search_url)
        
        if not search_results.product_links:
            raise SearchError(f"No results found for SKU: {numeric_sku}")
        
        # PATTERN: Try first result with confidence scoring
        first_product_url = search_results.product_links[0]
        product_data = await self.scrape_product_page(first_product_url)
        confidence_score = self.calculate_confidence_score(...)
        
        return EnrichmentData(...)

# Task 5: Main Enrichment Service
class ProductEnrichmentService:
    def __init__(self):
        # PATTERN: Dependency injection like existing services
        self.firecrawl_client = FirecrawlClient()
        self.lawnfawn_matcher = LawnFawnMatcher()
        self.database_service = get_database_service()
    
    async def enrich_product(self, product_id: UUID) -> ProductEnrichmentResult:
        # PATTERN: Try-catch with proper error handling and logging
        try:
            product = await self.database_service.get_product_by_id(product_id)
            if not product.supplier_sku:
                raise EnrichmentError("No supplier SKU available")
            
            # PATTERN: Update status during processing
            await self.database_service.update_product_status(product_id, ProductStatus.PROCESSING)
            
            enrichment_data = await self.lawnfawn_matcher.match_product(product)
            
            # PATTERN: Store attempt record for audit trail
            scraping_attempt = await self.database_service.create_scraping_attempt(...)
            
            # PATTERN: Update product with enriched data
            await self.database_service.update_product_enrichment(...)
            
            return ProductEnrichmentResult(success=True, ...)
            
        except Exception as e:
            # PATTERN: Store failed attempt and update status
            await self.database_service.create_scraping_attempt(status="failed", error_message=str(e))
            await self.database_service.update_product_status(product_id, ProductStatus.FAILED)
            return ProductEnrichmentResult(success=False, error_message=str(e))
```

### Integration Points
```yaml
DATABASE:
  - migration: "007_product_enrichment_system.sql"
  - tables: "scraping_attempts, enhanced products table"
  - indexes: "product_id, status, method, created_at, confidence_score"
  
CONFIG:
  - add to: backend/.env
  - pattern: "FIRECRAWL_API_KEY=your_key_here"
  - pattern: "ENRICHMENT_MAX_CONCURRENT=5"
  
ROUTES:
  - add to: backend/app/main.py
  - pattern: "app.include_router(enrichment_router, prefix='/api/products')"
  
DEPENDENCIES:
  - add to: backend/requirements.txt
  - libraries: "beautifulsoup4==4.12.2, tenacity==8.2.3, limits==3.6.0"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
ruff check backend/app/services/product_enrichment.py --fix
ruff check backend/app/services/firecrawl_client.py --fix
ruff check backend/app/services/lawnfawn_matcher.py --fix
mypy backend/app/services/product_enrichment.py
mypy backend/app/services/firecrawl_client.py
mypy backend/app/services/lawnfawn_matcher.py

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests
```python
# CREATE comprehensive test files following existing patterns:

# backend/tests/unit/test_product_enrichment.py
def test_enrich_product_success():
    """Test successful product enrichment with mocked dependencies"""
    # PATTERN: Mock all external dependencies
    with patch('app.services.database_service.get_database_service') as mock_db:
        mock_db.return_value.get_product_by_id.return_value = sample_product
        service = ProductEnrichmentService()
        result = await service.enrich_product(product_id)
        assert result.success is True

def test_enrich_product_sku_extraction_failure():
    """Test handling of invalid SKU formats"""
    # PATTERN: Test error conditions thoroughly
    with pytest.raises(SKUExtractionError):
        matcher = LawnFawnMatcher()
        await matcher.match_product(product_with_invalid_sku)

def test_firecrawl_api_timeout():
    """Test Firecrawl API timeout handling"""
    # PATTERN: Mock external API failures
    with patch('httpx.AsyncClient.post', side_effect=httpx.TimeoutException):
        client = FirecrawlClient()
        result = await client.scrape_page("https://example.com")
        assert result.success is False
```

```bash
# Run and iterate until passing:
cd backend && python -m pytest tests/unit/test_product_enrichment.py -v
cd backend && python -m pytest tests/unit/test_firecrawl_client.py -v
cd backend && python -m pytest tests/unit/test_lawnfawn_matcher.py -v

# If failing: Read error, understand root cause, fix code, re-run
```

### Level 3: Integration Test
```bash
# Start the service
cd backend && python -m uvicorn app.main:app --reload --port 8000

# Test the enrichment endpoint
curl -X POST http://localhost:8000/api/products/enrich \
  -H "Content-Type: application/json" \
  -d '{"batch_id": "test-batch-id"}'

# Expected: {"success": true, "message": "Enrichment started", "processing_started": true}
# If error: Check logs and fix issues
```

## Testing Strategy (MANDATORY)

### Pre-Implementation Testing Validation
- [ ] Run `npm run test:all` to ensure clean baseline
- [ ] Verify existing product and invoice processing tests pass
- [ ] Plan test structure for enrichment functionality

### Backend Tests (All Categories Required)
- [ ] **Unit Tests** (`backend/tests/unit/test_product_enrichment.py`):
  - [ ] ProductEnrichmentService methods with mocked dependencies
  - [ ] LawnFawnMatcher SKU extraction and confidence scoring
  - [ ] FirecrawlClient API interactions and error handling
  - [ ] Edge cases: invalid SKUs, API failures, timeout scenarios
- [ ] **Integration Tests** (`backend/tests/integration/test_enrichment_workflow.py`):
  - [ ] Complete workflow from DRAFT products to ENRICHED status
  - [ ] API endpoint functionality with real database
  - [ ] Batch processing and concurrent enrichment scenarios
  - [ ] Error recovery and retry mechanisms
- [ ] **Connectivity Tests** (`backend/tests/connectivity/test_firecrawl_connectivity.py`):
  - [ ] Firecrawl API authentication and connection
  - [ ] Rate limiting and timeout configuration
  - [ ] Environment variable validation

### Test Execution Validation (MANDATORY)
- [ ] **Quick Validation**: `npm run test:quick` passes during development
- [ ] **Pre-Commit Validation**: `npm run test:pre-commit` passes before completion
- [ ] **Full Test Suite**: `npm run test:all` passes before task completion
- [ ] **Coverage Validation**: Meets 95%+ coverage requirement for new code
- [ ] **No Regressions**: All existing tests continue to pass

## Documentation Updates Required (MANDATORY)

### Core Documentation
- [ ] Update README.md with enrichment setup instructions
- [ ] Document new API endpoints in API documentation
- [ ] Update architecture docs with enrichment workflow
- [ ] Create interface documentation for enrichment models

### Code Documentation
- [ ] Add Google-style docstrings to all new functions
- [ ] Document complex SKU extraction and confidence scoring logic
- [ ] Update type hints and annotations throughout
- [ ] Document Firecrawl API configuration options

## Final Validation Checklist (MANDATORY)
- [ ] **All tests pass**: `npm run test:all` ✅
- [ ] **Coverage meets standards**: 95%+ overall coverage ✅
- [ ] **No test regressions**: Existing functionality unaffected ✅
- [ ] **Environment validated**: All required environment variables set ✅
- [ ] No linting errors: `ruff check backend/app/` passes
- [ ] No type errors: `mypy backend/app/` passes
- [ ] Manual test successful: Enrichment API endpoints work correctly
- [ ] Error cases handled gracefully with proper logging
- [ ] Database migration applied successfully
- [ ] Firecrawl API integration working with rate limiting
- [ ] Documentation updated as specified above
- [ ] Ready for PRP completion workflow

---

## Anti-Patterns to Avoid
- ❌ Don't create synchronous functions in async service context
- ❌ Don't skip retry logic for external API calls
- ❌ Don't ignore rate limiting - respect website policies
- ❌ Don't hardcode confidence score thresholds - use configuration
- ❌ Don't catch generic exceptions - be specific about error types
- ❌ Don't skip audit trail - always record scraping attempts
- ❌ Don't ignore test coverage requirements - they are mandatory
- ❌ Don't skip database migration - schema changes are required
- ❌ Don't forget to handle UUID string conversion for Supabase
- ❌ Don't skip background task processing for long operations
