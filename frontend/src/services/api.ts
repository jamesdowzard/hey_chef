import { 
  Recipe, 
  RecipeListResponse,
  RecipeSearchRequest,
  RecipeSearchResponse,
  RecipeCreateRequest,
  RecipeUpdateRequest,
  RecipeContentResponse,
  AudioHealthResponse,
  AudioConfigResponse,
  TTSRequest,
  AudioValidationResponse,
  AudioModelsResponse
} from '../types';

const API_BASE_URL = '/api';

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    returnRawResponse = false
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.error || errorMessage;
        } catch {
          // If we can't parse error response, use status text
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
      }
      
      const data = await response.json();
      return returnRawResponse ? data : data;
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Recipe endpoints
  async getRecipes(
    page: number = 1, 
    limit: number = 10, 
    category?: string
  ): Promise<RecipeListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    if (category) {
      params.append('category', category);
    }
    
    return this.request<RecipeListResponse>(`/recipes?${params}`);
  }

  async getRecipe(id: string): Promise<Recipe> {
    return this.request<Recipe>(`/recipes/${id}`);
  }

  async searchRecipes(searchRequest: RecipeSearchRequest): Promise<RecipeSearchResponse> {
    return this.request<RecipeSearchResponse>('/recipes/search', {
      method: 'POST',
      body: JSON.stringify(searchRequest),
    });
  }

  async getRecipeCategories(): Promise<{ categories: string[] }> {
    return this.request<{ categories: string[] }>('/recipes/categories/list');
  }

  async getRecipeContent(id: string): Promise<RecipeContentResponse> {
    return this.request<RecipeContentResponse>(`/recipes/${id}/content`);
  }

  async createRecipe(recipe: RecipeCreateRequest): Promise<Recipe> {
    return this.request<Recipe>('/recipes', {
      method: 'POST',
      body: JSON.stringify(recipe),
    });
  }

  async updateRecipe(id: string, recipe: RecipeUpdateRequest): Promise<Recipe> {
    return this.request<Recipe>(`/recipes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(recipe),
    });
  }

  async deleteRecipe(id: string): Promise<{ status: string; message: string }> {
    return this.request<{ status: string; message: string }>(`/recipes/${id}`, {
      method: 'DELETE',
    });
  }

  // Audio endpoints
  async getAudioHealth(): Promise<AudioHealthResponse> {
    return this.request<AudioHealthResponse>('/audio/health');
  }

  async getAudioConfig(): Promise<AudioConfigResponse> {
    return this.request<AudioConfigResponse>('/audio/config');
  }

  async validateApiKeys(): Promise<AudioValidationResponse> {
    return this.request<AudioValidationResponse>('/audio/validate-api-keys', {
      method: 'POST',
    });
  }

  async transcribeAudio(audioFile: File): Promise<{ status: string; text: string; filename: string; size: number }> {
    const formData = new FormData();
    formData.append('audio_file', audioFile);
    
    return this.request<{ status: string; text: string; filename: string; size: number }>('/audio/transcribe', {
      method: 'POST',
      body: formData,
      headers: {}, // Remove Content-Type to let browser set it for FormData
    });
  }

  async synthesizeSpeech(request: TTSRequest): Promise<{ status: string; message: string; audio_file: string; text: string; voice: string }> {
    return this.request<{ status: string; message: string; audio_file: string; text: string; voice: string }>('/audio/synthesize', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async testWakeWord(): Promise<{ status: string; message: string; duration_seconds: number; detections: any[]; total_detections: number }> {
    return this.request<{ status: string; message: string; duration_seconds: number; detections: any[]; total_detections: number }>('/audio/test-wake-word', {
      method: 'POST',
    });
  }

  async getAudioModels(): Promise<AudioModelsResponse> {
    return this.request<AudioModelsResponse>('/audio/models');
  }

  async getAudioStats(): Promise<{ status: string; stats: Record<string, any>; message: string }> {
    return this.request<{ status: string; stats: Record<string, any>; message: string }>('/audio/stats');
  }

  // Recipe health check
  async getRecipesHealth(): Promise<{ status: string; notion_api: string; notion_url?: string }> {
    return this.request<{ status: string; notion_api: string; notion_url?: string }>('/recipes/health');
  }

  // General health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request<{ status: string; timestamp: string }>('/health');
  }
}

export const apiService = new ApiService();
export default apiService;