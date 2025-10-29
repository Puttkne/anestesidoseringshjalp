import streamlit as st
import pandas as pd
import database as db
import auth
from calculation_engine import calculate_rule_based_dose
from ml_model import predict_with_xgboost
from callbacks import get_current_inputs, handle_save_and_learn
from config import APP_CONFIG
from validation import validate_recommended_dose

def render_dosing_tab(specialties, procedures_df):
    # Enhanced CSS matching the new HTML design
    st.markdown("""
        <style>
            /* Blue/Orange color scheme for high-stress emergency */
            :root {
                --primary: #FF6B00;
                --primary-hover: #E55F00;
                --background-dark: #0B1D48;
                --card-dark: #1A3266;
                --input-bg: #384F83;
                --text-dark: #ffffff;
                --subtext-dark: #9BB0C7;
                --border-dark: #2d4a7f;
            }

            /* Section headers with border */
            .stMarkdown h2, .stMarkdown h3 {
                color: var(--text-dark) !important;
                font-weight: 600 !important;
                border-bottom: 1px solid var(--border-dark);
                padding-bottom: 0.5rem;
                margin-bottom: 0.75rem;
            }

            /* Input fields */
            .stNumberInput > div > div > input,
            .stTextInput > div > div > input,
            .stSelectbox > div > div > div {
                background-color: var(--input-bg) !important;
                color: var(--text-dark) !important;
                border: none !important;
                border-radius: 0.5rem !important;
            }

            /* Selectbox dropdown */
            div[data-baseweb="select"] > div {
                background-color: var(--input-bg) !important;
                border: none !important;
            }

            /* Labels - white for better visibility */
            .stNumberInput > label, .stTextInput > label,
            .stSelectbox > label, .stCheckbox > label {
                color: var(--text-dark) !important;
                font-weight: 500 !important;
            }

            /* Buttons */
            .stButton > button {
                background-color: var(--primary) !important;
                color: white !important;
                font-weight: 700 !important;
                border-radius: 0.5rem !important;
                padding: 0.625rem 1rem !important;
                border: none !important;
                box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
            }

            .stButton > button:hover {
                background-color: var(--primary-hover) !important;
            }

            /* Info/Warning boxes */
            .stAlert {
                background-color: var(--card-dark) !important;
                color: var(--text-dark) !important;
                border: 1px solid var(--border-dark) !important;
                border-radius: 0.5rem !important;
            }

            /* Slider */
            .stSlider {
                color: var(--text-dark) !important;
            }

            /* Radio buttons */
            .stRadio > div {
                background-color: var(--card-dark) !important;
                padding: 0.5rem !important;
                border-radius: 0.5rem !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # Load case if editing
    if st.session_state.get('load_case_data'):
        case = st.session_state.load_case_data
        st.session_state.editing_case_id = case['id']

        # Populate form with case data
        if 'age' in case: st.session_state['age'] = case['age']
        if 'sex' in case: st.session_state['sex'] = case['sex']
        if 'weight' in case: st.session_state['weight'] = case['weight']
        if 'height' in case: st.session_state['height'] = case['height']
        if 'asa' in case: st.session_state['asa'] = f"ASA {case['asa']}"
        if 'opioidHistory' in case: st.session_state['opioidHistory'] = case['opioidHistory']
        if 'lowPainThreshold' in case: st.session_state['lowPainThreshold'] = case['lowPainThreshold']
        if 'renalImpairment' in case: st.session_state['renalImpairment'] = case['renalImpairment']
        if 'givenDose' in case: st.session_state['givenDose'] = case['givenDose']
        if 'vas' in case: st.session_state['vas'] = case['vas']
        if 'uvaDose' in case: st.session_state['uvaDose'] = case.get('uvaDose', 0.0)
        if 'postop_minutes' in case:
            st.session_state['postop_hours'] = case['postop_minutes'] // 60
            st.session_state['postop_minutes'] = case['postop_minutes'] % 60
        if 'postop_reason' in case: st.session_state['postop_reason'] = case['postop_reason']
        if 'respiratory_status' in case: st.session_state['respiratory_status'] = case['respiratory_status']
        if 'severe_fatigue' in case: st.session_state['severe_fatigue'] = case['severe_fatigue']
        if 'rescue_early' in case: st.session_state['rescue_early'] = case.get('rescue_early', False)
        if 'rescue_late' in case: st.session_state['rescue_late'] = case.get('rescue_late', False)

        st.session_state.load_case_data = None

    # Patient input form - kompakt layout med smalare dropdowns
    st.subheader("👤 Patient")
    input_cols = st.columns([0.6, 0.5, 0.6, 0.6, 0.6, 0.6, 0.7, 0.6])

    with input_cols[0]:
        st.number_input("Ålder", 0, 120, 50, key='age', label_visibility="visible")
    with input_cols[1]:
        st.selectbox("Kön", ["Man", "Kvinna"], key='sex', label_visibility="visible")
    with input_cols[2]:
        st.number_input("Vikt", 0, 300, 75, key='weight', label_visibility="visible")
    with input_cols[3]:
        st.number_input("Längd", 0, 250, 175, key='height', label_visibility="visible")
    with input_cols[4]:
        st.selectbox("ASA", ["ASA 1", "ASA 2", "ASA 3", "ASA 4", "ASA 5"], index=1, key='asa', label_visibility="visible")
    with input_cols[5]:
        st.selectbox("Opioid", ["Naiv", "Tolerant"], key='opioidHistory', label_visibility="visible", format_func=lambda x: x if x == "Naiv" else "Tolerant")
    with input_cols[6]:
        st.checkbox("Låg smärttröskel", key='lowPainThreshold')
    with input_cols[7]:
        st.checkbox("GFR <35", key='renalImpairment')

    # Opioid tolerance advice
    if st.session_state.get('opioidHistory') == 'Tolerant':
        st.info("💊 **Opioidtoleranta patienter:** Ge daglig grunddos opioid + ca 20-30% för postop smärta. Systemet justerar automatiskt rekommendationen med 50% för toleranta patienter.")

    st.divider()

    # Procedure selection - kompakt och smalare (halverad bredd igen)
    st.subheader("🔬 Ingrepp")
    proc_cols = st.columns([0.5, 1, 0.4])

    with proc_cols[0]:
        st.selectbox("Specialitet", specialties, key='specialty', label_visibility="visible")
    with proc_cols[1]:
        specialty = st.session_state.get('specialty')
        if specialty:
            specialty_procedures = procedures_df[procedures_df['specialty'] == specialty]['name'].sort_values()
            st.selectbox("Ingrepp", specialty_procedures, key='procedure_name', label_visibility="visible")
    with proc_cols[2]:
        st.selectbox("Läge", ["Elektivt", "Akut"], key='surgery_type', label_visibility="visible")

    st.divider()

    # Givna Opioider (temporal dosering) - ersätter Anestesidata
    st.subheader("💉 Givna Opioider")

    # Initialize temporal doses in session state
    if 'temporal_doses' not in st.session_state:
        st.session_state.temporal_doses = []

    # Initialize temporal timing preference
    if 'temporal_timing_preop' not in st.session_state:
        st.session_state.temporal_timing_preop = True  # Default till "före opslut"

    # Kompakt input för opioider - smalare kolumner
    opioid_cols = st.columns([0.5, 0.35, 0.3, 0.3, 0.5])

    with opioid_cols[0]:
        opioid_drug = st.selectbox("Läkemedel", ["Fentanyl", "Oxycodone", "Morfin"], key='temp_opioid_drug', label_visibility="collapsed")

    # Unit baserat på läkemedel
    opioid_unit_map = {"Fentanyl": "µg", "Oxycodone": "mg", "Morfin": "mg"}
    opioid_unit = opioid_unit_map.get(opioid_drug, "mg")

    # Dynamiskt steg och format baserat på läkemedel
    if opioid_drug == "Fentanyl":
        step_size = 25
        # For Fentanyl, use integer input to avoid format warning
        with opioid_cols[1]:
            opioid_dose = float(st.number_input(f"Dos ({opioid_unit})", min_value=0, step=step_size, key='temp_opioid_dose', label_visibility="collapsed", format="%d"))
    else:  # Oxycodone eller Morfin
        step_size = 0.5
        with opioid_cols[1]:
            opioid_dose = st.number_input(f"Dos ({opioid_unit})", min_value=0.0, step=step_size, key='temp_opioid_dose', label_visibility="collapsed", format="%.1f")

    with opioid_cols[2]:
        # Tid som två inputfält bredvid varandra
        temp_hours = st.number_input("Timmar", min_value=0, max_value=12, value=1, key='temp_opioid_hours', label_visibility="collapsed")

    with opioid_cols[3]:
        temp_mins = st.number_input("Minuter", min_value=0, max_value=55, value=30, step=5, key='temp_opioid_mins', label_visibility="collapsed")

    with opioid_cols[4]:
        # Checkbox för att switcha mellan pre/postop
        is_postop = st.checkbox("Postop", key='temp_opioid_postop', value=False)

    if st.button("➕ Lägg till opioid", key='add_opioid_btn', use_container_width=False):
        # Validate
        if opioid_dose <= 0:
            st.error("❌ Dos måste vara större än 0")
            st.stop()

        total_minutes = temp_hours * 60 + temp_mins
        if total_minutes == 0 and not is_postop:
            st.error("❌ Ange tid")
            st.stop()

        time_relative_minutes = total_minutes if is_postop else -total_minutes

        st.session_state.temporal_doses.append({
            'drug_type': opioid_drug.lower(),
            'drug_name': opioid_drug,
            'dose': opioid_dose,
            'unit': opioid_unit,
            'time_relative_minutes': time_relative_minutes,
            'administration_route': 'IV',
            'notes': ''
        })
        st.rerun()

    # Display added opioids - kompakt och färglagd
    if st.session_state.temporal_doses:
        st.markdown("**Tillagda opioider:**")

        sorted_doses = sorted(st.session_state.temporal_doses, key=lambda x: x['time_relative_minutes'])

        for idx, dose in enumerate(sorted_doses):
            from pharmacokinetics import format_time_relative
            time_str = format_time_relative(dose['time_relative_minutes'])

            # Ljusblå färg för alla tillagda opioider
            bg_color = "#d6ebf5"  # Ljusblå

            col1, col2 = st.columns([10, 1])
            with col1:
                st.markdown(
                    f'<div style="background-color: {bg_color}; color: #31333F; padding: 5px; border-radius: 3px; margin: 2px 0;">'
                    f'{time_str} | {dose["drug_name"]} {dose["dose"]} {dose["unit"]}'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with col2:
                if st.button("🗑️", key=f"del_opioid_{idx}"):
                    for i, original_dose in enumerate(st.session_state.temporal_doses):
                        if (original_dose['time_relative_minutes'] == dose['time_relative_minutes'] and
                            original_dose['drug_name'] == dose['drug_name'] and
                            original_dose['dose'] == dose['dose']):
                            st.session_state.temporal_doses.pop(i)
                            st.rerun()
                            break

    st.divider()

    # Adjuvanter - Vertical columns layout
    st.subheader("💊 Adjuvanter")

    # Create vertical columns for all adjuvants
    adj_cols = st.columns(4)

    # Column 1: NSAID + Paracetamol
    with adj_cols[0]:
        nsaid_choice = st.selectbox("NSAID", ["Ingen", "Ibuprofen 400mg", "Ketorolac 30mg", "Parecoxib 40mg"], key='nsaid_choice_direct', label_visibility="visible")
        if nsaid_choice != "Ingen":
            st.session_state['nsaid'] = True
            st.session_state['nsaid_choice'] = nsaid_choice
        else:
            st.session_state['nsaid'] = False
            st.session_state['nsaid_choice'] = 'Ej given'

        paracetamol = st.checkbox("Paracetamol 1g", key='paracetamol_checkbox')
        st.session_state['paracetamol'] = paracetamol

    # Column 2: Catapressan + Betapred
    with adj_cols[1]:
        st.number_input("Catapressan (µg)", 0, 150, 0, 25, key='catapressan_dose', label_visibility="visible")

        betapred = st.selectbox("Betapred (mg)", ["Nej", "4 mg", "8 mg"], key='betapred', label_visibility="visible")

    # Column 3: Ketamin + Lidokain
    with adj_cols[2]:
        ketamine_dose = st.number_input("Ketamin (mg)", 0.0, 200.0, 0.0, 5.0, key='ketamine_dose_input', label_visibility="visible")
        ketamine_infusion = st.checkbox("Infusion (mg/kg/h)", key='ketamine_infusion')

        # Set ketamine state based on dose
        if ketamine_dose > 0:
            st.session_state['ketamine'] = "Ja"
            st.session_state['ketamine_choice'] = 'Infusion' if ketamine_infusion else 'Bolus'
        else:
            st.session_state['ketamine'] = "Nej"
            st.session_state['ketamine_choice'] = 'Ej given'

        lidocaine_dose = st.number_input("Lidokain (mg)", 0.0, 200.0, 0.0, 10.0, key='lidocaine_dose_input', label_visibility="visible")
        lidocaine_infusion = st.checkbox("Infusion (mg/h)", key='lidocaine_infusion')

        # Set lidocaine state
        if lidocaine_dose > 0:
            st.session_state['lidocaine'] = 'Infusion' if lidocaine_infusion else 'Bolus'
        else:
            st.session_state['lidocaine'] = 'Nej'

    # Column 4: Checkboxes
    with adj_cols[3]:
        st.checkbox("Droperidol", key='droperidol')
        st.checkbox("Infiltration", key='infiltration')
        st.checkbox("Sevo", key='sevoflurane')

    st.divider()

    # Calculate and display results
    res_cols = st.columns([1, 1])

    with res_cols[0]:
        st.subheader("💡 Dosrekommendation")

        if st.button("🧮 Beräkna Rekommendation", type="primary", use_container_width=True):
            current_inputs = get_current_inputs(procedures_df)
            # Get temporal doses from session state
            temporal_doses = st.session_state.get('temporal_doses', [])
            regel_calc = calculate_rule_based_dose(current_inputs, procedures_df, temporal_doses)
            regel_dose = regel_calc.get('finalDose', 0.0)

            all_cases = db.get_all_cases()
            cases_df_ml = pd.DataFrame(all_cases) if all_cases else pd.DataFrame()
            num_proc_cases = 0
            if not cases_df_ml.empty and 'procedure_id' in cases_df_ml.columns and current_inputs.get('procedure_id'):
                num_proc_cases = len(cases_df_ml[cases_df_ml['procedure_id'] == current_inputs['procedure_id']])

            if num_proc_cases >= APP_CONFIG['ML_THRESHOLD_PER_PROCEDURE']:
                # Add temporal doses to current_inputs for ML
                current_inputs['temporal_doses'] = temporal_doses
                xgb_calc = predict_with_xgboost(current_inputs, procedures_df)
                xgb_dose = xgb_calc.get('finalDose', 0.0)

                weight_xgb = min(1.0, num_proc_cases / 50)
                ensemble_dose = regel_dose * (1 - weight_xgb) + xgb_dose * weight_xgb
                ensemble_dose = round(ensemble_dose / 0.25) * 0.25

                st.session_state.current_calculation = xgb_calc.copy()
                st.session_state.current_calculation['finalDose'] = ensemble_dose
                st.session_state.current_calculation['engine'] = f"Ensemble (XGBoost {int(weight_xgb*100)}% + Regel {int((1-weight_xgb)*100)}%)"
            else:
                st.session_state.current_calculation = regel_calc

        if st.session_state.current_calculation:
            calc = st.session_state.current_calculation
            final_dose = calc.get('finalDose', 0.0)
            engine = calc.get('engine', "Väntar på beräkning...")

            current_inputs = get_current_inputs(procedures_df)
            all_cases = db.get_all_cases()
            cases_df_confidence = pd.DataFrame(all_cases) if all_cases else pd.DataFrame()

            num_total_cases = len(cases_df_confidence) if not cases_df_confidence.empty else 0
            num_proc_cases = 0
            if not cases_df_confidence.empty and 'procedure_id' in cases_df_confidence.columns:
                proc_cases_df = cases_df_confidence[cases_df_confidence['procedure_id'] == current_inputs['procedure_id']]
                num_proc_cases = len(proc_cases_df)

            user_id = auth.get_current_user_id()
            composite_key = calc.get('compositeKey', '')
            calibration_factor = db.get_calibration_factor(user_id, composite_key) if composite_key else 1.0

            low_confidence = (num_proc_cases < 3 and abs(calibration_factor - 1.0) < 0.1) or num_total_cases < 5

            procedure_id = current_inputs.get('procedure_id')

            # Validate recommended dose (only for perioperative starting dose)
            is_safe, severity, validation_msg = validate_recommended_dose(final_dose)

            info_lines = []
            info_lines.append(f"### 💡 Förslag: {final_dose} mg ({engine})")
            info_lines.append("⚙️ **Använd som utgångspunkt** och justera efter klinisk bedömning.")

            # Show validation warning if dose is high
            if severity == 'WARNING':
                info_lines.append(f"\n{validation_msg}")

            if current_inputs['weight'] > 0 and current_inputs['height'] > 0:
                from calculation_engine import calculate_bmi
                bmi = calculate_bmi(current_inputs['weight'], current_inputs['height'])
                ibw = calc.get('ibw')
                abw = calc.get('abw')
                actual_weight = calc.get('actual_weight')

                info_lines.append(f"**BMI:** {bmi:.1f} kg/m²")

                if ibw and abw and actual_weight:
                    info_lines.append(f"**IBW:** {ibw:.1f} kg")
                    if abw < actual_weight:
                        info_lines.append(f"**ABW:** {abw:.1f} kg (används för dosering)")
                    else:
                        info_lines.append(f"**Aktuell vikt** används för dosering")

            if procedure_id:
                proc_data = procedures_df[procedures_df['id'] == procedure_id]
                if not proc_data.empty:
                    pain_score = float(proc_data.iloc[0].get('painTypeScore', 5))
                    pain_type_desc = "Visceral" if pain_score <= 3 else ("Somatisk" if pain_score >= 7 else "Blandad")
                    pain_emoji = "🔵" if pain_score <= 3 else ("🔴" if pain_score >= 7 else "🟣")
                    info_lines.append(f"{pain_emoji} **Smärttyp:** {pain_type_desc} ({pain_score:.0f}/10)")

            st.info("\n".join(info_lines))

            if low_confidence:
                st.warning("⚠️ **Låg konfidiens** - Använd kliniskt omdömme!")
                st.caption(f"📊 Detta ingrepp har endast **{num_proc_cases}** loggade fall. Systemet kan inte ge en tillförlitlig dosrekommendation ännu. Vi uppmuntrar dig starkt att logga given dos och utfall så att algoritmerna kan lära sig och förbättras för framtida fall!")
            else:
                if num_proc_cases < 10:
                    st.caption(f"ℹ️ Baserad på {num_proc_cases} tidigare fall för detta ingrepp")

            if current_inputs['weight'] > 0 and current_inputs['height'] > 0:
                from calculation_engine import calculate_bmi
                bmi = calculate_bmi(current_inputs['weight'], current_inputs['height'])

                bmi_warnings = []
                if bmi < 18.5:
                    bmi_warnings.append("⚠️ Undervikt - risk för förlängd effekt och ökad känslighet")
                elif bmi >= 30 and bmi < 35:
                    bmi_warnings.append("⚠️ Fetma grad I - övervaka noga")
                elif bmi >= 35 and bmi < 40:
                    bmi_warnings.append("⚠️ Fetma grad II - risk för förlängd effekt och andningsdepression")
                elif bmi >= 40:
                    bmi_warnings.append("⚠️ Fetma grad III - hög risk, överväg dosreduktion")

                if current_inputs['age'] > 75 and final_dose > 10:
                    bmi_warnings.append("⚠️ Hög dos för patient >75 år")

                if bmi_warnings:
                    for warning in bmi_warnings:
                        st.warning(warning)

            if 'feature_importance' in calc and calc['feature_importance'] is not None:
                with st.expander("🔬 Feature Importance - Vilka faktorer påverkar mest?"):
                    feat_imp = calc['feature_importance'].head(10)
                    st.markdown("**Top 10 viktigaste faktorer för denna dos:**")
                    st.bar_chart(feat_imp.set_index('feature')['importance'])
                    st.caption("Högre värde = större påverkan på dosrekommendationen")
        else:
            st.info("Fyll i data och klicka på 'Beräkna Rekommendation'.")

    with res_cols[1]:
        st.subheader("📈 Logga Utfall")
        if st.session_state.current_calculation:
            calc = st.session_state.current_calculation
            current_inputs = get_current_inputs(procedures_df)
            all_cases = db.get_all_cases()
            cases_df_log = pd.DataFrame(all_cases) if all_cases else pd.DataFrame()

            num_total_cases = len(cases_df_log) if not cases_df_log.empty else 0
            num_proc_cases = 0
            if not cases_df_log.empty and 'procedure_id' in cases_df_log.columns:
                proc_cases = cases_df_log[cases_df_log['procedure_id'] == current_inputs['procedure_id']]
                num_proc_cases = len(proc_cases)

            user_id = auth.get_current_user_id()
            composite_key = calc.get('compositeKey', '')
            calibration_factor = db.get_calibration_factor(user_id, composite_key) if composite_key else 1.0
            low_confidence = (num_proc_cases < 3 and abs(calibration_factor - 1.0) < 0.1) or num_total_cases < 5

            if low_confidence:
                st.success("✨ **Ditt bidrag är särskilt värdefullt!** Genom att logga detta fall hjälper du systemet att lära sig och ge bättre rekommendationer nästa gång.")

            final_dose = st.session_state.current_calculation.get('finalDose', 0.0)
            st.number_input("Administrerad dos Oxycodon (mg)", min_value=0.0, step=0.25, key='givenDose', value=final_dose, format="%.2f")

            st.button("💾 Spara Fall (initial)", on_click=lambda: handle_save_and_learn(procedures_df), use_container_width=True,
                     help="Spara fallet direkt efter administrerad dos - du kan redigera och lägga till utfall senare")

            st.divider()
            st.markdown("**Postoperativa data (lägg till senare):**")

            st.slider("Högsta VAS under första timmen (UVA)", 0, 10, 3, key='vas')
            st.number_input("Extra dos given på UVA första timmen (mg)", min_value=0.0, step=0.25, key='uvaDose',
                          help="Endast rescue-doser inom den första timmen efter väckning räknas som underdosering. Doser givna senare är normal smärtbehandling.")

            st.write("**När gavs rescue-doser? (hjälper modellen skilja fentanyl-svans från grunddos)**")
            rescue_timing_cols = st.columns(2)
            rescue_timing_cols[0].checkbox("Rescue <30 min (tidig smärta = kort fentanylsvans)", key='rescue_early')
            rescue_timing_cols[1].checkbox("Rescue >30 min (sen smärta = för låg grunddos)", key='rescue_late')

            postop_cols = st.columns(2)
            postop_cols[0].number_input("Post-op tid (timmar)", 0, 48, 0, 1, key='postop_hours', help="Tid på postop i timmar")
            postop_cols[1].number_input("Post-op tid (min)", 0, 55, 0, 5, key='postop_minutes', help="Tid på postop i minuter (5 min steg)")

            st.selectbox(
                "Orsak till post-op tid",
                ["Normal återhämtning", "Andningspåverkan/trötthet (för hög dos)", "Klinisk rutin (t.ex. blödningsrisk)", "Smärtgenombrott/redosering (för låg dos)"],
                key='postop_reason',
                help="Ange orsak till post-op tid - hjälper maskininlärningen att optimera dosen korrekt"
            )

            st.write("**Postoperativ vakenhetsnivå:**")
            respiratory = st.radio(
                "",
                ["vaken", "trött", "sederad väckbar", "sederad djupt", "naturlig sömn"],
                index=0,
                key='respiratory_status',
                help="Postoperativ medvetandegrad",
                label_visibility="collapsed"
            )

            st.checkbox("Grav trötthet", key='severe_fatigue', help="Tecken på för mycket catapressan eller droperidol")

            st.button("✅ Uppdatera Fall (komplett)", on_click=lambda: handle_save_and_learn(procedures_df), use_container_width=True,
                     help="Uppdatera fallet med kompletta postoperativa data")
        else:
            st.info("Beräkna en dos för att kunna logga ett utfall.")