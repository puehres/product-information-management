-- Initial database schema for Universal Product Automation System MVP
-- This migration creates the 4 core tables needed for the Lawn Fawn → Gambio workflow

-- Enable UUID extension for primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types for better data integrity (idempotent)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'file_type') THEN
        CREATE TYPE file_type AS ENUM ('pdf', 'csv', 'xlsx', 'manual');
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'batch_status') THEN
        CREATE TYPE batch_status AS ENUM ('uploaded', 'processing', 'completed', 'failed', 'review_required');
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'product_status') THEN
        CREATE TYPE product_status AS ENUM ('draft', 'processing', 'scraped', 'translated', 'ready', 'exported', 'failed');
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'image_type') THEN
        CREATE TYPE image_type AS ENUM ('main', 'additional', 'detail', 'manual_upload');
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'processing_status') THEN
        CREATE TYPE processing_status AS ENUM ('pending', 'processing', 'completed', 'failed');
    END IF;
END $$;

-- Table 1: suppliers
-- Stores supplier configuration and scraping settings
CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(10) NOT NULL UNIQUE,
    website_url VARCHAR(255),
    identifier_type VARCHAR(50) NOT NULL DEFAULT 'sku',
    scraping_config JSONB DEFAULT '{}',
    search_url_template VARCHAR(500),
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: upload_batches
-- Tracks file uploads and processing batches
CREATE TABLE IF NOT EXISTS upload_batches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id UUID NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    batch_name VARCHAR(255) NOT NULL,
    file_type file_type NOT NULL,
    file_path VARCHAR(500),
    file_size INTEGER,
    status batch_status NOT NULL DEFAULT 'uploaded',
    total_products INTEGER DEFAULT 0,
    processed_products INTEGER DEFAULT 0,
    failed_products INTEGER DEFAULT 0,
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table 3: products
-- Core product data with Gambio export fields
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_id UUID NOT NULL REFERENCES upload_batches(id) ON DELETE CASCADE,
    supplier_id UUID NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    
    -- Supplier product identifiers
    supplier_sku VARCHAR(100) NOT NULL,
    supplier_name VARCHAR(500),
    supplier_description TEXT,
    supplier_price_usd DECIMAL(10,2),
    supplier_price_eur DECIMAL(10,2),
    
    -- Scraped product data
    scraped_name VARCHAR(500),
    scraped_description TEXT,
    scraped_url VARCHAR(1000),
    scraped_images_urls TEXT[], -- Array of image URLs
    scraping_confidence INTEGER DEFAULT 0, -- 0-100 confidence score
    
    -- German translations
    german_name VARCHAR(500),
    german_description TEXT,
    german_short_description VARCHAR(255),
    
    -- Gambio export fields
    gambio_category VARCHAR(255) DEFAULT 'Neu: LawnFawn > PD-neu',
    gambio_tax_class_id INTEGER DEFAULT 1,
    gambio_model VARCHAR(100), -- Will be set to supplier_sku
    gambio_price_eur DECIMAL(10,2),
    gambio_seo_url VARCHAR(255),
    
    -- Processing status and metadata
    status product_status NOT NULL DEFAULT 'draft',
    processing_notes TEXT,
    quality_score INTEGER DEFAULT 0, -- Overall quality score 0-100
    requires_review BOOLEAN DEFAULT false,
    review_notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_supplier_sku_per_batch UNIQUE (batch_id, supplier_sku),
    CONSTRAINT valid_confidence_score CHECK (scraping_confidence >= 0 AND scraping_confidence <= 100),
    CONSTRAINT valid_quality_score CHECK (quality_score >= 0 AND quality_score <= 100)
);

-- Table 4: images
-- Image metadata and processing information
CREATE TABLE IF NOT EXISTS images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    
    -- Image source and processing
    original_url VARCHAR(1000),
    s3_key VARCHAR(500), -- S3 object key for processed image
    s3_url VARCHAR(1000), -- Full S3 URL for processed image
    filename VARCHAR(255), -- Standardized filename for Gambio
    
    -- Image properties
    image_type image_type NOT NULL DEFAULT 'main',
    sequence_number INTEGER NOT NULL DEFAULT 1,
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    format VARCHAR(10), -- jpeg, png, etc.
    
    -- Processing status
    processing_status processing_status NOT NULL DEFAULT 'pending',
    processing_error TEXT,
    quality_check_passed BOOLEAN DEFAULT false,
    quality_warnings TEXT[],
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_product_image_sequence UNIQUE (product_id, image_type, sequence_number),
    CONSTRAINT positive_dimensions CHECK (width > 0 AND height > 0),
    CONSTRAINT positive_file_size CHECK (file_size > 0)
);

-- Create indexes for performance optimization (idempotent)

-- Suppliers indexes
CREATE INDEX IF NOT EXISTS idx_suppliers_code ON suppliers(code);
CREATE INDEX IF NOT EXISTS idx_suppliers_active ON suppliers(active);

-- Upload batches indexes
CREATE INDEX IF NOT EXISTS idx_upload_batches_supplier_id ON upload_batches(supplier_id);
CREATE INDEX IF NOT EXISTS idx_upload_batches_status ON upload_batches(status);
CREATE INDEX IF NOT EXISTS idx_upload_batches_created_at ON upload_batches(created_at);

-- Products indexes
CREATE INDEX IF NOT EXISTS idx_products_batch_id ON products(batch_id);
CREATE INDEX IF NOT EXISTS idx_products_supplier_id ON products(supplier_id);
CREATE INDEX IF NOT EXISTS idx_products_supplier_sku ON products(supplier_sku);
CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);
CREATE INDEX IF NOT EXISTS idx_products_requires_review ON products(requires_review);
CREATE INDEX IF NOT EXISTS idx_products_created_at ON products(created_at);

-- Images indexes
CREATE INDEX IF NOT EXISTS idx_images_product_id ON images(product_id);
CREATE INDEX IF NOT EXISTS idx_images_processing_status ON images(processing_status);
CREATE INDEX IF NOT EXISTS idx_images_image_type ON images(image_type);

-- Create composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_products_batch_status ON products(batch_id, status);
CREATE INDEX IF NOT EXISTS idx_products_supplier_status ON products(supplier_id, status);
CREATE INDEX IF NOT EXISTS idx_images_product_type_sequence ON images(product_id, image_type, sequence_number);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to all tables (idempotent)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_suppliers_updated_at') THEN
        CREATE TRIGGER update_suppliers_updated_at BEFORE UPDATE ON suppliers
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_upload_batches_updated_at') THEN
        CREATE TRIGGER update_upload_batches_updated_at BEFORE UPDATE ON upload_batches
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_products_updated_at') THEN
        CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_images_updated_at') THEN
        CREATE TRIGGER update_images_updated_at BEFORE UPDATE ON images
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Add helpful comments for documentation
COMMENT ON TABLE suppliers IS 'Supplier configuration and scraping settings';
COMMENT ON TABLE upload_batches IS 'File upload batches and processing status';
COMMENT ON TABLE products IS 'Core product data with Gambio export fields';
COMMENT ON TABLE images IS 'Image metadata and processing information';

COMMENT ON COLUMN products.scraping_confidence IS 'Confidence score (0-100) for scraped product match';
COMMENT ON COLUMN products.quality_score IS 'Overall product quality score (0-100) for export readiness';
COMMENT ON COLUMN products.gambio_category IS 'Category path for Gambio import (default: Neu: LawnFawn > PD-neu)';
COMMENT ON COLUMN images.quality_check_passed IS 'Whether image meets minimum quality standards (>=1000px)';
