#!/usr/bin/env python3
"""
Simple download URL generation test.

This script generates a download URL for a known S3 file.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.s3_manager import S3InvoiceManager


async def test_download_url():
    """Test download URL generation."""
    
    print("🔗 Testing Download URL Generation")
    print("=" * 50)
    
    # Initialize S3 manager
    s3_manager = S3InvoiceManager()
    
    # Use a known S3 key from our recent uploads
    # This is from the test we just ran
    s3_key = "invoices/lawnfawn/2025/07/20250707_214043_test_invoice.pdf"
    
    print(f"📄 Testing with S3 key: {s3_key}")
    
    try:
        # Check if file exists
        print("🔍 Checking if file exists in S3...")
        exists = s3_manager.check_invoice_exists(s3_key)
        
        if not exists:
            print("❌ File does not exist in S3")
            # Let's try to list some files to see what's available
            print("\n📋 Let's check what files are available...")
            
            # Try a few different possible keys
            possible_keys = [
                "invoices/lawnfawn/2025/07/20250707_213952_KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf",
                "invoices/lawnfawn/2025/07/20250707_213902_KK-Inv_CPSummer25_from_Lawn_Fawn_35380_003.pdf",
                "invoices/lawnfawn/2025/07/20250707_214043_test_invoice.pdf"
            ]
            
            for key in possible_keys:
                exists = s3_manager.check_invoice_exists(key)
                print(f"   {key}: {'✅ EXISTS' if exists else '❌ NOT FOUND'}")
                if exists:
                    s3_key = key
                    break
            
            if not exists:
                print("❌ No files found. Upload an invoice first.")
                return None
        
        print(f"✅ File exists: {s3_key}")
        
        # Generate download URL
        print(f"\n🔗 Generating download URL...")
        download_url, expires_at = s3_manager.generate_download_url(s3_key)
        
        print("✅ Download URL generated successfully!")
        print()
        print("=" * 80)
        print("📥 DOWNLOAD URL:")
        print("=" * 80)
        print(download_url)
        print("=" * 80)
        print()
        print(f"⏰ Expires at: {expires_at}")
        print()
        
        # Show usage instructions
        print("💡 Usage Instructions:")
        print("   1. Copy the URL above")
        print("   2. Paste it into your browser to download the PDF")
        print("   3. Or use curl:")
        print(f"      curl -o 'downloaded_invoice.pdf' '{download_url}'")
        print()
        print("🔒 Note: This is a secure presigned URL that expires in 1 hour")
        print()
        
        return download_url
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function."""
    print("Simple Download URL Test")
    print("Testing presigned URL generation for S3 files")
    print()
    
    download_url = asyncio.run(test_download_url())
    
    if download_url:
        print(f"🎯 Download URL generated successfully!")
        print(f"You can now test the URL by copying it to your browser.")
        print(f"The PDF should download automatically.")
    else:
        print(f"💥 Failed to generate download URL!")


if __name__ == "__main__":
    main()
