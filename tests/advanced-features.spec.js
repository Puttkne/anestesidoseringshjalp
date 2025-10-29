const { test, expect } = require('@playwright/test');
const { login } = require('./test-helpers.js');

test.describe('Advanced Features - Save, History, and Export', () => {

  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('11 - Calculate and Save Case', async ({ page }) => {
    // Fill patient data
    await page.getByLabel('Ålder').fill('50');
    await page.getByLabel('Vikt (kg)').fill('70');
    await page.getByLabel('Längd (cm)').fill('175');

    // Select procedure
    await page.getByLabel('Specialitet').selectOption({ label: 'Kirurgi' });
    await page.getByLabel('Ingrepp').nth(1).selectOption({ index: 1 });

    // Calculate dose
    await page.getByRole('button', { name: 'Beräkna Rekommendation' }).click();
    await expect(page.locator('text=/Förslag:/i')).toBeVisible({ timeout: 20000 });

    // Save case
    await page.getByRole('button', { name: 'Spara Fall' }).click();
    await expect(page.getByText(/Fallet har sparats/i)).toBeVisible();
  });

  test('12 - View Saved Cases in History', async ({ page }) => {
    await page.getByRole('tab', { name: 'Historik & Statistik' }).click();
    await expect(page.getByRole('heading', { name: 'Sparade Fall' })).toBeVisible();

    // Check if there are any saved cases by looking for the table
    await expect(page.locator('.stDataFrame')).toBeVisible();
  });

  test('13 - Export Functionality', async ({ page }) => {
    await page.getByRole('tab', { name: 'Historik & Statistik' }).click();

    // Look for export button
    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Ladda ner historik som CSV' }).click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('.csv');
  });

  test('14 - Edit and Delete Case', async ({ page }) => {
    await page.getByRole('tab', { name: 'Historik & Statistik' }).click();

    // This test is more complex and depends on the state of the database.
    // For now, we just check that the buttons are there.
    const editButton = page.getByRole('button', { name: 'Redigera' }).first();
    const deleteButton = page.getByRole('button', { name: 'Radera' }).first();

    await expect(editButton).toBeVisible();
    await expect(deleteButton).toBeVisible();
  });
});