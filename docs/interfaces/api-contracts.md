# API Contracts Documentation

## Overview
This document maintains the current API interface contracts for the Universal Product Automation System.

## Current API Structure

### Base Configuration
- **Base URL**: `http://localhost:8000` (development)
- **API Version**: `v1`
- **Content Type**: `application/json`
- **Authentication**: TBD (future implementation)

## Backend API Endpoints

### Health Check
```http
GET /health
```
**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-07T00:00:00Z",
  "version": "1.0.0"
}
```

### Configuration
```http
GET /api/v1/config
```
**Response**:
```json
{
  "environment": "development",
  "database_connected": true,
  "redis_connected": false,
  "features": {
    "file_upload": true,
    "web_scraping": false,
    "translation": false
  }
}
```

## Data Models

### Core Models (Planned)
```python
# Supplier Model
class Supplier:
    id: int
    name: str
    base_url: str
    scraping_config: dict
    confidence_thresholds: dict
    created_at: datetime
    updated_at: datetime

# Product Model  
class Product:
    id: int
    supplier_id: int
    external_id: str
    name: str
    description: Optional[str]
    price: Optional[Decimal]
    image_urls: List[str]
    categories: List[str]
    confidence_score: float
    status: ProductStatus
    created_at: datetime
    updated_at: datetime
```

## Interface Contracts

### File Upload Interface (Planned)
```typescript
interface FileUploadRequest {
  file: File;
  supplier_id: number;
  file_type: 'csv' | 'excel' | 'pdf';
  options?: {
    skip_validation?: boolean;
    batch_name?: string;
  };
}

interface FileUploadResponse {
  batch_id: string;
  status: 'processing' | 'completed' | 'failed';
  total_records: number;
  processed_records: number;
  errors: string[];
}
```

### Product Matching Interface (Planned)
```typescript
interface MatchingRequest {
  batch_id: string;
  supplier_id: number;
  matching_strategy: 'exact' | 'fuzzy' | 'search' | 'browse';
  confidence_threshold: number;
}

interface MatchingResponse {
  batch_id: string;
  matches: ProductMatch[];
  summary: {
    total_products: number;
    matched: number;
    requires_review: number;
    failed: number;
  };
}
```

## Error Handling

### Standard Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {
      "field": "supplier_id",
      "reason": "Supplier not found"
    },
    "timestamp": "2025-01-07T00:00:00Z"
  }
}
```

### Error Codes
- `VALIDATION_ERROR`: Input validation failed
- `NOT_FOUND`: Resource not found
- `UNAUTHORIZED`: Authentication required
- `FORBIDDEN`: Insufficient permissions
- `INTERNAL_ERROR`: Server error
- `RATE_LIMITED`: Too many requests

## WebSocket Interfaces (Planned)

### Progress Updates
```typescript
interface ProgressUpdate {
  batch_id: string;
  operation: 'file_processing' | 'product_matching' | 'image_download';
  progress: {
    current: number;
    total: number;
    percentage: number;
  };
  status: 'running' | 'completed' | 'failed';
  message?: string;
}
```

## Frontend-Backend Integration

### State Management
```typescript
// React Query keys
export const queryKeys = {
  suppliers: ['suppliers'],
  products: (supplierId: number) => ['products', supplierId],
  batches: ['batches'],
  batch: (batchId: string) => ['batch', batchId],
} as const;
```

### API Client Configuration
```typescript
// Axios configuration
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

## Version History

### v1.0.0 (Current - Task 1)
- Basic FastAPI structure
- Health check endpoint
- Configuration endpoint
- Development environment setup

### Planned (Task 2+)
- Database models and migrations
- CRUD operations for suppliers and products
- File upload endpoints
- Product matching endpoints
- WebSocket connections for real-time updates

## Notes

- All endpoints return JSON responses
- Timestamps are in ISO 8601 format (UTC)
- File uploads use multipart/form-data
- WebSocket connections use JSON message format
- Error responses follow RFC 7807 Problem Details format

---

**Last Updated**: 2025-01-07 (Task 1 completion)
**Next Update**: Task 2 (Database implementation)
