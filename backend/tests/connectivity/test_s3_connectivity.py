#!/usr/bin/env python3
"""
S3 Connectivity Test Script

Tests AWS S3 connection and basic operations for the invoice processing system.
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.config import get_settings
from app.services.s3_manager import S3InvoiceManager
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@pytest.mark.asyncio
@pytest.mark.connectivity
async def test_s3_connectivity():
    """
    Test S3 connectivity and basic operations.
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    print("🔍 Testing S3 Connectivity...")
    print("=" * 50)
    
    try:
        # Load settings
        settings = get_settings()
        print(f"✓ Settings loaded")
        print(f"  AWS Region: {settings.aws_region}")
        print(f"  S3 Bucket: {settings.s3_bucket_name}")
        
        # Check if AWS credentials are configured
        if not settings.aws_access_key_id:
            print("❌ AWS_ACCESS_KEY_ID not configured")
            return False
        
        if not settings.aws_secret_access_key:
            print("❌ AWS_SECRET_ACCESS_KEY not configured")
            return False
            
        print(f"✓ AWS credentials configured")
        print(f"  Access Key ID: {settings.aws_access_key_id[:8]}...")
        
        # Initialize S3 manager
        s3_manager = S3InvoiceManager()
        print(f"✓ S3 manager initialized")
        
        # Test 1: Check if bucket exists and is accessible
        print("\n📋 Test 1: Bucket Access")
        try:
            bucket_exists = await s3_manager.bucket_exists()
            if bucket_exists:
                print(f"✓ Bucket '{settings.s3_bucket_name}' exists and is accessible")
            else:
                print(f"❌ Bucket '{settings.s3_bucket_name}' does not exist or is not accessible")
                return False
        except Exception as e:
            print(f"❌ Bucket access test failed: {str(e)}")
            return False
        
        # Test 2: Test upload with a small test file
        print("\n📤 Test 2: Upload Test")
        try:
            test_content = b"Test invoice content for S3 connectivity test"
            test_filename = "test_connectivity_invoice.pdf"
            
            s3_url = await s3_manager.upload_invoice_async(
                file_content=test_content,
                filename=test_filename,
                supplier="test"
            )
            
            if s3_url:
                print(f"✓ Test file uploaded successfully")
                print(f"  S3 URL: {s3_url}")
            else:
                print(f"❌ Upload test failed - no URL returned")
                return False
                
        except Exception as e:
            print(f"❌ Upload test failed: {str(e)}")
            return False
        
        # Test 3: Test presigned URL generation and validation
        print("\n🔗 Test 3: Presigned URL Generation & Validation")
        try:
            # Extract S3 key from the uploaded file URL
            s3_key = s3_url.split(f"{settings.s3_bucket_name}/")[-1]
            
            presigned_url = await s3_manager.generate_download_url_async(s3_key)
            
            if presigned_url:
                print(f"✓ Presigned URL generated successfully")
                print(f"  URL length: {len(presigned_url)} characters")
                print(f"  URL preview: {presigned_url[:80]}...")
                
                # Enhanced validation: Check URL format structure
                print(f"  🔍 Validating URL format structure...")
                
                # Validate AWS signature components are present
                required_params = [
                    "X-Amz-Algorithm=AWS4-HMAC-SHA256",
                    "X-Amz-Signature=",
                    "X-Amz-Expires=",
                    "X-Amz-Date=",
                    "X-Amz-SignedHeaders="
                ]
                
                missing_params = []
                for param in required_params:
                    if param not in presigned_url:
                        missing_params.append(param)
                
                if missing_params:
                    print(f"  ❌ Missing required AWS signature parameters:")
                    for param in missing_params:
                        print(f"    - {param}")
                    return False
                else:
                    print(f"  ✓ All required AWS signature parameters present")
                
                # Enhanced validation: Test URL accessibility
                print(f"  🌐 Testing URL accessibility...")
                try:
                    import requests
                    response = requests.head(presigned_url, timeout=10)
                    
                    if response.status_code == 200:
                        print(f"  ✅ URL is accessible (200 OK)")
                        print(f"    Content-Length: {response.headers.get('Content-Length', 'unknown')}")
                        print(f"    Content-Type: {response.headers.get('Content-Type', 'unknown')}")
                    else:
                        print(f"  ❌ URL accessibility failed: {response.status_code}")
                        print(f"    This indicates the presigned URL generation fix is needed")
                        return False
                        
                except ImportError:
                    print(f"  ⚠️  requests library not available, skipping URL accessibility test")
                except Exception as url_test_error:
                    print(f"  ❌ URL accessibility test failed: {str(url_test_error)}")
                    return False
                    
            else:
                print(f"❌ Presigned URL generation failed")
                return False
                
        except Exception as e:
            print(f"❌ Presigned URL test failed: {str(e)}")
            return False
        
        # Test 4: Test file deletion (cleanup)
        print("\n🗑️  Test 4: File Deletion (Cleanup)")
        try:
            deleted = await s3_manager.delete_file(s3_key)
            
            if deleted:
                print(f"✓ Test file deleted successfully")
            else:
                print(f"⚠️  Test file deletion returned False (file may not exist)")
                
        except Exception as e:
            print(f"❌ File deletion test failed: {str(e)}")
            # Don't return False here as cleanup failure shouldn't fail the connectivity test
        
        print("\n🎉 All S3 connectivity tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ S3 connectivity test failed with error: {str(e)}")
        logger.error("S3 connectivity test failed", error=str(e))
        return False


@pytest.mark.asyncio
@pytest.mark.connectivity
async def test_s3_configuration():
    """
    Test S3 configuration and settings.
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    print("\n🔧 Testing S3 Configuration...")
    print("=" * 50)
    
    try:
        settings = get_settings()
        
        # Check required S3 settings
        required_settings = [
            ('aws_access_key_id', 'AWS_ACCESS_KEY_ID'),
            ('aws_secret_access_key', 'AWS_SECRET_ACCESS_KEY'),
            ('aws_region', 'AWS_REGION'),
            ('s3_bucket_name', 'S3_BUCKET_NAME')
        ]
        
        missing_settings = []
        
        for setting_name, env_var in required_settings:
            value = getattr(settings, setting_name, None)
            if not value:
                missing_settings.append(env_var)
                print(f"❌ {env_var} not configured")
            else:
                if 'key' in setting_name.lower():
                    # Mask sensitive values
                    display_value = f"{value[:8]}..." if len(value) > 8 else "***"
                else:
                    display_value = value
                print(f"✓ {env_var}: {display_value}")
        
        if missing_settings:
            print(f"\n❌ Missing required S3 configuration:")
            for setting in missing_settings:
                print(f"  - {setting}")
            print(f"\nPlease add these to your backend/.env file")
            return False
        
        print(f"\n✓ All required S3 settings configured")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")
        return False


async def main():
    """Main test function."""
    print("🚀 S3 Connectivity Test Suite")
    print("=" * 50)
    
    # Test configuration first
    config_ok = await test_s3_configuration()
    if not config_ok:
        print("\n❌ S3 configuration test failed. Please fix configuration before testing connectivity.")
        sys.exit(1)
    
    # Test connectivity
    connectivity_ok = await test_s3_connectivity()
    
    print("\n" + "=" * 50)
    if connectivity_ok:
        print("🎉 S3 connectivity test PASSED")
        print("✓ S3 is properly configured and accessible")
        sys.exit(0)
    else:
        print("❌ S3 connectivity test FAILED")
        print("Please check your AWS credentials and S3 configuration")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
