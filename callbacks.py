import streamlit as st
import pandas as pd
import math
import database as db
import auth
from calculation_engine import (calculate_ideal_body_weight, calculate_adjusted_body_weight,
                                calculate_synergy_adjustment,
                                calculate_selectivity_adjustment, calculate_potency_adjustment)
from config import APP_CONFIG
from learning_engine import (calculate_actual_requirement, learn_procedure_requirements,
                             learn_patient_factors, learn_adjuvant_percentage,
                             learn_procedure_3d_pain)

def get_current_inputs(procedures_df):
    specialty = st.session_state.get('specialty')
    procedure_name = st.session_state.get('procedure_name')
    procedure_id, kva_code = None, None
    if specialty and procedure_name:
        proc_row = procedures_df[(procedures_df['name'] == procedure_name) & (procedures_df['specialty'] == specialty)]
        if not proc_row.empty:
            procedure_id = proc_row.iloc[0]['id']
            kva_code = proc_row.iloc[0].get('kva_code', None)

    optime_total_minutes = (st.session_state.get('optime_hours', 0) * 60) + st.session_state.get('optime_minutes', 0)

    # Handle paracetamol - if checkbox is checked, override nsaid_choice
    nsaid_choice = st.session_state.get('nsaid_choice', 'Ej given')
    paracetamol = st.session_state.get('paracetamol', False)

    # If paracetamol checkbox is checked, use it (even if NSAID dropdown has a value)
    if paracetamol:
        final_nsaid_choice = 'Paracetamol 1g'
        has_nsaid = True
    elif nsaid_choice != 'Ej given':
        final_nsaid_choice = nsaid_choice
        has_nsaid = True
    else:
        final_nsaid_choice = 'Ej given'
        has_nsaid = False

    return {
        'age': st.session_state.get('age', 0),
        'sex': st.session_state.get('sex', 'Man'),
        'weight': st.session_state.get('weight', 0),
        'height': st.session_state.get('height', 0),
        'asa': st.session_state.get('asa', 'ASA 2'),
        'opioidHistory': st.session_state.get('opioidHistory', 'Opioidnaiv'),
        'lowPainThreshold': st.session_state.get('lowPainThreshold', False),
        'renalImpairment': st.session_state.get('renalImpairment', False),
        'procedure_id': procedure_id,
        'kva_code': kva_code,
        'specialty': specialty,
        'surgery_type': st.session_state.get('surgery_type', 'Elektivt'),
        'fentanylDose': st.session_state.get('fentanylDose', 0),
        'optime_minutes': optime_total_minutes,
        'nsaid': has_nsaid,
        'nsaid_choice': final_nsaid_choice,
        'catapressan': st.session_state.get('catapressan_dose', 0) > 0,
        'catapressan_dose': st.session_state.get('catapressan_dose', 0),
        'droperidol': st.session_state.get('droperidol', False),
        'ketamine': st.session_state.get('ketamine', 'Nej'),
        'ketamine_choice': st.session_state.get('ketamine_choice', 'Ej given'),
        'lidocaine': st.session_state.get('lidocaine', 'Nej'),
        'betapred': st.session_state.get('betapred', 'Nej'),
        'sevoflurane': st.session_state.get('sevoflurane', False),
        'infiltration': st.session_state.get('infiltration', False),
    }

def _get_outcome_data_from_state():
    postop_hours = st.session_state.get('postop_hours', 0)
    postop_minutes = st.session_state.get('postop_minutes', 0)
    postop_total_minutes = (postop_hours * 60) + postop_minutes

    return {
        'givenDose': st.session_state.get('givenDose', 0.0),
        'vas': st.session_state.get('vas', 0),
        'uvaDose': st.session_state.get('uvaDose', 0.0),
        'postop_minutes': postop_total_minutes,
        'postop_reason': st.session_state.get('postop_reason', 'Normal återhämtning'),
        'respiratory_status': st.session_state.get('respiratory_status', 'vaken'),
        'severe_fatigue': st.session_state.get('severe_fatigue', False),
        'rescue_early': st.session_state.get('rescue_early', False),
        'rescue_late': st.session_state.get('rescue_late', False),
    }

def _save_or_update_case_in_db(current_inputs, outcome_data):
    from calculation_engine import calculate_bmi
    user_id = auth.get_current_user_id()
    weight_data = {}
    if current_inputs['weight'] > 0 and current_inputs['height'] > 0:
        sex = current_inputs.get('sex', 'Man')
        ibw = calculate_ideal_body_weight(current_inputs['height'], sex)
        abw = calculate_adjusted_body_weight(current_inputs['weight'], current_inputs['height'], sex)
        bmi = calculate_bmi(current_inputs['weight'], current_inputs['height'])
        weight_data = {
            'ibw': round(ibw, 1),
            'abw': round(abw, 1),
            'bmi': round(bmi, 1)
        }

    if st.session_state.editing_case_id is not None:
        case_id = st.session_state.editing_case_id
        old_case = db.get_case_by_id(case_id)
        if old_case:
            db.add_edit_history(
                case_id, user_id,
                {'givenDose': old_case.get('givenDose', 0), 'vas': old_case.get('vas', 0), 'uvaDose': old_case.get('uvaDose', 0)},
                outcome_data, st.session_state.current_calculation.get('engine', 'Okänd')
            )
            outcome_with_weight = {**outcome_data, **weight_data}
            db.update_case(case_id, outcome_with_weight, user_id)
        st.session_state.editing_case_id = None
        st.success("Fallet har uppdaterats!")
    else:
        case_data = {**current_inputs, **outcome_data, **weight_data}
        case_data['asa'] = case_data['asa'].replace('ASA ', '')
        case_data['calculation'] = st.session_state.current_calculation
        case_id = db.save_case(case_data, user_id)

        # Save temporal doses if any
        temporal_doses = st.session_state.get('temporal_doses', [])
        if temporal_doses and case_id:
            db.save_temporal_doses(case_id, temporal_doses)

        # Clear temporal doses after save to prevent leaking to next case
        st.session_state.temporal_doses = []

        st.success("Fallet har sparats till databasen!")

def handle_save_and_learn(procedures_df):
    """
    Save case and learn from ACTUAL REQUIREMENT.

    NEW APPROACH (Back-calculation learning):
    1. Calculate actual opioid requirement from givenDose + uvaDose + outcome quality
    2. Compare to what we recommended
    3. Back-calculate what parameter adjustments would have predicted correctly
    4. Distribute learning across: procedure baseMME, adjuvant effectiveness, patient factors
    """
    outcome_data = _get_outcome_data_from_state()
    if not outcome_data['givenDose'] or outcome_data['vas'] is None:
        st.warning("Ange både given startdos och högsta VAS för att spara.")
        return

    current_inputs = get_current_inputs(procedures_df)
    _save_or_update_case_in_db(current_inputs, outcome_data)

    # Get procedure info for learning
    user_id = auth.get_current_user_id()
    all_cases = db.get_all_cases()
    cases_df_learn = pd.DataFrame(all_cases) if all_cases else pd.DataFrame()
    num_proc_cases = 0
    if not cases_df_learn.empty and 'procedure_id' in cases_df_learn.columns and current_inputs.get('procedure_id'):
        num_proc_cases = len(cases_df_learn[cases_df_learn['procedure_id'] == current_inputs['procedure_id']])

    # Get the recommended dose from calculation (for comparison)
    recommended_dose = st.session_state.current_calculation.get('finalDose', 0)

    # NEW: Calculate actual requirement and learning from it
    requirement_data = calculate_actual_requirement(outcome_data, recommended_dose, num_proc_cases, current_inputs)

    learning_updates = []

    # Learn from actual requirement (back-calculation approach)
    # success, msg = learn_procedure_requirements(user_id, requirement_data, current_inputs, procedures_df)
    # if success and msg:
    #     learning_updates.append(msg)

    # Learn patient factors (age, weight, ASA)
    patient_updates = learn_patient_factors(user_id, requirement_data, current_inputs)
    learning_updates.extend(patient_updates)

    # NEW IN V5: Learn adjuvant percentage-based potency (GLOBAL learning)
    adjuvant_updates = learn_adjuvant_percentage(user_id, requirement_data, current_inputs)
    learning_updates.extend(adjuvant_updates)

    # NEW IN V6: Learn procedure 3D pain profile (GLOBAL learning)
    pain_3d_updates = learn_procedure_3d_pain(user_id, requirement_data, current_inputs, procedures_df)
    learning_updates.extend(pain_3d_updates)

    # Learn fentanyl kinetics (uses requirement_data)
    _learn_fentanyl_kinetics(user_id, requirement_data, current_inputs, outcome_data)

    # Show learning updates
    if learning_updates:
        with st.expander("🧠 Learning Updates - Klicka för att se detaljer", expanded=False):
            st.markdown(f"**Outcome:** {requirement_data['outcome_quality'].upper()}")
            st.markdown(f"**Actual requirement:** {requirement_data['actual_requirement']:.1f} mg")
            st.markdown(f"**Predicted:** {requirement_data['recommended']:.1f} mg")
            st.markdown(f"**Prediction error:** {requirement_data['prediction_error']:+.1f} mg")
            st.markdown("---")
            st.markdown("Systemet har uppdaterat följande parametrar:")
            for update in learning_updates:
                st.caption(update)

def _learn_fentanyl_kinetics(user_id, requirement_data, current_inputs, outcome):

    if current_inputs.get('fentanylDose', 0) <= 0: return



    cfg_learn = APP_CONFIG['LEARNING']

    rescue_early = outcome.get('rescue_early', False)

    rescue_late = outcome.get('rescue_late', False)



    # Learn only if the outcome was underdosed

    if requirement_data['outcome_quality'] != 'underdosed':

        return



    fentanyl_adjustment = 0

    caption = None

    adjustment = requirement_data['learning_magnitude']



    if rescue_early and not rescue_late:

        fentanyl_adjustment = adjustment * cfg_learn['FENTANYL_KINETICS_ADJ_LARGE']

        caption = f"💉 Fentanyl-kinetik uppdaterad (tidig smärta): {db.get_fentanyl_remaining_fraction(user_id):.3f} (kortare svans)"

    elif rescue_late and not rescue_early:

        caption = f"📊 Grunddos för låg (sen smärta), calibration_factor justerad"

    elif rescue_early and rescue_late:

        fentanyl_adjustment = adjustment * cfg_learn['FENTANYL_KINETICS_ADJ_SMALL']

        caption = f"⚠️ Både fentanyl-kinetik OCH grunddos justerade (massiv underdosering)"

    

    if fentanyl_adjustment != 0:

        db.update_fentanyl_remaining_fraction(user_id, fentanyl_adjustment)

    

    if caption: st.caption(caption)
