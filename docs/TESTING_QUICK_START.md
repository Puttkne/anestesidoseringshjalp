# Testing Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### Step 1: Install Test Dependencies

```bash
pip install -r test_requirements.txt
```

### Step 2: Install Playwright Browsers

```bash
playwright install chromium
```

### Step 3: Verify Setup

```bash
python run_comprehensive_tests.py --check
```

---

## 🏃 Run Tests

### Run Everything

```bash
python run_comprehensive_tests.py
```

### Run Specific Tests

```bash
# Just authentication
python run_comprehensive_tests.py --auth

# Just dosing features
python run_comprehensive_tests.py --dosing

# Just history tab
python run_comprehensive_tests.py --history

# Just admin features
python run_comprehensive_tests.py --admin
```

---

## 📊 View Results

Reports are saved in `test_reports/`:

- Open `test_report_*.html` in your browser for detailed results

---

## 🧪 What's Tested?

### ✅ Authentication (4 tests)
- Login page
- New user creation
- Admin login
- Logout

### ✅ Dosing Tab (18 tests)
- All patient input fields
- Procedure selection
- Temporal opioid doses (add/remove)
- All adjuvants (NSAID, Paracetamol, Catapressan, Betapred, Ketamine, Lidocaine, etc.)
- Dose calculation
- Case logging (initial & complete)

### ✅ History Tab (6 tests)
- Export to Excel
- Search/filter functions
- Case display

### ✅ Learning Tab (4 tests)
- Model status
- Rule engine learning
- Statistics

### ✅ Procedures Tab (4 tests)
- Add new procedure
- View procedures
- Form validation

### ✅ Admin Tab (7 tests)
- User management
- ML settings
- System status

### ✅ Integration (1 test)
- Complete workflow end-to-end

### **Total: 44 tests covering every button and feature**

---

## 🐛 Common Issues

### Browser doesn't open?

```bash
playwright install chromium
```

### App doesn't start?

Make sure the app runs normally first:

```bash
streamlit run oxydos_v8.py
```

### Tests timeout?

The app may be slow to load. Tests have 30-second timeouts by default.

---

## 📝 Test Output Example

```
✓ test_01_login_page_appears PASSED
✓ test_02_login_with_new_user PASSED
✓ test_05_patient_input_fields PASSED
✓ test_18_calculate_recommendation PASSED
...
✅ All tests passed! (44/44)
```

---

## 🔧 Advanced Usage

### Run specific test

```bash
pytest tests/test_full_app_comprehensive.py::TestDosingTab::test_18_calculate_recommendation -v
```

### Run tests in parallel (faster)

```bash
pytest tests/test_full_app_comprehensive.py -n 4
```

### Run with detailed output

```bash
pytest tests/test_full_app_comprehensive.py -vv -s
```

---

## 📚 More Info

See [TEST_DOCUMENTATION.md](TEST_DOCUMENTATION.md) for complete documentation.

---

## ✨ That's it!

You now have a comprehensive test suite that validates every button and feature in your application.
