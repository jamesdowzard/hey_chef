/**
 * Test utilities for Hey Chef v2 frontend tests.
 */

import React, { ReactElement, ReactNode } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';

// Mock providers wrapper
interface ProvidersProps {
  children: ReactNode;
}

const AllTheProviders: React.FC<ProvidersProps> = ({ children }) => {
  return (
    <BrowserRouter>
      {children}
    </BrowserRouter>
  );
};

// Custom render function with providers
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  return render(ui, { wrapper: AllTheProviders, ...options });
};

// Custom user event setup
const setupUserEvent = () => {
  return userEvent.setup();
};

// Mock WebSocket for tests
export class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  public readyState = MockWebSocket.OPEN;
  public onopen: ((event: Event) => void) | null = null;
  public onclose: ((event: CloseEvent) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;

  constructor(public url: string) {
    setTimeout(() => {
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 0);
  }

  send(data: string | ArrayBufferLike | Blob | ArrayBufferView) {
    // Mock send - in tests, you can override this behavior
  }

  close(code?: number, reason?: string) {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code, reason }));
    }
  }

  addEventListener(type: string, listener: EventListener) {
    if (type === 'open' && this.onopen === null) {
      this.onopen = listener as (event: Event) => void;
    } else if (type === 'close' && this.onclose === null) {
      this.onclose = listener as (event: CloseEvent) => void;
    } else if (type === 'message' && this.onmessage === null) {
      this.onmessage = listener as (event: MessageEvent) => void;
    } else if (type === 'error' && this.onerror === null) {
      this.onerror = listener as (event: Event) => void;
    }
  }

  removeEventListener(type: string, listener: EventListener) {
    if (type === 'open' && this.onopen === listener) {
      this.onopen = null;
    } else if (type === 'close' && this.onclose === listener) {
      this.onclose = null;
    } else if (type === 'message' && this.onmessage === listener) {
      this.onmessage = null;
    } else if (type === 'error' && this.onerror === listener) {
      this.onerror = null;
    }
  }

  // Helper method to simulate receiving a message
  simulateMessage(data: any) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }));
    }
  }

  // Helper method to simulate an error
  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }
}

// Mock MediaRecorder for audio recording tests
export class MockMediaRecorder {
  static isTypeSupported = jest.fn(() => true);

  public state: RecordingState = 'inactive';
  public ondataavailable: ((event: BlobEvent) => void) | null = null;
  public onstart: ((event: Event) => void) | null = null;
  public onstop: ((event: Event) => void) | null = null;
  public onerror: ((event: MediaRecorderErrorEvent) => void) | null = null;

  constructor(public stream: MediaStream, public options?: MediaRecorderOptions) {}

  start(timeslice?: number) {
    this.state = 'recording';
    if (this.onstart) {
      this.onstart(new Event('start'));
    }
  }

  stop() {
    this.state = 'inactive';
    if (this.ondataavailable) {
      const blob = new Blob(['mock audio data'], { type: 'audio/wav' });
      this.ondataavailable(new BlobEvent('dataavailable', { data: blob }));
    }
    if (this.onstop) {
      this.onstop(new Event('stop'));
    }
  }

  pause() {
    this.state = 'paused';
  }

  resume() {
    this.state = 'recording';
  }

  requestData() {
    if (this.ondataavailable) {
      const blob = new Blob(['mock audio data'], { type: 'audio/wav' });
      this.ondataavailable(new BlobEvent('dataavailable', { data: blob }));
    }
  }

  addEventListener(type: string, listener: EventListener) {
    if (type === 'dataavailable' && this.ondataavailable === null) {
      this.ondataavailable = listener as (event: BlobEvent) => void;
    } else if (type === 'start' && this.onstart === null) {
      this.onstart = listener as (event: Event) => void;
    } else if (type === 'stop' && this.onstop === null) {
      this.onstop = listener as (event: Event) => void;
    } else if (type === 'error' && this.onerror === null) {
      this.onerror = listener as (event: MediaRecorderErrorEvent) => void;
    }
  }

  removeEventListener(type: string, listener: EventListener) {
    if (type === 'dataavailable' && this.ondataavailable === listener) {
      this.ondataavailable = null;
    } else if (type === 'start' && this.onstart === listener) {
      this.onstart = null;
    } else if (type === 'stop' && this.onstop === listener) {
      this.onstop = null;
    } else if (type === 'error' && this.onerror === listener) {
      this.onerror = null;
    }
  }
}

// Test data factories for frontend components
export const createMockRecipe = (overrides = {}) => ({
  id: 'test-recipe-1',
  title: 'Test Recipe',
  description: 'A test recipe for unit tests',
  prep_time: 15,
  cook_time: 30,
  servings: 4,
  category: 'main_course',
  ingredients: [
    '1 cup ingredient 1',
    '2 tbsp ingredient 2',
    '3 cloves ingredient 3'
  ],
  instructions: [
    'Step 1: Do something',
    'Step 2: Do something else',
    'Step 3: Finish the recipe'
  ],
  currentStep: 0,
  ...overrides
});

export const createMockWebSocketMessage = (type: string, data: any = {}) => ({
  type,
  data,
  session_id: 'test-session-123',
  timestamp: new Date().toISOString()
});

export const createMockAudioData = () => {
  const arrayBuffer = new ArrayBuffer(1024);
  return new Uint8Array(arrayBuffer);
};

// Helper functions for testing async operations
export const waitForAsync = () => new Promise(resolve => setTimeout(resolve, 0));

export const waitForState = async (
  getState: () => any,
  expectedState: any,
  timeout = 1000
) => {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    if (getState() === expectedState) {
      return;
    }
    await new Promise(resolve => setTimeout(resolve, 10));
  }
  throw new Error(`State did not reach expected value within ${timeout}ms`);
};

// Audio testing utilities
export const mockAudioContext = () => {
  const mockAudioContext = {
    createAnalyser: jest.fn(() => ({
      frequencyBinCount: 1024,
      getByteFrequencyData: jest.fn(),
      connect: jest.fn(),
      disconnect: jest.fn(),
    })),
    createMediaStreamSource: jest.fn(() => ({
      connect: jest.fn(),
      disconnect: jest.fn(),
    })),
    resume: jest.fn().mockResolvedValue(undefined),
    suspend: jest.fn().mockResolvedValue(undefined),
    close: jest.fn().mockResolvedValue(undefined),
    state: 'running',
    sampleRate: 44100,
  };

  // @ts-ignore
  global.AudioContext = jest.fn(() => mockAudioContext);
  // @ts-ignore
  global.webkitAudioContext = jest.fn(() => mockAudioContext);

  return mockAudioContext;
};

// Export everything
export * from '@testing-library/react';
export { customRender as render, setupUserEvent };

// Re-export commonly used testing utilities
export { userEvent };
export { screen, waitFor, act } from '@testing-library/react';