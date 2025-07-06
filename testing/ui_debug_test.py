#!/usr/bin/env python3
"""
UI Debug Test using Playwright
Diagnoses and fixes UI connection issues in Hey Chef v2
"""

import asyncio
import json
from playwright.async_api import async_playwright
import httpx
from typing import Dict, List, Any

class UIDebugger:
    """Debug Hey Chef v2 UI issues using Playwright."""
    
    def __init__(self, frontend_url: str = "http://localhost:3000", 
                 backend_url: str = "http://localhost:8000"):
        self.frontend_url = frontend_url
        self.backend_url = backend_url
        self.issues_found = []
        self.fixes_applied = []
    
    async def run_full_debug(self):
        """Run comprehensive UI debugging."""
        print("🔍 Starting Hey Chef v2 UI Debug Session...")
        
        # Test backend connectivity first
        await self._test_backend_connectivity()
        
        # Test frontend with Playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=1000)
            context = await browser.new_context()
            
            # Enable console logging
            page = await context.new_page()
            
            # Listen for console messages
            page.on("console", self._handle_console_message)
            
            # Listen for network requests
            page.on("request", self._handle_request)
            page.on("response", self._handle_response)
            
            try:
                await self._test_page_load(page)
                await self._test_websocket_connection(page)
                await self._test_api_calls(page)
                await self._test_system_checks(page)
                await self._test_recipe_loading(page)
                
                # Generate report
                await self._generate_debug_report(page)
                
            except Exception as e:
                print(f"❌ Debug session failed: {e}")
                self.issues_found.append(f"Debug session error: {e}")
            
            finally:
                await browser.close()
    
    async def _test_backend_connectivity(self):
        """Test if backend services are accessible."""
        print("🔌 Testing backend connectivity...")
        
        services = [
            ("Backend Health", f"{self.backend_url}/health"),
            ("Recipe API", f"{self.backend_url}/api/recipes/health"),
            ("Categories API", f"{self.backend_url}/api/recipes/categories/list")
        ]
        
        async with httpx.AsyncClient() as client:
            for service_name, url in services:
                try:
                    response = await client.get(url, timeout=5.0)
                    if response.status_code == 200:
                        print(f"  ✅ {service_name}: OK")
                    else:
                        print(f"  ❌ {service_name}: HTTP {response.status_code}")
                        self.issues_found.append(f"{service_name} returned {response.status_code}")
                except Exception as e:
                    print(f"  ❌ {service_name}: {e}")
                    self.issues_found.append(f"{service_name} connection failed: {e}")
    
    async def _test_page_load(self, page):
        """Test if the frontend loads correctly."""
        print("🌐 Testing page load...")
        
        try:
            response = await page.goto(self.frontend_url)
            
            if response.status >= 400:
                self.issues_found.append(f"Page load failed with status {response.status}")
                return
            
            # Wait for React app to load
            await page.wait_for_selector('[data-testid="app-container"], .App, #root', timeout=10000)
            print("  ✅ React app loaded successfully")
            
            # Check for error messages
            error_elements = await page.query_selector_all('.error, .alert-error, [class*="error"]')
            if error_elements:
                print("  ⚠️  Found error elements on page")
                for element in error_elements:
                    text = await element.text_content()
                    self.issues_found.append(f"Page error: {text}")
            
        except Exception as e:
            print(f"  ❌ Page load failed: {e}")
            self.issues_found.append(f"Page load error: {e}")
    
    async def _test_websocket_connection(self, page):
        """Test WebSocket connection status."""
        print("🔌 Testing WebSocket connection...")
        
        try:
            # Look for connection status indicators
            connection_status = await page.query_selector_all('[class*="connection"], [class*="status"]')
            
            for element in connection_status:
                text = await element.text_content()
                if "disconnected" in text.lower():
                    print(f"  ❌ Found disconnection indicator: {text}")
                    self.issues_found.append(f"WebSocket disconnected: {text}")
                elif "connected" in text.lower():
                    print(f"  ✅ Found connection indicator: {text}")
            
            # Check for WebSocket errors in console
            await page.evaluate("""
                window.wsErrors = [];
                const originalWebSocket = window.WebSocket;
                window.WebSocket = function(url) {
                    const ws = new originalWebSocket(url);
                    ws.addEventListener('error', (e) => {
                        window.wsErrors.push({type: 'error', message: e.message, url});
                    });
                    ws.addEventListener('close', (e) => {
                        if (e.code !== 1000) {
                            window.wsErrors.push({type: 'close', code: e.code, reason: e.reason, url});
                        }
                    });
                    return ws;
                };
            """)
            
            # Wait a bit for connections to be attempted
            await page.wait_for_timeout(3000)
            
            # Check for WebSocket errors
            ws_errors = await page.evaluate("window.wsErrors || []")
            for error in ws_errors:
                print(f"  ❌ WebSocket error: {error}")
                self.issues_found.append(f"WebSocket error: {error}")
        
        except Exception as e:
            print(f"  ❌ WebSocket test failed: {e}")
            self.issues_found.append(f"WebSocket test error: {e}")
    
    async def _test_api_calls(self, page):
        """Test API call functionality."""
        print("📡 Testing API calls...")
        
        try:
            # Monitor network requests
            network_errors = []
            
            def handle_response(response):
                if response.status >= 400:
                    network_errors.append({
                        'url': response.url,
                        'status': response.status,
                        'method': response.request.method
                    })
            
            page.on("response", handle_response)
            
            # Trigger a refresh to force API calls
            await page.reload()
            await page.wait_for_timeout(5000)
            
            # Check for network errors
            for error in network_errors:
                print(f"  ❌ API error: {error['method']} {error['url']} -> {error['status']}")
                self.issues_found.append(f"API error: {error['method']} {error['url']} returned {error['status']}")
            
            if not network_errors:
                print("  ✅ No API errors detected")
        
        except Exception as e:
            print(f"  ❌ API test failed: {e}")
            self.issues_found.append(f"API test error: {e}")
    
    async def _test_system_checks(self, page):
        """Test system status checks."""
        print("🔧 Testing system checks...")
        
        try:
            # Look for system status indicators
            await page.wait_for_timeout(2000)  # Wait for checks to complete
            
            # Check for "Checking..." states that never resolve
            checking_elements = await page.query_selector_all(':text("Checking...")')
            if checking_elements:
                print(f"  ⚠️  Found {len(checking_elements)} elements stuck in 'Checking...' state")
                for element in checking_elements:
                    parent = await element.evaluate_handle("el => el.closest('[class*=\"status\"], [class*=\"check\"], .system-info')")
                    if parent:
                        context = await parent.text_content()
                        self.issues_found.append(f"System check stuck: {context}")
            
            # Look for any status indicators
            status_elements = await page.query_selector_all('[class*="status"], .system-info')
            for element in status_elements:
                text = await element.text_content()
                if "checking" in text.lower() and "..." in text:
                    print(f"  ❌ Stuck system check: {text}")
                    self.issues_found.append(f"Stuck system check: {text}")
        
        except Exception as e:
            print(f"  ❌ System checks test failed: {e}")
            self.issues_found.append(f"System checks test error: {e}")
    
    async def _test_recipe_loading(self, page):
        """Test recipe loading functionality."""
        print("🍳 Testing recipe loading...")
        
        try:
            # Look for recipe-related elements
            recipe_elements = await page.query_selector_all('[class*="recipe"], [class*="Recipe"]')
            
            if not recipe_elements:
                print("  ⚠️  No recipe elements found")
                self.issues_found.append("No recipe elements found on page")
            else:
                print(f"  ✅ Found {len(recipe_elements)} recipe-related elements")
            
            # Check for loading states
            loading_elements = await page.query_selector_all(':text("Loading..."), [class*="loading"], [class*="spinner"]')
            if loading_elements:
                print(f"  ⚠️  Found {len(loading_elements)} elements in loading state")
                # Wait to see if they resolve
                await page.wait_for_timeout(5000)
                
                # Check again
                loading_elements = await page.query_selector_all(':text("Loading..."), [class*="loading"], [class*="spinner"]')
                if loading_elements:
                    print(f"  ❌ {len(loading_elements)} elements still stuck in loading state")
                    self.issues_found.append(f"{len(loading_elements)} elements stuck in loading state")
        
        except Exception as e:
            print(f"  ❌ Recipe loading test failed: {e}")
            self.issues_found.append(f"Recipe loading test error: {e}")
    
    def _handle_console_message(self, msg):
        """Handle console messages from the browser."""
        if msg.type in ['error', 'warning']:
            print(f"  🚨 Console {msg.type}: {msg.text}")
            self.issues_found.append(f"Console {msg.type}: {msg.text}")
    
    def _handle_request(self, request):
        """Handle network requests."""
        if request.url.startswith('ws://') or request.url.startswith('wss://'):
            print(f"  🔌 WebSocket request: {request.url}")
    
    def _handle_response(self, response):
        """Handle network responses."""
        if response.status >= 400:
            print(f"  ❌ Failed request: {response.request.method} {response.url} -> {response.status}")
    
    async def _generate_debug_report(self, page):
        """Generate comprehensive debug report."""
        print("\n" + "="*60)
        print("🔍 UI DEBUG REPORT")
        print("="*60)
        
        # Take screenshot for visual reference
        await page.screenshot(path="/Users/jamesdowzard/Documents/code/gh/hey_chef/hey_chef_v2/testing/debug_screenshot.png")
        print("📸 Screenshot saved: testing/debug_screenshot.png")
        
        # Summary
        print(f"\n📊 Summary:")
        print(f"  • Issues Found: {len(self.issues_found)}")
        print(f"  • Frontend URL: {self.frontend_url}")
        print(f"  • Backend URL: {self.backend_url}")
        
        # Issues
        if self.issues_found:
            print(f"\n❌ Issues Detected:")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"  {i}. {issue}")
            
            # Suggest fixes
            print(f"\n💡 Suggested Fixes:")
            await self._suggest_fixes()
        else:
            print(f"\n✅ No issues detected!")
        
        # Save detailed report
        report_data = {
            "timestamp": "2025-07-04",
            "frontend_url": self.frontend_url,
            "backend_url": self.backend_url,
            "issues_found": self.issues_found,
            "suggested_fixes": getattr(self, 'suggested_fixes', [])
        }
        
        with open("/Users/jamesdowzard/Documents/code/gh/hey_chef/hey_chef_v2/testing/ui_debug_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved: testing/ui_debug_report.json")
    
    async def _suggest_fixes(self):
        """Suggest fixes based on detected issues."""
        self.suggested_fixes = []
        
        # Analyze issues and suggest fixes
        websocket_issues = [issue for issue in self.issues_found if 'websocket' in issue.lower() or 'connection' in issue.lower()]
        api_issues = [issue for issue in self.issues_found if 'api' in issue.lower() or 'http' in issue.lower()]
        loading_issues = [issue for issue in self.issues_found if 'loading' in issue.lower() or 'checking' in issue.lower()]
        
        if websocket_issues:
            fix = "Fix WebSocket connection issues:\n"
            fix += "  - Check if backend WebSocket endpoint is correct (/ws/audio)\n"
            fix += "  - Verify CORS settings allow WebSocket connections\n"
            fix += "  - Check for WebSocket URL construction in frontend code\n"
            fix += "  - Ensure WebSocket server is properly handling connections"
            self.suggested_fixes.append(fix)
            print(f"  1. {fix}")
        
        if api_issues:
            fix = "Fix API connection issues:\n"
            fix += "  - Check API endpoint URLs in frontend configuration\n"
            fix += "  - Verify CORS middleware is properly configured\n"
            fix += "  - Check for API base URL configuration\n"
            fix += "  - Ensure all required services are running"
            self.suggested_fixes.append(fix)
            print(f"  2. {fix}")
        
        if loading_issues:
            fix = "Fix loading state issues:\n"
            fix += "  - Add proper error handling for failed requests\n"
            fix += "  - Implement timeout handling for long-running requests\n"
            fix += "  - Add fallback states for when services are unavailable\n"
            fix += "  - Review async/await patterns in React components"
            self.suggested_fixes.append(fix)
            print(f"  3. {fix}")
        
        # Check for specific issues
        if any('3333' in issue for issue in self.issues_found):
            fix = "Fix Notion MCP server issues:\n"
            fix += "  - Ensure Notion MCP server is running on port 3333\n"
            fix += "  - Check Notion API credentials and database ID\n"
            fix += "  - Verify network connectivity to Notion API"
            self.suggested_fixes.append(fix)
            print(f"  4. {fix}")

async def main():
    """Run the UI debugging session."""
    debugger = UIDebugger()
    await debugger.run_full_debug()

if __name__ == "__main__":
    asyncio.run(main())