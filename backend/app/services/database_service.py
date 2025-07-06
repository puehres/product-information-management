"""
Database service for the Universal Product Automation System.

This module provides high-level database operations using the Supabase client
with comprehensive error handling and transaction support.
"""

import asyncio
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
import structlog
from ..core.database import get_supabase_client, supabase_manager
from ..models import (
    Supplier, SupplierCreate, SupplierUpdate,
    UploadBatch, UploadBatchCreate, UploadBatchUpdate,
    Product, ProductCreate, ProductUpdate,
    Image, ImageCreate, ImageUpdate,
    PaginationParams, PaginatedResponse
)

logger = structlog.get_logger(__name__)


class DatabaseService:
    """
    High-level database service with CRUD operations for all entities.
    
    This service provides a clean interface to database operations with
    proper error handling, logging, and transaction support.
    """
    
    def __init__(self):
        """Initialize the database service."""
        self.client = get_supabase_client()
    
    # Supplier operations
    
    async def get_suppliers(
        self,
        active_only: bool = True,
        pagination: Optional[PaginationParams] = None
    ) -> Union[List[Supplier], PaginatedResponse]:
        """
        Get all suppliers with optional filtering and pagination.
        
        Args:
            active_only: Whether to return only active suppliers.
            pagination: Optional pagination parameters.
            
        Returns:
            List of suppliers or paginated response.
        """
        try:
            query = self.client.table('suppliers').select('*')
            
            if active_only:
                query = query.eq('active', True)
            
            query = query.order('name')
            
            if pagination:
                # Get total count for pagination
                count_result = self.client.table('suppliers').select('count')
                if active_only:
                    count_result = count_result.eq('active', True)
                total = count_result.execute().count
                
                # Apply pagination
                query = query.range(pagination.offset, pagination.offset + pagination.limit - 1)
                
                result = query.execute()
                suppliers = [Supplier(**item) for item in result.data]
                
                return PaginatedResponse.create(suppliers, total, pagination)
            else:
                result = query.execute()
                return [Supplier(**item) for item in result.data]
                
        except Exception as e:
            logger.error("Failed to get suppliers", error=str(e))
            raise
    
    async def get_supplier_by_id(self, supplier_id: UUID) -> Optional[Supplier]:
        """
        Get a supplier by ID.
        
        Args:
            supplier_id: Supplier ID.
            
        Returns:
            Supplier if found, None otherwise.
        """
        try:
            result = self.client.table('suppliers')\
                .select('*')\
                .eq('id', str(supplier_id))\
                .execute()
            
            if result.data:
                return Supplier(**result.data[0])
            return None
            
        except Exception as e:
            logger.error("Failed to get supplier by ID", supplier_id=str(supplier_id), error=str(e))
            raise
    
    async def get_supplier_by_code(self, code: str) -> Optional[Supplier]:
        """
        Get a supplier by code.
        
        Args:
            code: Supplier code.
            
        Returns:
            Supplier if found, None otherwise.
        """
        try:
            result = self.client.table('suppliers')\
                .select('*')\
                .eq('code', code.upper())\
                .execute()
            
            if result.data:
                return Supplier(**result.data[0])
            return None
            
        except Exception as e:
            logger.error("Failed to get supplier by code", code=code, error=str(e))
            raise
    
    async def create_supplier(self, supplier_data: SupplierCreate) -> Supplier:
        """
        Create a new supplier.
        
        Args:
            supplier_data: Supplier creation data.
            
        Returns:
            Created supplier.
        """
        try:
            data = supplier_data.model_dump(mode='json')
            result = self.client.table('suppliers').insert(data).execute()
            
            if result.data:
                logger.info("Supplier created", supplier_id=result.data[0]['id'])
                return Supplier(**result.data[0])
            else:
                raise ValueError("Failed to create supplier")
                
        except Exception as e:
            logger.error("Failed to create supplier", error=str(e))
            raise
    
    async def update_supplier(
        self,
        supplier_id: UUID,
        supplier_data: SupplierUpdate
    ) -> Optional[Supplier]:
        """
        Update an existing supplier.
        
        Args:
            supplier_id: Supplier ID.
            supplier_data: Supplier update data.
            
        Returns:
            Updated supplier if found, None otherwise.
        """
        try:
            # Only include non-None values in update
            data = {k: v for k, v in supplier_data.dict().items() if v is not None}
            
            if not data:
                # No data to update
                return await self.get_supplier_by_id(supplier_id)
            
            result = self.client.table('suppliers')\
                .update(data)\
                .eq('id', str(supplier_id))\
                .execute()
            
            if result.data:
                logger.info("Supplier updated", supplier_id=str(supplier_id))
                return Supplier(**result.data[0])
            return None
            
        except Exception as e:
            logger.error("Failed to update supplier", supplier_id=str(supplier_id), error=str(e))
            raise
    
    async def delete_supplier(self, supplier_id: UUID) -> bool:
        """
        Delete a supplier.
        
        Args:
            supplier_id: Supplier ID.
            
        Returns:
            True if deleted, False if not found.
        """
        try:
            result = self.client.table('suppliers')\
                .delete()\
                .eq('id', str(supplier_id))\
                .execute()
            
            success = len(result.data) > 0
            if success:
                logger.info("Supplier deleted", supplier_id=str(supplier_id))
            
            return success
            
        except Exception as e:
            logger.error("Failed to delete supplier", supplier_id=str(supplier_id), error=str(e))
            raise
    
    # Upload batch operations
    
    async def get_upload_batches(
        self,
        supplier_id: Optional[UUID] = None,
        pagination: Optional[PaginationParams] = None
    ) -> Union[List[UploadBatch], PaginatedResponse]:
        """
        Get upload batches with optional filtering and pagination.
        
        Args:
            supplier_id: Optional supplier ID filter.
            pagination: Optional pagination parameters.
            
        Returns:
            List of upload batches or paginated response.
        """
        try:
            query = self.client.table('upload_batches').select('*')
            
            if supplier_id:
                query = query.eq('supplier_id', str(supplier_id))
            
            query = query.order('created_at', desc=True)
            
            if pagination:
                # Get total count
                count_query = self.client.table('upload_batches').select('count')
                if supplier_id:
                    count_query = count_query.eq('supplier_id', str(supplier_id))
                total = count_query.execute().count
                
                # Apply pagination
                query = query.range(pagination.offset, pagination.offset + pagination.limit - 1)
                
                result = query.execute()
                batches = [UploadBatch(**item) for item in result.data]
                
                return PaginatedResponse.create(batches, total, pagination)
            else:
                result = query.execute()
                return [UploadBatch(**item) for item in result.data]
                
        except Exception as e:
            logger.error("Failed to get upload batches", error=str(e))
            raise
    
    async def get_upload_batch_by_id(self, batch_id: UUID) -> Optional[UploadBatch]:
        """
        Get an upload batch by ID.
        
        Args:
            batch_id: Batch ID.
            
        Returns:
            Upload batch if found, None otherwise.
        """
        try:
            result = self.client.table('upload_batches')\
                .select('*')\
                .eq('id', str(batch_id))\
                .execute()
            
            if result.data:
                return UploadBatch(**result.data[0])
            return None
            
        except Exception as e:
            logger.error("Failed to get upload batch by ID", batch_id=str(batch_id), error=str(e))
            raise
    
    async def create_upload_batch(self, batch_data: UploadBatchCreate) -> UploadBatch:
        """
        Create a new upload batch.
        
        Args:
            batch_data: Batch creation data.
            
        Returns:
            Created upload batch.
        """
        try:
            data = batch_data.model_dump(mode='json')
            result = self.client.table('upload_batches').insert(data).execute()
            
            if result.data:
                logger.info("Upload batch created", batch_id=result.data[0]['id'])
                return UploadBatch(**result.data[0])
            else:
                raise ValueError("Failed to create upload batch")
                
        except Exception as e:
            logger.error("Failed to create upload batch", error=str(e))
            raise
    
    async def update_upload_batch(
        self,
        batch_id: UUID,
        batch_data: UploadBatchUpdate
    ) -> Optional[UploadBatch]:
        """
        Update an existing upload batch.
        
        Args:
            batch_id: Batch ID.
            batch_data: Batch update data.
            
        Returns:
            Updated upload batch if found, None otherwise.
        """
        try:
            # Only include non-None values in update
            data = {k: v for k, v in batch_data.dict().items() if v is not None}
            
            if not data:
                return await self.get_upload_batch_by_id(batch_id)
            
            result = self.client.table('upload_batches')\
                .update(data)\
                .eq('id', str(batch_id))\
                .execute()
            
            if result.data:
                logger.info("Upload batch updated", batch_id=str(batch_id))
                return UploadBatch(**result.data[0])
            return None
            
        except Exception as e:
            logger.error("Failed to update upload batch", batch_id=str(batch_id), error=str(e))
            raise
    
    # Product operations
    
    async def get_products(
        self,
        batch_id: Optional[UUID] = None,
        supplier_id: Optional[UUID] = None,
        status: Optional[str] = None,
        pagination: Optional[PaginationParams] = None
    ) -> Union[List[Product], PaginatedResponse]:
        """
        Get products with optional filtering and pagination.
        
        Args:
            batch_id: Optional batch ID filter.
            supplier_id: Optional supplier ID filter.
            status: Optional status filter.
            pagination: Optional pagination parameters.
            
        Returns:
            List of products or paginated response.
        """
        try:
            query = self.client.table('products').select('*')
            
            if batch_id:
                query = query.eq('batch_id', str(batch_id))
            if supplier_id:
                query = query.eq('supplier_id', str(supplier_id))
            if status:
                query = query.eq('status', status)
            
            query = query.order('created_at', desc=True)
            
            if pagination:
                # Build count query with same filters
                count_query = self.client.table('products').select('count')
                if batch_id:
                    count_query = count_query.eq('batch_id', str(batch_id))
                if supplier_id:
                    count_query = count_query.eq('supplier_id', str(supplier_id))
                if status:
                    count_query = count_query.eq('status', status)
                
                total = count_query.execute().count
                
                # Apply pagination
                query = query.range(pagination.offset, pagination.offset + pagination.limit - 1)
                
                result = query.execute()
                products = [Product(**item) for item in result.data]
                
                return PaginatedResponse.create(products, total, pagination)
            else:
                result = query.execute()
                return [Product(**item) for item in result.data]
                
        except Exception as e:
            logger.error("Failed to get products", error=str(e))
            raise
    
    async def get_product_by_id(self, product_id: UUID) -> Optional[Product]:
        """
        Get a product by ID.
        
        Args:
            product_id: Product ID.
            
        Returns:
            Product if found, None otherwise.
        """
        try:
            result = self.client.table('products')\
                .select('*')\
                .eq('id', str(product_id))\
                .execute()
            
            if result.data:
                return Product(**result.data[0])
            return None
            
        except Exception as e:
            logger.error("Failed to get product by ID", product_id=str(product_id), error=str(e))
            raise
    
    async def create_product(self, product_data: ProductCreate) -> Product:
        """
        Create a new product.
        
        Args:
            product_data: Product creation data.
            
        Returns:
            Created product.
        """
        try:
            data = product_data.model_dump(mode='json')
            result = self.client.table('products').insert(data).execute()
            
            if result.data:
                logger.info("Product created", product_id=result.data[0]['id'])
                return Product(**result.data[0])
            else:
                raise ValueError("Failed to create product")
                
        except Exception as e:
            logger.error("Failed to create product", error=str(e))
            raise
    
    async def update_product(
        self,
        product_id: UUID,
        product_data: ProductUpdate
    ) -> Optional[Product]:
        """
        Update an existing product.
        
        Args:
            product_id: Product ID.
            product_data: Product update data.
            
        Returns:
            Updated product if found, None otherwise.
        """
        try:
            # Only include non-None values in update
            data = {k: v for k, v in product_data.dict().items() if v is not None}
            
            if not data:
                return await self.get_product_by_id(product_id)
            
            result = self.client.table('products')\
                .update(data)\
                .eq('id', str(product_id))\
                .execute()
            
            if result.data:
                logger.info("Product updated", product_id=str(product_id))
                return Product(**result.data[0])
            return None
            
        except Exception as e:
            logger.error("Failed to update product", product_id=str(product_id), error=str(e))
            raise
    
    # Image operations
    
    async def get_images_by_product_id(self, product_id: UUID) -> List[Image]:
        """
        Get all images for a product.
        
        Args:
            product_id: Product ID.
            
        Returns:
            List of images.
        """
        try:
            result = self.client.table('images')\
                .select('*')\
                .eq('product_id', str(product_id))\
                .order('image_type', 'sequence_number')\
                .execute()
            
            return [Image(**item) for item in result.data]
            
        except Exception as e:
            logger.error("Failed to get images by product ID", product_id=str(product_id), error=str(e))
            raise
    
    async def create_image(self, image_data: ImageCreate) -> Image:
        """
        Create a new image.
        
        Args:
            image_data: Image creation data.
            
        Returns:
            Created image.
        """
        try:
            data = image_data.model_dump(mode='json')
            result = self.client.table('images').insert(data).execute()
            
            if result.data:
                logger.info("Image created", image_id=result.data[0]['id'])
                return Image(**result.data[0])
            else:
                raise ValueError("Failed to create image")
                
        except Exception as e:
            logger.error("Failed to create image", error=str(e))
            raise
    
    async def update_image(
        self,
        image_id: UUID,
        image_data: ImageUpdate
    ) -> Optional[Image]:
        """
        Update an existing image.
        
        Args:
            image_id: Image ID.
            image_data: Image update data.
            
        Returns:
            Updated image if found, None otherwise.
        """
        try:
            # Only include non-None values in update
            data = {k: v for k, v in image_data.dict().items() if v is not None}
            
            if not data:
                return await self.get_image_by_id(image_id)
            
            result = self.client.table('images')\
                .update(data)\
                .eq('id', str(image_id))\
                .execute()
            
            if result.data:
                logger.info("Image updated", image_id=str(image_id))
                return Image(**result.data[0])
            return None
            
        except Exception as e:
            logger.error("Failed to update image", image_id=str(image_id), error=str(e))
            raise
    
    async def get_image_by_id(self, image_id: UUID) -> Optional[Image]:
        """
        Get an image by ID.
        
        Args:
            image_id: Image ID.
            
        Returns:
            Image if found, None otherwise.
        """
        try:
            result = self.client.table('images')\
                .select('*')\
                .eq('id', str(image_id))\
                .execute()
            
            if result.data:
                return Image(**result.data[0])
            return None
            
        except Exception as e:
            logger.error("Failed to get image by ID", image_id=str(image_id), error=str(e))
            raise
    
    # Health and utility operations
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive database health check.
        
        Returns:
            Health check results.
        """
        try:
            return await supabase_manager.health_check()
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }


# Global database service instance
database_service = DatabaseService()


def get_database_service() -> DatabaseService:
    """
    Get the global database service instance.
    
    Returns:
        DatabaseService: Database service instance.
    """
    return database_service
