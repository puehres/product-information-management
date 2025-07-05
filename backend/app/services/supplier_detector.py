"""
Supplier detection service for PDF invoice processing.

This module provides automatic supplier detection from PDF invoice headers
using pattern matching and confidence scoring.
"""

import re
import structlog
from typing import Dict, List, Any
from app.models.invoice import (
    SupplierDetectionResult, 
    DetectionMethod, 
    UnknownSupplierError,
    SupplierCode
)
from app.core.config import get_settings

logger = structlog.get_logger(__name__)


class SupplierDetectionService:
    """
    Service for detecting invoice suppliers from PDF content.
    
    Uses pattern matching against known supplier signatures including
    company names, addresses, websites, and other identifying information.
    """
    
    # Supplier detection patterns with confidence weights
    SUPPLIER_PATTERNS = {
        SupplierCode.LAWNFAWN: {
            'company_names': [
                'Lawn Fawn',
                'lawnfawn.com',
                'www.lawnfawn.com'
            ],
            'addresses': [
                'Rancho Santa Margarita, CA 92688',
                'Rancho Santa Margarita',
                'CA 92688'
            ],
            'phone_patterns': [
                r'\(949\)\s*888-2083',
                r'949\.888\.2083',
                r'949-888-2083'
            ],
            'confidence_weight': 0.95,
            'min_patterns_required': 1
        },
        SupplierCode.CRAFTLINES: {
            'company_names': [
                'Craftlines',
                'Craft Lines Europe',
                'craftlines.eu',
                'www.craftlines.eu'
            ],
            'addresses': [
                'Netherlands',
                'Europe'
            ],
            'confidence_weight': 0.90,
            'min_patterns_required': 1
        },
        SupplierCode.MAMA_ELEPHANT: {
            'company_names': [
                'Mama Elephant',
                'mamaelephant.com',
                'www.mamaelephant.com'
            ],
            'confidence_weight': 0.85,
            'min_patterns_required': 1
        }
    }
    
    def __init__(self):
        """Initialize supplier detection service."""
        self.settings = get_settings()
        self.confidence_threshold = self.settings.supplier_detection_confidence_threshold
        
    def detect_supplier(self, pdf_text: str) -> SupplierDetectionResult:
        """
        Detect supplier from PDF text content.
        
        Args:
            pdf_text: Full text content extracted from PDF
            
        Returns:
            SupplierDetectionResult: Detection result with confidence score
            
        Raises:
            UnknownSupplierError: If no supported supplier is detected
        """
        logger.info("Starting supplier detection", text_length=len(pdf_text))
        
        # Clean and normalize text for better matching
        normalized_text = self._normalize_text(pdf_text)
        
        best_match = None
        best_confidence = 0.0
        
        # Check each supplier pattern
        for supplier_code, patterns in self.SUPPLIER_PATTERNS.items():
            result = self._check_supplier_patterns(
                supplier_code, 
                patterns, 
                normalized_text, 
                pdf_text
            )
            
            if result and result.confidence > best_confidence:
                best_match = result
                best_confidence = result.confidence
                
        # Return best match if above threshold
        if best_match and best_confidence >= self.confidence_threshold:
            logger.info(
                "Supplier detected successfully",
                supplier=best_match.supplier_code,
                confidence=best_match.confidence,
                patterns=best_match.matched_patterns
            )
            return best_match
            
        # No supplier detected above threshold
        logger.warning(
            "No supplier detected above threshold",
            best_confidence=best_confidence,
            threshold=self.confidence_threshold
        )
        
        supported_suppliers = [code.value for code in SupplierCode]
        raise UnknownSupplierError(
            "Could not identify invoice supplier from content",
            supported_suppliers=supported_suppliers
        )
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for better pattern matching.
        
        Args:
            text: Raw text content
            
        Returns:
            str: Normalized text
        """
        # Remove extra whitespace and normalize line endings
        normalized = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common PDF artifacts
        normalized = re.sub(r'[^\w\s\.\-\(\)@,]', ' ', normalized)
        
        return normalized
    
    def _check_supplier_patterns(
        self, 
        supplier_code: SupplierCode, 
        patterns: Dict[str, Any], 
        normalized_text: str,
        original_text: str
    ) -> SupplierDetectionResult:
        """
        Check if supplier patterns match in the text.
        
        Args:
            supplier_code: Supplier code to check
            patterns: Pattern configuration for supplier
            normalized_text: Normalized text for matching
            original_text: Original text for regex patterns
            
        Returns:
            SupplierDetectionResult: Detection result or None if no match
        """
        matched_patterns = []
        confidence_score = 0.0
        detection_methods = []
        
        # Check company names
        if 'company_names' in patterns:
            for company_name in patterns['company_names']:
                if self._text_contains_pattern(normalized_text, company_name):
                    matched_patterns.append(f"company_name: {company_name}")
                    confidence_score += 0.4
                    detection_methods.append(DetectionMethod.COMPANY_NAME)
        
        # Check addresses
        if 'addresses' in patterns:
            for address in patterns['addresses']:
                if self._text_contains_pattern(normalized_text, address):
                    matched_patterns.append(f"address: {address}")
                    confidence_score += 0.3
                    detection_methods.append(DetectionMethod.ADDRESS_PATTERN)
        
        # Check phone patterns (regex)
        if 'phone_patterns' in patterns:
            for phone_pattern in patterns['phone_patterns']:
                if re.search(phone_pattern, original_text, re.IGNORECASE):
                    matched_patterns.append(f"phone: {phone_pattern}")
                    confidence_score += 0.2
                    detection_methods.append(DetectionMethod.HEADER_PATTERN)
        
        # Apply confidence weight and check minimum requirements
        base_confidence = confidence_score * patterns['confidence_weight']
        min_patterns = patterns.get('min_patterns_required', 1)
        
        if len(matched_patterns) >= min_patterns and base_confidence > 0:
            # Determine primary detection method
            primary_method = (
                detection_methods[0] if detection_methods 
                else DetectionMethod.HEADER_PATTERN
            )
            
            return SupplierDetectionResult(
                supplier_code=supplier_code.value,
                confidence=min(base_confidence, 1.0),  # Cap at 1.0
                matched_patterns=matched_patterns,
                detection_method=primary_method
            )
        
        return None
    
    def _text_contains_pattern(self, text: str, pattern: str) -> bool:
        """
        Check if text contains pattern (case-insensitive).
        
        Args:
            text: Text to search in
            pattern: Pattern to search for
            
        Returns:
            bool: True if pattern found
        """
        return pattern.lower() in text.lower()
    
    def get_supported_suppliers(self) -> List[str]:
        """
        Get list of supported supplier codes.
        
        Returns:
            List[str]: List of supported supplier codes
        """
        return [code.value for code in SupplierCode]
    
    def validate_supplier_code(self, supplier_code: str) -> bool:
        """
        Validate if supplier code is supported.
        
        Args:
            supplier_code: Supplier code to validate
            
        Returns:
            bool: True if supported
        """
        return supplier_code in self.get_supported_suppliers()
