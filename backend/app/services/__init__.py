"""
Services package for the Universal Product Automation System.

This package contains business logic services and database operations.
"""

from .database_service import DatabaseService, get_database_service

__all__ = [
    "DatabaseService",
    "get_database_service",
]
