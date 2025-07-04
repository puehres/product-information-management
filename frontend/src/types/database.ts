/**
 * TypeScript type definitions for the Universal Product Automation System database.
 * 
 * These types correspond to the Supabase database schema and provide
 * type safety for frontend operations.
 */

// Enum types matching the database
export type FileType = 'pdf' | 'csv' | 'xlsx' | 'manual'
export type BatchStatus = 'uploaded' | 'processing' | 'completed' | 'failed' | 'review_required'
export type ProductStatus = 'draft' | 'processing' | 'scraped' | 'translated' | 'ready' | 'exported' | 'failed'
export type ImageType = 'main' | 'additional' | 'detail' | 'manual_upload'
export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed'

// Base interface for all database entities
export interface BaseEntity {
  id: string
  created_at: string
  updated_at: string
}

// Supplier interfaces
export interface Supplier extends BaseEntity {
  name: string
  code: string
  website_url: string | null
  identifier_type: string
  scraping_config: Record<string, any>
  search_url_template: string | null
  active: boolean
}

export interface SupplierCreate {
  name: string
  code: string
  website_url?: string | null
  identifier_type?: string
  scraping_config?: Record<string, any>
  search_url_template?: string | null
  active?: boolean
}

export interface SupplierUpdate {
  name?: string
  code?: string
  website_url?: string | null
  identifier_type?: string
  scraping_config?: Record<string, any>
  search_url_template?: string | null
  active?: boolean
}

// Upload batch interfaces
export interface UploadBatch extends BaseEntity {
  supplier_id: string
  batch_name: string
  file_type: FileType
  file_path: string | null
  file_size: number | null
  status: BatchStatus
  total_products: number
  processed_products: number
  failed_products: number
  processing_started_at: string | null
  processing_completed_at: string | null
  error_message: string | null
  metadata: Record<string, any>
}

export interface UploadBatchCreate {
  supplier_id: string
  batch_name: string
  file_type: FileType
  file_path?: string | null
  file_size?: number | null
  metadata?: Record<string, any>
}

export interface UploadBatchUpdate {
  batch_name?: string
  file_type?: FileType
  file_path?: string | null
  file_size?: number | null
  status?: BatchStatus
  total_products?: number
  processed_products?: number
  failed_products?: number
  processing_started_at?: string | null
  processing_completed_at?: string | null
  error_message?: string | null
  metadata?: Record<string, any>
}

// Product interfaces
export interface Product extends BaseEntity {
  batch_id: string
  supplier_id: string
  
  // Supplier product identifiers
  supplier_sku: string
  supplier_name: string | null
  supplier_description: string | null
  supplier_price_usd: number | null
  supplier_price_eur: number | null
  
  // Scraped product data
  scraped_name: string | null
  scraped_description: string | null
  scraped_url: string | null
  scraped_images_urls: string[] | null
  scraping_confidence: number
  
  // German translations
  german_name: string | null
  german_description: string | null
  german_short_description: string | null
  
  // Gambio export fields
  gambio_category: string
  gambio_tax_class_id: number
  gambio_model: string | null
  gambio_price_eur: number | null
  gambio_seo_url: string | null
  
  // Processing status and metadata
  status: ProductStatus
  processing_notes: string | null
  quality_score: number
  requires_review: boolean
  review_notes: string | null
}

export interface ProductCreate {
  batch_id: string
  supplier_id: string
  supplier_sku: string
  supplier_name?: string | null
  supplier_description?: string | null
  supplier_price_usd?: number | null
  supplier_price_eur?: number | null
}

export interface ProductUpdate {
  supplier_sku?: string
  supplier_name?: string | null
  supplier_description?: string | null
  supplier_price_usd?: number | null
  supplier_price_eur?: number | null
  scraped_name?: string | null
  scraped_description?: string | null
  scraped_url?: string | null
  scraped_images_urls?: string[] | null
  scraping_confidence?: number
  german_name?: string | null
  german_description?: string | null
  german_short_description?: string | null
  gambio_category?: string
  gambio_tax_class_id?: number
  gambio_model?: string | null
  gambio_price_eur?: number | null
  gambio_seo_url?: string | null
  status?: ProductStatus
  processing_notes?: string | null
  quality_score?: number
  requires_review?: boolean
  review_notes?: string | null
}

// Image interfaces
export interface Image extends BaseEntity {
  product_id: string
  
  // Image source and processing
  original_url: string | null
  s3_key: string | null
  s3_url: string | null
  filename: string | null
  
  // Image properties
  image_type: ImageType
  sequence_number: number
  width: number | null
  height: number | null
  file_size: number | null
  format: string | null
  
  // Processing status
  processing_status: ProcessingStatus
  processing_error: string | null
  quality_check_passed: boolean
  quality_warnings: string[] | null
}

export interface ImageCreate {
  product_id: string
  original_url?: string | null
  image_type?: ImageType
  sequence_number?: number
}

export interface ImageUpdate {
  original_url?: string | null
  s3_key?: string | null
  s3_url?: string | null
  filename?: string | null
  image_type?: ImageType
  sequence_number?: number
  width?: number | null
  height?: number | null
  file_size?: number | null
  format?: string | null
  processing_status?: ProcessingStatus
  processing_error?: string | null
  quality_check_passed?: boolean
  quality_warnings?: string[] | null
}

// Utility types for API responses
export interface PaginationParams {
  page: number
  pageSize: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
  hasNext: boolean
  hasPrevious: boolean
}

export interface ApiResponse<T> {
  data: T | null
  error: string | null
}

export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy' | 'error'
  timestamp: string
  services: Record<string, any>
  version: string
  environment: string
}

// Summary types for list views
export interface SupplierSummary {
  id: string
  name: string
  code: string
  website_url: string | null
  active: boolean
}

export interface UploadBatchSummary {
  id: string
  supplier_id: string
  batch_name: string
  file_type: FileType
  status: BatchStatus
  total_products: number
  processed_products: number
  failed_products: number
  created_at: string
}

export interface ProductSummary {
  id: string
  batch_id: string
  supplier_sku: string
  supplier_name: string | null
  german_name: string | null
  status: ProductStatus
  scraping_confidence: number
  quality_score: number
  requires_review: boolean
  created_at: string
}

export interface ImageSummary {
  id: string
  product_id: string
  image_type: ImageType
  sequence_number: number
  width: number | null
  height: number | null
  processing_status: ProcessingStatus
  quality_check_passed: boolean
  s3_url: string | null
}

// Statistics types
export interface SupplierStats {
  supplier_id: string
  total_batches: number
  total_products: number
  successful_products: number
  failed_products: number
  avg_processing_time_minutes: number | null
  last_batch_date: string | null
  success_rate: number
}

export interface BatchStats {
  batch_id: string
  total_products: number
  processed_products: number
  failed_products: number
  pending_products: number
  success_rate: number
  avg_processing_time_seconds: number | null
  estimated_completion_minutes: number | null
}

export interface ProductStats {
  total_products: number
  by_status: Record<ProductStatus, number>
  avg_confidence_score: number
  avg_quality_score: number
  products_requiring_review: number
  ready_for_export: number
  with_images: number
  translated: number
}

export interface ImageStats {
  total_images: number
  by_status: Record<ProcessingStatus, number>
  by_type: Record<ImageType, number>
  quality_passed: number
  avg_file_size_mb: number
  avg_dimensions: { width: number; height: number }
  processed_images: number
  failed_images: number
}

// Filter types for queries
export interface SupplierFilters {
  active?: boolean
  search?: string
}

export interface UploadBatchFilters {
  supplier_id?: string
  status?: BatchStatus
  file_type?: FileType
  date_from?: string
  date_to?: string
}

export interface ProductFilters {
  batch_id?: string
  supplier_id?: string
  status?: ProductStatus
  requires_review?: boolean
  min_confidence?: number
  min_quality?: number
  search?: string
}

export interface ImageFilters {
  product_id?: string
  image_type?: ImageType
  processing_status?: ProcessingStatus
  quality_check_passed?: boolean
}

// Export data types
export interface ProductExportData {
  id: string
  supplier_sku: string
  gambio_model: string
  german_name: string
  german_description: string
  german_short_description: string
  gambio_category: string
  gambio_price_eur: number
  gambio_tax_class_id: number
  gambio_seo_url: string
  image_filenames: string[]
}

// Review types
export interface ProductReviewItem {
  id: string
  supplier_sku: string
  supplier_name: string | null
  scraped_name: string | null
  german_name: string | null
  scraping_confidence: number
  quality_score: number
  review_reason: string
  scraped_url: string | null
  image_count: number
}

// Processing progress types
export interface BatchProcessingProgress {
  batch_id: string
  current_product: number
  total_products: number
  current_step: string
  progress_percentage: number
  estimated_remaining_minutes: number | null
  last_updated: string
}

export interface ImageProcessingResult {
  image_id: string
  success: boolean
  s3_key: string | null
  s3_url: string | null
  filename: string | null
  width: number | null
  height: number | null
  file_size: number | null
  format: string | null
  quality_check_passed: boolean
  quality_warnings: string[]
  processing_time_seconds: number | null
  error_message: string | null
}
