const { test, expect } = require('@playwright/test');
const { login } = require('./test-helpers.js');

test.describe('Anestesi Doseringshjälp - Refactored Test Suite', () => {

  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('01 - Login and Session Verification', async ({ page }) => {
    await expect(page.locator('button:has-text("Logga ut")')).toBeVisible();
    await expect(page.getByLabel('Ålder')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Beräkna Rekommendation' })).toBeVisible();
  });

  test('02 - Fill Patient Data', async ({ page }) => {
    await page.getByLabel('Ålder').fill('55');
    await page.getByLabel('Vikt (kg)').fill('70');
    await page.getByLabel('Längd (cm)').fill('170');

    await expect(page.getByLabel('Ålder')).toHaveValue('55');
    await expect(page.getByLabel('Vikt (kg)')).toHaveValue('70');
    await expect(page.getByLabel('Längd (cm)')).toHaveValue('170');
  });

  test('03 - Select Specialty and Procedure', async ({ page }) => {
    await page.getByLabel('Specialitet').selectOption({ label: 'Kirurgi' });
    // The label for procedure is also 'Ingrepp', but since there are two, we need to be more specific
    await page.getByLabel('Ingrepp').nth(1).selectOption({ index: 1 });

    await expect(page.getByLabel('Specialitet')).toHaveText(/Kirurgi/);
    await expect(page.getByLabel('Ingrepp').nth(1)).not.toBeEmpty();
  });

  test('04 - Calculate Dose Without Adjuvants', async ({ page }) => {
    await page.getByLabel('Ålder').fill('45');
    await page.getByLabel('Vikt (kg)').fill('75');
    await page.getByLabel('Längd (cm)').fill('175');

    await page.getByLabel('Specialitet').selectOption({ label: 'Kirurgi' });
    await page.getByLabel('Ingrepp').nth(1).selectOption({ index: 1 });

    await page.getByRole('button', { name: 'Beräkna Rekommendation' }).click();

    const recommendation = page.locator('text=/Förslag:/i');
    await expect(recommendation).toBeVisible({ timeout: 20000 });
    const recommendationText = await recommendation.textContent();
    expect(recommendationText).toContain('mg');
  });

  test('05 - Calculate Dose With Adjuvants', async ({ page }) => {
    await page.getByLabel('Ålder').fill('60');
    await page.getByLabel('Vikt (kg)').fill('80');
    await page.getByLabel('Längd (cm)').fill('170');

    await page.getByLabel('Specialitet').selectOption({ label: 'Kirurgi' });
    await page.getByLabel('Ingrepp').nth(1).selectOption({ index: 1 });

    await page.getByLabel('Ketamin').selectOption({ label: 'Liten bolus (0.05-0.1 mg/kg)' });

    await page.getByRole('button', { name: 'Beräkna Rekommendation' }).click();

    const recommendation = page.locator('text=/Förslag:/i');
    await expect(recommendation).toBeVisible({ timeout: 20000 });
    const recommendationText = await recommendation.textContent();
    expect(recommendationText).toContain('mg');
  });

  test('06 - Navigate Between Tabs', async ({ page }) => {
    await page.getByRole('tab', { name: 'Historik & Statistik' }).click();
    await expect(page.getByRole('heading', { name: 'Sparade Fall' })).toBeVisible();

    await page.getByRole('tab', { name: 'Inlärning & Modeller' }).click();
    await expect(page.getByRole('heading', { name: 'Användarspecifika Justeringar' })).toBeVisible();

    await page.getByRole('tab', { name: 'Hantera Ingrepp' }).click();
    await expect(page.getByRole('heading', { name: 'Lägg till nytt ingrepp' })).toBeVisible();

    await page.getByRole('tab', { name: 'Dosering' }).click();
    await expect(page.getByRole('button', { name: 'Beräkna Rekommendation' })).toBeVisible();
  });
});