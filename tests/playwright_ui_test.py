"""
Playwright E2E tests for Hey Chef v2 UI functionality.
Tests the complete user interface including WebSocket connections, health checks, and recipe features.
"""

import asyncio
import os
import sys
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from typing import List, Dict, Any
import json
import time

class HeyChefUITester:
    """Comprehensive UI tester for Hey Chef v2 application."""
    
    def __init__(self):
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None
        self.frontend_url = "http://localhost:3001"
        self.backend_url = "http://localhost:8000"
        self.test_results = []
        
    async def setup(self):
        """Set up Playwright browser and page."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False, slow_mo=1000)
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        self.page = await self.context.new_page()
        
        # Set up console logging
        self.page.on("console", lambda msg: print(f"Console: {msg.text}"))
        self.page.on("pageerror", lambda err: print(f"Page Error: {err}"))
        
    async def teardown(self):
        """Clean up browser resources."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
            
    async def wait_for_element(self, selector: str, timeout: int = 10000):
        """Wait for element to be visible with timeout."""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            print(f"Element not found: {selector} - {e}")
            return False
            
    async def test_initial_page_load(self) -> Dict[str, Any]:
        """Test that the initial page loads correctly."""
        test_name = "Initial Page Load"
        print(f"\n🧪 Testing: {test_name}")
        
        try:
            # Navigate to the app
            await self.page.goto(self.frontend_url)
            
            # Wait for the app to load
            await self.page.wait_for_load_state('networkidle')
            
            # Check for main elements
            title_found = await self.wait_for_element('h1:has-text("Hey Chef")')
            nav_found = await self.wait_for_element('nav')
            
            # Check for tab navigation
            chat_tab = await self.wait_for_element('button:has-text("Chat")')
            recipe_tab = await self.wait_for_element('button:has-text("Recipe")')
            settings_tab = await self.wait_for_element('button:has-text("Settings")')
            
            success = all([title_found, nav_found, chat_tab, recipe_tab, settings_tab])
            
            result = {
                "test": test_name,
                "success": success,
                "details": {
                    "title_found": title_found,
                    "nav_found": nav_found,
                    "chat_tab": chat_tab,
                    "recipe_tab": recipe_tab,
                    "settings_tab": settings_tab
                },
                "error": None if success else "Missing essential UI elements"
            }
            
            print(f"✅ {test_name}: {'PASSED' if success else 'FAILED'}")
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
    
    async def test_websocket_connection_status(self) -> Dict[str, Any]:
        """Test WebSocket connection status indicator."""
        test_name = "WebSocket Connection Status"
        print(f"\n🧪 Testing: {test_name}")
        
        try:
            # Wait for connection indicator
            connection_indicator = await self.wait_for_element('[class*="text-green-600"], [class*="text-red-600"]')
            
            if connection_indicator:
                # Check if it shows connected or disconnected
                connected_element = await self.page.query_selector('text=Connected')
                disconnected_element = await self.page.query_selector('text=Disconnected')
                
                has_status = connected_element is not None or disconnected_element is not None
                is_connected = connected_element is not None
                
                result = {
                    "test": test_name,
                    "success": has_status,
                    "details": {
                        "connection_indicator_found": True,
                        "has_status": has_status,
                        "is_connected": is_connected,
                        "status": "Connected" if is_connected else "Disconnected" if disconnected_element else "Unknown"
                    },
                    "error": None if has_status else "Connection status not displayed"
                }
            else:
                result = {
                    "test": test_name,
                    "success": False,
                    "details": {"connection_indicator_found": False},
                    "error": "Connection status indicator not found"
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
    
    async def test_settings_health_checks(self) -> Dict[str, Any]:
        """Test settings panel health check functionality."""
        test_name = "Settings Health Checks"
        print(f"\n🧪 Testing: {test_name}")
        
        try:
            # Navigate to settings tab
            settings_tab = await self.page.query_selector('button:has-text("Settings")')
            if settings_tab:
                await settings_tab.click()
                await self.page.wait_for_timeout(1000)
            
            # Wait for settings panel to load
            settings_panel = await self.wait_for_element('h2:has-text("Settings")', timeout=5000)
            
            if not settings_panel:
                return {
                    "test": test_name,
                    "success": False,
                    "details": {},
                    "error": "Settings panel not found"
                }
            
            # Look for system information section
            system_info = await self.wait_for_element('h3:has-text("System Information")', timeout=5000)
            
            # Check for health check elements
            connection_status = await self.wait_for_element('text=Connection Status', timeout=3000)
            api_key_status = await self.wait_for_element('text=OpenAI API Key', timeout=3000)
            audio_services = await self.wait_for_element('text=Audio Services', timeout=3000)
            
            # Look for status indicators (Valid, Invalid, Checking...)
            valid_indicators = await self.page.query_selector_all('text=Valid')
            invalid_indicators = await self.page.query_selector_all('text=Invalid')
            checking_indicators = await self.page.query_selector_all('text=Checking...')
            healthy_indicators = await self.page.query_selector_all('text=Healthy')
            
            has_health_checks = connection_status and api_key_status and audio_services
            has_status_indicators = len(valid_indicators) > 0 or len(invalid_indicators) > 0 or len(healthy_indicators) > 0
            
            result = {
                "test": test_name,
                "success": has_health_checks and has_status_indicators,
                "details": {
                    "system_info_found": system_info is not None,
                    "connection_status_found": connection_status is not None,
                    "api_key_status_found": api_key_status is not None,
                    "audio_services_found": audio_services is not None,
                    "valid_indicators": len(valid_indicators),
                    "invalid_indicators": len(invalid_indicators),
                    "checking_indicators": len(checking_indicators),
                    "healthy_indicators": len(healthy_indicators),
                    "has_status_indicators": has_status_indicators
                },
                "error": None if (has_health_checks and has_status_indicators) else "Health checks not properly implemented"
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
    
    async def test_recipe_list_functionality(self) -> Dict[str, Any]:
        """Test recipe list and navigation functionality."""
        test_name = "Recipe List Functionality"
        print(f"\n🧪 Testing: {test_name}")
        
        try:
            # Navigate to recipe tab
            recipe_tab = await self.page.query_selector('button:has-text("Recipe")')
            if recipe_tab:
                await recipe_tab.click()
                await self.page.wait_for_timeout(2000)
            
            # Wait for recipe content to load
            recipe_section = await self.wait_for_element('h2:has-text("Recipes")', timeout=10000)
            
            if not recipe_section:
                # Check if we're in recipe detail view
                back_button = await self.page.query_selector('text=Back to Recipes')
                if back_button:
                    await back_button.click()
                    await self.page.wait_for_timeout(1000)
                    recipe_section = await self.wait_for_element('h2:has-text("Recipes")', timeout=5000)
            
            # Look for recipe list elements
            search_box = await self.wait_for_element('input[placeholder*="Search recipes"]', timeout=5000)
            category_filter = await self.wait_for_element('button:has-text("All Categories")', timeout=5000)
            
            # Wait for recipes to load
            await self.page.wait_for_timeout(3000)
            
            # Check for recipe items
            recipe_items = await self.page.query_selector_all('[class*="border"][class*="rounded-lg"][class*="cursor-pointer"]')
            
            # Check for loading state
            loading_spinner = await self.page.query_selector('[class*="animate-spin"]')
            loading_text = await self.page.query_selector('text=Loading recipes...')
            
            # Check for error state
            error_text = await self.page.query_selector('text=Failed to load recipes')
            no_recipes_text = await self.page.query_selector('text=No recipes found')
            
            has_recipe_elements = search_box and category_filter
            has_recipes = len(recipe_items) > 0
            is_loading = loading_spinner is not None or loading_text is not None
            has_error = error_text is not None
            
            result = {
                "test": test_name,
                "success": recipe_section is not None and has_recipe_elements,
                "details": {
                    "recipe_section_found": recipe_section is not None,
                    "search_box_found": search_box is not None,
                    "category_filter_found": category_filter is not None,
                    "recipe_count": len(recipe_items),
                    "has_recipes": has_recipes,
                    "is_loading": is_loading,
                    "has_error": has_error,
                    "no_recipes": no_recipes_text is not None
                },
                "error": None if (recipe_section and has_recipe_elements) else "Recipe list not properly loaded"
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
    
    async def test_recipe_selection_and_detail_view(self) -> Dict[str, Any]:
        """Test recipe selection and detail view functionality."""
        test_name = "Recipe Selection and Detail View"
        print(f"\n🧪 Testing: {test_name}")
        
        try:
            # Ensure we're in the recipe tab
            recipe_tab = await self.page.query_selector('button:has-text("Recipe")')
            if recipe_tab:
                await recipe_tab.click()
                await self.page.wait_for_timeout(2000)
            
            # Wait for recipe list
            await self.page.wait_for_timeout(3000)
            
            # Find and click on a recipe
            recipe_items = await self.page.query_selector_all('[class*="border"][class*="rounded-lg"][class*="cursor-pointer"]')
            
            if len(recipe_items) == 0:
                return {
                    "test": test_name,
                    "success": False,
                    "details": {"recipe_items_found": 0},
                    "error": "No recipe items found to test"
                }
            
            # Click on the first recipe
            first_recipe = recipe_items[0]
            recipe_title_element = await first_recipe.query_selector('h3')
            recipe_title = await recipe_title_element.inner_text() if recipe_title_element else "Unknown Recipe"
            
            await first_recipe.click()
            await self.page.wait_for_timeout(2000)
            
            # Check if we're now in detail view
            back_to_recipes_button = await self.wait_for_element('text=Back to Recipes', timeout=5000)
            
            # Look for recipe detail elements
            recipe_ingredients = await self.page.query_selector('h3:has-text("Ingredients"), h4:has-text("Ingredients")')
            recipe_instructions = await self.page.query_selector('h3:has-text("Instructions"), h4:has-text("Instructions"), h3:has-text("Steps")')
            
            # Check for recipe meta information
            cooking_time = await self.page.query_selector('[class*="Clock"]')
            if not cooking_time:
                cooking_time = await self.page.query_selector('text=/\\d+\\s*(min|hour|minute)/')
            servings = await self.page.query_selector('text=/\\d+\\s*serving/')
            
            # Test back navigation
            back_navigation_works = False
            if back_to_recipes_button:
                await back_to_recipes_button.click()
                await self.page.wait_for_timeout(1000)
                recipe_list_header = await self.page.query_selector('h2:has-text("Recipes")')
                back_navigation_works = recipe_list_header is not None
            
            result = {
                "test": test_name,
                "success": back_to_recipes_button is not None and back_navigation_works,
                "details": {
                    "recipe_selected": recipe_title,
                    "back_button_found": back_to_recipes_button is not None,
                    "ingredients_section_found": recipe_ingredients is not None,
                    "instructions_section_found": recipe_instructions is not None,
                    "cooking_time_found": cooking_time is not None,
                    "servings_found": servings is not None,
                    "back_navigation_works": back_navigation_works
                },
                "error": None if (back_to_recipes_button and back_navigation_works) else "Recipe detail view or navigation not working"
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
        """Run all UI tests and return results."""
        print("🚀 Starting Hey Chef v2 UI Test Suite")
        print("=" * 50)
        
        await self.setup()
        
        try:
            # Run all tests
            test_functions = [
                self.test_initial_page_load,
                self.test_websocket_connection_status,
                self.test_settings_health_checks,
                self.test_recipe_list_functionality,
                self.test_recipe_selection_and_detail_view
            ]
            
            for test_func in test_functions:
                result = await test_func()
                self.test_results.append(result)
                
                # Add delay between tests
                await self.page.wait_for_timeout(1000)
            
        finally:
            await self.teardown()
        
        return self.test_results
    
    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 50)
        print("🧪 TEST SUMMARY")
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
    tester = HeyChefUITester()
    
    try:
        results = await tester.run_all_tests()
        success = tester.print_summary()
        
        # Save results to file
        with open('ui_test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nTest results saved to: ui_test_results.json")
        
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