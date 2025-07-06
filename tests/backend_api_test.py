"""
Backend API test suite for Hey Chef v2.
Tests all API endpoints for functionality, error handling, and response formats.
"""

import asyncio
import aiohttp
import json
import sys
import time
from typing import Dict, Any, List
from pathlib import Path

class BackendAPITester:
    """Comprehensive API tester for Hey Chef v2 backend."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
        
    async def setup(self):
        """Set up HTTP session."""
        self.session = aiohttp.ClientSession()
        
    async def teardown(self):
        """Clean up HTTP session."""
        if self.session:
            await self.session.close()
            
    async def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request and return response data."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                content_type = response.headers.get('content-type', '')
                
                if 'application/json' in content_type:
                    data = await response.json()
                else:
                    data = await response.text()
                
                return {
                    "status": response.status,
                    "headers": dict(response.headers),
                    "data": data,
                    "success": 200 <= response.status < 300
                }
        except Exception as e:
            return {
                "status": None,
                "headers": {},
                "data": None,
                "success": False,
                "error": str(e)
            }
    
    async def test_health_endpoint(self) -> Dict[str, Any]:
        """Test main health check endpoint."""
        test_name = "Health Endpoint"
        print(f"\n🧪 Testing: {test_name}")
        
        try:
            response = await self.make_request("GET", "/health")
            
            expected_fields = ["status", "service", "version", "environment"]
            has_expected_fields = all(field in response["data"] for field in expected_fields) if response["data"] else False
            
            result = {
                "test": test_name,
                "success": response["success"] and has_expected_fields,
                "details": {
                    "status_code": response["status"],
                    "response_data": response["data"],
                    "has_expected_fields": has_expected_fields,
                    "expected_fields": expected_fields
                },
                "error": response.get("error") if not response["success"] else None
            }
            
            print(f"✅ {test_name}: {'PASSED' if result['success'] else 'FAILED'}")
            return result
            
        except Exception as e:
            result = {
                "test": test_name,
                "success": False,
                "details": {},
                "error": str(e)
            }
            print(f"❌ {test_name}: FAILED - {e}")
            return result
    
    async def test_detailed_health_endpoint(self) -> Dict[str, Any]:
        """Test detailed health check endpoint."""
        test_name = "Detailed Health Endpoint"
        print(f"\n🧪 Testing: {test_name}")
        
        try:
            response = await self.make_request("GET", "/health/detailed")
            
            if response["success"] and response["data"]:
                data = response["data"]
                has_services = "services" in data
                has_configuration = "configuration" in data
                
                result = {
                    "test": test_name,
                    "success": response["success"] and has_services and has_configuration,
                    "details": {
                        "status_code": response["status"],
                        "has_services": has_services,
                        "has_configuration": has_configuration,
                        "services": data.get("services", {}),
                        "configuration": data.get("configuration", {})
                    },
                    "error": None
                }
            else:
                result = {
                    "test": test_name,
                    "success": False,
                    "details": {
                        "status_code": response["status"],
                        "response_data": response["data"]
                    },
                    "error": response.get("error", "Invalid response format")
                }
            
            print(f"✅ {test_name}: {'PASSED' if result['success'] else 'FAILED'}")
            return result
            
        except Exception as e:
            result = {
                "test": test_name,
                "success": False,
                "details": {},
                "error": str(e)
            }
            print(f"❌ {test_name}: FAILED - {e}")
            return result
    
    async def test_audio_health_endpoint(self) -> Dict[str, Any]:
        """Test audio service health check."""
        test_name = "Audio Health Endpoint"
        print(f"\n🧪 Testing: {test_name}")
        
        try:
            response = await self.make_request("GET", "/api/audio/health")
            
            if response["success"] and response["data"]:
                data = response["data"]
                has_status = "status" in data
                has_services = "services" in data
                has_configuration = "configuration" in data
                
                result = {
                    "test": test_name,
                    "success": response["success"] and has_status and has_services,
                    "details": {
                        "status_code": response["status"],
                        "overall_status": data.get("status"),
                        "services": data.get("services", {}),
                        "configuration": data.get("configuration", {}),
                        "has_required_fields": has_status and has_services
                    },
                    "error": None
                }
            else:
                result = {
                    "test": test_name,
                    "success": False,
                    "details": {
                        "status_code": response["status"],
                        "response_data": response["data"]
                    },
                    "error": response.get("error", "Invalid response format")
                }
            
            print(f"✅ {test_name}: {'PASSED' if result['success'] else 'FAILED'}")
            return result
            
        except Exception as e:
            result = {
                "test": test_name,
                "success": False,
                "details": {},
                "error": str(e)
            }
            print(f"❌ {test_name}: FAILED - {e}")
            return result
    
    async def test_api_key_validation(self) -> Dict[str, Any]:
        """Test API key validation endpoint."""
        test_name = "API Key Validation"
        print(f"\n🧪 Testing: {test_name}")
        
        try:
            response = await self.make_request("POST", "/api/audio/validate-api-keys")
            
            if response["success"] and response["data"]:
                data = response["data"]
                has_openai_valid = "openai_valid" in data
                has_picovoice_valid = "picovoice_valid" in data
                has_status = "status" in data
                
                result = {
                    "test": test_name,
                    "success": response["success"] and has_openai_valid and has_status,
                    "details": {
                        "status_code": response["status"],
                        "openai_valid": data.get("openai_valid"),
                        "picovoice_valid": data.get("picovoice_valid"),
                        "status": data.get("status"),
                        "message": data.get("message"),
                        "api_keys": data.get("api_keys", {}),
                        "has_required_fields": has_openai_valid and has_status
                    },
                    "error": None
                }
            else:
                result = {
                    "test": test_name,
                    "success": False,
                    "details": {
                        "status_code": response["status"],
                        "response_data": response["data"]
                    },
                    "error": response.get("error", "Invalid response format")
                }
            
            print(f"✅ {test_name}: {'PASSED' if result['success'] else 'FAILED'}")
            return result
            
        except Exception as e:
            result = {
                "test": test_name,
                "success": False,
                "details": {},
                "error": str(e)
            }
            print(f"❌ {test_name}: FAILED - {e}")
            return result
    
    async def test_websocket_health(self) -> Dict[str, Any]:
        """Test WebSocket health endpoint."""
        test_name = "WebSocket Health"
        print(f"\n🧪 Testing: {test_name}")
        
        try:
            response = await self.make_request("GET", "/ws/health")
            
            if response["success"] and response["data"]:
                data = response["data"]
                has_status = "status" in data
                has_connections = "active_connections" in data
                has_sessions = "total_sessions" in data
                
                result = {
                    "test": test_name,
                    "success": response["success"] and has_status,
                    "details": {
                        "status_code": response["status"],
                        "status": data.get("status"),
                        "active_connections": data.get("active_connections"),
                        "total_sessions": data.get("total_sessions"),
                        "has_required_fields": has_status and has_connections
                    },
                    "error": None
                }
            else:
                result = {
                    "test": test_name,
                    "success": False,
                    "details": {
                        "status_code": response["status"],
                        "response_data": response["data"]
                    },
                    "error": response.get("error", "Invalid response format")
                }
            
            print(f"✅ {test_name}: {'PASSED' if result['success'] else 'FAILED'}")
            return result
            
        except Exception as e:
            result = {
                "test": test_name,
                "success": False,
                "details": {},
                "error": str(e)
            }
            print(f"❌ {test_name}: FAILED - {e}")
            return result
    
    async def test_recipe_endpoints(self) -> Dict[str, Any]:
        """Test recipe API endpoints."""
        test_name = "Recipe Endpoints"
        print(f"\n🧪 Testing: {test_name}")
        
        try:
            # Test recipe list endpoint
            list_response = await self.make_request("GET", "/api/recipes")
            
            # Test recipe categories endpoint
            categories_response = await self.make_request("GET", "/api/recipes/categories/list")
            
            # Test recipe health endpoint
            health_response = await self.make_request("GET", "/api/recipes/health")
            
            list_success = list_response["success"]
            categories_success = categories_response["success"]
            health_success = health_response["success"]
            
            # Check response formats
            list_has_recipes = False
            if list_success and list_response["data"]:
                list_data = list_response["data"]
                list_has_recipes = "recipes" in list_data
            
            categories_has_list = False
            if categories_success and categories_response["data"]:
                categories_data = categories_response["data"]
                categories_has_list = "categories" in categories_data
            
            overall_success = list_success and categories_success and health_success
            
            result = {
                "test": test_name,
                "success": overall_success,
                "details": {
                    "recipes_list": {
                        "success": list_success,
                        "status_code": list_response["status"],
                        "has_recipes": list_has_recipes,
                        "data": list_response["data"] if list_success else None
                    },
                    "categories_list": {
                        "success": categories_success,
                        "status_code": categories_response["status"],
                        "has_categories": categories_has_list,
                        "data": categories_response["data"] if categories_success else None
                    },
                    "health_check": {
                        "success": health_success,
                        "status_code": health_response["status"],
                        "data": health_response["data"] if health_success else None
                    }
                },
                "error": None if overall_success else "One or more recipe endpoints failed"
            }
            
            print(f"✅ {test_name}: {'PASSED' if result['success'] else 'FAILED'}")
            return result
            
        except Exception as e:
            result = {
                "test": test_name,
                "success": False,
                "details": {},
                "error": str(e)
            }
            print(f"❌ {test_name}: FAILED - {e}")
            return result
    
    async def test_audio_models_endpoint(self) -> Dict[str, Any]:
        """Test audio models information endpoint."""
        test_name = "Audio Models Endpoint"
        print(f"\n🧪 Testing: {test_name}")
        
        try:
            response = await self.make_request("GET", "/api/audio/models")
            
            if response["success"] and response["data"]:
                data = response["data"]
                has_whisper_models = "whisper_models" in data
                has_tts_voices = "tts_voices" in data
                has_llm_models = "llm_models" in data
                has_chef_modes = "chef_modes" in data
                
                result = {
                    "test": test_name,
                    "success": response["success"] and has_whisper_models and has_chef_modes,
                    "details": {
                        "status_code": response["status"],
                        "whisper_models": data.get("whisper_models", []),
                        "tts_voices": data.get("tts_voices", {}),
                        "llm_models": data.get("llm_models", []),
                        "chef_modes": data.get("chef_modes", []),
                        "has_required_fields": has_whisper_models and has_chef_modes
                    },
                    "error": None
                }
            else:
                result = {
                    "test": test_name,
                    "success": False,
                    "details": {
                        "status_code": response["status"],
                        "response_data": response["data"]
                    },
                    "error": response.get("error", "Invalid response format")
                }
            
            print(f"✅ {test_name}: {'PASSED' if result['success'] else 'FAILED'}")
            return result
            
        except Exception as e:
            result = {
                "test": test_name,
                "success": False,
                "details": {},
                "error": str(e)
            }
            print(f"❌ {test_name}: FAILED - {e}")
            return result
    
    async def test_cors_headers(self) -> Dict[str, Any]:
        """Test CORS headers are properly set."""
        test_name = "CORS Headers"
        print(f"\n🧪 Testing: {test_name}")
        
        try:
            # Test preflight request
            preflight_response = await self.make_request(
                "OPTIONS", 
                "/health",
                headers={
                    "Origin": "http://localhost:3001",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Content-Type"
                }
            )
            
            # Test regular request with Origin header
            regular_response = await self.make_request(
                "GET", 
                "/health",
                headers={"Origin": "http://localhost:3001"}
            )
            
            preflight_headers = preflight_response["headers"]
            regular_headers = regular_response["headers"]
            
            has_access_control_origin = "access-control-allow-origin" in regular_headers
            has_access_control_methods = "access-control-allow-methods" in preflight_headers
            has_access_control_headers = "access-control-allow-headers" in preflight_headers
            
            result = {
                "test": test_name,
                "success": has_access_control_origin,
                "details": {
                    "preflight_status": preflight_response["status"],
                    "regular_status": regular_response["status"],
                    "access_control_origin": regular_headers.get("access-control-allow-origin"),
                    "access_control_methods": preflight_headers.get("access-control-allow-methods"),
                    "access_control_headers": preflight_headers.get("access-control-allow-headers"),
                    "has_cors_headers": has_access_control_origin
                },
                "error": None if has_access_control_origin else "CORS headers not properly configured"
            }
            
            print(f"✅ {test_name}: {'PASSED' if result['success'] else 'FAILED'}")
            return result
            
        except Exception as e:
            result = {
                "test": test_name,
                "success": False,
                "details": {},
                "error": str(e)
            }
            print(f"❌ {test_name}: FAILED - {e}")
            return result
    
    async def run_all_tests(self) -> List[Dict[str, Any]]:
        """Run all backend API tests."""
        print("🚀 Starting Hey Chef v2 Backend API Test Suite")
        print("=" * 50)
        
        await self.setup()
        
        try:
            # Run all tests
            test_functions = [
                self.test_health_endpoint,
                self.test_detailed_health_endpoint,
                self.test_audio_health_endpoint,
                self.test_api_key_validation,
                self.test_websocket_health,
                self.test_recipe_endpoints,
                self.test_audio_models_endpoint,
                self.test_cors_headers
            ]
            
            for test_func in test_functions:
                result = await test_func()
                self.test_results.append(result)
                
                # Add delay between tests
                await asyncio.sleep(0.5)
            
        finally:
            await self.teardown()
        
        return self.test_results
    
    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 50)
        print("🧪 BACKEND API TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            print(f"  {status}: {result['test']}")
            if not result['success'] and result['error']:
                print(f"    Error: {result['error']}")
        
        return passed == total

async def main():
    """Main test runner."""
    tester = BackendAPITester()
    
    try:
        results = await tester.run_all_tests()
        success = tester.print_summary()
        
        # Save results to file
        with open('backend_test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nTest results saved to: backend_test_results.json")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"\nTest suite failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)