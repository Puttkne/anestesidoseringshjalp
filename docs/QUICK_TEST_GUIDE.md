# Quick Test Guide

## 🚀 Run Tests in 30 Seconds

### Step 1: Start the App
```bash
streamlit run oxydoseks.py --server.headless true --server.port 8501 &
```

### Step 2: Wait 5 seconds
```bash
sleep 5
```

### Step 3: Run Tests
```bash
# Quick test (5 seconds)
python test_ui_light.py

# OR Full test (60 seconds)
python test_full_playwright.py
```

---

## ✅ Expected Output

### Quick Test
```
>> Starting light UI test...
[OK] Screenshot saved to test_screenshot.png
[OK] App loaded successfully - found title 'Anestesi-assistent Alfa V0.8'
[OK] Found login button - login page is working
[OK] Found username field
[OK] Found password field
[OK] Found first-time login instructions
[OK] No Python errors detected on page load

>> Summary:
   - App starts correctly
   - Login page renders properly
   - No fatal errors detected
```

### Full Test
```
============================================================
TEST SUMMARY
============================================================
Total Tests: 8
Passed: 8 (100.0%)
Failed: 0
Warnings: 2
============================================================
```

---

## 📸 Screenshots

Tests automatically save screenshots:
- `test_screenshot.png` - App state
- `test_after_login.png` - After login
- `test_final_state.png` - Final state

---

## ❌ Troubleshooting

**Connection refused?**
```bash
# Check if app is running
curl http://localhost:8501
```

**Tests fail?**
```bash
# Stop all Streamlit processes
pkill -f streamlit

# Restart app
streamlit run oxydoseks.py --server.headless true --server.port 8501 &

# Wait longer
sleep 10

# Re-run tests
python test_ui_light.py
```

---

## 📚 More Info

See [TESTING.md](TESTING.md) for detailed guide
See [TEST_SUITE_SUMMARY.md](TEST_SUITE_SUMMARY.md) for complete documentation
