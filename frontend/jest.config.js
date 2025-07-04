const nextJest = require("next/jest");

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files
  dir: "./",
});

// Add any custom config to be passed to Jest
const customJestConfig = {
  // Add more setup options before each test is run
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],

  // Test environment
  testEnvironment: "jest-environment-jsdom",

  // Module name mapping for path aliases
  moduleNameMapper: {
    // Handle module aliases (this will be automatically configured for you based on your tsconfig.json paths)
    "^@/(.*)$": "<rootDir>/src/$1",
    "^@/components/(.*)$": "<rootDir>/src/components/$1",
    "^@/lib/(.*)$": "<rootDir>/src/lib/$1",
    "^@/hooks/(.*)$": "<rootDir>/src/hooks/$1",
    "^@/types/(.*)$": "<rootDir>/src/types/$1",
    "^@/utils/(.*)$": "<rootDir>/src/utils/$1",
    "^@/styles/(.*)$": "<rootDir>/src/styles/$1",
    "^@/public/(.*)$": "<rootDir>/src/public/$1",
    // Mock problematic ES modules
    "^@supabase/supabase-js$": "<rootDir>/src/__mocks__/@supabase/supabase-js.js",
  },

  // Test file patterns
  testMatch: [
    "<rootDir>/src/**/__tests__/**/*.{js,jsx,ts,tsx}",
    "<rootDir>/src/**/*.(test|spec).{js,jsx,ts,tsx}",
    "<rootDir>/__tests__/**/*.{js,jsx,ts,tsx}",
  ],

  // Files to ignore
  testPathIgnorePatterns: [
    "<rootDir>/.next/",
    "<rootDir>/node_modules/",
    "<rootDir>/out/",
    "<rootDir>/build/",
  ],

  // Transform configuration
  transform: {
    // Use babel-jest to transpile tests with the next/babel preset
    // https://jestjs.io/docs/configuration#transform-string-pathtotransformer--pathtotransformer-object
    "^.+\\.(js|jsx|ts|tsx)$": ["babel-jest", { presets: ["next/babel"] }],
  },

  // Transform ignore patterns - allow transformation of Supabase ES modules
  transformIgnorePatterns: [
    "/node_modules/(?!(@supabase|isows|@supabase/realtime-js|@supabase/supabase-js)/)",
    "^.+\\.module\\.(css|sass|scss)$",
  ],

  // Module file extensions
  moduleFileExtensions: ["ts", "tsx", "js", "jsx", "json", "node"],

  // Coverage configuration
  collectCoverageFrom: [
    "src/**/*.{js,jsx,ts,tsx}",
    "!src/**/*.d.ts",
    "!src/**/*.stories.{js,jsx,ts,tsx}",
    "!src/**/*.test.{js,jsx,ts,tsx}",
    "!src/**/*.spec.{js,jsx,ts,tsx}",
    "!src/**/index.{js,jsx,ts,tsx}",
    "!src/app/layout.tsx",
    "!src/app/globals.css",
  ],

  // Coverage thresholds
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },

  // Coverage reporters
  coverageReporters: ["text", "lcov", "html"],

  // Coverage directory
  coverageDirectory: "coverage",

  // Clear mocks between tests
  clearMocks: true,

  // Restore mocks after each test
  restoreMocks: true,

  // Verbose output
  verbose: true,

  // Test timeout
  testTimeout: 10000,

  // Global setup and teardown
  // globalSetup: '<rootDir>/jest.global-setup.js',
  // globalTeardown: '<rootDir>/jest.global-teardown.js',

  // Custom resolver for handling module resolution
  // resolver: '<rootDir>/jest.resolver.js',

  // Watch plugins - commented out due to version compatibility issues
  // watchPlugins: [
  //   'jest-watch-typeahead/filename',
  //   'jest-watch-typeahead/testname',
  // ],
};

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig);
