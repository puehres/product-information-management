# Universal Product Automation System - Backend

FastAPI-based backend for the Universal Product Automation System, providing APIs for product data management, web scraping, image processing, and multi-language content generation.

## Features

- **Product Management**: CRUD operations for product data with supplier integration
- **Web Scraping**: Automated data extraction from supplier websites using Firecrawl API
- **Image Processing**: Image optimization, validation, and format conversion
- **Translation**: Multi-language content generation using OpenAI API
- **Batch Processing**: Efficient handling of large product datasets
- **Structured Logging**: Comprehensive logging with structured output
- **Type Safety**: Full type hints and validation using Pydantic

## Technology Stack

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Caching**: Redis for session and data caching
- **Image Processing**: Pillow for image manipulation
- **HTTP Client**: httpx and aiohttp for web requests
- **Logging**: structlog for structured logging
- **Testing**: pytest with async support
- **Code Quality**: black, isort, mypy, flake8

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration management
│   │   └── logging.py         # Logging configuration
│   ├── api/                   # API route handlers (future)
│   ├── models/                # Database models (future)
│   ├── services/              # Business logic (future)
│   └── utils/                 # Utility functions (future)
├── tests/                     # Test files
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Project configuration
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## Quick Start

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 12 or higher
- Redis 6 or higher

### Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone https://github.com/puehres/product-information-management.git
   cd product-information-management/backend
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your actual configuration values
   ```

5. **Start the development server**:
   ```bash
   python -m app.main
   # Or using uvicorn directly:
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Configuration

The application uses environment variables for configuration. Copy `.env.example` to `.env` and update the values:

### Required Configuration

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/product_automation

# Redis
REDIS_URL=redis://localhost:6379
```

### Optional Configuration

```bash
# API Keys (for future features)
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Development
DEBUG=true
LOG_LEVEL=DEBUG
ENVIRONMENT=development

# Server
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## API Endpoints

### Current Endpoints

- `GET /` - Root endpoint with application information
- `GET /health` - Health check endpoint
- `GET /api/v1/info` - Detailed API information

### Future Endpoints (Planned)

- `GET /api/v1/products` - List products
- `POST /api/v1/products` - Create product
- `GET /api/v1/suppliers` - List suppliers
- `POST /api/v1/scraping/start` - Start scraping job
- `POST /api/v1/processing/batch` - Process batch data

## Development

### Code Quality

The project uses several tools to maintain code quality:

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Type checking
mypy app/

# Linting
flake8 app/ tests/
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_config.py
```

### Project Configuration

The project uses `pyproject.toml` for configuration:

- **Black**: Line length 88, Python 3.9+ target
- **isort**: Black-compatible profile
- **mypy**: Strict type checking enabled
- **pytest**: Async mode enabled, structured test discovery

## Logging

The application uses structured logging with different output formats:

- **Development**: Human-readable colored output
- **Production**: JSON format for log aggregation

Log levels and structured data are automatically included:

```python
from app.core.logging import get_logger

logger = get_logger(__name__)
logger.info("Processing batch", batch_id="123", items=100)
```

## Database

### Setup (Future)

```bash
# Initialize database
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

## Deployment

### Docker (Future)

```bash
# Build image
docker build -t product-automation-backend .

# Run container
docker run -p 8000:8000 --env-file .env product-automation-backend
```

### Environment Variables for Production

```bash
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production
DATABASE_URL=postgresql://user:password@prod-db:5432/product_automation
REDIS_URL=redis://prod-redis:6379
```

## Contributing

1. Follow the existing code style and structure
2. Add type hints to all functions
3. Write tests for new features
4. Update documentation as needed
5. Use structured logging for all operations

## License

This project is licensed under the MIT License - see the LICENSE file for details.
