# Universal Product Automation System

A comprehensive system for automating product data management, web scraping, image processing, and multi-language content generation. Built with modern technologies for scalability, performance, and maintainability.

## 🚀 Features

### Core Functionality
- **Product Data Management**: Complete CRUD operations with supplier integration
- **Web Scraping**: Automated data extraction from supplier websites using Firecrawl API
- **Image Processing**: Optimization, validation, and format conversion
- **Multi-language Translation**: AI-powered content generation using OpenAI API
- **Batch Processing**: Efficient handling of large product datasets
- **Real-time Updates**: Live status tracking for all operations

### Technical Features
- **Type Safety**: Full TypeScript support across frontend and backend
- **Modern Architecture**: FastAPI backend with Next.js frontend
- **Structured Logging**: Comprehensive logging with structured output
- **Responsive Design**: Mobile-first UI with dark mode support
- **Performance Optimized**: Caching, lazy loading, and optimized queries
- **Testing Coverage**: Comprehensive test suites for reliability

## 🏗️ Architecture

### Technology Stack

#### Backend
- **Framework**: FastAPI 0.104.1 with Python 3.9+
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Caching**: Redis for session and data caching
- **Image Processing**: Pillow for image manipulation
- **HTTP Client**: httpx and aiohttp for web requests
- **Logging**: structlog for structured logging
- **Testing**: pytest with async support

#### Frontend
- **Framework**: Next.js 14.0.4 with React 18
- **Language**: TypeScript 5.3.3 with strict type checking
- **Styling**: Tailwind CSS 3.3.6 with custom design system
- **Components**: Shadcn/UI with Radix UI primitives
- **State Management**: TanStack React Query 5.14.2
- **Forms**: React Hook Form with Zod validation
- **Testing**: Jest with React Testing Library

#### External Services
- **Web Scraping**: Firecrawl API for reliable data extraction
- **AI Translation**: OpenAI API for content generation
- **Image Optimization**: Built-in processing with Pillow

## 📁 Project Structure

```
product-information-management/
├── backend/                   # FastAPI backend application
│   ├── app/
│   │   ├── core/             # Core configuration and logging
│   │   ├── api/              # API route handlers (future)
│   │   ├── models/           # Database models (future)
│   │   ├── services/         # Business logic (future)
│   │   └── utils/            # Utility functions (future)
│   ├── tests/                # Backend tests
│   ├── requirements.txt      # Python dependencies
│   ├── pyproject.toml       # Project configuration
│   └── README.md            # Backend documentation
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/             # Next.js App Router pages
│   │   ├── components/      # Reusable UI components (future)
│   │   ├── lib/             # Utility functions (future)
│   │   ├── hooks/           # Custom React hooks (future)
│   │   └── types/           # TypeScript definitions (future)
│   ├── public/              # Static assets
│   ├── package.json         # Node.js dependencies
│   └── README.md           # Frontend documentation
├── docs/                    # Project documentation (future)
├── scripts/                 # Utility scripts (future)
├── .gitignore              # Git ignore rules
├── LICENSE                 # MIT License
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.9 or higher
- **Node.js**: 18.0.0 or higher
- **PostgreSQL**: 12 or higher
- **Redis**: 6 or higher

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/puehres/product-information-management.git
   cd product-information-management
   ```

2. **Backend Setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Frontend Setup**:
   ```bash
   cd ../frontend
   npm install
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

4. **Start Development Servers**:
   
   **Backend** (Terminal 1):
   ```bash
   cd backend
   python -m app.main
   # Backend available at http://localhost:8000
   ```
   
   **Frontend** (Terminal 2):
   ```bash
   cd frontend
   npm run dev
   # Frontend available at http://localhost:3000
   ```

## ⚙️ Configuration

### Backend Configuration

Copy `backend/.env.example` to `backend/.env` and configure:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/product_automation

# Redis
REDIS_URL=redis://localhost:6379

# API Keys
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Development
DEBUG=true
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

### Frontend Configuration

Copy `frontend/.env.example` to `frontend/.env.local` and configure:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Application Configuration
NEXT_PUBLIC_APP_NAME=Universal Product Automation System
NEXT_PUBLIC_APP_VERSION=1.0.0
```

## 🔗 API Documentation

### Current Endpoints

- **GET** `/` - Application information
- **GET** `/health` - Health check
- **GET** `/api/v1/info` - Detailed API information

### Planned Endpoints

#### Product Management
- **GET** `/api/v1/products` - List products with filtering and pagination
- **POST** `/api/v1/products` - Create new product
- **GET** `/api/v1/products/{id}` - Get product details
- **PUT** `/api/v1/products/{id}` - Update product
- **DELETE** `/api/v1/products/{id}` - Delete product

#### Supplier Management
- **GET** `/api/v1/suppliers` - List suppliers
- **POST** `/api/v1/suppliers` - Create supplier
- **GET** `/api/v1/suppliers/{id}` - Get supplier details

#### Web Scraping
- **POST** `/api/v1/scraping/start` - Start scraping job
- **GET** `/api/v1/scraping/status/{id}` - Get scraping status
- **GET** `/api/v1/scraping/results/{id}` - Get scraping results

#### Batch Processing
- **POST** `/api/v1/processing/batch` - Start batch processing
- **GET** `/api/v1/processing/status/{id}` - Get processing status

#### Image Processing
- **POST** `/api/v1/images/upload` - Upload and process images
- **POST** `/api/v1/images/optimize` - Optimize image quality
- **POST** `/api/v1/images/convert` - Convert image formats

#### Translation
- **POST** `/api/v1/translate/text` - Translate text content
- **POST** `/api/v1/translate/batch` - Batch translate content

### Interactive API Documentation

When the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing

### Backend Testing

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_config.py

# Run tests in watch mode
pytest-watch
```

### Frontend Testing

```bash
cd frontend

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

## 🔧 Development

### Code Quality

Both backend and frontend use comprehensive code quality tools:

#### Backend
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

#### Frontend
```bash
# Linting
npm run lint
npm run lint:fix

# Code formatting
npm run format
npm run format:check

# Type checking
npm run type-check
```

### Development Workflow

1. **Create Feature Branch**: `git checkout -b feature/your-feature-name`
2. **Make Changes**: Follow the coding standards and add tests
3. **Run Tests**: Ensure all tests pass
4. **Code Quality**: Run linting and formatting tools
5. **Commit Changes**: Use semantic commit messages
6. **Create Pull Request**: Include description and testing notes

## 📊 Monitoring and Logging

### Structured Logging

The application uses structured logging for better observability:

- **Development**: Human-readable colored output
- **Production**: JSON format for log aggregation
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Context**: Request IDs, user information, operation metadata

### Health Checks

- **Backend Health**: `GET /health`
- **Database Status**: Connection and query performance
- **Redis Status**: Cache connectivity and performance
- **External APIs**: Service availability checks

## 🚀 Deployment

### Production Environment

#### Backend Deployment

```bash
# Set production environment variables
export DEBUG=false
export LOG_LEVEL=INFO
export ENVIRONMENT=production

# Install dependencies
pip install -r requirements.txt

# Run database migrations (when implemented)
alembic upgrade head

# Start production server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Frontend Deployment

```bash
# Set production environment variables
export NODE_ENV=production
export NEXT_PUBLIC_API_URL=https://api.yourdomain.com

# Install dependencies
npm ci

# Build for production
npm run build

# Start production server
npm start
```

### Docker Deployment (Future)

```bash
# Build and run with Docker Compose
docker-compose up -d

# Scale services
docker-compose up -d --scale backend=3 --scale frontend=2
```

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the Repository**: Create your own fork
2. **Create Feature Branch**: `git checkout -b feature/amazing-feature`
3. **Follow Code Standards**: Use the established patterns and tools
4. **Add Tests**: Ensure new features have appropriate test coverage
5. **Update Documentation**: Keep README and code comments current
6. **Commit Changes**: Use semantic commit messages
7. **Push to Branch**: `git push origin feature/amazing-feature`
8. **Open Pull Request**: Provide clear description and context

### Code Standards

- **Python**: Follow PEP8, use type hints, add docstrings
- **TypeScript**: Use strict typing, functional components
- **Testing**: Write tests for new features and bug fixes
- **Documentation**: Update relevant documentation

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation

- **Backend API**: http://localhost:8000/docs (when running)
- **Project Wiki**: [GitHub Wiki](https://github.com/puehres/product-information-management/wiki)
- **Issue Tracker**: [GitHub Issues](https://github.com/puehres/product-information-management/issues)

### Getting Help

1. **Check Documentation**: Review README files and API docs
2. **Search Issues**: Look for existing solutions
3. **Create Issue**: Provide detailed description and reproduction steps
4. **Community**: Join discussions in GitHub Discussions

## 🗺️ Roadmap

### Phase 1: Foundation (Current)
- [x] Project structure and configuration
- [x] Backend API framework setup
- [x] Frontend application setup
- [x] Basic documentation and testing

### Phase 2: Core Features (Next)
- [ ] Database models and migrations
- [ ] Product management API
- [ ] Basic UI components and pages
- [ ] File upload and processing

### Phase 3: Advanced Features
- [ ] Web scraping integration
- [ ] Image processing pipeline
- [ ] Translation services
- [ ] Batch processing system

### Phase 4: Production Ready
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Monitoring and alerting
- [ ] Deployment automation

## 📈 Status

- **Backend**: ✅ Initial setup complete
- **Frontend**: ✅ Initial setup complete
- **Database**: 🔄 In progress
- **API Integration**: 🔄 In progress
- **Testing**: ✅ Framework setup complete
- **Documentation**: ✅ Initial documentation complete

---

**Built with ❤️ for efficient product data management**
