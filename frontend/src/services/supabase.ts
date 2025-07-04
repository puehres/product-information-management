/**
 * Supabase client configuration for the Universal Product Automation System frontend.
 * 
 * This module provides a configured Supabase client for frontend operations
 * with proper error handling and type safety.
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js'

// Environment variables validation
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

if (!supabaseUrl) {
  throw new Error('Missing NEXT_PUBLIC_SUPABASE_URL environment variable')
}

if (!supabaseAnonKey) {
  throw new Error('Missing NEXT_PUBLIC_SUPABASE_ANON_KEY environment variable')
}

// Create Supabase client with configuration
export const supabase: SupabaseClient = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: false, // MVP doesn't need authentication persistence
    autoRefreshToken: false,
  },
  realtime: {
    params: {
      eventsPerSecond: 10, // Limit real-time events for performance
    },
  },
})

/**
 * Database table names for type safety
 */
export const TABLES = {
  SUPPLIERS: 'suppliers',
  UPLOAD_BATCHES: 'upload_batches',
  PRODUCTS: 'products',
  IMAGES: 'images',
} as const

/**
 * Test the Supabase connection
 * 
 * @returns Promise<boolean> - True if connection is successful
 */
export async function testConnection(): Promise<boolean> {
  try {
    const { data: _data, error } = await supabase
      .from(TABLES.SUPPLIERS)
      .select('count')
      .limit(1)
    
    if (error) {
      console.error('Supabase connection test failed:', error)
      return false
    }
    
    console.log('Supabase connection test successful')
    return true
  } catch (error) {
    console.error('Supabase connection test error:', error)
    return false
  }
}

/**
 * Get database health status
 * 
 * @returns Promise<object> - Health status information
 */
export async function getDatabaseHealth(): Promise<{
  status: 'healthy' | 'unhealthy' | 'error'
  timestamp: string
  error?: string
}> {
  try {
    const startTime = Date.now()
    const { data: _data, error } = await supabase
      .from(TABLES.SUPPLIERS)
      .select('count')
      .limit(1)
    
    const endTime = Date.now()
    const responseTime = endTime - startTime
    
    if (error) {
      return {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        error: error.message,
      }
    }
    
    return {
      status: responseTime < 2000 ? 'healthy' : 'unhealthy',
      timestamp: new Date().toISOString(),
    }
  } catch (error) {
    return {
      status: 'error',
      timestamp: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}

/**
 * Utility function to handle Supabase errors consistently
 * 
 * @param error - Supabase error object
 * @returns Formatted error message
 */
export function handleSupabaseError(error: any): string {
  if (!error) return 'Unknown error occurred'
  
  // Handle different types of Supabase errors
  if (error.message) {
    return error.message
  }
  
  if (error.details) {
    return error.details
  }
  
  if (error.hint) {
    return error.hint
  }
  
  return 'Database operation failed'
}

/**
 * Generic function to execute Supabase queries with error handling
 * 
 * @param queryFn - Function that returns a Supabase query
 * @returns Promise with data or error
 */
export async function executeQuery<T>(
  queryFn: () => Promise<{ data: T | null; error: any }>
): Promise<{ data: T | null; error: string | null }> {
  try {
    const { data, error } = await queryFn()
    
    if (error) {
      return {
        data: null,
        error: handleSupabaseError(error),
      }
    }
    
    return {
      data,
      error: null,
    }
  } catch (error) {
    return {
      data: null,
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}

/**
 * Pagination helper for Supabase queries
 * 
 * @param page - Page number (1-based)
 * @param pageSize - Number of items per page
 * @returns Range parameters for Supabase
 */
export function getPaginationRange(page: number, pageSize: number): {
  from: number
  to: number
} {
  const from = (page - 1) * pageSize
  const to = from + pageSize - 1
  
  return { from, to }
}

/**
 * Real-time subscription helper
 * 
 * @param table - Table name to subscribe to
 * @param callback - Callback function for real-time updates
 * @returns Subscription object
 */
export function subscribeToTable(
  table: string,
  callback: (payload: any) => void
) {
  return supabase
    .channel(`public:${table}`)
    .on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: table,
      },
      callback
    )
    .subscribe()
}

/**
 * Batch operation helper for multiple database operations
 * 
 * @param operations - Array of database operations
 * @returns Promise with results of all operations
 */
export async function executeBatch<T>(
  operations: Array<() => Promise<{ data: T | null; error: any }>>
): Promise<Array<{ data: T | null; error: string | null }>> {
  const results = await Promise.allSettled(
    operations.map(op => executeQuery(op))
  )
  
  return results.map(result => {
    if (result.status === 'fulfilled') {
      return result.value
    } else {
      return {
        data: null,
        error: result.reason?.message || 'Operation failed',
      }
    }
  })
}

export default supabase
