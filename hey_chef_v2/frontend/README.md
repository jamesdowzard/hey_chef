# Hey Chef Frontend

A modern React TypeScript frontend for the Hey Chef AI cooking assistant.

## Features

- **Voice Control**: Real-time voice interaction with wake word detection
- **Multiple Chef Personalities**: Normal, Sassy, and Gordon Ramsay modes
- **Recipe Management**: Browse, view, and follow cooking instructions step-by-step
- **Real-time Chat**: WebSocket-powered conversation with AI chef
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Dark Mode**: Toggle between light and dark themes
- **PWA Ready**: Installable as a progressive web app

## Technology Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for utility-first styling
- **WebSocket** for real-time communication
- **Lucide React** for beautiful icons
- **ESLint** for code linting

## Getting Started

### Prerequisites

- Node.js 18 or higher
- npm or yarn package manager

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
# or
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

### Backend Connection

The frontend expects the FastAPI backend to be running on `http://localhost:8000`. Make sure to start the backend server before using the frontend.

## Available Scripts

- `npm start` / `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Project Structure

```
src/
├── components/          # React components
│   ├── VoiceController.tsx    # Voice input controls
│   ├── ChatInterface.tsx      # Chat messaging interface
│   ├── RecipeViewer.tsx       # Recipe display and navigation
│   └── SettingsPanel.tsx      # Application settings
├── hooks/              # Custom React hooks
│   ├── useWebSocket.ts       # WebSocket connection management
│   ├── useAudio.ts           # Audio state management
│   └── useRecipes.ts         # Recipe data management
├── services/           # API and WebSocket services
│   ├── websocket.ts          # WebSocket service class
│   └── api.ts               # REST API service
├── types/              # TypeScript type definitions
│   └── index.ts             # All app types
├── App.tsx             # Main application component
├── main.tsx           # React entry point
└── index.css          # Global styles and Tailwind imports
```

## Components

### VoiceController
- Microphone controls and status
- Wake word detection indicator
- Volume monitoring
- Voice input start/stop buttons

### ChatInterface
- Real-time messaging with AI chef
- Message history with timestamps
- Audio playback for responses
- Chef personality indicators

### RecipeViewer
- Recipe details and ingredients
- Step-by-step cooking instructions
- Progress tracking and navigation
- Recipe metadata (time, servings, difficulty)

### SettingsPanel
- Chef personality selection
- Audio configuration
- UI theme settings
- Feature toggles

## WebSocket Integration

The frontend connects to the FastAPI backend via WebSocket for:
- Real-time voice transcription
- Streaming AI responses
- Status updates and error handling
- Audio data transmission

## Styling

The app uses Tailwind CSS with:
- Custom color palette based on cooking themes
- Responsive breakpoints for all screen sizes
- Dark mode support
- Smooth animations and transitions
- Accessibility-friendly focus states

## Browser Support

- Chrome/Edge 88+
- Firefox 85+
- Safari 14+
- Mobile browsers with WebSocket support

## Environment Variables

No environment variables are required for the frontend. Configuration is handled through the settings panel and connects to the backend via proxy.

## Development

### Code Style
- TypeScript with strict mode enabled
- ESLint for code quality
- Prettier formatting (recommended)
- Component-first architecture

### Adding New Features
1. Create components in `src/components/`
2. Add types to `src/types/index.ts`
3. Use custom hooks for stateful logic
4. Follow existing patterns for WebSocket integration

### Testing
While not yet implemented, the structure supports:
- Unit tests with Jest/Vitest
- Component tests with React Testing Library
- E2E tests with Playwright

## Deployment

### Production Build
```bash
npm run build
```

### Deployment Options
- Static hosting (Vercel, Netlify, GitHub Pages)
- CDN deployment
- Docker containerization
- Server-side rendering with Next.js (future enhancement)

## Troubleshooting

### Common Issues

1. **WebSocket connection fails**
   - Ensure backend is running on port 8000
   - Check browser console for connection errors
   - Verify proxy configuration in vite.config.ts

2. **Audio not working**
   - Check browser microphone permissions
   - Ensure HTTPS in production (required for audio APIs)
   - Verify audio settings in the settings panel

3. **Build errors**
   - Clear node_modules and reinstall dependencies
   - Check TypeScript errors with `npm run lint`
   - Ensure all required environment variables are set

### Performance Tips
- Use browser dev tools to monitor WebSocket messages
- Check Network tab for API call performance
- Monitor memory usage during long conversations
- Use React DevTools Profiler for component performance

## Contributing

1. Follow the existing code style and patterns
2. Add TypeScript types for new features
3. Test on multiple browsers and screen sizes
4. Ensure accessibility best practices
5. Update documentation for new components or features

## License

This project is part of the Hey Chef application suite.