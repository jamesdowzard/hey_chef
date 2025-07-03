import React, { useState, useEffect } from 'react';
import { Clock, Users, ChefHat, CheckCircle, Circle, ArrowLeft, ArrowRight, Timer, Thermometer } from 'lucide-react';
import { Recipe } from '../types';

interface RecipeViewerProps {
  recipe: Recipe | null;
  onStepChange?: (stepNumber: number) => void;
  className?: string;
}

export const RecipeViewer: React.FC<RecipeViewerProps> = ({
  recipe,
  onStepChange,
  className = ''
}) => {
  const [checkedIngredients, setCheckedIngredients] = useState<Set<string>>(new Set());

  // Reset ingredient checkboxes when recipe changes
  useEffect(() => {
    setCheckedIngredients(new Set());
  }, [recipe?.id]);

  const toggleIngredient = (ingredientId: string) => {
    setCheckedIngredients(prev => {
      const newSet = new Set(prev);
      if (newSet.has(ingredientId)) {
        newSet.delete(ingredientId);
      } else {
        newSet.add(ingredientId);
      }
      return newSet;
    });
  };

  if (!recipe) {
    return (
      <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
        <div className="text-center text-gray-500 py-12">
          <ChefHat className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium mb-2">No Recipe Selected</h3>
          <p className="text-sm">Choose a recipe to start cooking!</p>
        </div>
      </div>
    );
  }

  const currentStep = recipe.currentStep || 0;
  const totalSteps = recipe.instructions.length;

  const handlePreviousStep = () => {
    if (currentStep > 0) {
      onStepChange?.(currentStep - 1);
    }
  };

  const handleNextStep = () => {
    if (currentStep < totalSteps - 1) {
      onStepChange?.(currentStep + 1);
    }
  };

  const getDifficultyColor = () => {
    switch (recipe.difficulty) {
      case 'easy': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'hard': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatTime = (minutes: number) => {
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  };

  return (
    <div className={`bg-white rounded-lg shadow-lg overflow-hidden ${className}`}>
      {/* Recipe Header */}
      <div className="relative">
        {recipe.imageUrl ? (
          <>
            <img
              src={recipe.imageUrl}
              alt={recipe.title}
              className="w-full h-48 object-cover"
              onError={(e) => {
                e.currentTarget.style.display = 'none';
              }}
            />
            <div className="absolute inset-0 bg-black bg-opacity-40 flex items-end">
              <div className="p-6 text-white w-full">
                <h1 className="text-2xl font-bold mb-2">{recipe.title}</h1>
                <p className="text-gray-200 text-sm">{recipe.description}</p>
              </div>
            </div>
          </>
        ) : (
          <div className="bg-gradient-to-br from-primary-500 to-primary-700 p-6 text-white">
            <div className="flex items-center space-x-3 mb-2">
              <ChefHat className="w-8 h-8" />
              <h1 className="text-2xl font-bold">{recipe.title}</h1>
            </div>
            <p className="text-primary-100 text-sm">{recipe.description}</p>
          </div>
        )}
      </div>

      {/* Recipe Info */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex flex-wrap items-center gap-4 mb-4">
          <div className="flex items-center space-x-2">
            <Clock className="w-5 h-5 text-gray-500" />
            <span className="text-sm font-medium">{formatTime(recipe.cookingTime)}</span>
          </div>
          <div className="flex items-center space-x-2">
            <Users className="w-5 h-5 text-gray-500" />
            <span className="text-sm font-medium">{recipe.servings} servings</span>
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-medium ${getDifficultyColor()}`}>
            {recipe.difficulty.charAt(0).toUpperCase() + recipe.difficulty.slice(1)}
          </div>
        </div>

        {/* Tags */}
        {recipe.tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {recipe.tags.map((tag, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Ingredients */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Ingredients</h2>
          <div className="text-sm text-gray-500">
            {checkedIngredients.size} of {recipe.ingredients.length} checked
          </div>
        </div>
        <div className="grid grid-cols-1 gap-2">
          {recipe.ingredients.map((ingredient) => {
            const isChecked = checkedIngredients.has(ingredient.id);
            return (
              <div 
                key={ingredient.id} 
                className={`
                  flex items-center justify-between py-3 px-3 rounded-lg cursor-pointer transition-all duration-200
                  ${isChecked 
                    ? 'bg-green-50 border border-green-200' 
                    : 'hover:bg-gray-50'
                  }
                `}
                onClick={() => toggleIngredient(ingredient.id)}
              >
                <div className="flex items-center space-x-3">
                  <button
                    className={`
                      flex-shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all duration-200
                      ${isChecked
                        ? 'bg-green-500 border-green-500 text-white'
                        : 'border-gray-300 hover:border-green-400'
                      }
                    `}
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleIngredient(ingredient.id);
                    }}
                  >
                    {isChecked && <CheckCircle className="w-3 h-3" />}
                  </button>
                  <span className={`text-sm font-medium transition-all duration-200 ${
                    isChecked ? 'text-green-700 line-through' : 'text-gray-800'
                  }`}>
                    {ingredient.name}
                  </span>
                  {ingredient.notes && (
                    <span className="text-xs text-gray-500 italic">
                      ({ingredient.notes})
                    </span>
                  )}
                </div>
                <div className={`text-sm transition-all duration-200 ${
                  isChecked ? 'text-green-600' : 'text-gray-600'
                }`}>
                  {ingredient.amount} {ingredient.unit}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Instructions */}
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Instructions</h2>
          <div className="text-sm text-gray-500">
            Step {currentStep + 1} of {totalSteps}
          </div>
        </div>

        {/* Current Step */}
        <div className="mb-6">
          <div className="bg-primary-50 border border-primary-200 rounded-lg p-6">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-10 h-10 bg-primary-500 text-white rounded-full flex items-center justify-center text-lg font-bold">
                {currentStep + 1}
              </div>
              <div className="flex-1">
                <p className="text-gray-800 leading-relaxed text-lg mb-3">
                  {recipe.instructions[currentStep]?.description}
                </p>
                
                {/* Step metadata */}
                <div className="flex flex-wrap gap-4">
                  {recipe.instructions[currentStep]?.duration && (
                    <div className="flex items-center space-x-2 bg-white px-3 py-2 rounded-lg border border-primary-200">
                      <Timer className="w-5 h-5 text-primary-600" />
                      <span className="text-sm font-medium text-gray-700">
                        {recipe.instructions[currentStep].duration} min
                      </span>
                    </div>
                  )}
                  {recipe.instructions[currentStep]?.temperature && (
                    <div className="flex items-center space-x-2 bg-white px-3 py-2 rounded-lg border border-primary-200">
                      <Thermometer className="w-5 h-5 text-red-500" />
                      <span className="text-sm font-medium text-gray-700">
                        {recipe.instructions[currentStep].temperature}
                      </span>
                    </div>
                  )}
                </div>

                {recipe.instructions[currentStep]?.notes && (
                  <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="text-sm text-yellow-800">
                      <strong>Note:</strong> {recipe.instructions[currentStep].notes}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Step Navigation */}
        <div className="space-y-4">
          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-primary-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${((currentStep + 1) / totalSteps) * 100}%` }}
            />
          </div>

          {/* Navigation Buttons */}
          <div className="flex items-center justify-between">
            <button
              onClick={handlePreviousStep}
              disabled={currentStep === 0}
              className={`
                flex items-center space-x-2 px-6 py-3 rounded-lg font-medium text-sm transition-all duration-200
                ${currentStep === 0
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-200 hover:bg-gray-300 text-gray-700 hover:shadow-md'
                }
              `}
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="hidden sm:inline">Previous</span>
            </button>

            {/* Step Dots - Hidden on small screens */}
            <div className="hidden sm:flex space-x-2 overflow-x-auto max-w-xs">
              {recipe.instructions.map((_, index) => (
                <button
                  key={index}
                  onClick={() => onStepChange?.(index)}
                  className={`
                    flex-shrink-0 w-4 h-4 rounded-full transition-all duration-200 hover:scale-110
                    ${index === currentStep
                      ? 'bg-primary-500 ring-2 ring-primary-300'
                      : index < currentStep
                      ? 'bg-green-500'
                      : 'bg-gray-300 hover:bg-gray-400'
                    }
                  `}
                  title={`Step ${index + 1}`}
                />
              ))}
            </div>

            {/* Mobile Step Counter */}
            <div className="sm:hidden text-sm text-gray-600 font-medium">
              {currentStep + 1} / {totalSteps}
            </div>

            <button
              onClick={handleNextStep}
              disabled={currentStep === totalSteps - 1}
              className={`
                flex items-center space-x-2 px-6 py-3 rounded-lg font-medium text-sm transition-all duration-200
                ${currentStep === totalSteps - 1
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-primary-500 hover:bg-primary-600 text-white hover:shadow-md transform hover:scale-105'
                }
              `}
            >
              <span className="hidden sm:inline">
                {currentStep === totalSteps - 1 ? 'Complete!' : 'Next'}
              </span>
              <span className="sm:hidden">
                {currentStep === totalSteps - 1 ? '✓' : '→'}
              </span>
              {currentStep < totalSteps - 1 && <ArrowRight className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* All Steps Overview */}
        <div className="mt-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">All Steps</h3>
            <div className="text-sm text-gray-500">
              {recipe.instructions.filter((_, index) => index < currentStep).length} of {totalSteps} completed
            </div>
          </div>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {recipe.instructions.map((instruction, index) => (
              <div
                key={instruction.id}
                className={`
                  flex items-start space-x-4 p-4 rounded-lg cursor-pointer transition-all duration-200 border
                  ${index === currentStep
                    ? 'bg-primary-50 border-primary-300 shadow-md transform scale-[1.02]'
                    : index < currentStep
                    ? 'bg-green-50 border-green-200 hover:bg-green-100'
                    : 'bg-gray-50 border-gray-200 hover:bg-gray-100 hover:shadow-sm'
                  }
                `}
                onClick={() => onStepChange?.(index)}
              >
                <div className={`
                  flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all duration-200
                  ${index === currentStep
                    ? 'bg-primary-500 text-white ring-2 ring-primary-300'
                    : index < currentStep
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-300 text-gray-600'
                  }
                `}>
                  {index < currentStep ? (
                    <CheckCircle className="w-5 h-5" />
                  ) : (
                    index + 1
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm leading-relaxed ${
                    index === currentStep 
                      ? 'text-gray-900 font-medium' 
                      : index < currentStep 
                      ? 'text-gray-700' 
                      : 'text-gray-600'
                  }`}>
                    {instruction.description}
                  </p>
                  
                  {/* Step metadata */}
                  <div className="flex flex-wrap gap-3 mt-2">
                    {instruction.duration && (
                      <div className="flex items-center space-x-1">
                        <Timer className="w-3 h-3 text-gray-500" />
                        <span className="text-xs text-gray-500">
                          {instruction.duration} min
                        </span>
                      </div>
                    )}
                    {instruction.temperature && (
                      <div className="flex items-center space-x-1">
                        <Thermometer className="w-3 h-3 text-red-500" />
                        <span className="text-xs text-gray-500">
                          {instruction.temperature}
                        </span>
                      </div>
                    )}
                  </div>

                  {instruction.notes && (
                    <p className="text-xs text-gray-500 mt-2 italic">
                      {instruction.notes}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};