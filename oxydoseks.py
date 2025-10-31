import streamlit as st
import pandas as pd
import logging
from datetime import datetime

# Configure logging at application start
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('anestesi_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import våra nya moduler
import database as db
import auth
import database_backup
from ui.main_layout import render_main_layout
from callbacks import get_current_inputs, handle_save_and_learn
from migrations import run_migrations
from session_manager import cleanup_expired_sessions

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Grundkonfiguration av sidan ---
st.set_page_config(
    page_title="Anestesi-assistent Alfa V0.8",
    page_icon="🤖",
    layout="wide"
)

logger.info("Application started")

# Enhanced dark theme matching new HTML design
load_css("ui/style.css")

# --- Initialisering ---
def initialize_session():
    """Initialize database, auth, and session state."""
    if 'db_initialized' not in st.session_state:
        try:
            db.init_database()
            logger.info("Database initialized")

            # Run migrations and add indexes
            run_migrations()
            logger.info("Migrations completed")

            # Auto-restore from backup if database is empty
            restore_performed = database_backup.auto_restore()
            if restore_performed:
                logger.info("Database restored from backup")
            else:
                logger.info("No restore needed or no backup available")

            # Initialize admin user
            auth.initialize_admin()
            logger.info("Admin initialization completed")

            # Cleanup old sessions
            cleanup_expired_sessions()
            logger.info("Expired sessions cleaned up")

            st.session_state.db_initialized = True
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            st.error(f"Initialization error: {e}")

    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.is_admin = False

    if 'current_calculation' not in st.session_state:
        st.session_state.current_calculation = {}

    if 'editing_case_id' not in st.session_state:
        st.session_state.editing_case_id = None

    if 'load_case_data' not in st.session_state:
        st.session_state.load_case_data = None

initialize_session()

# --- Datainläsning ---
@st.cache_data
def load_procedures():
    all_procs = db.get_all_procedures() + db.get_all_custom_procedures()
    return pd.DataFrame(all_procs), sorted(pd.DataFrame(all_procs)['specialty'].unique())

procedures_df, specialties = load_procedures()

# --- Huvudapplikation ---
def main():
    if not auth.is_logged_in():
        # Login UI
        st.title("🔐 Anestesi-assistent Alfa V0.8 - Inloggning")
        with st.form("login_form"):
            user_id_input = st.text_input("Användar-ID", placeholder="t.ex. DN123")
            password_input = st.text_input("Lösenord", type="password")
            login_btn = st.form_submit_button("Logga in")

            if login_btn and user_id_input and password_input:
                if auth.login_user(user_id_input, password_input):
                    st.rerun()
                else:
                    st.error("Felaktigt användarnamn eller lösenord")
            elif login_btn:
                st.error("Vänligen ange både Användar-ID och Lösenord")
        st.info("💡 Endast behöriga användare kan logga in. Kontakta en administratör för att få ett konto.")
        st.stop()

    # Header - Compact single row layout
    header_col1, header_col2, header_col3 = st.columns([0.3, 0.4, 0.3])

    with header_col2:
        st.markdown('''
            <h1 style="font-size: 2.25rem; font-weight: 700; color: #ffffff; margin: 0; text-align: center;">
                <span style="color: #22d3ee;">Anestesi</span>-assistent
            </h1>
        ''', unsafe_allow_html=True)

    with header_col3:
        user_info_col, logout_col = st.columns([0.7, 0.3])
        with user_info_col:
            st.markdown(f'''
                <div style="text-align: right; padding-top: 0.5rem;">
                    <span style="color: #cbd5e1; font-size: 0.875rem;">
                        👤 <strong>{auth.get_current_username()}</strong>
                        {' | 👑 <span style="color: #22d3ee;">ADMIN</span>' if auth.is_admin() else ''}
                    </span>
                </div>
            ''', unsafe_allow_html=True)
        with logout_col:
            if st.button("Logga ut", key="logout_btn"):
                auth.logout_user()
                st.rerun()

    # Render main layout
    render_main_layout(procedures_df, specialties)

if __name__ == "__main__":
    main()
