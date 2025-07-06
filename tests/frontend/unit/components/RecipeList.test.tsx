/**
 * Unit tests for RecipeList component.
 */

import React from 'react';
import { render, screen, waitFor } from '../../fixtures/test-utils';
import userEvent from '@testing-library/user-event';
import { RecipeList } from '../../../../frontend/src/components/RecipeList';
import { createMockRecipe } from '../../fixtures/test-utils';

// Mock the API service
jest.mock('../../../../frontend/src/services/api', () => ({
  recipeAPI: {
    getRecipes: jest.fn(),
    searchRecipes: jest.fn(),
    getCategories: jest.fn(),
  },
}));

describe('RecipeList Component', () => {
  const mockRecipes = [
    createMockRecipe({
      id: 'recipe-1',
      title: 'Spaghetti Carbonara',
      category: 'pasta',
      difficulty: 'medium',
      total_time: 25
    }),
    createMockRecipe({
      id: 'recipe-2',
      title: 'Tomato Soup',
      category: 'soup',
      difficulty: 'easy',
      total_time: 45
    }),
    createMockRecipe({
      id: 'recipe-3',
      title: 'Caesar Salad',
      category: 'salad',
      difficulty: 'easy',
      total_time: 15
    })
  ];

  const defaultProps = {
    onRecipeSelect: jest.fn(),
    searchTerm: '',
    category: 'all',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock API responses
    const { recipeAPI } = require('../../../../frontend/src/services/api');
    recipeAPI.getRecipes.mockResolvedValue({
      recipes: mockRecipes,
      total: mockRecipes.length
    });
    recipeAPI.searchRecipes.mockResolvedValue({
      recipes: mockRecipes,
      total: mockRecipes.length
    });
    recipeAPI.getCategories.mockResolvedValue({
      categories: ['pasta', 'soup', 'salad', 'dessert']
    });
  });

  it('renders recipe list correctly', async () => {
    render(<RecipeList {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('Spaghetti Carbonara')).toBeInTheDocument();
      expect(screen.getByText('Tomato Soup')).toBeInTheDocument();
      expect(screen.getByText('Caesar Salad')).toBeInTheDocument();
    });
  });

  it('displays loading state while fetching recipes', () => {
    render(<RecipeList {...defaultProps} />);

    expect(screen.getByText(/loading recipes/i)).toBeInTheDocument();
  });

  it('handles empty recipe list', async () => {
    const { recipeAPI } = require('../../../../frontend/src/services/api');
    recipeAPI.getRecipes.mockResolvedValue({
      recipes: [],
      total: 0
    });

    render(<RecipeList {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(/no recipes found/i)).toBeInTheDocument();
    });
  });

  it('calls onRecipeSelect when recipe is clicked', async () => {
    const user = userEvent.setup();
    const onRecipeSelectMock = jest.fn();

    render(<RecipeList {...defaultProps} onRecipeSelect={onRecipeSelectMock} />);

    await waitFor(() => {
      expect(screen.getByText('Spaghetti Carbonara')).toBeInTheDocument();
    });

    const recipeCard = screen.getByText('Spaghetti Carbonara').closest('[data-testid="recipe-card"]');
    await user.click(recipeCard!);

    expect(onRecipeSelectMock).toHaveBeenCalledWith(mockRecipes[0]);
  });

  it('filters recipes by search term', async () => {
    const { recipeAPI } = require('../../../../frontend/src/services/api');
    const filteredRecipes = [mockRecipes[0]]; // Only Carbonara
    recipeAPI.searchRecipes.mockResolvedValue({
      recipes: filteredRecipes,
      total: 1
    });

    render(<RecipeList {...defaultProps} searchTerm="carbonara" />);

    await waitFor(() => {
      expect(screen.getByText('Spaghetti Carbonara')).toBeInTheDocument();
      expect(screen.queryByText('Tomato Soup')).not.toBeInTheDocument();
    });

    expect(recipeAPI.searchRecipes).toHaveBeenCalledWith('carbonara');
  });

  it('filters recipes by category', async () => {
    const { recipeAPI } = require('../../../../frontend/src/services/api');
    const pastaRecipes = [mockRecipes[0]]; // Only Carbonara
    recipeAPI.getRecipes.mockResolvedValue({
      recipes: pastaRecipes,
      total: 1
    });

    render(<RecipeList {...defaultProps} category="pasta" />);

    await waitFor(() => {
      expect(screen.getByText('Spaghetti Carbonara')).toBeInTheDocument();
      expect(screen.queryByText('Tomato Soup')).not.toBeInTheDocument();
    });

    expect(recipeAPI.getRecipes).toHaveBeenCalledWith({ category: 'pasta' });
  });

  it('displays recipe metadata correctly', async () => {
    render(<RecipeList {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('25 min')).toBeInTheDocument(); // Carbonara time
      expect(screen.getByText('45 min')).toBeInTheDocument(); // Soup time
      expect(screen.getByText('15 min')).toBeInTheDocument(); // Salad time
      
      expect(screen.getByText('medium')).toBeInTheDocument(); // Carbonara difficulty
      expect(screen.getAllByText('easy')).toHaveLength(2); // Soup and Salad difficulty
    });
  });

  it('supports pagination', async () => {
    const user = userEvent.setup();
    
    // Mock paginated response
    const { recipeAPI } = require('../../../../frontend/src/services/api');
    recipeAPI.getRecipes.mockResolvedValue({
      recipes: mockRecipes.slice(0, 2),
      total: 10,
      page: 1,
      limit: 2
    });

    render(<RecipeList {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 5')).toBeInTheDocument();
    });

    const nextButton = screen.getByLabelText(/next page/i);
    await user.click(nextButton);

    expect(recipeAPI.getRecipes).toHaveBeenCalledWith({ page: 2, limit: 2 });
  });

  it('supports sorting options', async () => {
    const user = userEvent.setup();

    render(<RecipeList {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('Spaghetti Carbonara')).toBeInTheDocument();
    });

    const sortSelect = screen.getByLabelText(/sort by/i);
    await user.selectOptions(sortSelect, 'time_asc');

    expect(recipeAPI.getRecipes).toHaveBeenCalledWith({ sort: 'time_asc' });
  });

  it('displays recipe images when available', async () => {
    const recipesWithImages = mockRecipes.map(recipe => ({
      ...recipe,
      image_url: `https://example.com/${recipe.id}.jpg`
    }));

    const { recipeAPI } = require('../../../../frontend/src/services/api');
    recipeAPI.getRecipes.mockResolvedValue({
      recipes: recipesWithImages,
      total: recipesWithImages.length
    });

    render(<RecipeList {...defaultProps} />);

    await waitFor(() => {
      const images = screen.getAllByRole('img');
      expect(images).toHaveLength(3);
      expect(images[0]).toHaveAttribute('src', 'https://example.com/recipe-1.jpg');
    });
  });

  it('handles image loading errors gracefully', async () => {
    const recipesWithImages = mockRecipes.map(recipe => ({
      ...recipe,
      image_url: 'https://broken-url.com/image.jpg'
    }));

    const { recipeAPI } = require('../../../../frontend/src/services/api');
    recipeAPI.getRecipes.mockResolvedValue({
      recipes: recipesWithImages,
      total: recipesWithImages.length
    });

    render(<RecipeList {...defaultProps} />);

    await waitFor(() => {
      const images = screen.getAllByRole('img');
      images.forEach(img => {
        // Simulate image error
        img.onerror?.(new Event('error'));
      });
    });

    // Should show placeholder images
    const placeholders = screen.getAllByTestId('recipe-placeholder');
    expect(placeholders).toHaveLength(3);
  });

  it('supports grid and list view modes', async () => {
    const user = userEvent.setup();

    render(<RecipeList {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('Spaghetti Carbonara')).toBeInTheDocument();
    });

    // Default should be grid view
    const container = screen.getByTestId('recipe-list-container');
    expect(container).toHaveClass('grid-view');

    // Switch to list view
    const listViewButton = screen.getByLabelText(/list view/i);
    await user.click(listViewButton);

    expect(container).toHaveClass('list-view');
  });

  it('handles API errors gracefully', async () => {
    const { recipeAPI } = require('../../../../frontend/src/services/api');
    recipeAPI.getRecipes.mockRejectedValue(new Error('API Error'));

    render(<RecipeList {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(/error loading recipes/i)).toBeInTheDocument();
    });

    // Should show retry button
    const retryButton = screen.getByText(/retry/i);
    expect(retryButton).toBeInTheDocument();
  });

  it('allows retrying after error', async () => {
    const user = userEvent.setup();
    const { recipeAPI } = require('../../../../frontend/src/services/api');
    
    // First call fails
    recipeAPI.getRecipes.mockRejectedValueOnce(new Error('API Error'));
    // Second call succeeds
    recipeAPI.getRecipes.mockResolvedValue({
      recipes: mockRecipes,
      total: mockRecipes.length
    });

    render(<RecipeList {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(/error loading recipes/i)).toBeInTheDocument();
    });

    const retryButton = screen.getByText(/retry/i);
    await user.click(retryButton);

    await waitFor(() => {
      expect(screen.getByText('Spaghetti Carbonara')).toBeInTheDocument();
    });
  });

  it('shows favorites indicator for liked recipes', async () => {
    const recipesWithFavorites = mockRecipes.map((recipe, index) => ({
      ...recipe,
      is_favorite: index === 0 // Only first recipe is favorite
    }));

    const { recipeAPI } = require('../../../../frontend/src/services/api');
    recipeAPI.getRecipes.mockResolvedValue({
      recipes: recipesWithFavorites,
      total: recipesWithFavorites.length
    });

    render(<RecipeList {...defaultProps} />);

    await waitFor(() => {
      const favoriteIcons = screen.getAllByTestId('favorite-icon');
      expect(favoriteIcons).toHaveLength(1); // Only one favorite
    });
  });

  it('supports infinite scroll loading', async () => {
    const { recipeAPI } = require('../../../../frontend/src/services/api');
    
    // First load
    recipeAPI.getRecipes.mockResolvedValueOnce({
      recipes: mockRecipes.slice(0, 2),
      total: 10,
      hasMore: true
    });

    render(<RecipeList {...defaultProps} infinite={true} />);

    await waitFor(() => {
      expect(screen.getByText('Spaghetti Carbonara')).toBeInTheDocument();
      expect(screen.getByText('Tomato Soup')).toBeInTheDocument();
    });

    // Mock second load for infinite scroll
    recipeAPI.getRecipes.mockResolvedValueOnce({
      recipes: [mockRecipes[2]],
      total: 10,
      hasMore: false
    });

    // Simulate scroll to bottom
    const scrollContainer = screen.getByTestId('recipe-list-container');
    scrollContainer.scrollTop = scrollContainer.scrollHeight;

    await waitFor(() => {
      expect(screen.getByText('Caesar Salad')).toBeInTheDocument();
    });
  });

  it('supports keyboard navigation', async () => {
    const user = userEvent.setup();
    const onRecipeSelectMock = jest.fn();

    render(<RecipeList {...defaultProps} onRecipeSelect={onRecipeSelectMock} />);

    await waitFor(() => {
      expect(screen.getByText('Spaghetti Carbonara')).toBeInTheDocument();
    });

    const firstRecipeCard = screen.getByText('Spaghetti Carbonara').closest('[data-testid="recipe-card"]');
    firstRecipeCard?.focus();

    // Test Enter key
    await user.keyboard('{Enter}');
    expect(onRecipeSelectMock).toHaveBeenCalledWith(mockRecipes[0]);

    // Test arrow key navigation
    await user.keyboard('{ArrowDown}');
    const secondRecipeCard = screen.getByText('Tomato Soup').closest('[data-testid="recipe-card"]');
    expect(secondRecipeCard).toHaveFocus();
  });
});