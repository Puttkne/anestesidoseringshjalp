const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1920, height: 1080 });

  console.log('Navigating to app...');
  await page.goto('http://localhost:8503', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  // Login
  console.log('Logging in...');
  await page.fill('input[type="text"]', 'blapa');
  await page.fill('input[type="password"]', 'Flubber1');
  await page.click('button:has-text("Logga in")');
  await page.waitForTimeout(4000);

  // Screenshot 1: Main dosing tab
  await page.screenshot({
    path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\review_01_dosing.png',
    fullPage: true
  });
  console.log('Screenshot 1: Dosing tab');

  // Click through all tabs
  const tabSelectors = [
    'text=Historik & Statistik',
    'text=Inlärning & Modeller',
    'text=Hantera Ingrepp'
  ];

  for (let i = 0; i < tabSelectors.length; i++) {
    try {
      await page.click(tabSelectors[i]);
      await page.waitForTimeout(2000);
      await page.screenshot({
        path: `c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\review_0${i + 2}_tab${i + 2}.png`,
        fullPage: true
      });
      console.log(`Screenshot ${i + 2}: Tab ${i + 2}`);
    } catch (e) {
      console.log(`Could not click tab ${i + 2}: ${e.message}`);
    }
  }

  // Go back to dosing tab
  await page.click('text=💊 Dosering');
  await page.waitForTimeout(1000);

  // Scroll down to see form elements
  await page.evaluate(() => window.scrollTo(0, 500));
  await page.screenshot({
    path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\review_05_dosing_form.png',
    fullPage: false
  });
  console.log('Screenshot 5: Dosing form');

  await browser.close();
  console.log('Review complete!');
})();
