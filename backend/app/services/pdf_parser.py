"""
PDF parsing service for invoice processing.

This module provides PDF text and table extraction using pdfplumber
with proper temporary file handling and error management.
"""

import os
import tempfile
import structlog
import pdfplumber
from typing import List, Tuple, Optional, Dict, Any
from app.models.invoice import PDFParsingError
from app.core.config import get_settings

logger = structlog.get_logger(__name__)


class PDFParserService:
    """
    Service for parsing PDF invoices to extract text and table data.
    
    Uses pdfplumber for robust PDF processing with automatic cleanup
    of temporary files and comprehensive error handling.
    """
    
    def __init__(self):
        """Initialize PDF parser service."""
        self.settings = get_settings()
    
    def extract_text_and_tables(self, file_data: bytes) -> Tuple[str, List[List[List[str]]]]:
        """
        Extract full text and all tables from PDF.
        
        Args:
            file_data: PDF file content as bytes
            
        Returns:
            Tuple of (full_text, list_of_tables)
            
        Raises:
            PDFParsingError: If PDF parsing fails
        """
        temp_file_path = None
        
        try:
            # Create temporary file for pdfplumber (requires file path)
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(file_data)
                tmp_file.flush()
                temp_file_path = tmp_file.name
            
            logger.info(
                "Starting PDF parsing",
                file_size=len(file_data),
                temp_file=temp_file_path
            )
            
            # Extract content using pdfplumber
            full_text, all_tables = self._parse_pdf_file(temp_file_path)
            
            logger.info(
                "PDF parsing completed",
                text_length=len(full_text),
                tables_found=len(all_tables)
            )
            
            return full_text, all_tables
            
        except Exception as e:
            logger.error("PDF parsing failed", error=str(e))
            raise PDFParsingError(f"Failed to parse PDF: {e}", original_error=e)
        
        finally:
            # Always cleanup temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.debug("Temporary file cleaned up", temp_file=temp_file_path)
                except Exception as e:
                    logger.warning("Failed to cleanup temp file", error=str(e))
    
    def extract_text_only(self, file_data: bytes) -> str:
        """
        Extract only text content from PDF (faster for supplier detection).
        
        Args:
            file_data: PDF file content as bytes
            
        Returns:
            str: Extracted text content
            
        Raises:
            PDFParsingError: If PDF parsing fails
        """
        temp_file_path = None
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(file_data)
                tmp_file.flush()
                temp_file_path = tmp_file.name
            
            logger.info("Extracting text from PDF", file_size=len(file_data))
            
            # Extract only text
            full_text = self._extract_text_from_file(temp_file_path)
            
            logger.info("Text extraction completed", text_length=len(full_text))
            
            return full_text
            
        except Exception as e:
            logger.error("Text extraction failed", error=str(e))
            raise PDFParsingError(f"Failed to extract text: {e}", original_error=e)
        
        finally:
            # Cleanup temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning("Failed to cleanup temp file", error=str(e))
    
    def extract_tables_only(self, file_data: bytes) -> List[List[List[str]]]:
        """
        Extract only table data from PDF.
        
        Args:
            file_data: PDF file content as bytes
            
        Returns:
            List of tables (each table is a list of rows, each row is a list of cells)
            
        Raises:
            PDFParsingError: If PDF parsing fails
        """
        temp_file_path = None
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(file_data)
                tmp_file.flush()
                temp_file_path = tmp_file.name
            
            logger.info("Extracting tables from PDF", file_size=len(file_data))
            
            # Extract only tables
            all_tables = self._extract_tables_from_file(temp_file_path)
            
            logger.info("Table extraction completed", tables_found=len(all_tables))
            
            return all_tables
            
        except Exception as e:
            logger.error("Table extraction failed", error=str(e))
            raise PDFParsingError(f"Failed to extract tables: {e}", original_error=e)
        
        finally:
            # Cleanup temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning("Failed to cleanup temp file", error=str(e))
    
    def get_pdf_metadata(self, file_data: bytes) -> Dict[str, Any]:
        """
        Extract PDF metadata information.
        
        Args:
            file_data: PDF file content as bytes
            
        Returns:
            Dict containing PDF metadata
            
        Raises:
            PDFParsingError: If metadata extraction fails
        """
        temp_file_path = None
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(file_data)
                tmp_file.flush()
                temp_file_path = tmp_file.name
            
            with pdfplumber.open(temp_file_path) as pdf:
                metadata = {
                    'page_count': len(pdf.pages),
                    'metadata': pdf.metadata or {},
                    'file_size': len(file_data)
                }
                
                # Add page dimensions if available
                if pdf.pages:
                    first_page = pdf.pages[0]
                    metadata['page_width'] = first_page.width
                    metadata['page_height'] = first_page.height
                
                return metadata
                
        except Exception as e:
            logger.error("Metadata extraction failed", error=str(e))
            raise PDFParsingError(f"Failed to extract metadata: {e}", original_error=e)
        
        finally:
            # Cleanup temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning("Failed to cleanup temp file", error=str(e))
    
    def _parse_pdf_file(self, file_path: str) -> Tuple[str, List[List[List[str]]]]:
        """
        Parse PDF file to extract text and tables.
        
        Args:
            file_path: Path to temporary PDF file
            
        Returns:
            Tuple of (full_text, all_tables)
        """
        full_text = ""
        all_tables = []
        
        with pdfplumber.open(file_path) as pdf:
            logger.info("Processing PDF pages", page_count=len(pdf.pages))
            
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    # Extract text from page
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                    
                    # Extract tables from page
                    page_tables = page.extract_tables()
                    if page_tables:
                        # Clean and validate tables
                        cleaned_tables = self._clean_tables(page_tables)
                        all_tables.extend(cleaned_tables)
                        
                        logger.debug(
                            "Extracted tables from page",
                            page=page_num,
                            tables_count=len(cleaned_tables)
                        )
                
                except Exception as e:
                    logger.warning(
                        "Failed to process page",
                        page=page_num,
                        error=str(e)
                    )
                    continue
        
        return full_text.strip(), all_tables
    
    def _extract_text_from_file(self, file_path: str) -> str:
        """
        Extract only text from PDF file.
        
        Args:
            file_path: Path to temporary PDF file
            
        Returns:
            str: Extracted text
        """
        full_text = ""
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                try:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                except Exception as e:
                    logger.warning("Failed to extract text from page", error=str(e))
                    continue
        
        return full_text.strip()
    
    def _extract_tables_from_file(self, file_path: str) -> List[List[List[str]]]:
        """
        Extract only tables from PDF file.
        
        Args:
            file_path: Path to temporary PDF file
            
        Returns:
            List of cleaned tables
        """
        all_tables = []
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                try:
                    page_tables = page.extract_tables()
                    if page_tables:
                        cleaned_tables = self._clean_tables(page_tables)
                        all_tables.extend(cleaned_tables)
                except Exception as e:
                    logger.warning("Failed to extract tables from page", error=str(e))
                    continue
        
        return all_tables
    
    def _clean_tables(self, raw_tables: List[List[List[Optional[str]]]]) -> List[List[List[str]]]:
        """
        Clean and validate extracted tables.
        
        Args:
            raw_tables: Raw tables from pdfplumber
            
        Returns:
            List of cleaned tables
        """
        cleaned_tables = []
        
        for table_idx, table in enumerate(raw_tables):
            if not table or len(table) < 2:  # Skip empty or single-row tables
                continue
            
            cleaned_table = []
            
            for row_idx, row in enumerate(table):
                if not row:  # Skip empty rows
                    continue
                
                # Clean cells and convert None to empty string
                cleaned_row = []
                for cell in row:
                    if cell is None:
                        cleaned_row.append("")
                    else:
                        # Clean whitespace and normalize
                        cleaned_cell = str(cell).strip()
                        cleaned_row.append(cleaned_cell)
                
                # Only add rows with at least one non-empty cell
                if any(cell for cell in cleaned_row):
                    cleaned_table.append(cleaned_row)
            
            # Only add tables with at least 2 rows (header + data)
            if len(cleaned_table) >= 2:
                cleaned_tables.append(cleaned_table)
                logger.debug(
                    "Cleaned table",
                    table_index=table_idx,
                    rows=len(cleaned_table),
                    columns=len(cleaned_table[0]) if cleaned_table else 0
                )
        
        return cleaned_tables
    
    def validate_pdf_file(self, file_data: bytes) -> bool:
        """
        Validate if file data is a valid PDF.
        
        Args:
            file_data: File content to validate
            
        Returns:
            bool: True if valid PDF
        """
        try:
            # Check PDF header
            if not file_data.startswith(b'%PDF-'):
                return False
            
            # Try to open with pdfplumber
            temp_file_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    tmp_file.write(file_data)
                    tmp_file.flush()
                    temp_file_path = tmp_file.name
                
                with pdfplumber.open(temp_file_path) as pdf:
                    # Try to access first page
                    if len(pdf.pages) > 0:
                        return True
                    
            finally:
                if temp_file_path and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
            return False
            
        except Exception:
            return False
