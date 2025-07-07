#!/usr/bin/env python3
"""
Generate a download link for an invoice in the database.

This script:
1. Lists recent invoices in the database
2. Selects the most recent one
3. Generates a presigned download URL
4. Displays the URL for testing
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.database_service import DatabaseService
from app.services.invoice_processor import InvoiceProcessorService


async def generate_download_link():
    """Generate download link for a recent invoice."""
    
    print("🔗 Generating Download Link for Invoice")
    print("=" * 50)
    
    # Step 1: Get database service and list invoices
    print("📋 Finding recent invoices in database...")
    
    db_service = DatabaseService()
    
    # Get recent invoices
    batches, total_count = await db_service.list_upload_batches_with_filters(
        limit=5,
        offset=0,
        sort_by="created_at",
        sort_order="desc"
    )
    
    if not batches:
        print("❌ No invoices found in database")
        return None
    
    print(f"✅ Found {len(batches)} invoices in database")
    
    # Display available invoices
    print("\n📄 Available invoices:")
    for i, batch in enumerate(batches, 1):
        print(f"   {i}. Batch ID: {batch.id}")
        print(f"      Supplier: {getattr(batch, 'supplier_code', 'unknown')}")
        print(f"      Filename: {getattr(batch, 'original_filename', 'unknown')}")
        print(f"      Products: {getattr(batch, 'total_products', 0)}")
        print(f"      Created: {batch.created_at}")
        print()
    
    # Step 2: Select the most recent invoice
    selected_batch = batches[0]
    batch_id = str(selected_batch.id)
    
    print(f"🎯 Selected most recent invoice:")
    print(f"   Batch ID: {batch_id}")
    print(f"   Supplier: {getattr(selected_batch, 'supplier_code', 'unknown')}")
    print(f"   Filename: {getattr(selected_batch, 'original_filename', 'unknown')}")
    print(f"   S3 Key: {getattr(selected_batch, 's3_key', 'unknown')}")
    
    # Step 3: Generate download URL
    print(f"\n🔗 Generating download URL...")
    
    processor = InvoiceProcessorService()
    
    try:
        download_url = await processor.generate_invoice_download_url(batch_id)
        
        if not download_url:
            print("❌ Failed to generate download URL")
            return None
        
        print("✅ Download URL generated successfully!")
        print()
        print("=" * 80)
        print("📥 DOWNLOAD URL:")
        print("=" * 80)
        print(download_url)
        print("=" * 80)
        print()
        
        # Step 4: Show usage instructions
        print("💡 Usage Instructions:")
        print("   1. Copy the URL above")
        print("   2. Paste it into your browser to download the PDF")
        print("   3. Or use curl:")
        print(f"      curl -o 'invoice.pdf' '{download_url}'")
        print()
        print("⏰ Note: This URL expires in 1 hour for security")
        print()
        
        return download_url
        
    except Exception as e:
        print(f"❌ Error generating download URL: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main function."""
    print("Invoice Download Link Generator")
    print("Generating download link for most recent invoice")
    print()
    
    download_url = await generate_download_link()
    
    if download_url:
        print(f"🎯 Download link generated successfully!")
        print(f"You can now test the URL by copying it to your browser.")
    else:
        print(f"💥 Failed to generate download link!")


if __name__ == "__main__":
    asyncio.run(main())
