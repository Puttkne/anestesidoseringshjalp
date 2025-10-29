
const { expect } = require('@playwright/test');

async function login(page, username = 'blapa', password = 'Flubber1') {
  await page.goto('http://localhost:8501');

  const usernameInput = page.locator('input[type="text"]').first();
  await expect(usernameInput).toBeVisible({ timeout: 10000 });
  await usernameInput.fill(username);

  const passwordInput = page.locator('input[type="password"]').first();
  await passwordInput.fill(password);

  await page.click('button:has-text("Logga in")');
  await expect(page.locator('button:has-text("Logga ut")')).toBeVisible();
}

module.exports = { login };
