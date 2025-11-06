const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1920, height: 1080 });

  console.log('Navigating to app...');
  await page.goto('http://localhost:8502', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  console.log('Please log in manually...');
  console.log('Waiting 15 seconds for you to log in and navigate...');
  await page.waitForTimeout(15000);

  // Take screenshot of current state
  await page.screenshot({
    path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\current_view.png',
    fullPage: true
  });
  console.log('Screenshot saved: current_view.png');

  console.log('Done! Browser will close in 5 seconds...');
  await page.waitForTimeout(5000);
  await browser.close();
})();
