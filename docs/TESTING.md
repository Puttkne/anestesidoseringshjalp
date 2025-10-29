# Testing Guide for Anestesidoseringshjälp

## Overview

This document describes the comprehensive test suite for the Anestesidoseringshjälp application using **Playwright** for end-to-end testing of the Streamlit application.

## Quick Start

```bash
# Windows
run_tests.bat

# Linux/Mac
chmod +x run_tests.sh
./run_tests.sh
```

## Playwright Test Suites

This application includes comprehensive Playwright test suites to validate all UI functionality.

### Prerequisites

```bash
pip install playwright
python -m playwright install chromium
```

### Test Files

#### 1. **test_ui_light.py** - Quick Smoke Test
Tests basic app functionality without authentication.

**What it tests:**
- App starts without errors
- Login page loads correctly
- All basic UI elements are present

**Run it:**
```bash
# Start the app first
streamlit run oxydos_v8.py --server.headless true --server.port 8501 &

# Run the test
python test_ui_light.py
```

**Expected output:**
```
[OK] App loaded successfully
[OK] Login button - login page is working
[OK] No Python errors detected on page load
```

---

#### 2. **test_full_playwright.py** - Basic Test Suite
Original basic test suite with fundamental feature testing.

**What it tests:**
- Login page (4 tests)
- User authentication (2 tests)
- Main interface tabs (4 tests)
- Patient section (5 tests)
- Procedure section (3 tests)
- Opioid temporal dosing section (4 tests)
- Adjuvant section (7 tests)
- Temporal dose addition (2 tests)
- Dose calculation (1 test)
- History tab navigation (3 tests)
- Error checking (1 test)

**Total: 36 tests**

**Run it:**
```bash
# Start the app first
streamlit run oxydos_v8.py --server.headless true --server.port 8501 &

# Wait for app to start (5 seconds)
sleep 5

# Run the basic test suite
python test_full_playwright.py
```

---

#### 3. **test_comprehensive_playwright.py** - COMPREHENSIVE Test Suite (NEW!)
The most complete end-to-end testing suite with 15 test categories covering ALL features.

**What it tests:**
1. **Login Page Structure** - All login elements and help text
2. **User Authentication** - Login flow, user creation, logout
3. **Main Interface Elements** - All tabs and navigation
4. **Patient Section** - All input fields and checkboxes
5. **Procedure Section** - Specialty, procedure, surgery type selection
6. **Temporal Dosing** - Add/delete opioid doses with timing
7. **Adjuvant Section** - All adjuvant medications and checkboxes
8. **Calculation Engine** - Full dose calculation with real data
9. **Logging Section** - VAS, rescue timing, postop data, respiratory status
10. **History Tab** - Case list, filtering, editing, Excel export
11. **Learning Tab** - ML status, calibration factors, statistics
12. **Procedures Tab** - Procedure management and access control
13. **Error Detection** - Scan for errors and exceptions
14. **Admin Features** - Admin login, user management, ML settings, system status
15. **Responsive Layout** - Viewport sizing and scroll behavior

**Total: 95+ comprehensive tests**

**Features:**
- Auto-screenshot capture for each test suite
- Detailed pass/fail reporting with colors
- Configurable timeouts and browser settings
- Support for both headless and headed modes
- Test result summaries with timing

**Run it:**
```bash
# Quick run with scripts (recommended)
run_tests.bat  # Windows
./run_tests.sh # Linux/Mac

# Or manually
streamlit run oxydos_v8.py &
sleep 10
python test_comprehensive_playwright.py
```

**Configuration:**
Edit the `TestConfig` class in the file to customize:
- Base URL
- Timeouts
- Test credentials
- Headless mode
- Browser slow-mo speed

---

### Authentication for Full Testing

The app requires valid user credentials. There are two ways to run full authenticated tests:

#### Option A: Create a test user first
1. Open the app manually: `streamlit run oxydos_v8.py`
2. Create a user account (e.g., TEST_USER)
3. Note the username and password
4. Update `test_full_playwright.py` line 79 with your test user credentials

#### Option B: Use admin credentials
If you have admin access, you can modify the test to use admin credentials.

---

### Test Output

The tests generate screenshots for debugging:
- `test_screenshot.png` - Current state during light test
- `test_after_login.png` - State after login attempt
- `test_final_state.png` - Final state of full test suite
- `test_error_state.png` - Error state (if tests crash)

---

### Test Summary Example

```
============================================================
TEST SUMMARY
============================================================
Total Tests: 36
Passed: 34 (94.4%)
Failed: 2
Warnings: 0
============================================================
```

---

### Continuous Integration

To integrate with CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Install Playwright
  run: |
    pip install playwright
    python -m playwright install chromium

- name: Start Streamlit App
  run: streamlit run oxydos_v8.py --server.headless true --server.port 8501 &

- name: Wait for App
  run: sleep 10

- name: Run Tests
  run: python test_full_playwright.py
```

---

### Test Coverage

Current test coverage includes:

✅ **UI Elements**
- All patient input fields
- Procedure selection dropdowns
- Temporal opioid dosing interface
- Adjuvant medication controls
- History and statistics display

✅ **Recent UI Changes Validated**
- "Låg smärttröskel" checkbox (updated label)
- "GFR <35" checkbox (updated from GFR <50)
- "Dosering & Dosrekommendation" tab name
- Compact dropdowns (halved width)
- Opioid section with Timmar/Minuter fields
- Infiltration checkbox repositioned between Droperidol and Sevo
- Light blue background for temporal doses

✅ **Error Detection**
- No Python exceptions on page load
- No Streamlit errors in console
- Proper authentication flow

---

### Troubleshooting

**Test fails with "Connection refused"**
- Make sure Streamlit app is running first
- Check port 8501 is not blocked
- Wait longer for app to start (increase sleep time)

**Authentication tests fail**
- Create a test user manually first
- Or update test credentials to use existing user

**Screenshots show blank page**
- Increase wait timeouts in test file
- Streamlit may be slow to render in headless mode

---

### Manual Testing Checklist

For features not covered by automated tests:

- [ ] Add multiple temporal opioid doses
- [ ] Verify color-coded temporal doses (light blue)
- [ ] Test dose calculation with various inputs
- [ ] Save a case and verify it appears in history
- [ ] Export history to Excel
- [ ] Test ML model predictions
- [ ] Verify 3D pain scoring
- [ ] Test edit functionality on saved cases
- [ ] Verify temporal dose pharmacokinetics calculations

---

## Notes

- Tests run in headless Chrome browser
- All tests are non-destructive (read-only)
- Tests do not modify the database
- Estimated run time: 30-60 seconds for full suite
