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

def fetch_children(block_id):
    blocks = notion.blocks.children.list(block_id=block_id)
    results = []
    for block in blocks.get("results", []):
        if block.get("has_children"):
            block["children"] = fetch_children(block.get("id"))
        results.append(block)
    return results

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
    try:
        page = notion.pages.retrieve(page_id=recipe_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Recipe not found")
    props = page.get("properties", {})
    filtered = {name: prop for name, prop in props.items() if prop.get("type") != "rollup"}
    content = fetch_children(recipe_id)
    return {"id": recipe_id, "properties": filtered, "content": content} 