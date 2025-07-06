import React, { useState, useEffect } from 'react';
import { 
  Search, 
  ChefHat, 
  Clock, 
  Users, 
  Filter,
  ChevronDown,
  Eye,
  Heart,
  Star
} from 'lucide-react';
import { Recipe, AsyncState } from '../types';

interface RecipeListProps {
  recipes: AsyncState<Recipe[]>;
  currentRecipe?: Recipe | null;
  categories: AsyncState<string[]>;
  onRecipeSelect: (recipe: Recipe) => void;
  onLoadMore?: () => void;
  onSearch?: (query: string) => void;
  onCategoryFilter?: (category?: string) => void;
  hasMore?: boolean;
  className?: string;
}

export const RecipeList: React.FC<RecipeListProps> = ({
  recipes,
  currentRecipe,
  categories,
  onRecipeSelect,
  onLoadMore,
  onSearch,
  onCategoryFilter,
  hasMore = false,
  className = ''
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>(undefined);
  const [showCategoryFilter, setShowCategoryFilter] = useState(false);

  const handleSearchChange = (query: string) => {
    setSearchQuery(query);
    if (onSearch) {
      // Debounce search
      const timeoutId = setTimeout(() => {
        onSearch(query);
      }, 300);
      return () => clearTimeout(timeoutId);
    }
  };

  const handleCategorySelect = (category?: string) => {
    setSelectedCategory(category);
    setShowCategoryFilter(false);
    if (onCategoryFilter) {
      onCategoryFilter(category);
    }
  };

  const getRecipeImage = (recipe: Recipe) => {
    // Placeholder image logic - in a real app this would come from recipe data
    return `https://via.placeholder.com/300x200?text=${encodeURIComponent(recipe.title)}`;
  };

  const formatDifficulty = (difficulty?: string) => {
    if (!difficulty) return 'Medium';
    return difficulty.charAt(0).toUpperCase() + difficulty.slice(1);
  };

  const formatCookingTime = (time?: number) => {
    if (!time) return '30 min';
    if (time < 60) return `${time} min`;
    const hours = Math.floor(time / 60);
    const minutes = time % 60;
    return `${hours}h ${minutes > 0 ? `${minutes}m` : ''}`;
  };

  return (
    <div className={`bg-white rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center space-x-3 mb-4">
          <ChefHat className="w-6 h-6 text-primary-500" />
          <h2 className="text-xl font-semibold text-gray-800">Recipes</h2>
        </div>

        {/* Search Bar */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search recipes..."
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        {/* Category Filter */}
        <div className="relative">
          <button
            onClick={() => setShowCategoryFilter(!showCategoryFilter)}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Filter className="w-4 h-4" />
            <span className="text-sm">
              {selectedCategory ? selectedCategory : 'All Categories'}
            </span>
            <ChevronDown className={`w-4 h-4 transition-transform ${showCategoryFilter ? 'rotate-180' : ''}`} />
          </button>

          {showCategoryFilter && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
              <button
                onClick={() => handleCategorySelect(undefined)}
                className={`w-full text-left px-4 py-2 hover:bg-gray-50 ${!selectedCategory ? 'bg-primary-50 text-primary-700' : ''}`}
              >
                All Categories
              </button>
              {categories.data?.map((category) => (
                <button
                  key={category}
                  onClick={() => handleCategorySelect(category)}
                  className={`w-full text-left px-4 py-2 hover:bg-gray-50 capitalize ${
                    selectedCategory === category ? 'bg-primary-50 text-primary-700' : ''
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recipe List */}
      <div className="p-6">
        {recipes.loading && (!recipes.data || recipes.data.length === 0) && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto mb-4"></div>
            <p className="text-gray-500">Loading recipes...</p>
          </div>
        )}

        {recipes.error && (
          <div className="text-center py-8">
            <div className="text-red-500 mb-2">Failed to load recipes</div>
            <p className="text-sm text-gray-500">{recipes.error.message}</p>
          </div>
        )}

        {recipes.data && recipes.data.length === 0 && !recipes.loading && (
          <div className="text-center py-8">
            <ChefHat className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No recipes found</p>
            {searchQuery && (
              <p className="text-sm text-gray-400 mt-2">
                Try adjusting your search or filter criteria
              </p>
            )}
          </div>
        )}

        {recipes.data && recipes.data.length > 0 && (
          <div className="space-y-4">
            {recipes.data.map((recipe) => (
              <div
                key={recipe.id}
                onClick={() => onRecipeSelect(recipe)}
                className={`
                  p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md
                  ${currentRecipe?.id === recipe.id 
                    ? 'border-primary-500 bg-primary-50' 
                    : 'border-gray-200 hover:border-gray-300'
                  }
                `}
              >
                <div className="flex items-start space-x-4">
                  {/* Recipe Image */}
                  <div className="flex-shrink-0">
                    <img
                      src={getRecipeImage(recipe)}
                      alt={recipe.title}
                      className="w-20 h-20 object-cover rounded-lg"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.src = `https://via.placeholder.com/80x80/f3f4f6/6b7280?text=${recipe.title.charAt(0)}`;
                      }}
                    />
                  </div>

                  {/* Recipe Details */}
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-medium text-gray-900 mb-1 truncate">
                      {recipe.title}
                    </h3>
                    
                    {recipe.description && (
                      <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                        {recipe.description}
                      </p>
                    )}

                    {/* Recipe Meta */}
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      {recipe.cookingTime && (
                        <div className="flex items-center space-x-1">
                          <Clock className="w-3 h-3" />
                          <span>{formatCookingTime(recipe.cookingTime)}</span>
                        </div>
                      )}
                      
                      {recipe.servings && (
                        <div className="flex items-center space-x-1">
                          <Users className="w-3 h-3" />
                          <span>{recipe.servings} servings</span>
                        </div>
                      )}
                      
                      <div className="flex items-center space-x-1">
                        <Star className="w-3 h-3" />
                        <span>{formatDifficulty(recipe.difficulty)}</span>
                      </div>
                    </div>

                    {/* Recipe Categories */}
                    {recipe.categories && recipe.categories.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {recipe.categories.slice(0, 3).map((category) => (
                          <span
                            key={category}
                            className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full"
                          >
                            {category}
                          </span>
                        ))}
                        {recipe.categories.length > 3 && (
                          <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full">
                            +{recipe.categories.length - 3} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Action Icons */}
                  <div className="flex-shrink-0 flex items-center space-x-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onRecipeSelect(recipe);
                      }}
                      className="p-2 text-gray-400 hover:text-primary-500 transition-colors"
                      title="View Recipe"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}

            {/* Load More Button */}
            {hasMore && (
              <div className="text-center pt-4">
                <button
                  onClick={onLoadMore}
                  disabled={recipes.loading}
                  className="px-6 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {recipes.loading ? 'Loading...' : 'Load More Recipes'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};