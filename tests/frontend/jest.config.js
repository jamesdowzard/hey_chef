/**
 * Jest configuration for Hey Chef v2 frontend tests.
 */

module.exports = {
  preset: '@testing-library/jest-dom',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/tests/frontend/fixtures/setup.ts'],
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/frontend/src/$1',
    '^@components/(.*)$': '<rootDir>/frontend/src/components/$1',
    '^@services/(.*)$': '<rootDir>/frontend/src/services/$1',
    '^@hooks/(.*)$': '<rootDir>/frontend/src/hooks/$1',
    '^@utils/(.*)$': '<rootDir>/frontend/src/utils/$1',
    '^@types/(.*)$': '<rootDir>/frontend/src/types/$1'
  },
  testMatch: [
    '<rootDir>/tests/frontend/unit/**/*.test.{ts,tsx}',
    '<rootDir>/tests/frontend/integration/**/*.test.{ts,tsx}'
  ],
  collectCoverageFrom: [
    'frontend/src/**/*.{ts,tsx}',
    '!frontend/src/**/*.d.ts',
    '!frontend/src/main.tsx',
    '!frontend/src/vite-env.d.ts'
  ],
  coverageDirectory: '<rootDir>/coverage/frontend',
  coverageReporters: ['text', 'lcov', 'html'],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70
    }
  },
  transform: {
    '^.+\\.tsx?$': ['ts-jest', {
      tsconfig: 'frontend/tsconfig.json'
    }]
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
  testTimeout: 10000,
  verbose: true,
  roots: ['<rootDir>/tests/frontend'],
  globalSetup: '<rootDir>/tests/frontend/fixtures/global-setup.ts',
  globalTeardown: '<rootDir>/tests/frontend/fixtures/global-teardown.ts'
};