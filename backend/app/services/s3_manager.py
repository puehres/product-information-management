"""
S3 management service for invoice file storage.

This module provides secure S3 operations for storing and retrieving
PDF invoices with organized folder structure and presigned URLs.
"""

import boto3
import structlog
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from botocore.exceptions import ClientError, NoCredentialsError
from app.models.invoice import S3UploadError
from app.core.config import get_settings

logger = structlog.get_logger(__name__)


class S3InvoiceManager:
    """
    Service for managing invoice files in AWS S3.
    
    Provides secure upload, download, and organization of PDF invoices
    with automatic folder structure and presigned URL generation.
    """
    
    def __init__(self):
        """Initialize S3 client with configuration."""
        self.settings = get_settings()
        
        # Validate S3 configuration
        if not self.settings.aws_access_key_id or not self.settings.aws_secret_access_key:
            raise ValueError("AWS credentials not configured")
        
        try:
            # Create session with explicit credentials
            session = boto3.Session(
                aws_access_key_id=self.settings.aws_access_key_id,
                aws_secret_access_key=self.settings.aws_secret_access_key,
                region_name=self.settings.aws_region
            )
            
            # Create S3 client with proper configuration for eu-north-1
            config = boto3.session.Config(
                signature_version='s3v4',  # Required for newer regions
                retries={
                    'max_attempts': 3,
                    'mode': 'adaptive'
                },
                region_name=self.settings.aws_region
            )
            
            self.s3_client = session.client('s3', config=config)
            
            logger.info(
                "S3 client initialized",
                region=self.settings.aws_region,
                bucket=self.settings.s3_bucket_name
            )
            
            # Test connection (skip for now due to credential propagation issues)
            # self._validate_bucket_access()
            logger.info("S3 client initialized (validation skipped due to new access key)")
            
        except NoCredentialsError as e:
            logger.error("AWS credentials not found", error=str(e))
            raise S3UploadError("AWS credentials not configured properly")
        except Exception as e:
            logger.error("Failed to initialize S3 client", error=str(e))
            raise S3UploadError(f"S3 initialization failed: {e}")
    
    def upload_invoice(
        self, 
        file_data: bytes, 
        supplier: str, 
        original_filename: str
    ) -> Dict[str, str]:
        """
        Upload invoice PDF to S3 with organized folder structure.
        
        Args:
            file_data: PDF file content as bytes
            supplier: Detected supplier code
            original_filename: Original filename from upload
            
        Returns:
            Dict containing s3_key, s3_url, and metadata
            
        Raises:
            S3UploadError: If upload fails
        """
        try:
            # Generate organized S3 key
            s3_key = self._generate_s3_key(supplier, original_filename)
            
            # Prepare metadata
            metadata = {
                'supplier': supplier,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'original_filename': original_filename,
                'file_size': str(len(file_data))
            }
            
            logger.info(
                "Uploading invoice to S3",
                s3_key=s3_key,
                supplier=supplier,
                file_size=len(file_data)
            )
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.settings.s3_bucket_name,
                Key=s3_key,
                Body=file_data,
                ContentType='application/pdf',
                Metadata=metadata,
                ServerSideEncryption='AES256'  # Enable encryption
            )
            
            # Generate S3 URL (not presigned, just the object URL)
            s3_url = f"https://{self.settings.s3_bucket_name}.s3.{self.settings.aws_region}.amazonaws.com/{s3_key}"
            
            logger.info("Invoice uploaded successfully", s3_key=s3_key)
            
            return {
                's3_key': s3_key,
                's3_url': s3_url,
                'bucket': self.settings.s3_bucket_name,
                'region': self.settings.aws_region,
                'metadata': metadata
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(
                "S3 upload failed",
                error_code=error_code,
                error_message=e.response['Error']['Message']
            )
            raise S3UploadError(f"S3 upload failed: {error_code}")
        except Exception as e:
            logger.error("Unexpected error during S3 upload", error=str(e))
            raise S3UploadError(f"Upload failed: {e}")
    
    def generate_download_url(
        self, 
        s3_key: str, 
        expires_in: Optional[int] = None
    ) -> Tuple[str, datetime]:
        """
        Generate presigned URL for secure invoice download.
        
        Args:
            s3_key: S3 object key
            expires_in: URL expiration time in seconds (default from config)
            
        Returns:
            Tuple of (presigned_url, expiration_datetime)
            
        Raises:
            S3UploadError: If URL generation fails
        """
        try:
            if expires_in is None:
                expires_in = self.settings.invoice_download_expiration
            
            logger.info(
                "Generating presigned download URL",
                s3_key=s3_key,
                expires_in=expires_in
            )
            
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.settings.s3_bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expires_in
            )
            
            expiration_time = datetime.utcnow() + timedelta(seconds=expires_in)
            
            logger.info("Presigned URL generated successfully", s3_key=s3_key)
            
            return presigned_url, expiration_time
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(
                "Failed to generate presigned URL",
                s3_key=s3_key,
                error_code=error_code
            )
            raise S3UploadError(f"Failed to generate download URL: {error_code}")
        except Exception as e:
            logger.error("Unexpected error generating presigned URL", error=str(e))
            raise S3UploadError(f"URL generation failed: {e}")
    
    def delete_invoice(self, s3_key: str) -> bool:
        """
        Delete invoice from S3.
        
        Args:
            s3_key: S3 object key to delete
            
        Returns:
            bool: True if deletion successful
            
        Raises:
            S3UploadError: If deletion fails
        """
        try:
            logger.info("Deleting invoice from S3", s3_key=s3_key)
            
            self.s3_client.delete_object(
                Bucket=self.settings.s3_bucket_name,
                Key=s3_key
            )
            
            logger.info("Invoice deleted successfully", s3_key=s3_key)
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(
                "Failed to delete invoice",
                s3_key=s3_key,
                error_code=error_code
            )
            raise S3UploadError(f"Failed to delete invoice: {error_code}")
        except Exception as e:
            logger.error("Unexpected error deleting invoice", error=str(e))
            raise S3UploadError(f"Deletion failed: {e}")
    
    def check_invoice_exists(self, s3_key: str) -> bool:
        """
        Check if invoice exists in S3.
        
        Args:
            s3_key: S3 object key to check
            
        Returns:
            bool: True if invoice exists
        """
        try:
            self.s3_client.head_object(
                Bucket=self.settings.s3_bucket_name,
                Key=s3_key
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise S3UploadError(f"Error checking invoice existence: {e}")
    
    def get_invoice_metadata(self, s3_key: str) -> Dict[str, str]:
        """
        Get invoice metadata from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Dict containing object metadata
            
        Raises:
            S3UploadError: If metadata retrieval fails
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.settings.s3_bucket_name,
                Key=s3_key
            )
            
            return {
                'content_length': str(response.get('ContentLength', 0)),
                'last_modified': response.get('LastModified', '').isoformat() if response.get('LastModified') else '',
                'content_type': response.get('ContentType', ''),
                **response.get('Metadata', {})
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(
                "Failed to get invoice metadata",
                s3_key=s3_key,
                error_code=error_code
            )
            raise S3UploadError(f"Failed to get metadata: {error_code}")
    
    def _generate_s3_key(self, supplier: str, original_filename: str) -> str:
        """
        Generate organized S3 key for invoice storage.
        
        Format: invoices/{supplier}/{year}/{month}/{timestamp}_{filename}
        
        Args:
            supplier: Supplier code
            original_filename: Original filename
            
        Returns:
            str: Generated S3 key
        """
        now = datetime.utcnow()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        
        # Clean filename
        clean_filename = self._clean_filename(original_filename)
        
        # Generate key with organized structure
        s3_key = (
            f"{self.settings.s3_invoice_prefix}/"
            f"{supplier}/"
            f"{now.year}/"
            f"{now.month:02d}/"
            f"{timestamp}_{clean_filename}"
        )
        
        return s3_key
    
    def _clean_filename(self, filename: str) -> str:
        """
        Clean filename for S3 storage.
        
        Args:
            filename: Original filename
            
        Returns:
            str: Cleaned filename
        """
        # Remove path components
        clean_name = filename.split('/')[-1].split('\\')[-1]
        
        # Ensure PDF extension
        if not clean_name.lower().endswith('.pdf'):
            clean_name += '.pdf'
        
        # Replace problematic characters
        clean_name = clean_name.replace(' ', '_')
        clean_name = ''.join(c for c in clean_name if c.isalnum() or c in '._-')
        
        return clean_name
    
    async def bucket_exists(self) -> bool:
        """
        Check if the configured S3 bucket exists and is accessible.
        
        Returns:
            bool: True if bucket exists and is accessible
        """
        try:
            self.s3_client.head_bucket(Bucket=self.settings.s3_bucket_name)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['404', 'NoSuchBucket']:
                return False
            # Re-raise other errors (like access denied)
            raise
    
    async def upload_invoice_async(
        self, 
        file_content: bytes, 
        filename: str, 
        supplier: str
    ) -> str:
        """
        Upload invoice file to S3 (async wrapper for compatibility).
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            supplier: Supplier code
            
        Returns:
            str: S3 URL of uploaded file
        """
        result = self.upload_invoice(file_content, supplier, filename)
        return result['s3_url']
    
    async def generate_download_url_async(self, s3_key: str) -> str:
        """
        Generate presigned download URL (async wrapper for compatibility).
        
        Args:
            s3_key: S3 object key
            
        Returns:
            str: Presigned download URL
        """
        url, _ = self.generate_download_url(s3_key)
        return url
    
    async def delete_file(self, s3_key: str) -> bool:
        """
        Delete file from S3 (async wrapper for compatibility).
        
        Args:
            s3_key: S3 object key
            
        Returns:
            bool: True if deletion successful
        """
        return self.delete_invoice(s3_key)
    
    def _validate_bucket_access(self) -> None:
        """
        Validate S3 bucket access and permissions.
        
        Raises:
            S3UploadError: If bucket access validation fails
        """
        try:
            # Use head_bucket for simpler validation
            self.s3_client.head_bucket(Bucket=self.settings.s3_bucket_name)
            logger.info("S3 bucket access validated", bucket=self.settings.s3_bucket_name)
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                raise S3UploadError(f"S3 bucket does not exist: {self.settings.s3_bucket_name}")
            elif error_code == 'AccessDenied':
                raise S3UploadError("Access denied to S3 bucket")
            else:
                raise S3UploadError(f"S3 bucket validation failed: {error_code}")
