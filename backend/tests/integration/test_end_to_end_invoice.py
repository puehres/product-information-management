#!/usr/bin/env python3
"""
End-to-end test for invoice processing with the CP-Summer25 invoice.

This script tests the complete invoice processing workflow:
1. Upload and process the PDF invoice
2. Verify supplier detection (should be 'lawnfawn')
3. Check that ~90 products are created
4. Validate invoice metadata extraction
5. Test download URL generation
6. Query the database to verify all data
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.invoice_processor import InvoiceProcessorService
from app.services.database_service import DatabaseService
from app.models.invoice import InvoiceUploadResponse


async def test_end_to_end_invoice_processing():
    """Test complete invoice processing workflow."""
    
    print("🚀 Starting End-to-End Invoice Processing Test")
    print("=" * 60)
    
    # Step 1: Load the test invoice
    invoice_path = Path(__file__).parent / "test_invoice.pdf"
    if not invoice_path.exists():
        print(f"❌ Test invoice not found at {invoice_path}")
        return False
    
    print(f"📄 Loading invoice: {invoice_path.name}")
    with open(invoice_path, 'rb') as f:
        invoice_data = f.read()
    
    print(f"📊 Invoice size: {len(invoice_data):,} bytes")
    
    # Step 2: Process the invoice
    print("\n🔄 Processing invoice...")
    processor = InvoiceProcessorService()
    
    try:
        result = await processor.process_invoice(invoice_data, "KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf")
        
        if not result.success:
            print(f"❌ Invoice processing failed: {result.message}")
            if result.error:
                print(f"   Error type: {result.error}")
            return False
        
        print("✅ Invoice processing completed successfully!")
        
        # Step 3: Verify results
        print(f"\n📋 Processing Results:")
        print(f"   Batch ID: {result.batch_id}")
        print(f"   Supplier: {result.supplier}")
        print(f"   Total Products: {result.total_products}")
        print(f"   Parsing Success Rate: {result.parsing_success_rate}%")
        
        # Step 4: Verify supplier detection
        expected_supplier = "lawnfawn"
        if result.supplier != expected_supplier:
            print(f"❌ Supplier detection failed. Expected '{expected_supplier}', got '{result.supplier}'")
            return False
        print(f"✅ Supplier correctly detected as '{result.supplier}'")
        
        # Step 5: Verify product count (should be around 90)
        expected_min_products = 85
        expected_max_products = 95
        if not (expected_min_products <= result.total_products <= expected_max_products):
            print(f"❌ Product count unexpected. Expected {expected_min_products}-{expected_max_products}, got {result.total_products}")
            return False
        print(f"✅ Product count within expected range: {result.total_products} products")
        
        # Step 6: Verify invoice metadata
        if result.invoice_metadata:
            print(f"\n📊 Invoice Metadata:")
            for key, value in result.invoice_metadata.items():
                print(f"   {key}: {value}")
            
            # Check specific metadata
            if result.invoice_metadata.get('invoice_number') != 'CP-Summer25':
                print(f"❌ Invoice number mismatch. Expected 'CP-Summer25', got '{result.invoice_metadata.get('invoice_number')}'")
                return False
            print("✅ Invoice number correctly extracted")
            
            if result.invoice_metadata.get('currency') != 'USD':
                print(f"❌ Currency mismatch. Expected 'USD', got '{result.invoice_metadata.get('currency')}'")
                return False
            print("✅ Currency correctly detected")
        
        # Step 7: Test download URL generation
        print(f"\n🔗 Testing download URL generation...")
        download_url = await processor.generate_invoice_download_url(result.batch_id)
        
        if not download_url:
            print("❌ Failed to generate download URL")
            return False
        
        print("✅ Download URL generated successfully")
        print(f"   URL: {download_url[:100]}...")
        
        # Step 8: Query database to verify data storage
        print(f"\n🗄️  Verifying database storage...")
        db_service = DatabaseService()
        
        # Get batch details
        from uuid import UUID
        batch_details = await processor.get_invoice_details(result.batch_id)
        
        if not batch_details:
            print("❌ Failed to retrieve batch details from database")
            return False
        
        print("✅ Batch details retrieved from database")
        
        # Verify product storage
        stored_products = batch_details.get('products', [])
        if len(stored_products) != result.total_products:
            print(f"❌ Product storage mismatch. Expected {result.total_products}, found {len(stored_products)} in database")
            return False
        
        print(f"✅ All {len(stored_products)} products correctly stored in database")
        
        # Step 9: Sample a few products to verify data quality
        print(f"\n🔍 Sampling product data quality...")
        sample_products = stored_products[:3]  # Check first 3 products
        
        for i, product in enumerate(sample_products, 1):
            print(f"   Product {i}:")
            print(f"     Supplier SKU: {product.get('supplier_sku', 'N/A')}")
            print(f"     Product Name: {product.get('supplier_name', 'N/A')}")
            print(f"     Manufacturer: {product.get('manufacturer', 'N/A')}")
            print(f"     Price USD: ${product.get('supplier_price_usd', 'N/A')}")
            print(f"     Quantity: {product.get('quantity_ordered', 'N/A')}")
            
            # Verify required fields are present
            required_fields = ['supplier_sku', 'supplier_name', 'manufacturer', 'supplier_price_usd']
            missing_fields = [field for field in required_fields if not product.get(field)]
            
            if missing_fields:
                print(f"❌ Product {i} missing required fields: {missing_fields}")
                return False
        
        print("✅ Product data quality verified")
        
        # Step 10: Final summary
        print(f"\n🎉 End-to-End Test Results:")
        print(f"   ✅ Invoice uploaded and processed successfully")
        print(f"   ✅ Supplier detected: {result.supplier}")
        print(f"   ✅ Products parsed: {result.total_products}")
        print(f"   ✅ Success rate: {result.parsing_success_rate}%")
        print(f"   ✅ Invoice metadata extracted correctly")
        print(f"   ✅ Download URL generated")
        print(f"   ✅ All data stored in database")
        print(f"   ✅ Data quality verified")
        
        print(f"\n🏆 ALL TESTS PASSED! Invoice processing system working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error during processing: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    print("Invoice Processing End-to-End Test")
    print("Testing with CP-Summer25 Lawn Fawn invoice")
    print()
    
    success = await test_end_to_end_invoice_processing()
    
    if success:
        print(f"\n🎯 Test completed successfully!")
        sys.exit(0)
    else:
        print(f"\n💥 Test failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
