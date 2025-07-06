/**
 * Jest setup file for Hey Chef v2 frontend tests.
 */

import '@testing-library/jest-dom';
import { configure } from '@testing-library/react';
import { server } from './mocks/server';

// Configure React Testing Library
configure({
  testIdAttribute: 'data-testid',
  defaultHidden: true,
});

// Mock console methods for cleaner test output
const originalError = console.error;
const originalWarn = console.warn;

beforeAll(() => {
  // Start Mock Service Worker
  server.listen({
    onUnhandledRequest: 'error',
  });

  // Mock console methods to reduce noise in tests
  console.error = (...args: any[]) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is no longer supported')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };

  console.warn = (...args: any[]) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning:') || args[0].includes('React Router'))
    ) {
      return;
    }
    originalWarn.call(console, ...args);
  };
});

afterEach(() => {
  // Reset MSW handlers after each test
  server.resetHandlers();
  
  // Clear any mocks
  jest.clearAllMocks();
});

afterAll(() => {
  // Clean up MSW
  server.close();
  
  // Restore console methods
  console.error = originalError;
  console.warn = originalWarn;
});

// Mock window.matchMedia (often needed for responsive components)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock window.ResizeObserver (used by some components)
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock HTMLMediaElement (for audio/video elements)
Object.defineProperty(HTMLMediaElement.prototype, 'play', {
  writable: true,
  value: jest.fn().mockResolvedValue(undefined),
});

Object.defineProperty(HTMLMediaElement.prototype, 'pause', {
  writable: true,
  value: jest.fn(),
});

Object.defineProperty(HTMLMediaElement.prototype, 'load', {
  writable: true,
  value: jest.fn(),
});

// Mock navigator.mediaDevices (for audio recording)
Object.defineProperty(navigator, 'mediaDevices', {
  writable: true,
  value: {
    getUserMedia: jest.fn().mockResolvedValue({
      getTracks: () => [
        {
          stop: jest.fn(),
          getSettings: () => ({ deviceId: 'mock-device' }),
        },
      ],
    }),
    enumerateDevices: jest.fn().mockResolvedValue([
      {
        deviceId: 'mock-device-1',
        label: 'Mock Microphone 1',
        kind: 'audioinput',
      },
      {
        deviceId: 'mock-device-2',
        label: 'Mock Microphone 2',
        kind: 'audioinput',
      },
    ]),
  },
});

// Mock WebSocket for testing
global.WebSocket = jest.fn().mockImplementation(() => ({
  send: jest.fn(),
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  readyState: WebSocket.OPEN,
})) as any;

// Mock IntersectionObserver (used by some UI libraries)
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock requestAnimationFrame
global.requestAnimationFrame = jest.fn((cb) => setTimeout(cb, 0));
global.cancelAnimationFrame = jest.fn((id) => clearTimeout(id));

// Mock localStorage and sessionStorage
const createStorage = () => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
    get length() {
      return Object.keys(store).length;
    },
    key: (index: number) => Object.keys(store)[index] || null,
  };
};

Object.defineProperty(window, 'localStorage', {
  value: createStorage(),
});

Object.defineProperty(window, 'sessionStorage', {
  value: createStorage(),
});

// Export test utilities
export * from '@testing-library/react';
export * from '@testing-library/user-event';
export { default as userEvent } from '@testing-library/user-event';