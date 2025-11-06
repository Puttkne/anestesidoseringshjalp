const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  // Test at 1080p
  await page.setViewportSize({ width: 1920, height: 1080 });

  console.log('=== TESTING RESULT VISIBILITY @ 1040px ===\n');

  await page.goto('http://localhost:8511', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  // Take screenshot of login
  await page.screenshot({
    path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\01_login.png',
    fullPage: false
  });
  console.log('Screenshot 1: Login page');

  // Login
  await page.fill('input[type="text"]', 'blapa');
  await page.fill('input[type="password"]', 'Flubber1');
  await page.click('button:has-text("Logga in")');
  await page.waitForTimeout(4000);

  // Take screenshot of initial form
  await page.screenshot({
    path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\02_initial_form.png',
    fullPage: false
  });
  console.log('Screenshot 2: Initial form after login');

  // Fill minimal data to enable calculation
  try {
    // Select specialty
    await page.selectOption('select >> nth=0', { index: 1 });
    await page.waitForTimeout(500);

    // Select procedure
    await page.selectOption('select >> nth=1', { index: 1 });
    await page.waitForTimeout(500);

    console.log('Filled specialty and procedure');

    // Take screenshot before calculation
    await page.screenshot({
      path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\03_before_calculate.png',
      fullPage: false
    });
    console.log('Screenshot 3: Before calculation');

    // Click calculate
    await page.click('button:has-text("Beräkna Rekommendation")');
    await page.waitForTimeout(2000);

    // Measure positions after calculation
    const measurements = await page.evaluate(() => {
      const getYByText = (tag, text) => {
        const elements = Array.from(document.querySelectorAll(tag));
        const el = elements.find(e => e.textContent && e.textContent.includes(text));
        return el ? el.getBoundingClientRect().top : null;
      };

      const getBottomByText = (tag, text) => {
        const elements = Array.from(document.querySelectorAll(tag));
        const el = elements.find(e => e.textContent && e.textContent.includes(text));
        return el ? el.getBoundingClientRect().bottom : null;
      };

      return {
        calculateButton: getYByText('button', 'Beräkna'),
        resultSection: getYByText('*', 'Rekommenderad') || getYByText('*', 'Dos'),
        resultBottom: getBottomByText('*', 'Rekommenderad') || getBottomByText('*', 'mg'),
        scrollY: window.scrollY
      };
    });

    console.log('\n=== MEASUREMENTS ===');
    console.log(`Calculate button Y: ${measurements.calculateButton}px`);
    console.log(`Result section Y: ${measurements.resultSection}px`);
    console.log(`Result bottom Y: ${measurements.resultBottom}px`);
    console.log(`Current scroll: ${measurements.scrollY}px`);

    const TARGET = 1040;
    const resultVisible = measurements.resultSection && measurements.resultSection >= 0 && measurements.resultBottom <= TARGET;

    if (resultVisible) {
      console.log(`\n✅ SUCCESS: Result IS visible by ${TARGET}px!`);
    } else if (measurements.resultBottom) {
      const overshoot = measurements.resultBottom - TARGET;
      console.log(`\n❌ FAIL: Result extends ${Math.ceil(overshoot)}px beyond ${TARGET}px`);
    } else {
      console.log('\n⚠️ Could not find result section');
    }

    // Take screenshot after calculation
    await page.screenshot({
      path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\04_after_calculate.png',
      fullPage: false
    });
    console.log('\nScreenshot 4: After calculation');

  } catch (e) {
    console.log('\nError during test:', e.message);
  }

  console.log('\nAll screenshots saved to screenshots/ directory');

  await page.waitForTimeout(3000);
  await browser.close();
})();
