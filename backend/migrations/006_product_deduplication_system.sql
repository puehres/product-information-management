-- Migration 006: Product Deduplication System
-- Add unique constraint on manufacturer_sku and review fields for conflict detection

-- First, handle any existing duplicate data by updating manufacturer_sku to be unique
-- This is a safety measure in case there are existing duplicates
DO $$
DECLARE
    sku_record RECORD;
    product_record RECORD;
    counter INTEGER;
    original_sku TEXT;
BEGIN
    -- Find and handle duplicate manufacturer_sku entries
    FOR sku_record IN 
        SELECT manufacturer_sku, COUNT(*) as count
        FROM products 
        WHERE manufacturer_sku IS NOT NULL 
        AND manufacturer_sku != ''
        GROUP BY manufacturer_sku 
        HAVING COUNT(*) > 1
    LOOP
        counter := 1;
        original_sku := sku_record.manufacturer_sku;
        
        -- Update duplicates to have unique manufacturer_sku values
        FOR product_record IN 
            SELECT id FROM products 
            WHERE manufacturer_sku = original_sku
            ORDER BY created_at
        LOOP
            IF counter > 1 THEN
                UPDATE products 
                SET manufacturer_sku = original_sku || '_dup_' || counter
                WHERE id = product_record.id;
            END IF;
            counter := counter + 1;
        END LOOP;
    END LOOP;
END $$;

-- Add review fields for conflict detection
ALTER TABLE products ADD COLUMN IF NOT EXISTS requires_review BOOLEAN DEFAULT FALSE;
ALTER TABLE products ADD COLUMN IF NOT EXISTS review_notes TEXT;

-- Add unique constraint on manufacturer_sku (only for non-null, non-empty values)
-- We use a partial unique index to allow multiple NULL values but enforce uniqueness for actual SKUs
CREATE UNIQUE INDEX IF NOT EXISTS unique_manufacturer_sku_idx 
ON products (manufacturer_sku) 
WHERE manufacturer_sku IS NOT NULL AND manufacturer_sku != '';

-- Add index for review queries
CREATE INDEX IF NOT EXISTS idx_products_requires_review 
ON products (requires_review) 
WHERE requires_review = TRUE;

-- Add index for manufacturer_sku lookups (for deduplication queries)
CREATE INDEX IF NOT EXISTS idx_products_manufacturer_sku_lookup 
ON products (manufacturer_sku) 
WHERE manufacturer_sku IS NOT NULL AND manufacturer_sku != '';

-- Add helpful comments
COMMENT ON COLUMN products.requires_review IS 'Flag indicating product needs manual review due to data conflicts';
COMMENT ON COLUMN products.review_notes IS 'Notes about conflicts detected during deduplication process';
COMMENT ON INDEX unique_manufacturer_sku_idx IS 'Ensures unique manufacturer_sku values (excluding NULL/empty)';
