import React from 'react';
import { Mic, MicOff, Volume2, AlertCircle } from 'lucide-react';
import { useAudio } from '../hooks/useAudio';

interface VoiceControllerProps {
  className?: string;
}

export const VoiceController: React.FC<VoiceControllerProps> = ({ className = '' }) => {
  const { audioState, startVoiceInput, stopVoiceInput, clearError } = useAudio();

  const getStatusColor = () => {
    if (audioState.error) return 'text-red-500';
    if (audioState.isProcessing) return 'text-yellow-500';
    if (audioState.isListening) return 'text-green-500';
    if (audioState.isWaitingForWakeWord) return 'text-blue-500';
    return 'text-gray-500';
  };

  const getStatusMessage = () => {
    if (audioState.error) return audioState.error;
    if (audioState.isProcessing) return 'Processing your request...';
    if (audioState.isListening) return 'Listening... Speak now';
    if (audioState.isWaitingForWakeWord) return 'Waiting for "Hey Chef"';
    return 'Voice control ready';
  };

  const getMicrophoneIcon = () => {
    if (audioState.isListening) {
      return <Mic className="w-8 h-8" />;
    }
    return <MicOff className="w-8 h-8" />;
  };

  const handleMicrophoneClick = () => {
    if (audioState.error) {
      clearError();
      return;
    }

    if (audioState.isListening) {
      stopVoiceInput();
    } else {
      startVoiceInput();
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-800">Voice Control</h2>
        <div className="flex items-center space-x-2">
          {audioState.error && (
            <AlertCircle className="w-5 h-5 text-red-500" />
          )}
          <Volume2 className="w-5 h-5 text-gray-500" />
        </div>
      </div>

      <div className="flex flex-col items-center space-y-4">
        {/* Microphone Button */}
        <button
          onClick={handleMicrophoneClick}
          disabled={audioState.isProcessing}
          className={`
            relative w-20 h-20 rounded-full border-4 transition-all duration-200 
            ${audioState.isListening 
              ? 'bg-green-100 border-green-500 hover:bg-green-200' 
              : audioState.error
              ? 'bg-red-100 border-red-500 hover:bg-red-200'
              : 'bg-gray-100 border-gray-300 hover:bg-gray-200'
            }
            ${audioState.isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            flex items-center justify-center
          `}
        >
          {audioState.isProcessing ? (
            <div className="animate-spin w-8 h-8 border-3 border-primary-500 border-t-transparent rounded-full" />
          ) : (
            <span className={getStatusColor()}>
              {getMicrophoneIcon()}
            </span>
          )}
          
          {/* Pulse animation for listening state */}
          {audioState.isListening && (
            <div className="absolute inset-0 rounded-full border-4 border-green-500 animate-pulse-slow opacity-75" />
          )}
        </button>

        {/* Status Message */}
        <div className="text-center">
          <p className={`font-medium ${getStatusColor()}`}>
            {getStatusMessage()}
          </p>
        </div>

        {/* Volume Indicator */}
        {audioState.isListening && (
          <div className="w-full max-w-xs">
            <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
              <span>Volume</span>
              <span>{audioState.volume}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all duration-150"
                style={{ width: `${audioState.volume}%` }}
              />
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="flex space-x-4 pt-4">
          <button
            onClick={startVoiceInput}
            disabled={audioState.isListening || audioState.isProcessing}
            className={`
              px-4 py-2 rounded-lg font-medium transition-colors
              ${audioState.isListening || audioState.isProcessing
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-primary-500 hover:bg-primary-600 text-white'
              }
            `}
          >
            Start Listening
          </button>
          <button
            onClick={stopVoiceInput}
            disabled={!audioState.isListening}
            className={`
              px-4 py-2 rounded-lg font-medium transition-colors
              ${!audioState.isListening
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-red-500 hover:bg-red-600 text-white'
              }
            `}
          >
            Stop Listening
          </button>
        </div>
      </div>
    </div>
  );
};