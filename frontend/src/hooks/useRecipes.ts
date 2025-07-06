import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  Recipe, 
  AsyncState, 
  RecipeListResponse,
  RecipeSearchRequest,
  RecipeSearchResponse,
  RecipeCreateRequest,
  RecipeUpdateRequest,
  RecipeContentResponse
} from '../types';
import { apiService } from '../services/api';

export const useRecipes = () => {
  const [recipes, setRecipes] = useState<AsyncState<Recipe[]>>({
    data: null,
    loading: false,
    error: null,
  });

  const [currentRecipe, setCurrentRecipe] = useState<AsyncState<Recipe>>({
    data: null,
    loading: false,
    error: null,
  });

  const [recipeContent, setRecipeContent] = useState<AsyncState<RecipeContentResponse>>({
    data: null,
    loading: false,
    error: null,
  });

  const [categories, setCategories] = useState<AsyncState<string[]>>({
    data: null,
    loading: false,
    error: null,
  });

  const [searchQuery, setSearchQuery] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [currentCategory, setCurrentCategory] = useState<string | undefined>(undefined);
  const [totalRecipes, setTotalRecipes] = useState<number>(0);
  const [hasMore, setHasMore] = useState<boolean>(true);
  const [limit] = useState<number>(10);
  
  // Cache for preventing duplicate requests
  const loadingCache = useRef<Set<string>>(new Set());

  // Load recipes with pagination and category filtering
  const loadRecipes = useCallback(async (
    page: number = 1, 
    category?: string, 
    append: boolean = false
  ) => {
    const cacheKey = `recipes_${page}_${category || 'all'}`;
    if (loadingCache.current.has(cacheKey)) {
      return; // Prevent duplicate requests
    }

    setRecipes(prev => ({ ...prev, loading: true, error: null }));
    loadingCache.current.add(cacheKey);

    try {
      const result: RecipeListResponse = await apiService.getRecipes(page, limit, category);
      
      setRecipes(prev => ({
        data: append && prev.data ? [...prev.data, ...result.recipes] : result.recipes,
        loading: false,
        error: null,
      }));

      setTotalRecipes(result.total);
      setHasMore(result.recipes.length === limit && (page * limit) < result.total);
      setCurrentPage(page);
      setCurrentCategory(category);
    } catch (error) {
      setRecipes(prev => ({
        ...prev,
        loading: false,
        error: {
          code: 'LOAD_RECIPES_ERROR',
          message: error instanceof Error ? error.message : 'Failed to load recipes',
          timestamp: new Date(),
        },
      }));
    } finally {
      loadingCache.current.delete(cacheKey);
    }
  }, [limit]);

  // Load a specific recipe
  const loadRecipe = useCallback(async (id: string) => {
    const cacheKey = `recipe_${id}`;
    if (loadingCache.current.has(cacheKey)) {
      return;
    }

    setCurrentRecipe(prev => ({ ...prev, loading: true, error: null }));
    loadingCache.current.add(cacheKey);

    try {
      const recipe = await apiService.getRecipe(id);
      setCurrentRecipe({
        data: { ...recipe, currentStep: 0 }, // Initialize with first step
        loading: false,
        error: null,
      });
      
      // Also load recipe content for voice assistant
      await loadRecipeContent(id, false);
    } catch (error) {
      setCurrentRecipe(prev => ({
        ...prev,
        loading: false,
        error: {
          code: 'LOAD_RECIPE_ERROR',
          message: error instanceof Error ? error.message : 'Failed to load recipe',
          timestamp: new Date(),
        },
      }));
    } finally {
      loadingCache.current.delete(cacheKey);
    }
  }, []);

  // Load recipe content for voice assistant
  const loadRecipeContent = useCallback(async (id: string, setLoading: boolean = true) => {
    if (setLoading) {
      setRecipeContent(prev => ({ ...prev, loading: true, error: null }));
    }

    try {
      const content = await apiService.getRecipeContent(id);
      setRecipeContent({
        data: content,
        loading: false,
        error: null,
      });
    } catch (error) {
      setRecipeContent(prev => ({
        ...prev,
        loading: false,
        error: {
          code: 'LOAD_RECIPE_CONTENT_ERROR',
          message: error instanceof Error ? error.message : 'Failed to load recipe content',
          timestamp: new Date(),
        },
      }));
    }
  }, []);

  // Load categories
  const loadCategories = useCallback(async () => {
    setCategories(prev => ({ ...prev, loading: true, error: null }));

    try {
      const result = await apiService.getRecipeCategories();
      setCategories({
        data: result.categories,
        loading: false,
        error: null,
      });
    } catch (error) {
      setCategories(prev => ({
        ...prev,
        loading: false,
        error: {
          code: 'LOAD_CATEGORIES_ERROR',
          message: error instanceof Error ? error.message : 'Failed to load categories',
          timestamp: new Date(),
        },
      }));
    }
  }, []);

  // Search recipes using the search endpoint
  const searchRecipes = useCallback(async (query: string, category?: string, searchLimit: number = 10) => {
    setSearchQuery(query);
    setRecipes(prev => ({ ...prev, loading: true, error: null }));

    try {
      const searchRequest: RecipeSearchRequest = {
        query: query.trim(),
        limit: searchLimit,
        category,
      };
      
      const result: RecipeSearchResponse = await apiService.searchRecipes(searchRequest);
      
      setRecipes({
        data: result.results,
        loading: false,
        error: null,
      });
      
      setTotalRecipes(result.total);
      setHasMore(false); // Search results don't support pagination yet
      setCurrentPage(1);
    } catch (error) {
      setRecipes(prev => ({
        ...prev,
        loading: false,
        error: {
          code: 'SEARCH_RECIPES_ERROR',
          message: error instanceof Error ? error.message : 'Failed to search recipes',
          timestamp: new Date(),
        },
      }));
    }
  }, []);

  // Filter recipes by category
  const filterByCategory = useCallback((category?: string) => {
    setCurrentPage(1);
    loadRecipes(1, category, false);
  }, [loadRecipes]);

  // Load more recipes (pagination)
  const loadMoreRecipes = useCallback(() => {
    if (hasMore && !recipes.loading) {
      loadRecipes(currentPage + 1, currentCategory, true);
    }
  }, [hasMore, recipes.loading, currentPage, currentCategory, loadRecipes]);

  // Create a new recipe
  const createRecipe = useCallback(async (recipeData: RecipeCreateRequest) => {
    try {
      const newRecipe = await apiService.createRecipe(recipeData);
      
      // Add to the current recipes list
      setRecipes(prev => ({
        ...prev,
        data: prev.data ? [newRecipe, ...prev.data] : [newRecipe],
      }));
      
      setTotalRecipes(prev => prev + 1);

      return newRecipe;
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Failed to create recipe');
    }
  }, []);

  // Update a recipe
  const updateRecipe = useCallback(async (id: string, updates: RecipeUpdateRequest) => {
    try {
      const updatedRecipe = await apiService.updateRecipe(id, updates);
      
      // Update in recipes list
      setRecipes(prev => ({
        ...prev,
        data: prev.data?.map(recipe => 
          recipe.id === id ? updatedRecipe : recipe
        ) || null,
      }));

      // Update current recipe if it's the same one
      if (currentRecipe.data?.id === id) {
        setCurrentRecipe(prev => ({
          ...prev,
          data: { ...updatedRecipe, currentStep: prev.data?.currentStep || 0 },
        }));
        
        // Reload recipe content after update
        await loadRecipeContent(id, false);
      }

      return updatedRecipe;
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Failed to update recipe');
    }
  }, [currentRecipe.data?.id, loadRecipeContent]);

  // Delete a recipe
  const deleteRecipe = useCallback(async (id: string) => {
    try {
      await apiService.deleteRecipe(id);
      
      // Remove from recipes list
      setRecipes(prev => ({
        ...prev,
        data: prev.data?.filter(recipe => recipe.id !== id) || null,
      }));
      
      setTotalRecipes(prev => Math.max(0, prev - 1));

      // Clear current recipe if it's the deleted one
      if (currentRecipe.data?.id === id) {
        clearCurrentRecipe();
      }
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Failed to delete recipe');
    }
  }, [currentRecipe.data?.id]);

  // Set current recipe step
  const setRecipeStep = useCallback((stepNumber: number) => {
    if (currentRecipe.data) {
      const maxSteps = currentRecipe.data.instructions?.length || 0;
      const validStepNumber = Math.max(0, Math.min(stepNumber, maxSteps - 1));
      
      const updatedRecipe = {
        ...currentRecipe.data,
        currentStep: validStepNumber,
      };
      setCurrentRecipe(prev => ({
        ...prev,
        data: updatedRecipe,
      }));
    }
  }, [currentRecipe.data]);

  // Navigate to next step
  const nextStep = useCallback(() => {
    if (currentRecipe.data) {
      const currentStep = currentRecipe.data.currentStep || 0;
      const maxSteps = currentRecipe.data.instructions?.length || 0;
      if (currentStep < maxSteps - 1) {
        setRecipeStep(currentStep + 1);
      }
    }
  }, [currentRecipe.data, setRecipeStep]);

  // Navigate to previous step
  const previousStep = useCallback(() => {
    if (currentRecipe.data) {
      const currentStep = currentRecipe.data.currentStep || 0;
      if (currentStep > 0) {
        setRecipeStep(currentStep - 1);
      }
    }
  }, [currentRecipe.data, setRecipeStep]);

  // Clear current recipe
  const clearCurrentRecipe = useCallback(() => {
    setCurrentRecipe({
      data: null,
      loading: false,
      error: null,
    });
    setRecipeContent({
      data: null,
      loading: false,
      error: null,
    });
  }, []);

  // Refresh recipes (reload current view)
  const refreshRecipes = useCallback(() => {
    if (searchQuery) {
      searchRecipes(searchQuery, currentCategory);
    } else {
      loadRecipes(1, currentCategory, false);
    }
  }, [searchQuery, currentCategory, searchRecipes, loadRecipes]);

  // Check if recipe is currently loaded
  const isRecipeLoaded = useCallback((id: string) => {
    return currentRecipe.data?.id === id;
  }, [currentRecipe.data?.id]);

  // Get current instruction text
  const getCurrentInstruction = useCallback(() => {
    if (!currentRecipe.data || !currentRecipe.data.instructions) {
      return null;
    }
    const currentStep = currentRecipe.data.currentStep || 0;
    return currentRecipe.data.instructions[currentStep] || null;
  }, [currentRecipe.data]);

  // WebSocket integration for recipe loading notifications
  const handleWebSocketMessage = useCallback((message: any) => {
    if (message.type === 'recipe_loaded' && message.data?.recipe_title) {
      // Find and load the recipe with matching title
      if (recipes.data) {
        const matchingRecipe = recipes.data.find(
          recipe => recipe.title.toLowerCase() === message.data.recipe_title.toLowerCase()
        );
        if (matchingRecipe) {
          loadRecipe(matchingRecipe.id);
        }
      }
    }
  }, [recipes.data, loadRecipe]);

  // Load initial data on mount
  useEffect(() => {
    loadRecipes();
    loadCategories();
  }, [loadRecipes, loadCategories]);

  // Clear loading cache periodically
  useEffect(() => {
    const interval = setInterval(() => {
      loadingCache.current.clear();
    }, 5 * 60 * 1000); // Clear cache every 5 minutes
    
    return () => clearInterval(interval);
  }, []);

  return {
    // State
    recipes,
    currentRecipe,
    recipeContent,
    categories,
    searchQuery,
    currentPage,
    currentCategory,
    totalRecipes,
    hasMore,
    limit,
    
    // Actions
    loadRecipes,
    loadRecipe,
    loadRecipeContent,
    loadCategories,
    searchRecipes,
    filterByCategory,
    loadMoreRecipes,
    refreshRecipes,
    
    // CRUD operations
    createRecipe,
    updateRecipe,
    deleteRecipe,
    
    // Recipe navigation
    setRecipeStep,
    nextStep,
    previousStep,
    getCurrentInstruction,
    
    // Utility functions
    clearCurrentRecipe,
    isRecipeLoaded,
    handleWebSocketMessage,
  };
};

export default useRecipes;