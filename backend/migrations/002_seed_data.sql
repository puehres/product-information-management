-- Seed data for Universal Product Automation System MVP
-- This migration inserts the Lawn Fawn supplier configuration and test data

-- Insert Lawn Fawn supplier configuration
INSERT INTO suppliers (
    name,
    code,
    website_url,
    identifier_type,
    scraping_config,
    search_url_template,
    active
) VALUES (
    'Lawn Fawn',
    'LF',
    'https://www.lawnfawn.com',
    'sku',
    '{
        "search_method": "sku_search",
        "sku_extraction_pattern": "LF(\\d+)",
        "search_delay_seconds": 1.0,
        "max_retries": 3,
        "timeout_seconds": 30,
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        },
        "selectors": {
            "product_name": "h1.product-title, .product-name h1",
            "product_description": ".product-description, .product-details",
            "product_images": "img.product-image, .product-gallery img",
            "price": ".price, .product-price"
        },
        "image_processing": {
            "min_width": 1000,
            "min_height": 1000,
            "preferred_format": "jpeg",
            "quality": 85
        }
    }'::jsonb,
    'https://www.lawnfawn.com/search?options%5Bprefix%5D=last&q={sku}&filter.p.product_type=',
    true
) ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    website_url = EXCLUDED.website_url,
    scraping_config = EXCLUDED.scraping_config,
    search_url_template = EXCLUDED.search_url_template,
    updated_at = CURRENT_TIMESTAMP;

-- Add helpful comments for the seed data
COMMENT ON TABLE suppliers IS 'Supplier configuration and scraping settings - includes Lawn Fawn MVP configuration';

-- Verify the seed data was inserted correctly
DO $$
DECLARE
    supplier_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO supplier_count FROM suppliers WHERE code = 'LF';
    
    IF supplier_count = 0 THEN
        RAISE EXCEPTION 'Failed to insert Lawn Fawn supplier data';
    ELSE
        RAISE NOTICE 'Successfully inserted Lawn Fawn supplier configuration';
    END IF;
END $$;
