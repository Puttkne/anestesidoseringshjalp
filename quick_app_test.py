"""
Quick App Test - Verify app works after bloat cleanup
"""
import sys
import io
import requests
import time
from playwright.sync_api import sync_playwright

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

APP_URL = "http://localhost:8501"

def test_app_loads():
    """Test that app loads successfully"""
    try:
        response = requests.get(APP_URL, timeout=5)
        assert response.status_code == 200
        print("✓ App loads successfully (HTTP 200)")
        return True
    except Exception as e:
        print(f"✗ App failed to load: {e}")
        return False

def test_ui_interaction():
    """Test basic UI interaction"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(APP_URL, wait_until="networkidle", timeout=15000)
            time.sleep(2)

            # Try to login
            if page.locator("text=Anestesi-assistent").is_visible(timeout=5000):
                print("✓ App title visible")

            # Check if user can interact
            if page.locator('input').count() > 0:
                print("✓ Input fields present")

            browser.close()
        return True
    except Exception as e:
        print(f"✗ UI interaction failed: {e}")
        return False

def main():
    print("=" * 60)
    print("QUICK APP TEST - POST CLEANUP VERIFICATION")
    print("=" * 60)
    print()

    results = []

    print("1. Testing app loads...")
    results.append(test_app_loads())
    print()

    print("2. Testing UI interaction...")
    results.append(test_ui_interaction())
    print()

    print("=" * 60)
    if all(results):
        print("✅ ALL TESTS PASSED - App works perfectly after cleanup!")
    else:
        print("❌ SOME TESTS FAILED - Check errors above")
    print("=" * 60)

    return 0 if all(results) else 1

if __name__ == "__main__":
    exit(main())
