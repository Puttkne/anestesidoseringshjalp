# Quick Test Reference Guide

## Run Tests Now

### Option 1: One-Click Run (Easiest)
```bash
# Windows
run_tests.bat

# Linux/Mac
./run_tests.sh
```

### Option 2: Manual Run
```bash
# Terminal 1: Start the app
streamlit run oxydoseks.py

# Terminal 2: Run tests (wait 10 seconds after starting app)
python test_comprehensive_playwright.py
```

### Option 3: Using npm scripts
```bash
npm test          # Run comprehensive tests
npm run test:basic # Run basic tests
npm run test:light # Run light smoke tests
npm run test:all   # Run all test suites
```

## Test Files Overview

| File | Tests | Description | Run Time |
|------|-------|-------------|----------|
| `test_ui_light.py` | 3 | Quick smoke test | 5s |
| `test_full_playwright.py` | 36 | Basic feature testing | 30s |
| `test_comprehensive_playwright.py` | 95+ | **FULL comprehensive suite** | 60s |

## What Gets Tested (Comprehensive Suite)

✅ **15 Test Suites:**
1. Login Page Structure
2. User Authentication
3. Main Interface Elements
4. Patient Section (age, weight, height, ASA, opioid history, checkboxes)
5. Procedure Section (specialty, procedure, surgery type)
6. Temporal Dosing (add/delete opioid doses with timing)
7. Adjuvant Section (NSAID, Ketamin, Lidokain, Catapressan, etc.)
8. Calculation Engine (dose recommendation with real data)
9. Logging Section (VAS, rescue timing, postop data)
10. History Tab (case list, filtering, editing, export)
11. Learning Tab (ML status, calibration, statistics)
12. Procedures Tab (procedure management)
13. Error Detection (no exceptions or crashes)
14. Admin Features (user management, ML settings)
15. Responsive Layout (viewport and scroll)

## Test Results

Results are shown in console with:
- ✅ Green checkmarks for passed tests
- ❌ Red X for failed tests
- ⚠️  Yellow warning for non-critical issues

**Screenshots are auto-saved to:** `test_screenshots/`

## Test Configuration

Edit `test_comprehensive_playwright.py` to configure:

```python
class TestConfig:
    BASE_URL = "http://localhost:8501"
    TIMEOUT = 30000  # 30 seconds
    TEST_USER = "TEST_PLAYWRIGHT_USER"
    TEST_ADMIN = "admin"
    TEST_PASSWORD = "admin123"
    HEADLESS = True  # Set False to watch tests run
    SLOW_MO = 100  # Milliseconds delay between actions
```

## Troubleshooting

**"Connection refused"**
→ Make sure Streamlit app is running first

**"Timeout exceeded"**
→ Increase `TIMEOUT` in TestConfig or wait longer before running tests

**"Element not found"**
→ Check screenshots in `test_screenshots/` folder to see what's on screen

**Tests pass but you want to see them run**
→ Set `HEADLESS = False` in TestConfig

## Screenshots Explained

After running tests, check these screenshots:

- `00_initial_load.png` - App initial state
- `01_login_page.png` - Login page
- `02_authenticated.png` - After successful login
- `03-15_*.png` - Each test suite state
- `99_final_state.png` - Final state
- `ERROR_state.png` - Error screenshot (if failure)

## Example Output

```
================================================================================
                      COMPREHENSIVE PLAYWRIGHT TEST SUITE
================================================================================

✅ [PASS] Login page title visible
✅ [PASS] Username field present
✅ [PASS] Password field present
...
✅ [PASS] User login successful - Logged in as TEST_PLAYWRIGHT_USER
...
✅ [PASS] Dose recommendation calculated - Förslag: 7.5 mg
...

================================================================================
                                 TEST SUMMARY
================================================================================
Total Tests: 95
Passed: 93 (97.9%)
Failed: 2
Warnings: 3
Time elapsed: 58.34 seconds
================================================================================
```

## Best Practices

1. ✅ Always start the Streamlit app before running tests
2. ✅ Check screenshots after test failures
3. ✅ Run tests before committing code changes
4. ✅ Use test user credentials (not production data)
5. ✅ Review console output for detailed test results

## Need More Help?

See full documentation: [TESTING.md](TESTING.md)
