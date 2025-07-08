#!/usr/bin/env python3
"""
Comprehensive deduplication testing script.
Tests the complete deduplication workflow using the test invoice.
"""

import os
import sys
import asyncio
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.database import get_supabase_client
from app.core.config import get_settings
from app.services.invoice_processor import InvoiceProcessorService
from app.services.deduplication_service import get_deduplication_service
from app.services.database_service import get_database_service

async def test_deduplication_logic():
    """Test complete deduplication workflow with test invoice."""
    print("🧪 Starting comprehensive deduplication testing...")
    
    # Initialize services
    settings = get_settings()
    supabase = get_supabase_client()
    db_service = get_database_service()
    dedup_service = get_deduplication_service()
    
    # Test invoice path
    test_invoice_path = Path("tests/fixtures/test_invoice.pdf")
    if not test_invoice_path.exists():
        print(f"❌ Test invoice not found: {test_invoice_path}")
        return False
    
    try:
        print(f"\n📄 Using test invoice: {test_invoice_path}")
        
        # Read test invoice
        with open(test_invoice_path, 'rb') as f:
            invoice_content = f.read()
        
        print(f"📊 Invoice file size: {len(invoice_content)} bytes")
        
        # === FIRST PROCESSING ===
        print("\n🔄 === FIRST PROCESSING (Should create new products) ===")
        
        # Check initial database state
        initial_products = supabase.table('products').select('id', count='exact').execute()
        initial_batches = supabase.table('upload_batches').select('id', count='exact').execute()
        
        print(f"📊 Initial state: {initial_products.count} products, {initial_batches.count} batches")
        
        # Process invoice first time
        print("🚀 Processing test invoice (first time)...")
        
        # Create invoice processor
        processor = InvoiceProcessorService()
        
        # Process the invoice
        try:
            result1 = await processor.process_invoice(
                file_data=invoice_content,
                filename="test_invoice_first.pdf"
            )
            
            print(f"✅ First processing completed:")
            print(f"   - Batch ID: {result1.batch_id}")
            print(f"   - Products processed: {result1.total_products}")
            print(f"   - Success rate: {result1.parsing_success_rate}%")
            
        except Exception as e:
            print(f"❌ First processing failed: {e}")
            return False
        
        # Check database state after first processing
        products_after_first = supabase.table('products').select('id', count='exact').execute()
        batches_after_first = supabase.table('upload_batches').select('id', count='exact').execute()
        
        print(f"📊 After first processing: {products_after_first.count} products, {batches_after_first.count} batches")
        
        # Get product details for verification
        first_products = supabase.table('products').select('manufacturer_sku, supplier_name').execute()
        print(f"📋 Products created: {len(first_products.data)} records")
        
        # Show sample products
        if first_products.data:
            print("   Sample products:")
            for i, product in enumerate(first_products.data[:3]):
                print(f"     {i+1}. {product['manufacturer_sku']} - {product['supplier_name']}")
            if len(first_products.data) > 3:
                print(f"     ... and {len(first_products.data) - 3} more")
        
        # === SECOND PROCESSING ===
        print("\n🔄 === SECOND PROCESSING (Should detect duplicates) ===")
        
        # Process the same invoice again
        print("🚀 Processing same test invoice (second time)...")
        
        try:
            result2 = await processor.process_invoice(
                file_data=invoice_content,
                filename="test_invoice_second.pdf"
            )
            
            print(f"✅ Second processing completed:")
            print(f"   - Batch ID: {result2.batch_id}")
            print(f"   - Products processed: {result2.total_products}")
            print(f"   - Success rate: {result2.parsing_success_rate}%")
            
        except Exception as e:
            print(f"❌ Second processing failed: {e}")
            return False
        
        # Check final database state
        products_after_second = supabase.table('products').select('id', count='exact').execute()
        batches_after_second = supabase.table('upload_batches').select('id', count='exact').execute()
        
        print(f"📊 After second processing: {products_after_second.count} products, {batches_after_second.count} batches")
        
        # === DEDUPLICATION ANALYSIS ===
        print("\n🔍 === DEDUPLICATION ANALYSIS ===")
        
        products_created_first = products_after_first.count - initial_products.count
        products_created_second = products_after_second.count - products_after_first.count
        
        print(f"📈 Products created in first processing: {products_created_first}")
        print(f"📈 Products created in second processing: {products_created_second}")
        
        # Test deduplication effectiveness
        if products_created_second == 0:
            print("✅ DEDUPLICATION SUCCESS: No duplicate products created!")
            print("   All products from second processing were correctly identified as duplicates")
        else:
            print(f"❌ DEDUPLICATION ISSUE: {products_created_second} products were created in second processing")
            print("   This indicates deduplication logic may not be working correctly")
        
        # Verify unique constraint
        print("\n🔒 Testing unique constraint on manufacturer_sku...")
        
        # Get all manufacturer SKUs
        all_products = supabase.table('products').select('manufacturer_sku').execute()
        skus = [p['manufacturer_sku'] for p in all_products.data if p['manufacturer_sku']]
        unique_skus = set(skus)
        
        print(f"📊 Total products: {len(all_products.data)}")
        print(f"📊 Total SKUs: {len(skus)}")
        print(f"📊 Unique SKUs: {len(unique_skus)}")
        
        if len(skus) == len(unique_skus):
            print("✅ UNIQUE CONSTRAINT SUCCESS: All manufacturer_sku values are unique")
        else:
            duplicates = len(skus) - len(unique_skus)
            print(f"❌ UNIQUE CONSTRAINT ISSUE: {duplicates} duplicate SKUs found")
        
        # === SUMMARY ===
        print("\n📋 === TEST SUMMARY ===")
        
        success_criteria = [
            ("Database cleanup", initial_products.count == 0),
            ("First processing created products", products_created_first > 0),
            ("Second processing detected duplicates", products_created_second == 0),
            ("Unique constraint enforced", len(skus) == len(unique_skus)),
            ("Both batches recorded", batches_after_second.count == 2)
        ]
        
        all_passed = True
        for criterion, passed in success_criteria:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {status}: {criterion}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED: Deduplication system is working correctly!")
        else:
            print("\n⚠️  SOME TESTS FAILED: Deduplication system needs attention")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_deduplication_logic())
    sys.exit(0 if success else 1)
