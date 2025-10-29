import streamlit as st
import pandas as pd
import database as db
import auth
from datetime import datetime
from io import BytesIO

def render_history_tab(procedures_df):
    st.header("📊 Historik & Statistik")

    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.subheader("Sparade Fall i Databasen")
    with col_header2:
        all_cases = db.get_all_cases()
        if all_cases:
            export_df = pd.DataFrame(all_cases)
            if 'timestamp' in export_df.columns:
                export_df['timestamp'] = export_df['timestamp'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if isinstance(x, datetime) else x)
            if 'last_modified' in export_df.columns:
                export_df['last_modified'] = export_df['last_modified'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if isinstance(x, datetime) else x)

            export_df['procedure_name'] = export_df['procedure_id'].apply(
                lambda x: procedures_df.loc[procedures_df['id'] == x, 'name'].iloc[0] if x and x in procedures_df['id'].values else 'Okänt'
            )

            export_df['created_by_name'] = export_df['user_id'].apply(
                lambda x: db.get_user_by_id(x)['username'] if db.get_user_by_id(x) else 'Okänd'
            )

            export_cols = ['timestamp', 'procedure_name', 'age', 'sex', 'weight', 'height', 'bmi', 'ibw', 'abw',
                          'asa', 'opioidHistory', 'lowPainThreshold', 'optime_minutes', 'fentanylDose',
                          'nsaid', 'catapressan', 'droperidol', 'ketamine', 'lidocaine', 'betapred',
                          'givenDose', 'vas', 'uvaDose', 'postop_minutes', 'postop_reason', 'respiratory_status', 'severe_fatigue',
                          'created_by_name', 'last_modified']
            export_df_filtered = export_df[[col for col in export_cols if col in export_df.columns]]

            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                export_df_filtered.to_excel(writer, sheet_name='Fall', index=False)
            buffer.seek(0)

            st.download_button(
                label="📥 Exportera till Excel",
                data=buffer,
                file_name=f"anestesi_fall_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    all_cases = db.get_all_cases()
    num_cases = len(all_cases)
    if num_cases > 0:
        st.markdown("**Klicka på ett fall för att redigera det**")

        filter_cols = st.columns(5)
        with filter_cols[0]:
            search_user = st.text_input("🔍 Sök användar-ID", key="search_user", placeholder="t.ex. DN123")
        with filter_cols[1]:
            search_procedure = st.selectbox("Filtrera ingrepp", ["Alla"] + sorted(procedures_df['name'].unique()), key="search_proc")
        with filter_cols[2]:
            min_vas = st.number_input("Min VAS", 0, 10, 0, key="min_vas")
        with filter_cols[3]:
            show_incomplete = st.checkbox("Visa bara ofullständiga", key="show_incomplete", help="Visa fall utan VAS/utfall (admin)")
        with filter_cols[4]:
            max_results = st.number_input("Visa antal", 5, 100, 10, 5, key="max_results")

        filtered_cases = []
        for case in all_cases:
            case_user = db.get_user_by_id(case['user_id'])
            case_username = case_user['username'] if case_user else 'Okänd'

            if search_user and search_user.lower() not in case_username.lower():
                continue
            if search_procedure != "Alla":
                proc_name = procedures_df.loc[procedures_df['id'] == case.get('procedure_id'), 'name'].iloc[0] if case.get('procedure_id') and case.get('procedure_id') in procedures_df['id'].values else 'Okänt'
                if proc_name != search_procedure:
                    continue
            if case.get('vas', 0) < min_vas:
                continue

            if show_incomplete:
                is_incomplete = (case.get('vas', 3) == 3 and
                               case.get('uvaDose', 0) == 0 and
                               case.get('postop_minutes', 0) == 0)
                if not is_incomplete:
                    continue

            filtered_cases.append(case)

        st.caption(f"Visar {min(len(filtered_cases), max_results)} av {len(filtered_cases)} matchande fall (totalt {num_cases} fall)")

        if auth.is_admin() and show_incomplete and len(filtered_cases) > 0:
            st.warning(f"⚠️ Admin: {len(filtered_cases)} ofullständiga fall hittades")
            if st.button(f"🗑️ Radera alla {len(filtered_cases)} ofullständiga fall", type="secondary"):
                for case in filtered_cases:
                    db.delete_case(case['id'])
                st.success(f"Raderade {len(filtered_cases)} ofullständiga fall!")
                st.rerun()

        for case in filtered_cases[:max_results]:
            proc_name = procedures_df.loc[procedures_df['id'] == case.get('procedure_id'), 'name'].iloc[0] if case.get('procedure_id') and case.get('procedure_id') in procedures_df['id'].values else 'Okänt'
            timestamp_str = case['timestamp'].strftime('%Y-%m-%d %H:%M')

            case_user = db.get_user_by_id(case['user_id'])
            created_by = case_user['username'] if case_user else 'Okänd'

            edited_info = ""
            if case.get('last_modified'):
                last_mod_user = db.get_user_by_id(case.get('last_modified_by'))
                last_mod_name = last_mod_user['username'] if last_mod_user else 'Okänd'
                edited_info = f" (Senast redigerat: {case['last_modified'].strftime('%Y-%m-%d %H:%M')} av {last_mod_name})"

            col1, col2, col3, col4, col5, col6 = st.columns([2, 3, 1, 1, 1, 1])
            with col1:
                st.text(timestamp_str)
            with col2:
                st.text(proc_name)
            with col3:
                st.text(f"VAS: {case.get('vas', 'N/A')}")
            with col4:
                st.text(f"Dos: {case.get('givenDose', 'N/A')} mg")
            with col5:
                if auth.can_edit_case(case['user_id']):
                    if st.button("📝 Redigera", key=f"edit_case_{case['id']}"):
                        st.session_state.load_case_data = case
                        st.rerun()
                else:
                    st.text("🔒")

            with col6:
                if auth.can_delete_case(case['user_id']):
                    @st.dialog("Bekräfta radering")
                    def confirm_delete(case_id, case_name):
                        st.write(f"Är du säker på att du vill radera fallet:")
                        st.markdown(f"**{case_name}**")
                        st.warning("⚠️ Denna åtgärd kan inte ångras!")
                        col1, col2 = st.columns(2)
                        if col1.button("✅ Ja, radera", type="primary", use_container_width=True):
                            db.delete_case(case_id)
                            st.rerun()
                        if col2.button("❌ Avbryt", use_container_width=True):
                            st.rerun()

                    case_name = f"{procedures_df.loc[procedures_df['id'] == case.get('procedure_id'), 'name'].iloc[0] if case.get('procedure_id') and case.get('procedure_id') in procedures_df['id'].values else 'Okänt'} ({timestamp_str})"
                    if st.button("🗑️", key=f"delete_case_{case['id']}", help="Radera fall"):
                        confirm_delete(case['id'], case_name)
                else:
                    st.text("🔒")

            st.caption(f"Skapad av: {created_by}{edited_info}")

            edit_history = db.get_edit_history(case['id'])
            if edit_history:
                with st.expander(f"📊 Ändringshistorik ({len(edit_history)} ändringar)"):
                    for edit in edit_history:
                        st.markdown(f"**{edit['timestamp'].strftime('%Y-%m-%d %H:%M')}** av {edit['edited_by_name']} (Modell: {edit['model_used']})")
                        st.markdown(f"- Dos: {edit['old_values']['givenDose']} → {edit['new_values']['givenDose']} mg")
                        st.markdown(f"- VAS: {edit['old_values']['vas']} → {edit['new_values']['vas']}")
                        st.markdown(f"- UVA dos: {edit['old_values']['uvaDose']} → {edit['new_values']['uvaDose']} mg")
                        st.divider()

            # Display temporal doses if any
            temporal_doses = db.get_temporal_doses(case['id'])
            if temporal_doses:
                with st.expander(f"📅 Temporal Dosering ({len(temporal_doses)} doser)"):
                    from pharmacokinetics import format_time_relative
                    # Sort by time
                    sorted_doses = sorted(temporal_doses, key=lambda x: x['time_relative_minutes'])

                    for dose in sorted_doses:
                        time_str = format_time_relative(dose['time_relative_minutes'])

                        # Färglägg baserat på tid (samma färger som dosing_tab) - dämpad palett
                        if dose['time_relative_minutes'] < -30:
                            bg_color = "#d1e3f0"  # Dämpad blå för preop
                        elif dose['time_relative_minutes'] < 0:
                            bg_color = "#f5e6d3"  # Dämpad orange för periop
                        else:
                            bg_color = "#e2ecd8"  # Dämpad grön för postop

                        st.markdown(
                            f'<div style="background-color: {bg_color}; padding: 5px; border-radius: 3px; margin: 2px 0;">'
                            f'{time_str} | {dose["drug_name"]} {dose["dose"]} {dose["unit"]} ({dose["administration_route"]})'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        if dose.get('notes'):
                            st.caption(f"   Note: {dose['notes']}")

                    # Timeline visualization
                    if len(sorted_doses) > 1:
                        st.markdown("**Tidslinje:**")
                        import plotly.graph_objects as go

                        times = [d['time_relative_minutes'] for d in sorted_doses]
                        names = [f"{d['drug_name']}<br>{d['dose']}{d['unit']}" for d in sorted_doses]

                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=times,
                            y=[1]*len(times),
                            mode='markers+text',
                            marker=dict(size=12, color='lightblue'),
                            text=names,
                            textposition='top center',
                            hovertext=[f"{format_time_relative(d['time_relative_minutes'])}: {d['drug_name']} {d['dose']} {d['unit']}"
                                      for d in sorted_doses],
                            hoverinfo='text',
                            showlegend=False
                        ))

                        # Add opslut line
                        fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Opslut (0:00)")

                        fig.update_layout(
                            xaxis_title="Minuter relativt opslut",
                            yaxis_visible=False,
                            height=200,
                            showlegend=False,
                            margin=dict(t=50, b=30)
                        )

                        st.plotly_chart(fig, use_container_width=True)

            st.divider()

        if st.session_state.editing_case_id is not None:
            st.info(f"🔄 Du redigerar nu fall. När du sparar kommer fallet att uppdateras, inte dupliceras.")
            if st.button("❌ Avbryt redigering"):
                st.session_state.editing_case_id = None
                st.rerun()
    else:
        st.info("Inga fall har sparats ännu.")
