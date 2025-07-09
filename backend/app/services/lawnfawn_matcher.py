"""
LawnFawn-specific product matching and scraping logic.

This module handles SKU extraction, search URL construction, product page scraping,
and confidence scoring specifically for LawnFawn products.
"""

import re
import time
from typing import Optional, List, Dict, Any
from urllib.parse import quote
import structlog
from bs4 import BeautifulSoup

from ..models.product import Product
from ..models.enrichment import (
    EnrichmentData, SearchResults, ProductData, EnrichmentMethod,
    EnrichmentConfig
)
from ..exceptions.enrichment import (
    SKUExtractionError, SearchError, ScrapingError
)
from .firecrawl_client import get_firecrawl_client

logger = structlog.get_logger(__name__)


class LawnFawnMatcher:
    """
    LawnFawn-specific product matching and scraping logic.
    
    Handles:
    - SKU extraction and normalization
    - Search URL construction
    - Search results parsing
    - Product page scraping
    - Confidence scoring
    """
    
    def __init__(self, config: Optional[EnrichmentConfig] = None):
        """
        Initialize LawnFawn matcher.
        
        Args:
            config: Optional enrichment configuration
        """
        self.firecrawl_client = get_firecrawl_client(config)
        
        if config:
            self.base_search_url = f"{config.lawnfawn_base_url}/search"
            self.sku_pattern = config.sku_extraction_pattern
            self.confidence_scores = config.confidence_thresholds
        else:
            import os
            self.base_search_url = f"{os.getenv('LAWNFAWN_BASE_URL', 'https://www.lawnfawn.com')}/search"
            self.sku_pattern = os.getenv('SKU_EXTRACTION_PATTERN', r'LF[-]?(\d+)')
            self.confidence_scores = {
                'exact_match': int(os.getenv('CONFIDENCE_EXACT_MATCH', '100')),
                'first_result_match': int(os.getenv('CONFIDENCE_FIRST_RESULT_MATCH', '90')),
                'first_result_no_match': int(os.getenv('CONFIDENCE_FIRST_RESULT_NO_MATCH', '60')),
                'fallback': int(os.getenv('CONFIDENCE_FALLBACK', '30'))
            }
        
        logger.info(
            "LawnFawn matcher initialized",
            base_search_url=self.base_search_url,
            sku_pattern=self.sku_pattern
        )
    
    def extract_numeric_sku(self, supplier_sku: str) -> Optional[str]:
        """
        Extract numeric part from LawnFawn SKU.
        
        Examples:
        - "LF2538" → "2538"
        - "LF-1142" → "1142"
        - "lf3456" → "3456"
        
        Args:
            supplier_sku: Original supplier SKU
            
        Returns:
            Optional[str]: Numeric SKU or None if not found
        """
        if not supplier_sku:
            return None
        
        try:
            match = re.search(self.sku_pattern, supplier_sku.upper())
            numeric_sku = match.group(1) if match else None
            
            logger.debug(
                "SKU extraction",
                supplier_sku=supplier_sku,
                numeric_sku=numeric_sku,
                pattern=self.sku_pattern
            )
            
            return numeric_sku
            
        except Exception as e:
            logger.error(
                "Error extracting SKU",
                supplier_sku=supplier_sku,
                error=str(e)
            )
            return None
    
    def build_search_url(self, numeric_sku: str) -> str:
        """
        Build LawnFawn search URL for numeric SKU.
        
        Args:
            numeric_sku: Numeric SKU (e.g., "2538")
            
        Returns:
            str: Complete search URL
        """
        # URL encode the SKU for safety
        encoded_sku = quote(numeric_sku)
        
        # LawnFawn search URL format
        search_url = f"{self.base_search_url}?options%5Bprefix%5D=last&q={encoded_sku}&filter.p.product_type="
        
        logger.debug(
            "Built search URL",
            numeric_sku=numeric_sku,
            search_url=search_url
        )
        
        return search_url
    
    async def search_products(self, search_url: str) -> SearchResults:
        """
        Search for products using Firecrawl API.
        
        Args:
            search_url: LawnFawn search URL
            
        Returns:
            SearchResults: Parsed search results with product links
            
        Raises:
            SearchError: If search fails or returns no results
        """
        logger.info("Starting product search", search_url=search_url)
        
        try:
            # Scrape search page
            response = await self.firecrawl_client.scrape_page(search_url)
            
            if not response.success:
                raise SearchError(
                    f"Failed to scrape search page: {response.error_message}",
                    search_url=search_url
                )
            
            # Parse search results to extract product links
            product_links = self.extract_product_links(response.content)
            
            logger.info(
                "Search completed",
                search_url=search_url,
                total_results=len(product_links),
                processing_time_ms=response.processing_time_ms
            )
            
            return SearchResults(
                search_url=search_url,
                product_links=product_links,
                total_results=len(product_links),
                raw_response=response.raw_data
            )
            
        except SearchError:
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during search",
                search_url=search_url,
                error=str(e)
            )
            raise SearchError(
                f"Search failed: {str(e)}",
                search_url=search_url
            )
    
    def extract_product_links(self, html_content: str) -> List[str]:
        """
        Extract product page links from search results content using context-aware parsing.
        
        This method looks for the "Show X result(s)" pattern to determine the expected
        number of results, then extracts only product links from the actual search
        results section, avoiding navigation and promotional links.
        
        Args:
            html_content: Content from search page (markdown/text format from Firecrawl)
            
        Returns:
            List[str]: List of product page URLs from actual search results
        """
        try:
            product_links = []
            
            # Step 1: Try HTML parsing first (in case format changes)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for LawnFawn-specific product link selectors
            lawnfawn_selectors = [
                'a.js-prod-link',  # Primary LawnFawn product link class
                'a.media.block.relative',  # Alternative class combination
                'a[href*="/products/"]',  # Generic product URL selector
                '.product-item a',  # Fallback selectors
                '.product-link',
                '.grid-product__link'
            ]
            
            for selector in lawnfawn_selectors:
                for link in soup.select(selector):
                    href = link.get('href')
                    if href and '/products/' in href:
                        # Convert relative URLs to absolute
                        if href.startswith('/'):
                            href = f"https://www.lawnfawn.com{href}"
                        elif href.startswith('//'):
                            href = f"https:{href}"
                        
                        # Avoid duplicates
                        if href not in product_links:
                            product_links.append(href)
                            logger.debug(
                                "Found product link (HTML)",
                                selector=selector,
                                href=href,
                                link_classes=link.get('class', [])
                            )
            
            # Step 2: If no HTML links found, use context-aware regex extraction
            if not product_links:
                logger.debug("No HTML links found, trying context-aware regex extraction")
                
                # First, find the expected number of search results
                expected_results = self._extract_results_count(html_content)
                logger.debug(
                    "Search results context",
                    expected_results=expected_results
                )
                
                # If no results expected, return empty list
                if expected_results == 0:
                    logger.info("Search returned 0 results")
                    return []
                
                # Extract product links from the search results section only
                search_result_links = self._extract_search_result_links(html_content)
                
                # Validate that we found the expected number of results
                if expected_results is not None and len(search_result_links) != expected_results:
                    logger.warning(
                        "Result count mismatch",
                        expected=expected_results,
                        found=len(search_result_links),
                        links=search_result_links
                    )
                    
                    # If we found more than expected, take only the first N
                    if len(search_result_links) > expected_results:
                        search_result_links = search_result_links[:expected_results]
                        logger.debug(
                            "Trimmed results to expected count",
                            trimmed_links=search_result_links
                        )
                
                product_links.extend(search_result_links)
            
            # Step 3: Fallback to broad extraction if context-aware method failed
            if not product_links:
                logger.debug("Context-aware extraction failed, trying broad regex patterns")
                product_links = self._extract_with_broad_patterns(html_content)
            
            # Step 4: Final fallback - content-based construction
            if not product_links:
                logger.debug("All regex methods failed, trying content-based construction")
                product_links = self._construct_urls_from_content(html_content)
            
            logger.debug(
                "Final extracted product links",
                total_links=len(product_links),
                sample_links=product_links[:3] if product_links else []
            )
            
            return product_links
            
        except Exception as e:
            logger.error(
                "Error extracting product links",
                error=str(e)
            )
            return []
    
    def _extract_results_count(self, content: str) -> Optional[int]:
        """
        Extract the expected number of search results from "Show X result(s)" pattern.
        
        Args:
            content: Page content
            
        Returns:
            Optional[int]: Number of expected results, or None if not found
        """
        try:
            # Look for "Show X result" or "Show X results" pattern
            result_patterns = [
                r'Show (\d+) results?',
                r'(\d+) results? found',
                r'(\d+) products? found',
            ]
            
            for pattern in result_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    count = int(match.group(1))
                    logger.debug(
                        "Found results count",
                        pattern=pattern,
                        count=count
                    )
                    return count
            
            return None
            
        except Exception as e:
            logger.error("Error extracting results count", error=str(e))
            return None
    
    def _extract_search_result_links(self, content: str) -> List[str]:
        """
        Extract product links specifically from the search results section.
        
        This looks for product links that appear after "Show X result(s)" and
        before price indicators, ensuring we only get actual search results.
        
        Args:
            content: Page content
            
        Returns:
            List[str]: Product URLs from search results section
        """
        try:
            product_links = []
            
            # Find the search results section boundaries
            # Start: after "Show X result(s)"
            # End: before next major section or end of content
            
            # Pattern to find search results section
            results_section_pattern = r'Show \d+ results?.*?(?=(?:Filter|Sort|Product type|\Z))'
            results_section_match = re.search(results_section_pattern, content, re.IGNORECASE | re.DOTALL)
            
            if results_section_match:
                results_section = results_section_match.group(0)
                logger.debug(
                    "Found search results section",
                    section_length=len(results_section),
                    section_preview=results_section[:200] + "..." if len(results_section) > 200 else results_section
                )
            else:
                # Fallback: look for product links after any "result" mention
                results_section = content
                logger.debug("No clear results section found, using full content")
            
            # Extract product links from the results section
            # Look for markdown link patterns: [product name](url)
            link_patterns = [
                # Markdown link with product URL
                r'\[([^\]]+)\]\((https://www\.lawnfawn\.com/products/[^)]+)\)',
                # Direct product URLs
                r'(https://www\.lawnfawn\.com/products/[^\s\)]+)',
                # Relative product URLs
                r'\((/products/[^)]+)\)',
            ]
            
            for pattern in link_patterns:
                matches = re.findall(pattern, results_section, re.IGNORECASE)
                
                for match in matches:
                    # Handle tuple results from regex groups
                    if isinstance(match, tuple):
                        # Find the URL part (usually the second element)
                        url = None
                        for part in match:
                            if '/products/' in part:
                                url = part
                                break
                    else:
                        url = match
                    
                    if url:
                        # Clean up and normalize URL
                        url = url.strip('()')
                        
                        # Convert relative URLs to absolute
                        if url.startswith('/'):
                            url = f"https://www.lawnfawn.com{url}"
                        elif url.startswith('//'):
                            url = f"https:{url}"
                        
                        # Avoid duplicates and ensure it's a product URL
                        if url not in product_links and '/products/' in url:
                            product_links.append(url)
                            logger.debug(
                                "Found search result link",
                                pattern=pattern,
                                url=url
                            )
            
            return product_links
            
        except Exception as e:
            logger.error("Error extracting search result links", error=str(e))
            return []
    
    def _extract_with_broad_patterns(self, content: str) -> List[str]:
        """
        Fallback method using broad regex patterns (original approach).
        
        Args:
            content: Page content
            
        Returns:
            List[str]: Product URLs found with broad patterns
        """
        try:
            product_links = []
            
            # Broad regex patterns (original approach)
            url_patterns = [
                # Markdown link format: [text](url)
                r'\[([^\]]*)\]\((https://www\.lawnfawn\.com/[^)]*products/[^)]*)\)',
                # Direct URL mentions
                r'(https://www\.lawnfawn\.com/[^\s]*products/[^\s]*)',
                # Relative URLs that start with /products/
                r'(\(/products/[^)]*\))',
                r'(/products/[^\s\)]*)',
            ]
            
            for pattern in url_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                
                for match in matches:
                    # Handle tuple results from regex groups
                    if isinstance(match, tuple):
                        # For patterns with groups, find the URL part
                        url = None
                        for part in match:
                            if '/products/' in part:
                                url = part
                                break
                    else:
                        url = match
                    
                    if url:
                        # Clean up the URL
                        url = url.strip('()')
                        
                        # Convert relative URLs to absolute
                        if url.startswith('/'):
                            url = f"https://www.lawnfawn.com{url}"
                        elif url.startswith('//'):
                            url = f"https:{url}"
                        
                        # Avoid duplicates
                        if url not in product_links and '/products/' in url:
                            product_links.append(url)
                            logger.debug(
                                "Found product link (broad pattern)",
                                pattern=pattern,
                                url=url
                            )
            
            return product_links
            
        except Exception as e:
            logger.error("Error with broad pattern extraction", error=str(e))
            return []
    
    def _construct_urls_from_content(self, content: str) -> List[str]:
        """
        Final fallback: construct URLs based on product names found in content.
        
        Args:
            content: Page content
            
        Returns:
            List[str]: Constructed product URLs
        """
        try:
            product_links = []
            content_lower = content.lower()
            
            # Common product name patterns that might appear in content
            product_indicators = [
                'stitched rectangle frames',
                'rectangle frames',
                'stitched frames'
            ]
            
            for indicator in product_indicators:
                if indicator in content_lower:
                    # Construct likely URL based on product name
                    url_slug = indicator.replace(' ', '-')
                    constructed_url = f"https://www.lawnfawn.com/products/{url_slug}"
                    
                    if constructed_url not in product_links:
                        product_links.append(constructed_url)
                        logger.debug(
                            "Constructed product URL from content",
                            indicator=indicator,
                            url=constructed_url
                        )
                    break
            
            return product_links
            
        except Exception as e:
            logger.error("Error constructing URLs from content", error=str(e))
            return []
    
    async def scrape_product_page(self, product_url: str) -> ProductData:
        """
        Scrape individual product page for detailed information.
        
        Args:
            product_url: Product page URL
            
        Returns:
            ProductData: Extracted product information
            
        Raises:
            ScrapingError: If scraping fails
        """
        logger.info("Starting product page scrape", product_url=product_url)
        
        try:
            # Scrape product page
            response = await self.firecrawl_client.scrape_page(product_url)
            
            if not response.success:
                raise ScrapingError(
                    f"Failed to scrape product page: {response.error_message}",
                    product_url=product_url
                )
            
            # Parse product page content
            product_data = self.extract_product_data(response.content, product_url)
            product_data.raw_response = response.raw_data
            
            logger.info(
                "Product page scrape completed",
                product_url=product_url,
                product_name=product_data.name,
                images_found=len(product_data.image_urls),
                processing_time_ms=response.processing_time_ms
            )
            
            return product_data
            
        except ScrapingError:
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during product scraping",
                product_url=product_url,
                error=str(e)
            )
            raise ScrapingError(
                f"Product scraping failed: {str(e)}",
                product_url=product_url
            )
    
    def extract_product_data(self, html_content: str, product_url: str) -> ProductData:
        """
        Extract product data from product page content.
        
        Firecrawl returns markdown/text format, so we need to use both
        HTML parsing and text pattern matching.
        
        Args:
            html_content: Content from product page (markdown/text format)
            product_url: Product page URL
            
        Returns:
            ProductData: Extracted product information
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract product name (try HTML selectors first)
            name_selectors = [
                'h1.product-title',
                'h1.product__title',
                '.product-single__title',
                'h1',
                '.product-name'
            ]
            
            product_name = "Unknown Product"
            for selector in name_selectors:
                name_element = soup.select_one(selector)
                if name_element:
                    product_name = name_element.get_text(strip=True)
                    break
            
            # If no HTML name found, try extracting from text content
            if product_name == "Unknown Product":
                # Look for product name patterns in text content
                content_lines = html_content.split('\n')
                
                # Try to find the product name from URL slug
                url_parts = product_url.split('/')
                if 'products' in url_parts:
                    product_index = url_parts.index('products')
                    if product_index + 1 < len(url_parts):
                        url_slug = url_parts[product_index + 1]
                        # Convert URL slug to readable name
                        product_name = url_slug.replace('-', ' ').title()
                        logger.debug(
                            "Extracted product name from URL slug",
                            url_slug=url_slug,
                            product_name=product_name
                        )
                
                # Try to find product name in content patterns
                if product_name == "Unknown Product":
                    # Look for title patterns in content
                    title_patterns = [
                        r'^# (.+)$',  # Markdown h1
                        r'^\*\*(.+)\*\*$',  # Bold text
                        r'^(.+) – Lawn Fawn$',  # Common title format
                    ]
                    
                    for line in content_lines[:10]:  # Check first 10 lines
                        line = line.strip()
                        for pattern in title_patterns:
                            match = re.match(pattern, line)
                            if match:
                                potential_name = match.group(1).strip()
                                if len(potential_name) > 3 and not potential_name.lower().startswith(('skip', 'quick', 'post')):
                                    product_name = potential_name
                                    logger.debug(
                                        "Extracted product name from content pattern",
                                        pattern=pattern,
                                        product_name=product_name
                                    )
                                    break
                        if product_name != "Unknown Product":
                            break
            
            # Extract description (try multiple selectors)
            desc_selectors = [
                '.product-description',
                '.product__description',
                '.product-single__description',
                '.description',
                '.product-content'
            ]
            
            description = ""
            for selector in desc_selectors:
                desc_element = soup.select_one(selector)
                if desc_element:
                    description = desc_element.get_text(strip=True)
                    break
            
            # Extract SKU for validation (try multiple approaches)
            found_sku = ""
            
            # Look for SKU in specific elements
            sku_selectors = [
                '.sku',
                '.product-sku',
                '.variant-sku',
                '[data-sku]'
            ]
            
            for selector in sku_selectors:
                sku_element = soup.select_one(selector)
                if sku_element:
                    found_sku = sku_element.get_text(strip=True)
                    break
            
            # If no SKU found in elements, search in text content
            if not found_sku:
                sku_pattern = re.compile(r'LF[-]?\d+', re.IGNORECASE)
                sku_match = sku_pattern.search(html_content)
                if sku_match:
                    found_sku = sku_match.group(0)
            
            # Extract image URLs with enhanced metadata
            image_urls = []
            image_metadata = []
            
            # Look for product images
            img_selectors = [
                '.product-single__photos img',
                '.product__media img',
                '.product-images img',
                '.product-gallery img',
                'img[src*="product"]',
                'img[data-src*="product"]'
            ]
            
            processed_urls = set()
            
            for selector in img_selectors:
                for img in soup.select(selector):
                    src = img.get('src') or img.get('data-src') or img.get('data-original')
                    
                    if src and self._is_product_image(src):
                        # Convert relative URLs to absolute
                        if src.startswith('/'):
                            src = f"https://www.lawnfawn.com{src}"
                        elif src.startswith('//'):
                            src = f"https:{src}"
                        
                        if src not in processed_urls:
                            processed_urls.add(src)
                            image_urls.append(src)
                            
                            # Collect metadata for future image download task
                            metadata = {
                                'url': src,
                                'alt_text': img.get('alt', ''),
                                'title': img.get('title', ''),
                                'width': img.get('width'),
                                'height': img.get('height'),
                                'class': img.get('class', []),
                                'data_attributes': {k: v for k, v in img.attrs.items() if k.startswith('data-')},
                                'estimated_type': self._estimate_image_type(img, src),
                                'quality_indicators': self._assess_image_quality_indicators(img, src)
                            }
                            image_metadata.append(metadata)
            
            logger.debug(
                "Extracted product data",
                product_name=product_name,
                description_length=len(description),
                found_sku=found_sku,
                images_count=len(image_urls)
            )
            
            return ProductData(
                name=product_name,
                description=description,
                sku=found_sku,
                image_urls=image_urls,
                product_url=product_url,
                image_metadata=image_metadata
            )
            
        except Exception as e:
            logger.error(
                "Error extracting product data",
                product_url=product_url,
                error=str(e)
            )
            # Return minimal data rather than failing completely
            return ProductData(
                name="Unknown Product",
                description="",
                sku="",
                image_urls=[],
                product_url=product_url,
                image_metadata=[]
            )
    
    def _is_product_image(self, src: str) -> bool:
        """Check if URL appears to be a product image."""
        src_lower = src.lower()
        
        # Include images that contain product-related keywords
        product_indicators = ['product', 'cdn', 'files', 'images']
        
        # Exclude common non-product images
        exclude_indicators = ['logo', 'icon', 'banner', 'footer', 'header', 'nav']
        
        has_product_indicator = any(indicator in src_lower for indicator in product_indicators)
        has_exclude_indicator = any(indicator in src_lower for indicator in exclude_indicators)
        
        return has_product_indicator and not has_exclude_indicator
    
    def _estimate_image_type(self, img_element, src_url: str) -> str:
        """
        Estimate image type based on element attributes and URL.
        
        Args:
            img_element: BeautifulSoup img element
            src_url: Image source URL
            
        Returns:
            str: Estimated image type (main, thumbnail, detail, gallery, etc.)
        """
        # Check class names for type indicators
        classes = img_element.get('class', [])
        class_str = ' '.join(classes).lower()
        
        # Check for main product image indicators
        if any(indicator in class_str for indicator in ['main', 'primary', 'hero', 'featured']):
            return 'main'
        
        # Check for thumbnail indicators
        if any(indicator in class_str for indicator in ['thumb', 'small', 'mini', 'preview']):
            return 'thumbnail'
        
        # Check for gallery indicators
        if any(indicator in class_str for indicator in ['gallery', 'additional', 'alternate']):
            return 'gallery'
        
        # Check for detail/zoom indicators
        if any(indicator in class_str for indicator in ['zoom', 'large', 'detail', 'full']):
            return 'detail'
        
        # Check URL patterns
        url_lower = src_url.lower()
        if any(pattern in url_lower for pattern in ['thumb', 'small', '_s.', '_sm.']):
            return 'thumbnail'
        elif any(pattern in url_lower for pattern in ['large', 'big', '_l.', '_lg.']):
            return 'detail'
        elif any(pattern in url_lower for pattern in ['main', 'primary', 'hero']):
            return 'main'
        
        # Default to gallery if no specific type detected
        return 'gallery'
    
    def _assess_image_quality_indicators(self, img_element, src_url: str) -> Dict[str, Any]:
        """
        Assess image quality indicators for future download prioritization.
        
        Args:
            img_element: BeautifulSoup img element
            src_url: Image source URL
            
        Returns:
            Dict[str, Any]: Quality indicators and metadata
        """
        quality_indicators = {
            'has_dimensions': False,
            'estimated_size': 'unknown',
            'format_quality': 'unknown',
            'resolution_hints': [],
            'download_priority': 50  # Default priority (0-100)
        }
        
        # Check for dimension attributes
        width = img_element.get('width')
        height = img_element.get('height')
        
        if width and height:
            quality_indicators['has_dimensions'] = True
            try:
                w, h = int(width), int(height)
                if w >= 800 or h >= 800:
                    quality_indicators['estimated_size'] = 'large'
                    quality_indicators['download_priority'] = 80
                elif w >= 400 or h >= 400:
                    quality_indicators['estimated_size'] = 'medium'
                    quality_indicators['download_priority'] = 60
                else:
                    quality_indicators['estimated_size'] = 'small'
                    quality_indicators['download_priority'] = 30
            except ValueError:
                pass
        
        # Analyze URL for quality hints
        url_lower = src_url.lower()
        
        # Format quality assessment
        if url_lower.endswith('.jpg') or url_lower.endswith('.jpeg'):
            quality_indicators['format_quality'] = 'good'
        elif url_lower.endswith('.png'):
            quality_indicators['format_quality'] = 'excellent'
        elif url_lower.endswith('.webp'):
            quality_indicators['format_quality'] = 'excellent'
        elif url_lower.endswith('.gif'):
            quality_indicators['format_quality'] = 'poor'
        
        # Resolution hints from URL
        resolution_patterns = [
            (r'(\d+)x(\d+)', 'explicit_dimensions'),
            (r'_(\d+)w', 'width_hint'),
            (r'_(\d+)h', 'height_hint'),
            (r'@(\d+)x', 'retina_multiplier')
        ]
        
        for pattern, hint_type in resolution_patterns:
            matches = re.findall(pattern, url_lower)
            if matches:
                quality_indicators['resolution_hints'].append({
                    'type': hint_type,
                    'values': matches
                })
        
        # Adjust priority based on URL quality indicators
        if any(indicator in url_lower for indicator in ['hd', 'high', 'quality', '1080', '720']):
            quality_indicators['download_priority'] += 20
        elif any(indicator in url_lower for indicator in ['low', 'compressed', 'thumb']):
            quality_indicators['download_priority'] -= 20
        
        # Ensure priority stays within bounds
        quality_indicators['download_priority'] = max(0, min(100, quality_indicators['download_priority']))
        
        return quality_indicators
    
    def calculate_confidence_score(
        self, 
        original_sku: str, 
        found_sku: str, 
        search_results_count: int, 
        method: str
    ) -> int:
        """
        Calculate confidence score based on match quality.
        
        Args:
            original_sku: Original SKU from invoice
            found_sku: SKU found on product page
            search_results_count: Number of search results
            method: Matching method used
            
        Returns:
            int: Confidence score (0-100)
        """
        try:
            # Extract numeric parts for comparison
            original_numeric = self.extract_numeric_sku(original_sku)
            found_numeric = self.extract_numeric_sku(found_sku) if found_sku else None
            
            # Exact SKU match
            if original_numeric and found_numeric and original_numeric == found_numeric:
                logger.debug(
                    "Exact SKU match",
                    original_sku=original_sku,
                    found_sku=found_sku,
                    confidence=self.confidence_scores['exact_match']
                )
                return self.confidence_scores['exact_match']
            
            # First result with SKU match (but not exact)
            if search_results_count > 0 and found_numeric:
                logger.debug(
                    "First result with SKU",
                    original_sku=original_sku,
                    found_sku=found_sku,
                    confidence=self.confidence_scores['first_result_match']
                )
                return self.confidence_scores['first_result_match']
            
            # First result without SKU match
            if search_results_count > 0:
                logger.debug(
                    "First result without SKU match",
                    original_sku=original_sku,
                    found_sku=found_sku,
                    confidence=self.confidence_scores['first_result_no_match']
                )
                return self.confidence_scores['first_result_no_match']
            
            # Fallback methods
            logger.debug(
                "Fallback confidence score",
                original_sku=original_sku,
                found_sku=found_sku,
                confidence=self.confidence_scores['fallback']
            )
            return self.confidence_scores['fallback']
            
        except Exception as e:
            logger.error(
                "Error calculating confidence score",
                original_sku=original_sku,
                found_sku=found_sku,
                error=str(e)
            )
            return self.confidence_scores['fallback']
    
    async def match_product(self, product: Product) -> EnrichmentData:
        """
        Match LawnFawn product using SKU-based search strategy.
        
        Args:
            product: Product to match
            
        Returns:
            EnrichmentData: Complete enrichment data with confidence score
            
        Raises:
            SKUExtractionError: If SKU cannot be extracted
            SearchError: If search fails
            ScrapingError: If product page scraping fails
        """
        start_time = time.time()
        
        logger.info(
            "Starting product matching",
            product_id=str(product.id),
            supplier_sku=product.supplier_sku
        )
        
        try:
            # Extract numeric SKU
            numeric_sku = self.extract_numeric_sku(product.supplier_sku)
            if not numeric_sku:
                raise SKUExtractionError(
                    f"Could not extract numeric SKU from: {product.supplier_sku}",
                    supplier_sku=product.supplier_sku
                )
            
            # Construct search URL
            search_url = self.build_search_url(numeric_sku)
            
            # Perform search
            search_results = await self.search_products(search_url)
            
            if not search_results.product_links:
                raise SearchError(
                    f"No search results found for SKU: {numeric_sku}",
                    search_url=search_url,
                    sku=numeric_sku
                )
            
            # Try first result with fallback logic
            product_data = None
            successful_url = None
            
            for i, product_url in enumerate(search_results.product_links[:3]):  # Try up to 3 results
                try:
                    logger.info(
                        "Attempting to scrape product URL",
                        url=product_url,
                        attempt=i+1,
                        total_links=len(search_results.product_links)
                    )
                    
                    product_data = await self.scrape_product_page(product_url)
                    successful_url = product_url
                    
                    logger.info(
                        "Successfully scraped product page",
                        url=product_url,
                        product_name=product_data.name,
                        attempt=i+1
                    )
                    break
                    
                except ScrapingError as e:
                    logger.warning(
                        "Failed to scrape product URL, trying next",
                        url=product_url,
                        attempt=i+1,
                        error=str(e)
                    )
                    
                    # If this was the last URL, re-raise the error
                    if i == len(search_results.product_links[:3]) - 1:
                        raise
                    continue
            
            if not product_data or not successful_url:
                raise ScrapingError(
                    f"Failed to scrape any product pages from {len(search_results.product_links)} search results",
                    product_url=search_results.product_links[0] if search_results.product_links else None
                )
            
            # Validate SKU match and calculate confidence
            confidence_score = self.calculate_confidence_score(
                original_sku=product.supplier_sku,
                found_sku=product_data.sku,
                search_results_count=len(search_results.product_links),
                method="search_first_result"
            )
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                "Product matching completed",
                product_id=str(product.id),
                confidence_score=confidence_score,
                processing_time_ms=processing_time_ms,
                images_found=len(product_data.image_urls)
            )
            
            return EnrichmentData(
                search_url=search_url,
                product_url=successful_url,
                product_name=product_data.name,
                description=product_data.description,
                image_urls=product_data.image_urls,
                confidence_score=confidence_score,
                method=EnrichmentMethod.SEARCH_FIRST_RESULT,
                raw_response={
                    "search_response": search_results.raw_response,
                    "product_response": product_data.raw_response
                },
                image_metadata=product_data.image_metadata,
                processing_time_ms=processing_time_ms
            )
            
        except (SKUExtractionError, SearchError, ScrapingError):
            # Re-raise specific enrichment errors
            raise
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "Unexpected error during product matching",
                product_id=str(product.id),
                supplier_sku=product.supplier_sku,
                error=str(e),
                processing_time_ms=processing_time_ms
            )
            raise ScrapingError(
                f"Product matching failed: {str(e)}",
                product_url=getattr(product, 'scraped_url', None)
            )


# Global matcher instance
_lawnfawn_matcher: Optional[LawnFawnMatcher] = None


def get_lawnfawn_matcher(config: Optional[EnrichmentConfig] = None) -> LawnFawnMatcher:
    """
    Get the global LawnFawn matcher instance.
    
    Args:
        config: Optional enrichment configuration
        
    Returns:
        LawnFawnMatcher: Configured LawnFawn matcher instance
    """
    global _lawnfawn_matcher
    
    if _lawnfawn_matcher is None:
        _lawnfawn_matcher = LawnFawnMatcher(config)
    
    return _lawnfawn_matcher


def reset_lawnfawn_matcher() -> None:
    """Reset the global LawnFawn matcher instance (useful for testing)."""
    global _lawnfawn_matcher
    _lawnfawn_matcher = None
