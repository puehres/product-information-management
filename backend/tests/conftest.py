"""
Pytest configuration and fixtures for the Universal Product Automation System backend.

This module provides shared fixtures and configuration for all backend tests,
including environment variable isolation and mock setup.
"""

import os
import pytest
from unittest.mock import AsyncMock, Mock
from typing import Dict, Any


@pytest.fixture(autouse=True)
def clean_environment():
    """
    Automatically clean environment variables before each test.
    
    This fixture ensures that tests don't interfere with each other
    by clearing sensitive environment variables and restoring them
    after the test completes.
    """
    # Store original environment
    original_env = os.environ.copy()
    
    # List of environment variables that should be cleared for tests
    test_sensitive_vars = [
        'FIRECRAWL_API_KEY',
        'OPENAI_API_KEY',
        'DATABASE_URL',
        'SUPABASE_URL',
        'SUPABASE_SERVICE_KEY',
        'REDIS_URL'
    ]
    
    # Clear test-sensitive variables
    for var in test_sensitive_vars:
        os.environ.pop(var, None)
    
    # Also prevent pydantic from loading .env files during tests
    # by temporarily setting a flag that Settings can check
    os.environ['PYTEST_RUNNING'] = 'true'
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_supabase_client():
    """
    Provide a mock Supabase client for testing.
    
    Returns:
        Mock: A configured mock Supabase client with common methods.
    """
    mock_client = Mock()
    
    # Mock table method chain
    mock_table = Mock()
    mock_select = Mock()
    mock_execute = Mock()
    
    # Configure the method chain
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.execute.return_value = Mock(data=[])
    mock_select.eq.return_value = mock_select
    mock_select.limit.return_value = mock_select
    mock_select.order.return_value = mock_select
    
    # Configure insert/update/delete chains
    mock_table.insert.return_value = mock_execute
    mock_table.update.return_value = mock_execute
    mock_table.delete.return_value = mock_execute
    mock_execute.execute.return_value = Mock(data=[])
    
    return mock_client


@pytest.fixture
def mock_async_supabase_manager():
    """
    Provide a mock async Supabase manager for testing.
    
    Returns:
        Mock: A configured mock SupabaseManager with async methods.
    """
    mock_manager = Mock()
    
    # Configure async methods
    mock_manager.test_connection = AsyncMock(return_value=True)
    mock_manager.health_check = AsyncMock(return_value={
        "status": "healthy",
        "connection_time_ms": 50.0,
        "timestamp": 1641024000.0
    })
    
    return mock_manager


@pytest.fixture
def sample_supplier_data():
    """
    Provide sample supplier data for testing.
    
    Returns:
        Dict[str, Any]: Sample supplier data.
    """
    return {
        "name": "Test Supplier",
        "code": "TEST",
        "website_url": "https://test.com",
        "identifier_type": "sku",
        "active": True
    }


@pytest.fixture
def sample_product_data():
    """
    Provide sample product data for testing.
    
    Returns:
        Dict[str, Any]: Sample product data.
    """
    from uuid import uuid4
    
    return {
        "batch_id": str(uuid4()),
        "supplier_id": str(uuid4()),
        "supplier_sku": "TEST-001",
        "supplier_name": "Test Product",
        "supplier_price_usd": 19.99
    }


@pytest.fixture
def mock_environment_variables():
    """
    Provide a fixture for setting test environment variables.
    
    Returns:
        function: A function to set environment variables for testing.
    """
    def set_env_vars(env_dict: Dict[str, str]):
        """Set environment variables for testing."""
        for key, value in env_dict.items():
            os.environ[key] = value
    
    return set_env_vars


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database connection"
    )


# Async test utilities
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
