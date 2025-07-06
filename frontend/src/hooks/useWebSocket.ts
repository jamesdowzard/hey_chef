import { useEffect, useRef, useCallback } from 'react';
import { websocketService, WebSocketEventHandler } from '../services/websocket';

export const useWebSocket = () => {
  const handlersRef = useRef<Map<string, WebSocketEventHandler[]>>(new Map());

  const subscribe = useCallback((eventType: string, handler: WebSocketEventHandler) => {
    if (!handlersRef.current.has(eventType)) {
      handlersRef.current.set(eventType, []);
    }
    handlersRef.current.get(eventType)!.push(handler);
    websocketService.on(eventType, handler);
  }, []);

  const unsubscribe = useCallback((eventType: string, handler: WebSocketEventHandler) => {
    const handlers = handlersRef.current.get(eventType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
    websocketService.off(eventType, handler);
  }, []);

  const connect = useCallback(() => {
    return websocketService.connect();
  }, []);

  const disconnect = useCallback(() => {
    websocketService.disconnect();
  }, []);

  const sendMessage = useCallback((message: any) => {
    websocketService.sendMessage(message);
  }, []);

  const sendTextMessage = useCallback((text: string, chefMode: string = 'normal') => {
    websocketService.sendTextMessage(text, chefMode);
  }, []);

  const startAudioPipeline = useCallback((recipeText?: string) => {
    websocketService.startAudioPipeline(recipeText);
  }, []);

  const stopAudioPipeline = useCallback(() => {
    websocketService.stopAudioPipeline();
  }, []);

  const loadRecipe = useCallback((recipeData: any) => {
    websocketService.loadRecipe(recipeData);
  }, []);

  const updateSettings = useCallback((settings: any) => {
    websocketService.updateSettings(settings);
  }, []);

  const isConnected = useCallback(() => {
    return websocketService.isConnected();
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      handlersRef.current.forEach((handlers, eventType) => {
        handlers.forEach(handler => {
          websocketService.off(eventType, handler);
        });
      });
      handlersRef.current.clear();
    };
  }, []);

  return {
    subscribe,
    unsubscribe,
    connect,
    disconnect,
    sendMessage,
    sendTextMessage,
    startAudioPipeline,
    stopAudioPipeline,
    loadRecipe,
    updateSettings,
    isConnected,
  };
};