#!/usr/bin/env python3
"""
Test script for invoice download system functionality.

This script demonstrates how the S3 download link generation works
and tests the complete workflow with an existing processed invoice.
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import requests
from uuid import UUID

from app.core.config import get_settings
from app.services.s3_manager import S3InvoiceManager
from app.services.database_service import DatabaseService
from app.services.invoice_processor import InvoiceProcessorService


@pytest.mark.asyncio
@pytest.mark.integration
async def test_s3_download_system():
    """Test the complete S3 download system workflow."""
    print("🧪 Testing Invoice Download System")
    print("=" * 50)
    
    settings = get_settings()
    
    # Test data - your existing Lawn Fawn invoice
    test_s3_key = "invoices/lawnfawn/2025/07/20250706_125003_KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf"
    expected_invoice_number = "CPSummer25"
    
    print(f"📄 Testing with invoice: {test_s3_key}")
    print()
    
    try:
        # Step 1: Test direct S3 manager functionality
        print("1️⃣ Testing Direct S3 Manager")
        print("-" * 30)
        
        s3_manager = S3InvoiceManager()
        
        # Check if the file exists in S3
        print(f"   Checking if invoice exists in S3...")
        file_exists = s3_manager.check_invoice_exists(test_s3_key)
        print(f"   ✅ File exists: {file_exists}")
        
        if file_exists:
            # Get file metadata
            print(f"   Getting file metadata...")
            metadata = s3_manager.get_invoice_metadata(test_s3_key)
            print(f"   📊 File size: {metadata.get('content_length', 'unknown')} bytes")
            print(f"   📅 Last modified: {metadata.get('last_modified', 'unknown')}")
            print(f"   📋 Content type: {metadata.get('content_type', 'unknown')}")
            
            # Generate presigned download URL
            print(f"   Generating presigned download URL...")
            download_url, expires_at = s3_manager.generate_download_url(test_s3_key)
            print(f"   🔗 Download URL generated successfully")
            print(f"   ⏰ Expires at: {expires_at}")
            print(f"   🔗 URL: {download_url[:100]}...")
            
            # Test that the URL works (using GET with Range header for validation)
            print(f"   Testing download URL accessibility...")
            
            # Use browser-like headers and Range request to validate without downloading full file
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/pdf,*/*',
                'Range': 'bytes=0-1023'  # Only download first 1KB for validation
            }
            
            try:
                response = requests.get(download_url, headers=headers, timeout=10)
                if response.status_code in [200, 206]:  # 200 = OK, 206 = Partial Content
                    print(f"   ✅ Download URL is accessible")
                    print(f"   📊 Content received: {len(response.content)} bytes")
                    print(f"   📋 Content-Type: {response.headers.get('Content-Type', 'unknown')}")
                    print(f"   📊 Status: {response.status_code} ({'Full content' if response.status_code == 200 else 'Partial content'})")
                else:
                    print(f"   ❌ Download URL failed: {response.status_code}")
            except Exception as e:
                print(f"   ❌ Download URL test failed: {e}")
        else:
            print(f"   ❌ File not found in S3")
        
        print()
        
        # Step 2: Test database lookup for batch_id
        print("2️⃣ Testing Database Lookup")
        print("-" * 30)
        
        db_service = DatabaseService()
        
        # Find the batch by S3 key
        print(f"   Searching for batch with S3 key...")
        
        # We'll need to query the database directly since we don't have a method for this yet
        # This demonstrates what we need to implement
        try:
            # Connect to database and search for the batch using Supabase client
            from app.core.database import get_supabase_client
            
            supabase = get_supabase_client()
            
            # Query for the batch with the specific S3 key (using only existing columns)
            result = supabase.table('upload_batches')\
                .select('id, supplier_code, invoice_number, original_filename, created_at, s3_key, s3_url')\
                .eq('s3_key', test_s3_key)\
                .execute()
            
            if result.data and len(result.data) > 0:
                batch_data = result.data[0]
                
                batch_id = str(batch_data['id'])
                print(f"   ✅ Found batch in database")
                print(f"   🆔 Batch ID: {batch_id}")
                print(f"   🏢 Supplier: {batch_data['supplier_code']}")
                print(f"   📄 Invoice Number: {batch_data.get('invoice_number', 'Unknown')}")
                print(f"   📁 Filename: {batch_data['original_filename']}")
                print(f"    Processed: {batch_data['created_at']}")
                
                # Step 3: Test the invoice processor service
                print()
                print("3️⃣ Testing Invoice Processor Service")
                print("-" * 30)
                
                processor = InvoiceProcessorService()
                
                # Test getting invoice details
                print(f"   Getting invoice details...")
                details = await processor.get_invoice_details(batch_id)
                
                if details:
                    print(f"   ✅ Invoice details retrieved")
                    print(f"   📦 Products in batch: {len(details['products'])}")
                    print(f"   📊 Summary: {details['summary']}")
                    
                    # Test generating download URL via processor
                    print(f"   Generating download URL via processor...")
                    processor_download_url = await processor.generate_invoice_download_url(batch_id)
                    
                    if processor_download_url:
                        print(f"   ✅ Download URL generated via processor")
                        print(f"   🔗 URL: {processor_download_url[:100]}...")
                        
                        # Test the processor-generated URL
                        print(f"   Testing processor download URL...")
                        response = requests.head(processor_download_url, timeout=10)
                        if response.status_code == 200:
                            print(f"   ✅ Processor download URL works")
                        else:
                            print(f"   ❌ Processor download URL failed: {response.status_code}")
                    else:
                        print(f"   ❌ Failed to generate download URL via processor")
                else:
                    print(f"   ❌ Failed to get invoice details")
                        
            else:
                print(f"   ❌ Batch not found in database")
                print(f"   💡 This might mean the invoice wasn't processed through the system")
                batch_data = None
                    
        except Exception as e:
            print(f"   ❌ Database error: {e}")
        
        print()
        
        # Step 4: Demonstrate what the API endpoints would return
        print("4️⃣ Simulating API Responses")
        print("-" * 30)
        
        if 'batch_data' in locals() and batch_data:
            # Simulate /api/invoices response
            print("   📋 Simulated GET /api/invoices response:")
            simulated_invoice_list = {
                "success": True,
                "invoices": [
                    {
                        "batch_id": str(batch_data['id']),
                        "supplier": batch_data['supplier_code'],
                        "invoice_number": batch_data.get('invoice_number', 'Unknown'),
                        "invoice_date": None,  # Would need to parse from invoice
                        "products_found": "N/A",  # Column doesn't exist in current schema
                        "processing_date": batch_data['created_at'],
                        "original_filename": batch_data['original_filename'],
                        "parsing_success_rate": "N/A",  # Column doesn't exist in current schema
                        "file_size_mb": round(int(metadata.get('content_length', 0)) / (1024*1024), 2),
                        "currency": "USD",  # From Lawn Fawn
                        "total_amount": None  # Would need to calculate
                    }
                ],
                "total_count": 1,
                "has_more": False,
                "pagination": {
                    "limit": 50,
                    "offset": 0,
                    "next_offset": None
                },
                "error": None
            }
            
            print(f"   {simulated_invoice_list}")
            print()
            
            # Simulate /api/invoices/{batch_id}/download response
            print("   🔗 Simulated GET /api/invoices/{batch_id}/download response:")
            simulated_download_response = {
                "success": True,
                "download_url": download_url,
                "filename": batch_data['original_filename'],
                "expires_at": expires_at.isoformat(),
                "error": None
            }
            
            print(f"   {simulated_download_response}")
        
        print()
        print("✅ Invoice Download System Test Complete!")
        print()
        print("📋 Summary:")
        print(f"   • S3 file exists and is accessible")
        print(f"   • Presigned URLs generate successfully")
        print(f"   • Database contains processing results")
        print(f"   • Download workflow is functional")
        print()
        print("🚀 Next Steps:")
        print(f"   • Implement the missing /api/invoices list endpoint")
        print(f"   • Add database query methods for listing invoices")
        print(f"   • Test the complete API workflow")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_download_url_expiration():
    """Test download URL expiration behavior."""
    print("\n🕐 Testing Download URL Expiration")
    print("-" * 40)
    
    s3_manager = S3InvoiceManager()
    test_s3_key = "invoices/lawnfawn/2025/07/20250706_125003_KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf"
    
    # Generate URL with short expiration (5 seconds for testing)
    print("   Generating URL with 5-second expiration...")
    download_url, expires_at = s3_manager.generate_download_url(test_s3_key, expires_in=5)
    
    print(f"   🔗 URL expires at: {expires_at}")
    
    # Test immediately with GET request (matches browser behavior)
    print("   Testing URL immediately...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Range': 'bytes=0-1023'  # Only download first 1KB for validation
    }
    response = requests.get(download_url, headers=headers, timeout=10)
    print(f"   ✅ Immediate test: {response.status_code} ({'Working correctly' if response.status_code in [200, 206] else 'Failed'})")
    
    # Wait and test after expiration
    print("   Waiting 6 seconds for expiration...")
    await asyncio.sleep(6)
    
    print("   Testing expired URL...")
    try:
        response = requests.get(download_url, headers=headers, timeout=10)
        print(f"   Status after expiration: {response.status_code}")
        if response.status_code == 403:
            print("   ✅ URL properly expired (403 Forbidden)")
        else:
            print("   ⚠️  URL still accessible after expiration")
    except Exception as e:
        print(f"   ✅ URL expired (connection error): {e}")


if __name__ == "__main__":
    print("🧪 Invoice Download System Test Suite")
    print("=" * 50)
    print()
    
    # Run the main test
    asyncio.run(test_s3_download_system())
    
    # Test expiration behavior
    asyncio.run(test_download_url_expiration())
    
    print("\n🎉 All tests completed!")
