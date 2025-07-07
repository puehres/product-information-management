-- Migration 005: Invoice Management Indexes
-- Add indexes for efficient invoice listing, filtering, and search

-- Index for supplier filtering
CREATE INDEX IF NOT EXISTS idx_upload_batches_supplier_code 
ON upload_batches(supplier_code);

-- Index for date range filtering (most common query pattern)
CREATE INDEX IF NOT EXISTS idx_upload_batches_created_at 
ON upload_batches(created_at DESC);

-- Index for invoice number lookups
CREATE INDEX IF NOT EXISTS idx_upload_batches_invoice_number 
ON upload_batches(invoice_number);

-- Index for filename searches
CREATE INDEX IF NOT EXISTS idx_upload_batches_filename 
ON upload_batches(original_filename);

-- Composite index for common filter combinations
CREATE INDEX IF NOT EXISTS idx_upload_batches_supplier_date 
ON upload_batches(supplier_code, created_at DESC);

-- Full-text search index for search functionality
-- This creates a GIN index on a tsvector for efficient text search
CREATE INDEX IF NOT EXISTS idx_upload_batches_search 
ON upload_batches 
USING gin(to_tsvector('english', 
    COALESCE(invoice_number, '') || ' ' || 
    COALESCE(original_filename, '') || ' ' || 
    COALESCE(supplier_code, '')
));

-- Index for file size queries (for future filtering)
CREATE INDEX IF NOT EXISTS idx_upload_batches_file_size 
ON upload_batches(file_size_bytes);

-- Index for processing status queries
CREATE INDEX IF NOT EXISTS idx_upload_batches_status 
ON upload_batches(status);

-- Composite index for pagination optimization
CREATE INDEX IF NOT EXISTS idx_upload_batches_pagination 
ON upload_batches(created_at DESC, id);
