"""
LawnFawn invoice parsing strategy.

This module provides LawnFawn-specific parsing logic for extracting
product data from LawnFawn invoice format.
"""

import re
import structlog
from typing import List, Optional
from decimal import Decimal
from app.models.invoice import InvoiceMetadata, ParsedProduct, InvoiceParsingResult
from .base import InvoiceParsingStrategy

logger = structlog.get_logger(__name__)


class LawnFawnParsingStrategy(InvoiceParsingStrategy):
    """
    Parsing strategy for LawnFawn invoices.
    
    Handles LawnFawn-specific invoice format:
    - Format: "LF1142 - Lawn Cuts - Stitched Rectangle Frames Dies"
    - Currency: USD
    - Table structure: Qty, Description, Price, Origin, Tariff Code, Amount
    """
    
    def __init__(self):
        """Initialize LawnFawn parsing strategy."""
        super().__init__("lawnfawn")
        
        # LawnFawn-specific patterns
        self.sku_pattern = r'(LF\d+)'
        self.category_patterns = {
            'Lawn Cuts': ['Lawn Cuts', 'Dies'],
            'Clear Stamps': ['Clear Stamps', 'Stamps'],
            'Paper': ['Paper', 'Cardstock'],
            'Ink': ['Ink', 'Inkpad'],
            'Accessories': ['Accessories', 'Tools']
        }
    
    def parse_invoice(self, pdf_text: str, tables: List[List[List[str]]]) -> InvoiceParsingResult:
        """
        Parse LawnFawn invoice content.
        
        Args:
            pdf_text: Full text content from PDF
            tables: Extracted tables from PDF
            
        Returns:
            InvoiceParsingResult: Complete parsing result
        """
        logger.info("Starting LawnFawn invoice parsing")
        
        # Reset errors for this parsing session
        self.reset_errors()
        
        try:
            # Extract metadata
            metadata = self.extract_metadata(pdf_text)
            
            # Parse products from tables
            products = self.parse_product_table(tables)
            
            # Calculate success rate
            total_products = len(products)
            successful_products = len([p for p in products if p.supplier_sku and p.product_name])
            success_rate = self.calculate_parsing_success_rate(total_products, successful_products)
            
            logger.info(
                "LawnFawn parsing completed",
                products_found=total_products,
                success_rate=success_rate,
                errors=len(self.parsing_errors)
            )
            
            return InvoiceParsingResult(
                supplier=self.supplier_code,
                metadata=metadata,
                products=products,
                total_products=total_products,
                parsing_success_rate=success_rate,
                parsing_errors=self.get_parsing_errors()
            )
            
        except Exception as e:
            logger.error("LawnFawn parsing failed", error=str(e))
            self.add_parsing_error(f"Critical parsing error: {e}")
            
            return InvoiceParsingResult(
                supplier=self.supplier_code,
                metadata=InvoiceMetadata(),
                products=[],
                total_products=0,
                parsing_success_rate=0.0,
                parsing_errors=self.get_parsing_errors()
            )
    
    def extract_metadata(self, pdf_text: str) -> InvoiceMetadata:
        """
        Extract LawnFawn invoice metadata.
        
        Args:
            pdf_text: Full text content from PDF
            
        Returns:
            InvoiceMetadata: Extracted metadata
        """
        logger.debug("Extracting LawnFawn metadata")
        
        # Extract invoice number (e.g., "CP-Summer25")
        invoice_number = self.extract_text_pattern(
            pdf_text, 
            r'(?:Invoice|Order|CP)[\s#]*([A-Z0-9\-]+)', 
            1
        )
        
        # Extract ship date
        ship_date = self.extract_text_pattern(
            pdf_text,
            r'Ship Date[:\s]*(\d{1,2}/\d{1,2}/\d{4})',
            1
        )
        
        # Extract invoice date (alternative pattern)
        invoice_date = self.extract_text_pattern(
            pdf_text,
            r'Date[:\s]*(\d{1,2}/\d{1,2}/\d{4})',
            1
        )
        
        # Extract total amount
        total_amount = None
        total_match = self.extract_text_pattern(
            pdf_text,
            r'Total[:\s]*\$?([\d,]+\.?\d*)',
            1
        )
        if total_match:
            try:
                total_amount = self.parse_decimal_amount(total_match)
            except ValueError as e:
                self.add_parsing_error(f"Failed to parse total amount: {e}")
        
        metadata = InvoiceMetadata(
            invoice_number=invoice_number,
            invoice_date=invoice_date or ship_date,
            ship_date=ship_date,
            currency="USD",
            total_amount=total_amount,
            company_name="Lawn Fawn",
            company_address="Rancho Santa Margarita, CA 92688"
        )
        
        logger.debug(
            "Metadata extracted",
            invoice_number=invoice_number,
            ship_date=ship_date,
            total_amount=total_amount
        )
        
        return metadata
    
    def parse_product_table(self, tables: List[List[List[str]]]) -> List[ParsedProduct]:
        """
        Parse LawnFawn product tables (may be multiple tables across pages).
        
        Expected format:
        Qty | Description | Price | Origin | Tariff Code | Amount
        3   | LF1142 - Lawn Cuts - Stitched Rectangle Frames Dies | 12.40 | China | 8441.90.0000 | 37.20T
        
        Args:
            tables: List of extracted tables
            
        Returns:
            List[ParsedProduct]: Parsed products
        """
        logger.debug("Parsing LawnFawn product tables")
        
        # Find ALL product tables (LawnFawn invoices can span multiple pages)
        product_tables = self.find_all_product_tables(tables)
        if not product_tables:
            self.add_parsing_error("No product tables found")
            return []
        
        logger.info(f"Found {len(product_tables)} product tables")
        
        all_products = []
        global_row_number = 1  # Track row numbers across all tables
        
        for table_idx, product_table in enumerate(product_tables):
            logger.debug(f"Processing product table {table_idx + 1} with {len(product_table)} rows")
            
            header_row = product_table[0] if product_table else []
            
            # Find column indices
            column_indices = self._find_column_indices(header_row)
            
            logger.debug(
                "Column mapping for table",
                table_index=table_idx + 1,
                columns=column_indices,
                header=header_row
            )
            
            # Parse data rows (skip header)
            for row_idx, row in enumerate(product_table[1:], start=1):
                global_row_number += 1
                try:
                    product = self._parse_product_row(row, column_indices, global_row_number)
                    if product:
                        all_products.append(product)
                except Exception as e:
                    self.add_parsing_error(f"Failed to parse product row: {e}", global_row_number)
                    continue
        
        logger.info(f"Parsed {len(all_products)} products from {len(product_tables)} tables")
        return all_products
    
    def _find_column_indices(self, header_row: List[str]) -> dict:
        """
        Find column indices in header row.
        
        Args:
            header_row: Header row from table
            
        Returns:
            dict: Column name to index mapping
        """
        indices = {}
        
        for idx, header in enumerate(header_row):
            header_lower = header.lower().strip()
            
            if 'qty' in header_lower or 'quantity' in header_lower:
                indices['qty'] = idx
            elif 'description' in header_lower or 'item' in header_lower:
                indices['description'] = idx
            elif 'price' in header_lower and 'unit' not in header_lower:
                indices['price'] = idx
            elif 'origin' in header_lower or 'country' in header_lower:
                indices['origin'] = idx
            elif 'tariff' in header_lower or 'code' in header_lower:
                indices['tariff'] = idx
            elif 'amount' in header_lower or 'total' in header_lower:
                indices['amount'] = idx
        
        return indices
    
    def _parse_product_row(self, row: List[str], column_indices: dict, row_number: int) -> Optional[ParsedProduct]:
        """
        Parse a single product row.
        
        Args:
            row: Table row data
            column_indices: Column index mapping
            row_number: Row number for error reporting
            
        Returns:
            Optional[ParsedProduct]: Parsed product or None if parsing fails
        """
        try:
            # Extract basic fields
            qty_str = row[column_indices.get('qty', 0)] if len(row) > column_indices.get('qty', 0) else ""
            description = row[column_indices.get('description', 1)] if len(row) > column_indices.get('description', 1) else ""
            price_str = row[column_indices.get('price', 2)] if len(row) > column_indices.get('price', 2) else ""
            origin = row[column_indices.get('origin', 3)] if len(row) > column_indices.get('origin', 3) else ""
            tariff = row[column_indices.get('tariff', 4)] if len(row) > column_indices.get('tariff', 4) else ""
            amount_str = row[column_indices.get('amount', 5)] if len(row) > column_indices.get('amount', 5) else ""
            
            # Skip empty rows
            if not description or not description.strip():
                return None
            
            # Parse LawnFawn description format: "LF1142 - Lawn Cuts - Stitched Rectangle Frames Dies"
            sku_match = re.search(self.sku_pattern, description)
            if not sku_match:
                self.add_parsing_error(f"No LawnFawn SKU found in description: {description}", row_number)
                return None
            
            supplier_sku = sku_match.group(1)
            manufacturer_sku = supplier_sku  # Same for LawnFawn direct
            
            # Extract category and product name
            category, product_name = self._parse_description(description)
            
            # Parse quantities and prices
            try:
                quantity = self.parse_integer_quantity(qty_str)
            except ValueError as e:
                self.add_parsing_error(f"Invalid quantity '{qty_str}': {e}", row_number)
                return None
            
            try:
                price_usd = self.parse_decimal_amount(price_str)
            except ValueError as e:
                self.add_parsing_error(f"Invalid price '{price_str}': {e}", row_number)
                return None
            
            try:
                line_total_usd = self.parse_decimal_amount(amount_str) if amount_str else price_usd * quantity
            except ValueError as e:
                # Fallback to calculated total
                line_total_usd = price_usd * quantity
                self.add_parsing_error(f"Invalid amount '{amount_str}', using calculated total: {e}", row_number)
            
            return ParsedProduct(
                supplier_sku=supplier_sku,
                manufacturer="lawnfawn",
                manufacturer_sku=manufacturer_sku,
                category=category,
                product_name=product_name,
                quantity=quantity,
                price_usd=price_usd,
                line_total_usd=line_total_usd,
                origin_country=origin.strip() if origin else None,
                tariff_code=tariff.strip() if tariff else None,
                raw_description=description.strip(),
                line_number=row_number
            )
            
        except Exception as e:
            self.add_parsing_error(f"Unexpected error parsing row: {e}", row_number)
            return None
    
    def _parse_description(self, description: str) -> tuple[str, str]:
        """
        Parse LawnFawn description to extract category and product name.
        
        Format: "LF1142 - Lawn Cuts - Stitched Rectangle Frames Dies"
        
        Args:
            description: Full product description
            
        Returns:
            tuple: (category, product_name)
        """
        # Remove SKU from description
        cleaned_desc = re.sub(self.sku_pattern + r'\s*-\s*', '', description).strip()
        
        # Try to identify category
        category = "Unknown"
        product_name = cleaned_desc
        
        for cat_name, keywords in self.category_patterns.items():
            for keyword in keywords:
                if keyword.lower() in cleaned_desc.lower():
                    category = cat_name
                    # Remove category from product name
                    product_name = re.sub(
                        rf'{re.escape(keyword)}\s*-\s*', 
                        '', 
                        cleaned_desc, 
                        flags=re.IGNORECASE
                    ).strip()
                    break
            if category != "Unknown":
                break
        
        # Clean up product name
        product_name = re.sub(r'^-\s*|\s*-$', '', product_name).strip()
        
        return category, product_name
    
    def find_all_product_tables(self, tables: List[List[List[str]]]) -> List[List[List[str]]]:
        """
        Find ALL product tables from extracted tables (LawnFawn invoices span multiple pages).
        
        Args:
            tables: List of extracted tables
            
        Returns:
            List[List[List[str]]]: All product tables found
        """
        if not tables:
            return []
        
        product_tables = []
        product_keywords = ['qty', 'quantity', 'description', 'price', 'amount', 'tariff']
        
        for table_idx, table in enumerate(tables):
            if len(table) < 2:  # Need at least header + 1 data row
                continue
            
            # Check if header row contains product keywords
            header_row = table[0] if table else []
            header_text = ' '.join(header_row).lower()
            
            keyword_matches = sum(1 for keyword in product_keywords if keyword in header_text)
            
            # If we find multiple product keywords and it has 7 columns (LawnFawn format), it's a product table
            if keyword_matches >= 3 and len(header_row) == 7:
                logger.debug(
                    "Found product table",
                    table_index=table_idx,
                    rows=len(table),
                    columns=len(header_row),
                    keyword_matches=keyword_matches
                )
                product_tables.append(table)
        
        logger.info(f"Found {len(product_tables)} product tables total")
        return product_tables
