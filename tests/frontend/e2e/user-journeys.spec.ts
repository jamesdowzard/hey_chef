/**
 * End-to-end user journey tests for Hey Chef v2.
 */

import { test, expect, Page } from '@playwright/test';

// Helper function to wait for the app to load
async function waitForAppLoad(page: Page) {
  await page.waitForSelector('[data-testid="app-container"]', { timeout: 10000 });
  await page.waitForLoadState('networkidle');
}

// Helper function to mock WebSocket connection
async function mockWebSocket(page: Page) {
  await page.addInitScript(() => {
    class MockWebSocket {
      constructor(url: string) {
        setTimeout(() => {
          if (this.onopen) this.onopen(new Event('open'));
        }, 100);
      }
      
      send(data: string) {
        // Mock sending data
        setTimeout(() => {
          if (this.onmessage) {
            this.onmessage(new MessageEvent('message', {
              data: JSON.stringify({
                type: 'text_response',
                data: { text: 'Here is how to cook that dish properly.' }
              })
            }));
          }
        }, 500);
      }
      
      close() {
        if (this.onclose) this.onclose(new CloseEvent('close'));
      }
      
      onopen: ((event: Event) => void) | null = null;
      onclose: ((event: CloseEvent) => void) | null = null;
      onmessage: ((event: MessageEvent) => void) | null = null;
      onerror: ((event: Event) => void) | null = null;
      readyState = 1; // OPEN
    }
    
    (window as any).WebSocket = MockWebSocket;
  });
}

test.describe('Hey Chef User Journeys', () => {
  test.beforeEach(async ({ page }) => {
    // Mock WebSocket for all tests
    await mockWebSocket(page);
    
    // Navigate to the application
    await page.goto('http://localhost:3000');
    await waitForAppLoad(page);
  });

  test('Complete cooking assistance workflow', async ({ page }) => {
    // 1. User arrives at the app and sees the main interface
    await expect(page.getByTestId('app-container')).toBeVisible();
    await expect(page.getByText('Hey Chef')).toBeVisible();
    
    // 2. Check that the initial state is correct
    await expect(page.getByTestId('chef-status')).toContainText('Ready to help');
    await expect(page.getByTestId('audio-status')).toContainText('Idle');
    
    // 3. User switches to a different chef mode
    await page.getByTestId('chef-mode-selector').click();
    await page.getByText('Sassy Chef').click();
    await expect(page.getByTestId('chef-mode-display')).toContainText('Sassy');
    
    // 4. User types a cooking question
    const questionInput = page.getByTestId('text-input');
    await questionInput.fill('How do I cook pasta?');
    await page.getByTestId('send-button').click();
    
    // 5. Verify the question appears in chat
    await expect(page.getByTestId('chat-messages')).toContainText('How do I cook pasta?');
    
    // 6. Wait for and verify the response
    await expect(page.getByTestId('chat-messages')).toContainText('Here is how to cook that dish properly.');
    
    // 7. User asks a follow-up question
    await questionInput.fill('What about the sauce?');
    await page.getByTestId('send-button').click();
    
    // 8. Verify conversation history is maintained
    await expect(page.getByTestId('chat-messages')).toContainText('How do I cook pasta?');
    await expect(page.getByTestId('chat-messages')).toContainText('What about the sauce?');
  });

  test('Recipe browsing and viewing workflow', async ({ page }) => {
    // 1. Navigate to recipes section
    await page.getByTestId('recipes-tab').click();
    
    // 2. Wait for recipes to load
    await expect(page.getByTestId('recipe-list')).toBeVisible();
    await page.waitForSelector('[data-testid="recipe-card"]');
    
    // 3. Verify recipes are displayed
    const recipeCards = page.getByTestId('recipe-card');
    await expect(recipeCards.first()).toBeVisible();
    
    // 4. Use search functionality
    const searchInput = page.getByTestId('recipe-search');
    await searchInput.fill('pasta');
    await page.keyboard.press('Enter');
    
    // 5. Verify search results
    await expect(page.getByTestId('recipe-list')).toContainText('pasta');
    
    // 6. Filter by category
    await page.getByTestId('category-filter').selectOption('italian');
    await page.waitForTimeout(1000); // Wait for filter to apply
    
    // 7. Click on a recipe to view details
    await recipeCards.first().click();
    
    // 8. Verify recipe viewer opens
    await expect(page.getByTestId('recipe-viewer')).toBeVisible();
    await expect(page.getByTestId('recipe-title')).toBeVisible();
    await expect(page.getByTestId('recipe-ingredients')).toBeVisible();
    await expect(page.getByTestId('recipe-instructions')).toBeVisible();
    
    // 9. Ask a question about the recipe
    await page.getByTestId('ask-question-button').click();
    const questionModal = page.getByTestId('question-modal');
    await expect(questionModal).toBeVisible();
    
    await questionModal.getByRole('textbox').fill('How long should I cook this?');
    await questionModal.getByTestId('submit-question').click();
    
    // 10. Close recipe viewer
    await page.getByTestId('close-recipe-viewer').click();
    await expect(page.getByTestId('recipe-viewer')).not.toBeVisible();
  });

  test('Audio interaction workflow', async ({ page }) => {
    // Mock audio permissions and MediaRecorder
    await page.addInitScript(() => {
      navigator.mediaDevices = {
        getUserMedia: () => Promise.resolve({
          getTracks: () => [{ stop: () => {} }]
        } as any),
        enumerateDevices: () => Promise.resolve([])
      } as any;
      
      (window as any).MediaRecorder = class {
        constructor() {}
        start() { if (this.onstart) this.onstart(new Event('start')); }
        stop() { 
          if (this.ondataavailable) {
            this.ondataavailable(new BlobEvent('dataavailable', { 
              data: new Blob(['audio'], { type: 'audio/wav' }) 
            }));
          }
          if (this.onstop) this.onstop(new Event('stop'));
        }
        onstart: any = null;
        onstop: any = null;
        ondataavailable: any = null;
        state = 'inactive';
      };
    });

    // 1. Enable audio mode
    await page.getByTestId('audio-toggle').click();
    
    // 2. Verify audio permissions are requested (mock granted)
    await expect(page.getByTestId('audio-status')).toContainText('Ready');
    
    // 3. Start recording
    await page.getByTestId('record-button').click();
    await expect(page.getByTestId('audio-status')).toContainText('Recording');
    
    // 4. Stop recording
    await page.getByTestId('stop-recording-button').click();
    await expect(page.getByTestId('audio-status')).toContainText('Processing');
    
    // 5. Verify transcription appears
    await expect(page.getByTestId('transcription-display')).toBeVisible();
    
    // 6. Verify response is generated
    await expect(page.getByTestId('chat-messages')).toContainText('Here is how to cook that dish properly.');
  });

  test('Error handling and recovery workflow', async ({ page }) => {
    // 1. Simulate network error by blocking API calls
    await page.route('**/api/**', route => route.abort());
    
    // 2. Try to load recipes
    await page.getByTestId('recipes-tab').click();
    
    // 3. Verify error message is displayed
    await expect(page.getByTestId('error-message')).toContainText('Error loading recipes');
    
    // 4. Try retry functionality
    await page.getByTestId('retry-button').click();
    
    // 5. Restore network and retry
    await page.unroute('**/api/**');
    await page.getByTestId('retry-button').click();
    
    // 6. Verify recipes load successfully
    await expect(page.getByTestId('recipe-list')).toBeVisible();
  });

  test('Responsive design workflow', async ({ page }) => {
    // 1. Test desktop layout
    await page.setViewportSize({ width: 1200, height: 800 });
    await expect(page.getByTestId('desktop-layout')).toBeVisible();
    
    // 2. Test tablet layout
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.getByTestId('tablet-layout')).toBeVisible();
    
    // 3. Test mobile layout
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.getByTestId('mobile-layout')).toBeVisible();
    
    // 4. Test mobile navigation
    await page.getByTestId('mobile-menu-button').click();
    await expect(page.getByTestId('mobile-menu')).toBeVisible();
    
    // 5. Navigate using mobile menu
    await page.getByTestId('mobile-recipes-link').click();
    await expect(page.getByTestId('recipe-list')).toBeVisible();
  });

  test('Accessibility workflow', async ({ page }) => {
    // 1. Test keyboard navigation
    await page.keyboard.press('Tab');
    await expect(page.getByTestId('text-input')).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(page.getByTestId('send-button')).toBeFocused();
    
    // 2. Test screen reader compatibility
    const textInput = page.getByTestId('text-input');
    await expect(textInput).toHaveAttribute('aria-label');
    
    const sendButton = page.getByTestId('send-button');
    await expect(sendButton).toHaveAttribute('aria-label');
    
    // 3. Test high contrast mode
    await page.emulateMedia({ colorScheme: 'dark' });
    await expect(page.getByTestId('app-container')).toHaveClass(/dark-theme/);
    
    // 4. Test focus indicators
    await page.keyboard.press('Tab');
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toHaveCSS('outline-width', /^[1-9]/); // Has outline
  });

  test('Performance workflow', async ({ page }) => {
    // 1. Measure initial page load
    const startTime = Date.now();
    await page.goto('http://localhost:3000');
    await waitForAppLoad(page);
    const loadTime = Date.now() - startTime;
    
    // 2. Verify reasonable load time (adjust threshold as needed)
    expect(loadTime).toBeLessThan(5000); // 5 seconds
    
    // 3. Test smooth scrolling in recipe list
    await page.getByTestId('recipes-tab').click();
    await page.waitForSelector('[data-testid="recipe-card"]');
    
    const recipeList = page.getByTestId('recipe-list');
    await recipeList.evaluate(el => el.scrollBy(0, 1000));
    
    // 4. Verify no performance warnings in console
    const logs = [];
    page.on('console', msg => {
      if (msg.type() === 'warning' && msg.text().includes('performance')) {
        logs.push(msg.text());
      }
    });
    
    // Perform some interactions
    await page.getByTestId('text-input').fill('Test message');
    await page.getByTestId('send-button').click();
    
    // Check for performance warnings
    expect(logs.length).toBe(0);
  });

  test('Data persistence workflow', async ({ page }) => {
    // 1. Set chef mode
    await page.getByTestId('chef-mode-selector').click();
    await page.getByText('Gordon Ramsay').click();
    
    // 2. Send a message
    await page.getByTestId('text-input').fill('Test message for persistence');
    await page.getByTestId('send-button').click();
    
    // 3. Refresh the page
    await page.reload();
    await waitForAppLoad(page);
    
    // 4. Verify chat history is restored
    await expect(page.getByTestId('chat-messages')).toContainText('Test message for persistence');
    
    // 5. Verify chef mode is restored
    await expect(page.getByTestId('chef-mode-display')).toContainText('Gordon Ramsay');
  });

  test('Multi-tab workflow', async ({ browser }) => {
    // 1. Open two tabs
    const context = await browser.newContext();
    const page1 = await context.newPage();
    const page2 = await context.newPage();
    
    // 2. Navigate both to the app
    await mockWebSocket(page1);
    await mockWebSocket(page2);
    
    await page1.goto('http://localhost:3000');
    await page2.goto('http://localhost:3000');
    
    await waitForAppLoad(page1);
    await waitForAppLoad(page2);
    
    // 3. Send message in first tab
    await page1.getByTestId('text-input').fill('Message from tab 1');
    await page1.getByTestId('send-button').click();
    
    // 4. Switch to second tab and verify independent state
    await page2.getByTestId('text-input').fill('Message from tab 2');
    await page2.getByTestId('send-button').click();
    
    // 5. Verify each tab maintains its own conversation
    await expect(page1.getByTestId('chat-messages')).toContainText('Message from tab 1');
    await expect(page1.getByTestId('chat-messages')).not.toContainText('Message from tab 2');
    
    await expect(page2.getByTestId('chat-messages')).toContainText('Message from tab 2');
    await expect(page2.getByTestId('chat-messages')).not.toContainText('Message from tab 1');
    
    await context.close();
  });
});