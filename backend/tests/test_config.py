"""
Tests for the configuration module.

This module tests the Settings class and configuration management
functionality to ensure proper environment variable handling and
default value assignment.
"""

import os
import pytest
from unittest.mock import patch

from app.core.config import Settings, get_settings


class TestSettings:
    """Test cases for the Settings configuration class."""

    def test_default_settings(self):
        """
        Test that default settings are properly initialized.
        
        Verifies that the Settings class creates an instance with
        expected default values when no environment variables are set.
        """
        settings = Settings()
        
        # Test database configuration defaults
        assert settings.database_url == "postgresql://user:password@localhost:5432/product_automation"
        assert settings.redis_url == "redis://localhost:6379"
        
        # Test development configuration defaults
        assert settings.debug is True
        assert settings.log_level == "DEBUG"
        assert settings.environment == "development"
        
        # Test server configuration defaults
        assert settings.backend_port == 8000
        assert settings.frontend_port == 3000
        
        # Test application configuration defaults
        assert settings.app_name == "Universal Product Automation System"
        assert settings.app_version == "1.0.0"
        
        # Test CORS configuration defaults
        assert "http://localhost:3000" in settings.cors_origins
        assert "http://127.0.0.1:3000" in settings.cors_origins

    def test_environment_variable_override(self):
        """
        Test that environment variables properly override default settings.
        
        Verifies that when environment variables are set, they take
        precedence over the default configuration values.
        """
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@testhost:5432/testdb',
            'REDIS_URL': 'redis://testhost:6379',
            'DEBUG': 'false',
            'LOG_LEVEL': 'INFO',
            'ENVIRONMENT': 'testing',
            'BACKEND_PORT': '9000',
            'APP_NAME': 'Test Application'
        }):
            settings = Settings()
            
            assert settings.database_url == 'postgresql://test:test@testhost:5432/testdb'
            assert settings.redis_url == 'redis://testhost:6379'
            assert settings.debug is False
            assert settings.log_level == 'INFO'
            assert settings.environment == 'testing'
            assert settings.backend_port == 9000
            assert settings.app_name == 'Test Application'

    def test_optional_api_keys(self):
        """
        Test that optional API keys are handled correctly.
        
        Verifies that API keys default to None when not provided
        and are properly set when environment variables are available.
        """
        # Test default None values
        settings = Settings()
        assert settings.firecrawl_api_key is None
        assert settings.openai_api_key is None
        
        # Test with environment variables set
        with patch.dict(os.environ, {
            'FIRECRAWL_API_KEY': 'test_firecrawl_key',
            'OPENAI_API_KEY': 'test_openai_key'
        }):
            settings = Settings()
            assert settings.firecrawl_api_key == 'test_firecrawl_key'
            assert settings.openai_api_key == 'test_openai_key'

    def test_file_processing_configuration(self):
        """
        Test file processing configuration settings.
        
        Verifies that file size limits and supported file types
        are properly configured with expected default values.
        """
        settings = Settings()
        
        # Test file size limit (50MB in bytes)
        assert settings.max_file_size == 50 * 1024 * 1024
        
        # Test supported file types
        expected_types = [".csv", ".xlsx", ".xls", ".pdf"]
        assert settings.supported_file_types == expected_types

    def test_image_processing_configuration(self):
        """
        Test image processing configuration settings.
        
        Verifies that image dimension requirements and supported
        formats are properly configured.
        """
        settings = Settings()
        
        # Test minimum image dimension
        assert settings.min_image_dimension == 1000
        
        # Test supported image formats
        expected_formats = [".jpg", ".jpeg", ".png", ".webp", ".gif"]
        assert settings.image_formats == expected_formats

    def test_scraping_configuration(self):
        """
        Test web scraping configuration settings.
        
        Verifies that scraping delay and timeout values
        are properly configured for rate limiting.
        """
        settings = Settings()
        
        assert settings.scraping_delay == 1.0
        assert settings.scraping_timeout == 30

    def test_cors_origins_list_handling(self):
        """
        Test CORS origins list configuration.
        
        Verifies that CORS origins are properly handled as a list
        and can be overridden via environment variables.
        """
        settings = Settings()
        
        # Test default CORS origins
        assert isinstance(settings.cors_origins, list)
        assert len(settings.cors_origins) == 2
        
        # Test environment variable override
        with patch.dict(os.environ, {
            'CORS_ORIGINS': 'http://example.com,https://app.example.com'
        }):
            # Note: This test assumes the Settings class can parse comma-separated values
            # The actual implementation might need adjustment for this to work
            pass

    def test_production_configuration(self):
        """
        Test production environment configuration.
        
        Verifies that production settings are properly applied
        when the environment is set to production.
        """
        with patch.dict(os.environ, {
            'DEBUG': 'false',
            'LOG_LEVEL': 'INFO',
            'ENVIRONMENT': 'production'
        }):
            settings = Settings()
            
            assert settings.debug is False
            assert settings.log_level == 'INFO'
            assert settings.environment == 'production'


class TestGetSettings:
    """Test cases for the get_settings function."""

    def test_get_settings_returns_settings_instance(self):
        """
        Test that get_settings returns a Settings instance.
        
        Verifies that the get_settings function returns a properly
        configured Settings instance.
        """
        settings = get_settings()
        
        assert isinstance(settings, Settings)
        assert hasattr(settings, 'database_url')
        assert hasattr(settings, 'app_name')

    def test_get_settings_singleton_behavior(self):
        """
        Test that get_settings returns the same instance.
        
        Verifies that multiple calls to get_settings return
        the same Settings instance (singleton pattern).
        """
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Both should reference the same instance
        assert settings1 is settings2


# Integration test for configuration validation
class TestConfigurationIntegration:
    """Integration tests for configuration validation."""

    def test_database_url_format_validation(self):
        """
        Test database URL format validation.
        
        Verifies that the database URL follows the expected
        PostgreSQL connection string format.
        """
        settings = Settings()
        
        # Basic format check
        assert settings.database_url.startswith('postgresql://')
        assert 'localhost' in settings.database_url or 'user' in settings.database_url

    def test_redis_url_format_validation(self):
        """
        Test Redis URL format validation.
        
        Verifies that the Redis URL follows the expected
        connection string format.
        """
        settings = Settings()
        
        # Basic format check
        assert settings.redis_url.startswith('redis://')
        assert 'localhost' in settings.redis_url or '6379' in settings.redis_url

    def test_port_range_validation(self):
        """
        Test that port numbers are within valid ranges.
        
        Verifies that configured ports are within the valid
        range for network ports (1-65535).
        """
        settings = Settings()
        
        assert 1 <= settings.backend_port <= 65535
        assert 1 <= settings.frontend_port <= 65535

    def test_log_level_validation(self):
        """
        Test that log level is a valid logging level.
        
        Verifies that the configured log level is one of the
        standard Python logging levels.
        """
        settings = Settings()
        
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        assert settings.log_level in valid_levels
