const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1920, height: 1080 });

  await page.goto('http://localhost:8505', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  // Login
  await page.fill('input[type="text"]', 'blapa');
  await page.fill('input[type="password"]', 'Flubber1');
  await page.click('button:has-text("Logga in")');
  await page.waitForTimeout(4000);

  // Scroll to adjuvants section
  await page.evaluate(() => window.scrollBy(0, 600));
  await page.waitForTimeout(1000);

  await page.screenshot({
    path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\new_features_adjuvants.png',
    fullPage: true
  });
  console.log('Screenshot saved with new sevoflurane and infiltration toggles');

  await browser.close();
})();
