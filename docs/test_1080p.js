const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  // 1080p resolution
  await page.setViewportSize({ width: 1920, height: 1080 });

  console.log('=== UI TEST @ 1920x1080 ===\n');

  await page.goto('http://localhost:8510', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  // Login
  await page.fill('input[type="text"]', 'blapa');
  await page.fill('input[type="password"]', 'Flubber1');
  await page.click('button:has-text("Logga in")');
  await page.waitForTimeout(4000);

  // Measure elements
  const measurements = await page.evaluate(() => {
    const getYByText = (tag, text) => {
      const elements = Array.from(document.querySelectorAll(tag));
      const el = elements.find(e => e.textContent.includes(text));
      return el ? el.getBoundingClientRect().top : null;
    };

    const getBottomByText = (tag, text) => {
      const elements = Array.from(document.querySelectorAll(tag));
      const el = elements.find(e => e.textContent.includes(text));
      return el ? el.getBoundingClientRect().bottom : null;
    };

    return {
      calculateButton: getYByText('button', 'Beräkna'),
      calculateButtonBottom: getBottomByText('button', 'Beräkna'),
      pageHeight: document.documentElement.scrollHeight
    };
  });

  const viewportHeight = 1080;
  const buttonVisible = measurements.calculateButtonBottom <= viewportHeight;
  const scrollNeeded = measurements.calculateButtonBottom - viewportHeight;

  console.log(`Viewport height: ${viewportHeight}px`);
  console.log(`Calculate button bottom: ${measurements.calculateButtonBottom}px`);
  console.log(`Page height: ${measurements.pageHeight}px`);

  if (buttonVisible) {
    console.log('\n✅ SUCCESS: Calculate button IS visible without scrolling!');
  } else {
    console.log(`\n❌ FAIL: Still needs ${Math.ceil(scrollNeeded)}px scrolling`);
  }

  // Take screenshot
  await page.screenshot({
    path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\test_1080p.png',
    fullPage: false
  });

  console.log('\nScreenshot saved: test_1080p.png');

  await page.waitForTimeout(5000);
  await browser.close();
})();
