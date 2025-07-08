#!/usr/bin/env python3
"""
Database cleanup script for deduplication testing.
Safely removes test data while preserving schema and seed data.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.database import get_supabase_client
from app.core.config import get_settings

async def cleanup_database():
    """Clean database tables for deduplication testing."""
    print("🧹 Starting database cleanup for deduplication testing...")
    
    settings = get_settings()
    supabase = get_supabase_client()
    
    try:
        # Check current data counts
        print("\n📊 Current database state:")
        
        # Count existing records
        images_count = supabase.table('images').select('id', count='exact').execute()
        products_count = supabase.table('products').select('id', count='exact').execute()
        batches_count = supabase.table('upload_batches').select('id', count='exact').execute()
        suppliers_count = supabase.table('suppliers').select('id', count='exact').execute()
        
        print(f"  - Images: {images_count.count}")
        print(f"  - Products: {products_count.count}")
        print(f"  - Upload Batches: {batches_count.count}")
        print(f"  - Suppliers: {suppliers_count.count}")
        
        # Clean in dependency order (respecting foreign keys)
        print("\n🗑️  Cleaning tables in dependency order...")
        
        # 1. Delete images (references products)
        if images_count.count > 0:
            print("  Deleting images...")
            result = supabase.table('images').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            print(f"    Deleted {len(result.data)} image records")
        
        # 2. Delete products (references upload_batches and suppliers)
        if products_count.count > 0:
            print("  Deleting products...")
            result = supabase.table('products').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            print(f"    Deleted {len(result.data)} product records")
        
        # 3. Delete upload batches (main batch records)
        if batches_count.count > 0:
            print("  Deleting upload batches...")
            result = supabase.table('upload_batches').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            print(f"    Deleted {len(result.data)} batch records")
        
        # Keep suppliers (seed data) and schema_migrations (tracking)
        print("  Preserving suppliers and schema_migrations (seed data)")
        
        # Verify cleanup
        print("\n✅ Cleanup completed. Final database state:")
        
        images_count_after = supabase.table('images').select('id', count='exact').execute()
        products_count_after = supabase.table('products').select('id', count='exact').execute()
        batches_count_after = supabase.table('upload_batches').select('id', count='exact').execute()
        suppliers_count_after = supabase.table('suppliers').select('id', count='exact').execute()
        
        print(f"  - Images: {images_count_after.count}")
        print(f"  - Products: {products_count_after.count}")
        print(f"  - Upload Batches: {batches_count_after.count}")
        print(f"  - Suppliers: {suppliers_count_after.count} (preserved)")
        
        print("\n🎯 Database is now clean and ready for deduplication testing!")
        return True
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(cleanup_database())
    sys.exit(0 if success else 1)
