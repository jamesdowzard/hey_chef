import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Volume2, 
  User, 
  Zap, 
  Moon, 
  Sun, 
  Save, 
  Info,
  CheckCircle,
  XCircle,
  AlertCircle,
  Wifi,
  Key,
  Activity,
  HelpCircle
} from 'lucide-react';
import { AppSettings, ChefMode } from '../types';

interface SettingsPanelProps {
  settings: AppSettings;
  onSettingsChange: (settings: AppSettings) => void;
  className?: string;
  connectionStatus?: 'connected' | 'disconnected' | 'connecting';
  apiKeyValid?: boolean;
  audioServiceHealthy?: boolean;
}

interface SystemStatus {
  connection: 'connected' | 'disconnected' | 'connecting';
  apiKey: boolean | null;
  audioService: boolean | null;
}

interface TooltipProps {
  content: string;
  children: React.ReactNode;
}

const Tooltip: React.FC<TooltipProps> = ({ content, children }) => {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div 
      className="relative inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div className="absolute z-10 px-3 py-2 text-sm text-white bg-gray-900 rounded-lg shadow-lg -top-12 left-1/2 transform -translate-x-1/2 whitespace-nowrap">
          {content}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
        </div>
      )}
    </div>
  );
};

const chefModes: { mode: ChefMode; name: string; description: string; color: string; preview: string }[] = [
  {
    mode: 'normal',
    name: 'Normal Chef',
    description: 'Friendly and helpful cooking assistant',
    color: 'bg-blue-100 text-blue-800 border-blue-200',
    preview: 'Let me help you create something delicious! What are we cooking today?'
  },
  {
    mode: 'sassy',
    name: 'Sassy Chef',
    description: 'Witty and entertaining with cooking advice',
    color: 'bg-purple-100 text-purple-800 border-purple-200',
    preview: 'Oh honey, you want to cook? Well, buckle up because we\'re about to make magic happen!'
  },
  {
    mode: 'gordon_ramsay',
    name: 'Gordon Ramsay',
    description: 'Passionate and direct culinary guidance',
    color: 'bg-red-100 text-red-800 border-red-200',
    preview: 'Right! Let\'s get this kitchen moving! No messing about - we\'re cooking perfection!'
  }
];

export const SettingsPanel: React.FC<SettingsPanelProps> = ({
  settings,
  onSettingsChange,
  className = '',
  connectionStatus = 'disconnected',
  apiKeyValid = null,
  audioServiceHealthy = null
}) => {
  const [localSettings, setLocalSettings] = useState<AppSettings>(settings);
  const [hasChanges, setHasChanges] = useState(false);
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    connection: connectionStatus,
    apiKey: apiKeyValid,
    audioService: audioServiceHealthy
  });
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [showPreview, setShowPreview] = useState<ChefMode | null>(null);

  // Update system status when props change
  useEffect(() => {
    setSystemStatus({
      connection: connectionStatus,
      apiKey: apiKeyValid,
      audioService: audioServiceHealthy
    });
  }, [connectionStatus, apiKeyValid, audioServiceHealthy]);

  // Update local settings when external settings change
  useEffect(() => {
    setLocalSettings(settings);
    setHasChanges(false);
  }, [settings]);

  const validateSettings = (settings: AppSettings): Record<string, string> => {
    const errors: Record<string, string> = {};
    
    if (settings.audio.volume < 0 || settings.audio.volume > 100) {
      errors.volume = 'Volume must be between 0 and 100';
    }
    
    if (settings.audio.speechRate < 0.5 || settings.audio.speechRate > 2) {
      errors.speechRate = 'Speech rate must be between 0.5x and 2x';
    }
    
    return errors;
  };

  const updateSettings = (newSettings: AppSettings) => {
    const errors = validateSettings(newSettings);
    setValidationErrors(errors);
    setLocalSettings(newSettings);
    
    if (Object.keys(errors).length === 0) {
      setHasChanges(true);
    }
  };

  const handleSave = () => {
    const errors = validateSettings(localSettings);
    if (Object.keys(errors).length === 0) {
      onSettingsChange(localSettings);
      setHasChanges(false);
    }
  };

  const handleReset = () => {
    setLocalSettings(settings);
    setHasChanges(false);
    setValidationErrors({});
  };

  const getStatusIcon = (status: boolean | null) => {
    if (status === null) return <AlertCircle className="w-4 h-4 text-yellow-500" />;
    return status ? <CheckCircle className="w-4 h-4 text-green-500" /> : <XCircle className="w-4 h-4 text-red-500" />;
  };

  const getConnectionIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'connecting':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      default:
        return <XCircle className="w-4 h-4 text-red-500" />;
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-lg p-4 md:p-6 ${className}`} role="region" aria-label="Settings Panel">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Settings className="w-6 h-6 text-gray-600" />
          <h2 className="text-xl font-semibold text-gray-800">Settings</h2>
        </div>
        {hasChanges && (
          <div className="flex space-x-2">
            <button
              onClick={handleReset}
              className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 transition-colors"
            >
              Reset
            </button>
            <button
              onClick={handleSave}
              disabled={Object.keys(validationErrors).length > 0}
              className={`flex items-center space-x-2 px-4 py-2 text-white text-sm rounded-lg transition-colors ${
                Object.keys(validationErrors).length > 0
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-primary-500 hover:bg-primary-600'
              }`}
            >
              <Save className="w-4 h-4" />
              <span>Save</span>
            </button>
          </div>
        )}
      </div>

      <div className="space-y-6 md:space-y-8">
        {/* Chef Personality */}
        <section>
          <h3 className="text-lg font-medium text-gray-800 mb-4 flex items-center space-x-2">
            <User className="w-5 h-5" />
            <span>Chef Personality</span>
            <Tooltip content="Choose your preferred chef's personality and communication style">
              <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
            </Tooltip>
          </h3>
          <div className="space-y-3">
            {chefModes.map((chef) => (
              <div key={chef.mode}>
                <label
                  className={`
                    block p-4 border-2 rounded-lg cursor-pointer transition-all
                    ${localSettings.chef.mode === chef.mode
                      ? chef.color
                      : 'border-gray-200 hover:border-gray-300'
                    }
                  `}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <input
                        type="radio"
                        name="chefMode"
                        value={chef.mode}
                        checked={localSettings.chef.mode === chef.mode}
                        onChange={(e) => updateSettings({
                          ...localSettings,
                          chef: { ...localSettings.chef, mode: e.target.value as ChefMode }
                        })}
                        className="w-4 h-4 text-primary-600"
                      />
                      <div>
                        <div className="font-medium text-gray-800">{chef.name}</div>
                        <div className="text-sm text-gray-600">{chef.description}</div>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        setShowPreview(showPreview === chef.mode ? null : chef.mode);
                      }}
                      className="px-3 py-1 text-xs text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-colors"
                    >
                      {showPreview === chef.mode ? 'Hide' : 'Preview'}
                    </button>
                  </div>
                </label>
                {showPreview === chef.mode && (
                  <div className="mt-2 p-3 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="text-xs text-gray-500 mb-1">Preview:</div>
                    <div className="text-sm text-gray-700 italic">"{chef.preview}"</div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Audio Settings */}
        <section>
          <h3 className="text-lg font-medium text-gray-800 mb-4 flex items-center space-x-2">
            <Volume2 className="w-5 h-5" />
            <span>Audio Settings</span>
            <Tooltip content="Configure audio input, output, and voice preferences">
              <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
            </Tooltip>
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700">Wake Word Detection</label>
                <Tooltip content="Enable 'Hey Chef' wake word detection to start conversations hands-free">
                  <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                </Tooltip>
              </div>
              <button
                onClick={() => updateSettings({
                  ...localSettings,
                  audio: { ...localSettings.audio, wakeWordEnabled: !localSettings.audio.wakeWordEnabled }
                })}
                className={`
                  relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                  ${localSettings.audio.wakeWordEnabled ? 'bg-primary-500' : 'bg-gray-300'}
                `}
                role="switch"
                aria-checked={localSettings.audio.wakeWordEnabled}
                aria-label="Toggle wake word detection"
              >
                <span
                  className={`
                    inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                    ${localSettings.audio.wakeWordEnabled ? 'translate-x-6' : 'translate-x-1'}
                  `}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700">Microphone</label>
                <Tooltip content="Enable microphone access for voice input">
                  <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                </Tooltip>
              </div>
              <button
                onClick={() => updateSettings({
                  ...localSettings,
                  audio: { ...localSettings.audio, microphoneEnabled: !localSettings.audio.microphoneEnabled }
                })}
                className={`
                  relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                  ${localSettings.audio.microphoneEnabled ? 'bg-primary-500' : 'bg-gray-300'}
                `}
              >
                <span
                  className={`
                    inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                    ${localSettings.audio.microphoneEnabled ? 'translate-x-6' : 'translate-x-1'}
                  `}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700">Speaker Output</label>
                <Tooltip content="Enable audio output for chef responses">
                  <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                </Tooltip>
              </div>
              <button
                onClick={() => updateSettings({
                  ...localSettings,
                  audio: { ...localSettings.audio, speakerEnabled: !localSettings.audio.speakerEnabled }
                })}
                className={`
                  relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                  ${localSettings.audio.speakerEnabled ? 'bg-primary-500' : 'bg-gray-300'}
                `}
              >
                <span
                  className={`
                    inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                    ${localSettings.audio.speakerEnabled ? 'translate-x-6' : 'translate-x-1'}
                  `}
                />
              </button>
            </div>

            <div>
              <div className="flex items-center space-x-2 mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Volume: {localSettings.audio.volume}%
                </label>
                <Tooltip content="Adjust the output volume for chef responses (0-100%)">
                  <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                </Tooltip>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={localSettings.audio.volume}
                onChange={(e) => updateSettings({
                  ...localSettings,
                  audio: { ...localSettings.audio, volume: parseInt(e.target.value) }
                })}
                className={`w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider ${
                  validationErrors.volume ? 'border-red-500' : ''
                }`}
              />
              {validationErrors.volume && (
                <p className="text-red-500 text-xs mt-1">{validationErrors.volume}</p>
              )}
            </div>

            <div>
              <div className="flex items-center space-x-2 mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Speech Rate: {localSettings.audio.speechRate}x
                </label>
                <Tooltip content="Adjust how fast the chef speaks (0.5x - 2x speed)">
                  <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                </Tooltip>
              </div>
              <input
                type="range"
                min="0.5"
                max="2"
                step="0.1"
                value={localSettings.audio.speechRate}
                onChange={(e) => updateSettings({
                  ...localSettings,
                  audio: { ...localSettings.audio, speechRate: parseFloat(e.target.value) }
                })}
                className={`w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider ${
                  validationErrors.speechRate ? 'border-red-500' : ''
                }`}
              />
              {validationErrors.speechRate && (
                <p className="text-red-500 text-xs mt-1">{validationErrors.speechRate}</p>
              )}
            </div>

            <div>
              <div className="flex items-center space-x-2 mb-2">
                <label className="block text-sm font-medium text-gray-700">Voice Type</label>
                <Tooltip content="Choose between your system's built-in voice or OpenAI's neural voices">
                  <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                </Tooltip>
              </div>
              <select
                value={localSettings.audio.voiceType}
                onChange={(e) => updateSettings({
                  ...localSettings,
                  audio: { ...localSettings.audio, voiceType: e.target.value as 'system' | 'openai' }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="system">System Voice (Built-in)</option>
                <option value="openai">OpenAI Voice (Neural)</option>
              </select>
            </div>
          </div>
        </section>

        {/* AI Features */}
        <section>
          <h3 className="text-lg font-medium text-gray-800 mb-4 flex items-center space-x-2">
            <Zap className="w-5 h-5" />
            <span>AI Features</span>
            <Tooltip content="Configure AI behavior and response preferences">
              <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
            </Tooltip>
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700">Streaming Responses</label>
                <p className="text-xs text-gray-500">Get responses as they're generated</p>
              </div>
              <button
                onClick={() => updateSettings({
                  ...localSettings,
                  chef: { ...localSettings.chef, streamingEnabled: !localSettings.chef.streamingEnabled }
                })}
                className={`
                  relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                  ${localSettings.chef.streamingEnabled ? 'bg-primary-500' : 'bg-gray-300'}
                `}
              >
                <span
                  className={`
                    inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                    ${localSettings.chef.streamingEnabled ? 'translate-x-6' : 'translate-x-1'}
                  `}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700">Context Memory</label>
                <p className="text-xs text-gray-500">Remember conversation history</p>
              </div>
              <button
                onClick={() => updateSettings({
                  ...localSettings,
                  chef: { ...localSettings.chef, contextMemory: !localSettings.chef.contextMemory }
                })}
                className={`
                  relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                  ${localSettings.chef.contextMemory ? 'bg-primary-500' : 'bg-gray-300'}
                `}
              >
                <span
                  className={`
                    inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                    ${localSettings.chef.contextMemory ? 'translate-x-6' : 'translate-x-1'}
                  `}
                />
              </button>
            </div>
          </div>
        </section>

        {/* UI Settings */}
        <section>
          <h3 className="text-lg font-medium text-gray-800 mb-4 flex items-center space-x-2">
            {localSettings.ui.theme === 'dark' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
            <span>Interface</span>
            <Tooltip content="Customize the appearance and behavior of the user interface">
              <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
            </Tooltip>
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">Dark Mode</label>
              <button
                onClick={() => updateSettings({
                  ...localSettings,
                  ui: { ...localSettings.ui, theme: localSettings.ui.theme === 'dark' ? 'light' : 'dark' }
                })}
                className={`
                  relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                  ${localSettings.ui.theme === 'dark' ? 'bg-primary-500' : 'bg-gray-300'}
                `}
              >
                <span
                  className={`
                    inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                    ${localSettings.ui.theme === 'dark' ? 'translate-x-6' : 'translate-x-1'}
                  `}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">Compact Mode</label>
              <button
                onClick={() => updateSettings({
                  ...localSettings,
                  ui: { ...localSettings.ui, compactMode: !localSettings.ui.compactMode }
                })}
                className={`
                  relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                  ${localSettings.ui.compactMode ? 'bg-primary-500' : 'bg-gray-300'}
                `}
              >
                <span
                  className={`
                    inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                    ${localSettings.ui.compactMode ? 'translate-x-6' : 'translate-x-1'}
                  `}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">Show Timestamps</label>
              <button
                onClick={() => updateSettings({
                  ...localSettings,
                  ui: { ...localSettings.ui, showTimestamps: !localSettings.ui.showTimestamps }
                })}
                className={`
                  relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                  ${localSettings.ui.showTimestamps ? 'bg-primary-500' : 'bg-gray-300'}
                `}
              >
                <span
                  className={`
                    inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                    ${localSettings.ui.showTimestamps ? 'translate-x-6' : 'translate-x-1'}
                  `}
                />
              </button>
            </div>
          </div>
        </section>

        {/* System Information */}
        <section>
          <h3 className="text-lg font-medium text-gray-800 mb-4 flex items-center space-x-2">
            <Info className="w-5 h-5" />
            <span>System Information</span>
            <Tooltip content="View current system status and health information">
              <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
            </Tooltip>
          </h3>
          <div className="space-y-4">
            {/* Connection Status */}
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <Wifi className="w-5 h-5 text-gray-600" />
                <div>
                  <div className="text-sm font-medium text-gray-700">Connection Status</div>
                  <div className="text-xs text-gray-500">WebSocket connection to backend</div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {getConnectionIcon(systemStatus.connection)}
                <span className={`text-sm font-medium capitalize ${
                  systemStatus.connection === 'connected' ? 'text-green-700' :
                  systemStatus.connection === 'connecting' ? 'text-yellow-700' :
                  'text-red-700'
                }`}>
                  {systemStatus.connection}
                </span>
              </div>
            </div>

            {/* API Key Validation */}
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <Key className="w-5 h-5 text-gray-600" />
                <div>
                  <div className="text-sm font-medium text-gray-700">OpenAI API Key</div>
                  <div className="text-xs text-gray-500">Validates access to AI services</div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {getStatusIcon(systemStatus.apiKey)}
                <span className={`text-sm font-medium ${
                  systemStatus.apiKey === true ? 'text-green-700' :
                  systemStatus.apiKey === false ? 'text-red-700' :
                  'text-yellow-700'
                }`}>
                  {systemStatus.apiKey === true ? 'Valid' :
                   systemStatus.apiKey === false ? 'Invalid' :
                   'Checking...'}
                </span>
              </div>
            </div>

            {/* Audio Service Health */}
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <Activity className="w-5 h-5 text-gray-600" />
                <div>
                  <div className="text-sm font-medium text-gray-700">Audio Services</div>
                  <div className="text-xs text-gray-500">Microphone and speaker functionality</div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {getStatusIcon(systemStatus.audioService)}
                <span className={`text-sm font-medium ${
                  systemStatus.audioService === true ? 'text-green-700' :
                  systemStatus.audioService === false ? 'text-red-700' :
                  'text-yellow-700'
                }`}>
                  {systemStatus.audioService === true ? 'Healthy' :
                   systemStatus.audioService === false ? 'Issues' :
                   'Checking...'}
                </span>
              </div>
            </div>

            {/* Version Information */}
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3 mb-2">
                <Settings className="w-5 h-5 text-gray-600" />
                <div className="text-sm font-medium text-gray-700">Version Information</div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-gray-600">
                <div>
                  <div className="font-medium">Frontend</div>
                  <div>v2.0.0</div>
                </div>
                <div>
                  <div className="font-medium">Backend</div>
                  <div>v2.0.0</div>
                </div>
                <div>
                  <div className="font-medium">Node.js</div>
                  <div>{typeof window !== 'undefined' && window.navigator ? window.navigator.platform : 'Unknown'}</div>
                </div>
                <div>
                  <div className="font-medium">Build</div>
                  <div>{process.env.NODE_ENV || 'development'}</div>
                </div>
              </div>
            </div>

            {/* Settings Summary */}
            <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center space-x-2 mb-2">
                <Info className="w-4 h-4 text-blue-600" />
                <div className="text-sm font-medium text-blue-800">Current Configuration</div>
              </div>
              <div className="text-xs text-blue-700 space-y-1">
                <div>Chef Mode: <span className="font-medium capitalize">{localSettings.chef.mode.replace('_', ' ')}</span></div>
                <div>Voice: <span className="font-medium">{localSettings.audio.voiceType === 'system' ? 'System' : 'OpenAI'}</span></div>
                <div>Theme: <span className="font-medium capitalize">{localSettings.ui.theme}</span></div>
                <div>Wake Word: <span className="font-medium">{localSettings.audio.wakeWordEnabled ? 'Enabled' : 'Disabled'}</span></div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};