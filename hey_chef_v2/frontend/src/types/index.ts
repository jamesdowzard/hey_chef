// Audio types
export interface AudioState {
  isListening: boolean;
  isProcessing: boolean;
  isWaitingForWakeWord: boolean;
  volume: number;
  error: string | null;
}

export interface AudioSettings {
  wakeWordEnabled: boolean;
  microphoneEnabled: boolean;
  speakerEnabled: boolean;
  volume: number;
  speechRate: number;
  voiceType: 'system' | 'openai';
}

// Recipe types
export interface Recipe {
  id: string;
  title: string;
  description?: string;
  ingredients: string[];
  instructions: string[];
  category?: string;
  prep_time?: number;
  cook_time?: number;
  servings?: number;
  created_at?: string;
  updated_at?: string;
  currentStep?: number;
}

// Legacy interfaces for backward compatibility
export interface Ingredient {
  id: string;
  name: string;
  amount: string;
  unit: string;
  notes?: string;
}

export interface Instruction {
  id: string;
  stepNumber: number;
  description: string;
  duration?: number;
  temperature?: string;
  notes?: string;
}

// Backend API request/response types
export interface RecipeSearchRequest {
  query: string;
  limit?: number;
  category?: string;
}

export interface RecipeCreateRequest {
  title: string;
  description?: string;
  ingredients: string[];
  instructions: string[];
  category?: string;
  prep_time?: number;
  cook_time?: number;
  servings?: number;
}

export interface RecipeUpdateRequest {
  title?: string;
  description?: string;
  ingredients?: string[];
  instructions?: string[];
  category?: string;
  prep_time?: number;
  cook_time?: number;
  servings?: number;
}

export interface RecipeListResponse {
  recipes: Recipe[];
  total: number;
  page: number;
  limit: number;
}

export interface RecipeContentResponse {
  recipe_id: string;
  title: string;
  formatted_content: string;
  word_count: number;
  character_count: number;
}

// Chat types
export interface ChatMessage {
  id: string;
  content: string;
  timestamp: Date;
  type: 'user' | 'assistant' | 'system';
  audioUrl?: string;
  isStreaming?: boolean;
}

export interface ConversationHistory {
  messages: ChatMessage[];
  sessionId: string;
  startTime: Date;
}

// WebSocket types
export interface WebSocketMessage {
  type: 'connection' | 'audio_status' | 'recipe_loaded' | 'settings_updated' | 'error' | 'audio_start' | 'audio_stop' | 'recipe_load' | 'settings_update';
  data: any;
  timestamp: number;
}

export interface AudioStatusMessage extends WebSocketMessage {
  type: 'audio_status';
  data: {
    status: string;
    message: string;
    timestamp: number;
  };
}

export interface ConnectionMessage extends WebSocketMessage {
  type: 'connection';
  data: {
    status: string;
    session_id: string;
  };
}

export interface RecipeLoadedMessage extends WebSocketMessage {
  type: 'recipe_loaded';
  data: {
    status: string;
    recipe_title: string;
  };
}

export interface ErrorMessage extends WebSocketMessage {
  type: 'error';
  data: {
    error: string;
    details: string;
  };
}

// Chef personality types
export type ChefMode = 'normal' | 'sassy' | 'gordon_ramsay';

export interface ChefPersonality {
  name: string;
  description: string;
  color: string;
  icon: string;
}

// App state types
export interface AppState {
  isConnected: boolean;
  currentRecipe: Recipe | null;
  audioState: AudioState;
  chatHistory: ChatMessage[];
  settings: AppSettings;
  chefMode: ChefMode;
}

export interface AppSettings {
  audio: AudioSettings;
  ui: {
    theme: 'light' | 'dark';
    compactMode: boolean;
    showTimestamps: boolean;
  };
  chef: {
    mode: ChefMode;
    streamingEnabled: boolean;
    contextMemory: boolean;
  };
}

// API response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
}

export interface RecipeSearchResult {
  recipes: Recipe[];
  total: number;
  page: number;
  hasMore: boolean;
}

export interface RecipeSearchResponse {
  results: Recipe[];
  total: number;
  query: string;
}

// Audio API types
export interface AudioHealthResponse {
  status: string;
  services: Record<string, string>;
  configuration: Record<string, any>;
}

export interface AudioConfigResponse {
  wake_word_sensitivity: number;
  whisper_model_size: string;
  sample_rate: number;
  max_silence_sec: number;
  speech_rate: number;
  use_external_tts: boolean;
}

export interface TTSRequest {
  text: string;
  voice?: string;
  speed?: number;
}

export interface AudioValidationResponse {
  status: string;
  message: string;
  api_keys: Record<string, string>;
}

export interface AudioModelsResponse {
  whisper_models: string[];
  current_whisper_model: string;
  tts_voices: {
    macos: string;
    openai: string;
    current: string;
  };
  llm_models: string[];
  current_llm_model: string;
  chef_modes: string[];
}

// Error types
export interface AppError {
  code: string;
  message: string;
  details?: any;
  timestamp: Date;
}

// Utility types
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: AppError | null;
}