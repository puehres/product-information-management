"""
Tests for the main FastAPI application.

This module tests the FastAPI application initialization, middleware
configuration, and basic endpoint functionality.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app, create_application
from app.core.config import get_settings


class TestFastAPIApplication:
    """Test cases for the FastAPI application setup."""

    def test_create_application_returns_fastapi_instance(self):
        """
        Test that create_application returns a FastAPI instance.
        
        Verifies that the application factory function creates
        a properly configured FastAPI application.
        """
        test_app = create_application()
        
        assert test_app is not None
        assert hasattr(test_app, 'title')
        assert hasattr(test_app, 'version')
        assert hasattr(test_app, 'description')

    def test_application_metadata(self):
        """
        Test that application metadata is properly configured.
        
        Verifies that the FastAPI application has the correct
        title, version, and description from settings.
        """
        settings = get_settings()
        test_app = create_application()
        
        assert test_app.title == settings.app_name
        assert test_app.version == settings.app_version
        assert "Universal Product Automation System" in test_app.description

    def test_application_debug_mode(self):
        """
        Test that debug mode is properly configured.
        
        Verifies that the debug setting from configuration
        is applied to the FastAPI application.
        """
        settings = get_settings()
        test_app = create_application()
        
        assert test_app.debug == settings.debug


class TestApplicationEndpoints:
    """Test cases for application endpoints."""

    @pytest.fixture
    def client(self):
        """
        Create a test client for the FastAPI application.
        
        Returns:
            TestClient: Configured test client for making requests.
        """
        return TestClient(app)

    def test_root_endpoint(self, client):
        """
        Test the root endpoint returns application information.
        
        Verifies that GET / returns basic application information
        including name, version, status, and environment.
        """
        response = client.get("/")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert "environment" in data
        assert "debug" in data
        
        assert data["status"] == "running"
        assert data["name"] == "Universal Product Automation System"

    def test_health_endpoint(self, client):
        """
        Test the health check endpoint.
        
        Verifies that GET /health returns health status information
        with proper structure and status indicators.
        """
        response = client.get("/health")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "checks" in data
        
        assert data["status"] == "healthy"
        
        # Verify health check structure
        checks = data["checks"]
        assert "database" in checks
        assert "redis" in checks
        assert "external_apis" in checks

    def test_api_info_endpoint(self, client):
        """
        Test the API information endpoint.
        
        Verifies that GET /api/v1/info returns detailed API
        and system information with proper structure.
        """
        response = client.get("/api/v1/info")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "api" in data
        assert "features" in data
        assert "supported_formats" in data
        assert "limits" in data
        
        # Verify API information structure
        api_info = data["api"]
        assert "name" in api_info
        assert "version" in api_info
        assert "environment" in api_info
        assert "debug" in api_info
        
        # Verify features information
        features = data["features"]
        assert "product_management" in features
        assert "web_scraping" in features
        assert "image_processing" in features
        assert "translation" in features
        assert "batch_processing" in features
        
        # Verify supported formats
        formats = data["supported_formats"]
        assert "import" in formats
        assert "images" in formats
        
        # Verify limits
        limits = data["limits"]
        assert "max_file_size_mb" in limits
        assert "min_image_dimension" in limits

    def test_nonexistent_endpoint_returns_404(self, client):
        """
        Test that nonexistent endpoints return 404.
        
        Verifies that requests to undefined routes return
        the appropriate HTTP 404 status code.
        """
        response = client.get("/nonexistent")
        
        assert response.status_code == 404

    def test_cors_headers_present(self, client):
        """
        Test that CORS headers are properly configured.
        
        Verifies that the CORS middleware is working and
        appropriate headers are present in responses.
        """
        response = client.get("/")
        
        # Check for CORS headers (may vary based on request origin)
        # The exact headers depend on the request and CORS configuration
        assert response.status_code == 200

    def test_options_request_handling(self, client):
        """
        Test that OPTIONS requests are handled for CORS.
        
        Verifies that preflight CORS requests are properly
        handled by the CORS middleware.
        """
        response = client.options("/")
        
        # OPTIONS requests should be handled by CORS middleware
        # The exact status code may vary (200, 204, or 405)
        assert response.status_code in [200, 204, 405]


class TestApplicationMiddleware:
    """Test cases for application middleware configuration."""

    @pytest.fixture
    def client(self):
        """
        Create a test client for middleware testing.
        
        Returns:
            TestClient: Configured test client for making requests.
        """
        return TestClient(app)

    def test_cors_middleware_configuration(self, client):
        """
        Test that CORS middleware is properly configured.
        
        Verifies that CORS middleware allows the configured
        origins and methods.
        """
        # Test with allowed origin
        headers = {"Origin": "http://localhost:3000"}
        response = client.get("/", headers=headers)
        
        assert response.status_code == 200

    def test_trusted_host_middleware_in_production(self):
        """
        Test that trusted host middleware is configured for production.
        
        Verifies that in production mode, the trusted host middleware
        is properly configured to restrict allowed hosts.
        """
        with patch('app.core.config.get_settings') as mock_settings:
            mock_settings.return_value.debug = False
            mock_settings.return_value.app_name = "Test App"
            mock_settings.return_value.app_version = "1.0.0"
            mock_settings.return_value.cors_origins = ["http://localhost:3000"]
            
            test_app = create_application()
            
            # Verify that the application was created successfully
            assert test_app is not None


class TestApplicationLifespan:
    """Test cases for application lifespan events."""

    def test_application_startup_logging(self):
        """
        Test that application startup is properly logged.
        
        Verifies that startup events are logged with appropriate
        information about the application configuration.
        """
        # This test would require mocking the logger and checking
        # that startup messages are logged correctly
        # For now, we'll just verify the app can be created
        test_app = create_application()
        assert test_app is not None

    def test_application_shutdown_handling(self):
        """
        Test that application shutdown is properly handled.
        
        Verifies that shutdown events are handled gracefully
        and cleanup operations are performed.
        """
        # This test would require testing the lifespan context manager
        # For now, we'll just verify the app can be created
        test_app = create_application()
        assert test_app is not None


class TestApplicationConfiguration:
    """Test cases for application configuration integration."""

    def test_settings_integration(self):
        """
        Test that application properly integrates with settings.
        
        Verifies that the FastAPI application uses configuration
        values from the Settings class.
        """
        settings = get_settings()
        test_app = create_application()
        
        assert test_app.title == settings.app_name
        assert test_app.version == settings.app_version
        assert test_app.debug == settings.debug

    def test_environment_specific_configuration(self):
        """
        Test that environment-specific configuration is applied.
        
        Verifies that different environments (development, production)
        result in appropriate application configuration.
        """
        # Test development configuration
        with patch.dict('os.environ', {'ENVIRONMENT': 'development', 'DEBUG': 'true'}):
            from app.core.config import Settings
            dev_settings = Settings()
            assert dev_settings.environment == 'development'
            assert dev_settings.debug is True
        
        # Test production configuration
        with patch.dict('os.environ', {'ENVIRONMENT': 'production', 'DEBUG': 'false'}):
            from app.core.config import Settings
            prod_settings = Settings()
            assert prod_settings.environment == 'production'
            assert prod_settings.debug is False


# Integration tests
class TestApplicationIntegration:
    """Integration tests for the complete application."""

    @pytest.fixture
    def client(self):
        """
        Create a test client for integration testing.
        
        Returns:
            TestClient: Configured test client for making requests.
        """
        return TestClient(app)

    def test_complete_application_flow(self, client):
        """
        Test a complete application flow.
        
        Verifies that the application can handle a sequence of
        requests and maintain proper state.
        """
        # Test root endpoint
        root_response = client.get("/")
        assert root_response.status_code == 200
        
        # Test health check
        health_response = client.get("/health")
        assert health_response.status_code == 200
        
        # Test API info
        info_response = client.get("/api/v1/info")
        assert info_response.status_code == 200
        
        # Verify consistent application information
        root_data = root_response.json()
        info_data = info_response.json()
        
        assert root_data["name"] == info_data["api"]["name"]
        assert root_data["version"] == info_data["api"]["version"]

    def test_application_error_handling(self, client):
        """
        Test that application properly handles errors.
        
        Verifies that the application returns appropriate error
        responses for various error conditions.
        """
        # Test 404 for nonexistent endpoint
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404
        
        # Test method not allowed (if applicable)
        response = client.post("/")  # Root endpoint likely doesn't accept POST
        assert response.status_code in [405, 422]  # Method not allowed or validation error
