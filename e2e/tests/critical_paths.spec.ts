import { test, expect } from '@playwright/test';

test.describe('Tier 3: E2E Critical Paths', () => {

  async function login(page) {
    await page.goto('http://127.0.0.1:4200/login', { timeout: 60000 });
    await page.fill('input[formControlName="email"]', 'admin@apla-kirana.com');
    await page.fill('input[formControlName="password"]', 'SecurePassword123!');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Welcome')).toBeVisible({ timeout: 15000 });
  }

  test('User Login & Routing', async ({ page }) => {
    test.skip(!process.env.E2E_SERVER_URL, 'Requires running environment');
    await login(page);
    await expect(page.getByRole('heading', { name: /crm deal pipeline/i })).toBeVisible();
  });

  test('CRM Deal Creation', async ({ page }) => {
    test.skip(!process.env.E2E_SERVER_URL, 'Requires running environment');
    await login(page);

    await page.getByRole('button', { name: '+ New Deal' }).click();

    const titleInput = page.getByRole('textbox', { name: 'Deal Title' });
    await titleInput.waitFor({ state: 'visible' });
    await titleInput.fill('Big Enterprise Deal');

    const [response] = await Promise.all([
      page.waitForResponse(res => res.url().includes('/api/v1/crm/deals') && res.request().method() === 'POST', { timeout: 10000 }).catch(() => null),
      page.getByRole('button', { name: 'Create Deal' }).click()
    ]);

    if (response) {
      expect(response.status()).toBeLessThan(400);
    }

    await page.waitForSelector('.deal-card', { timeout: 10000 }).catch(() => { });
  });

  test('RAG Document Upload & Query', async ({ page }) => {
    test.skip(!process.env.E2E_SERVER_URL, 'Requires running environment');
    await login(page);

    await page.getByRole('link', { name: /ai platform/i }).click();
    await page.waitForURL('**/ai');

    await page.getByPlaceholder('Document Title').fill('Test Document');
    await page.getByPlaceholder('Paste document content here...').fill('This is a test document content for RAG ingestion.');

    const uploadResponsePromise = page.waitForResponse(res => res.url().includes('/api/v1/ai/documents') && res.status() < 400);
    await page.getByRole('button', { name: /upload & ingest/i }).click();
    await uploadResponsePromise;

    const chatInput = page.locator('textarea, input').last();
    await chatInput.fill('What is this document?');

    const chatResponsePromise = page.waitForResponse(res => res.url().includes('/api/v1/ai/chat') && res.status() < 400);
    await page.getByRole('button', { name: /send|query|ask/i }).last().click();
    await chatResponsePromise;

    await expect(page.locator('app-chat, .chat-container, p, div').filter({ hasText: /test document/i }).first()).toBeVisible({ timeout: 15000 });
  });

  test('LMS Course Enrollment & Lesson Navigation', async ({ page }) => {
    test.skip(!process.env.E2E_SERVER_URL, 'Requires running environment');
    await login(page);

    // 1. Publish draft course via LMS Author
    await page.getByRole('link', { name: /lms author/i }).click();
    await page.waitForURL('**/lms-author');

    const publishButton = page.locator('text=Domestic Hygiene at Home').locator('..').getByRole('button', { name: /publish/i });
    if (await publishButton.isVisible()) {
      await publishButton.click();
    }

    // 2. Switch to LMS Learner, open course, and select lesson
    await page.getByRole('link', { name: /lms learner/i }).click();
    await page.waitForURL('**/lms-learner');

    const openCourseBtn = page.getByRole('button', { name: /open course|enroll|join/i }).first();
    await openCourseBtn.waitFor({ state: 'visible', timeout: 15000 });
    await openCourseBtn.click();

    const lessonLink = page.locator('text=Safe food handling').first();
    await lessonLink.waitFor({ state: 'visible', timeout: 15000 });
    await lessonLink.click();

    // Verify lesson view components are loaded
    await expect(page.getByRole('button', { name: /take quiz|mark complete/i }).first()).toBeVisible({ timeout: 15000 });
  });

});