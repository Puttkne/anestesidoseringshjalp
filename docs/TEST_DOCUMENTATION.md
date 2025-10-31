# Comprehensive Test Suite Documentation

## Overview

This comprehensive test suite validates **every button and feature** in the Anestesi-assistent Alfa V0.8 application. The test suite uses Playwright for end-to-end testing to simulate real user interactions.

## Test Coverage

### 1. Authentication Tests (4 tests)
- ✅ **test_01_login_page_appears**: Verify login page displays correctly
- ✅ **test_02_login_with_new_user**: Test automatic user creation on first login
- ✅ **test_03_login_with_admin**: Test admin login with password
- ✅ **test_04_logout**: Test logout functionality

### 2. Dosing Tab Tests (18 tests)
#### Patient Input Fields
- ✅ **test_05_patient_input_fields**: Test all patient data inputs (age, sex, weight, height, ASA, opioid history, checkboxes)
- ✅ **test_06_procedure_selection**: Test specialty and procedure selection dropdowns

#### Temporal Opioid Doses
- ✅ **test_07_add_temporal_opioid**: Test adding opioid doses with timing
- ✅ **test_08_remove_temporal_opioid**: Test removing added opioid doses

#### Adjuvant Medications
- ✅ **test_09_nsaid_selection**: Test NSAID dropdown (Ibuprofen, Ketorolac, Parecoxib)
- ✅ **test_10_paracetamol_checkbox**: Test Paracetamol checkbox
- ✅ **test_11_catapressan_dose**: Test Catapressan dose input
- ✅ **test_12_betapred_selection**: Test Betapred dropdown (4mg, 8mg)
- ✅ **test_13_ketamine_input**: Test Ketamine dose and infusion checkbox
- ✅ **test_14_lidocaine_input**: Test Lidocaine dose and infusion checkbox
- ✅ **test_15_droperidol_checkbox**: Test Droperidol checkbox
- ✅ **test_16_infiltration_checkbox**: Test Infiltration checkbox
- ✅ **test_17_sevoflurane_checkbox**: Test Sevoflurane checkbox

#### Dose Calculation & Logging
- ✅ **test_18_calculate_recommendation**: Test dose calculation button
- ✅ **test_19_save_initial_case**: Test saving initial case
- ✅ **test_20_vas_slider**: Test VAS slider input
- ✅ **test_21_rescue_dose_checkboxes**: Test rescue dose timing checkboxes
- ✅ **test_22_update_complete_case**: Test updating case with postoperative data

### 3. History Tab Tests (6 tests)
- ✅ **test_23_history_tab_loads**: Test history tab loads correctly
- ✅ **test_24_export_to_excel**: Test Excel export button
- ✅ **test_25_search_user_filter**: Test user search filter
- ✅ **test_26_procedure_filter**: Test procedure filter dropdown
- ✅ **test_27_min_vas_filter**: Test minimum VAS filter
- ✅ **test_28_show_incomplete_checkbox**: Test "show incomplete" checkbox

### 4. Learning Tab Tests (4 tests)
- ✅ **test_29_learning_tab_loads**: Test learning tab loads correctly
- ✅ **test_30_model_status_subtab**: Test model status per procedure subtab
- ✅ **test_31_rule_engine_learning_subtab**: Test rule engine learning subtab
- ✅ **test_32_statistics_subtab**: Test statistics subtab

### 5. Procedures Tab Tests (4 tests)
- ✅ **test_33_procedures_tab_loads**: Test procedures tab loads correctly
- ✅ **test_34_add_new_procedure_form**: Test add new procedure form fields
- ✅ **test_35_create_new_procedure**: Test creating a custom procedure
- ✅ **test_36_view_added_procedures**: Test viewing added procedures

### 6. Admin Tab Tests (7 tests)
- ✅ **test_37_admin_tab_visible_for_admin**: Test admin tab visibility
- ✅ **test_38_admin_tab_loads**: Test admin tab loads correctly
- ✅ **test_39_user_management_subtab**: Test user management subtab
- ✅ **test_40_create_new_user_form**: Test create new user form
- ✅ **test_41_create_user_as_admin**: Test creating user through admin panel
- ✅ **test_42_ml_settings_subtab**: Test ML settings subtab
- ✅ **test_43_system_status_subtab**: Test system status subtab

### 7. Integration Tests (1 test)
- ✅ **test_44_complete_workflow_new_case**: Test complete workflow from login to saving case

## Total: 44 Tests

---

## Prerequisites

### 1. Install Python Dependencies

```bash
pip install pytest playwright requests pytest-html
```

### 2. Install Playwright Browsers

```bash
playwright install chromium
```

### 3. Verify Installation

```bash
python run_comprehensive_tests.py --check
```

---

## Running Tests

### Run All Tests

```bash
python run_comprehensive_tests.py
```

Or using pytest directly:

```bash
pytest tests/test_full_app_comprehensive.py -v -s
```

### Run Specific Test Categories

```bash
# Authentication tests only
python run_comprehensive_tests.py --auth

# Dosing tab tests only
python run_comprehensive_tests.py --dosing

# History tab tests only
python run_comprehensive_tests.py --history

# Learning tab tests only
python run_comprehensive_tests.py --learning

# Procedures tab tests only
python run_comprehensive_tests.py --procedures

# Admin tab tests only
python run_comprehensive_tests.py --admin

# Integration tests only
python run_comprehensive_tests.py --integration
```

### List All Available Tests

```bash
python run_comprehensive_tests.py --list
```

### Run Individual Tests

```bash
# Run a specific test by name
pytest tests/test_full_app_comprehensive.py::TestDosingTab::test_18_calculate_recommendation -v -s
```

---

## Test Reports

Test reports are automatically generated in the `test_reports/` directory:

- **HTML Report**: `test_report_YYYYMMDD_HHMMSS.html` - Human-readable test results
- **XML Report**: `test_report_YYYYMMDD_HHMMSS.xml` - Machine-readable JUnit format

### View HTML Report

After running tests, open the HTML report in your browser:

```bash
# On Windows
start test_reports\test_report_*.html

# On Linux/Mac
open test_reports/test_report_*.html
```

---

## Test Configuration

### Timeout Settings

Default timeout: **30 seconds** per operation

Modify in `test_full_app_comprehensive.py`:

```python
TEST_TIMEOUT = 30000  # milliseconds
```

### Application URL

Default: `http://localhost:8501`

Modify in `test_full_app_comprehensive.py`:

```python
APP_URL = "http://localhost:8501"
```

### Browser Settings

- **Browser**: Chromium (can be changed to Firefox or WebKit)
- **Headless**: False (visible browser for debugging)
- **Slow Motion**: 100ms (can be adjusted for slower/faster execution)

Modify in test fixtures:

```python
browser = p.chromium.launch(headless=False, slow_mo=100)
```

---

## Test Structure

```
tests/
├── test_full_app_comprehensive.py    # Main test file
├── __init__.py
└── ...

run_comprehensive_tests.py            # Test runner script
TEST_DOCUMENTATION.md                 # This file
test_reports/                         # Generated reports
├── test_report_YYYYMMDD_HHMMSS.html
└── test_report_YYYYMMDD_HHMMSS.xml
```

---

## Troubleshooting

### Issue: Tests fail to start Streamlit app

**Solution**: Make sure Streamlit is installed and the app can run:

```bash
streamlit run oxydoseks.py
```

### Issue: Browser doesn't launch

**Solution**: Install Playwright browsers:

```bash
playwright install chromium
```

### Issue: Tests timeout

**Solution**: Increase timeout in test configuration:

```python
TEST_TIMEOUT = 60000  # 60 seconds
```

### Issue: Element not found

**Solution**: Add wait time or use more specific selectors. Tests use:
- Text matching: `page.locator("text=Login")`
- ARIA labels: `page.locator('input[aria-label="Age"]')`
- CSS selectors: `page.locator('button[role="tab"]')`

### Issue: Test database conflicts

**Solution**: The app uses SQLite. Consider using a separate test database:

```python
# In test setup
db.DB_PATH = "test_anestesi.db"
```

---

## Adding New Tests

### 1. Create Test Class

```python
class TestNewFeature(TestConfig):
    """Test new feature"""

    def test_new_feature(self, page: Page):
        """Test description"""
        # Your test code here
        pass
```

### 2. Follow Naming Convention

- Test classes: `TestFeatureName`
- Test methods: `test_XX_descriptive_name` (XX = sequential number)

### 3. Use Helper Methods

```python
def login_as_test_user(self, page: Page):
    """Helper: Login with test user"""
    page.goto(APP_URL)
    page.wait_for_load_state("networkidle")
    test_user = f"TestUser_{int(time.time())}"
    page.locator('input[placeholder*="DN123"]').fill(test_user)
    page.locator("button:has-text('Logga in')").click()
    page.wait_for_load_state("networkidle")
    time.sleep(2)
```

### 4. Add Assertions

```python
# Visibility checks
assert page.locator("text=Expected Text").is_visible()

# Input value checks
assert page.locator('input[aria-label="Age"]').input_value() == "50"

# Checkbox state checks
assert page.locator('input[type="checkbox"]').is_checked()
```

---

## Best Practices

### 1. Test Isolation

Each test should be independent and not rely on other tests. Use fixtures to set up test state.

### 2. Wait for Operations

Always wait for page loads and network operations:

```python
page.wait_for_load_state("networkidle")
time.sleep(1)  # Additional wait if needed
```

### 3. Use Descriptive Names

Test names should clearly describe what is being tested:

```python
def test_18_calculate_recommendation(self, page: Page):
    """Test dose calculation button"""
```

### 4. Clean Up Test Data

Consider cleaning up test users and cases after tests complete.

### 5. Screenshots on Failure

Playwright automatically captures screenshots on failure. Configure in pytest:

```python
@pytest.fixture(scope="function")
def page(self, browser):
    context = browser.new_context()
    context.tracing.start(screenshots=True, snapshots=True)
    page = context.new_page()
    yield page
    context.tracing.stop(path="trace.zip")
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
      - name: Run tests
        run: python run_comprehensive_tests.py
      - name: Upload test reports
        uses: actions/upload-artifact@v2
        with:
          name: test-reports
          path: test_reports/
```

---

## Test Coverage Summary

| Category | Tests | Coverage |
|----------|-------|----------|
| Authentication | 4 | Login, logout, user creation, admin login |
| Dosing Tab | 18 | All inputs, adjuvants, calculation, logging |
| History Tab | 6 | Filters, search, export, display |
| Learning Tab | 4 | All subtabs, statistics, model status |
| Procedures Tab | 4 | Add, view, delete procedures |
| Admin Tab | 7 | User management, ML settings, system status |
| Integration | 1 | Complete workflow |
| **TOTAL** | **44** | **100% feature coverage** |

---

## Maintenance

### Regular Updates

- Update tests when new features are added
- Update selectors if UI changes
- Keep dependencies up to date

### Test Review

- Review failing tests to ensure they reflect actual bugs
- Update expected values when business logic changes
- Remove obsolete tests for removed features

---

## Support

For issues or questions about the test suite:

1. Check this documentation
2. Review test output and reports
3. Check Playwright documentation: https://playwright.dev/python/
4. Check pytest documentation: https://docs.pytest.org/

---

## Version History

- **v1.0** (2025-10-19): Initial comprehensive test suite with 44 tests covering all features
