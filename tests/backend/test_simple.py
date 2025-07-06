"""
Simple test to verify test environment is working.
"""

import pytest
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def test_python_path():
    """Test that Python path is set up correctly."""
    assert str(backend_path) in sys.path

def test_basic_imports():
    """Test that we can import basic Python modules."""
    import json
    import asyncio
    assert json is not None
    assert asyncio is not None

def test_fastapi_import():
    """Test that FastAPI can be imported."""
    try:
        from fastapi import FastAPI
        assert FastAPI is not None
    except ImportError as e:
        pytest.skip(f"FastAPI not available: {e}")

def test_pydantic_import():
    """Test that Pydantic can be imported."""
    try:
        from pydantic import BaseModel
        assert BaseModel is not None
    except ImportError as e:
        pytest.skip(f"Pydantic not available: {e}")

@pytest.mark.asyncio
async def test_async_functionality():
    """Test that async functionality works."""
    async def async_function():
        return "test"
    
    result = await async_function()
    assert result == "test"