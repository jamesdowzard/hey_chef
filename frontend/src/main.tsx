import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import './index.css';

// Error Boundary Component
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Hey Chef Error:', error, errorInfo);
    
    // In development, you might want to send errors to a logging service
    if (import.meta.env.DEV) {
      console.group('Error Boundary Caught Error');
      console.error('Error:', error);
      console.error('Error Info:', errorInfo);
      console.groupEnd();
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
            <div className="text-6xl mb-4">👨‍🍳</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              Oops! Something went wrong in the kitchen
            </h1>
            <p className="text-gray-600 mb-6">
              Hey Chef encountered an unexpected error. Don't worry, even the best chefs make mistakes!
            </p>
            <div className="space-y-3">
              <button
                onClick={() => window.location.reload()}
                className="w-full btn-chef-primary"
              >
                Start Fresh
              </button>
              {import.meta.env.DEV && (
                <details className="text-left">
                  <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
                    Show Error Details (Dev Mode)
                  </summary>
                  <pre className="mt-2 p-3 bg-gray-100 rounded text-xs overflow-auto max-h-32">
                    {this.state.error?.toString()}
                  </pre>
                </details>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Development mode enhancements
if (import.meta.env.DEV) {
  // Enable React DevTools
  if (typeof window !== 'undefined') {
    (window as any).__REACT_DEVTOOLS_GLOBAL_HOOK__ = (window as any).__REACT_DEVTOOLS_GLOBAL_HOOK__ || {};
  }
  
  // Log application startup
  console.log('🍳 Hey Chef v2 Frontend Starting...');
  console.log('Environment:', import.meta.env.MODE);
  console.log('Build Date:', new Date().toISOString());
}

// Performance monitoring in development
if (import.meta.env.DEV && 'performance' in window) {
  window.addEventListener('load', () => {
    setTimeout(() => {
      const perfData = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      console.log('🍳 Hey Chef Performance Metrics:');
      console.log(`DOM Content Loaded: ${perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart}ms`);
      console.log(`Full Load Time: ${perfData.loadEventEnd - perfData.loadEventStart}ms`);
    }, 0);
  });
}

const root = ReactDOM.createRoot(document.getElementById('root')!);

root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);