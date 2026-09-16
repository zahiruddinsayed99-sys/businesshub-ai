import { test, expect } from '@playwright/test';

test.describe('BusinessHub AI - Error State & Negative Paths', () => {

    test.describe('Authentication Failures', () => {
        test('should display validation errors on empty login submission', async ({ page }) => {
            await page.goto('/login');
            await page.click('button[type="submit"]');

            await expect(page.locator('#email-error')).toContainText('Email is required');
            await expect(page.locator('#password-error')).toContainText('Password is required');
        });

        test('should reject invalid credentials with an alert banner', async ({ page }) => {
            await page.goto('/login');
            await page.fill('input[name="email"]', 'wrong_user@businesshub.ai');
            await page.fill('input[name="password"]', 'InvalidPassword123!');
            await page.click('button[type="submit"]');

            const alertBanner = page.locator('.alert-error');
            await expect(alertBanner).toBeVisible();
            await expect(alertBanner).toContainText('Invalid credentials or account locked');
        });
    });

    test.describe('RAG Document Ingestion & Query Errors', () => {
        test('should show error state on unsupported file format upload', async ({ page }) => {
            await page.goto('/rag/ingest');

            // Simulate selecting an unsupported file type (e.g., .exe)
            const fileInput = page.locator('input[type="file"]');
            await fileInput.setInputFiles({
                name: 'malicious.exe',
                mimeType: 'application/x-msdownload',
                buffer: Buffer.from('mock executable content')
            });

            await expect(page.locator('.upload-error-banner')).toContainText('Unsupported file format');
            await expect(page.locator('button:has-text("Upload")')).toBeDisabled();
        });

        test('should handle empty chat queries gracefully without crashing the UI', async ({ page }) => {
            await page.goto('/rag/chat');

            const chatInput = page.locator('textarea[placeholder*="Ask a question"]');
            await chatInput.fill('   '); // Whitespace only
            await page.keyboard.press('Enter');

            // Verify that send is prevented or an inline validation hint appears
            await expect(page.locator('.chat-error-toast')).toContainText('Query cannot be empty');
            await expect(page.locator('.message-list')).not.toContainText('   ');
        });
    });

    test.describe('LMS Enrollment Prerequisites', () => {
        test('should prevent enrollment when prerequisites are missing', async ({ page }) => {
            // Navigate directly to an advanced course requiring a prerequisite
            await page.goto('/lms/courses/advanced-ai-architecture');

            const enrollButton = page.locator('button:has-text("Enroll Now")');
            await expect(enrollButton).toBeEnabled();
            await enrollButton.click();

            const modalError = page.locator('.prerequisite-warning-modal');
            await expect(modalError).toBeVisible();
            await expect(modalError).toContainText('Prerequisite required: Fundamentals of AI Engineering');

            // Confirm modal dismissal works cleanly
            await page.click('button:has-text("Close")');
            await expect(modalError).not.toBeVisible();
        });
    });

});