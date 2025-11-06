const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 }
    });
    const page = await context.newPage();

    await page.goto('http://localhost:8515');

    // Wait for page to load
    await page.waitForTimeout(3000);

    // Helper to get Y position by text content
    const getYByText = (tag, text) => {
        const elements = Array.from(document.querySelectorAll(tag));
        const el = elements.find(e => e.textContent.includes(text));
        return el ? el.getBoundingClientRect().top : null;
    };

    // Login first
    try {
        const usernameInput = page.locator('input[placeholder*="DN123"]');
        await usernameInput.waitFor({ timeout: 2000 });
        await usernameInput.fill('blapa');

        const passwordInput = page.locator('input[type="password"]');
        await passwordInput.fill('Flubber1');

        await page.click('button:has-text("Logga in")');
        await page.waitForTimeout(2000);
    } catch (e) {
        console.log('Already logged in or login not needed');
    }

    // Measure header layout
    const headerLayout = await page.evaluate(() => {
        const title = document.querySelector('h1');
        const subtitle = Array.from(document.querySelectorAll('div')).find(
            el => el.textContent.includes('Ett datadrivet beslutsstöd')
        );

        return {
            titleY: title ? title.getBoundingClientRect().top : null,
            titleBottom: title ? title.getBoundingClientRect().bottom : null,
            subtitleY: subtitle ? subtitle.getBoundingClientRect().top : null,
            subtitleBottom: subtitle ? subtitle.getBoundingClientRect().bottom : null,
            subtitleLeft: subtitle ? subtitle.getBoundingClientRect().left : null,
        };
    });

    // Measure key elements
    const measurements = await page.evaluate(() => {
        // Find calculate button
        const buttons = Array.from(document.querySelectorAll('button'));
        const calcBtn = buttons.find(btn => btn.textContent.includes('Beräkna dos'));

        // Find first selectbox after "Patientdata"
        const labels = Array.from(document.querySelectorAll('label'));
        const firstSelect = labels.find(l => l.textContent.includes('Kön'));

        // Find specialty selectbox
        const specialtySelect = labels.find(l => l.textContent.includes('Specialitet'));

        return {
            calcBtnY: calcBtn ? calcBtn.getBoundingClientRect().top : null,
            calcBtnBottom: calcBtn ? calcBtn.getBoundingClientRect().bottom : null,
            firstSelectY: firstSelect ? firstSelect.getBoundingClientRect().top : null,
            specialtySelectY: specialtySelect ? specialtySelect.getBoundingClientRect().top : null,
        };
    });

    // Calculate spacing
    const selectSpacing = measurements.specialtySelectY - measurements.firstSelectY;
    const clearance = 1080 - measurements.calcBtnBottom;

    console.log('\n=== Header Layout ===');
    console.log(`Title top: ${headerLayout.titleY}px`);
    console.log(`Title bottom: ${headerLayout.titleBottom}px`);
    console.log(`Subtitle top: ${headerLayout.subtitleY}px`);
    console.log(`Subtitle left: ${headerLayout.subtitleLeft}px`);
    console.log(`Subtitle aligned horizontally: ${headerLayout.subtitleY < headerLayout.titleBottom && headerLayout.subtitleY >= headerLayout.titleY ? '✅ YES' : '❌ NO'}`);

    console.log('\n=== Layout Measurements ===');
    console.log(`First select (Kön): ${measurements.firstSelectY}px`);
    console.log(`Specialty select: ${measurements.specialtySelectY}px`);
    console.log(`Spacing between elements: ${selectSpacing.toFixed(2)}px`);
    console.log(`Calculate button: ${measurements.calcBtnY}px`);
    console.log(`Calculate button bottom: ${measurements.calcBtnBottom}px`);
    console.log(`Clearance for results: ${clearance.toFixed(2)}px`);

    if (measurements.calcBtnBottom < 1080) {
        console.log('✅ SUCCESS: Button visible within 1080px viewport');
    } else {
        console.log('❌ FAIL: Button extends beyond 1080px viewport');
    }

    // Take screenshots
    await page.screenshot({ path: 'test_final_ui_full.png', fullPage: false });
    console.log('\n📸 Screenshot saved: test_final_ui_full.png');

    await browser.close();
})();
