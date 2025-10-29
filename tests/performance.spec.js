const { test, expect } = require('@playwright/test');
const { login } = require('./test-helpers.js');

test.describe('Performance Tests - Load and Response Time', () => {

  test('23 - Page Load Time - Initial Load', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('http://localhost:8501');
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;
    console.log(`⏱️  Page load time: ${loadTime}ms`);
    expect(loadTime).toBeLessThan(10000);
  });

  test('24 - Response Time - Login Performance', async ({ page }) => {
    const startTime = Date.now();
    await login(page);
    const loginTime = Date.now() - startTime;
    console.log(`⏱️  Login time: ${loginTime}ms`);
    expect(loginTime).toBeLessThan(15000); // More reasonable timeout
  });

  test('25 - Response Time - Dose Calculation', async ({ page }) => {
    await login(page);
    await page.getByLabel('Ålder').fill('55');
    await page.getByLabel('Vikt (kg)').fill('75');
    await page.getByLabel('Längd (cm)').fill('175');
    await page.getByLabel('Specialitet').selectOption({ label: 'Kirurgi' });
    await page.getByLabel('Ingrepp').nth(1).selectOption({ index: 1 });

    const startTime = Date.now();
    await page.getByRole('button', { name: 'Beräkna Rekommendation' }).click();
    await expect(page.locator('text=/Förslag:/i')).toBeVisible({ timeout: 20000 });
    const calculationTime = Date.now() - startTime;
    console.log(`⏱️  Calculation time: ${calculationTime}ms`);
    expect(calculationTime).toBeLessThan(10000);
  });

  test('26 - Stress Test - Rapid Input Changes', async ({ page }) => {
    await login(page);
    const ageInput = page.getByLabel('Ålder');

    for (let i = 0; i < 5; i++) {
      await ageInput.fill(String(20 + i));
    }
    await expect(ageInput).toHaveValue('24');
  });

  test('27 - Stress Test - Rapid Tab Switching', async ({ page }) => {
    await login(page);
    const tabs = [
      'Historik & Statistik',
      'Inlärning & Modeller',
      'Hantera Ingrepp',
      'Dosering',
    ];

    for (let i = 0; i < 10; i++) {
      await page.getByRole('tab', { name: tabs[i % tabs.length] }).click();
    }

    await expect(page.getByRole('button', { name: 'Beräkna Rekommendation' })).toBeVisible();
  });
});