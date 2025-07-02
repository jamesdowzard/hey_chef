import os
from dotenv import load_dotenv
from notion_client import Client
from fastapi import FastAPI, HTTPException

# Load .env into environment
load_dotenv()
print("Loaded NOTION_API_TOKEN:", os.getenv("NOTION_API_TOKEN"))
print("Loaded NOTION_RECIPES_DB_ID:", os.getenv("NOTION_RECIPES_DB_ID"))

app = FastAPI()
notion = Client(auth=os.getenv("NOTION_API_TOKEN"))

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "notion-api"}

def fetch_children(block_id, max_depth=3, current_depth=0):
    """Fetch children blocks with depth limiting to prevent timeouts."""
    if current_depth >= max_depth:
        return []
    
    try:
        blocks = notion.blocks.children.list(block_id=block_id)
        results = []
        for block in blocks.get("results", []):
            # Only fetch children for certain block types to reduce API calls
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
                    # If fetching children fails, continue without them
                    block["children"] = []
            results.append(block)
        return results
    except Exception as e:
        print(f"Error fetching children for {block_id}: {e}")
        return []

@app.get("/recipes")
def list_recipes():
    db_id = os.getenv("NOTION_RECIPES_DB_ID")
    if not db_id:
        raise HTTPException(status_code=500, detail="Database ID not set")
    response = notion.databases.query(database_id=db_id)
    recipes = []
    for page in response.get("results", []):
        props = page.get("properties", {})
        # exclude rollup properties
        filtered = {name: prop for name, prop in props.items() if prop.get("type") != "rollup"}
        recipes.append({"id": page.get("id"), "properties": filtered})
    return {"recipes": recipes}

@app.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: str):
    """Get recipe with timeout protection."""
    try:
        page = notion.pages.retrieve(page_id=recipe_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    props = page.get("properties", {})
    filtered = {name: prop for name, prop in props.items() if prop.get("type") != "rollup"}
    
    # Fetch content with limited depth to prevent timeouts
    try:
        content = fetch_children(recipe_id, max_depth=2)  # Limit to 2 levels deep
    except Exception as e:
        print(f"Error fetching content for {recipe_id}: {e}")
        content = []  # Return empty content if fetch fails
    
    return {"id": recipe_id, "properties": filtered, "content": content} 