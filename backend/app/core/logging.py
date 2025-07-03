"""
Logging configuration for the Universal Product Automation System.

This module provides structured logging configuration using structlog
for consistent, machine-readable log output.
"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.types import Processor


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging for the application.
    
    Sets up structlog with JSON output for production and human-readable
    output for development. Includes timestamp, log level, logger name,
    and structured data.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    
    # Determine if we're in development mode
    is_development = log_level == "DEBUG"
    
    # Configure processors for structured logging
    processors: list[Processor] = [
        # Filter by log level
        structlog.stdlib.filter_by_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Add log level
        structlog.stdlib.add_log_level,
        # Process positional arguments
        structlog.stdlib.PositionalArgumentsFormatter(),
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Add stack info for exceptions
        structlog.processors.StackInfoRenderer(),
        # Format exception info
        structlog.processors.format_exc_info,
        # Decode unicode
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add appropriate final processor based on environment
    if is_development:
        # Human-readable output for development
        processors.append(
            structlog.dev.ConsoleRenderer(colors=True)
        )
    else:
        # JSON output for production
        processors.append(
            structlog.processors.JSONRenderer()
        )
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Set log levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("aioredis").setLevel(logging.INFO)


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name. If None, uses the calling module's name.
        
    Returns:
        BoundLogger: Configured structured logger instance.
    """
    return structlog.get_logger(name)


def log_request_info(
    method: str,
    url: str,
    status_code: int,
    duration_ms: float,
    **kwargs: Any
) -> None:
    """
    Log HTTP request information in a structured format.
    
    Args:
        method: HTTP method (GET, POST, etc.).
        url: Request URL.
        status_code: HTTP status code.
        duration_ms: Request duration in milliseconds.
        **kwargs: Additional context to include in log.
    """
    logger = get_logger("http")
    
    log_data = {
        "method": method,
        "url": url,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        **kwargs
    }
    
    if status_code >= 500:
        logger.error("HTTP request failed", **log_data)
    elif status_code >= 400:
        logger.warning("HTTP request error", **log_data)
    else:
        logger.info("HTTP request completed", **log_data)


def log_database_operation(
    operation: str,
    table: str,
    duration_ms: float,
    affected_rows: int = None,
    **kwargs: Any
) -> None:
    """
    Log database operation information in a structured format.
    
    Args:
        operation: Database operation (SELECT, INSERT, UPDATE, DELETE).
        table: Database table name.
        duration_ms: Operation duration in milliseconds.
        affected_rows: Number of affected rows (for write operations).
        **kwargs: Additional context to include in log.
    """
    logger = get_logger("database")
    
    log_data = {
        "operation": operation,
        "table": table,
        "duration_ms": round(duration_ms, 2),
        **kwargs
    }
    
    if affected_rows is not None:
        log_data["affected_rows"] = affected_rows
    
    logger.info("Database operation completed", **log_data)


def log_scraping_operation(
    url: str,
    success: bool,
    duration_ms: float,
    status_code: int = None,
    error: str = None,
    **kwargs: Any
) -> None:
    """
    Log web scraping operation information in a structured format.
    
    Args:
        url: Scraped URL.
        success: Whether the scraping was successful.
        duration_ms: Operation duration in milliseconds.
        status_code: HTTP status code (if applicable).
        error: Error message (if failed).
        **kwargs: Additional context to include in log.
    """
    logger = get_logger("scraping")
    
    log_data = {
        "url": url,
        "success": success,
        "duration_ms": round(duration_ms, 2),
        **kwargs
    }
    
    if status_code is not None:
        log_data["status_code"] = status_code
    
    if error:
        log_data["error"] = error
        logger.error("Scraping operation failed", **log_data)
    else:
        logger.info("Scraping operation completed", **log_data)


def log_processing_batch(
    batch_id: str,
    supplier: str,
    total_items: int,
    processed_items: int,
    failed_items: int,
    duration_ms: float,
    **kwargs: Any
) -> None:
    """
    Log batch processing information in a structured format.
    
    Args:
        batch_id: Unique batch identifier.
        supplier: Supplier name.
        total_items: Total number of items in batch.
        processed_items: Number of successfully processed items.
        failed_items: Number of failed items.
        duration_ms: Processing duration in milliseconds.
        **kwargs: Additional context to include in log.
    """
    logger = get_logger("processing")
    
    success_rate = (processed_items / total_items * 100) if total_items > 0 else 0
    
    log_data = {
        "batch_id": batch_id,
        "supplier": supplier,
        "total_items": total_items,
        "processed_items": processed_items,
        "failed_items": failed_items,
        "success_rate": round(success_rate, 2),
        "duration_ms": round(duration_ms, 2),
        **kwargs
    }
    
    if failed_items > 0:
        logger.warning("Batch processing completed with failures", **log_data)
    else:
        logger.info("Batch processing completed successfully", **log_data)
