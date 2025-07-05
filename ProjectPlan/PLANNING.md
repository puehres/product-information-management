# Product Automation System for Stempelwunderwelt.at

## Project Overview
Build a lean, iterative product automation system to eliminate manual product import processes for craft suppliers (Lawn Fawn, Craftlines, Mama Elephant) into Gambio webshop, delivering immediate value with each iteration.

## Core Problem Statement
Currently, adding products to the Gambio webshop requires:
- Manual data entry from supplier CSV files and invoices
- Manual product URL discovery and matching
- Manual image downloading and processing
- Manual translation from English to German
- Manual SEO optimization and category assignment
- Manual creation of Gambio import files

**Time Impact**: 5+ hours for 50 products → Target: 30 minutes with automation

## Three-Phase Development Strategy

### **Phase 1: MVP - Lawn Fawn → Gambio**
**Goal**: Prove core value with single supplier automation
**Value**: Process 50 Lawn Fawn products in 30 minutes vs 5 hours manually

**Core Pipeline:**
```
Lawn Fawn CSV → SKU Matching → Product Scraping → Image Processing → 
German Translation → Gambio CSV Export
```

**Key Features:**
- Lawn Fawn CSV upload and parsing
- SKU-based product URL construction and scraping
- Basic image download and JPEG conversion
- OpenAI-powered German translation
- Gambio 4.4.0.4 CSV export with proper formatting
- Simple web interface for upload/download

### **Phase 2: Multi-Supplier Expansion**
**Goal**: Complete supplier coverage with intelligent matching
**Value**: Handle all 3 suppliers with different data formats and matching strategies

**Enhanced Pipeline:**
```
Multi-Supplier Input → Intelligent Matching → Quality Review → 
Enhanced Processing → Unified Export
```

**Key Features:**
- Craftlines support (code-based matching)
- Mama Elephant support (name-based fuzzy matching)
- Supplier abstraction layer
- Review workflow for uncertain matches
- Cross-supplier duplicate detection
- Enhanced image quality validation

### **Phase 3: Production Ready**
**Goal**: Business-ready system with reliability and polish
**Value**: Dependable automation suitable for daily operations

**Production Features:**
- Comprehensive error handling and recovery
- Performance optimization for large batches
- User documentation and training materials
- Monitoring and logging systems
- Backup and data protection

### Technology Stack

#### Backend
- **Framework**: Python FastAPI or Node.js Express
- **Database**: Supabase PostgreSQL (eu-central-1, Frankfurt) for structured data
- **Caching**: Upstash Redis (free tier) for session storage and translation caching
- **Web Scraping**: Firecrawl API for reliable, enterprise-grade scraping
- **Translation**: Google Translate API or OpenAI GPT-4 for context-aware translations
- **Image Processing**: Pillow (Python) for in-memory processing and JPEG conversion
- **Cloud Storage**: AWS S3 (eu-central-1, Frankfurt) for image processing pipeline

#### Frontend
- **Framework**: React with TypeScript
- **UI Library**: Tailwind CSS + Shadcn/UI components
- **State Management**: React Query for server state
- **File Upload**: React-Dropzone for drag-and-drop

#### APIs & Services
- **Firecrawl**: Web scraping with JavaScript rendering
- **OpenAI GPT**: Product descriptions, translations, SEO tags
- **AWS S3**: Image storage and processing pipeline
- **boto3**: AWS SDK for Python S3 integration
- **Supabase**: PostgreSQL database with real-time features
- **Upstash**: Redis caching (free tier)

## Database Architecture

### **Supabase PostgreSQL (Cost-Effective Choice)**
**Decision**: Use Supabase instead of AWS RDS for significant cost savings
**Region**: eu-central-1 (Frankfurt) for optimal German user performance

### **Cost Comparison**
- **AWS RDS + ElastiCache**: ~$28/month for MVP
- **Supabase + Upstash**: $0/month for MVP (free tiers)
- **Savings**: $336/year during development phase

### **Supabase Free Tier Benefits**
- **Database**: 500MB PostgreSQL storage (sufficient for MVP)
- **Bandwidth**: 2GB/month data transfer
- **Real-time**: WebSocket subscriptions included
- **Auth**: 50,000 monthly active users
- **Storage**: 1GB file storage (alternative to S3 if needed)
- **Edge Functions**: 500,000 invocations/month

### **Development Setup**
```python
# Supabase Configuration
from supabase import create_client, Client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

# Standard PostgreSQL connection also works
DATABASE_URL = os.environ.get("SUPABASE_DATABASE_URL")
```

### **Scaling Path**
- **MVP**: Free tier ($0/month)
- **Production**: Pro tier ($25/month when needed)
- **Features**: Same PostgreSQL functionality + real-time updates
- **Migration**: Standard PostgreSQL migrations work seamlessly

### **Redis Caching (Upstash)**
- **Free Tier**: 10,000 commands/day, 256MB storage
- **Purpose**: Translation caching, session storage, processing queues
- **Serverless**: Pay-per-use model, no idle costs
- **Global**: Low-latency worldwide access

## Image Storage Architecture

### **Cloud-First Processing Pipeline**
**Decision**: Use AWS S3 for image processing, not local storage or hosting
**Purpose**: Temporary processing workspace → Download package → Manual FTP to Gambio

### **S3 Configuration (eu-central-1)**
- **Region**: Frankfurt for optimal performance with German users
- **Bucket Structure**: Organized processing and export folders
- **Access**: Private bucket with presigned URLs for downloads
- **Lifecycle**: Automatic cleanup to minimize costs

### **Processing Workflow**
```
Supplier URLs → S3 Processing → JPEG Conversion → Export Package → User Download → FTP to Gambio
```

### **S3 Bucket Organization**
```
s3://product-processing-bucket/
├── processing/{batch_id}/
│   ├── raw/                    # Original downloaded images
│   └── processed/              # Converted JPEG images
└── exports/{export_date}/
    ├── gambio_import.csv       # Gambio-compatible CSV
    └── images/                 # All JPEG files for FTP upload
```

### **Export Package Generation**
- **Format**: ZIP file with CSV + images folder
- **Download**: Time-limited presigned URLs (24 hours)
- **Content**: Gambio CSV + organized JPEG files + import instructions
- **User Workflow**: Download → Import CSV to Gambio → FTP images to server

### **Cost Optimization**
- **Lifecycle Policies**: Auto-delete processing files (7 days), exports (30 days)
- **Minimal Storage**: Only active processing and recent exports
- **Estimated Cost**: <$0.05/month for MVP scale (1000 products, 3 images each)
- **No CDN**: Direct S3 URLs for download packages only

### **Quality Standards**
- **Format**: All images converted to JPEG for Gambio compatibility
- **Dimensions**: Minimum 1000px on longest edge (with quality warnings)
- **Naming**: Standardized {SKU}_{type}_{sequence}.jpeg format
- **Processing**: In-memory conversion, no local file storage

## Universal Supplier Framework

### Supplier Configuration System
- **Pluggable Architecture**: Easy addition of new suppliers through configuration
- **Configuration-Driven**: Each supplier defined by config, not hardcoded logic
- **Identifier Flexibility**: Support any type of unique identifier (SKUs, names, codes, EANs)
- **Scraping Strategies**: Multiple fallback methods per supplier with confidence scoring

### Universal Processing Workflow
1. **Supplier Selection**: Choose from configured suppliers or add new ones
2. **File Upload**: Flexible input parsing (CSV, Excel, PDF, manual entry) with auto-detection
3. **Product Matching**: Supplier-specific scraping with universal confidence scoring
4. **Review System**: Universal flagging and review for uncertain matches, images, duplicates
5. **Duplicate Detection**: Cross-supplier duplicate identification and resolution
6. **Export Generation**: Standardized Gambio output regardless of source supplier

### Enhanced Database Schema

#### Suppliers Table (New)
- `id`: Primary key
- `name`: Supplier name (Lawn Fawn, Craftlines, Mama Elephant)
- `code`: Short code (LF, CL, ME)
- `website_url`: Base website URL
- `identifier_type`: What constitutes unique ID (sku, product_name, ean, code)
- `scraping_config`: JSON config for scraping strategy and selectors
- `search_url_template`: Template for product search URLs
- `active`: Boolean flag for enabled suppliers
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

#### Upload_Batches Table (Enhanced)
- `id`: Primary key
- `supplier_id`: Foreign key to suppliers
- `filename`: Original upload filename
- `file_type`: CSV, Excel, PDF, manual
- `identifier_column`: Which column/field contains unique identifiers
- `total_items`: Number of items in upload
- `processed_items`: Number successfully processed
- `flagged_items`: Number requiring review
- `duplicate_items`: Number of detected duplicates
- `status`: uploaded, processing, review_required, completed, failed
- `processing_notes`: JSON log of processing steps and issues
- `uploaded_at`: Upload timestamp
- `completed_at`: Processing completion timestamp

#### Product_Matches Table (New)
- `id`: Primary key
- `batch_id`: Foreign key to upload_batches
- `supplier_id`: Foreign key to suppliers
- `original_identifier`: Raw identifier from upload (SKU, name, code)
- `normalized_identifier`: Cleaned/standardized version
- `detected_url`: Found product URL
- `confidence_score`: Match confidence (0-100)
- `match_method`: How match was found (exact, fuzzy, search, browse, manual)
- `review_status`: auto_approved, pending_review, user_approved, rejected, manual_override
- `manual_url`: User-provided URL override
- `review_notes`: User notes/comments during review
- `created_at`: Match creation timestamp
- `reviewed_at`: Review completion timestamp

#### Products Table (Enhanced)
- `id`: Primary key
- `supplier_id`: Foreign key to suppliers
- `batch_id`: Foreign key to upload_batches (source batch)
- `match_id`: Foreign key to product_matches
- `supplier_sku`: Original supplier SKU/identifier
- `internal_sku`: Generated internal SKU
- `original_identifier`: Source identifier from upload
- `original_name`: English product name
- `german_name`: Translated German name
- `original_description`: English description
- `german_description`: German description
- `category`: Product category
- `supplier_price_eur`: EUR pricing from supplier
- `tax_class_id`: Foreign key to tax_classes
- `stock_info`: Stock information
- `seo_keywords`: Generated SEO keywords
- `meta_title`: SEO meta title
- `meta_description`: SEO meta description
- `gambio_url_slug`: SEO-friendly URL slug
- `gambio_url_at`: Full stempelwunderwelt.at URL
- `gambio_url_de`: Full stempelwunderwelt.de URL
- `gambio_category_primary`: "Neu: [Manufacturer]" category
- `gambio_category_secondary`: "PD-neu" category
- `category_path`: Full category hierarchy for URL generation
- `min_image_dimension`: Minimum image dimension found
- `image_quality_warning`: Flag for substandard images
- `duplicate_of`: Foreign key to another product (if duplicate)
- `duplicate_status`: unique, potential_duplicate, confirmed_duplicate, merged
- `review_flags`: JSON array of issues requiring review
- `scraped_at`: Last scrape timestamp
- `status`: draft, review_required, ready, exported
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

#### Images Table (Enhanced)
- `id`: Primary key
- `product_id`: Foreign key to products
- `filename`: Generated filename (always .jpeg)
- `original_url`: Source URL
- `original_format`: Original image format before conversion
- `alt_text`: SEO alt text
- `image_type`: main, additional, detail, manual_upload
- `sort_order`: Display order
- `file_size`: Image file size
- `dimensions`: Width x Height
- `longest_edge`: Longest dimension in pixels
- `meets_quality_standard`: Boolean (≥1000px longest edge)
- `review_status`: auto_approved, flagged, user_approved, manual_upload
- `upload_source`: scraped, manual_upload
- `created_at`: Creation timestamp

#### Image_Reviews Table (New)
- `id`: Primary key
- `product_id`: Foreign key to products
- `issue_type`: missing_images, poor_quality, manual_needed, user_request
- `status`: pending, resolved, user_uploaded, skipped
- `manual_images`: JSON array of user-uploaded image paths
- `resolution_notes`: User notes about resolution
- `created_at`: Issue creation timestamp
- `resolved_at`: Resolution timestamp

#### Categories Table (Enhanced)
- `id`: Primary key
- `name`: Category name
- `slug`: URL-friendly slug
- `parent_id`: Foreign key to parent category
- `supplier_id`: Associated supplier (for supplier categories, null for universal)
- `gambio_category_id`: Gambio system category ID
- `is_import_category`: Boolean flag for IMPORT category
- `is_supplier_category`: Boolean flag for supplier categories
- `category_path`: Full hierarchy path for URLs
- `active`: Boolean flag for enabled categories
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

#### Duplicate_Groups Table (New)
- `id`: Primary key
- `master_product_id`: Foreign key to the primary/kept product
- `duplicate_product_id`: Foreign key to the duplicate product
- `similarity_score`: Calculated similarity (0-100)
- `match_factors`: JSON array of what matched (name, description, images, specs)
- `resolution_status`: pending, confirmed, rejected, auto_merged
- `resolution_method`: user_decision, auto_merge, manual_review
- `resolved_by`: User who made the decision
- `created_at`: Detection timestamp
- `resolved_at`: Resolution timestamp

#### Review_Queue Table (New)
- `id`: Primary key
- `item_type`: product_match, image_issue, duplicate, manual_review
- `item_id`: Foreign key to relevant table (product_matches, image_reviews, etc.)
- `priority`: high, medium, low
- `status`: pending, in_progress, completed, skipped
- `assigned_to`: User assigned to review (optional)
- `review_notes`: User notes during review
- `created_at`: Queue entry timestamp
- `completed_at`: Review completion timestamp

#### Tax_Classes Table (New)
- `id`: Primary key
- `country_code`: Country code (AT, DE, etc.)
- `tax_rate`: VAT percentage (20.0, 19.0, etc.)
- `gambio_tax_class_id`: Gambio's internal tax class ID
- `description`: Human-readable description (e.g., "Austria Standard VAT")
- `is_default`: Boolean flag for default tax class per country
- `active`: Boolean flag for enabled tax classes
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Product Naming Taxonomy

#### SKU Generation
- Format: `{SUPPLIER_CODE}-{CATEGORY_CODE}-{SEQUENCE}`
- Example: `LF-STAMP-001`, `CL-DIES-042`
- Ensure uniqueness across all suppliers

#### URL Generation
- Format: `/{supplier-slug}/{category-slug}/{product-slug}`
- Example: `/lawn-fawn/clear-stamps/happy-howlidays-stamp-set`
- Multi-domain: `stempelwunderwelt.at` and `stempelwunderwelt.de`
- Ensures uniqueness through supplier/category namespacing

#### Image Naming
- Format: `{INTERNAL_SKU}_{IMAGE_TYPE}_{SEQUENCE}.jpeg`
- Example: `LF-STAMP-001_main_01.jpeg`, `LF-STAMP-001_detail_02.jpeg`
- All images converted to JPEG format for Gambio compatibility

#### Folder Structure
```
/exports/
  /{export_date}/
    /csv/
      - gambio_import.csv
    /images/
      /{category}/
        - {sku}_main_01.jpeg
        - {sku}_detail_01.jpeg
```

## Supplier vs Manufacturer Business Model

### **Critical Distinction: Invoice Suppliers vs Product Manufacturers**

**Invoice Suppliers** = Who you buy from (business relationship)
- LawnFawn (direct manufacturer sales)
- Craftlines (European wholesaler/distributor)
- Mama Elephant (direct manufacturer sales)

**Product Manufacturers** = Who makes the products (for scraping/categorization)
- LawnFawn products (can be sold by LawnFawn directly OR by Craftlines)
- Mama Elephant products (can be sold by Mama Elephant directly OR by Craftlines)
- Craftlines own-brand products (sold only by Craftlines)

### **Real-World Business Scenarios**

#### **Scenario 1: Direct Manufacturer Purchase**
```
Invoice From: LawnFawn
Products: Only LawnFawn products (LF1142, LF1167, etc.)
Scraping Target: lawnfawn.com
```

#### **Scenario 2: Wholesaler Purchase (Multi-Manufacturer)**
```
Invoice From: Craftlines
Products: Mixed manufacturers
- LawnFawn products (LF1142 - Lawn Cuts - Stitched Rectangle Frames)
- Mama Elephant products (ME5678 - Clear Stamps - Happy Birthday)
- Craftlines products (CL1234 - Dies - Custom Shape)
Scraping Targets: lawnfawn.com, mamaelephant.com, craftlines.eu
```

### **Enhanced Supplier Data Mapping Matrix**

| Field | LawnFawn Direct | Craftlines Multi-Mfg | Mama Elephant Direct | Scraping Priority |
|-------|-----------------|----------------------|---------------------|-------------------|
| **Invoice Supplier** | ✅ LawnFawn | ✅ Craftlines | ✅ Mama Elephant | N/A |
| **Product Manufacturers** | ✅ LawnFawn only | ⚠️ Mixed (LF+ME+CL) | ✅ Mama Elephant only | CRITICAL |
| **Manufacturer SKUs** | ✅ LF1142 | ✅ LF1142, ME5678 | ❌ Name only | HIGH |
| **Product Names** | ✅ Available | ✅ Available | ✅ Available | LOW |
| **Images** | ❌ Need scraping | ❌ Need scraping | ❌ Need scraping | CRITICAL |
| **Categories** | ❌ Need scraping | ❌ Need scraping | ❌ Need scraping | HIGH |
| **Pricing** | ✅ USD from invoice | ✅ EUR from invoice | ✅ USD from invoice | MEDIUM |

### **Supplier-Specific Processing Strategies**

### 1. LawnFawn Direct (lawnfawn.com invoices)
**Invoice Characteristics:**
- **Header**: "Lawn Fawn, Rancho Santa Margarita, CA 92688"
- **Format**: Clean table with Qty, Description, Price, Origin, Tariff Code, Amount
- **Products**: Only LawnFawn products (LF SKU format)
- **Currency**: USD pricing
- **Description Format**: "LF1142 - Lawn Cuts - Stitched Rectangle Frames Dies"

**Processing Strategy:**
- **Supplier Detection**: Company name in header (95% confidence)
- **Product Parsing**: Extract LF SKU, category, product name from description
- **Scraping Target**: lawnfawn.com only
- **Currency**: Store USD prices as-is, no conversion needed
- **Confidence**: HIGH (single manufacturer, consistent format)

### 2. Craftlines Wholesaler (craftlines.eu invoices)
**Invoice Characteristics:**
- **Header**: "Craftlines" or "Craft Lines Europe"
- **Format**: Multi-manufacturer product mix
- **Products**: LawnFawn (LF), Mama Elephant (ME), Craftlines (CL) products
- **Currency**: EUR pricing
- **Description Formats**: 
  - "LF1142 - Lawn Cuts - Stitched Rectangle Frames Dies" (LF products)
  - "ME5678 - Clear Stamps - Happy Birthday" (ME products)
  - "CL1234 - Dies - Custom Shape" (Craftlines products)

**Processing Strategy:**
- **Supplier Detection**: Company name in header
- **Product Parsing**: Extract manufacturer SKU, determine manufacturer from SKU prefix
- **Scraping Targets**: Multiple sites based on manufacturer
  - LF products → lawnfawn.com
  - ME products → mamaelephant.com  
  - CL products → craftlines.eu
- **Currency**: EUR prices from invoice
- **Confidence**: MEDIUM (multi-manufacturer complexity)

### 3. Mama Elephant Direct (mamaelephant.com invoices)
**Invoice Characteristics:**
- **Header**: "Mama Elephant"
- **Format**: Simple product names only
- **Products**: Only Mama Elephant products
- **Currency**: USD pricing
- **Description Format**: "bakery bears cc", "little agenda bakery" (no SKUs)

**Processing Strategy:**
- **Supplier Detection**: Company name in header
- **Product Parsing**: Product names only, no SKUs available
- **Scraping Target**: mamaelephant.com only
- **Currency**: USD pricing
- **Confidence**: LOW-MEDIUM (name-only matching is challenging)

### **Universal Product Processing Pipeline**

```
1. Invoice Upload → 
2. Supplier Detection (from invoice header) →
3. Product Line Parsing (supplier-specific format) →
4. Manufacturer Identification (from SKU prefix or supplier) →
5. Multi-Target Scraping (manufacturer-specific websites) →
6. Data Consolidation → 
7. Gambio Export
```

### **Database Schema for Two-Level Tracking**

```sql
-- Products table enhanced for supplier/manufacturer distinction
CREATE TABLE products (
    -- Invoice/Purchase Information (who you bought from)
    supplier_id UUID REFERENCES suppliers(id),           -- Craftlines
    supplier_sku VARCHAR(100),                           -- Craftlines' internal SKU
    supplier_price_usd DECIMAL(10,2),                    -- What Craftlines charged (USD)
    supplier_price_eur DECIMAL(10,2),                    -- What Craftlines charged (EUR)
    
    -- Product/Manufacturer Information (who made it)
    manufacturer VARCHAR(100),                           -- 'lawnfawn', 'mama-elephant'
    manufacturer_sku VARCHAR(100),                       -- 'LF1142', 'ME5678'
    manufacturer_website VARCHAR(255),                   -- For scraping target
    
    -- Product Details (from scraping manufacturer website)
    product_name VARCHAR(500),                           -- Actual product name
    category VARCHAR(255),                               -- Product category
    scraped_url VARCHAR(1000),                          -- Manufacturer product page
    -- ... rest of fields
);
```

### Universal Matching Confidence Algorithms

**Craftlines:**
```
1. Try direct code lookup on website
2. Search with product code
3. Fallback to name-based search
4. Confidence: Code match (95%), Search result (80%), Name match (60%)
```

**Lawn Fawn:**
```
1. Construct URL from SKU pattern
2. Search with SKU if URL fails
3. Category browse + name match
4. Confidence: SKU URL (90%), SKU search (85%), Name match (70%)
```

**Mama Elephant:**
```
1. Website search with exact product name
2. Fuzzy name matching with similarity scoring
3. Category browsing with name variants
4. Manual review for low confidence matches
5. Confidence: Exact name (75%), Fuzzy match (40-70%), Manual (100%)
```

## Key Features

### Universal Core Features
1. **Supplier Management**: Configure and manage any number of suppliers through admin interface
2. **Universal File Upload**: Support CSV, Excel, PDF, and manual entry with auto-detection
3. **Flexible Product Matching**: Handle any identifier type (SKUs, names, codes, EANs) with confidence scoring
4. **Universal Review System**: Unified interface for reviewing uncertain matches, images, and duplicates
5. **Cross-Supplier Duplicate Detection**: Identify and resolve duplicates across all suppliers
6. **Product Database**: Centralized, supplier-agnostic product information storage
7. **Web Scraping Engine**: Automated, supplier-specific product detail extraction
8. **Category Management**: Dual category assignment (IMPORT + supplier-specific) for all suppliers
9. **URL Generation**: SEO-friendly product URLs for multi-domain setup
10. **High-Quality Image Processing**: Download, validate (≥1000px), convert to JPEG with manual upload fallback
11. **Translation Engine**: English to German translation with context awareness
12. **SEO Generator**: Automatic keyword and meta tag generation
13. **Universal Export Engine**: Gambio-compatible CSV + image package + URLs regardless of source
14. **Progress Tracking**: Real-time processing status with detailed logging
15. **Quality Assurance**: Comprehensive validation and warning system

### Review & Validation Features
1. **Product Match Review**: Flag and review uncertain product matches with confidence scoring
2. **Image Review System**: Handle missing or poor-quality images with manual upload capability
3. **Duplicate Resolution**: Smart duplicate detection with user-guided resolution
4. **Bulk Review Operations**: Efficiently review multiple items with batch actions
5. **Manual Override System**: Always allow manual URL entry and data correction
6. **Review Queue Management**: Prioritized queue system for efficient workflow
7. **User Feedback Loop**: Learn from user corrections to improve future matching

### Supplier Integration Features
1. **Pluggable Architecture**: Easy addition of new suppliers without code changes
2. **Configuration-Driven Setup**: Define suppliers through configuration, not hardcoding
3. **Multiple Fallback Strategies**: Each supplier supports multiple matching methods
4. **Confidence Scoring**: Universal system for rating match quality across all suppliers
5. **Supplier-Specific Optimizations**: Tailored scraping strategies per supplier
6. **Cross-Supplier Analytics**: Compare performance and quality across suppliers

### Advanced Features (Current System)
1. **Batch Processing**: Handle up to 100 products per batch with progress tracking
2. **Real-Time Duplicate Detection**: Prevent duplicates during processing
3. **Multi-Format Support**: Process various input formats seamlessly
4. **Quality Validation**: Comprehensive image and data quality checks
5. **Error Recovery**: Robust error handling with retry mechanisms
6. **Audit Trail**: Complete logging of all processing steps and user actions

### Future Enhancement Features
1. **Price Monitoring**: Track supplier price changes over time
2. **Inventory Sync**: Real-time stock level updates from suppliers
3. **Multi-language Support**: Additional language pairs beyond German
4. **Advanced Analytics**: Detailed reporting on processing efficiency and quality
5. **API Integration**: Direct supplier API connections where available
6. **Machine Learning**: Improve matching accuracy through ML algorithms
7. **Competitor Analysis**: Price and feature comparison across suppliers
8. **Automated Categorization**: AI-powered category assignment

## Gambio Integration

### CSV + Images Import Approach (Gambio 4.4.0.4)
Based on comprehensive analysis and Gambio documentation, the system uses CSV + Images import:

#### **Core CSV Import Requirements:**
- **Format**: UTF-8 without BOM encoding
- **Delimiter**: Pipe symbol `|` (recommended)
- **Text Qualifier**: Double quotes `"`
- **Required Fields**: XTSOL, p_model, p_shortdesc.de, p_shortdesc.en (even if just spaces)
- **Image References**: Exact JPEG filenames in CSV, actual files uploaded separately

#### **Enhanced Gambio CSV Field Mapping:**
```
XTSOL: "XTSOL" (required control character)
p_model: Internal SKU (e.g., LF-STAMP-001)
p_name.de: German translated product name
p_desc.de: German translated description
p_shortdesc.de: German short description (required field)
p_shortdesc.en: English short description (required field)
p_cat.de: "Neu: [Manufacturer] > PD-neu"
p_priceNoTax: EUR net price from supplier
p_tax: Configurable tax class ID (multi-country support)
p_image: Main JPEG filename (e.g., LF-STAMP-001_main_01.jpeg)
p_image.1: Additional JPEG filename
p_image.2: Additional JPEG filename
p_image.3: Additional JPEG filename
p_status: 1 (active product)
rewrite_url.de: SEO-friendly URL slug
p_img_alt_text.de: German alt text for main image
p_img_alt_text.1.de: German alt text for additional images
```

#### **Multi-Country Tax Class System:**
- **Tax Classes Table**: Support for AT, DE, and other countries
- **Configurable VAT Rates**: 20% (AT), 19% (DE), etc.
- **Dynamic Assignment**: Products assigned appropriate tax class based on configuration
- **Admin Interface**: Manage tax class mappings per country

#### **Enhanced Image Processing & Upload:**
- **Format**: All images converted to JPEG for Gambio compatibility
- **Quality**: Minimum 1000px on longest edge (with quality warnings for substandard images)
- **Naming**: Standardized {SKU}_{type}_{sequence}.jpeg format
- **Upload Location**: `/images/product_images/original_images/` via FTP
- **Batch Processing**: Manual trigger in Gambio admin (Settings > Layout & Design > Image Processing)
- **Generated Sizes**: Gambio automatically creates thumbnails, info images, popup images, mobile versions
- **Alt Text**: SEO-optimized German descriptions for all images

#### **Refined Category Structure:**
- **Primary Category**: "Neu: [Manufacturer]" (e.g., "Neu: LawnFawn", "Neu: Craftlines", "Neu: Mama Elephant")
- **Secondary Category**: "PD-neu" (all products also assigned here)
- **CSV Format**: `p_cat.de: "Neu: LawnFawn > PD-neu"`
- **Assumption**: Categories pre-exist in Gambio system
- **URL Integration**: Categories used for SEO-friendly URL generation
- **Hierarchy**: Support for nested category structures

#### **Export Package Structure:**
```
/exports/{batch_date}/
├── gambio_import.csv (Gambio 4.4.0.4 format)
├── /images/
│   └── /product_images/
│       └── /original_images/
│           ├── LF-STAMP-001_main_01.jpeg
│           ├── LF-STAMP-001_detail_01.jpeg
│           ├── CL-DIES-042_main_01.jpeg
│           └── [all optimized JPEG images]
├── import_instructions.md (step-by-step Gambio admin guide)
├── batch_processing_guide.md (image processing instructions)
├── validation_checklist.md (import validation steps)
└── export_summary.json (batch processing summary)
```

#### **Post-Import Process:**
1. **CSV Import**: Upload and import CSV file in Gambio admin
2. **Image Upload**: FTP upload all JPEG images to correct directory
3. **Batch Processing**: Manual trigger in Gambio admin to generate image variants
4. **Validation**: Verify products, categories, images, and pricing
5. **Quality Check**: Review imported products for completeness

## Risk Mitigation

### Technical Risks
- **Rate Limiting**: Implement respectful scraping with delays
- **Website Changes**: Monitor for structural changes
- **Translation Quality**: Implement review workflow
- **Image Quality**: Validate image dimensions and file sizes

### Business Risks
- **Supplier Relations**: Ensure scraping complies with terms
- **Data Accuracy**: Implement validation and review processes
- **SEO Impact**: Monitor translation quality for search performance

## Success Metrics

### Efficiency Gains
- Time reduction: From hours to minutes per product batch
- Error reduction: Automated validation vs manual entry
- Consistency: Standardized SEO and naming

### Quality Metrics
- Translation accuracy: Review and approval workflow
- Image quality: Automated validation
- SEO performance: Keyword relevance scoring

## Phases

### Phase 1: Foundation
- Database setup and core models
- Basic file upload and CSV parsing
- Simple web scraping with Firecrawl

### Phase 2: Core Features
- Product enrichment pipeline
- Image downloading and processing
- Translation integration

### Phase 3: Export & Integration
- Gambio CSV generation
- Image organization and packaging
- UI polish and error handling

### Phase 4: Optimization
- Performance optimization
- Advanced features
- Testing and deployment

## Conclusion
This system will transform the product import process from a manual, time-consuming task into an automated, scalable solution that maintains high quality standards while dramatically reducing operational overhead.
