/**
 * Tests for Supabase client configuration and utilities.
 * 
 * This module contains tests for the frontend Supabase integration.
 */

import {
  TABLES,
  testConnection,
  getDatabaseHealth,
  handleSupabaseError,
  executeQuery,
  getPaginationRange,
  executeBatch
} from '../supabase'

// Mock the Supabase client
jest.mock('@supabase/supabase-js')

// Mock environment variables
const mockEnv = {
  NEXT_PUBLIC_SUPABASE_URL: 'https://test-project.supabase.co',
  NEXT_PUBLIC_SUPABASE_ANON_KEY: 'test-anon-key'
}

// Store original env
const originalEnv = process.env

beforeEach(() => {
  // Reset environment variables
  process.env = { ...originalEnv, ...mockEnv }
  
  // Clear all mocks
  jest.clearAllMocks()
})

afterEach(() => {
  // Restore original environment
  process.env = originalEnv
})

describe('Supabase Configuration', () => {
  it('should export correct table names', () => {
    expect(TABLES).toEqual({
      SUPPLIERS: 'suppliers',
      UPLOAD_BATCHES: 'upload_batches',
      PRODUCTS: 'products',
      IMAGES: 'images',
    })
  })

  it('should have environment variables configured', () => {
    expect(process.env.NEXT_PUBLIC_SUPABASE_URL).toBeDefined()
    expect(process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY).toBeDefined()
  })
})

describe('testConnection', () => {
  it('should be a function', () => {
    expect(typeof testConnection).toBe('function')
  })

  it('should return a promise', () => {
    const result = testConnection()
    expect(result).toBeInstanceOf(Promise)
  })
})

describe('getDatabaseHealth', () => {
  it('should be a function', () => {
    expect(typeof getDatabaseHealth).toBe('function')
  })

  it('should return a promise', () => {
    const result = getDatabaseHealth()
    expect(result).toBeInstanceOf(Promise)
  })
})

describe('handleSupabaseError', () => {
  it('should return message from error object', () => {
    const error = { message: 'Test error message' }
    const result = handleSupabaseError(error)
    
    expect(result).toBe('Test error message')
  })

  it('should return details from error object', () => {
    const error = { details: 'Test error details' }
    const result = handleSupabaseError(error)
    
    expect(result).toBe('Test error details')
  })

  it('should return hint from error object', () => {
    const error = { hint: 'Test error hint' }
    const result = handleSupabaseError(error)
    
    expect(result).toBe('Test error hint')
  })

  it('should return default message for null error', () => {
    const result = handleSupabaseError(null)
    
    expect(result).toBe('Unknown error occurred')
  })

  it('should return default message for empty error', () => {
    const error = {}
    const result = handleSupabaseError(error)
    
    expect(result).toBe('Database operation failed')
  })
})

describe('executeQuery', () => {
  it('should return data for successful query', async () => {
    const mockQueryFn = jest.fn().mockResolvedValue({
      data: { id: 1, name: 'Test' },
      error: null
    })

    const result = await executeQuery(mockQueryFn)
    
    expect(result.data).toEqual({ id: 1, name: 'Test' })
    expect(result.error).toBeNull()
  })

  it('should return error for failed query', async () => {
    const mockQueryFn = jest.fn().mockResolvedValue({
      data: null,
      error: { message: 'Query failed' }
    })

    const result = await executeQuery(mockQueryFn)
    
    expect(result.data).toBeNull()
    expect(result.error).toBe('Query failed')
  })

  it('should handle query function exceptions', async () => {
    const mockQueryFn = jest.fn().mockRejectedValue(new Error('Network error'))

    const result = await executeQuery(mockQueryFn)
    
    expect(result.data).toBeNull()
    expect(result.error).toBe('Network error')
  })
})

describe('getPaginationRange', () => {
  it('should calculate correct range for first page', () => {
    const result = getPaginationRange(1, 20)
    
    expect(result).toEqual({ from: 0, to: 19 })
  })

  it('should calculate correct range for second page', () => {
    const result = getPaginationRange(2, 20)
    
    expect(result).toEqual({ from: 20, to: 39 })
  })

  it('should calculate correct range for custom page size', () => {
    const result = getPaginationRange(3, 10)
    
    expect(result).toEqual({ from: 20, to: 29 })
  })
})

describe('executeBatch', () => {
  it('should execute all operations successfully', async () => {
    const operations = [
      jest.fn().mockResolvedValue({ data: { id: 1 }, error: null }),
      jest.fn().mockResolvedValue({ data: { id: 2 }, error: null }),
    ]

    const results = await executeBatch(operations)
    
    expect(results).toHaveLength(2)
    expect(results[0]?.data).toEqual({ id: 1 })
    expect(results[0]?.error).toBeNull()
    expect(results[1]?.data).toEqual({ id: 2 })
    expect(results[1]?.error).toBeNull()
  })

  it('should handle mixed success and failure', async () => {
    const operations = [
      jest.fn().mockResolvedValue({ data: { id: 1 }, error: null }),
      jest.fn().mockResolvedValue({ data: null, error: { message: 'Failed' } }),
    ]

    const results = await executeBatch(operations)
    
    expect(results).toHaveLength(2)
    expect(results[0]?.data).toEqual({ id: 1 })
    expect(results[0]?.error).toBeNull()
    expect(results[1]?.data).toBeNull()
    expect(results[1]?.error).toBe('Failed')
  })

  it('should handle operation exceptions', async () => {
    const operations = [
      jest.fn().mockResolvedValue({ data: { id: 1 }, error: null }),
      jest.fn().mockRejectedValue(new Error('Network error')),
    ]

    const results = await executeBatch(operations)
    
    expect(results).toHaveLength(2)
    expect(results[0]?.data).toEqual({ id: 1 })
    expect(results[0]?.error).toBeNull()
    expect(results[1]?.data).toBeNull()
    expect(results[1]?.error).toBe('Network error')
  })
})

describe('subscribeToTable', () => {
  it('should be a function', () => {
    const { subscribeToTable } = require('../supabase')
    expect(typeof subscribeToTable).toBe('function')
  })
})
