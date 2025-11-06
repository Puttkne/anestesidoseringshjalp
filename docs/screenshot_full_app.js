const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1920, height: 1080 });

  // Navigate and login
  await page.goto('http://localhost:8502', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  // Login with admin credentials
  await page.fill('input[type="text"]', 'DN123');
  await page.fill('input[type="password"]', 'admin');
  await page.click('button:has-text("Logga in")');
  await page.waitForTimeout(3000);

  // Take screenshot of main dosing tab
  await page.screenshot({
    path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\01_dosing_tab.png',
    fullPage: true
  });
  console.log('Screenshot 1: Dosing tab');

  // Click on Historik & Statistik tab
  const tabs = await page.locator('[data-baseweb="tab"]').all();
  if (tabs.length > 1) {
    await tabs[1].click();
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\02_history_tab.png',
      fullPage: true
    });
    console.log('Screenshot 2: History tab');
  }

  // Click on Inlärning & Modeller tab
  if (tabs.length > 2) {
    await tabs[2].click();
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\03_learning_tab.png',
      fullPage: true
    });
    console.log('Screenshot 3: Learning tab');
  }

  // Click on Hantera Ingrepp tab
  if (tabs.length > 3) {
    await tabs[3].click();
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\04_procedures_tab.png',
      fullPage: true
    });
    console.log('Screenshot 4: Procedures tab');
  }

  // Go back to dosing tab and fill in a sample case
  await tabs[0].click();
  await page.waitForTimeout(1000);

  // Scroll to show the whole form
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\05_dosing_form_top.png',
    fullPage: false
  });
  console.log('Screenshot 5: Dosing form top');

  await browser.close();
  console.log('All screenshots completed!');
})();
