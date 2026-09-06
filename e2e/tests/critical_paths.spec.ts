import { test, expect } from '@playwright/test';

// Tier 3: Playwright E2E Tests (UI "Happy Paths")
// Note: Since these tests rely on the full backend+frontend server, we write the structure
// and assertions as required, which will execute when the app is up.

test.describe('Tier 3: E2E Critical Paths', () => {

  test('User Login & Routing', async ({ page }) => {
    test.skip(!process.env.E2E_SERVER_URL, 'Requires running environment');

    await page.goto('http://127.0.0.1:4200/login', { timeout: 5000 });
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('CRM Deal Creation', async ({ page }) => {
    test.skip(!process.env.E2E_SERVER_URL, 'Requires running environment');

    await page.goto('http://127.0.0.1:4200/login', { timeout: 5000 });
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/crm');
    await page.click('button:has-text("New Deal")');
    await page.fill('input[name="title"]', 'Big Enterprise Deal');
    await page.click('button:has-text("Save")');
    await page.dragAndDrop('.deal-card', '.stage-qualified');
  });

  test('RAG Document Upload & Query', async ({ page }) => {
    test.skip(!process.env.E2E_SERVER_URL, 'Requires running environment');

    await page.goto('http://127.0.0.1:4200/login', { timeout: 5000 });
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/rag');

    // Upload doc
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.click('button:has-text("Upload Document")');
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles({
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('This is a test document for RAG.')
    });

    // Query doc
    await page.fill('input[name="query"]', 'What is this document?');
    await page.click('button:has-text("Search")');
    await expect(page.locator('.rag-result')).toBeVisible();
  });

  test('LMS Course Enrollment & Quiz Execution', async ({ page }) => {
    test.skip(!process.env.E2E_SERVER_URL, 'Requires running environment');

    await page.goto('http://127.0.0.1:4200/login', { timeout: 5000 });
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/lms/catalog');

    await page.click('button:has-text("Enroll")');
    await page.click('button:has-text("Start Course")');
    await page.click('button:has-text("Take Quiz")');

    // Answer quiz
    await page.click('.quiz-option:nth-child(1)'); // just picking first option
    await page.click('button:has-text("Submit Quiz")');

    await expect(page.locator('.quiz-result')).toContainText('Passed');
  });

});
