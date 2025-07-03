# Database Schema Documentation

## Overview
This document maintains the current database schema for the Universal Product Automation System.

## Current Status
- **Database**: PostgreSQL (planned)
- **ORM**: SQLAlchemy/SQLModel
- **Migrations**: Alembic (planned)
- **Current State**: Schema design phase (Task 1 completed, Task 2 pending)

## Planned Database Schema

### Core Tables

#### suppliers
```sql
CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    base_url VARCHAR(500) NOT NULL,
    scraping_config JSONB NOT NULL DEFAULT '{}',
    confidence_thresholds JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_suppliers_name ON suppliers(name);
CREATE INDEX idx_suppliers_active ON suppliers(is_active);
```

#### upload_batches
```sql
CREATE TABLE upload_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    total_records INTEGER NOT NULL DEFAULT 0,
    processed_records INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    error_log TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_upload_batches_supplier ON upload_batches(supplier_id);
CREATE INDEX idx_upload_batches_status ON upload_batches(status);
CREATE INDEX idx_upload_batches_created ON upload_batches(created_at);
```

#### products
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    batch_id UUID REFERENCES upload_batches(id),
    external_id VARCHAR(255) NOT NULL,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    price DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'EUR',
    product_url VARCHAR(1000),
    image_urls JSONB DEFAULT '[]',
    categories JSONB DEFAULT '[]',
    specifications JSONB DEFAULT '{}',
    confidence_score DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    UNIQUE(supplier_id, external_id)
);

-- Indexes
CREATE INDEX idx_products_supplier ON products(supplier_id);
CREATE INDEX idx_products_batch ON products(batch_id);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_confidence ON products(confidence_score);
CREATE INDEX idx_products_name_gin ON products USING gin(to_tsvector('english', name));
```

#### product_matches
```sql
CREATE TABLE product_matches (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    match_method VARCHAR(50) NOT NULL,
    confidence_score DECIMAL(5,2) NOT NULL,
    matched_url VARCHAR(1000),
    matched_data JSONB DEFAULT '{}',
    review_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_product_matches_product ON product_matches(product_id);
CREATE INDEX idx_product_matches_confidence ON product_matches(confidence_score);
CREATE INDEX idx_product_matches_review_status ON product_matches(review_status);
```

#### images
```sql
CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    original_url VARCHAR(1000) NOT NULL,
    local_path VARCHAR(500),
    file_name VARCHAR(255),
    file_size INTEGER,
    width INTEGER,
    height INTEGER,
    format VARCHAR(10),
    quality_score DECIMAL(3,2),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_images_product ON images(product_id);
CREATE INDEX idx_images_status ON images(status);
CREATE INDEX idx_images_quality ON images(quality_score);
```

### Review System Tables

#### image_reviews
```sql
CREATE TABLE image_reviews (
    id SERIAL PRIMARY KEY,
    image_id INTEGER NOT NULL REFERENCES images(id),
    review_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    reviewer_notes TEXT,
    manual_upload_path VARCHAR(500),
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_image_reviews_image ON image_reviews(image_id);
CREATE INDEX idx_image_reviews_status ON image_reviews(status);
CREATE INDEX idx_image_reviews_type ON image_reviews(review_type);
```

#### duplicate_groups
```sql
CREATE TABLE duplicate_groups (
    id SERIAL PRIMARY KEY,
    group_hash VARCHAR(64) NOT NULL UNIQUE,
    similarity_score DECIMAL(5,2) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    resolution_strategy VARCHAR(50),
    resolved_by VARCHAR(255),
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_duplicate_groups_hash ON duplicate_groups(group_hash);
CREATE INDEX idx_duplicate_groups_status ON duplicate_groups(status);
CREATE INDEX idx_duplicate_groups_similarity ON duplicate_groups(similarity_score);
```

#### duplicate_group_products
```sql
CREATE TABLE duplicate_group_products (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES duplicate_groups(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    is_primary BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    UNIQUE(group_id, product_id)
);

-- Indexes
CREATE INDEX idx_duplicate_group_products_group ON duplicate_group_products(group_id);
CREATE INDEX idx_duplicate_group_products_product ON duplicate_group_products(product_id);
CREATE INDEX idx_duplicate_group_products_primary ON duplicate_group_products(is_primary);
```

#### review_queue
```sql
CREATE TABLE review_queue (
    id SERIAL PRIMARY KEY,
    item_type VARCHAR(50) NOT NULL,
    item_id INTEGER NOT NULL,
    priority INTEGER NOT NULL DEFAULT 5,
    assigned_to VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_review_queue_type_id ON review_queue(item_type, item_id);
CREATE INDEX idx_review_queue_status ON review_queue(status);
CREATE INDEX idx_review_queue_priority ON review_queue(priority);
CREATE INDEX idx_review_queue_assigned ON review_queue(assigned_to);
```

## SQLModel Definitions (Planned)

### Base Models
```python
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
import uuid

class SupplierBase(SQLModel):
    name: str = Field(max_length=255, unique=True)
    base_url: str = Field(max_length=500)
    scraping_config: Dict[str, Any] = Field(default_factory=dict)
    confidence_thresholds: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = Field(default=True)

class Supplier(SupplierBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProductBase(SQLModel):
    supplier_id: int = Field(foreign_key="suppliers.id")
    batch_id: Optional[uuid.UUID] = Field(foreign_key="upload_batches.id")
    external_id: str = Field(max_length=255)
    name: str = Field(max_length=500)
    description: Optional[str] = None
    price: Optional[Decimal] = None
    currency: str = Field(default="EUR", max_length=3)
    product_url: Optional[str] = Field(max_length=1000)
    image_urls: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    specifications: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: Decimal = Field(default=Decimal('0.00'))
    status: str = Field(default="pending", max_length=50)

class Product(ProductBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

## Enums and Constants

### Status Values
```python
class ProductStatus(str, Enum):
    PENDING = "pending"
    MATCHED = "matched"
    REQUIRES_REVIEW = "requires_review"
    APPROVED = "approved"
    REJECTED = "rejected"

class MatchMethod(str, Enum):
    EXACT_CODE = "exact_code"
    EXACT_NAME = "exact_name"
    FUZZY_NAME = "fuzzy_name"
    SEARCH_RESULT = "search_result"
    BROWSE_CATEGORY = "browse_category"
    MANUAL = "manual"

class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_MANUAL = "requires_manual"
```

## Migration Strategy

### Phase 1 (Task 2)
- Create core tables: suppliers, upload_batches, products
- Set up basic relationships and indexes
- Create initial seed data for suppliers

### Phase 2 (Task 4-5)
- Add matching and review tables
- Implement duplicate detection schema
- Add review queue system

### Phase 3 (Task 6+)
- Add performance optimizations
- Implement partitioning if needed
- Add audit logging tables

## Performance Considerations

### Indexing Strategy
- Primary keys on all tables
- Foreign key indexes for relationships
- Composite indexes for common query patterns
- GIN indexes for JSONB columns and full-text search
- Partial indexes for status-based queries

### Query Optimization
- Use EXPLAIN ANALYZE for complex queries
- Implement connection pooling
- Consider read replicas for reporting
- Use materialized views for complex aggregations

## Data Integrity

### Constraints
- Foreign key constraints for referential integrity
- Check constraints for status values
- Unique constraints for business rules
- NOT NULL constraints for required fields

### Validation
- Input validation at application level
- Database-level constraints as backup
- Regular data quality checks
- Audit logging for changes

---

**Last Updated**: 2025-01-07 (Task 1 completion)
**Next Update**: Task 2 (Database implementation)
**Status**: Schema design complete, implementation pending
