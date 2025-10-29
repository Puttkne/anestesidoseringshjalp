import streamlit as st
import auth
from ui.tabs.dosing_tab import render_dosing_tab
from ui.tabs.history_tab import render_history_tab
from ui.tabs.learning_tab import render_learning_tab
from ui.tabs.procedures_tab import render_procedures_tab
from ui.tabs.admin_tab import render_admin_tab

def render_main_layout(procedures_df, specialties):
    # Visa admin-tab endast för admin
    if auth.is_admin():
        main_tabs = st.tabs(["💊 Dosering & Dosrekommendation", "📊 Historik & Statistik", "🧠 Inlärning & Modeller", "➕ Hantera Ingrepp", "🔧 Admin"])
    else:
        main_tabs = st.tabs(["💊 Dosering & Dosrekommendation", "📊 Historik & Statistik", "🧠 Inlärning & Modeller", "➕ Hantera Ingrepp"])

    with main_tabs[0]:
        render_dosing_tab(specialties, procedures_df)

    with main_tabs[1]:
        render_history_tab(procedures_df)

    with main_tabs[2]:
        render_learning_tab(procedures_df)

    with main_tabs[3]:
        render_procedures_tab(specialties)

    # Admin-flik (endast synlig för admin)
    if auth.is_admin() and len(main_tabs) > 4:
        with main_tabs[4]:
            render_admin_tab()
