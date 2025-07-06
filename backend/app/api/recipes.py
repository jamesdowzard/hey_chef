"""
Recipe API endpoints for Hey Chef v2.

HTTP endpoints for recipe management, integration with Notion API,
and recipe-related operations.
"""

import os
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.core.config import Settings
from app.core.models import RecipeSearchRequest, RecipeResponse, ErrorResponse
from app.core.logger import get_logger

logger = get_logger()
router = APIRouter()

# RecipeSearchRequest is imported from app.core.models

class RecipeCreateRequest(BaseModel):
    """Request model for creating a new recipe."""
    title: str
    description: Optional[str] = None
    ingredients: List[str]
    instructions: List[str]
    category: Optional[str] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None

class RecipeUpdateRequest(BaseModel):
    """Request model for updating a recipe."""
    title: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[List[str]] = None
    instructions: Optional[List[str]] = None
    category: Optional[str] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None

class RecipeListResponse(BaseModel):
    """Response model for recipe list."""
    recipes: List[Dict[str, Any]]
    total: int
    page: int
    limit: int

async def get_settings() -> Settings:
    """Dependency to get settings."""
    return Settings()

async def get_notion_client():
    """Get Notion API client if available."""
    try:
        # Check if Notion MCP server is available
        recipe_api_url = os.getenv("RECIPE_API_URL", "http://localhost:3333")
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{recipe_api_url}/health", timeout=5.0)
            if response.status_code == 200:
                return recipe_api_url
        return None
    except Exception as e:
        logger.warning(f"Notion API not available: {e}")
        return None

@router.get("/health")
async def recipes_health_check():
    """Health check for recipe service."""
    notion_url = await get_notion_client()
    return {
        "status": "healthy",
        "notion_api": "available" if notion_url else "unavailable",
        "notion_url": notion_url
    }

@router.get("/", response_model=RecipeListResponse)
async def list_recipes(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    settings: Settings = Depends(get_settings)
):
    """
    List all available recipes with pagination.
    
    Returns paginated list of recipes from Notion API or default recipes.
    """
    try:
        notion_url = await get_notion_client()
        
        if notion_url:
            # Fetch from Notion API
            import httpx
            async with httpx.AsyncClient() as client:
                params = {"page": page, "limit": limit}
                if category:
                    params["category"] = category
                
                response = await client.get(
                    f"{notion_url}/recipes",
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return RecipeListResponse(
                        recipes=data.get("recipes", []),
                        total=data.get("total", 0),
                        page=page,
                        limit=limit
                    )
                else:
                    logger.error(f"Notion API error: {response.status_code}")
                    raise HTTPException(status_code=502, detail="Recipe service unavailable")
        
        # Fallback to default recipe
        default_recipe = {
            "id": "default",
            "title": "Simple Scrambled Eggs",
            "description": "A basic scrambled eggs recipe perfect for beginners",
            "ingredients": [
                "3 large eggs",
                "2 tablespoons butter",
                "Salt to taste",
                "Black pepper to taste",
                "Optional: 2 tablespoons milk or cream"
            ],
            "instructions": [
                "Crack eggs into a bowl and whisk together",
                "Add salt, pepper, and milk if using",
                "Heat butter in a non-stick pan over medium-low heat",
                "Pour in the egg mixture",
                "Gently stir and scramble until eggs are just set",
                "Remove from heat and serve immediately"
            ],
            "category": "Breakfast",
            "prep_time": 5,
            "cook_time": 5,
            "servings": 2
        }
        
        recipes = [default_recipe] if not category or category.lower() == "breakfast" else []
        
        return RecipeListResponse(
            recipes=recipes,
            total=len(recipes),
            page=page,
            limit=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list recipes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list recipes: {str(e)}")

@router.get("/{recipe_id}", response_model=Dict[str, Any])
async def get_recipe(
    recipe_id: str,
    settings: Settings = Depends(get_settings)
):
    """
    Get a specific recipe by ID.
    
    Returns detailed recipe information including ingredients and instructions.
    """
    try:
        notion_url = await get_notion_client()
        
        if notion_url:
            # Fetch from Notion API
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{notion_url}/recipes/{recipe_id}",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    raise HTTPException(status_code=404, detail="Recipe not found")
                else:
                    logger.error(f"Notion API error: {response.status_code}")
                    raise HTTPException(status_code=502, detail="Recipe service unavailable")
        
        # Fallback to default recipe
        if recipe_id == "default":
            return {
                "id": "default",
                "title": "Simple Scrambled Eggs",
                "description": "A basic scrambled eggs recipe perfect for beginners",
                "ingredients": [
                    "3 large eggs",
                    "2 tablespoons butter", 
                    "Salt to taste",
                    "Black pepper to taste",
                    "Optional: 2 tablespoons milk or cream"
                ],
                "instructions": [
                    "Crack eggs into a bowl and whisk together",
                    "Add salt, pepper, and milk if using",
                    "Heat butter in a non-stick pan over medium-low heat",
                    "Pour in the egg mixture",
                    "Gently stir and scramble until eggs are just set",
                    "Remove from heat and serve immediately"
                ],
                "category": "Breakfast",
                "prep_time": 5,
                "cook_time": 5,
                "servings": 2,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        else:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recipe {recipe_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recipe: {str(e)}")

@router.post("/search", response_model=Dict[str, Any])
async def search_recipes(
    request: RecipeSearchRequest,
    settings: Settings = Depends(get_settings)
):
    """
    Search recipes by query string.
    
    Searches recipe titles, descriptions, and ingredients.
    """
    try:
        notion_url = await get_notion_client()
        
        if notion_url:
            # Search via Notion API
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{notion_url}/recipes/search",
                    json=request.model_dump(),
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Notion API search error: {response.status_code}")
                    raise HTTPException(status_code=502, detail="Recipe search service unavailable")
        
        # Fallback search in default recipe
        default_recipe = {
            "id": "default",
            "title": "Simple Scrambled Eggs", 
            "description": "A basic scrambled eggs recipe perfect for beginners",
            "category": "Breakfast"
        }
        
        query_lower = request.query.lower()
        results = []
        
        # Simple text search
        if (query_lower in default_recipe["title"].lower() or 
            query_lower in default_recipe["description"].lower() or
            query_lower == "eggs" or query_lower == "breakfast"):
            results.append(default_recipe)
        
        return {
            "results": results[:request.limit],
            "total": len(results),
            "query": request.query
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search recipes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search recipes: {str(e)}")

@router.post("/", response_model=Dict[str, Any])
async def create_recipe(
    request: RecipeCreateRequest,
    settings: Settings = Depends(get_settings)
):
    """
    Create a new recipe.
    
    Creates a new recipe in Notion database or returns error if not available.
    """
    try:
        notion_url = await get_notion_client()
        
        if not notion_url:
            raise HTTPException(
                status_code=503, 
                detail="Recipe creation not available - Notion API not connected"
            )
        
        # Create via Notion API
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{notion_url}/recipes",
                json=request.model_dump(),
                timeout=10.0
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                logger.error(f"Notion API create error: {response.status_code}")
                raise HTTPException(status_code=502, detail="Failed to create recipe")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create recipe: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create recipe: {str(e)}")

@router.put("/{recipe_id}", response_model=Dict[str, Any])
async def update_recipe(
    recipe_id: str,
    request: RecipeUpdateRequest,
    settings: Settings = Depends(get_settings)
):
    """
    Update an existing recipe.
    
    Updates recipe in Notion database or returns error if not available.
    """
    try:
        notion_url = await get_notion_client()
        
        if not notion_url:
            raise HTTPException(
                status_code=503,
                detail="Recipe updates not available - Notion API not connected"
            )
        
        # Update via Notion API
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{notion_url}/recipes/{recipe_id}",
                json=request.model_dump(exclude_unset=True),
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="Recipe not found")
            else:
                logger.error(f"Notion API update error: {response.status_code}")
                raise HTTPException(status_code=502, detail="Failed to update recipe")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update recipe {recipe_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update recipe: {str(e)}")

@router.delete("/{recipe_id}", response_model=Dict[str, Any])
async def delete_recipe(
    recipe_id: str,
    settings: Settings = Depends(get_settings)
):
    """
    Delete a recipe.
    
    Deletes recipe from Notion database or returns error if not available.
    """
    try:
        notion_url = await get_notion_client()
        
        if not notion_url:
            raise HTTPException(
                status_code=503,
                detail="Recipe deletion not available - Notion API not connected"
            )
        
        # Delete via Notion API
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{notion_url}/recipes/{recipe_id}",
                timeout=10.0
            )
            
            if response.status_code == 200:
                return {"status": "success", "message": "Recipe deleted successfully"}
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="Recipe not found")
            else:
                logger.error(f"Notion API delete error: {response.status_code}")
                raise HTTPException(status_code=502, detail="Failed to delete recipe")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete recipe {recipe_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete recipe: {str(e)}")

@router.get("/categories/list", response_model=Dict[str, Any])
async def list_categories(settings: Settings = Depends(get_settings)):
    """
    Get list of recipe categories.
    
    Returns available recipe categories from Notion or default categories.
    """
    try:
        notion_url = await get_notion_client()
        
        if notion_url:
            # Get categories from Notion API
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{notion_url}/recipes/categories",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
        
        # Fallback categories
        return {
            "categories": [
                "Breakfast",
                "Lunch", 
                "Dinner",
                "Snacks",
                "Desserts",
                "Beverages",
                "Appetizers",
                "Main Course",
                "Side Dishes"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@router.get("/{recipe_id}/content", response_model=Dict[str, Any])
async def get_recipe_content(
    recipe_id: str,
    settings: Settings = Depends(get_settings)
):
    """
    Get formatted recipe content for audio processing.
    
    Returns recipe content formatted for voice assistant interaction.
    """
    try:
        # Get the recipe first
        recipe = await get_recipe(recipe_id, settings)
        
        # Format for voice interaction
        content_parts = []
        content_parts.append(f"Recipe: {recipe['title']}")
        
        if recipe.get('description'):
            content_parts.append(f"Description: {recipe['description']}")
        
        # Add prep info
        if recipe.get('prep_time') or recipe.get('cook_time'):
            time_info = []
            if recipe.get('prep_time'):
                time_info.append(f"prep time {recipe['prep_time']} minutes")
            if recipe.get('cook_time'):
                time_info.append(f"cook time {recipe['cook_time']} minutes")
            content_parts.append(f"Time: {', '.join(time_info)}")
        
        if recipe.get('servings'):
            content_parts.append(f"Serves: {recipe['servings']}")
        
        # Add ingredients
        if recipe.get('ingredients'):
            content_parts.append("Ingredients:")
            for ingredient in recipe['ingredients']:
                content_parts.append(f"- {ingredient}")
        
        # Add instructions
        if recipe.get('instructions'):
            content_parts.append("Instructions:")
            for i, instruction in enumerate(recipe['instructions'], 1):
                content_parts.append(f"{i}. {instruction}")
        
        formatted_content = "\n".join(content_parts)
        
        return {
            "recipe_id": recipe_id,
            "title": recipe['title'],
            "formatted_content": formatted_content,
            "word_count": len(formatted_content.split()),
            "character_count": len(formatted_content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recipe content for {recipe_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recipe content: {str(e)}")