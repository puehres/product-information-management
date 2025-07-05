"""
Base invoice parsing strategy.

This module provides the abstract base class for supplier-specific
invoice parsing strategies using the Strategy pattern.
"""

import re
import structlog
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation
from app.models.invoice import InvoiceMetadata, ParsedProduct, InvoiceParsingResult

logger = structlog.get_logger(__name__)


class InvoiceParsingStrategy(ABC):
    """
    Abstract base class for supplier-specific invoice parsing strategies.
    
    Implements the Strategy pattern to handle different invoice formats
    with common validation and error handling.
    """
    
    def __init__(self, supplier_code: str):
        """
        Initialize parsing strategy.
        
        Args:
            supplier_code: Supplier code for this strategy
        """
        self.supplier_code = supplier_code
        self.parsing_errors = []
    
    @abstractmethod
    def parse_invoice(self, pdf_text: str, tables: List[List[List[str]]]) -> InvoiceParsingResult:
        """
        Parse invoice content to extract products and metadata.
        
        Args:
            pdf_text: Full text content from PDF
            tables: Extracted tables from PDF
            
        Returns:
            InvoiceParsingResult: Complete parsing result
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, pdf_text: str) -> InvoiceMetadata:
        """
        Extract invoice metadata from PDF text.
        
        Args:
            pdf_text: Full text content from PDF
            
        Returns:
            InvoiceMetadata: Extracted metadata
        """
        pass
    
    @abstractmethod
    def parse_product_table(self, tables: List[List[List[str]]]) -> List[ParsedProduct]:
        """
        Parse product data from extracted tables.
        
        Args:
            tables: List of tables from PDF
            
        Returns:
            List[ParsedProduct]: Parsed products
        """
        pass
    
    def validate_and_clean_sku(self, sku: str) -> str:
        """
        Validate and clean SKU format.
        
        Args:
            sku: Raw SKU string
            
        Returns:
            str: Cleaned SKU
            
        Raises:
            ValueError: If SKU is invalid
        """
        if not sku or not sku.strip():
            raise ValueError("SKU cannot be empty")
        
        # Remove extra whitespace
        cleaned_sku = sku.strip()
        
        # Remove common prefixes/suffixes that might be artifacts
        cleaned_sku = re.sub(r'^[^\w]+|[^\w]+$', '', cleaned_sku)
        
        if not cleaned_sku:
            raise ValueError("SKU contains no valid characters")
        
        return cleaned_sku
    
    def parse_decimal_amount(self, amount_str: str) -> Decimal:
        """
        Parse decimal amount from string with error handling.
        
        Args:
            amount_str: Amount string (e.g., "$12.40", "12,40", "12.40T")
            
        Returns:
            Decimal: Parsed amount
            
        Raises:
            ValueError: If amount cannot be parsed
        """
        if not amount_str or not amount_str.strip():
            raise ValueError("Amount cannot be empty")
        
        # Clean amount string
        cleaned = amount_str.strip()
        
        # Remove currency symbols and common suffixes
        cleaned = re.sub(r'[$€£¥]', '', cleaned)
        cleaned = re.sub(r'[T]$', '', cleaned)  # Remove trailing 'T' (tax indicator)
        
        # Handle comma as decimal separator (European format)
        if ',' in cleaned and '.' not in cleaned:
            cleaned = cleaned.replace(',', '.')
        elif ',' in cleaned and '.' in cleaned:
            # Assume comma is thousands separator
            cleaned = cleaned.replace(',', '')
        
        # Remove any remaining non-numeric characters except decimal point
        cleaned = re.sub(r'[^\d\.]', '', cleaned)
        
        if not cleaned:
            raise ValueError("No numeric content found in amount")
        
        try:
            return Decimal(cleaned)
        except InvalidOperation as e:
            raise ValueError(f"Invalid decimal format: {cleaned}") from e
    
    def parse_integer_quantity(self, quantity_str: str) -> int:
        """
        Parse integer quantity from string.
        
        Args:
            quantity_str: Quantity string
            
        Returns:
            int: Parsed quantity
            
        Raises:
            ValueError: If quantity cannot be parsed
        """
        if not quantity_str or not quantity_str.strip():
            raise ValueError("Quantity cannot be empty")
        
        # Clean quantity string
        cleaned = re.sub(r'[^\d]', '', quantity_str.strip())
        
        if not cleaned:
            raise ValueError("No numeric content found in quantity")
        
        try:
            quantity = int(cleaned)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            return quantity
        except ValueError as e:
            raise ValueError(f"Invalid quantity format: {quantity_str}") from e
    
    def extract_text_pattern(self, text: str, pattern: str, group: int = 1) -> Optional[str]:
        """
        Extract text using regex pattern.
        
        Args:
            text: Text to search in
            pattern: Regex pattern
            group: Group number to extract (default: 1)
            
        Returns:
            Optional[str]: Extracted text or None if not found
        """
        try:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match and len(match.groups()) >= group:
                return match.group(group).strip()
            return None
        except Exception as e:
            logger.warning("Pattern extraction failed", pattern=pattern, error=str(e))
            return None
    
    def find_product_table(self, tables: List[List[List[str]]]) -> Optional[List[List[str]]]:
        """
        Find the main product table from extracted tables.
        
        Args:
            tables: List of extracted tables
            
        Returns:
            Optional[List[List[str]]]: Product table or None if not found
        """
        if not tables:
            return None
        
        # Look for table with product-like headers
        product_keywords = ['qty', 'quantity', 'description', 'price', 'amount', 'sku', 'item']
        
        for table in tables:
            if len(table) < 2:  # Need at least header + 1 data row
                continue
            
            # Check if header row contains product keywords
            header_row = table[0] if table else []
            header_text = ' '.join(header_row).lower()
            
            keyword_matches = sum(1 for keyword in product_keywords if keyword in header_text)
            
            # If we find multiple product keywords, this is likely the product table
            if keyword_matches >= 2:
                logger.info(
                    "Found product table",
                    rows=len(table),
                    columns=len(header_row),
                    keyword_matches=keyword_matches
                )
                return table
        
        # Fallback: return largest table
        if tables:
            largest_table = max(tables, key=len)
            logger.info("Using largest table as fallback", rows=len(largest_table))
            return largest_table
        
        return None
    
    def calculate_parsing_success_rate(self, total_rows: int, successful_rows: int) -> float:
        """
        Calculate parsing success rate percentage.
        
        Args:
            total_rows: Total number of rows processed
            successful_rows: Number of successfully parsed rows
            
        Returns:
            float: Success rate as percentage (0-100)
        """
        if total_rows == 0:
            return 0.0
        
        return round((successful_rows / total_rows) * 100, 1)
    
    def add_parsing_error(self, error_message: str, row_number: Optional[int] = None):
        """
        Add parsing error to error list.
        
        Args:
            error_message: Error description
            row_number: Optional row number where error occurred
        """
        if row_number is not None:
            error_message = f"Row {row_number}: {error_message}"
        
        self.parsing_errors.append(error_message)
        logger.warning("Parsing error", error=error_message, supplier=self.supplier_code)
    
    def reset_errors(self):
        """Reset parsing errors list."""
        self.parsing_errors = []
    
    def get_parsing_errors(self) -> List[str]:
        """
        Get list of parsing errors.
        
        Returns:
            List[str]: List of error messages
        """
        return self.parsing_errors.copy()
