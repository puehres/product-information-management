## FEATURE:

MVP Database Design (Supabase) - Simplified - Comprehensive Supabase PostgreSQL database setup for the Universal Product Automation System MVP including Supabase project configuration in eu-central-1 (Frankfurt) region, simplified database schema with 4 core tables (suppliers, upload_batches, products, images), Supabase client integration, database relationships and constraints, Lawn Fawn supplier seed data, database utility functions, performance indexing, and local development configuration with cloud database.

## EXAMPLES:

[Reference examples in the `examples/` folder - will include:]
- Supabase project setup configuration and environment templates
- Database schema SQL scripts for MVP tables (suppliers, upload_batches, products, images)
- Supabase client connection examples for Python and TypeScript
- Sample seed data for Lawn Fawn supplier configuration
- Database utility functions for CRUD operations
- Migration scripts for schema updates and rollbacks
- Environment variable templates for development and production
- Connection string examples for different environments
- Database indexing strategies for performance optimization
- Backup and recovery procedures for Supabase projects

## DOCUMENTATION:

### Supabase Setup & Configuration
- **Supabase Dashboard**: https://supabase.com/dashboard - Project creation and management interface
- **Supabase CLI**: https://supabase.com/docs/guides/cli - Command-line tools for local development
- **Region Selection**: https://supabase.com/docs/guides/platform/regions - eu-central-1 (Frankfurt) for German users
- **Project Settings**: https://supabase.com/docs/guides/getting-started/architecture - Database configuration and limits
- **API Keys**: https://supabase.com/docs/guides/api/api-keys - Authentication and service keys management

### Database Schema Design & PostgreSQL
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/current/ - Core database functionality
- **Supabase Database**: https://supabase.com/docs/guides/database/overview - PostgreSQL with extensions
- **Schema Design**: https://supabase.com/docs/guides/database/tables - Table creation and relationships
- **Constraints**: https://www.postgresql.org/docs/current/ddl-constraints.html - Foreign keys and data integrity
- **Indexing**: https://www.postgresql.org/docs/current/indexes.html - Performance optimization strategies

### Supabase Client Integration
- **Python Client**: https://supabase.com/docs/reference/python/introduction - supabase-py SDK
- **TypeScript Client**: https://supabase.com/docs/reference/javascript/introduction - JavaScript/TypeScript SDK
- **Authentication**: https://supabase.com/docs/guides/auth/overview - Row Level Security and auth
- **Real-time**: https://supabase.com/docs/guides/realtime/overview - Live database updates
- **Storage**: https://supabase.com/docs/guides/storage/overview - File storage integration

### Database Migrations & Version Control
- **Supabase Migrations**: https://supabase.com/docs/guides/cli/local-development - Local development workflow
- **SQL Migrations**: https://supabase.com/docs/guides/database/migrations - Schema version control
- **Alembic Integration**: https://alembic.sqlalchemy.org/en/latest/ - SQLAlchemy migrations with PostgreSQL
- **Backup Strategies**: https://supabase.com/docs/guides/platform/backups - Automated and manual backups
- **Recovery Procedures**: https://supabase.com/docs/guides/platform/backups#point-in-time-recovery - Point-in-time recovery

### Environment Configuration & Security
- **Environment Variables**: https://supabase.com/docs/guides/getting-started/architecture#api-url-and-keys - Secure configuration
- **Connection Strings**: https://supabase.com/docs/guides/database/connecting-to-postgres - Direct PostgreSQL access
- **Row Level Security**: https://supabase.com/docs/guides/auth/row-level-security - Data access control
- **API Security**: https://supabase.com/docs/guides/api/securing-your-api - Rate limiting and protection
- **SSL Configuration**: https://supabase.com/docs/guides/database/connecting-to-postgres#ssl-modes - Secure connections

### Performance Optimization & Monitoring
- **Database Performance**: https://supabase.com/docs/guides/database/performance - Query optimization
- **Connection Pooling**: https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler - PgBouncer integration
- **Monitoring**: https://supabase.com/docs/guides/platform/logs - Database logs and metrics
- **Query Analysis**: https://www.postgresql.org/docs/current/using-explain.html - EXPLAIN and query planning
- **Index Optimization**: https://www.postgresql.org/docs/current/indexes-types.html - Index types and strategies

## OTHER CONSIDERATIONS:

### MVP Database Schema (Simplified Approach)

#### Core Tables Overview
The MVP focuses on 4 essential tables to validate the core Lawn Fawn → Gambio workflow:
- **suppliers**: Basic supplier information and configuration
- **upload_batches**: Track invoice/CSV uploads and processing status
- **products**: Core product data with Gambio export fields
- **images**: Image metadata and S3 URLs for processed images

#### Suppliers Table
```sql
CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(10) NOT NULL UNIQUE,
    website_url VARCHAR(255),
    identifier_type VARCHAR(50) DEFAULT 'sku',
    scraping_config JSONB,
    search_url_template VARCHAR(500),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for performance
CREATE INDEX idx_suppliers_code ON suppliers(code);
CREATE INDEX idx_suppliers_active ON suppliers(active);

-- Insert Lawn Fawn seed data
INSERT INTO suppliers (name, code, website_url, identifier_type, search_url_template) VALUES
('Lawn Fawn', 'LF', 'https://www.lawnfawn.com', 'sku', 'https://www.lawnfawn.com/search?options%5Bprefix%5D=last&q={sku}&filter.p.product_type=');
```

#### Upload_Batches Table
```sql
CREATE TABLE upload_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL CHECK (file_type IN ('pdf', 'csv', 'xlsx', 'manual')),
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'processing', 'completed', 'failed', 'review_required')),
    processing_notes JSONB,
    invoice_number VARCHAR(100),
    invoice_date DATE,
    currency_code VARCHAR(3) DEFAULT 'USD',
    exchange_rate DECIMAL(10,4) DEFAULT 0.85,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for performance
CREATE INDEX idx_upload_batches_supplier ON upload_batches(supplier_id);
CREATE INDEX idx_upload_batches_status ON upload_batches(status);
CREATE INDEX idx_upload_batches_date ON upload_batches(uploaded_at);
```

#### Products Table
```sql
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    batch_id UUID NOT NULL REFERENCES upload_batches(id) ON DELETE CASCADE,
    supplier_sku VARCHAR(100) NOT NULL,
    internal_sku VARCHAR(100) UNIQUE,
    original_name VARCHAR(500),
    german_name VARCHAR(500),
    original_description TEXT,
    german_description TEXT,
    supplier_price_usd DECIMAL(10,2),
    supplier_price_eur DECIMAL(10,2),
    quantity INTEGER DEFAULT 1,
    category VARCHAR(200),
    gambio_category VARCHAR(200) DEFAULT 'Neu: LawnFawn > PD-neu',
    tax_class_id INTEGER DEFAULT 1,
    seo_keywords TEXT,
    meta_title VARCHAR(200),
    meta_description VARCHAR(300),
    gambio_url_slug VARCHAR(200),
    product_url VARCHAR(500),
    scraping_confidence INTEGER DEFAULT 0 CHECK (scraping_confidence >= 0 AND scraping_confidence <= 100),
    review_required BOOLEAN DEFAULT false,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'processing', 'scraped', 'translated', 'ready', 'exported', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_products_supplier ON products(supplier_id);
CREATE INDEX idx_products_batch ON products(batch_id);
CREATE INDEX idx_products_sku ON products(supplier_sku);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_review ON products(review_required);
CREATE UNIQUE INDEX idx_products_internal_sku ON products(internal_sku) WHERE internal_sku IS NOT NULL;
```

#### Images Table
```sql
CREATE TABLE images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_url VARCHAR(500),
    s3_url VARCHAR(500),
    alt_text VARCHAR(200),
    image_type VARCHAR(20) DEFAULT 'main' CHECK (image_type IN ('main', 'additional', 'detail', 'manual_upload')),
    sort_order INTEGER DEFAULT 1,
    file_size INTEGER,
    width INTEGER,
    height INTEGER,
    longest_edge INTEGER,
    meets_quality_standard BOOLEAN DEFAULT false,
    processing_status VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_images_product ON images(product_id);
CREATE INDEX idx_images_type ON images(image_type);
CREATE INDEX idx_images_status ON images(processing_status);
CREATE INDEX idx_images_quality ON images(meets_quality_standard);
```

### Supabase Configuration Details

#### Project Setup (eu-central-1 Frankfurt)
```bash
# Create new Supabase project
# Region: Europe (Central) - eu-central-1
# Database: PostgreSQL 15
# Pricing: Free tier (500MB database, 2GB bandwidth/month)

# Project Configuration
Project Name: product-automation-mvp
Organization: stempelwunderwelt
Region: Europe (Central)
Database Password: [secure-password]
```

#### Environment Variables Configuration
```env
# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-key-here

# Direct PostgreSQL Connection (for migrations and admin tasks)
SUPABASE_DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres

# Redis Configuration (Upstash free tier)
REDIS_URL=rediss://default:[password]@[region].upstash.io:6380

# Tax Configuration (MVP - hardcoded)
GAMBIO_DEFAULT_TAX_CLASS_ID=1

# Currency Configuration
DEFAULT_CURRENCY_FROM=USD
DEFAULT_CURRENCY_TO=EUR
DEFAULT_EXCHANGE_RATE=0.85

# Development Settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
```

#### Python Supabase Client Setup
```python
import os
from supabase import create_client, Client
from typing import Optional

class SupabaseManager:
    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL")
        self.key = os.environ.get("SUPABASE_SERVICE_KEY")  # Use service key for backend
        self.client: Client = create_client(self.url, self.key)
    
    def get_client(self) -> Client:
        """Get Supabase client instance."""
        return self.client
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            result = self.client.table('suppliers').select('count').execute()
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

# Usage example
supabase_manager = SupabaseManager()
supabase = supabase_manager.get_client()

# Test connection
if supabase_manager.test_connection():
    print("✅ Supabase connection successful")
else:
    print("❌ Supabase connection failed")
```

#### TypeScript Supabase Client Setup
```typescript
import { createClient, SupabaseClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase: SupabaseClient = createClient(supabaseUrl, supabaseAnonKey)

// Database types (auto-generated)
export interface Database {
  public: {
    Tables: {
      suppliers: {
        Row: {
          id: string
          name: string
          code: string
          website_url: string | null
          identifier_type: string
          scraping_config: any | null
          search_url_template: string | null
          active: boolean
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          name: string
          code: string
          website_url?: string | null
          identifier_type?: string
          scraping_config?: any | null
          search_url_template?: string | null
          active?: boolean
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          name?: string
          code?: string
          website_url?: string | null
          identifier_type?: string
          scraping_config?: any | null
          search_url_template?: string | null
          active?: boolean
          created_at?: string
          updated_at?: string
        }
      }
      // ... other table types
    }
  }
}

// Usage example
export async function getSuppliers() {
  const { data, error } = await supabase
    .from('suppliers')
    .select('*')
    .eq('active', true)
  
  if (error) throw error
  return data
}
```

### Tax Handling Strategy (MVP Simplification)

#### Hardcoded Tax Class Approach
```python
# MVP Tax Configuration
GAMBIO_TAX_CLASSES = {
    'AT': {'id': 1, 'rate': 20.0, 'description': 'Austria Standard VAT'},
    'DE': {'id': 2, 'rate': 19.0, 'description': 'Germany Standard VAT'},
    'DEFAULT': {'id': 1, 'rate': 20.0, 'description': 'Default VAT'}
}

def get_tax_class_id(country_code: str = 'AT') -> int:
    """Get tax class ID for MVP (hardcoded approach)."""
    return GAMBIO_TAX_CLASSES.get(country_code, GAMBIO_TAX_CLASSES['DEFAULT'])['id']

def calculate_price_with_tax(net_price: float, country_code: str = 'AT') -> float:
    """Calculate gross price including VAT."""
    tax_info = GAMBIO_TAX_CLASSES.get(country_code, GAMBIO_TAX_CLASSES['DEFAULT'])
    return round(net_price * (1 + tax_info['rate'] / 100), 2)
```

#### Future Tax Classes Table (Phase 2)
```sql
-- Future enhancement: Full tax classes table
CREATE TABLE tax_classes (
    id SERIAL PRIMARY KEY,
    country_code VARCHAR(2) NOT NULL,
    tax_rate DECIMAL(5,2) NOT NULL,
    gambio_tax_class_id INTEGER NOT NULL,
    description VARCHAR(100),
    is_default BOOLEAN DEFAULT false,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for tax classes
CREATE INDEX idx_tax_classes_country ON tax_classes(country_code);
CREATE INDEX idx_tax_classes_default ON tax_classes(is_default);
```

### Database Utility Functions

#### Core CRUD Operations
```python
from typing import List, Dict, Optional, Any
from supabase import Client

class DatabaseManager:
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
    
    # Suppliers
    async def create_supplier(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new supplier."""
        result = self.client.table('suppliers').insert(supplier_data).execute()
        return result.data[0] if result.data else None
    
    async def get_supplier_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get supplier by code."""
        result = self.client.table('suppliers').select('*').eq('code', code).single().execute()
        return result.data if result.data else None
    
    # Upload Batches
    async def create_upload_batch(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new upload batch."""
        result = self.client.table('upload_batches').insert(batch_data).execute()
        return result.data[0] if result.data else None
    
    async def update_batch_status(self, batch_id: str, status: str, notes: Dict[str, Any] = None) -> bool:
        """Update batch processing status."""
        update_data = {'status': status, 'updated_at': 'NOW()'}
        if notes:
            update_data['processing_notes'] = notes
        
        result = self.client.table('upload_batches').update(update_data).eq('id', batch_id).execute()
        return len(result.data) > 0
    
    # Products
    async def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product."""
        result = self.client.table('products').insert(product_data).execute()
        return result.data[0] if result.data else None
    
    async def get_products_by_batch(self, batch_id: str) -> List[Dict[str, Any]]:
        """Get all products in a batch."""
        result = self.client.table('products').select('*').eq('batch_id', batch_id).execute()
        return result.data or []
    
    async def update_product_status(self, product_id: str, status: str) -> bool:
        """Update product status."""
        result = self.client.table('products').update({
            'status': status,
            'updated_at': 'NOW()'
        }).eq('id', product_id).execute()
        return len(result.data) > 0
    
    # Images
    async def create_image(self, image_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new image record."""
        result = self.client.table('images').insert(image_data).execute()
        return result.data[0] if result.data else None
    
    async def get_product_images(self, product_id: str) -> List[Dict[str, Any]]:
        """Get all images for a product."""
        result = self.client.table('images').select('*').eq('product_id', product_id).order('sort_order').execute()
        return result.data or []
    
    # Batch Operations
    async def get_batch_summary(self, batch_id: str) -> Dict[str, Any]:
        """Get comprehensive batch summary."""
        # Get batch info
        batch_result = self.client.table('upload_batches').select('*').eq('id', batch_id).single().execute()
        batch = batch_result.data
        
        # Get product counts by status
        products_result = self.client.table('products').select('status').eq('batch_id', batch_id).execute()
        products = products_result.data or []
        
        status_counts = {}
        for product in products:
            status = product['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'batch': batch,
            'total_products': len(products),
            'status_breakdown': status_counts
        }
```

### Performance Optimization

#### Database Indexing Strategy
```sql
-- Core performance indexes (already included in table definitions)

-- Additional composite indexes for common queries
CREATE INDEX idx_products_batch_status ON products(batch_id, status);
CREATE INDEX idx_products_supplier_status ON products(supplier_id, status);
CREATE INDEX idx_images_product_type ON images(product_id, image_type);

-- Partial indexes for specific conditions
CREATE INDEX idx_products_review_required ON products(id) WHERE review_required = true;
CREATE INDEX idx_images_quality_failed ON images(id) WHERE meets_quality_standard = false;

-- Text search indexes for product names (if needed)
CREATE INDEX idx_products_name_search ON products USING gin(to_tsvector('english', original_name));
CREATE INDEX idx_products_german_name_search ON products USING gin(to_tsvector('german', german_name));
```

#### Query Optimization Examples
```sql
-- Efficient batch processing query
SELECT 
    p.id,
    p.supplier_sku,
    p.original_name,
    p.status,
    COUNT(i.id) as image_count,
    COUNT(CASE WHEN i.meets_quality_standard THEN 1 END) as quality_images
FROM products p
LEFT JOIN images i ON p.id = i.product_id
WHERE p.batch_id = $1
GROUP BY p.id, p.supplier_sku, p.original_name, p.status
ORDER BY p.created_at;

-- Products requiring review
SELECT 
    p.*,
    s.name as supplier_name,
    ub.filename as batch_filename
FROM products p
JOIN suppliers s ON p.supplier_id = s.id
JOIN upload_batches ub ON p.batch_id = ub.id
WHERE p.review_required = true
ORDER BY p.created_at DESC;
```

### Migration Strategy

#### Initial Schema Migration
```sql
-- migrations/001_initial_schema.sql
-- Create all MVP tables with proper constraints and indexes
-- (Include all table creation SQL from above)

-- migrations/002_seed_data.sql
-- Insert initial supplier data
INSERT INTO suppliers (name, code, website_url, identifier_type, search_url_template) VALUES
('Lawn Fawn', 'LF', 'https://www.lawnfawn.com', 'sku', 'https://www.lawnfawn.com/search?options%5Bprefix%5D=last&q={sku}&filter.p.product_type=');

-- migrations/003_performance_indexes.sql
-- Add additional performance indexes
-- (Include additional index creation SQL from above)
```

#### Migration Management with Supabase CLI
```bash
# Initialize Supabase locally
supabase init

# Start local development
supabase start

# Create new migration
supabase migration new initial_schema

# Apply migrations to remote
supabase db push

# Generate TypeScript types
supabase gen types typescript --local > types/database.ts
```

### Backup and Recovery Procedures

#### Automated Backups (Supabase)
- **Point-in-Time Recovery**: Available for Pro tier (7 days retention)
- **Daily Backups**: Automatic daily backups included in free tier
- **Manual Backups**: On-demand backup creation via dashboard
- **Export Options**: CSV, SQL dump, or full database export

#### Manual Backup Procedures
```bash
# Export specific tables
pg_dump -h db.[project-ref].supabase.co -U postgres -t suppliers -t upload_batches -t products -t images --data-only --column-inserts > backup_data.sql

# Full database backup
pg_dump -h db.[project-ref].supabase.co -U postgres [database-name] > full_backup.sql

# Restore from backup
psql -h db.[project-ref].supabase.co -U postgres [database-name] < backup_data.sql
```

### Development vs Production Configuration

#### Development Setup
```python
# Development configuration
DEVELOPMENT_CONFIG = {
    'supabase_url': 'https://dev-project.supabase.co',
    'database_url': 'postgresql://postgres:password@localhost:54322/postgres',  # Local Supabase
    'debug': True,
    'log_level': 'DEBUG',
    'auto_migrate': True,
    'seed_data': True
}
```

#### Production Setup
```python
# Production configuration
PRODUCTION_CONFIG = {
    'supabase_url': 'https://prod-project.supabase.co',
    'database_url': 'postgresql://postgres:password@db.prod-project.supabase.co:5432/postgres',
    'debug': False,
    'log_level': 'INFO',
    'auto_migrate': False,
    'seed_data': False,
    'connection_pool_size': 20,
    'ssl_mode': 'require'
}
```

### Security Considerations

#### Row Level Security (RLS)
```sql
-- Enable RLS on all tables
ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY;
ALTER TABLE upload_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE images ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (for future multi-user support)
CREATE POLICY "Users can view all suppliers" ON suppliers FOR SELECT USING (true);
CREATE POLICY "Users can manage their own batches" ON upload_batches FOR ALL USING (true);  -- Simplified for MVP
CREATE POLICY "Users can manage all products" ON products FOR ALL USING (true);  -- Simplified for MVP
CREATE POLICY "Users can manage all images" ON images FOR ALL USING (true);  -- Simplified for MVP
```

#### API Security
```python
# Secure API key management
import os
from functools import wraps

def require_service_key(f):
    """Decorator to require service key for sensitive operations."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verify service key is being used for admin operations
        return f(*args, **kwargs)
    return decorated_function

# Environment-specific key usage
def get_supabase_client(admin: bool = False):
    """Get appropriate Supabase client based on operation type."""
    if admin:
        key = os.environ.get("SUPABASE_SERVICE_KEY")
    else:
        key = os.environ.get("SUPABASE_ANON_KEY")
    
    return create_client(os.environ.get("SUPABASE_URL"), key)
```

### Cost Optimization & Scaling

#### Free Tier Limits (Supabase)
- **Database**: 500MB storage (sufficient for MVP with ~10,000 products)
- **Bandwidth**: 2GB/month data transfer
- **API Requests**: 50,000 monthly active users
- **Storage**: 1GB file storage (alternative to S3 if needed)
- **Edge Functions**: 500,000 invocations/month

#### Scaling Considerations
```python
# Monitor database size
def check_database_usage():
    """Monitor database size and usage."""
    query = """
    SELECT 
        schemaname,
        tablename,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
    FROM pg_tables 
    WHERE schemaname = 'public'
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
    """
    # Execute query and return results

# Cleanup old data
def cleanup_old_batches(days_old: int = 30):
    """Clean up old upload batches and associated data."""
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    # Delete old completed batches and cascade to products/images
    result = supabase.table('upload_batches').delete().lt('completed_at', cutoff_date.isoformat()).execute()
    return len(result.data)
```

### Integration with Universal System Architecture

#### Preparation for Phase 2 Expansion
```sql
-- Future tables (commented out for MVP)
/*
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    parent_id UUID REFERENCES categories(id),
    supplier_id UUID REFERENCES suppliers(id),
    gambio_category_id INTEGER,
    is_import_category BOOLEAN DEFAULT false,
    category_path TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE product_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES upload_batches(id),
    supplier_id UUID NOT NULL REFERENCES suppliers(id),
    original_identifier VARCHAR(200),
    normalized_identifier VARCHAR(200),
    detected_url VARCHAR(500),
    confidence_score INTEGER CHECK (confidence_score >= 0 AND confidence_score <= 100),
    match_method VARCHAR(50),
    review_status VARCHAR(20) DEFAULT 'pending',
    manual_url VARCHAR(500),
    review_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE
);
*/
```

#### Database Evolution Path
1. **MVP Phase**: 4 core tables with essential functionality
2. **Phase 2**: Add product_matches, categories, review_queue tables
3. **Phase 3**: Add duplicate_groups, tax_classes, audit_logs tables
4. **Production**: Full universal schema with all advanced features

### Success Criteria for Task 2

#### Database Setup Validation
- [ ] **Supabase Project**: Created in eu-central-1 (Frankfurt) region
- [ ] **Schema Creation**: All 4 MVP tables created with proper constraints
- [ ] **Indexes**: Performance indexes created and validated
- [ ] **Seed Data**: Lawn Fawn supplier data inserted successfully
- [ ] **Connection Testing**: Python and TypeScript clients connecting successfully
- [ ] **Environment Variables**: All required environment variables configured
- [ ] **Migration System**: Basic migration workflow established
- [ ] **Backup Strategy**: Automated backup configuration verified

#### Performance Benchmarks
- [ ] **Connection Time**: Database connections established in under 2 seconds
- [ ] **Query Performance**: Basic CRUD operations complete in under 100ms
- [ ] **Batch Operations**: 50-product batch queries complete in under 5 seconds
- [ ] **Index Effectiveness**: All common queries use appropriate indexes
- [ ] **Storage Efficiency**: Database size optimized for MVP scale

#### Integration Readiness
- [ ] **Python Integration**: Supabase client working with FastAPI backend
- [ ] **TypeScript Integration**: Supabase client working with Next.js frontend
- [ ] **Error Handling**: Database errors properly caught and handled
- [ ] **Transaction Support**: Multi-table operations use proper transactions
- [ ] **Real-time Features**: Basic real-time subscriptions working (if needed)

#### Security & Compliance
- [ ] **SSL Connections**: All connections use SSL/TLS encryption
- [ ] **
