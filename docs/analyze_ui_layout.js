const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  // Standard laptop resolution
  await page.setViewportSize({ width: 1366, height: 768 });

  console.log('=== UI LAYOUT ANALYSIS ===\n');
  console.log('Viewport: 1366x768 (standard laptop)\n');

  await page.goto('http://localhost:8507', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  // Login
  await page.fill('input[type="text"]', 'blapa');
  await page.fill('input[type="password"]', 'Flubber1');
  await page.click('button:has-text("Logga in")');
  await page.waitForTimeout(4000);

  // Measure initial viewport
  const viewportHeight = 768;

  // Get positions of key elements
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
      header: getYByText('h1', 'Anestesi'),
      patientDataHeader: getYByText('h2', 'Patientdata'),
      ageInput: getYByText('label', 'Ålder') || 200,
      procedureHeader: getYByText('h2', 'Ingrepp'),
      adjuvantsHeader: getYByText('h3', 'Adjuvanter'),
      calculateButton: getYByText('button', 'Beräkna'),
      calculateButtonBottom: getBottomByText('button', 'Beräkna'),
      pageHeight: document.documentElement.scrollHeight
    };
  });

  console.log('Element Positions (Y-coordinate from top):');
  console.log('─────────────────────────────────────────');
  console.log(`Header (Anestesi-assistent): ${measurements.header}px`);
  console.log(`Patientdata section: ${measurements.patientDataHeader}px`);
  console.log(`Age input field: ${measurements.ageInput}px`);
  console.log(`Ingrepp section: ${measurements.procedureHeader}px`);
  console.log(`Adjuvanter section: ${measurements.adjuvantsHeader}px`);
  console.log(`Calculate button (top): ${measurements.calculateButton}px`);
  console.log(`Calculate button (bottom): ${measurements.calculateButtonBottom}px`);
  console.log(`\nViewport height: ${viewportHeight}px`);
  console.log(`Total page height: ${measurements.pageHeight}px`);

  // Check if calculate button is visible without scrolling
  const buttonVisible = measurements.calculateButtonBottom <= viewportHeight;
  const scrollNeeded = measurements.calculateButtonBottom - viewportHeight;

  console.log('\n=== ANALYSIS ===');
  if (buttonVisible) {
    console.log('✅ Calculate button IS visible without scrolling');
  } else {
    console.log(`❌ Calculate button NOT visible - needs ${Math.ceil(scrollNeeded)}px scrolling`);
  }

  // Now scroll and click calculate to see result position
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(500);

  // Fill in minimal data to enable calculation
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(500);

  // Try to find and fill procedure
  try {
    const specialtySelect = await page.locator('select').first();
    await specialtySelect.selectOption({ index: 1 });
    await page.waitForTimeout(500);

    const procedureSelect = await page.locator('select').nth(1);
    await procedureSelect.selectOption({ index: 1 });
    await page.waitForTimeout(500);

    // Scroll to button and click
    await page.evaluate(() => {
      const btn = document.querySelector('button:has-text("Beräkna Rekommendation")');
      if (btn) btn.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
    await page.waitForTimeout(1000);

    await page.click('button:has-text("Beräkna Rekommendation")');
    await page.waitForTimeout(2000);

    // Measure result position
    const resultMeasurements = await page.evaluate(() => {
      const getYByText = (tag, text) => {
        const elements = Array.from(document.querySelectorAll(tag));
        const el = elements.find(e => e.textContent.includes(text));
        return el ? el.getBoundingClientRect().top : null;
      };

      return {
        resultHeader: getYByText('*', 'Rekommenderad Dos') || getYByText('h3', 'Dos'),
        calculateButton: getYByText('button', 'Beräkna'),
        scrollPosition: window.scrollY
      };
    });

    console.log('\n=== AFTER CALCULATION ===');
    console.log(`Current scroll position: ${resultMeasurements.scrollPosition}px`);
    console.log(`Calculate button position: ${resultMeasurements.calculateButton}px`);
    console.log(`Result display position: ${resultMeasurements.resultHeader}px`);

    const resultVisible = resultMeasurements.resultHeader &&
                         resultMeasurements.resultHeader >= 0 &&
                         resultMeasurements.resultHeader <= viewportHeight;

    if (resultVisible) {
      console.log('✅ Result IS visible in viewport');
    } else {
      console.log('❌ Result NOT visible - requires additional scrolling');
    }

  } catch (e) {
    console.log('\nCould not complete calculation test:', e.message);
  }

  // Take screenshot
  await page.screenshot({
    path: 'c:\\Users\\patri\\Documents\\anestesidoseringshjälp\\screenshots\\ui_analysis.png',
    fullPage: true
  });

  console.log('\n=== RECOMMENDATIONS ===');
  if (scrollNeeded > 0) {
    console.log(`Need to reduce height by at least ${Math.ceil(scrollNeeded)}px`);
    console.log('Suggestions:');
    console.log('  - Use more horizontal space (multi-column layout)');
    console.log('  - Reduce padding/margins');
    console.log('  - Make input fields smaller');
    console.log('  - Combine sections side-by-side');
  }

  await page.waitForTimeout(3000);
  await browser.close();
})();
