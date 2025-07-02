"""
Tests for the Notion API server.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
import json

# Import the FastAPI app
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from notion_api import app, fetch_children


@pytest.fixture
def client():
    """Create test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_notion_client():
    """Mock Notion client."""
    with patch('notion_api.notion') as mock:
        yield mock


class TestNotionAPI:
    """Test cases for the Notion API endpoints."""
    
    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "notion-api"}
    
    def test_fetch_children_with_depth_limit(self, mock_notion_client):
        """Test fetch_children respects depth limits."""
        # Mock blocks response
        mock_blocks = {
            "results": [
                {
                    "id": "block1",
                    "type": "paragraph",
                    "has_children": False
                },
                {
                    "id": "block2", 
                    "type": "toggle",
                    "has_children": True
                }
            ]
        }
        mock_notion_client.blocks.children.list.return_value = mock_blocks
        
        # Test depth limit enforcement
        result = fetch_children("test_id", max_depth=0)
        assert result == []
        
        # Test normal operation
        result = fetch_children("test_id", max_depth=2)
        assert len(result) == 2
        assert result[0]["id"] == "block1"
        assert result[1]["id"] == "block2"
    
    def test_fetch_children_handles_errors(self, mock_notion_client):
        """Test fetch_children handles API errors gracefully."""
        mock_notion_client.blocks.children.list.side_effect = Exception("API Error")
        
        result = fetch_children("test_id")
        assert result == []
    
    @patch.dict(os.environ, {"NOTION_RECIPES_DB_ID": "test_db_id"})
    def test_list_recipes_success(self, client, mock_notion_client):
        """Test successful recipe listing."""
        # Mock database query response
        mock_response = {
            "results": [
                {
                    "id": "recipe1",
                    "properties": {
                        "Name": {"type": "title", "title": [{"plain_text": "Test Recipe"}]},
                        "Ingredients": {"type": "rollup"},  # Should be filtered
                        "Instructions": {"type": "rich_text"}
                    }
                }
            ]
        }
        mock_notion_client.databases.query.return_value = mock_response
        
        response = client.get("/recipes")
        assert response.status_code == 200
        
        data = response.json()
        assert "recipes" in data
        assert len(data["recipes"]) == 1
        
        recipe = data["recipes"][0]
        assert recipe["id"] == "recipe1"
        # Check rollup properties are filtered
        assert "Ingredients" not in recipe["properties"]
        assert "Instructions" in recipe["properties"]
    
    @patch.dict(os.environ, {"NOTION_RECIPES_DB_ID": ""})
    def test_list_recipes_no_db_id(self, client, mock_notion_client):
        """Test recipe listing with missing database ID."""
        response = client.get("/recipes")
        assert response.status_code == 500
        assert "Database ID not set" in response.json()["detail"]
    
    def test_get_recipe_success(self, client, mock_notion_client):
        """Test successful recipe retrieval."""
        # Mock page retrieve
        mock_page = {
            "properties": {
                "Name": {"type": "title"},
                "Description": {"type": "rich_text"},
                "Rating": {"type": "rollup"}  # Should be filtered
            }
        }
        mock_notion_client.pages.retrieve.return_value = mock_page
        
        # Mock blocks for content
        mock_blocks = {"results": [{"id": "block1", "type": "paragraph", "has_children": False}]}
        mock_notion_client.blocks.children.list.return_value = mock_blocks
        
        response = client.get("/recipes/test_recipe_id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == "test_recipe_id"
        assert "properties" in data
        assert "content" in data
        # Check rollup filtered
        assert "Rating" not in data["properties"]
        assert "Name" in data["properties"]
    
    def test_get_recipe_not_found(self, client, mock_notion_client):
        """Test recipe retrieval with invalid ID."""
        mock_notion_client.pages.retrieve.side_effect = Exception("Not found")
        
        response = client.get("/recipes/invalid_id")
        assert response.status_code == 404
        assert "Recipe not found" in response.json()["detail"]
    
    def test_get_recipe_content_fetch_error(self, client, mock_notion_client):
        """Test recipe retrieval when content fetch fails."""
        # Mock successful page retrieve
        mock_page = {"properties": {"Name": {"type": "title"}}}
        mock_notion_client.pages.retrieve.return_value = mock_page
        
        # Mock blocks fetch failure
        mock_notion_client.blocks.children.list.side_effect = Exception("Content error")
        
        response = client.get("/recipes/test_id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["content"] == []  # Should return empty content on error


class TestNotionIntegration:
    """Integration tests for Notion functionality."""
    
    def test_recursive_depth_protection(self, mock_notion_client):
        """Test that recursive calls respect depth limits."""
        # Create deeply nested mock structure
        def mock_list_side_effect(block_id):
            return {
                "results": [
                    {
                        "id": f"child_{block_id}",
                        "type": "toggle",
                        "has_children": True
                    }
                ]
            }
        
        mock_notion_client.blocks.children.list.side_effect = mock_list_side_effect
        
        # Should not recurse beyond max_depth
        result = fetch_children("root", max_depth=2)
        
        # Verify limited recursion
        assert len(result) == 1
        assert "children" in result[0]
        # Should not have deeply nested children due to depth limit
        
    def test_block_type_filtering(self, mock_notion_client):
        """Test that only certain block types have children fetched."""
        mock_blocks = {
            "results": [
                {"id": "para", "type": "paragraph", "has_children": True},
                {"id": "toggle", "type": "toggle", "has_children": True},
                {"id": "table", "type": "table", "has_children": True}
            ]
        }
        mock_notion_client.blocks.children.list.return_value = mock_blocks
        
        result = fetch_children("test", max_depth=2)
        
        # Only toggle and table should have children fetched
        para_block = next(b for b in result if b["id"] == "para")
        toggle_block = next(b for b in result if b["id"] == "toggle") 
        table_block = next(b for b in result if b["id"] == "table")
        
        assert "children" not in para_block
        assert "children" in toggle_block
        assert "children" in table_block