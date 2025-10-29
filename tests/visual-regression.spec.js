const { test, expect } = require('@playwright/test');
const { login } = require('./test-helpers.js');

test.describe('Visual Regression Tests - Screenshot Comparison', () => {

  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.waitForLoadState('networkidle');
  });

  test('31 - Visual: Main Dashboard', async ({ page }) => {
    await expect(page).toHaveScreenshot('main-dashboard.png', {
      fullPage: true,
      maxDiffPixels: 100,
    });
  });

  test('32 - Visual: Patient Data Form', async ({ page }) => {
    const patientSection = page.getByLabel('Ålder');
    await patientSection.scrollIntoViewIfNeeded();

    await expect(page).toHaveScreenshot('patient-data-form.png', {
      maxDiffPixels: 100,
    });
  });

  test('33 - Visual: Calculation Results', async ({ page }) => {
    await page.getByLabel('Ålder').fill('55');
    await page.getByLabel('Vikt (kg)').fill('75');
    await page.getByLabel('Längd (cm)').fill('175');
    await page.getByLabel('Specialitet').selectOption({ label: 'Kirurgi' });
    await page.getByLabel('Ingrepp').nth(1).selectOption({ index: 1 });

    await page.getByRole('button', { name: 'Beräkna Rekommendation' }).click();
    await expect(page.locator('text=/Förslag:/i')).toBeVisible({ timeout: 20000 });

    await expect(page).toHaveScreenshot('calculation-results.png', {
      fullPage: true,
      maxDiffPixels: 200,
    });
  });

  test('34 - Visual: History Tab', async ({ page }) => {
    await page.getByRole('tab', { name: 'Historik & Statistik' }).click();
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveScreenshot('history-tab.png', {
      fullPage: true,
      maxDiffPixels: 100,
    });
  });

  test('35 - Visual: Learning Tab', async ({ page }) => {
    await page.getByRole('tab', { name: 'Inlärning & Modeller' }).click();
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveScreenshot('learning-tab.png', {
      fullPage: true,
      maxDiffPixels: 100,
    });
  });

  test('36 - Visual: Procedures Management Tab', async ({ page }) => {
    await page.getByRole('tab', { name: 'Hantera Ingrepp' }).click();
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveScreenshot('procedures-tab.png', {
      fullPage: true,
      maxDiffPixels: 100,
    });
  });

  test('37 - Visual: Mobile Viewport (375x667)', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveScreenshot('mobile-view.png', {
      fullPage: true,
      maxDiffPixels: 150,
    });
  });

  test('38 - Visual: Tablet Viewport (768x1024)', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveScreenshot('tablet-view.png', {
      fullPage: true,
      maxDiffPixels: 150,
    });
  });
});