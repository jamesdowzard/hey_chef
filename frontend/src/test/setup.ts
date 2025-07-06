import '@testing-library/jest-dom'

// Mock WebSocket for tests
global.WebSocket = class MockWebSocket {
  constructor(url: string) {
    // Mock implementation
  }
  
  send(data: string) {
    // Mock implementation
  }
  
  close() {
    // Mock implementation
  }
  
  addEventListener() {
    // Mock implementation
  }
  
  removeEventListener() {
    // Mock implementation
  }
} as any

// Mock media devices for audio tests
Object.defineProperty(navigator, 'mediaDevices', {
  writable: true,
  value: {
    getUserMedia: vi.fn().mockResolvedValue({
      getTracks: () => [],
    }),
  },
})