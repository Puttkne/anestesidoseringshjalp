import streamlit as st
import bcrypt
import os
import html
from database import get_user_by_username, create_user, get_user_by_id

# Försök ladda .env fil om den finns
try:
    from dotenv import load_dotenv
    load_dotenv()  # Ladda .env fil
except ImportError:
    # python-dotenv ej installerat, använd OS miljövariabler direkt
    pass

def hash_password(password: str) -> str:
    """Hash lösenord med bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verifiera lösenord mot hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def initialize_admin():
    """Skapa admin-konto från miljövariabler eller Streamlit secrets om det inte finns"""
    import logging
    logger = logging.getLogger(__name__)

    # Försök hämta från Streamlit secrets först (för Streamlit Cloud)
    try:
        admin_username = st.secrets.get("admin", {}).get("username", os.getenv('ADMIN_USERNAME'))
        admin_password_hash = st.secrets.get("admin", {}).get("password_hash", None)

        # Om vi har en hash från secrets, använd den direkt
        if admin_username and admin_password_hash:
            admin = get_user_by_username(admin_username)
            if not admin:
                create_user(admin_username, admin_password_hash, is_admin=True)
                logger.info(f"Admin user '{admin_username}' created from Streamlit secrets")
                return
    except:
        pass  # Streamlit secrets inte tillgängliga

    # Annars, hämta från miljövariabler (för lokal utveckling)
    admin_username = os.getenv('ADMIN_USERNAME')
    admin_password = os.getenv('ADMIN_PASSWORD')

    # SÄKERHET: Kräv att credentials finns i miljövariabler eller secrets
    # Inga standardvärden tillåts!
    if admin_username and admin_password:
        admin = get_user_by_username(admin_username)
        if not admin:
            hashed_pwd = hash_password(admin_password)
            create_user(admin_username, hashed_pwd, is_admin=True)
            logger.info(f"Admin user '{admin_username}' created from environment variables")
    else:
        logger.warning("⚠️ No admin credentials found in environment variables or Streamlit secrets!")

def login_user(username: str, password: str = None) -> bool:
    """Logga in användare

    Usernames are case-insensitive (Blapa = blapa = BLAPA)
    Passwords are case-sensitive (Flubber1 != flubber1)

    Args:
        username: Användarnamn (case-insensitive)
        password: Lösenord (case-sensitive)

    Returns:
        True om inloggning lyckades, annars False
    """
    user = get_user_by_username(username)

    if not user:
        return False  # Användaren finns inte

    # Admin-användare MÅSTE ha lösenord
    if user['is_admin']:
        if password and verify_password(password, user['password_hash']):
            st.session_state.user_id = user['id']
            st.session_state.username = user['username']
            st.session_state.is_admin = True
            return True
        else:
            return False # Fel lösenord för admin

    # Vanliga användare (just nu utan lösenord)
    else:
        # Framtidssäkra: Om en vanlig användare HAR ett lösenord, kräv det.
        if user['password_hash']:
             if password and verify_password(password, user['password_hash']):
                st.session_state.user_id = user['id']
                st.session_state.username = user['username']
                st.session_state.is_admin = False
                return True
             else:
                return False # Fel lösenord för vanlig användare
        # Nuvarande logik: Vanlig användare har inget lösenord, så fältet ska vara tomt.
        elif not password:
            st.session_state.user_id = user['id']
            st.session_state.username = user['username']
            st.session_state.is_admin = False
            return True
        else:
            return False # Lösenord angavs för en användare som inte ska ha ett

def logout_user():
    """Logga ut användare"""
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.is_admin = False

def is_logged_in() -> bool:
    """Kontrollera om användare är inloggad"""
    return st.session_state.get('user_id') is not None

def is_admin() -> bool:
    """Kontrollera om användare är admin"""
    return st.session_state.get('is_admin', False)

def can_edit_case(case_user_id: int) -> bool:
    """Kontrollera om användare kan redigera ett fall

    Args:
        case_user_id: ID för användaren som skapade fallet

    Returns:
        True om användaren kan redigera, annars False
    """
    if not is_logged_in():
        return False

    # Admin kan redigera allt
    if is_admin():
        return True

    # Vanlig användare kan bara redigera egna fall
    return st.session_state.user_id == case_user_id

def can_delete_case(case_user_id: int) -> bool:
    """Kontrollera om användare kan radera ett fall

    Args:
        case_user_id: ID för användaren som skapade fallet

    Returns:
        True om användaren kan radera, annars False
    """
    return can_edit_case(case_user_id)  # Samma regler som för redigering

def get_current_user_id() -> int:
    """Hämta nuvarande användar-ID"""
    return st.session_state.get('user_id')

def get_current_username() -> str:
    """Hämta nuvarande användarnamn"""
    return html.escape(st.session_state.get('username', ''))
