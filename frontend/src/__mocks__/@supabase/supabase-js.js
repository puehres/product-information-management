// Mock implementation of @supabase/supabase-js for Jest testing

const mockSupabaseClient = {
  from: jest.fn().mockReturnThis(),
  select: jest.fn().mockReturnThis(),
  insert: jest.fn().mockReturnThis(),
  update: jest.fn().mockReturnThis(),
  delete: jest.fn().mockReturnThis(),
  limit: jest.fn().mockReturnThis(),
  order: jest.fn().mockReturnThis(),
  filter: jest.fn().mockReturnThis(),
  eq: jest.fn().mockReturnThis(),
  neq: jest.fn().mockReturnThis(),
  gt: jest.fn().mockReturnThis(),
  gte: jest.fn().mockReturnThis(),
  lt: jest.fn().mockReturnThis(),
  lte: jest.fn().mockReturnThis(),
  like: jest.fn().mockReturnThis(),
  ilike: jest.fn().mockReturnThis(),
  is: jest.fn().mockReturnThis(),
  in: jest.fn().mockReturnThis(),
  contains: jest.fn().mockReturnThis(),
  containedBy: jest.fn().mockReturnThis(),
  rangeGt: jest.fn().mockReturnThis(),
  rangeGte: jest.fn().mockReturnThis(),
  rangeLt: jest.fn().mockReturnThis(),
  rangeLte: jest.fn().mockReturnThis(),
  rangeAdjacent: jest.fn().mockReturnThis(),
  overlaps: jest.fn().mockReturnThis(),
  textSearch: jest.fn().mockReturnThis(),
  match: jest.fn().mockReturnThis(),
  not: jest.fn().mockReturnThis(),
  or: jest.fn().mockReturnThis(),
  channel: jest.fn().mockReturnValue({
    on: jest.fn().mockReturnThis(),
    subscribe: jest.fn().mockReturnValue({
      unsubscribe: jest.fn()
    })
  }),
  auth: {
    signUp: jest.fn(),
    signIn: jest.fn(),
    signOut: jest.fn(),
    getUser: jest.fn(),
    getSession: jest.fn(),
    onAuthStateChange: jest.fn()
  },
  storage: {
    from: jest.fn().mockReturnValue({
      upload: jest.fn(),
      download: jest.fn(),
      remove: jest.fn(),
      list: jest.fn(),
      getPublicUrl: jest.fn()
    })
  }
}

// Mock the createClient function
const createClient = jest.fn().mockReturnValue(mockSupabaseClient)

module.exports = {
  createClient,
  mockSupabaseClient
}
