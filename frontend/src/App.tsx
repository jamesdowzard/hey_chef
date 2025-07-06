import React, { useState, useEffect, useCallback } from 'react';
import { ChefHat, Wifi, WifiOff, Menu, X } from 'lucide-react';
import { VoiceController } from './components/VoiceController';
import { ChatInterface } from './components/ChatInterface';
import { RecipeViewer } from './components/RecipeViewer';
import { RecipeList } from './components/RecipeList';
import { SettingsPanel } from './components/SettingsPanel';
import { useWebSocket } from './hooks/useWebSocket';
import { useRecipes } from './hooks/useRecipes';
import { AppSettings, ChatMessage } from './types';
import { apiService } from './services/api';

const defaultSettings: AppSettings = {
  audio: {
    wakeWordEnabled: true,
    microphoneEnabled: true,
    speakerEnabled: true,
    volume: 75,
    speechRate: 1.0,
    voiceType: 'system',
  },
  ui: {
    theme: 'light',
    compactMode: false,
    showTimestamps: true,
  },
  chef: {
    mode: 'normal',
    streamingEnabled: true,
    contextMemory: true,
  },
};

export const App: React.FC = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [settings, setSettings] = useState<AppSettings>(defaultSettings);
  const [activeTab, setActiveTab] = useState<'chat' | 'recipe' | 'settings'>('chat');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [recipeView, setRecipeView] = useState<'list' | 'detail'>('list');

  // Health check states
  const [apiKeyValid, setApiKeyValid] = useState<boolean | null>(null);
  const [audioServiceHealthy, setAudioServiceHealthy] = useState<boolean | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected');

  const { subscribe, unsubscribe, connect, disconnect, sendTextMessage, startAudioPipeline, stopAudioPipeline, loadRecipe } = useWebSocket();
  const { 
    recipes, 
    currentRecipe, 
    categories,
    hasMore,
    loadRecipe: selectRecipe,
    loadMoreRecipes,
    searchRecipes,
    filterByCategory,
    setRecipeStep 
  } = useRecipes();

  // Health check functions
  const checkApiKeyHealth = useCallback(async () => {
    try {
      const result = await apiService.validateApiKeys();
      setApiKeyValid(result.openai_valid || false);
    } catch (error) {
      console.error('API key validation failed:', error);
      setApiKeyValid(false);
    }
  }, []);

  const checkAudioServiceHealth = useCallback(async () => {
    try {
      const result = await apiService.getAudioHealth();
      setAudioServiceHealthy(result.status === 'healthy');
    } catch (error) {
      console.error('Audio service health check failed:', error);
      setAudioServiceHealthy(false);
    }
  }, []);

  const checkOverallHealth = useCallback(async () => {
    try {
      await apiService.healthCheck();
      // If we reach here, backend is responding
    } catch (error) {
      console.error('General health check failed:', error);
    }
  }, []);

  // Initialize WebSocket connection
  useEffect(() => {
    const initConnection = async () => {
      try {
        setConnectionStatus('connecting');
        await connect();
        setIsConnected(true);
        setConnectionStatus('connected');
      } catch (error) {
        console.error('Failed to connect to WebSocket:', error);
        setIsConnected(false);
        setConnectionStatus('disconnected');
      }
    };

    initConnection();

    return () => {
      disconnect();
      setConnectionStatus('disconnected');
    };
  }, [connect, disconnect]);

  // Perform initial health checks and set up intervals
  useEffect(() => {
    // Initial health checks
    checkOverallHealth();
    checkApiKeyHealth();
    checkAudioServiceHealth();

    // Set up health check intervals
    const healthCheckInterval = setInterval(() => {
      checkOverallHealth();
      checkApiKeyHealth();
      checkAudioServiceHealth();
    }, 30000); // Check every 30 seconds

    return () => {
      clearInterval(healthCheckInterval);
    };
  }, [checkOverallHealth, checkApiKeyHealth, checkAudioServiceHealth]);

  // Handle WebSocket messages
  const handleConnection = useCallback((message: any) => {
    const { status, session_id } = message.data;
    if (status === 'connected') {
      setIsConnected(true);
      setConnectionStatus('connected');
      console.log('Connected with session ID:', session_id);
    } else if (status === 'disconnected') {
      setIsConnected(false);
      setConnectionStatus('disconnected');
    }
  }, []);

  const handleAudioStatus = useCallback((message: any) => {
    const { status, message: statusMessage } = message.data;
    console.log('Audio status:', status, statusMessage);
    
    // Update processing state based on audio status
    setIsProcessing(status === 'processing' || status === 'listening' || status === 'started');
    
    // Add status message to chat if it's important
    if (status === 'error' || status === 'started' || status === 'stopped') {
      const systemMessage: ChatMessage = {
        id: Date.now().toString(),
        content: statusMessage,
        timestamp: new Date(),
        type: 'system',
      };
      setChatMessages(prev => [...prev, systemMessage]);
    }
  }, []);

  const handleRecipeLoaded = useCallback((message: any) => {
    const { status, recipe_title } = message.data;
    if (status === 'success') {
      const systemMessage: ChatMessage = {
        id: Date.now().toString(),
        content: `Recipe loaded: ${recipe_title}`,
        timestamp: new Date(),
        type: 'system',
      };
      setChatMessages(prev => [...prev, systemMessage]);
    }
  }, []);

  const handleError = useCallback((message: any) => {
    const { error, details } = message.data;
    const errorMessage: ChatMessage = {
      id: Date.now().toString(),
      content: `Error: ${error}. ${details}`,
      timestamp: new Date(),
      type: 'system',
    };
    setChatMessages(prev => [...prev, errorMessage]);
    setIsProcessing(false);
    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  // Subscribe to WebSocket events
  useEffect(() => {
    subscribe('connection', handleConnection);
    subscribe('audio_status', handleAudioStatus);
    subscribe('recipe_loaded', handleRecipeLoaded);
    subscribe('error', handleError);

    return () => {
      unsubscribe('connection', handleConnection);
      unsubscribe('audio_status', handleAudioStatus);
      unsubscribe('recipe_loaded', handleRecipeLoaded);
      unsubscribe('error', handleError);
    };
  }, [subscribe, unsubscribe, handleConnection, handleAudioStatus, handleRecipeLoaded, handleError]);

  // Handle sending messages
  const handleSendMessage = useCallback((message: string) => {
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: message,
      timestamp: new Date(),
      type: 'user',
    };
    setChatMessages(prev => [...prev, userMessage]);
    
    setIsProcessing(true);
    sendTextMessage(message, settings.chef.mode);
  }, [sendTextMessage, settings.chef.mode]);

  // Handle settings changes
  const handleSettingsChange = useCallback((newSettings: AppSettings) => {
    setSettings(newSettings);
    // Save to localStorage
    localStorage.setItem('heyChefSettings', JSON.stringify(newSettings));
  }, []);

  // Handle recipe selection
  const handleRecipeSelect = useCallback((recipe: any) => {
    selectRecipe(recipe.id);
    setRecipeView('detail');
    loadRecipe(recipe); // Notify WebSocket
  }, [selectRecipe, loadRecipe]);

  // Load settings from localStorage on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('heyChefSettings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings({ ...defaultSettings, ...parsed });
      } catch (error) {
        console.error('Failed to parse saved settings:', error);
      }
    }
  }, []);

  const ConnectionIndicator = () => (
    <div className={`flex items-center space-x-2 ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
      {isConnected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
      <span className="text-sm font-medium">
        {isConnected ? 'Connected' : 'Disconnected'}
      </span>
    </div>
  );

  return (
    <div data-testid="app-container" className={`min-h-screen ${settings.ui.theme === 'dark' ? 'dark bg-gray-900' : 'bg-gray-50'}`}>
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center space-x-3">
              <ChefHat className="w-8 h-8 text-primary-500" />
              <h1 className="text-xl font-bold text-gray-900">Hey Chef</h1>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex space-x-6">
              <button
                onClick={() => setActiveTab('chat')}
                className={`text-sm font-medium transition-colors ${
                  activeTab === 'chat' ? 'text-primary-600' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Chat
              </button>
              <button
                onClick={() => setActiveTab('recipe')}
                className={`text-sm font-medium transition-colors ${
                  activeTab === 'recipe' ? 'text-primary-600' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Recipe
              </button>
              <button
                onClick={() => setActiveTab('settings')}
                className={`text-sm font-medium transition-colors ${
                  activeTab === 'settings' ? 'text-primary-600' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Settings
              </button>
            </nav>

            {/* Connection Status & Mobile Menu */}
            <div className="flex items-center space-x-4">
              <ConnectionIndicator />
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="md:hidden p-2 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              >
                {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation */}
        {sidebarOpen && (
          <div className="md:hidden border-t border-gray-200 bg-white">
            <div className="px-4 py-3 space-y-2">
              <button
                onClick={() => {
                  setActiveTab('chat');
                  setSidebarOpen(false);
                }}
                className={`block w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'chat' ? 'bg-primary-100 text-primary-700' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                Chat
              </button>
              <button
                onClick={() => {
                  setActiveTab('recipe');
                  setSidebarOpen(false);
                }}
                className={`block w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'recipe' ? 'bg-primary-100 text-primary-700' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                Recipe
              </button>
              <button
                onClick={() => {
                  setActiveTab('settings');
                  setSidebarOpen(false);
                }}
                className={`block w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'settings' ? 'bg-primary-100 text-primary-700' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                Settings
              </button>
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Voice Controller - Always visible on desktop, conditional on mobile */}
          <div className={`lg:col-span-1 ${activeTab !== 'chat' && 'hidden lg:block'}`}>
            <VoiceController />
          </div>

          {/* Main Content Area */}
          <div className="lg:col-span-3">
            {activeTab === 'chat' && (
              <ChatInterface
                messages={chatMessages}
                onSendMessage={handleSendMessage}
                isProcessing={isProcessing}
                chefMode={settings.chef.mode}
                className="h-[600px]"
              />
            )}

            {activeTab === 'recipe' && (
              <>
                {recipeView === 'list' ? (
                  <RecipeList
                    recipes={recipes}
                    currentRecipe={currentRecipe.data}
                    categories={categories}
                    onRecipeSelect={handleRecipeSelect}
                    onLoadMore={loadMoreRecipes}
                    onSearch={searchRecipes}
                    onCategoryFilter={filterByCategory}
                    hasMore={hasMore}
                    className="h-[600px] overflow-y-auto"
                  />
                ) : (
                  <RecipeViewer
                    recipe={currentRecipe.data}
                    onStepChange={setRecipeStep}
                    onBackToList={() => setRecipeView('list')}
                    className="h-[600px] overflow-y-auto"
                  />
                )}
              </>
            )}

            {activeTab === 'settings' && (
              <SettingsPanel
                settings={settings}
                onSettingsChange={handleSettingsChange}
                connectionStatus={connectionStatus}
                apiKeyValid={apiKeyValid}
                audioServiceHealthy={audioServiceHealthy}
                className="h-[600px] overflow-y-auto"
              />
            )}
          </div>
        </div>
      </main>
    </div>
  );
};