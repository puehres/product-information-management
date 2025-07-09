"""
Custom exceptions for product enrichment system.

This module defines a hierarchy of exceptions specific to the product enrichment
workflow, providing clear error categorization and handling for different failure modes.
"""

from typing import Optional


class EnrichmentError(Exception):
    """Base exception for enrichment errors."""
    
    def __init__(self, message: str, search_url: Optional[str] = None, method: Optional[str] = None):
        """
        Initialize enrichment error.
        
        Args:
            message: Error message describing the issue
            search_url: Optional URL that was being processed when error occurred
            method: Optional enrichment method that failed
        """
        super().__init__(message)
        self.search_url = search_url
        self.method = method


class SKUExtractionError(EnrichmentError):
    """Error extracting SKU from product code."""
    
    def __init__(self, message: str, supplier_sku: Optional[str] = None):
        """
        Initialize SKU extraction error.
        
        Args:
            message: Error message describing the SKU extraction issue
            supplier_sku: The supplier SKU that failed to be extracted
        """
        super().__init__(message)
        self.supplier_sku = supplier_sku


class SearchError(EnrichmentError):
    """Error during product search."""
    
    def __init__(self, message: str, search_url: Optional[str] = None, sku: Optional[str] = None):
        """
        Initialize search error.
        
        Args:
            message: Error message describing the search issue
            search_url: URL that was being searched when error occurred
            sku: SKU that was being searched for
        """
        super().__init__(message, search_url=search_url)
        self.sku = sku


class ScrapingError(EnrichmentError):
    """Error during product page scraping."""
    
    def __init__(self, message: str, product_url: Optional[str] = None, status_code: Optional[int] = None):
        """
        Initialize scraping error.
        
        Args:
            message: Error message describing the scraping issue
            product_url: URL that was being scraped when error occurred
            status_code: HTTP status code if applicable
        """
        super().__init__(message)
        self.product_url = product_url
        self.status_code = status_code


class FirecrawlAPIError(EnrichmentError):
    """Error with Firecrawl API."""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None, 
        response_data: Optional[dict] = None,
        url: Optional[str] = None
    ):
        """
        Initialize Firecrawl API error.
        
        Args:
            message: Error message describing the API issue
            status_code: HTTP status code from API response
            response_data: Raw response data from API
            url: URL that was being processed when error occurred
        """
        super().__init__(message, search_url=url)
        self.status_code = status_code
        self.response_data = response_data


class ConfidenceThresholdError(EnrichmentError):
    """Confidence score below minimum threshold."""
    
    def __init__(self, message: str, confidence_score: int, threshold: int):
        """
        Initialize confidence threshold error.
        
        Args:
            message: Error message describing the confidence issue
            confidence_score: Actual confidence score achieved
            threshold: Minimum required confidence threshold
        """
        super().__init__(message)
        self.confidence_score = confidence_score
        self.threshold = threshold


class RateLimitError(FirecrawlAPIError):
    """Rate limit exceeded for Firecrawl API."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        """
        Initialize rate limit error.
        
        Args:
            message: Error message describing the rate limit issue
            retry_after: Seconds to wait before retrying (if provided by API)
        """
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class ConfigurationError(EnrichmentError):
    """Configuration error for enrichment system."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        """
        Initialize configuration error.
        
        Args:
            message: Error message describing the configuration issue
            config_key: Configuration key that is missing or invalid
        """
        super().__init__(message)
        self.config_key = config_key


class DatabaseError(EnrichmentError):
    """Database operation error during enrichment."""
    
    def __init__(self, message: str, operation: Optional[str] = None, table: Optional[str] = None):
        """
        Initialize database error.
        
        Args:
            message: Error message describing the database issue
            operation: Database operation that failed (e.g., 'insert', 'update', 'select')
            table: Database table involved in the operation
        """
        super().__init__(message)
        self.operation = operation
        self.table = table
