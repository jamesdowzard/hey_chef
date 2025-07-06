import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Volume2, Clock } from 'lucide-react';
import { ChatMessage, ChefMode } from '../types';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  isProcessing: boolean;
  chefMode: ChefMode;
  className?: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  onSendMessage,
  isProcessing,
  chefMode,
  className = ''
}) => {
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMessage.trim() && !isProcessing) {
      onSendMessage(inputMessage.trim());
      setInputMessage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const playAudio = (audioUrl: string) => {
    const audio = new Audio(audioUrl);
    audio.play().catch(console.error);
  };

  const getChefModeColor = () => {
    switch (chefMode) {
      case 'sassy': return 'text-purple-600';
      case 'gordon_ramsay': return 'text-red-600';
      default: return 'text-primary-600';
    }
  };

  const getChefModeName = () => {
    switch (chefMode) {
      case 'sassy': return 'Sassy Chef';
      case 'gordon_ramsay': return 'Gordon Ramsay';
      default: return 'Chef';
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-lg flex flex-col ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-800">Chat with Chef</h2>
          <div className={`text-sm font-medium ${getChefModeColor()}`}>
            {getChefModeName()} Mode
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 min-h-0" style={{ maxHeight: '400px' }}>
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <Bot className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p className="text-lg font-medium mb-2">Ready to help with your cooking!</p>
            <p className="text-sm">Ask me about recipes, cooking techniques, or ingredients.</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`
                  max-w-xs lg:max-w-md px-4 py-3 rounded-lg
                  ${message.type === 'user'
                    ? 'bg-primary-500 text-white'
                    : message.type === 'system'
                    ? 'bg-gray-100 text-gray-700 border border-gray-200'
                    : 'bg-gray-50 text-gray-800 border border-gray-200'
                  }
                `}
              >
                {/* Message Header */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {message.type === 'user' ? (
                      <User className="w-4 h-4" />
                    ) : message.type === 'system' ? (
                      <Bot className="w-4 h-4 text-gray-500" />
                    ) : (
                      <Bot className={`w-4 h-4 ${getChefModeColor()}`} />
                    )}
                    <span className="text-xs opacity-75 flex items-center">
                      <Clock className="w-3 h-3 mr-1" />
                      {formatTimestamp(message.timestamp)}
                    </span>
                  </div>
                  {message.audioUrl && (
                    <button
                      onClick={() => playAudio(message.audioUrl!)}
                      className="p-1 rounded-full hover:bg-black hover:bg-opacity-10 transition-colors"
                    >
                      <Volume2 className="w-4 h-4" />
                    </button>
                  )}
                </div>

                {/* Message Content */}
                <div className="text-sm leading-relaxed">
                  {message.isStreaming ? (
                    <div className="flex items-center space-x-1">
                      <span>{message.content}</span>
                      <div className="animate-pulse">
                        <div className="w-2 h-4 bg-current opacity-75 rounded"></div>
                      </div>
                    </div>
                  ) : (
                    <span>{message.content}</span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}

        {/* Processing Indicator */}
        {isProcessing && (
          <div className="flex justify-start">
            <div className="bg-gray-50 border border-gray-200 px-4 py-3 rounded-lg max-w-xs">
              <div className="flex items-center space-x-2">
                <Bot className={`w-4 h-4 ${getChefModeColor()}`} />
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-6 border-t border-gray-200">
        <form onSubmit={handleSubmit} className="flex space-x-4">
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me about cooking..."
            disabled={isProcessing}
            className={`
              flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
              ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}
            `}
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || isProcessing}
            className={`
              px-6 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2
              ${!inputMessage.trim() || isProcessing
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-primary-500 hover:bg-primary-600 text-white'
              }
            `}
          >
            <Send className="w-4 h-4" />
            <span>Send</span>
          </button>
        </form>
      </div>
    </div>
  );
};