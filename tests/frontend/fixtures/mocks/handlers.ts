/**
 * Mock API handlers for Hey Chef v2 frontend tests.
 */

import { rest } from 'msw';

const API_BASE_URL = 'http://localhost:8000';

export const handlers = [
  // Health endpoints
  rest.get(`${API_BASE_URL}/health`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        status: 'healthy',
        service: 'hey-chef-v2',
        version: '2.0.0',
        environment: 'test'
      })
    );
  }),

  rest.get(`${API_BASE_URL}/health/detailed`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        status: 'healthy',
        services: {
          audio_pipeline: 'healthy',
          wake_word: 'healthy',
          speech_to_text: 'healthy',
          text_to_speech: 'healthy',
          llm: 'healthy'
        },
        configuration: {
          environment: 'test',
          audio_enabled: true,
          llm_enabled: true
        }
      })
    );
  }),

  rest.get(`${API_BASE_URL}/`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        message: 'Hey Chef v2 API',
        version: '2.0.0',
        docs: '/docs',
        health: '/health'
      })
    );
  }),

  // Audio endpoints
  rest.get(`${API_BASE_URL}/api/audio/health`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        status: 'healthy',
        services: {
          wake_word: 'healthy',
          stt: 'healthy',
          tts: 'healthy',
          llm: 'healthy'
        },
        configuration: {
          wake_word_enabled: true,
          external_tts: false
        }
      })
    );
  }),

  rest.get(`${API_BASE_URL}/api/audio/config`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        wake_word_sensitivity: 0.7,
        whisper_model_size: 'base',
        sample_rate: 16000,
        use_external_tts: false,
        supported_languages: ['en', 'es', 'fr', 'it']
      })
    );
  }),

  rest.get(`${API_BASE_URL}/api/audio/models`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        whisper_models: ['tiny', 'base', 'small', 'medium', 'large'],
        tts_voices: ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'],
        llm_models: ['gpt-4', 'gpt-3.5-turbo']
      })
    );
  }),

  rest.post(`${API_BASE_URL}/api/audio/transcribe`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        transcription: 'How do I cook pasta?',
        confidence: 0.95,
        language: 'en',
        processing_time: 0.15
      })
    );
  }),

  rest.post(`${API_BASE_URL}/api/audio/synthesize`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.set('Content-Type', 'audio/wav'),
      ctx.body(new ArrayBuffer(1024)) // Mock audio data
    );
  }),

  rest.post(`${API_BASE_URL}/api/audio/validate-api-keys`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        status: 'valid',
        api_keys: {
          openai: 'valid',
          picovoice: 'valid'
        }
      })
    );
  }),

  // Recipe endpoints
  rest.get(`${API_BASE_URL}/api/recipes/health`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        status: 'healthy',
        notion_api: 'connected'
      })
    );
  }),

  rest.get(`${API_BASE_URL}/api/recipes/`, (req, res, ctx) => {
    const limit = req.url.searchParams.get('limit') || '10';
    
    return res(
      ctx.status(200),
      ctx.json({
        recipes: [
          {
            id: 'recipe-1',
            title: 'Classic Spaghetti Carbonara',
            description: 'A traditional Italian pasta dish',
            prep_time: 10,
            cook_time: 15,
            total_time: 25,
            servings: 4,
            difficulty: 'medium',
            category: 'pasta',
            cuisine: 'italian',
            ingredients: [
              '400g spaghetti',
              '200g pancetta',
              '4 large eggs',
              '100g Pecorino Romano cheese',
              'Black pepper',
              'Salt'
            ],
            instructions: [
              'Cook spaghetti in salted boiling water',
              'Fry pancetta until crispy',
              'Whisk eggs with cheese and pepper',
              'Combine hot pasta with pancetta',
              'Add egg mixture and toss quickly'
            ]
          },
          {
            id: 'recipe-2',
            title: 'Tomato Basil Soup',
            description: 'Comforting homemade tomato soup',
            prep_time: 15,
            cook_time: 30,
            total_time: 45,
            servings: 6,
            difficulty: 'easy',
            category: 'soup',
            cuisine: 'american',
            ingredients: [
              '2 lbs fresh tomatoes',
              '1 onion, diced',
              '4 garlic cloves',
              '2 cups vegetable broth',
              'Fresh basil leaves',
              'Heavy cream'
            ],
            instructions: [
              'Roast tomatoes in oven',
              'Sauté onion and garlic',
              'Combine with tomatoes and broth',
              'Simmer for 20 minutes',
              'Blend until smooth',
              'Stir in cream and basil'
            ]
          }
        ],
        total: 2,
        page: 1,
        limit: parseInt(limit)
      })
    );
  }),

  rest.get(`${API_BASE_URL}/api/recipes/search`, (req, res, ctx) => {
    const query = req.url.searchParams.get('q') || '';
    
    return res(
      ctx.status(200),
      ctx.json({
        recipes: [
          {
            id: 'recipe-search-1',
            title: `${query} Recipe Result`,
            description: `A delicious ${query} recipe`,
            category: 'main_course'
          }
        ],
        total: 1,
        query: query
      })
    );
  }),

  rest.get(`${API_BASE_URL}/api/recipes/:id`, (req, res, ctx) => {
    const { id } = req.params;
    
    return res(
      ctx.status(200),
      ctx.json({
        id: id,
        title: 'Recipe Details',
        description: 'Detailed recipe information',
        ingredients: ['ingredient 1', 'ingredient 2'],
        instructions: ['step 1', 'step 2'],
        prep_time: 15,
        cook_time: 30,
        servings: 4
      })
    );
  }),

  rest.get(`${API_BASE_URL}/api/recipes/categories`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        categories: [
          'appetizer',
          'main_course',
          'side_dish',
          'dessert',
          'beverage',
          'soup',
          'salad',
          'pasta',
          'pizza'
        ]
      })
    );
  }),

  // Error handlers for testing error scenarios
  rest.get(`${API_BASE_URL}/api/test/error`, (req, res, ctx) => {
    return res(
      ctx.status(500),
      ctx.json({
        detail: 'Internal server error for testing'
      })
    );
  }),

  rest.post(`${API_BASE_URL}/api/test/validation-error`, (req, res, ctx) => {
    return res(
      ctx.status(422),
      ctx.json({
        detail: [
          {
            loc: ['body', 'text'],
            msg: 'field required',
            type: 'value_error.missing'
          }
        ]
      })
    );
  }),

  // Catch-all handler for unmatched requests
  rest.all('*', (req, res, ctx) => {
    console.warn(`Unhandled ${req.method} request to ${req.url}`);
    return res(
      ctx.status(404),
      ctx.json({ detail: 'Not found' })
    );
  })
];