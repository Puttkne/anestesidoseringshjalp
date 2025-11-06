const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1920, height: 1080 });

  console.log('=== FINAL UI SCREENSHOTS @ 1920x1080 ===\n');

  await page.goto('http://localhost:8512', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  // Screenshot 1: Login
  await page.screenshot({
    path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\final_01_login.png',
    fullPage: false
  });
  console.log('✓ Screenshot 1: Login');

  // Login
  await page.fill('input[type="text"]', 'blapa');
  await page.fill('input[type="password"]', 'Flubber1');
  await page.click('button:has-text("Logga in")');
  await page.waitForTimeout(4000);

  // Screenshot 2: Initial form layout
  await page.screenshot({
    path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\final_02_form_layout.png',
    fullPage: false
  });
  console.log('✓ Screenshot 2: Form layout with compressed spacing');

  // Measure positions
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
      patientdata: getYByText('*', 'Patientdata'),
      ingrepp: getYByText('*', 'Ingrepp'),
      analgesi: getYByText('*', 'Analgesi'),
      adjuvanter: getYByText('*', 'Adjuvanter'),
      calculateButton: getYByText('button', 'Beräkna'),
      calculateButtonBottom: getBottomByText('button', 'Beräkna')
    };
  });

  console.log('\n=== Layout Measurements ===');
  console.log(`Patientdata: ${measurements.patientdata}px`);
  console.log(`Ingrepp: ${measurements.ingrepp}px`);
  console.log(`Analgesi (right column): ${measurements.analgesi}px`);
  console.log(`Adjuvanter: ${measurements.adjuvanter}px`);
  console.log(`Calculate button: ${measurements.calculateButton}px`);
  console.log(`Calculate button bottom: ${measurements.calculateButtonBottom}px`);

  const viewport = 1080;
  if (measurements.calculateButtonBottom <= viewport) {
    console.log(`\n✅ SUCCESS: Button visible (${measurements.calculateButtonBottom}px < ${viewport}px)`);
  } else {
    console.log(`\n❌ Button NOT visible (${measurements.calculateButtonBottom}px > ${viewport}px)`);
  }

  console.log('\nAll screenshots saved!');
  console.log('Check: screenshots/final_01_login.png');
  console.log('Check: screenshots/final_02_form_layout.png');

  await page.waitForTimeout(5000);
  await browser.close();
})();
