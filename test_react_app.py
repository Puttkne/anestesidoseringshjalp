from playwright.sync_api import sync_playwright
import time

def capture_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1280, 'height': 1024})

        try:
            # Navigate to the app
            page.goto('http://localhost:3001', timeout=10000)
            time.sleep(2)

            # Screenshot of login page
            page.screenshot(path='react_login_page.png', full_page=True)
            print("Login page screenshot captured")

            # Login with test user
            page.fill('input[name="username"]', 'DN123')
            page.fill('input[name="password"]', 'test123')
            page.click('button[type="submit"]')
            time.sleep(2)

            # Screenshot of dashboard
            page.screenshot(path='react_dashboard.png', full_page=True)
            print("Dashboard screenshot captured")

            # Fill in some test data
            page.fill('input[type="number"]', '45')
            time.sleep(1)
            page.screenshot(path='react_dashboard_filled.png', full_page=True)
            print("Dashboard with data screenshot captured")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path='react_error.png', full_page=True)
        finally:
            browser.close()

if __name__ == "__main__":
    capture_screenshots()
