import { WebSocketMessage } from '../types';

export type WebSocketEventHandler = (message: WebSocketMessage) => void;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 1000;
  private isIntentionallyClosed = false;
  private eventHandlers: Map<string, WebSocketEventHandler[]> = new Map();

  constructor(url: string = 'ws://localhost:8000/ws/audio') {
    this.url = url;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);
        this.isIntentionallyClosed = false;

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.emit('status', {
            type: 'status',
            data: { status: 'idle', message: 'Connected to server' },
            timestamp: new Date().toISOString()
          });
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.ws = null;
          
          this.emit('status', {
            type: 'status',
            data: { status: 'error', message: 'Disconnected from server' },
            timestamp: new Date().toISOString()
          });

          if (!this.isIntentionallyClosed && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.attemptReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.emit('error', {
            type: 'error',
            data: { message: 'WebSocket connection error' },
            timestamp: new Date().toISOString()
          });
          reject(error);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect(): void {
    this.isIntentionallyClosed = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  private attemptReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);
    
    setTimeout(() => {
      this.connect().catch(console.error);
    }, delay);
  }

  private handleMessage(message: WebSocketMessage): void {
    this.emit(message.type, message);
  }

  private emit(eventType: string, message: WebSocketMessage): void {
    const handlers = this.eventHandlers.get(eventType) || [];
    handlers.forEach(handler => handler(message));
  }

  on(eventType: string, handler: WebSocketEventHandler): void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, []);
    }
    this.eventHandlers.get(eventType)!.push(handler);
  }

  off(eventType: string, handler: WebSocketEventHandler): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  sendMessage(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  sendAudioData(audioData: Blob): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(audioData);
    }
  }

  startAudioPipeline(recipeText?: string): void {
    this.sendMessage({
      type: 'audio_start',
      data: { recipe_text: recipeText || '' },
      timestamp: Date.now() / 1000
    });
  }

  stopAudioPipeline(): void {
    this.sendMessage({
      type: 'audio_stop',
      data: {},
      timestamp: Date.now() / 1000
    });
  }

  loadRecipe(recipeData: any): void {
    this.sendMessage({
      type: 'recipe_load',
      data: recipeData,
      timestamp: Date.now() / 1000
    });
  }

  updateSettings(settings: any): void {
    this.sendMessage({
      type: 'settings_update',
      data: settings,
      timestamp: Date.now() / 1000
    });
  }

  sendTextMessage(text: string, chefMode: string = 'normal'): void {
    this.sendMessage({
      type: 'text_message',
      data: { text, chefMode },
      timestamp: new Date().toISOString()
    });
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
export const websocketService = new WebSocketService();