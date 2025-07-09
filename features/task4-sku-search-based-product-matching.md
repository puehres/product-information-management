# Task 4: SKU-Search-Based Product Matching (Lawn Fawn)

**Status**: ✅ COMPLETED (2025-01-09)  
**Priority**: High  
**Complexity**: Medium  
**Estimated Effort**: 3-4 days  

## Overview

Implement intelligent product matching for Lawn Fawn products using SKU-based search and web scraping. This system extracts SKU numbers from invoice data, searches the Lawn Fawn website, and enriches product information with detailed descriptions, images, and metadata.

## Business Requirements

### Core Functionality
- **SKU Extraction**: Parse LF numbers from invoice data (LF3242 → 3242)
- **Website Search**: Construct and execute search queries on lawnfawn.com
- **Product Matching**: Find and validate product matches with confidence scoring
- **Data Enrichment**: Extract comprehensive product details from product pages
- **Error Handling**: Graceful handling of failed searches and scraping errors
- **Performance**: Efficient processing with rate limiting and retry mechanisms

### Success Criteria
- **Accuracy**: 90%+ successful product matching for valid LF numbers
- **Performance**: Process 50 products in under 10 minutes
- **Reliability**: Robust error handling with comprehensive logging
- **Scalability**: Support for concurrent processing with rate limiting
- **Maintainability**: Extensible architecture for future suppliers

## Technical Specifications

### Architecture Components

#### 1. SKU Extraction Service
```python
class LawnFawnMatcher:
    def extract_sku(self, lf_number: str) -> str:
        """Extract numeric SKU from LF number (LF3242 → 3242)"""
        # Handle variations: LF3242, LF-3242, lf3242
        return lf_number.upper().replace("LF", "").replace("-", "").strip()
```

#### 2. Search URL Construction
```python
def build_search_url(self, sku: str) -> str:
    """Build Lawn Fawn search URL with proper parameters"""
    base_url = "https://www.lawnfawn.com/search"
    params = {
        "options[prefix]": "last",
        "q": sku,
        "filter.p.product_type": ""
    }
    return f"{base_url}?{urlencode(params)}"
```

#### 3. Web Scraping Integration
- **Firecrawl API**: Primary scraping service with structured data extraction
- **Rate Limiting**: Respect website terms with configurable delays
- **Retry Logic**: Exponential backoff for failed requests
- **Error Recovery**: Fallback strategies for scraping failures

#### 4. Confidence Scoring System
- **95%**: Unique SKU match with exact product found
- **80%**: Multiple results, first match selected
- **60%**: Fallback search methods successful
- **30%**: Partial match requiring manual review
- **0%**: No match found, manual intervention required

### Database Schema

#### Product Enrichment System
```sql
-- Migration 007: Product enrichment system
CREATE TABLE IF NOT EXISTS enrichment_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    method VARCHAR(50) NOT NULL, -- 'sku_search', 'name_search', 'manual'
    search_query VARCHAR(500) NOT NULL,
    search_url TEXT,
    result_url TEXT,
    confidence_score INTEGER CHECK (confidence_score >= 0 AND confidence_score <= 100),
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'success', 'failed', 'manual_review'
    error_message TEXT,
    scraped_data JSONB,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_enrichment_attempts_product_id ON enrichment_attempts(product_id);
CREATE INDEX IF NOT EXISTS idx_enrichment_attempts_status ON enrichment_attempts(status);
CREATE INDEX IF NOT EXISTS idx_enrichment_attempts_method ON enrichment_attempts(method);
CREATE INDEX IF NOT EXISTS idx_enrichment_attempts_confidence ON enrichment_attempts(confidence_score DESC);
```

### API Endpoints

#### Product Enrichment Management
```python
# POST /api/v1/enrichment/enrich/{product_id}
# - Trigger enrichment for specific product
# - Returns: enrichment attempt details and status

# GET /api/v1/enrichment/status/{product_id}
# - Get enrichment status and results
# - Returns: current status, confidence score, scraped data

# POST /api/v1/enrichment/batch
# - Trigger batch enrichment for multiple products
# - Returns: batch processing status and progress

# GET /api/v1/enrichment/attempts
# - List enrichment attempts with filtering
# - Supports: status, method, confidence range filters
```

### Service Layer Architecture

#### 1. Product Enrichment Service
```python
class ProductEnrichmentService:
    """Main orchestration service for product enrichment"""
    
    async def enrich_product(self, product_id: UUID) -> EnrichmentResult:
        """Enrich single product with web scraping"""
        
    async def enrich_batch(self, product_ids: List[UUID]) -> BatchEnrichmentResult:
        """Process multiple products concurrently"""
        
    async def get_enrichment_status(self, product_id: UUID) -> EnrichmentStatus:
        """Get current enrichment status and results"""
```

#### 2. Firecrawl Client Integration
```python
class FirecrawlClient:
    """Web scraping client with rate limiting and error handling"""
    
    async def scrape_page(self, url: str) -> FirecrawlResponse:
        """Scrape single page with structured data extraction"""
        
    async def health_check(self) -> Dict[str, Any]:
        """Validate Firecrawl API connectivity"""
        
    async def get_credits_info(self) -> Dict[str, Any]:
        """Get API usage information (mock for Firecrawl)"""
```

#### 3. Lawn Fawn Matcher
```python
class LawnFawnMatcher:
    """Lawn Fawn specific matching logic"""
    
    async def find_product_by_sku(self, sku: str) -> Optional[ProductMatch]:
        """Find product using SKU-based search"""
        
    async def extract_product_details(self, product_url: str) -> ProductDetails:
        """Extract detailed product information from product page"""
        
    def calculate_confidence(self, search_results: List[SearchResult]) -> int:
        """Calculate confidence score based on search results"""
```

### Error Handling Strategy

#### Exception Hierarchy
```python
class EnrichmentError(Exception):
    """Base exception for enrichment operations"""

class FirecrawlAPIError(EnrichmentError):
    """Firecrawl API specific errors"""
    
class ScrapingError(EnrichmentError):
    """Web scraping related errors"""
    
class RateLimitError(EnrichmentError):
    """Rate limiting errors with retry information"""
    
class ConfigurationError(EnrichmentError):
    """Configuration and setup errors"""
```

#### Retry Logic
- **Exponential Backoff**: 1s, 2s, 4s, 8s delays
- **Max Attempts**: 3 retries for transient failures
- **Rate Limiting**: Respect API limits with automatic delays
- **Circuit Breaker**: Temporary disable on repeated failures

### Configuration Management

#### Environment Variables
```env
# Firecrawl API Configuration
FIRECRAWL_API_KEY=fc-1913bea1fd544d4496890018e3164f1a
FIRECRAWL_BASE_URL=https://api.firecrawl.dev
FIRECRAWL_TIMEOUT=30
FIRECRAWL_MAX_RETRIES=3
FIRECRAWL_RETRY_DELAY=2

# Product Enrichment Configuration
ENRICHMENT_MAX_CONCURRENT=5
ENRICHMENT_BATCH_SIZE=10
ENRICHMENT_TIMEOUT=300
ENRICHMENT_RETRY_ATTEMPTS=3
ENRICHMENT_RETRY_DELAY=5

# LawnFawn Specific Configuration
LAWNFAWN_BASE_URL=https://www.lawnfawn.com
LAWNFAWN_SEARCH_DELAY=2
LAWNFAWN_PAGE_TIMEOUT=15

# Confidence Score Thresholds
CONFIDENCE_EXACT_MATCH=100
CONFIDENCE_FIRST_RESULT_MATCH=90
CONFIDENCE_FIRST_RESULT_NO_MATCH=60
CONFIDENCE_FALLBACK=30
CONFIDENCE_MINIMUM_THRESHOLD=30

# Rate Limiting
SCRAPING_REQUESTS_PER_MINUTE=30
SCRAPING_BURST_LIMIT=10
```

## Implementation Details

### Search Strategy Implementation

#### 1. SKU Extraction Logic
```python
def extract_sku(self, lf_number: str) -> str:
    """
    Extract numeric SKU from various LF number formats.
    
    Examples:
    - LF3242 → 3242
    - LF-3242 → 3242  
    - lf3242 → 3242
    - LF 3242 → 3242
    """
    if not lf_number:
        raise ValueError("LF number cannot be empty")
    
    # Normalize and extract numeric part
    cleaned = lf_number.upper().replace("LF", "").replace("-", "").replace(" ", "").strip()
    
    if not cleaned.isdigit():
        raise ValueError(f"Invalid LF number format: {lf_number}")
    
    return cleaned
```

#### 2. Search URL Construction
```python
def build_search_url(self, sku: str) -> str:
    """Build search URL with proper encoding and parameters"""
    base_url = "https://www.lawnfawn.com/search"
    
    # Use actual Lawn Fawn search parameters
    params = {
        "options[prefix]": "last",
        "q": sku,
        "filter.p.product_type": ""
    }
    
    return f"{base_url}?{urlencode(params)}"
```

#### 3. Product URL Extraction
```python
async def extract_product_urls(self, search_html: str) -> List[str]:
    """Extract product URLs from search results HTML"""
    soup = BeautifulSoup(search_html, 'html.parser')
    
    # Find product links in search results
    product_links = soup.find_all('a', href=True)
    product_urls = []
    
    for link in product_links:
        href = link.get('href')
        if href and '/products/' in href:
            # Convert relative URLs to absolute
            if href.startswith('/'):
                href = f"https://www.lawnfawn.com{href}"
            product_urls.append(href)
    
    return list(set(product_urls))  # Remove duplicates
```

### Data Extraction Implementation

#### 1. Product Details Extraction
```python
async def extract_product_details(self, product_url: str) -> ProductDetails:
    """Extract comprehensive product details from product page"""
    
    # Scrape product page
    response = await self.firecrawl_client.scrape_page(product_url)
    
    if not response.success:
        raise ScrapingError(f"Failed to scrape product page: {product_url}")
    
    # Parse product information
    soup = BeautifulSoup(response.content, 'html.parser')
    
    return ProductDetails(
        name=self._extract_product_name(soup),
        description=self._extract_description(soup),
        images=self._extract_image_urls(soup),
        price=self._extract_price(soup),
        availability=self._extract_availability(soup),
        specifications=self._extract_specifications(soup),
        categories=self._extract_categories(soup)
    )
```

#### 2. Confidence Scoring Logic
```python
def calculate_confidence(self, sku: str, search_results: List[str], product_details: ProductDetails) -> int:
    """Calculate confidence score based on search and extraction results"""
    
    if not search_results:
        return 0  # No results found
    
    if len(search_results) == 1:
        # Single result - high confidence if SKU matches
        if sku in product_details.name or sku in product_details.description:
            return 95  # Exact match
        else:
            return 80  # Single result but no SKU confirmation
    
    elif len(search_results) <= 3:
        # Few results - medium confidence
        return 60
    
    else:
        # Many results - lower confidence, needs review
        return 30
```

### Testing Strategy

#### 1. Unit Tests
```python
# tests/unit/test_lawnfawn_matcher.py
class TestLawnFawnMatcher:
    def test_extract_sku_valid_formats(self):
        """Test SKU extraction from various valid formats"""
        
    def test_extract_sku_invalid_formats(self):
        """Test error handling for invalid formats"""
        
    def test_build_search_url(self):
        """Test search URL construction"""
        
    def test_confidence_calculation(self):
        """Test confidence scoring logic"""
```

#### 2. Integration Tests
```python
# tests/integration/test_enrichment_workflow.py
class TestEnrichmentWorkflow:
    async def test_end_to_end_enrichment(self):
        """Test complete enrichment workflow"""
        
    async def test_batch_processing(self):
        """Test concurrent batch processing"""
        
    async def test_error_recovery(self):
        """Test error handling and recovery"""
```

#### 3. Connectivity Tests
```python
# tests/connectivity/test_firecrawl_connectivity.py
class TestFirecrawlConnectivity:
    async def test_real_api_scraping(self):
        """Test actual Firecrawl API integration"""
        
    async def test_lawnfawn_website_access(self):
        """Test Lawn Fawn website accessibility"""
```

## Performance Considerations

### Optimization Strategies
- **Concurrent Processing**: Process multiple products simultaneously
- **Rate Limiting**: Respect website terms with configurable delays
- **Caching**: Cache search results to avoid duplicate requests
- **Database Indexing**: Optimize queries with strategic indexes
- **Connection Pooling**: Reuse HTTP connections for efficiency

### Monitoring and Metrics
- **Success Rate**: Track enrichment success percentage
- **Processing Time**: Monitor average processing time per product
- **Error Rates**: Track and alert on error patterns
- **API Usage**: Monitor Firecrawl API credit consumption
- **Confidence Distribution**: Analyze confidence score patterns

## Security Considerations

### Data Protection
- **API Key Security**: Secure storage of Firecrawl API credentials
- **Rate Limiting**: Prevent abuse with request throttling
- **Input Validation**: Sanitize all user inputs and URLs
- **Error Handling**: Avoid exposing sensitive information in errors

### Compliance
- **Robots.txt**: Respect website scraping policies
- **Terms of Service**: Comply with Lawn Fawn website terms
- **Data Privacy**: Handle scraped data according to privacy regulations
- **Rate Limiting**: Respectful scraping practices

## Deployment Requirements

### Dependencies
```python
# New dependencies for Task 4
beautifulsoup4==4.12.2    # HTML parsing
tenacity==8.2.3           # Retry logic
limits==3.5.0             # Rate limiting
httpx==0.25.0             # HTTP client (already installed)
structlog==23.1.0         # Logging (already installed)
```

### Environment Setup
- **Firecrawl API Key**: Required for web scraping functionality
- **Database Migration**: Apply migration 007 for enrichment system
- **Configuration**: Set environment variables for rate limiting and timeouts

### Monitoring Setup
- **Health Checks**: Monitor Firecrawl API connectivity
- **Error Alerting**: Alert on high error rates or API failures
- **Performance Monitoring**: Track processing times and success rates

## Future Enhancements

### Phase 2 Considerations
- **Multi-Supplier Support**: Extend architecture for other suppliers
- **Advanced Matching**: Implement fuzzy matching algorithms
- **Machine Learning**: Add ML-based confidence scoring
- **User Interface**: Build review interface for manual validation

### Scalability Improvements
- **Queue System**: Implement background job processing
- **Distributed Processing**: Support for multiple worker instances
- **Advanced Caching**: Redis-based caching for improved performance
- **API Rate Management**: Dynamic rate limiting based on API quotas

## Risk Assessment

### Technical Risks
- **Website Changes**: Lawn Fawn website structure modifications
- **API Limitations**: Firecrawl API rate limits or service issues
- **Data Quality**: Inconsistent or missing product information
- **Performance**: Slow scraping affecting user experience

### Mitigation Strategies
- **Flexible Parsing**: Robust HTML parsing with fallback strategies
- **Error Recovery**: Comprehensive retry and fallback mechanisms
- **Data Validation**: Quality checks and manual review workflows
- **Performance Monitoring**: Real-time monitoring and alerting

## Success Metrics

### Quantitative Metrics
- **Match Rate**: 90%+ successful product matches
- **Processing Speed**: <12 seconds average per product
- **Error Rate**: <5% failed enrichment attempts
- **Confidence Accuracy**: 85%+ high-confidence matches are correct

### Qualitative Metrics
- **User Satisfaction**: Positive feedback on enriched product data
- **Data Quality**: Comprehensive and accurate product information
- **System Reliability**: Consistent performance under normal load
- **Maintainability**: Easy to extend and modify for new requirements

## Completion Criteria

### Technical Completion
- [x] All service components implemented and tested
- [x] Database migration applied successfully
- [x] API endpoints functional and documented
- [x] Comprehensive test suite with good coverage
- [x] Error handling and logging implemented

### Business Completion
- [x] SKU extraction working for all LF number formats
- [x] Search and scraping functionality operational
- [x] Confidence scoring system implemented
- [x] Batch processing capability available
- [x] Integration with existing product management system

### Documentation Completion
- [x] Technical documentation complete
- [x] API documentation with examples
- [x] Configuration and deployment guides
- [x] Testing procedures documented
- [x] Troubleshooting and maintenance guides

---

**Dependencies**: Task 3 (Enhanced Invoice Parser), Task 3.5 (Testing Infrastructure)  
**Blocks**: Task 5 (Cloud Image Processing Pipeline)  
**Related**: Task 3.4 (Product Deduplication System)
