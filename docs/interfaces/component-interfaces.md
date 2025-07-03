# Component Interfaces Documentation

## Overview
This document maintains the current frontend component interfaces and contracts for the Universal Product Automation System.

## Current Status
- **Framework**: Next.js 14 with TypeScript
- **UI Library**: Shadcn/UI + Tailwind CSS
- **State Management**: React Query (planned)
- **Current State**: Basic setup completed (Task 1), components pending (Task 13)

## Component Architecture

### Layout Components

#### RootLayout
```typescript
// src/app/layout.tsx
interface RootLayoutProps {
  children: React.ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps): JSX.Element
```

**Current Implementation**:
- Basic HTML structure with metadata
- Global CSS imports (Tailwind)
- Font configuration (Inter)

#### Navigation (Planned)
```typescript
interface NavigationProps {
  currentPath: string;
  user?: User;
  onNavigate: (path: string) => void;
}

interface NavigationItem {
  label: string;
  path: string;
  icon?: React.ComponentType;
  requiresAuth?: boolean;
  children?: NavigationItem[];
}
```

### Core Application Components (Planned)

#### SupplierSelector
```typescript
interface SupplierSelectorProps {
  suppliers: Supplier[];
  selectedSupplier?: Supplier;
  onSupplierChange: (supplier: Supplier) => void;
  loading?: boolean;
  error?: string;
}

interface Supplier {
  id: number;
  name: string;
  baseUrl: string;
  isActive: boolean;
  confidenceThresholds: Record<string, number>;
}
```

#### FileUpload
```typescript
interface FileUploadProps {
  supplierId: number;
  acceptedTypes: FileType[];
  maxSize: number;
  onUploadStart: (file: File) => void;
  onUploadProgress: (progress: UploadProgress) => void;
  onUploadComplete: (result: UploadResult) => void;
  onUploadError: (error: UploadError) => void;
}

interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

interface UploadResult {
  batchId: string;
  fileName: string;
  totalRecords: number;
  status: 'processing' | 'completed' | 'failed';
}

type FileType = 'csv' | 'excel' | 'pdf';
```

#### ProductTable
```typescript
interface ProductTableProps {
  products: Product[];
  loading?: boolean;
  error?: string;
  pagination: PaginationState;
  sorting: SortingState;
  filtering: FilteringState;
  onProductSelect: (product: Product) => void;
  onBulkAction: (action: BulkAction, productIds: number[]) => void;
  onPageChange: (page: number) => void;
  onSortChange: (sorting: SortingState) => void;
  onFilterChange: (filters: FilteringState) => void;
}

interface Product {
  id: number;
  supplierId: number;
  externalId: string;
  name: string;
  description?: string;
  price?: number;
  currency: string;
  imageUrls: string[];
  categories: string[];
  confidenceScore: number;
  status: ProductStatus;
  createdAt: string;
  updatedAt: string;
}

type ProductStatus = 'pending' | 'matched' | 'requires_review' | 'approved' | 'rejected';
type BulkAction = 'approve' | 'reject' | 'delete' | 'export';
```

#### ReviewDashboard
```typescript
interface ReviewDashboardProps {
  reviewItems: ReviewItem[];
  filters: ReviewFilters;
  onItemReview: (itemId: number, decision: ReviewDecision) => void;
  onBulkReview: (itemIds: number[], decision: ReviewDecision) => void;
  onFilterChange: (filters: ReviewFilters) => void;
}

interface ReviewItem {
  id: number;
  type: 'product_match' | 'image_quality' | 'duplicate_group';
  itemId: number;
  priority: number;
  confidenceScore?: number;
  data: Record<string, any>;
  createdAt: string;
}

interface ReviewFilters {
  type?: ReviewItem['type'];
  priority?: number;
  supplierId?: number;
  dateRange?: [string, string];
}

type ReviewDecision = 'approve' | 'reject' | 'requires_manual';
```

### UI Components (Shadcn/UI Based)

#### Button
```typescript
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  asChild?: boolean;
}
```

#### DataTable
```typescript
interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  loading?: boolean;
  error?: string;
  pagination?: {
    pageIndex: number;
    pageSize: number;
    pageCount: number;
  };
  sorting?: SortingState;
  filtering?: ColumnFiltersState;
  onPaginationChange?: (pagination: PaginationState) => void;
  onSortingChange?: (sorting: SortingState) => void;
  onFilteringChange?: (filters: ColumnFiltersState) => void;
}
```

#### ProgressIndicator
```typescript
interface ProgressIndicatorProps {
  value: number;
  max: number;
  label?: string;
  showPercentage?: boolean;
  variant?: 'default' | 'success' | 'warning' | 'error';
  size?: 'sm' | 'md' | 'lg';
}
```

### Form Components

#### SupplierForm
```typescript
interface SupplierFormProps {
  supplier?: Supplier;
  onSubmit: (data: SupplierFormData) => void;
  onCancel: () => void;
  loading?: boolean;
  error?: string;
}

interface SupplierFormData {
  name: string;
  baseUrl: string;
  scrapingConfig: Record<string, any>;
  confidenceThresholds: Record<string, number>;
  isActive: boolean;
}
```

#### ProductMatchForm
```typescript
interface ProductMatchFormProps {
  product: Product;
  matchCandidates: MatchCandidate[];
  onSubmit: (matchId: number, confidence: number) => void;
  onReject: (reason: string) => void;
  onManualEntry: (data: ManualProductData) => void;
}

interface MatchCandidate {
  id: number;
  url: string;
  name: string;
  description?: string;
  price?: number;
  imageUrls: string[];
  confidenceScore: number;
  matchMethod: string;
}

interface ManualProductData {
  name: string;
  description?: string;
  price?: number;
  productUrl: string;
  imageUrls: string[];
  categories: string[];
}
```

## State Management Interfaces

### React Query Keys
```typescript
export const queryKeys = {
  // Suppliers
  suppliers: ['suppliers'] as const,
  supplier: (id: number) => ['supplier', id] as const,
  
  // Products
  products: ['products'] as const,
  productsBySupplier: (supplierId: number) => ['products', 'supplier', supplierId] as const,
  product: (id: number) => ['product', id] as const,
  
  // Batches
  batches: ['batches'] as const,
  batch: (id: string) => ['batch', id] as const,
  batchProducts: (batchId: string) => ['batch', batchId, 'products'] as const,
  
  // Reviews
  reviewQueue: ['review-queue'] as const,
  reviewItem: (id: number) => ['review-item', id] as const,
  
  // Duplicates
  duplicateGroups: ['duplicate-groups'] as const,
  duplicateGroup: (id: number) => ['duplicate-group', id] as const,
} as const;
```

### API Hooks (Planned)
```typescript
// Suppliers
export function useSuppliers(): UseQueryResult<Supplier[], Error>
export function useSupplier(id: number): UseQueryResult<Supplier, Error>
export function useCreateSupplier(): UseMutationResult<Supplier, Error, SupplierFormData>
export function useUpdateSupplier(): UseMutationResult<Supplier, Error, { id: number; data: Partial<SupplierFormData> }>

// Products
export function useProducts(filters?: ProductFilters): UseQueryResult<PaginatedResponse<Product>, Error>
export function useProduct(id: number): UseQueryResult<Product, Error>
export function useBulkProductAction(): UseMutationResult<void, Error, { action: BulkAction; productIds: number[] }>

// File Upload
export function useFileUpload(): UseMutationResult<UploadResult, Error, { file: File; supplierId: number }>
export function useBatchStatus(batchId: string): UseQueryResult<BatchStatus, Error>

// Reviews
export function useReviewQueue(filters?: ReviewFilters): UseQueryResult<PaginatedResponse<ReviewItem>, Error>
export function useSubmitReview(): UseMutationResult<void, Error, { itemId: number; decision: ReviewDecision; notes?: string }>
```

## Type Definitions

### Common Types
```typescript
interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
}

interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
}

interface SortingState {
  field: string;
  direction: 'asc' | 'desc';
}

interface FilteringState {
  [key: string]: any;
}

interface PaginationState {
  pageIndex: number;
  pageSize: number;
}
```

### WebSocket Types (Planned)
```typescript
interface WebSocketMessage {
  type: 'progress' | 'status' | 'error' | 'notification';
  data: any;
  timestamp: string;
}

interface ProgressMessage extends WebSocketMessage {
  type: 'progress';
  data: {
    batchId: string;
    operation: string;
    current: number;
    total: number;
    percentage: number;
  };
}

interface StatusMessage extends WebSocketMessage {
  type: 'status';
  data: {
    batchId: string;
    status: 'processing' | 'completed' | 'failed';
    message?: string;
  };
}
```

## Component Testing Interfaces

### Test Utilities
```typescript
interface RenderOptions {
  initialEntries?: string[];
  user?: User;
  queryClient?: QueryClient;
}

interface MockApiResponse<T> {
  data: T;
  status: number;
  delay?: number;
}

// Test helpers
export function renderWithProviders(
  ui: React.ReactElement,
  options?: RenderOptions
): RenderResult

export function createMockQueryClient(): QueryClient
export function mockApiEndpoint<T>(endpoint: string, response: MockApiResponse<T>): void
```

## Styling Interfaces

### Theme Configuration
```typescript
interface ThemeConfig {
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    foreground: string;
    muted: string;
    border: string;
    destructive: string;
    warning: string;
    success: string;
  };
  spacing: Record<string, string>;
  typography: {
    fontFamily: string;
    fontSize: Record<string, [string, string]>;
  };
}
```

### Component Variants
```typescript
interface ComponentVariants {
  button: {
    variant: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
    size: 'default' | 'sm' | 'lg' | 'icon';
  };
  badge: {
    variant: 'default' | 'secondary' | 'destructive' | 'outline';
  };
  alert: {
    variant: 'default' | 'destructive' | 'warning' | 'success';
  };
}
```

---

**Last Updated**: 2025-01-07 (Task 1 completion)
**Next Update**: Task 13 (Frontend development)
**Status**: Interface design complete, implementation pending
