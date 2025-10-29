const { test, expect } = require('@playwright/test');
const { login } = require('./test-helpers.js');

test.describe('Edge Cases - Extreme Values & Validation', () => {

  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('15 - Extreme Age - Very Young Patient (18 years)', async ({ page }) => {
    await page.getByLabel('Ålder').fill('18');
    await page.getByLabel('Vikt (kg)').fill('50');
    await page.getByLabel('Längd (cm)').fill('160');

    await expect(page.getByLabel('Ålder')).toHaveValue('18');
  });

  test('16 - Extreme Age - Very Old Patient (100 years)', async ({ page }) => {
    await page.getByLabel('Ålder').fill('100');
    await page.getByLabel('Vikt (kg)').fill('60');
    await page.getByLabel('Längd (cm)').fill('160');

    await expect(page.getByLabel('Ålder')).toHaveValue('100');
  });

  test('17 - Extreme Weight - Very Low (30 kg)', async ({ page }) => {
    await page.getByLabel('Ålder').fill('25');
    await page.getByLabel('Vikt (kg)').fill('30');
    await page.getByLabel('Längd (cm)').fill('150');

    await page.getByLabel('Specialitet').selectOption({ label: 'Kirurgi' });
    await page.getByLabel('Ingrepp').nth(1).selectOption({ index: 1 });

    await page.getByRole('button', { name: 'Beräkna Rekommendation' }).click();

    const recommendation = page.locator('text=/Förslag:/i');
    await expect(recommendation).toBeVisible({ timeout: 20000 });
    const recommendationText = await recommendation.textContent();
    expect(recommendationText).toContain('mg');
  });

  test('18 - Extreme Weight - Very High (200 kg)', async ({ page }) => {
    await page.getByLabel('Ålder').fill('45');
    await page.getByLabel('Vikt (kg)').fill('200');
    await page.getByLabel('Längd (cm)').fill('180');

    await page.getByLabel('Specialitet').selectOption({ label: 'Kirurgi' });
    await page.getByLabel('Ingrepp').nth(1).selectOption({ index: 1 });

    await page.getByRole('button', { name: 'Beräkna Rekommendation' }).click();

    const recommendation = page.locator('text=/Förslag:/i');
    await expect(recommendation).toBeVisible({ timeout: 20000 });
    const recommendationText = await recommendation.textContent();
    expect(recommendationText).toContain('mg');
  });

  test('19 - Empty Fields - Calculate Without Data', async ({ page }) => {
    await page.getByRole('button', { name: 'Beräkna Rekommendation' }).click();

    // The app should not crash and the button should still be there.
    await expect(page.getByRole('button', { name: 'Beräkna Rekommendation' })).toBeVisible();
  });

  test('20 - Special Characters in Input', async ({ page }) => {
    await page.getByLabel('Ålder').fill('abc');
    // The input should be sanitized and the value should be empty or a number
    const value = await page.getByLabel('Ålder').inputValue();
    expect(isNaN(parseInt(value))).toBe(true);
  });

  test('21 - ASA 4 - Critical Patient', async ({ page }) => {
    await page.getByLabel('Ålder').fill('70');
    await page.getByLabel('Vikt (kg)').fill('65');
    await page.getByLabel('Längd (cm)').fill('165');

    await page.getByLabel('ASA-klass').selectOption({ label: 'ASA 4' });

    await page.getByLabel('Specialitet').selectOption({ label: 'Kirurgi' });
    await page.getByLabel('Ingrepp').nth(1).selectOption({ index: 1 });

    await page.getByRole('button', { name: 'Beräkna Rekommendation' }).click();

    const recommendation = page.locator('text=/Förslag:/i');
    await expect(recommendation).toBeVisible({ timeout: 20000 });
    const recommendationText = await recommendation.textContent();
    expect(recommendationText).toContain('mg');
  });

  test('22 - Multiple Calculations in Sequence', async ({ page }) => {
    for (let i = 0; i < 3; i++) {
      await page.getByLabel('Ålder').fill(String(30 + i * 10));
      await page.getByLabel('Vikt (kg)').fill(String(70 + i * 5));
      await page.getByLabel('Längd (cm)').fill(String(170 + i * 5));

      await page.getByLabel('Specialitet').selectOption({ label: 'Kirurgi' });
      await page.getByLabel('Ingrepp').nth(1).selectOption({ index: i + 1 });

      await page.getByRole('button', { name: 'Beräkna Rekommendation' }).click();

      const recommendation = page.locator('text=/Förslag:/i');
      await expect(recommendation).toBeVisible({ timeout: 20000 });
    }
  });
});