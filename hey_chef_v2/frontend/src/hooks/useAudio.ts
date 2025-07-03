import { useState, useCallback, useEffect } from 'react';
import { useWebSocket } from './useWebSocket';
import { AudioState } from '../types';

const initialAudioState: AudioState = {
  isListening: false,
  isProcessing: false,
  isWaitingForWakeWord: false,
  volume: 0,
  error: null,
};

export const useAudio = () => {
  const [audioState, setAudioState] = useState<AudioState>(initialAudioState);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const { subscribe, unsubscribe, startAudioPipeline, stopAudioPipeline, isConnected } = useWebSocket();

  // Handle connection messages to get session ID
  const handleConnection = useCallback((message: any) => {
    const { status, session_id } = message.data;
    if (status === 'connected') {
      setSessionId(session_id);
      setAudioState(prev => ({ ...prev, error: null }));
    }
  }, []);

  // Handle audio status updates
  const handleAudioStatus = useCallback((message: any) => {
    const { status, message: statusMessage } = message.data;
    
    setAudioState(prev => {
      const newState = { ...prev };
      
      switch (status) {
        case 'started':
          newState.isWaitingForWakeWord = true;
          newState.isListening = false;
          newState.isProcessing = false;
          newState.error = null;
          break;
        case 'listening':
          newState.isListening = true;
          newState.isWaitingForWakeWord = false;
          newState.isProcessing = false;
          newState.error = null;
          break;
        case 'processing':
          newState.isListening = false;
          newState.isWaitingForWakeWord = false;
          newState.isProcessing = true;
          newState.error = null;
          break;
        case 'stopped':
          newState.isListening = false;
          newState.isWaitingForWakeWord = false;
          newState.isProcessing = false;
          newState.error = null;
          break;
        case 'error':
          newState.isListening = false;
          newState.isWaitingForWakeWord = false;
          newState.isProcessing = false;
          newState.error = statusMessage;
          break;
        default:
          // Unknown status, don't change state
          break;
      }
      
      return newState;
    });
  }, []);

  // Handle errors
  const handleError = useCallback((message: any) => {
    const { error, details } = message.data;
    setAudioState(prev => ({
      ...prev,
      isListening: false,
      isWaitingForWakeWord: false,
      isProcessing: false,
      error: `${error}: ${details}`,
    }));
  }, []);

  // Subscribe to WebSocket events
  useEffect(() => {
    subscribe('connection', handleConnection);
    subscribe('audio_status', handleAudioStatus);
    subscribe('error', handleError);

    return () => {
      unsubscribe('connection', handleConnection);
      unsubscribe('audio_status', handleAudioStatus);
      unsubscribe('error', handleError);
    };
  }, [subscribe, unsubscribe, handleConnection, handleAudioStatus, handleError]);

  // Start voice input (audio pipeline)
  const startVoiceInput = useCallback(() => {
    if (!isConnected()) {
      setAudioState(prev => ({ ...prev, error: 'Not connected to server' }));
      return;
    }

    if (audioState.isProcessing || audioState.isListening || audioState.isWaitingForWakeWord) {
      return; // Already active
    }

    try {
      startAudioPipeline();
      setAudioState(prev => ({ ...prev, error: null }));
    } catch (error) {
      setAudioState(prev => ({ 
        ...prev, 
        error: `Failed to start audio pipeline: ${error}` 
      }));
    }
  }, [startAudioPipeline, isConnected, audioState]);

  // Stop voice input (audio pipeline)
  const stopVoiceInput = useCallback(() => {
    if (!isConnected()) {
      setAudioState(prev => ({ ...prev, error: 'Not connected to server' }));
      return;
    }

    try {
      stopAudioPipeline();
      setAudioState(prev => ({ ...prev, error: null }));
    } catch (error) {
      setAudioState(prev => ({ 
        ...prev, 
        error: `Failed to stop audio pipeline: ${error}` 
      }));
    }
  }, [stopAudioPipeline, isConnected]);

  // Clear error
  const clearError = useCallback(() => {
    setAudioState(prev => ({ ...prev, error: null }));
  }, []);

  // Simulate volume updates for listening state
  useEffect(() => {
    if (!audioState.isListening) {
      setAudioState(prev => ({ ...prev, volume: 0 }));
      return;
    }

    // Simple volume simulation while listening
    const interval = setInterval(() => {
      setAudioState(prev => {
        if (!prev.isListening) return prev;
        
        // Generate random volume between 20-80 to simulate voice activity
        const volume = Math.floor(Math.random() * 60) + 20;
        return { ...prev, volume };
      });
    }, 200);

    return () => clearInterval(interval);
  }, [audioState.isListening]);

  return {
    audioState,
    sessionId,
    startVoiceInput,
    stopVoiceInput,
    clearError,
  };
};