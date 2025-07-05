"""
Main FastAPI application for the Universal Product Automation System.

This module initializes the FastAPI application with all necessary middleware,
routers, and configuration.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

# Initialize settings and logger
settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application.
    This includes initializing logging, database connections, and cleanup.
    
    Args:
        app: FastAPI application instance.
        
    Yields:
        None: Control back to FastAPI during application runtime.
    """
    # Startup
    logger.info(
        "Starting Universal Product Automation System",
        version=settings.app_version,
        environment=settings.environment,
        debug=settings.debug
    )
    
    # Configure logging based on settings
    configure_logging(settings.log_level)
    
    # TODO: Initialize database connection pool
    # TODO: Initialize Redis connection
    # TODO: Validate API keys and external service connections
    
    logger.info("Application startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Universal Product Automation System")
    
    # TODO: Close database connections
    # TODO: Close Redis connections
    # TODO: Cleanup any background tasks
    
    logger.info("Application shutdown completed")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    
    # Create FastAPI application with lifespan manager
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Universal Product Automation System for managing product data, "
                   "web scraping, image processing, and multi-language content generation.",
        debug=settings.debug,
        lifespan=lifespan,
    )
    
    # Add CORS middleware for frontend communication
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware for security
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", "*.stempelwunderwelt.at"]
        )
    
    # Add API routers
    from app.api import upload
    app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
    
    # TODO: Add additional routers
    # app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
    # app.include_router(suppliers.router, prefix="/api/v1/suppliers", tags=["suppliers"])
    # app.include_router(scraping.router, prefix="/api/v1/scraping", tags=["scraping"])
    # app.include_router(processing.router, prefix="/api/v1/processing", tags=["processing"])
    
    return app


# Create the application instance
app = create_application()


@app.get("/")
async def root():
    """
    Root endpoint providing basic application information.
    
    Returns:
        dict: Application information including name, version, and status.
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "environment": settings.environment,
        "debug": settings.debug,
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        dict: Health status information.
    """
    # TODO: Add actual health checks for database, Redis, external APIs
    return {
        "status": "healthy",
        "timestamp": "2025-01-07T21:40:00Z",  # Will be replaced with actual timestamp
        "version": settings.app_version,
        "checks": {
            "database": "ok",  # TODO: Implement actual database health check
            "redis": "ok",     # TODO: Implement actual Redis health check
            "external_apis": "ok"  # TODO: Implement external API health checks
        }
    }


@app.get("/api/v1/info")
async def api_info():
    """
    API information endpoint providing detailed system information.
    
    Returns:
        dict: Detailed API and system information.
    """
    return {
        "api": {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "debug": settings.debug,
        },
        "features": {
            "product_management": True,
            "web_scraping": True,
            "image_processing": True,
            "translation": True,
            "batch_processing": True,
        },
        "supported_formats": {
            "import": settings.supported_file_types,
            "images": settings.image_formats,
        },
        "limits": {
            "max_file_size_mb": settings.max_file_size // (1024 * 1024),
            "min_image_dimension": settings.min_image_dimension,
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run the application with uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.backend_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
