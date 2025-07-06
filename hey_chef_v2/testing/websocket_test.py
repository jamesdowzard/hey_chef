#!/usr/bin/env python3
"""
Direct WebSocket Connection Test
"""

import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/audio"
    
    try:
        print(f"Attempting to connect to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Wait for welcome message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📨 Received welcome message: {message}")
            except asyncio.TimeoutError:
                print("⚠️  No welcome message received within 5 seconds")
            
            # Send a test message
            test_message = {
                "type": "test",
                "data": {"message": "Hello from test client"},
                "timestamp": "2025-07-04T06:50:00Z"
            }
            
            await websocket.send(json.dumps(test_message))
            print(f"📤 Sent test message: {test_message}")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📨 Received response: {response}")
            except asyncio.TimeoutError:
                print("⚠️  No response received within 5 seconds")
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ WebSocket connection closed: {e}")
    except websockets.exceptions.InvalidURI as e:
        print(f"❌ Invalid WebSocket URI: {e}")
    except OSError as e:
        print(f"❌ Connection failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())