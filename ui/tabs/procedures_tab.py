import streamlit as st
import database as db
import auth
from datetime import datetime

def render_procedures_tab(specialties):
    st.header("➕ Hantera Ingrepp")

    proc_tabs = st.tabs(["Lägg till nytt ingrepp", "Visa tillagda ingrepp"])

    with proc_tabs[0]:
        st.markdown("Lägg till nya ingrepp i databasen som inte finns med i standardlistan.")

        with st.form("new_procedure_form"):
            st.write("Skapa ett nytt ingrepp")

            new_name = st.text_input("Namn på ingrepp", placeholder="T.ex. Njurtransplantation")

            new_kva_code = st.text_input("KVÅ-kod (valfritt)", placeholder="T.ex. KAC20", help="KVÅ-kod enligt Socialstyrelsens klassifikation. Används för dataexport och standardiserad kodning.")

            all_specialties = sorted(list(set(specialties + ["<Skapa ny>"])))
            new_specialty_choice = st.selectbox("Välj specialitet", options=all_specialties)

            new_specialty_name = ""
            if new_specialty_choice == "<Skapa ny>":
                new_specialty_name = st.text_input("Namn på ny specialitet")

            new_base_mme = st.number_input("Grund-MME", min_value=1, max_value=50, value=10, step=1, help="Uppskattat opioidbehov i Morfinekvivalenter för en standardpatient.")
            new_pain_type = st.selectbox("Dominerande smärttyp", options=['somatic', 'visceral', 'mixed'])

            submitted = st.form_submit_button("Spara nytt ingrepp")
            if submitted:
                final_specialty = new_specialty_name if new_specialty_name else new_specialty_choice
                if new_name and final_specialty:
                    new_id = f"custom_{new_name.lower().replace(' ', '_')}_{datetime.now().strftime('%f')}"
                    new_proc = {
                        'id': new_id,
                        'specialty': final_specialty,
                        'name': new_name,
                        'kva_code': new_kva_code if new_kva_code else None,
                        'baseMME': new_base_mme,
                        'painType': new_pain_type
                    }
                    user_id = auth.get_current_user_id()
                    db.save_custom_procedure(new_proc, user_id)
                    st.success(f"Ingreppet '{new_name}' har sparats!")
                    st.rerun()
                else:
                    st.error("Namn på ingrepp och specialitet måste fyllas i.")

    with proc_tabs[1]:
        st.markdown("**Dina tillagda ingrepp**")

        custom_procs = db.get_all_custom_procedures()
        if len(custom_procs) == 0:
            st.info("Inga custom ingrepp har lagts till ännu.")
        else:
            for proc in custom_procs:
                with st.expander(f"{proc['name']} ({proc['specialty']})"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Specialitet:** {proc['specialty']}")
                        st.write(f"**Grund-MME:** {proc['baseMME']}")
                        st.write(f"**Smärttyp:** {proc['painType']}")
                        st.write(f"**ID:** `{proc['id']}`")

                    with col2:
                        can_delete = auth.is_admin() or proc.get('created_by') == auth.get_current_user_id()
                        if can_delete:
                            if st.button("🗑️ Radera", key=f"delete_proc_{proc['id']}"):
                                db.delete_custom_procedure(proc['id'])
                                st.rerun()
                        else:
                            st.text("🔒")