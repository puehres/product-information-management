-- Migration: Add invoice processing fields to upload_batches and products tables
-- Date: 2025-01-07
-- Description: Extends existing tables with S3 storage, supplier detection, and invoice-specific fields

-- Add invoice-specific fields to upload_batches table
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS original_filename VARCHAR(255);
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS file_size_bytes BIGINT;
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS s3_key VARCHAR(500);
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS s3_url VARCHAR(1000);
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS supplier_code VARCHAR(50);
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS supplier_detection_method VARCHAR(50);
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS supplier_detection_confidence DECIMAL(3,2);
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS invoice_number VARCHAR(100);
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS invoice_date VARCHAR(20);
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS currency_code VARCHAR(3);
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS total_amount_original DECIMAL(10,2);
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS parsing_success_rate DECIMAL(5,2);
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS download_count INTEGER DEFAULT 0;
ALTER TABLE upload_batches ADD COLUMN IF NOT EXISTS last_downloaded_at TIMESTAMP WITH TIME ZONE;

-- Add manufacturer and invoice-specific fields to products table
ALTER TABLE products ADD COLUMN IF NOT EXISTS manufacturer VARCHAR(50);
ALTER TABLE products ADD COLUMN IF NOT EXISTS manufacturer_sku VARCHAR(100);
ALTER TABLE products ADD COLUMN IF NOT EXISTS manufacturer_website VARCHAR(255);
ALTER TABLE products ADD COLUMN IF NOT EXISTS category VARCHAR(100);
ALTER TABLE products ADD COLUMN IF NOT EXISTS quantity_ordered INTEGER;
ALTER TABLE products ADD COLUMN IF NOT EXISTS line_total_usd DECIMAL(10,2);
ALTER TABLE products ADD COLUMN IF NOT EXISTS line_total_eur DECIMAL(10,2);
ALTER TABLE products ADD COLUMN IF NOT EXISTS origin_country VARCHAR(50);
ALTER TABLE products ADD COLUMN IF NOT EXISTS tariff_code VARCHAR(20);
ALTER TABLE products ADD COLUMN IF NOT EXISTS raw_description TEXT;
ALTER TABLE products ADD COLUMN IF NOT EXISTS line_number INTEGER;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_upload_batches_s3_key ON upload_batches(s3_key);
CREATE INDEX IF NOT EXISTS idx_upload_batches_supplier_code ON upload_batches(supplier_code);
CREATE INDEX IF NOT EXISTS idx_upload_batches_invoice_number ON upload_batches(invoice_number);
CREATE INDEX IF NOT EXISTS idx_upload_batches_invoice_date ON upload_batches(invoice_date);
CREATE INDEX IF NOT EXISTS idx_upload_batches_currency_code ON upload_batches(currency_code);

CREATE INDEX IF NOT EXISTS idx_products_manufacturer ON products(manufacturer);
CREATE INDEX IF NOT EXISTS idx_products_manufacturer_sku ON products(manufacturer_sku);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_origin_country ON products(origin_country);
CREATE INDEX IF NOT EXISTS idx_products_tariff_code ON products(tariff_code);
CREATE INDEX IF NOT EXISTS idx_products_line_number ON products(line_number);

-- Add constraints
ALTER TABLE upload_batches ADD CONSTRAINT IF NOT EXISTS chk_supplier_detection_confidence 
    CHECK (supplier_detection_confidence IS NULL OR (supplier_detection_confidence >= 0 AND supplier_detection_confidence <= 1));

ALTER TABLE upload_batches ADD CONSTRAINT IF NOT EXISTS chk_parsing_success_rate 
    CHECK (parsing_success_rate IS NULL OR (parsing_success_rate >= 0 AND parsing_success_rate <= 100));

ALTER TABLE upload_batches ADD CONSTRAINT IF NOT EXISTS chk_download_count 
    CHECK (download_count >= 0);

ALTER TABLE products ADD CONSTRAINT IF NOT EXISTS chk_quantity_ordered 
    CHECK (quantity_ordered IS NULL OR quantity_ordered > 0);

ALTER TABLE products ADD CONSTRAINT IF NOT EXISTS chk_line_number 
    CHECK (line_number IS NULL OR line_number > 0);

-- Add manufacturer consistency constraint
ALTER TABLE products ADD CONSTRAINT IF NOT EXISTS chk_manufacturer_consistency 
    CHECK (
        (manufacturer IS NULL AND manufacturer_sku IS NULL) OR 
        (manufacturer IS NOT NULL AND manufacturer_sku IS NOT NULL)
    );

-- Add comments for documentation
COMMENT ON COLUMN upload_batches.original_filename IS 'Original filename of uploaded invoice';
COMMENT ON COLUMN upload_batches.file_size_bytes IS 'File size in bytes';
COMMENT ON COLUMN upload_batches.s3_key IS 'S3 object key for stored invoice';
COMMENT ON COLUMN upload_batches.s3_url IS 'S3 object URL for stored invoice';
COMMENT ON COLUMN upload_batches.supplier_code IS 'Detected supplier code (lawnfawn, craftlines, etc.)';
COMMENT ON COLUMN upload_batches.supplier_detection_method IS 'Method used for supplier detection';
COMMENT ON COLUMN upload_batches.supplier_detection_confidence IS 'Confidence score for supplier detection (0-1)';
COMMENT ON COLUMN upload_batches.invoice_number IS 'Invoice number extracted from PDF';
COMMENT ON COLUMN upload_batches.invoice_date IS 'Invoice date extracted from PDF';
COMMENT ON COLUMN upload_batches.currency_code IS 'Currency code (USD, EUR, etc.)';
COMMENT ON COLUMN upload_batches.total_amount_original IS 'Total invoice amount in original currency';
COMMENT ON COLUMN upload_batches.parsing_success_rate IS 'Percentage of successfully parsed products';
COMMENT ON COLUMN upload_batches.download_count IS 'Number of times invoice was downloaded';
COMMENT ON COLUMN upload_batches.last_downloaded_at IS 'Timestamp of last download';

COMMENT ON COLUMN products.manufacturer IS 'Product manufacturer (may differ from supplier)';
COMMENT ON COLUMN products.manufacturer_sku IS 'Original manufacturer SKU';
COMMENT ON COLUMN products.manufacturer_website IS 'Manufacturer website URL';
COMMENT ON COLUMN products.category IS 'Product category from invoice';
COMMENT ON COLUMN products.quantity_ordered IS 'Quantity ordered from invoice';
COMMENT ON COLUMN products.line_total_usd IS 'Total line amount in USD';
COMMENT ON COLUMN products.line_total_eur IS 'Total line amount in EUR';
COMMENT ON COLUMN products.origin_country IS 'Country of origin';
COMMENT ON COLUMN products.tariff_code IS 'Tariff/customs code';
COMMENT ON COLUMN products.raw_description IS 'Original description from invoice';
COMMENT ON COLUMN products.line_number IS 'Line number in invoice';

-- Create a view for invoice summaries
CREATE OR REPLACE VIEW invoice_summaries AS
SELECT 
    ub.id,
    ub.original_filename,
    ub.supplier_code,
    ub.invoice_number,
    ub.invoice_date,
    ub.currency_code,
    ub.total_amount_original,
    ub.parsing_success_rate,
    ub.total_products,
    ub.processed_products,
    ub.failed_products,
    ub.status,
    ub.created_at,
    ub.download_count,
    ub.last_downloaded_at,
    s.name as supplier_name
FROM upload_batches ub
LEFT JOIN suppliers s ON ub.supplier_id = s.id
WHERE ub.file_type = 'PDF'
ORDER BY ub.created_at DESC;

COMMENT ON VIEW invoice_summaries IS 'Summary view of processed invoices with supplier information';

-- Create a view for product details with invoice information
CREATE OR REPLACE VIEW product_details AS
SELECT 
    p.id,
    p.supplier_sku,
    p.manufacturer,
    p.manufacturer_sku,
    p.category,
    p.supplier_name as product_name,
    p.quantity_ordered,
    p.supplier_price_usd as price_usd,
    p.line_total_usd,
    p.origin_country,
    p.tariff_code,
    p.raw_description,
    p.line_number,
    p.status,
    p.created_at,
    ub.invoice_number,
    ub.invoice_date,
    ub.supplier_code,
    ub.original_filename,
    s.name as supplier_name
FROM products p
JOIN upload_batches ub ON p.upload_batch_id = ub.id
LEFT JOIN suppliers s ON p.supplier_id = s.id
ORDER BY ub.created_at DESC, p.line_number ASC;

COMMENT ON VIEW product_details IS 'Detailed view of products with invoice and supplier information';
