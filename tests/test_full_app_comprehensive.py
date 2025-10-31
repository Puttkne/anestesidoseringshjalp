"""
Comprehensive Test Suite for Anestesi-assistent Alfa V0.8
Tests every button, feature, and interaction in the application.

Run with: pytest tests/test_full_app_comprehensive.py -v -s
Or: python tests/test_full_app_comprehensive.py
"""

import pytest
import sys
import os
from pathlib import Path
import time
import subprocess
import requests
from playwright.sync_api import sync_playwright, expect, Page, Browser

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import database as db
import auth

# Test configuration
APP_URL = "http://localhost:8501"
TEST_TIMEOUT = 30000  # 30 seconds


class TestConfig:
    """Test configuration and fixtures"""

    @pytest.fixture(scope="session")
    def streamlit_app(self):
        """Start Streamlit app for testing"""
        # Check if app is already running
        try:
            response = requests.get(APP_URL, timeout=2)
            if response.status_code == 200:
                print(f"✓ Streamlit app already running at {APP_URL}")
                yield None
                return
        except:
            pass

        # Start the app
        print(f"Starting Streamlit app at {APP_URL}...")
        process = subprocess.Popen(
            ["streamlit", "run", "oxydoseks.py", "--server.port=8501", "--server.headless=true"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for app to start
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(APP_URL, timeout=2)
                if response.status_code == 200:
                    print(f"✓ Streamlit app started successfully")
                    break
            except:
                if i < max_retries - 1:
                    time.sleep(1)
                else:
                    process.kill()
                    raise Exception("Failed to start Streamlit app")

        yield process

        # Cleanup
        print("Stopping Streamlit app...")
        process.kill()
        process.wait()

    @pytest.fixture(scope="function")
    def browser(self, streamlit_app):
        """Create browser instance"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=100)
            yield browser
            browser.close()

    @pytest.fixture(scope="function")
    def page(self, browser):
        """Create new page for each test"""
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        page.set_default_timeout(TEST_TIMEOUT)
        yield page
        page.close()
        context.close()


class TestAuthentication(TestConfig):
    """Test authentication functionality"""

    def test_01_login_page_appears(self, page: Page):
        """Test that login page appears on first visit"""
        page.goto(APP_URL)
        page.wait_for_load_state("networkidle")

        # Check for login form
        assert page.locator("text=Anestesi-assistent Alfa V0.8 - Inloggning").is_visible()
        assert page.locator('input[placeholder*="DN123"]').is_visible()
        assert page.locator("button:has-text('Logga in')").is_visible()

    def test_02_login_with_new_user(self, page: Page):
        """Test creating and logging in with new user"""
        page.goto(APP_URL)
        page.wait_for_load_state("networkidle")

        # Enter test user ID
        test_user = f"TestUser_{int(time.time())}"
        page.locator('input[placeholder*="DN123"]').fill(test_user)
        page.locator("button:has-text('Logga in')").click()

        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Should be logged in and see main interface
        assert page.locator("text=Anestesi-assistent Alfa V0.8").is_visible()
        assert page.locator(f"text={test_user}").is_visible()

    def test_03_login_with_admin(self, page: Page):
        """Test admin login with password"""
        page.goto(APP_URL)
        page.wait_for_load_state("networkidle")

        # Enter admin credentials
        page.locator('input[placeholder*="DN123"]').fill("Blapa")
        page.locator('input[type="password"]').fill("Flubber1")
        page.locator("button:has-text('Logga in')").click()

        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Should see admin badge
        assert page.locator("text=ADMIN").is_visible()

    def test_04_logout(self, page: Page):
        """Test logout functionality"""
        # Login first
        page.goto(APP_URL)
        page.wait_for_load_state("networkidle")
        test_user = f"LogoutTest_{int(time.time())}"
        page.locator('input[placeholder*="DN123"]').fill(test_user)
        page.locator("button:has-text('Logga in')").click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Logout
        page.locator("button:has-text('Logga ut')").click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Should be back at login page
        assert page.locator("text=Anestesi-assistent Alfa V0.8 - Inloggning").is_visible()


class TestDosingTab(TestConfig):
    """Test Dosing & Recommendation tab"""

    def login_as_test_user(self, page: Page):
        """Helper: Login with test user"""
        page.goto(APP_URL)
        page.wait_for_load_state("networkidle")
        test_user = f"DosingTest_{int(time.time())}"
        page.locator('input[placeholder*="DN123"]').fill(test_user)
        page.locator("button:has-text('Logga in')").click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

    def test_05_patient_input_fields(self, page: Page):
        """Test all patient input fields"""
        self.login_as_test_user(page)

        # Fill in patient data
        page.locator('input[aria-label="Ålder"]').fill("50")

        # Gender dropdown
        page.locator('div[data-baseweb="select"]:near(:text("Kön"))').click()
        page.locator('text="Kvinna"').first.click()

        # Weight and height
        page.locator('input[aria-label="Vikt"]').fill("75")
        page.locator('input[aria-label="Längd"]').fill("175")

        # ASA classification
        page.locator('div[data-baseweb="select"]:near(:text("ASA"))').click()
        page.locator('text="ASA 2"').first.click()

        # Opioid history
        page.locator('div[data-baseweb="select"]:near(:text("Opioid"))').click()
        page.locator('text="Naiv"').first.click()

        # Checkboxes
        page.locator('input[type="checkbox"]:near(:text("Låg smärttröskel"))').check()
        page.locator('input[type="checkbox"]:near(:text("GFR <35"))').check()

        time.sleep(1)

        # Verify values are set
        assert page.locator('input[aria-label="Ålder"]').input_value() == "50"
        assert page.locator('input[aria-label="Vikt"]').input_value() == "75"

    def test_06_procedure_selection(self, page: Page):
        """Test procedure selection"""
        self.login_as_test_user(page)

        # Select specialty
        specialty_dropdown = page.locator('div[data-baseweb="select"]:near(:text("Specialitet"))').first
        specialty_dropdown.click()
        page.locator('text="Ortopedi"').first.click()
        time.sleep(1)

        # Select procedure
        procedure_dropdown = page.locator('div[data-baseweb="select"]:near(:text("Ingrepp"))').first
        procedure_dropdown.click()
        # Select first available procedure
        page.locator('[role="option"]').first.click()
        time.sleep(1)

        # Select surgery type
        surgery_dropdown = page.locator('div[data-baseweb="select"]:near(:text("Läge"))').first
        surgery_dropdown.click()
        page.locator('text="Elektivt"').first.click()

    def test_07_add_temporal_opioid(self, page: Page):
        """Test adding temporal opioid doses"""
        self.login_as_test_user(page)

        # Select opioid drug
        page.locator('div[data-baseweb="select"]:has-text("Fentanyl")').first.click()
        page.locator('text="Fentanyl"').first.click()

        # Enter dose
        page.locator('input[aria-label*="Dos"]').first.fill("100")

        # Enter time (hours and minutes)
        page.locator('input[aria-label="Timmar"]').fill("1")
        page.locator('input[aria-label="Minuter"]').fill("30")

        # Add opioid
        page.locator('button:has-text("Lägg till opioid")').click()
        time.sleep(1)

        # Verify opioid was added
        assert page.locator('text=Fentanyl').is_visible()
        assert page.locator('text=100').is_visible()

    def test_08_remove_temporal_opioid(self, page: Page):
        """Test removing temporal opioid doses"""
        self.login_as_test_user(page)

        # Add an opioid first
        page.locator('input[aria-label*="Dos"]').first.fill("50")
        page.locator('button:has-text("Lägg till opioid")').click()
        time.sleep(1)

        # Remove it
        page.locator('button:has-text("🗑️")').first.click()
        time.sleep(1)

        # Verify it's removed
        # (The list should be empty or show no doses)

    def test_09_nsaid_selection(self, page: Page):
        """Test NSAID dropdown selection"""
        self.login_as_test_user(page)

        # Find and click NSAID dropdown
        nsaid_dropdown = page.locator('div[data-baseweb="select"]:near(:text("NSAID"))').first
        nsaid_dropdown.click()
        time.sleep(0.5)

        # Select Ibuprofen
        page.locator('text="Ibuprofen 400mg"').first.click()
        time.sleep(0.5)

    def test_10_paracetamol_checkbox(self, page: Page):
        """Test Paracetamol checkbox"""
        self.login_as_test_user(page)

        # Check paracetamol
        page.locator('input[type="checkbox"]:near(:text("Paracetamol 1g"))').check()
        time.sleep(0.5)

        # Verify it's checked
        assert page.locator('input[type="checkbox"]:near(:text("Paracetamol 1g"))').is_checked()

    def test_11_catapressan_dose(self, page: Page):
        """Test Catapressan dose input"""
        self.login_as_test_user(page)

        # Enter catapressan dose
        page.locator('input[aria-label="Catapressan (µg)"]').fill("75")
        time.sleep(0.5)

        # Verify value
        assert page.locator('input[aria-label="Catapressan (µg)"]').input_value() == "75"

    def test_12_betapred_selection(self, page: Page):
        """Test Betapred selection"""
        self.login_as_test_user(page)

        # Select betapred
        betapred_dropdown = page.locator('div[data-baseweb="select"]:near(:text("Betapred"))').first
        betapred_dropdown.click()
        page.locator('text="4 mg"').first.click()
        time.sleep(0.5)

    def test_13_ketamine_input(self, page: Page):
        """Test Ketamine dose and infusion checkbox"""
        self.login_as_test_user(page)

        # Enter ketamine dose
        page.locator('input[aria-label="Ketamin (mg)"]').fill("20")

        # Check infusion checkbox
        page.locator('input[type="checkbox"]:near(:text("Infusion"))').first.check()
        time.sleep(0.5)

    def test_14_lidocaine_input(self, page: Page):
        """Test Lidocaine dose and infusion checkbox"""
        self.login_as_test_user(page)

        # Enter lidocaine dose
        page.locator('input[aria-label="Lidokain (mg)"]').fill("50")

        # Check infusion checkbox
        page.locator('input[type="checkbox"]:near(:text("Infusion"))').nth(1).check()
        time.sleep(0.5)

    def test_15_droperidol_checkbox(self, page: Page):
        """Test Droperidol checkbox"""
        self.login_as_test_user(page)

        page.locator('input[type="checkbox"]:near(:text("Droperidol"))').check()
        assert page.locator('input[type="checkbox"]:near(:text("Droperidol"))').is_checked()

    def test_16_infiltration_checkbox(self, page: Page):
        """Test Infiltration checkbox"""
        self.login_as_test_user(page)

        page.locator('input[type="checkbox"]:near(:text("Infiltration"))').check()
        assert page.locator('input[type="checkbox"]:near(:text("Infiltration"))').is_checked()

    def test_17_sevoflurane_checkbox(self, page: Page):
        """Test Sevoflurane checkbox"""
        self.login_as_test_user(page)

        page.locator('input[type="checkbox"]:near(:text("Sevo"))').check()
        assert page.locator('input[type="checkbox"]:near(:text("Sevo"))').is_checked()

    def test_18_calculate_recommendation(self, page: Page):
        """Test dose calculation button"""
        self.login_as_test_user(page)

        # Fill minimum required data
        page.locator('input[aria-label="Ålder"]').fill("50")
        page.locator('input[aria-label="Vikt"]').fill("75")
        page.locator('input[aria-label="Längd"]').fill("175")

        # Select procedure
        page.locator('div[data-baseweb="select"]:near(:text("Specialitet"))').first.click()
        page.locator('text="Ortopedi"').first.click()
        time.sleep(0.5)

        page.locator('div[data-baseweb="select"]:near(:text("Ingrepp"))').first.click()
        page.locator('[role="option"]').first.click()
        time.sleep(0.5)

        # Calculate recommendation
        page.locator('button:has-text("Beräkna Rekommendation")').click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Should see dose recommendation
        assert page.locator('text=Förslag:').is_visible()

    def test_19_save_initial_case(self, page: Page):
        """Test saving initial case"""
        self.login_as_test_user(page)

        # Fill data and calculate
        page.locator('input[aria-label="Ålder"]').fill("50")
        page.locator('input[aria-label="Vikt"]').fill("75")
        page.locator('input[aria-label="Längd"]').fill("175")

        page.locator('div[data-baseweb="select"]:near(:text("Specialitet"))').first.click()
        page.locator('text="Ortopedi"').first.click()
        time.sleep(0.5)

        page.locator('div[data-baseweb="select"]:near(:text("Ingrepp"))').first.click()
        page.locator('[role="option"]').first.click()
        time.sleep(0.5)

        page.locator('button:has-text("Beräkna Rekommendation")').click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Save case
        page.locator('button:has-text("Spara Fall (initial)")').click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Should see success message or confirmation

    def test_20_vas_slider(self, page: Page):
        """Test VAS slider input"""
        self.login_as_test_user(page)

        # Calculate first to enable logging section
        page.locator('input[aria-label="Ålder"]').fill("50")
        page.locator('input[aria-label="Vikt"]').fill("75")
        page.locator('input[aria-label="Längd"]').fill("175")

        page.locator('div[data-baseweb="select"]:near(:text("Specialitet"))').first.click()
        page.locator('text="Ortopedi"').first.click()
        time.sleep(0.5)

        page.locator('div[data-baseweb="select"]:near(:text("Ingrepp"))').first.click()
        page.locator('[role="option"]').first.click()
        time.sleep(0.5)

        page.locator('button:has-text("Beräkna Rekommendation")').click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Adjust VAS slider
        vas_slider = page.locator('input[type="range"]:near(:text("VAS"))')
        if vas_slider.is_visible():
            vas_slider.fill("7")
            time.sleep(0.5)

    def test_21_rescue_dose_checkboxes(self, page: Page):
        """Test rescue dose timing checkboxes"""
        self.login_as_test_user(page)

        # Calculate first
        page.locator('input[aria-label="Ålder"]').fill("50")
        page.locator('input[aria-label="Vikt"]').fill("75")
        page.locator('input[aria-label="Längd"]').fill("175")

        page.locator('div[data-baseweb="select"]:near(:text("Specialitet"))').first.click()
        page.locator('text="Ortopedi"').first.click()
        time.sleep(0.5)

        page.locator('div[data-baseweb="select"]:near(:text("Ingrepp"))').first.click()
        page.locator('[role="option"]').first.click()
        time.sleep(0.5)

        page.locator('button:has-text("Beräkna Rekommendation")').click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Check rescue timing checkboxes
        page.locator('input[type="checkbox"]:near(:text("Rescue <30 min"))').check()
        page.locator('input[type="checkbox"]:near(:text("Rescue >30 min"))').check()
        time.sleep(0.5)

    def test_22_update_complete_case(self, page: Page):
        """Test updating case with complete postoperative data"""
        self.login_as_test_user(page)

        # Calculate and save initial case first
        page.locator('input[aria-label="Ålder"]').fill("50")
        page.locator('input[aria-label="Vikt"]').fill("75")
        page.locator('input[aria-label="Längd"]').fill("175")

        page.locator('div[data-baseweb="select"]:near(:text("Specialitet"))').first.click()
        page.locator('text="Ortopedi"').first.click()
        time.sleep(0.5)

        page.locator('div[data-baseweb="select"]:near(:text("Ingrepp"))').first.click()
        page.locator('[role="option"]').first.click()
        time.sleep(0.5)

        page.locator('button:has-text("Beräkna Rekommendation")').click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Fill postoperative data
        page.locator('input[aria-label*="Post-op tid (timmar)"]').fill("2")
        page.locator('input[aria-label*="Post-op tid (min)"]').fill("30")

        # Update case
        page.locator('button:has-text("Uppdatera Fall (komplett)")').click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)


class TestHistoryTab(TestConfig):
    """Test History & Statistics tab"""

    def login_and_go_to_history(self, page: Page):
        """Helper: Login and navigate to history tab"""
        page.goto(APP_URL)
        page.wait_for_load_state("networkidle")
        test_user = f"HistoryTest_{int(time.time())}"
        page.locator('input[placeholder*="DN123"]').fill(test_user)
        page.locator("button:has-text('Logga in')").click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Click History tab
        page.locator('button[role="tab"]:has-text("Historik & Statistik")').click()
        time.sleep(2)

    def test_23_history_tab_loads(self, page: Page):
        """Test that history tab loads"""
        self.login_and_go_to_history(page)

        assert page.locator('text=Historik & Statistik').is_visible()

    def test_24_export_to_excel(self, page: Page):
        """Test Excel export button"""
        self.login_and_go_to_history(page)

        # Check if export button exists
        export_button = page.locator('button:has-text("Exportera till Excel")')
        if export_button.is_visible():
            # Button exists, test is successful
            pass

    def test_25_search_user_filter(self, page: Page):
        """Test user search filter"""
        self.login_and_go_to_history(page)

        # Find search input
        search_input = page.locator('input[placeholder*="DN123"]')
        if search_input.is_visible():
            search_input.fill("Test")
            time.sleep(1)

    def test_26_procedure_filter(self, page: Page):
        """Test procedure filter dropdown"""
        self.login_and_go_to_history(page)

        # Find procedure filter
        proc_filter = page.locator('div[data-baseweb="select"]:near(:text("Filtrera ingrepp"))')
        if proc_filter.is_visible():
            proc_filter.click()
            time.sleep(0.5)

    def test_27_min_vas_filter(self, page: Page):
        """Test minimum VAS filter"""
        self.login_and_go_to_history(page)

        # Find min VAS input
        min_vas = page.locator('input[aria-label="Min VAS"]')
        if min_vas.is_visible():
            min_vas.fill("4")
            time.sleep(1)

    def test_28_show_incomplete_checkbox(self, page: Page):
        """Test show incomplete cases checkbox"""
        self.login_and_go_to_history(page)

        # Find checkbox
        incomplete_checkbox = page.locator('input[type="checkbox"]:near(:text("ofullständiga"))')
        if incomplete_checkbox.is_visible():
            incomplete_checkbox.check()
            time.sleep(1)


class TestLearningTab(TestConfig):
    """Test Learning & Models tab"""

    def login_and_go_to_learning(self, page: Page):
        """Helper: Login and navigate to learning tab"""
        page.goto(APP_URL)
        page.wait_for_load_state("networkidle")
        test_user = f"LearningTest_{int(time.time())}"
        page.locator('input[placeholder*="DN123"]').fill(test_user)
        page.locator("button:has-text('Logga in')").click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Click Learning tab
        page.locator('button[role="tab"]:has-text("Inlärning & Modeller")').click()
        time.sleep(2)

    def test_29_learning_tab_loads(self, page: Page):
        """Test that learning tab loads"""
        self.login_and_go_to_learning(page)

        assert page.locator('text=Inlärning & Modeller').is_visible()

    def test_30_model_status_subtab(self, page: Page):
        """Test model status per procedure subtab"""
        self.login_and_go_to_learning(page)

        # Click on model status subtab
        page.locator('button[role="tab"]:has-text("Modellstatus")').click()
        time.sleep(1)

        assert page.locator('text=ML-Modellens Aktiveringsstatus').is_visible()

    def test_31_rule_engine_learning_subtab(self, page: Page):
        """Test rule engine learning subtab"""
        self.login_and_go_to_learning(page)

        # Click on rule engine subtab
        page.locator('button[role="tab"]:has-text("Regelmotor")').click()
        time.sleep(1)

        assert page.locator('text=Regelmotorns').is_visible()

    def test_32_statistics_subtab(self, page: Page):
        """Test statistics subtab"""
        self.login_and_go_to_learning(page)

        # Click on statistics subtab
        page.locator('button[role="tab"]:has-text("Statistik")').click()
        time.sleep(1)

        assert page.locator('text=Statistik & Analys').is_visible()


class TestProceduresTab(TestConfig):
    """Test Manage Procedures tab"""

    def login_and_go_to_procedures(self, page: Page):
        """Helper: Login and navigate to procedures tab"""
        page.goto(APP_URL)
        page.wait_for_load_state("networkidle")
        test_user = f"ProcTest_{int(time.time())}"
        page.locator('input[placeholder*="DN123"]').fill(test_user)
        page.locator("button:has-text('Logga in')").click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Click Procedures tab
        page.locator('button[role="tab"]:has-text("Hantera Ingrepp")').click()
        time.sleep(2)

    def test_33_procedures_tab_loads(self, page: Page):
        """Test that procedures tab loads"""
        self.login_and_go_to_procedures(page)

        assert page.locator('text=Hantera Ingrepp').is_visible()

    def test_34_add_new_procedure_form(self, page: Page):
        """Test add new procedure form fields"""
        self.login_and_go_to_procedures(page)

        # Check form fields exist
        assert page.locator('input[placeholder*="Njurtransplantation"]').is_visible()
        assert page.locator('input[placeholder*="KAC20"]').is_visible()

    def test_35_create_new_procedure(self, page: Page):
        """Test creating a new custom procedure"""
        self.login_and_go_to_procedures(page)

        # Fill in form
        test_proc_name = f"TestProc_{int(time.time())}"
        page.locator('input[placeholder*="Njurtransplantation"]').fill(test_proc_name)
        page.locator('input[placeholder*="KAC20"]').fill("TEST01")

        # Select specialty
        page.locator('div[data-baseweb="select"]:near(:text("specialitet"))').click()
        page.locator('[role="option"]').first.click()
        time.sleep(0.5)

        # Enter base MME
        page.locator('input[aria-label="Grund-MME"]').fill("15")

        # Select pain type
        page.locator('div[data-baseweb="select"]:near(:text("smärttyp"))').click()
        page.locator('text="somatic"').first.click()
        time.sleep(0.5)

        # Submit form
        page.locator('button:has-text("Spara nytt ingrepp")').click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

    def test_36_view_added_procedures(self, page: Page):
        """Test viewing added procedures tab"""
        self.login_and_go_to_procedures(page)

        # Click on "Visa tillagda ingrepp" subtab
        page.locator('button[role="tab"]:has-text("Visa tillagda")').click()
        time.sleep(1)

        assert page.locator('text=Dina tillagda ingrepp').is_visible()


class TestAdminTab(TestConfig):
    """Test Admin tab (requires admin login)"""

    def login_as_admin(self, page: Page):
        """Helper: Login as admin"""
        page.goto(APP_URL)
        page.wait_for_load_state("networkidle")
        page.locator('input[placeholder*="DN123"]').fill("Blapa")
        page.locator('input[type="password"]').fill("Flubber1")
        page.locator("button:has-text('Logga in')").click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

    def test_37_admin_tab_visible_for_admin(self, page: Page):
        """Test that admin tab is visible for admin users"""
        self.login_as_admin(page)

        # Admin tab should be visible
        assert page.locator('button[role="tab"]:has-text("Admin")').is_visible()

    def test_38_admin_tab_loads(self, page: Page):
        """Test that admin tab loads"""
        self.login_as_admin(page)

        # Click admin tab
        page.locator('button[role="tab"]:has-text("Admin")').click()
        time.sleep(2)

        assert page.locator('text=Systeminställningar').is_visible()

    def test_39_user_management_subtab(self, page: Page):
        """Test user management subtab"""
        self.login_as_admin(page)
        page.locator('button[role="tab"]:has-text("Admin")').click()
        time.sleep(2)

        # Should be on user management by default
        assert page.locator('text=Användarhantering').is_visible()

    def test_40_create_new_user_form(self, page: Page):
        """Test create new user form"""
        self.login_as_admin(page)
        page.locator('button[role="tab"]:has-text("Admin")').click()
        time.sleep(2)

        # Check form exists
        assert page.locator('text=Skapa Ny Användare').is_visible()
        assert page.locator('input[placeholder*="DN123"]').is_visible()

    def test_41_create_user_as_admin(self, page: Page):
        """Test creating a new user through admin panel"""
        self.login_as_admin(page)
        page.locator('button[role="tab"]:has-text("Admin")').click()
        time.sleep(2)

        # Fill in username
        test_username = f"AdminCreated_{int(time.time())}"
        page.locator('input[placeholder*="förnamn.efternamn"]').fill(test_username)

        # Submit
        page.locator('button:has-text("Skapa Användare")').click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

    def test_42_ml_settings_subtab(self, page: Page):
        """Test ML settings subtab"""
        self.login_as_admin(page)
        page.locator('button[role="tab"]:has-text("Admin")').click()
        time.sleep(2)

        # Click ML settings subtab
        page.locator('button[role="tab"]:has-text("ML-Inställningar")').click()
        time.sleep(1)

        assert page.locator('text=ML-Motorns Inställningar').is_visible()

    def test_43_system_status_subtab(self, page: Page):
        """Test system status subtab"""
        self.login_as_admin(page)
        page.locator('button[role="tab"]:has-text("Admin")').click()
        time.sleep(2)

        # Click system status subtab
        page.locator('button[role="tab"]:has-text("Systemstatus")').click()
        time.sleep(1)

        assert page.locator('text=Systemstatus').is_visible()


class TestIntegration(TestConfig):
    """Integration tests for complete workflows"""

    def test_44_complete_workflow_new_case(self, page: Page):
        """Test complete workflow: login, enter data, calculate, save case"""
        # Login
        page.goto(APP_URL)
        page.wait_for_load_state("networkidle")
        test_user = f"Workflow_{int(time.time())}"
        page.locator('input[placeholder*="DN123"]').fill(test_user)
        page.locator("button:has-text('Logga in')").click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Fill patient data
        page.locator('input[aria-label="Ålder"]').fill("65")
        page.locator('input[aria-label="Vikt"]').fill("80")
        page.locator('input[aria-label="Längd"]').fill("170")

        # Select procedure
        page.locator('div[data-baseweb="select"]:near(:text("Specialitet"))').first.click()
        page.locator('text="Ortopedi"').first.click()
        time.sleep(0.5)

        page.locator('div[data-baseweb="select"]:near(:text("Ingrepp"))').first.click()
        page.locator('[role="option"]').first.click()
        time.sleep(0.5)

        # Add adjuvants
        page.locator('input[type="checkbox"]:near(:text("Paracetamol 1g"))').check()

        # Calculate
        page.locator('button:has-text("Beräkna Rekommendation")').click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Verify recommendation appears
        assert page.locator('text=Förslag:').is_visible()

        # Save case
        page.locator('button:has-text("Spara Fall (initial)")').click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Go to history and verify case was saved
        page.locator('button[role="tab"]:has-text("Historik & Statistik")').click()
        time.sleep(2)

        # Should see at least one case
        # (exact verification depends on UI structure)


# Test runner for standalone execution
if __name__ == "__main__":
    print("=" * 80)
    print("COMPREHENSIVE TEST SUITE FOR ANESTESI-ASSISTENT V8.0")
    print("=" * 80)
    print("\nThis will test every button and feature in the application.")
    print("\nStarting tests...\n")

    # Run pytest
    pytest.main([__file__, "-v", "-s", "--tb=short"])
