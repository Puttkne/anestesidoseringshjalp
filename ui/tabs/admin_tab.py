import streamlit as st
import database as db
import auth
from config import APP_CONFIG

def render_admin_tab():
    """Admin-flik för användarhantering och systeminställningar"""
    if not auth.is_admin():
        st.error("⛔ Endast admin har åtkomst till denna sida.")
        return

    st.header("🔧 Admin - Systeminställningar")

    admin_tabs = st.tabs(["👥 Användarhantering", "⚙️ ML-Inställningar", "📊 Systemstatus"])

    # ========== TAB 1: ANVÄNDARHANTERING ==========
    with admin_tabs[0]:
        st.subheader("👥 Användarhantering")

        # Lista alla användare
        all_users = db.get_all_users()

        if all_users:
            st.markdown(f"**Totalt {len(all_users)} användare i systemet**")

            for user in all_users:
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

                with col1:
                    admin_badge = "👑 Admin" if user['is_admin'] else "👤 Användare"
                    st.text(f"{user['username']} ({admin_badge})")

                with col2:
                    # Räkna antal fall för användaren
                    user_cases = db.get_all_cases(user['id'])
                    st.text(f"📊 {len(user_cases)} fall")

                with col3:
                    if user['is_admin']:
                        st.text("🔒")
                    else:
                        # Bara vanliga användare kan raderas
                        if st.button("🗑️", key=f"delete_user_{user['id']}", help="Radera användare"):
                            st.session_state[f'confirm_delete_user_{user["id"]}'] = True

                with col4:
                    st.text(f"ID: {user['id']}")

                # Bekräftelsedialog för radering
                if st.session_state.get(f'confirm_delete_user_{user["id"]}', False):
                    st.warning(f"⚠️ Vill du verkligen radera **{user['username']}**?")
                    col_confirm1, col_confirm2 = st.columns(2)
                    with col_confirm1:
                        if st.button("✅ Ja, radera", key=f"confirm_yes_{user['id']}", use_container_width=True):
                            # Radera användarens fall och kalibreringsfaktorer först
                            user_cases = db.get_all_cases(user['id'])
                            for case in user_cases:
                                db.delete_case(case['id'])

                            # Radera användaren
                            db.delete_user(user['id'])

                            st.success(f"✅ Användare {user['username']} har raderats!")
                            st.session_state[f'confirm_delete_user_{user["id"]}'] = False
                            st.rerun()

                    with col_confirm2:
                        if st.button("❌ Avbryt", key=f"confirm_no_{user['id']}", use_container_width=True):
                            st.session_state[f'confirm_delete_user_{user["id"]}'] = False
                            st.rerun()

                st.divider()
        else:
            st.info("Inga användare hittades (förutom admin).")

        # Skapa ny användare
        st.subheader("➕ Skapa Ny Användare")
        st.markdown("Alla nya användare måste tilldelas ett lösenord.")

        with st.form("create_user_form"):
            new_username = st.text_input(
                "Användarnamn",
                placeholder="t.ex. DN123 eller förnamn.efternamn",
                help="Användarnamnet används för att logga in"
            )
            new_password = st.text_input("Lösenord", type="password")

            create_as_admin = st.checkbox(
                "Skapa som admin",
                value=False,
                help="Admin kan hantera användare och systeminställningar"
            )

            submitted = st.form_submit_button("➕ Skapa Användare", type="primary")

            if submitted:
                if not new_username or len(new_username) < 2:
                    st.error("❌ Användarnamn måste vara minst 2 tecken långt")
                elif not new_password or len(new_password) < 6:
                    st.error("❌ Lösenord måste vara minst 6 tecken långt")
                elif db.get_user_by_username(new_username):
                    st.error(f"❌ Användare '{new_username}' finns redan")
                else:
                    # Skapa användare med hashat lösenord
                    hashed_pwd = auth.hash_password(new_password)
                    user_id = db.create_user(
                        username=new_username,
                        password_hash=hashed_pwd,
                        is_admin=create_as_admin
                    )

                    if user_id:
                        admin_text = "admin" if create_as_admin else "användare"
                        st.success(f"✅ {admin_text.capitalize()} '{new_username}' har skapats! (ID: {user_id})")
                        st.rerun()
                    else:
                        st.error("❌ Kunde inte skapa användare. Kontrollera loggen.")

    # ========== TAB 2: ML-INSTÄLLNINGAR ==========
    with admin_tabs[1]:
        st.subheader("⚙️ ML-Motorns Inställningar")

        st.markdown("""
        Här kan du justera ML-motorns parametrar. Ändringarna påverkar alla framtida dosberäkningar.
        """)

        # Hämta nuvarande inställningar
        current_ml_target_vas = db.get_setting('ML_TARGET_VAS', APP_CONFIG.get('ML_TARGET_VAS', 1.0)) if hasattr(db, 'get_setting') else APP_CONFIG.get('ML_TARGET_VAS', 1.0)
        current_ml_max_dose = db.get_setting('ML_SAFETY_MAX_DOSE', APP_CONFIG.get('ML_SAFETY_MAX_DOSE', 20.0)) if hasattr(db, 'get_setting') else APP_CONFIG.get('ML_SAFETY_MAX_DOSE', 20.0)

        col_ml1, col_ml2 = st.columns(2)

        with col_ml1:
            st.markdown("#### 🎯 Mål-VAS för ML")
            st.caption("ML-motorn försöker hitta dosen som når detta VAS-värde")

            ml_target_vas = st.number_input(
                "Mål-VAS",
                min_value=0.0,
                max_value=3.0,
                value=float(current_ml_target_vas),
                step=0.5,
                key='ml_target_vas_input',
                help="Lägre värde = högre doser. Rekommenderat: 1.0-1.5"
            )

            st.caption(f"**Nuvarande:** {current_ml_target_vas}")

        with col_ml2:
            st.markdown("#### 🛡️ Max säkerhetsdos (ML)")
            st.caption("Absolut maxdos som ML-motorn kan föreslå")

            ml_max_dose = st.number_input(
                "Max dos (mg)",
                min_value=10.0,
                max_value=30.0,
                value=float(current_ml_max_dose),
                step=1.0,
                key='ml_max_dose_input',
                help="Säkerhetsgräns för att förhindra extrema doser"
            )

            st.caption(f"**Nuvarande:** {current_ml_max_dose} mg")

        st.divider()

        # Regelmotor-inställningar
        st.markdown("#### 🧠 Regelmotor-inlärning")

        # Hämta nuvarande inställningar för regelmotorn
        current_target_vas = db.get_setting('TARGET_VAS', 3.0)
        current_probe_factor = db.get_setting('DOSE_PROBE_REDUCTION_FACTOR', 0.97)
        current_probe_strength_percent = (1 - current_probe_factor) * 100

        col_rm1, col_rm2 = st.columns(2)
        with col_rm1:
            target_vas = st.number_input(
                "Target VAS (Regelmotor)",
                min_value=0.0,
                max_value=5.0,
                value=float(current_target_vas),
                step=0.5,
                key='rm_target_vas',
                help="Mål-VAS för en 'perfekt' utgång. Systemet kommer att försöka sänka dosen tills detta mål inte längre uppnås."
            )
            st.caption(f"**Nuvarande:** {current_target_vas}")

        with col_rm2:
            probe_strength = st.number_input(
                "Probing-styrka (%)",
                min_value=0.0,
                max_value=20.0,
                value=float(current_probe_strength_percent),
                step=1.0,
                key='rm_probe_strength',
                help="Hur många procent dosen ska sänkas vid varje 'perfekt' utfall för att hitta minimidosen. 0 inaktiverar funktionen."
            )
            st.caption(f"**Nuvarande:** {current_probe_strength_percent:.1f}% (faktor: {current_probe_factor:.3f})")


        if st.button("💾 Spara Inställningar", type="primary"):
            user_id = auth.get_current_user_id()
            if hasattr(db, 'save_setting') and user_id:
                # Spara ML-inställningar
                db.save_setting('ML_TARGET_VAS', ml_target_vas, user_id)
                db.save_setting('ML_SAFETY_MAX_DOSE', ml_max_dose, user_id)

                # Spara Regelmotor-inställningar
                probe_factor = 1 - (probe_strength / 100.0)
                db.save_setting('TARGET_VAS', target_vas, user_id)
                db.save_setting('DOSE_PROBE_REDUCTION_FACTOR', probe_factor, user_id)

                st.success(f"✅ Inställningar sparade!")
                st.rerun()
            else:
                st.warning("⚠️ Spara inställningar misslyckades (kunde inte hämta användar-ID eller databasfunktion saknas).")

        st.divider()

        st.markdown("#### 📋 Alla Systeminställningar")
        if hasattr(db, 'get_all_settings'):
            settings = db.get_all_settings()
            if settings:
                st.dataframe(settings, use_container_width=True)
            else:
                st.info("Inga inställningar sparade ännu.")
        else:
            st.info("get_all_settings() inte implementerad ännu i database.py")

    # ========== TAB 3: SYSTEMSTATUS ==========
    with admin_tabs[2]:
        st.subheader("📊 Systemstatus")

        # Databas stats
        st.markdown("### 💾 Databasstatistik")
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

        all_cases = db.get_all_cases()
        all_users = db.get_all_users()
        all_procs = db.get_all_procedures()
        custom_procs = db.get_all_custom_procedures()

        with col_stat1:
            st.metric("Totalt antal fall", len(all_cases))

        with col_stat2:
            st.metric("Antal användare", len(all_users))

        with col_stat3:
            st.metric("Standard-ingrepp", len(all_procs))

        with col_stat4:
            st.metric("Custom-ingrepp", len(custom_procs))

        st.divider()

        # Config info
        st.markdown("### ⚙️ Aktiv Konfiguration")

        col_cfg1, col_cfg2 = st.columns(2)

        with col_cfg1:
            st.markdown("**Regelmotor:**")
            st.caption(f"• Adjuvant safety limit: {APP_CONFIG['ADJUVANT_SAFETY_LIMIT_FACTOR']}")
            st.caption(f"• Fentanyl halflife fraction: {APP_CONFIG['FENTANYL_HALFLIFE_FRACTION']}")
            st.caption(f"• MME rounding step: {APP_CONFIG['MME_ROUNDING_STEP']}")

        with col_cfg2:
            st.markdown("**ML-Motor:**")
            st.caption(f"• ML threshold per procedure: {APP_CONFIG['ML_THRESHOLD_PER_PROCEDURE']} fall")
            st.caption(f"• Target VAS: {APP_CONFIG.get('ML_TARGET_VAS', 1.0)}")
            st.caption(f"• Safety max dose: {APP_CONFIG.get('ML_SAFETY_MAX_DOSE', 20.0)} mg")

        st.divider()

        # Läkemedelsdata status
        st.markdown("### 💊 Läkemedelsdata (LÄKEMEDELS_DATA)")
        from config import LÄKEMEDELS_DATA

        st.caption(f"**{len(LÄKEMEDELS_DATA)} läkemedel definierade**")

        # Visa läkemedelsklasser
        classes = {}
        for drug_key, drug_data in LÄKEMEDELS_DATA.items():
            drug_class = drug_data.get('class', 'Unknown')
            if drug_class not in classes:
                classes[drug_class] = []
            classes[drug_class].append(drug_data['name'])

        for drug_class, drugs in classes.items():
            with st.expander(f"**{drug_class}** ({len(drugs)} läkemedel)"):
                for drug_name in drugs:
                    st.caption(f"• {drug_name}")
