const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // Set viewport for consistent screenshots
  await page.setViewportSize({ width: 1920, height: 1080 });

  // Navigate to the app
  await page.goto('http://localhost:8502', { waitUntil: 'networkidle' });

  // Wait for Streamlit to load
  await page.waitForTimeout(3000);

  // Take full page screenshot
  await page.screenshot({
    path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\main_page.png',
    fullPage: true
  });

  console.log('Screenshot saved: main_page.png');

  await browser.close();
})();
