#!/usr/bin/env python3
"""
Test script to verify Supabase database connectivity and validate the setup.

This script tests:
1. Environment variable loading
2. Supabase client connection
3. Database schema validation
4. Basic CRUD operations
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent / "app"))

def load_environment():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ Environment variables loaded successfully")
        return True
    else:
        print(f"❌ Environment file not found: {env_path}")
        return False

def create_supabase_client() -> Client:
    """Create and return a Supabase client."""
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not service_key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
    
    print(f"🔗 Connecting to Supabase: {url}")
    return create_client(url, service_key)

def test_basic_connection(client: Client) -> bool:
    """Test basic database connection."""
    try:
        # Try to query the suppliers table
        result = client.table('suppliers').select('*').limit(1).execute()
        print("✅ Basic database connection successful")
        return True
    except Exception as e:
        print(f"❌ Basic connection failed: {e}")
        return False

def test_schema_validation(client: Client) -> bool:
    """Validate that all required tables exist."""
    required_tables = ['suppliers', 'upload_batches', 'products', 'images']
    
    try:
        print("🔍 Validating database schema...")
        
        for table in required_tables:
            try:
                # Try to query each table structure
                result = client.table(table).select('*').limit(1).execute()
                print(f"  ✅ Table '{table}' exists and is accessible")
            except Exception as e:
                print(f"  ❌ Table '{table}' validation failed: {e}")
                return False
        
        print("✅ All required tables validated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
        return False

def test_lawn_fawn_supplier(client: Client) -> bool:
    """Test that Lawn Fawn supplier was inserted correctly."""
    try:
        print("🌱 Testing Lawn Fawn supplier data...")
        
        result = client.table('suppliers').select('*').eq('code', 'LF').execute()
        
        if not result.data:
            print("❌ Lawn Fawn supplier not found")
            return False
        
        supplier = result.data[0]
        print(f"  ✅ Supplier found: {supplier['name']} ({supplier['code']})")
        print(f"  ✅ Website: {supplier['website_url']}")
        print(f"  ✅ Active: {supplier['active']}")
        print(f"  ✅ Search template configured: {'search_url_template' in supplier and supplier['search_url_template']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lawn Fawn supplier test failed: {e}")
        return False

def test_crud_operations(client: Client) -> bool:
    """Test basic CRUD operations."""
    try:
        print("🔄 Testing CRUD operations...")
        
        # Get Lawn Fawn supplier ID
        supplier_result = client.table('suppliers').select('id').eq('code', 'LF').execute()
        if not supplier_result.data:
            print("❌ Cannot find Lawn Fawn supplier for CRUD test")
            return False
        
        supplier_id = supplier_result.data[0]['id']
        
        # Test CREATE - Insert a test upload batch
        test_batch_data = {
            'supplier_id': supplier_id,
            'batch_name': 'Test Connectivity Batch',
            'file_type': 'manual',
            'status': 'uploaded',
            'total_products': 0
        }
        
        insert_result = client.table('upload_batches').insert(test_batch_data).execute()
        if not insert_result.data:
            print("❌ CREATE operation failed")
            return False
        
        batch_id = insert_result.data[0]['id']
        print("  ✅ CREATE operation successful")
        
        # Test READ - Query the inserted batch
        read_result = client.table('upload_batches').select('*').eq('id', batch_id).execute()
        if not read_result.data:
            print("❌ READ operation failed")
            return False
        
        print("  ✅ READ operation successful")
        
        # Test UPDATE - Update the batch status
        update_result = client.table('upload_batches').update({
            'status': 'completed',
            'processed_products': 1
        }).eq('id', batch_id).execute()
        
        if not update_result.data:
            print("❌ UPDATE operation failed")
            return False
        
        print("  ✅ UPDATE operation successful")
        
        # Test DELETE - Remove the test batch
        delete_result = client.table('upload_batches').delete().eq('id', batch_id).execute()
        
        if not delete_result.data:
            print("❌ DELETE operation failed")
            return False
        
        print("  ✅ DELETE operation successful")
        print("✅ All CRUD operations completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ CRUD operations test failed: {e}")
        return False

def test_frontend_connection() -> bool:
    """Test frontend environment configuration."""
    try:
        print("🎨 Testing frontend configuration...")
        
        frontend_env_path = Path(__file__).parent.parent.parent.parent / "frontend" / ".env.local"
        
        if not frontend_env_path.exists():
            print("❌ Frontend .env.local file not found")
            return False
        
        # Read frontend environment file
        with open(frontend_env_path, 'r') as f:
            content = f.read()
        
        required_vars = [
            'NEXT_PUBLIC_SUPABASE_URL',
            'NEXT_PUBLIC_SUPABASE_ANON_KEY'
        ]
        
        for var in required_vars:
            if var not in content:
                print(f"❌ Missing frontend environment variable: {var}")
                return False
        
        print("  ✅ Frontend environment variables configured")
        print("✅ Frontend configuration validated")
        return True
        
    except Exception as e:
        print(f"❌ Frontend configuration test failed: {e}")
        return False

def run_connectivity_tests():
    """Run all connectivity and validation tests."""
    print("🚀 Starting Supabase connectivity tests...\n")
    
    tests_passed = 0
    total_tests = 6
    
    # Test 1: Environment loading
    print("Test 1/6: Environment Variable Loading")
    if load_environment():
        tests_passed += 1
    print()
    
    # Test 2: Supabase client creation
    print("Test 2/6: Supabase Client Creation")
    try:
        client = create_supabase_client()
        print("✅ Supabase client created successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Failed to create Supabase client: {e}")
        client = None
    print()
    
    if not client:
        print("❌ Cannot proceed with database tests - client creation failed")
        print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
        return False
    
    # Test 3: Basic connection
    print("Test 3/6: Basic Database Connection")
    if test_basic_connection(client):
        tests_passed += 1
    print()
    
    # Test 4: Schema validation
    print("Test 4/6: Database Schema Validation")
    if test_schema_validation(client):
        tests_passed += 1
    print()
    
    # Test 5: Lawn Fawn supplier validation
    print("Test 5/6: Lawn Fawn Supplier Validation")
    if test_lawn_fawn_supplier(client):
        tests_passed += 1
    print()
    
    # Test 6: CRUD operations
    print("Test 6/6: CRUD Operations")
    if test_crud_operations(client):
        tests_passed += 1
    print()
    
    # Bonus test: Frontend configuration
    print("Bonus Test: Frontend Configuration")
    frontend_ok = test_frontend_connection()
    print()
    
    # Summary
    print("📊 Test Results Summary:")
    print(f"  Database Tests: {tests_passed}/{total_tests} passed")
    print(f"  Frontend Config: {'✅ OK' if frontend_ok else '❌ Failed'}")
    
    if tests_passed == total_tests and frontend_ok:
        print("\n🎉 All tests passed! Your Supabase setup is ready for development.")
        print("\n🚀 Next Steps:")
        return True
    else:
        print(f"\n⚠️  {total_tests - tests_passed} tests failed. Please check the errors above.")
        if not frontend_ok:
            print("  - Frontend configuration needs attention")
        print("\n🔧 Troubleshooting:")
        print("  1. Ensure migrations were run successfully in Supabase dashboard")
        print("  2. Check environment variables are correctly set")
        print("  3. Verify Supabase project is active and accessible")
        return False

if __name__ == "__main__":
    success = run_connectivity_tests()
    sys.exit(0 if success else 1)
