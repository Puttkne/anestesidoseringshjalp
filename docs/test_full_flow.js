const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 100 });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1920, height: 1080 });

  console.log('=== TESTING FULL APP FLOW ===\n');

  // TEST 1: Login
  console.log('TEST 1: Login functionality');
  await page.goto('http://localhost:8501', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  await page.fill('input[type="text"]', 'blapa');
  await page.fill('input[type="password"]', 'Flubber1');
  await page.click('button:has-text("Logga in")');
  await page.waitForTimeout(3000);

  // Check if logged in
  const loggedIn = await page.locator('button:has-text("Logga ut")').isVisible();
  console.log(`  ✓ Login successful: ${loggedIn}\n`);

  // TEST 2: Dosering Tab - Fill form and calculate
  console.log('TEST 2: Dosering - Calculate recommendation');
  await page.click('text=💊 Dosering');
  await page.waitForTimeout(2000);

  // Fill patient data using aria-label
  const ageInput = page.locator('input[aria-label="Ålder"]').first();
  await ageInput.click();
  await ageInput.fill('');
  await ageInput.type('65');

  const weightInput = page.locator('input[aria-label="Vikt (kg)"]').first();
  await weightInput.click();
  await weightInput.fill('');
  await weightInput.type('80');

  const heightInput = page.locator('input[aria-label="Längd (cm)"]').first();
  await heightInput.click();
  await heightInput.fill('');
  await heightInput.type('170');
  await page.waitForTimeout(1000);

  // Select specialty using Streamlit select component
  const specialtySelects = page.locator('div[data-baseweb="select"]');
  const specialtySelect = specialtySelects.nth(2); // 3rd select (after kön, asa)
  await specialtySelect.scrollIntoViewIfNeeded();
  await specialtySelect.click();
  await page.waitForTimeout(800);
  await page.locator('text=Gynekologi').click({ force: true });
  await page.waitForTimeout(1000);

  // Select procedure
  const procedureSelect = specialtySelects.nth(3);
  await procedureSelect.scrollIntoViewIfNeeded();
  await procedureSelect.click();
  await page.waitForTimeout(800);
  await page.locator('text=Hysterektomi').first().click({ force: true });
  await page.waitForTimeout(1000);

  // Fill fentanyl dose
  const fentanylInput = page.locator('input[aria-label*="Fentanyl"]').first();
  await fentanylInput.click();
  await fentanylInput.fill('');
  await fentanylInput.type('150');
  await page.waitForTimeout(500);

  // Click calculate button
  await page.click('button:has-text("Beräkna Rekommendation")');
  await page.waitForTimeout(2000);

  // Check if results appeared
  const hasResults = await page.locator('text=Rekommenderad Dos').isVisible();
  console.log(`  ✓ Calculation successful: ${hasResults}\n`);

  await page.screenshot({
    path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\test_02_calculation.png',
    fullPage: true
  });

  // TEST 3: Save case
  console.log('TEST 3: Save case functionality');
  await page.waitForTimeout(1000);

  // Scroll down to find save button
  await page.evaluate(() => window.scrollBy(0, 500));
  await page.waitForTimeout(500);

  const hasSaveButton = await page.locator('button:has-text("Spara")').isVisible();
  console.log(`  ✓ Save button visible: ${hasSaveButton}\n`);

  // TEST 4: Historik & Statistik Tab
  console.log('TEST 4: Historik & Statistik tab');
  await page.click('text=Historik & Statistik');
  await page.waitForTimeout(2000);

  const hasHistory = await page.locator('text=Sparade Fall').isVisible();
  console.log(`  ✓ History tab loaded: ${hasHistory}\n`);

  await page.screenshot({
    path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\test_03_history.png',
    fullPage: true
  });

  // TEST 5: Inlärning & Modeller Tab
  console.log('TEST 5: Inlärning & Modeller tab');
  await page.click('text=Inlärning & Modeller');
  await page.waitForTimeout(2000);

  const hasLearning = await page.locator('text=ML-Modellens Aktiveringsstatus').isVisible();
  console.log(`  ✓ Learning tab loaded: ${hasLearning}\n`);

  await page.screenshot({
    path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\test_04_learning.png',
    fullPage: true
  });

  // TEST 6: Hantera Ingrepp Tab
  console.log('TEST 6: Hantera Ingrepp tab');
  await page.click('text=Hantera Ingrepp');
  await page.waitForTimeout(2000);

  const hasProcedures = await page.locator('text=Lägg till nytt ingrepp').isVisible();
  console.log(`  ✓ Procedures tab loaded: ${hasProcedures}\n`);

  await page.screenshot({
    path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\test_05_procedures.png',
    fullPage: true
  });

  // TEST 7: Back to Dosering
  console.log('TEST 7: Navigation back to Dosering');
  await page.click('text=💊 Dosering');
  await page.waitForTimeout(2000);

  const backToDosing = await page.locator('text=Beräkna Rekommendation').isVisible();
  console.log(`  ✓ Back to dosing tab: ${backToDosing}\n`);

  // TEST 8: Logout
  console.log('TEST 8: Logout functionality');
  await page.click('button:has-text("Logga ut")');
  await page.waitForTimeout(2000);

  const loggedOut = await page.locator('text=Logga in').isVisible();
  console.log(`  ✓ Logout successful: ${loggedOut}\n`);

  await page.screenshot({
    path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\test_06_logout.png',
    fullPage: true
  });

  console.log('=== ALL TESTS COMPLETED ===');
  console.log('Screenshots saved to screenshots/ directory');

  await page.waitForTimeout(2000);
  await browser.close();
})();
