-- Migration 007: Product enrichment and scraping attempts tracking
-- This migration adds comprehensive product enrichment capabilities with audit trails

-- Create scraping_attempts table for complete audit trail
CREATE TABLE IF NOT EXISTS scraping_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    search_url VARCHAR(1000),
    method VARCHAR(50) NOT NULL, -- 'search_first_result', 'direct_url', 'fallback'
    status VARCHAR(20) NOT NULL, -- 'success', 'failed', 'partial'
    confidence_score INTEGER DEFAULT 0 CHECK (confidence_score >= 0 AND confidence_score <= 100),
    firecrawl_response JSONB,
    error_message TEXT,
    credits_used INTEGER DEFAULT 0,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_scraping_attempts_product_id ON scraping_attempts(product_id);
CREATE INDEX IF NOT EXISTS idx_scraping_attempts_status ON scraping_attempts(status);
CREATE INDEX IF NOT EXISTS idx_scraping_attempts_method ON scraping_attempts(method);
CREATE INDEX IF NOT EXISTS idx_scraping_attempts_created_at ON scraping_attempts(created_at);
CREATE INDEX IF NOT EXISTS idx_scraping_attempts_confidence ON scraping_attempts(confidence_score);

-- Add unique constraint for attempt numbering per product
CREATE UNIQUE INDEX IF NOT EXISTS idx_scraping_attempts_product_attempt 
ON scraping_attempts(product_id, attempt_number);

-- Add trigger to auto-increment attempt_number
CREATE OR REPLACE FUNCTION set_scraping_attempt_number()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.attempt_number IS NULL OR NEW.attempt_number = 1 THEN
        SELECT COALESCE(MAX(attempt_number), 0) + 1
        INTO NEW.attempt_number
        FROM scraping_attempts
        WHERE product_id = NEW.product_id;
    END IF;
    
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_scraping_attempt_number
    BEFORE INSERT ON scraping_attempts
    FOR EACH ROW
    EXECUTE FUNCTION set_scraping_attempt_number();

-- Update products table to link to successful scraping attempt
ALTER TABLE products ADD COLUMN IF NOT EXISTS successful_scraping_attempt_id UUID REFERENCES scraping_attempts(id);
ALTER TABLE products ADD COLUMN IF NOT EXISTS enrichment_status VARCHAR(20) DEFAULT 'pending'; -- 'pending', 'processing', 'completed', 'failed'
ALTER TABLE products ADD COLUMN IF NOT EXISTS last_enrichment_attempt TIMESTAMP WITH TIME ZONE;

-- Add indexes for new product fields
CREATE INDEX IF NOT EXISTS idx_products_enrichment_status ON products(enrichment_status);
CREATE INDEX IF NOT EXISTS idx_products_scraping_attempt ON products(successful_scraping_attempt_id);
CREATE INDEX IF NOT EXISTS idx_products_last_enrichment ON products(last_enrichment_attempt);

-- Enhanced image metadata storage for future download task
ALTER TABLE products ADD COLUMN IF NOT EXISTS scraped_images_metadata JSONB;
CREATE INDEX IF NOT EXISTS idx_products_images_metadata ON products USING GIN (scraped_images_metadata);

-- Add image download preparation fields
ALTER TABLE images ADD COLUMN IF NOT EXISTS source_url VARCHAR(1000);
ALTER TABLE images ADD COLUMN IF NOT EXISTS download_status VARCHAR(20) DEFAULT 'pending'; -- 'pending', 'downloading', 'completed', 'failed'
ALTER TABLE images ADD COLUMN IF NOT EXISTS download_attempts INTEGER DEFAULT 0;
ALTER TABLE images ADD COLUMN IF NOT EXISTS last_download_attempt TIMESTAMP WITH TIME ZONE;
ALTER TABLE images ADD COLUMN IF NOT EXISTS download_error_message TEXT;
ALTER TABLE images ADD COLUMN IF NOT EXISTS original_filename VARCHAR(255);
ALTER TABLE images ADD COLUMN IF NOT EXISTS file_size_bytes BIGINT;
ALTER TABLE images ADD COLUMN IF NOT EXISTS image_type VARCHAR(20); -- 'main', 'thumbnail', 'gallery', 'detail'
ALTER TABLE images ADD COLUMN IF NOT EXISTS quality_score INTEGER DEFAULT 50 CHECK (quality_score >= 0 AND quality_score <= 100);
ALTER TABLE images ADD COLUMN IF NOT EXISTS download_priority INTEGER DEFAULT 50 CHECK (download_priority >= 0 AND download_priority <= 100);

-- Add indexes for image download fields
CREATE INDEX IF NOT EXISTS idx_images_download_status ON images(download_status);
CREATE INDEX IF NOT EXISTS idx_images_source_url ON images(source_url);
CREATE INDEX IF NOT EXISTS idx_images_type ON images(image_type);
CREATE INDEX IF NOT EXISTS idx_images_priority ON images(download_priority);
CREATE INDEX IF NOT EXISTS idx_images_quality ON images(quality_score);

-- Update ProductStatus enum to include enrichment states
-- Note: In PostgreSQL, we need to add enum values if they don't exist
DO $$ 
BEGIN
    -- Check if the enum values already exist before adding them
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'enriching' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'product_status')) THEN
        ALTER TYPE product_status ADD VALUE 'enriching';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'enriched' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'product_status')) THEN
        ALTER TYPE product_status ADD VALUE 'enriched';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'enrichment_failed' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'product_status')) THEN
        ALTER TYPE product_status ADD VALUE 'enrichment_failed';
    END IF;
END $$;

-- Commit the enum changes before using them
COMMIT;
BEGIN;

-- Add enrichment-specific fields to products table
ALTER TABLE products ADD COLUMN IF NOT EXISTS enrichment_notes TEXT;
ALTER TABLE products ADD COLUMN IF NOT EXISTS requires_manual_review BOOLEAN DEFAULT FALSE;
ALTER TABLE products ADD COLUMN IF NOT EXISTS manual_review_reason VARCHAR(255);

-- Create view for enrichment analytics
CREATE OR REPLACE VIEW enrichment_analytics AS
SELECT 
    p.batch_id,
    p.manufacturer,
    COUNT(*) as total_products,
    COUNT(CASE WHEN p.status = 'enriched' THEN 1 END) as enriched_count,
    COUNT(CASE WHEN p.status = 'enrichment_failed' THEN 1 END) as failed_count,
    COUNT(CASE WHEN p.requires_manual_review THEN 1 END) as review_required_count,
    AVG(sa.confidence_score) as avg_confidence_score,
    AVG(sa.processing_time_ms) as avg_processing_time_ms,
    SUM(sa.credits_used) as total_credits_used
FROM products p
LEFT JOIN scraping_attempts sa ON p.successful_scraping_attempt_id = sa.id
WHERE p.status IN ('enriched', 'enrichment_failed', 'enriching')
GROUP BY p.batch_id, p.manufacturer;

-- Add updated_at trigger for scraping_attempts
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_scraping_attempts_updated_at
    BEFORE UPDATE ON scraping_attempts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
