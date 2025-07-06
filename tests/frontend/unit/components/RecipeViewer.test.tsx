/**
 * Unit tests for RecipeViewer component.
 */

import React from 'react';
import { render, screen, waitFor } from '../../fixtures/test-utils';
import userEvent from '@testing-library/user-event';
import { RecipeViewer } from '../../../../frontend/src/components/RecipeViewer';
import { createMockRecipe } from '../../fixtures/test-utils';

// Mock the websocket service
jest.mock('../../../../frontend/src/services/websocket', () => ({
  websocketService: {
    sendMessage: jest.fn(),
    connect: jest.fn(),
    disconnect: jest.fn(),
    isConnected: jest.fn(() => true),
  },
}));

describe('RecipeViewer Component', () => {
  const mockRecipe = createMockRecipe({
    title: 'Test Spaghetti Recipe',
    description: 'A delicious test recipe',
    prep_time: 10,
    cook_time: 20,
    total_time: 30,
    servings: 4,
    difficulty: 'easy',
    ingredients: [
      '400g spaghetti',
      '2 tbsp olive oil',
      '3 cloves garlic',
      'Salt and pepper to taste'
    ],
    instructions: [
      'Boil water in a large pot',
      'Cook spaghetti according to package directions',
      'Heat olive oil in a pan',
      'Add garlic and cook until fragrant',
      'Combine pasta with garlic oil',
      'Season with salt and pepper'
    ]
  });

  const defaultProps = {
    recipe: mockRecipe,
    isVisible: true,
    onClose: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders recipe information correctly', () => {
    render(<RecipeViewer {...defaultProps} />);

    expect(screen.getByText('Test Spaghetti Recipe')).toBeInTheDocument();
    expect(screen.getByText('A delicious test recipe')).toBeInTheDocument();
    expect(screen.getByText('10 min')).toBeInTheDocument(); // prep time
    expect(screen.getByText('20 min')).toBeInTheDocument(); // cook time
    expect(screen.getByText('4 servings')).toBeInTheDocument();
    expect(screen.getByText('easy')).toBeInTheDocument();
  });

  it('displays ingredients list', () => {
    render(<RecipeViewer {...defaultProps} />);

    expect(screen.getByText('Ingredients')).toBeInTheDocument();
    expect(screen.getByText('400g spaghetti')).toBeInTheDocument();
    expect(screen.getByText('2 tbsp olive oil')).toBeInTheDocument();
    expect(screen.getByText('3 cloves garlic')).toBeInTheDocument();
    expect(screen.getByText('Salt and pepper to taste')).toBeInTheDocument();
  });

  it('displays instructions list', () => {
    render(<RecipeViewer {...defaultProps} />);

    expect(screen.getByText('Instructions')).toBeInTheDocument();
    expect(screen.getByText('Boil water in a large pot')).toBeInTheDocument();
    expect(screen.getByText('Cook spaghetti according to package directions')).toBeInTheDocument();
    expect(screen.getByText('Season with salt and pepper')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async () => {
    const user = userEvent.setup();
    const onCloseMock = jest.fn();
    
    render(<RecipeViewer {...defaultProps} onClose={onCloseMock} />);

    const closeButton = screen.getByLabelText(/close/i);
    await user.click(closeButton);

    expect(onCloseMock).toHaveBeenCalledTimes(1);
  });

  it('does not render when isVisible is false', () => {
    render(<RecipeViewer {...defaultProps} isVisible={false} />);

    expect(screen.queryByText('Test Spaghetti Recipe')).not.toBeInTheDocument();
  });

  it('handles recipe with no ingredients gracefully', () => {
    const recipeWithoutIngredients = createMockRecipe({
      ingredients: []
    });

    render(<RecipeViewer {...defaultProps} recipe={recipeWithoutIngredients} />);

    expect(screen.getByText('Ingredients')).toBeInTheDocument();
    expect(screen.getByText('No ingredients listed')).toBeInTheDocument();
  });

  it('handles recipe with no instructions gracefully', () => {
    const recipeWithoutInstructions = createMockRecipe({
      instructions: []
    });

    render(<RecipeViewer {...defaultProps} recipe={recipeWithoutInstructions} />);

    expect(screen.getByText('Instructions')).toBeInTheDocument();
    expect(screen.getByText('No instructions available')).toBeInTheDocument();
  });

  it('formats cooking times correctly', () => {
    const recipeWithLongTimes = createMockRecipe({
      prep_time: 65,  // 1 hour 5 minutes
      cook_time: 120, // 2 hours
      total_time: 185 // 3 hours 5 minutes
    });

    render(<RecipeViewer {...defaultProps} recipe={recipeWithLongTimes} />);

    expect(screen.getByText('1h 5m')).toBeInTheDocument(); // prep time
    expect(screen.getByText('2h')).toBeInTheDocument(); // cook time
    expect(screen.getByText('3h 5m')).toBeInTheDocument(); // total time
  });

  it('displays difficulty with appropriate styling', () => {
    render(<RecipeViewer {...defaultProps} />);

    const difficultyElement = screen.getByText('easy');
    expect(difficultyElement).toHaveClass('difficulty', 'easy');
  });

  it('allows asking questions about the recipe', async () => {
    const user = userEvent.setup();
    
    render(<RecipeViewer {...defaultProps} />);

    const askButton = screen.getByText(/ask about this recipe/i);
    await user.click(askButton);

    expect(screen.getByPlaceholderText(/ask a question/i)).toBeInTheDocument();
  });

  it('handles recipe scaling functionality', async () => {
    const user = userEvent.setup();
    
    render(<RecipeViewer {...defaultProps} />);

    const scaleButton = screen.getByText(/scale recipe/i);
    await user.click(scaleButton);

    const scaleInput = screen.getByLabelText(/servings/i);
    await user.clear(scaleInput);
    await user.type(scaleInput, '8');

    // Check that ingredients are scaled (simplified test)
    await waitFor(() => {
      expect(screen.getByText(/800g spaghetti/i)).toBeInTheDocument();
    });
  });

  it('supports keyboard navigation', async () => {
    const user = userEvent.setup();
    const onCloseMock = jest.fn();
    
    render(<RecipeViewer {...defaultProps} onClose={onCloseMock} />);

    // Test escape key
    await user.keyboard('{Escape}');
    expect(onCloseMock).toHaveBeenCalledTimes(1);
  });

  it('displays nutritional information when available', () => {
    const recipeWithNutrition = createMockRecipe({
      nutrition: {
        calories: 350,
        protein: 12,
        carbs: 45,
        fat: 8
      }
    });

    render(<RecipeViewer {...defaultProps} recipe={recipeWithNutrition} />);

    expect(screen.getByText('Nutrition')).toBeInTheDocument();
    expect(screen.getByText('350 calories')).toBeInTheDocument();
    expect(screen.getByText('12g protein')).toBeInTheDocument();
  });

  it('shows loading state during recipe updates', async () => {
    const user = userEvent.setup();
    
    render(<RecipeViewer {...defaultProps} />);

    const refreshButton = screen.getByLabelText(/refresh recipe/i);
    await user.click(refreshButton);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('handles error states gracefully', () => {
    const recipeWithError = null;

    render(<RecipeViewer {...defaultProps} recipe={recipeWithError} />);

    expect(screen.getByText(/recipe not found/i)).toBeInTheDocument();
  });

  it('supports printing recipe', async () => {
    const user = userEvent.setup();
    const printSpy = jest.spyOn(window, 'print').mockImplementation(() => {});
    
    render(<RecipeViewer {...defaultProps} />);

    const printButton = screen.getByLabelText(/print recipe/i);
    await user.click(printButton);

    expect(printSpy).toHaveBeenCalledTimes(1);
    
    printSpy.mockRestore();
  });

  it('allows saving recipe to favorites', async () => {
    const user = userEvent.setup();
    
    render(<RecipeViewer {...defaultProps} />);

    const favoriteButton = screen.getByLabelText(/add to favorites/i);
    await user.click(favoriteButton);

    expect(screen.getByLabelText(/remove from favorites/i)).toBeInTheDocument();
  });

  it('displays recipe tags when available', () => {
    const recipeWithTags = createMockRecipe({
      tags: ['quick', 'easy', 'vegetarian', 'italian']
    });

    render(<RecipeViewer {...defaultProps} recipe={recipeWithTags} />);

    expect(screen.getByText('quick')).toBeInTheDocument();
    expect(screen.getByText('easy')).toBeInTheDocument();
    expect(screen.getByText('vegetarian')).toBeInTheDocument();
    expect(screen.getByText('italian')).toBeInTheDocument();
  });

  it('handles responsive layout', () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });

    render(<RecipeViewer {...defaultProps} />);

    const container = screen.getByTestId('recipe-viewer');
    expect(container).toHaveClass('mobile-layout');
  });
});