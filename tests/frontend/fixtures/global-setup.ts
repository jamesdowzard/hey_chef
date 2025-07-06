/**
 * Global setup for Hey Chef v2 frontend tests.
 */

export default async function globalSetup() {
  // Set environment variables for testing
  process.env.NODE_ENV = 'test';
  process.env.VITE_API_URL = 'http://localhost:8000';
  process.env.VITE_WS_URL = 'ws://localhost:8000';

  // Any global setup logic can go here
  console.log('Setting up frontend test environment...');
}