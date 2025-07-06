#!/usr/bin/env python3
"""
Notion MCP Server for Hey Chef v2

This server provides the REST API endpoints that the v2 backend expects
for recipe management using the Notion API.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from notion_client import Client
from dotenv import load_dotenv
import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI(title="Hey Chef Notion MCP Server", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Notion client
notion_token = os.getenv("NOTION_API_TOKEN")
recipes_db_id = os.getenv("NOTION_RECIPES_DB_ID")

if not notion_token:
    raise ValueError("NOTION_API_TOKEN environment variable is required")
if not recipes_db_id:
    raise ValueError("NOTION_RECIPES_DB_ID environment variable is required")

notion = Client(auth=notion_token)

# Pydantic models
class RecipeCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    ingredients: List[str]
    instructions: List[str]
    category: Optional[str] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None

class RecipeUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[List[str]] = None
    instructions: Optional[List[str]] = None
    category: Optional[str] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None

class RecipeSearchRequest(BaseModel):
    query: str
    limit: int = 10
    offset: int = 0

def extract_text_from_blocks(blocks: List[Dict]) -> str:
    """Extract text content from Notion blocks."""
    text_parts = []
    for block in blocks:
        block_type = block.get("type", "")
        if block_type == "paragraph":
            text_parts.extend(extract_text_from_rich_text(block.get("paragraph", {}).get("rich_text", [])))
        elif block_type == "heading_1":
            text_parts.extend(extract_text_from_rich_text(block.get("heading_1", {}).get("rich_text", [])))
        elif block_type == "heading_2":
            text_parts.extend(extract_text_from_rich_text(block.get("heading_2", {}).get("rich_text", [])))
        elif block_type == "heading_3":
            text_parts.extend(extract_text_from_rich_text(block.get("heading_3", {}).get("rich_text", [])))
        elif block_type == "bulleted_list_item":
            text_parts.extend(extract_text_from_rich_text(block.get("bulleted_list_item", {}).get("rich_text", [])))
        elif block_type == "numbered_list_item":
            text_parts.extend(extract_text_from_rich_text(block.get("numbered_list_item", {}).get("rich_text", [])))
    return " ".join(text_parts)

def extract_text_from_rich_text(rich_text: List[Dict]) -> List[str]:
    """Extract plain text from Notion rich text objects."""
    return [text_obj.get("plain_text", "") for text_obj in rich_text]

def fetch_children(block_id: str, max_depth: int = 2, current_depth: int = 0) -> List[Dict]:
    """Fetch children blocks with depth limiting to prevent timeouts."""
    if current_depth >= max_depth:
        return []
    
    try:
        blocks = notion.blocks.children.list(block_id=block_id)
        results = []
        for block in blocks.get("results", []):
            if (block.get("has_children") and 
                current_depth < max_depth - 1 and
                block.get("type") in ["toggle", "column_list", "table"]):
                try:
                    block["children"] = fetch_children(
                        block.get("id"), 
                        max_depth, 
                        current_depth + 1
                    )
                except Exception:
                    block["children"] = []
            results.append(block)
        return results
    except Exception as e:
        print(f"Error fetching children for {block_id}: {e}")
        return []

def parse_recipe_properties(properties: Dict) -> Dict:
    """Parse Notion properties into a clean recipe format."""
    recipe = {}
    
    for prop_name, prop_data in properties.items():
        prop_type = prop_data.get("type", "")
        
        if prop_type == "title":
            recipe["title"] = "".join([t.get("plain_text", "") for t in prop_data.get("title", [])])
        elif prop_type == "rich_text":
            recipe[prop_name.lower()] = "".join([t.get("plain_text", "") for t in prop_data.get("rich_text", [])])
        elif prop_type == "select":
            select_obj = prop_data.get("select")
            recipe[prop_name.lower()] = select_obj.get("name", "") if select_obj else ""
        elif prop_type == "number":
            recipe[prop_name.lower()] = prop_data.get("number", 0)
        elif prop_type == "multi_select":
            recipe[prop_name.lower()] = [item.get("name", "") for item in prop_data.get("multi_select", [])]
        elif prop_type == "checkbox":
            recipe[prop_name.lower()] = prop_data.get("checkbox", False)
        elif prop_type == "date":
            date_obj = prop_data.get("date")
            if date_obj:
                recipe[prop_name.lower()] = date_obj.get("start", "")
    
    return recipe

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "notion-mcp-server"}

@app.get("/recipes")
async def list_recipes(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = Query(None)
):
    """List recipes from Notion database."""
    try:
        # Calculate offset
        offset = (page - 1) * limit
        
        # Build filter
        filter_conditions = []
        if category:
            filter_conditions.append({
                "property": "Category",
                "select": {
                    "equals": category
                }
            })
        
        # Query database
        query_params = {
            "database_id": recipes_db_id,
            "page_size": limit,
            "start_cursor": None  # TODO: Implement proper pagination with cursor
        }
        
        if filter_conditions:
            if len(filter_conditions) == 1:
                query_params["filter"] = filter_conditions[0]
            else:
                query_params["filter"] = {
                    "and": filter_conditions
                }
        
        response = notion.databases.query(**query_params)
        
        recipes = []
        for page_data in response.get("results", []):
            recipe = parse_recipe_properties(page_data.get("properties", {}))
            recipe["id"] = page_data.get("id")
            recipes.append(recipe)
        
        # Simple offset-based pagination (not ideal for large datasets)
        paginated_recipes = recipes[offset:offset + limit] if offset > 0 else recipes
        
        return {
            "recipes": paginated_recipes,
            "total": len(recipes),
            "page": page,
            "limit": limit
        }
        
    except Exception as e:
        print(f"Error listing recipes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list recipes: {str(e)}")

@app.get("/recipes/categories")
async def get_categories():
    """Get list of available categories."""
    try:
        # Get database schema to find category options
        db = notion.databases.retrieve(database_id=recipes_db_id)
        
        categories = []
        properties = db.get("properties", {})
        
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") in ["select", "multi_select"] and prop_name.lower() in ["category", "meal type"]:
                if prop_data.get("type") == "select":
                    options = prop_data.get("select", {}).get("options", [])
                else:  # multi_select
                    options = prop_data.get("multi_select", {}).get("options", [])
                categories = [option.get("name", "") for option in options]
                break
        
        return {"categories": categories}
        
    except Exception as e:
        print(f"Error getting categories: {e}")
        # Return default categories if we can't get them from Notion
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

@app.get("/recipes/{recipe_id}")
async def get_recipe(recipe_id: str):
    """Get a specific recipe by ID."""
    try:
        # Get the page
        page = notion.pages.retrieve(page_id=recipe_id)
        
        # Parse properties
        recipe = parse_recipe_properties(page.get("properties", {}))
        recipe["id"] = recipe_id
        
        # Get page content
        content = fetch_children(recipe_id, max_depth=2)
        recipe["content"] = content
        
        # Extract ingredients and instructions from content
        ingredients = []
        instructions = []
        
        for block in content:
            block_type = block.get("type", "")
            if block_type == "bulleted_list_item":
                text = extract_text_from_rich_text(block.get("bulleted_list_item", {}).get("rich_text", []))
                if text:
                    ingredients.extend(text)
            elif block_type == "numbered_list_item":
                text = extract_text_from_rich_text(block.get("numbered_list_item", {}).get("rich_text", []))
                if text:
                    instructions.extend(text)
        
        recipe["ingredients"] = ingredients
        recipe["instructions"] = instructions
        
        return recipe
        
    except Exception as e:
        print(f"Error getting recipe {recipe_id}: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Recipe not found")
        raise HTTPException(status_code=500, detail=f"Failed to get recipe: {str(e)}")

@app.post("/recipes/search")
async def search_recipes(request: RecipeSearchRequest):
    """Search recipes by query string."""
    try:
        # Get all recipes first (simple approach)
        response = notion.databases.query(database_id=recipes_db_id)
        
        results = []
        query_lower = request.query.lower()
        
        for page_data in response.get("results", []):
            recipe = parse_recipe_properties(page_data.get("properties", {}))
            recipe["id"] = page_data.get("id")
            
            # Simple text search in title and description
            title = recipe.get("title", "").lower()
            description = recipe.get("description", "").lower()
            
            if (query_lower in title or 
                query_lower in description or
                any(query_lower in str(v).lower() for v in recipe.values())):
                results.append(recipe)
        
        # Apply pagination
        paginated_results = results[request.offset:request.offset + request.limit]
        
        return {
            "results": paginated_results,
            "total": len(results),
            "query": request.query,
            "limit": request.limit,
            "offset": request.offset
        }
        
    except Exception as e:
        print(f"Error searching recipes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search recipes: {str(e)}")

@app.post("/recipes", status_code=201)
async def create_recipe(request: RecipeCreateRequest):
    """Create a new recipe."""
    try:
        # Build properties for the new page
        properties = {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": request.title
                        }
                    }
                ]
            }
        }
        
        if request.description:
            properties["Description"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": request.description
                        }
                    }
                ]
            }
        
        if request.category:
            properties["Category"] = {
                "select": {
                    "name": request.category
                }
            }
        
        if request.prep_time:
            properties["Prep Time"] = {
                "number": request.prep_time
            }
        
        if request.cook_time:
            properties["Cook Time"] = {
                "number": request.cook_time
            }
        
        if request.servings:
            properties["Servings"] = {
                "number": request.servings
            }
        
        # Create the page
        page = notion.pages.create(
            parent={"database_id": recipes_db_id},
            properties=properties
        )
        
        page_id = page["id"]
        
        # Add ingredients and instructions as content
        children = []
        
        if request.ingredients:
            children.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Ingredients"
                            }
                        }
                    ]
                }
            })
            
            for ingredient in request.ingredients:
                children.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": ingredient
                                }
                            }
                        ]
                    }
                })
        
        if request.instructions:
            children.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Instructions"
                            }
                        }
                    ]
                }
            })
            
            for instruction in request.instructions:
                children.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": instruction
                                }
                            }
                        ]
                    }
                })
        
        # Add content to the page
        if children:
            notion.blocks.children.append(block_id=page_id, children=children)
        
        # Return the created recipe
        return await get_recipe(page_id)
        
    except Exception as e:
        print(f"Error creating recipe: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create recipe: {str(e)}")

@app.put("/recipes/{recipe_id}")
async def update_recipe(recipe_id: str, request: RecipeUpdateRequest):
    """Update an existing recipe."""
    try:
        # Build properties to update
        properties = {}
        
        if request.title:
            properties["Name"] = {
                "title": [
                    {
                        "text": {
                            "content": request.title
                        }
                    }
                ]
            }
        
        if request.description:
            properties["Description"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": request.description
                        }
                    }
                ]
            }
        
        if request.category:
            properties["Category"] = {
                "select": {
                    "name": request.category
                }
            }
        
        if request.prep_time is not None:
            properties["Prep Time"] = {
                "number": request.prep_time
            }
        
        if request.cook_time is not None:
            properties["Cook Time"] = {
                "number": request.cook_time
            }
        
        if request.servings is not None:
            properties["Servings"] = {
                "number": request.servings
            }
        
        # Update the page
        notion.pages.update(page_id=recipe_id, properties=properties)
        
        # TODO: Update ingredients and instructions in content
        # This would require more complex logic to replace existing content
        
        return await get_recipe(recipe_id)
        
    except Exception as e:
        print(f"Error updating recipe {recipe_id}: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Recipe not found")
        raise HTTPException(status_code=500, detail=f"Failed to update recipe: {str(e)}")

@app.delete("/recipes/{recipe_id}")
async def delete_recipe(recipe_id: str):
    """Delete a recipe."""
    try:
        # Archive the page (Notion doesn't support true deletion)
        notion.pages.update(page_id=recipe_id, archived=True)
        
        return {"status": "success", "message": "Recipe deleted successfully"}
        
    except Exception as e:
        print(f"Error deleting recipe {recipe_id}: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Recipe not found")
        raise HTTPException(status_code=500, detail=f"Failed to delete recipe: {str(e)}")

if __name__ == "__main__":
    print(f"Starting Notion MCP Server...")
    print(f"Notion Database ID: {recipes_db_id}")
    print(f"Server will be available at: http://localhost:3333")
    
    uvicorn.run(app, host="0.0.0.0", port=3333)