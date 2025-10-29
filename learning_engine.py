"""
Learning Engine - Back-Calculation System
==========================================
Learns from actual opioid requirements (givenDose + uvaDose + outcome quality)
and back-calculates what parameters would explain this requirement.

Distributes learning across:
1. Procedure baseMME and 3D pain profile
2. Adjuvant 3D pain effectiveness (GLOBAL for all users)
3. Patient factors (age, weight/ABW/IBW, sex, ASA)
"""

import math
import logging
from typing import Dict, Tuple
import database as db
from config import APP_CONFIG
from body_composition_utils import (
    get_weight_bucket,
    get_ibw_ratio_bucket,
    get_abw_ratio_bucket,
    get_bmi_bucket,
    get_bmi_label
)

logger = logging.getLogger(__name__)


def calculate_actual_requirement(
    outcome_data: Dict,
    recommended_dose: float,
    num_proc_cases: int,
    current_inputs: Dict
) -> Dict:
    """
    Calculate the ACTUAL opioid requirement from case data.

    This is the KEY FUNCTION for learning - determines what dose was actually needed.

    Args:
        outcome_data: Dict with givenDose, uvaDose, vas, respiratory_status, etc.
        recommended_dose: What the app predicted
        num_proc_cases: Number of previous cases for this procedure (affects learning rate)

    Returns:
        Dict with:
            - actual_requirement: Total opioid actually needed (mg)
            - prediction_error: actual - recommended (negative = over-predicted)
            - outcome_quality: 'perfect', 'good', 'underdosed', 'overdosed'
            - learning_magnitude: How strongly to learn (0-1)
            - base_learning_rate: Adaptive rate based on experience
    """
    cfg = APP_CONFIG['LEARNING']

    # --- CONFIGURABLE LEARNING TARGETS ---
    # Get target VAS from settings, with a default of 3
    target_vas = db.get_setting('TARGET_VAS', 3)
    # Get the probing factor from settings, default to a 3% reduction
    probe_factor = db.get_setting('DOSE_PROBE_REDUCTION_FACTOR', 0.97)


    # Adaptive learning rate based on experience
    if num_proc_cases < 3:
        base_learning_rate = cfg['INITIAL_LEARNING_RATE']
    elif num_proc_cases < 10:
        base_learning_rate = cfg['INTERMEDIATE_LEARNING_RATE']
    elif num_proc_cases < 20:
        base_learning_rate = cfg['ADVANCED_LEARNING_RATE']
    else:
        base_learning_rate = cfg['INITIAL_LEARNING_RATE'] / (
            1 + cfg['LEARNING_RATE_DECAY'] * num_proc_cases
        )

    # Extract outcome data
    given_dose = outcome_data.get('givenDose', 0)
    uva_dose = outcome_data.get('uvaDose', 0)
    vas = outcome_data.get('vas', 5)
    postop_reason = outcome_data.get('postop_reason', 'Normal återhämtning')
    respiratory_status = outcome_data.get('respiratory_status', 'vaken')
    deeply_sedated = (respiratory_status == 'sederad djupt')
    severe_fatigue = outcome_data.get('severe_fatigue', False)

    # Simplified respiratory issue check
    respiratory_issue = deeply_sedated or severe_fatigue

    # Calculate what was actually given
    actual_given_total = given_dose + uva_dose

    # --- NEW LEARNING LOGIC ---

    # 1. PERFECT OUTCOME: VAS is at or below target, no side effects.
    if vas <= target_vas and uva_dose == 0 and not respiratory_issue:
        outcome_quality = 'perfect'
        # A. Clinician gave less than recommended and it worked -> Strong signal to lower dose.
        if given_dose < recommended_dose * 0.95:
            actual_requirement = actual_given_total
            learning_magnitude = base_learning_rate * 1.5  # Boost learning
        # B. Clinician followed recommendation -> Proactively probe for a lower dose.
        else:
            # Assume the "true" requirement was slightly less than what was given.
            # This creates a small, consistent negative error to drive the dose down.
            actual_requirement = actual_given_total * probe_factor
            learning_magnitude = base_learning_rate * 0.5  # Use a mild learning rate for probes

    # 2. UNDERDOSED: VAS is above target or a rescue dose was needed.
    elif vas > target_vas or uva_dose > 0:
        outcome_quality = 'underdosed'
        # The VAS score is above our acceptable target.
        vas_deficit = max(0, vas - target_vas)
        # Estimate the additional dose that would have been needed.
        additional_needed = (vas_deficit / 7) * given_dose * 0.3
        additional_needed += uva_dose * 0.5
        actual_requirement = actual_given_total + additional_needed

        # Define a strong learning signal to increase the dose.
        vas_error = math.sqrt(vas_deficit) / math.sqrt(10 - target_vas)
        uva_error = math.sqrt(min(1, uva_dose / 10)) if uva_dose > 0 else 0
        total_error = max(vas_error, uva_error)
        rescue_boost = 1.5 if uva_dose > 0 else 1.0
        learning_magnitude = (
            base_learning_rate
            + (total_error * cfg['ERROR_ADJUSTMENT_FACTOR'])
        ) * rescue_boost

    # 3. OVERDOSED: Patient had respiratory issues.
    elif respiratory_issue:
        outcome_quality = 'overdosed'
        # Assume the dose was too high.
        actual_requirement = actual_given_total * 0.85
        learning_magnitude = base_learning_rate * abs(cfg['RESPIRATORY_ADJUSTMENT_FACTOR'])

    # 4. ACCEPTABLE OUTCOME: None of the above (e.g., VAS is between target and underdosed threshold)
    else:
        outcome_quality = 'acceptable'
        actual_requirement = actual_given_total
        learning_magnitude = base_learning_rate * 0.2  # Very mild learning

    # Calculate final prediction error
    prediction_error = actual_requirement - recommended_dose

    # Dampen learning for extreme outliers to maintain stability
    is_outlier = vas > 8 or uva_dose > 15
    if is_outlier:
        learning_magnitude *= cfg['OUTLIER_DAMPING_FACTOR']

    # Calculate prediction error
    prediction_error = actual_requirement - recommended_dose

    # Outlier damping
    is_outlier = vas > 8 or uva_dose > 15
    if is_outlier:
        learning_magnitude *= cfg['OUTLIER_DAMPING_FACTOR']

    return {
        'actual_requirement': actual_requirement,
        'prediction_error': prediction_error,
        'outcome_quality': outcome_quality,
        'learning_magnitude': learning_magnitude,
        'base_learning_rate': base_learning_rate,
        'given_total': actual_given_total,
        'recommended': recommended_dose,
    }


def learn_procedure_requirements(
    user_id: int,
    requirement_data: Dict,
    current_inputs: Dict,
    procedures_df,
) -> Tuple[bool, str]:
    """
    Learn procedure baseMME from actual requirement.

    Back-calculates: If actual requirement was X mg, what baseMME adjustment
    would have predicted this correctly?

    Args:
        user_id: User ID
        requirement_data: From calculate_actual_requirement()
        current_inputs: Patient inputs
        procedures_df: Procedures dataframe

    Returns:
        (success: bool, update_message: str)
    """
    procedure_id = current_inputs.get('procedure_id')
    if not procedure_id:
        return False, ""

    proc_data = procedures_df[procedures_df['id'] == procedure_id]
    if proc_data.empty:
        return False, ""

    cfg_learn = APP_CONFIG['LEARNING']
    default_base_mme = float(proc_data.iloc[0]['baseMME'])
    default_pain_somatic = float(proc_data.iloc[0].get('painTypeScore', 5))

    learned_data = db.get_procedure_learning(user_id, procedure_id, default_base_mme, default_pain_somatic
    )

    actual_req = requirement_data['actual_requirement']
    recommended = requirement_data['recommended']
    prediction_error = requirement_data['prediction_error']
    learning_mag = requirement_data['learning_magnitude']

    # Back-calculate baseMME adjustment
    # prediction_error = (actual_baseMME - current_baseMME) * all_multipliers
    # We want to adjust baseMME to reduce this error

    # Rough estimate: assume multipliers ≈ 1.0 on average
    # So baseMME adjustment ≈ prediction_error * learning_rate
    base_mme_adjustment = prediction_error * learning_mag * 0.1

    # Safety clamps - don't over-correct
    max_adjustment = default_base_mme * 0.25  # Max 25% change per case
    base_mme_adjustment = max(
        -max_adjustment, min(max_adjustment, base_mme_adjustment)
    )

    # Update database
    result = db.update_procedure_learning(procedure_id,
        default_base_mme,
        default_pain_somatic,
        base_mme_adjustment,
        0,  # pain_type_adjustment (handle separately in 3D learning)
    )

    if base_mme_adjustment != 0:
        proc_name = proc_data.iloc[0]['name']
        direction = "ökat" if base_mme_adjustment > 0 else "minskat"
        msg = (
            f"**BaseMME för {proc_name}:** {learned_data['base_mme']:.1f} -> "
            f"{result['base_mme']:.1f} MME ({direction} {abs(base_mme_adjustment):.1f})"
        )
        logger.info(
            f"Learned procedure baseMME: {procedure_id} adjustment={base_mme_adjustment:.2f}"
        )
        return True, msg

    return False, ""


def learn_patient_factors(
    user_id: int,
    requirement_data: Dict,
    current_inputs: Dict,
) -> list:
    """
    Learn patient-specific factors from actual requirement.

    Learns:
    - Age factor (elderly need less/more?)
    - Weight factor (via ABW/IBW)
    - ASA factor (sicker patients need less/more?)

    Args:
        user_id: User ID
        requirement_data: From calculate_actual_requirement()
        current_inputs: Patient inputs (age, weight, height, sex, asa)

    Returns:
        List of update messages
    """
    updates = []

    actual_req = requirement_data['actual_requirement']
    recommended = requirement_data['recommended']
    prediction_error = requirement_data['prediction_error']
    learning_mag = requirement_data['learning_magnitude']

    # Only learn from significant deviations
    error_ratio = abs(prediction_error) / (recommended or 1)
    if error_ratio < 0.15:  # Less than 15% error, don't adjust patient factors
        return updates

    # Determine direction
    needs_more = prediction_error > 0  # actual > recommended
    needs_less = prediction_error < 0  # actual < recommended

    # AGE FACTOR LEARNING - FINE-GRAINED (every year)
    # System now learns for EVERY individual age (0, 1, 2, ..., 120)
    age = current_inputs.get('age', 50)
    age_adjustment = learning_mag * 0.05 * (1 if needs_more else -1)
    try:
        from calculation_engine import calculate_age_factor
        from interpolation_engine import get_age_bucket

        default_factor = calculate_age_factor(age)
        age_bucket = get_age_bucket(age)
        new_factor = db.update_age_bucket_learning(age_bucket, default_factor, age_adjustment)
        updates.append(
            f"**Åldersfaktor ({age}y):** {default_factor:.2f} -> {new_factor:.2f}"
        )
        logger.info(f"Learned age factor: age={age}, bucket={age_bucket}, adjustment={age_adjustment:.3f}")
    except Exception as e:
        logger.error(f"Error updating age factor: {e}")

    # ASA FACTOR LEARNING - UNIVERSAL (all ASA classes)
    # System now learns from ALL ASA classes: ASA 1, 2, 3, 4, 5
    asa_class = current_inputs.get('asa', 'ASA 2')
    asa_adjustment = learning_mag * 0.05 * (1 if needs_more else -1)
    try:
        asa_map = {'ASA 1': 1, 'ASA 2': 2, 'ASA 3': 3, 'ASA 4': 4, 'ASA 5': 5}
        asa_num = asa_map.get(asa_class, 2)
        default_asa_factor = APP_CONFIG['DEFAULTS']['ASA_FACTORS'].get(asa_num, 1.0)
        new_factor = db.update_asa_factor(asa_class, default_asa_factor, asa_adjustment)
        updates.append(
            f"**{asa_class} faktor:** {default_asa_factor:.2f} -> {new_factor:.2f}"
        )
        logger.info(f"Learned ASA factor: {asa_class}, adjustment={asa_adjustment:.3f}")
    except Exception as e:
        logger.error(f"Error updating ASA factor: {e}")

    # WEIGHT/BODY COMPOSITION LEARNING (4D: Weight, IBW, ABW, BMI)
    # Learn continuously across the full spectrum from super skinny to morbidly obese
    weight = current_inputs.get('weight', 0)
    height = current_inputs.get('height', 0)
    sex = current_inputs.get('sex', 'Man')

    if weight > 0 and height > 0:
        try:
            from calculation_engine import (
                calculate_bmi,
                calculate_ideal_body_weight,
                calculate_adjusted_body_weight
            )

            bmi = calculate_bmi(weight, height)
            ibw = calculate_ideal_body_weight(height, sex)
            abw = calculate_adjusted_body_weight(weight, ibw)

            # Calculate body composition ratios
            weight_to_ibw_ratio = weight / ibw if ibw > 0 else 1.0
            abw_to_ibw_ratio = abw / ibw if ibw > 0 else 1.0

            # Base learning magnitude for body composition
            body_comp_adjustment = learning_mag * 0.03 * (1 if needs_more else -1)

            # Learn from ACTUAL WEIGHT - FINE-GRAINED (every kg)
            # System learns: "Patients at 73kg need X adjustment"
            # Uses finest granularity: Every single kg (73, 74, 75, etc)
            try:
                from interpolation_engine import get_weight_bucket
                weight_bucket = get_weight_bucket(weight)
                new_factor = db.update_weight_bucket_learning(weight_bucket, 1.0, body_comp_adjustment)
                updates.append(
                    f"**Weight factor ({weight:.1f}kg -> {weight_bucket}kg):** -> {new_factor:.3f}"
                )
                logger.info(
                    f"Learned weight factor: actual_weight={weight:.1f}kg, "
                    f"bucket={weight_bucket}kg, adjustment={body_comp_adjustment:.3f}"
                )
            except Exception as e:
                logger.warning(f"Weight learning error: {e}")

            # Learn from IBW RATIO
            # System learns: "Patients at 180% of IBW need different dosing"
            try:
                ibw_ratio_bucket = get_ibw_ratio_bucket(weight_to_ibw_ratio)
                new_factor = db.update_body_composition_factor('ibw_ratio', ibw_ratio_bucket, 1.0, body_comp_adjustment
                )
                updates.append(
                    f"**IBW ratio ({weight_to_ibw_ratio:.1f}x):** -> {new_factor:.3f}"
                )
                logger.info(
                    f"Learned IBW ratio factor: weight={weight:.1f}, ibw={ibw:.1f}, "
                    f"ratio={weight_to_ibw_ratio:.2f}, adjustment={body_comp_adjustment:.3f}"
                )
            except Exception as e:
                logger.warning(f"IBW ratio learning not available: {e}")

            # Learn from ABW (for overweight/obese patients)
            # System learns: "Patients with ABW significantly different from IBW need adjustment"
            if weight > ibw * 1.2:  # Only learn ABW for overweight patients
                try:
                    abw_ratio_bucket = get_abw_ratio_bucket(abw_to_ibw_ratio)
                    new_factor = db.update_body_composition_factor('abw_ratio', abw_ratio_bucket, 1.0, body_comp_adjustment
                    )
                    updates.append(
                        f"**ABW ratio ({abw_to_ibw_ratio:.1f}x):** -> {new_factor:.3f}"
                    )
                    logger.info(
                        f"Learned ABW ratio factor: weight={weight:.1f}, ibw={ibw:.1f}, "
                        f"abw={abw:.1f}, ratio={abw_to_ibw_ratio:.2f}, "
                        f"adjustment={body_comp_adjustment:.3f}"
                    )
                except Exception as e:
                    logger.warning(f"ABW ratio learning not available: {e}")

            # Learn from BMI
            # System learns across the full BMI spectrum: 15, 20, 25, 30, 35, 40, 45+
            try:
                bmi_bucket = get_bmi_bucket(bmi)
                bmi_label = get_bmi_label(bmi)

                new_factor = db.update_body_composition_factor('bmi', bmi_bucket, 1.0, body_comp_adjustment
                )

                updates.append(
                    f"**BMI factor ({bmi:.1f} - {bmi_label}):** -> {new_factor:.3f}"
                )
                logger.info(
                    f"Learned BMI factor: bmi={bmi:.1f}, bucket={bmi_bucket}, "
                    f"adjustment={body_comp_adjustment:.3f}"
                )
            except Exception as e:
                logger.warning(f"BMI learning not available: {e}")

        except Exception as e:
            logger.error(f"Error in weight/body composition learning: {e}")

    # SEX FACTOR LEARNING
    # Learn if males/females need different dosing than calculated
    if sex in ['Man', 'Kvinna']:
        sex_adjustment = learning_mag * 0.03 * (1 if needs_more else -1)
        try:
            new_factor = db.update_sex_factor(sex, 1.0, sex_adjustment)
            sex_swedish = "Män" if sex == "Man" else "Kvinnor"
            updates.append(
                f"**{sex_swedish} faktor:** -> {new_factor:.2f}"
            )
            logger.info(f"Learned sex factor: {sex}, adjustment={sex_adjustment:.3f}")
        except Exception as e:
            logger.warning(f"Sex factor learning not available: {e}")

    # RENAL IMPAIRMENT LEARNING
    renal_impairment = current_inputs.get('renalImpairment', False)
    if renal_impairment:
        # Learn if renal impairment patients need more/less adjustment
        renal_adjustment = learning_mag * 0.04 * (1 if needs_more else -1)
        try:
            # Default renal factor is typically 0.75 (reduce dose)
            default_renal = APP_CONFIG['DEFAULTS'].get('RENAL_IMPAIRMENT_FACTOR', 0.75)
            new_factor = db.update_renal_factor(default_renal, renal_adjustment)
            updates.append(
                f"**Njursvikt faktor:** {default_renal:.2f} -> {new_factor:.2f}"
            )
            logger.info(f"Learned renal factor: adjustment={renal_adjustment:.3f}")
        except Exception as e:
            logger.warning(f"Renal factor learning not available: {e}")

    return updates


# ============================================================================
# NEW IN V5+V6: ADJUVANT PERCENTAGE & 3D PAIN LEARNING
# ============================================================================

def learn_adjuvant_percentage(
    user_id: int,
    requirement_data: Dict,
    current_inputs: Dict,
) -> list:
    """
    Learn adjuvant percentage-based potency from actual requirement (GLOBAL learning).

    Back-calculates: If adjuvants reduced requirements less/more than predicted,
    adjust their percentage reduction values.

    Args:
        user_id: User ID (for context, but learning is GLOBAL)
        requirement_data: From calculate_actual_requirement()
        current_inputs: Patient inputs including adjuvants used

    Returns:
        List of update messages
    """
    import config

    updates = []

    actual_req = requirement_data['actual_requirement']
    recommended = requirement_data['recommended']
    prediction_error = requirement_data['prediction_error']
    learning_mag = requirement_data['learning_magnitude']

    # Only learn if there's significant error AND adjuvants were used
    error_ratio = abs(prediction_error) / (recommended or 1)
    if error_ratio < 0.10:  # Less than 10% error, don't adjust adjuvants
        return updates

    # Determine if patient needed more/less opioid
    needs_more = prediction_error > 0  # actual > recommended
    needs_less = prediction_error < 0  # actual < recommended

    # Identify which adjuvants were used
    adjuvants_used = []

    # Check each adjuvant type
    if current_inputs.get('nsaid') and current_inputs.get('nsaid_choice') != 'Ej given':
        nsaid_choice = current_inputs.get('nsaid_choice')
        adjuvants_used.append(nsaid_choice)

    if current_inputs.get('catapressan'):
        adjuvants_used.append('catapressan')

    if current_inputs.get('droperidol'):
        adjuvants_used.append('droperidol')

    if current_inputs.get('ketamine_choice') and current_inputs['ketamine_choice'] != 'Ej given':
        ketamine_choice = current_inputs.get('ketamine_choice')
        adjuvants_used.append(ketamine_choice)

    if current_inputs.get('lidocaine') and current_inputs['lidocaine'] != 'Nej':
        adjuvants_used.append('lidocaine_infusion')

    if current_inputs.get('betapred') and current_inputs['betapred'] != 'Nej':
        adjuvants_used.append('betapred')

    # Learn for each adjuvant
    for adjuvant_name in adjuvants_used:
        try:
            # Find the adjuvant data in config
            drug_data = config.LÄKEMEDELS_DATA.get(adjuvant_name)
            if not drug_data or drug_data.get('class') != 'Adjuvant':
                continue

            default_potency = drug_data.get('potency_percent', 0.15)

            # Calculate adjustment
            # If needs_more: adjuvant was LESS effective than expected → reduce potency %
            # If needs_less: adjuvant was MORE effective than expected → increase potency %
            #
            # Adjustment is conservative - adjuvants are just one factor among many
            adjustment = learning_mag * 0.02 * (-1 if needs_more else 1)

            # Dampen adjustment if multiple adjuvants (can't tell which one to adjust)
            if len(adjuvants_used) > 1:
                adjustment *= 0.7

            # Update database
            new_potency = db.update_adjuvant_potency_percent(
                adjuvant_name,
                default_potency,
                adjustment
            )

            updates.append(
                f"**{drug_data['name']} potency:** {default_potency:.1%} -> {new_potency:.1%}"
            )

            logger.info(
                f"Learned adjuvant potency: {adjuvant_name}, "
                f"adjustment={adjustment:+.1%}, new_potency={new_potency:.1%}"
            )

        except Exception as e:
            logger.warning(f"Could not learn adjuvant {adjuvant_name}: {e}")

    return updates


def learn_procedure_3d_pain(
    user_id: int,
    requirement_data: Dict,
    current_inputs: Dict,
    procedures_df,
) -> list:
    """
    Learn procedure 3D pain profile from actual requirement (GLOBAL learning).

    Back-calculates: If adjuvants with certain pain profiles were more/less
    effective than expected, adjust procedure's 3D pain characteristics.

    Args:
        user_id: User ID (for context, but learning is GLOBAL)
        requirement_data: From calculate_actual_requirement()
        current_inputs: Patient inputs including adjuvants used
        procedures_df: Procedures dataframe

    Returns:
        List of update messages
    """
    import config

    updates = []

    procedure_id = current_inputs.get('procedure_id')
    if not procedure_id:
        return updates

    proc_data = procedures_df[procedures_df['id'] == procedure_id]
    if proc_data.empty:
        return updates

    actual_req = requirement_data['actual_requirement']
    recommended = requirement_data['recommended']
    prediction_error = requirement_data['prediction_error']
    learning_mag = requirement_data['learning_magnitude']

    # Only learn if significant error
    error_ratio = abs(prediction_error) / (recommended or 1)
    if error_ratio < 0.15:
        return updates

    # Get current procedure pain data
    default_base_mme = float(proc_data.iloc[0]['baseMME'])
    default_pain_somatic = float(proc_data.iloc[0].get('painTypeScore', 5))
    default_pain_visceral = float(proc_data.iloc[0].get('painVisceral', 5))
    default_pain_neuropathic = float(proc_data.iloc[0].get('painNeuropathic', 2))

    # Get learned 3D pain data
    learned_data = db.get_procedure_learning_3d(
        procedure_id,
        default_base_mme,
        default_pain_somatic,
        default_pain_visceral,
        default_pain_neuropathic
    )

    # Identify which adjuvants were used and their pain profiles
    adjuvants_used = []

    if current_inputs.get('nsaid') and current_inputs.get('nsaid_choice') != 'Ej given':
        nsaid_choice = current_inputs.get('nsaid_choice')
        drug_data = config.LÄKEMEDELS_DATA.get(nsaid_choice)
        if drug_data:
            adjuvants_used.append({
                'name': nsaid_choice,
                'somatic': drug_data.get('somatic_score', 5),
                'visceral': drug_data.get('visceral_score', 5),
                'neuropathic': drug_data.get('neuropathic_score', 2)
            })

    if current_inputs.get('ketamine_choice') and current_inputs['ketamine_choice'] != 'Ej given':
        ketamine_choice = current_inputs.get('ketamine_choice')
        drug_data = config.LÄKEMEDELS_DATA.get(ketamine_choice)
        if drug_data:
            adjuvants_used.append({
                'name': ketamine_choice,
                'somatic': drug_data.get('somatic_score', 5),
                'visceral': drug_data.get('visceral_score', 5),
                'neuropathic': drug_data.get('neuropathic_score', 2)
            })

    # If no adjuvants, can't learn 3D pain profile
    if not adjuvants_used:
        return updates

    # needs_more = adjuvants were LESS effective than expected
    # This could mean procedure pain profile doesn't match adjuvant profiles
    needs_more = prediction_error > 0

    # Calculate 3D pain adjustments
    # If adjuvants were less effective, procedure likely has pain dimensions
    # that adjuvants don't target well
    base_adjustment = learning_mag * 0.15

    # Average adjuvant pain profile
    avg_somatic = sum(a['somatic'] for a in adjuvants_used) / len(adjuvants_used)
    avg_visceral = sum(a['visceral'] for a in adjuvants_used) / len(adjuvants_used)
    avg_neuropathic = sum(a['neuropathic'] for a in adjuvants_used) / len(adjuvants_used)

    # If adjuvants were weak in a dimension and needs_more:
    # → procedure likely has MORE of that pain type
    # If adjuvants were strong in a dimension and needs_less:
    # → procedure likely has LESS of that pain type

    somatic_adjustment = 0
    visceral_adjustment = 0
    neuropathic_adjustment = 0

    if needs_more:
        # Adjuvants underperformed - increase pain dimensions where adjuvants were weak
        if avg_somatic < 7:
            somatic_adjustment = base_adjustment
        if avg_visceral < 7:
            visceral_adjustment = base_adjustment
        if avg_neuropathic < 7:
            neuropathic_adjustment = base_adjustment
    else:
        # Adjuvants overperformed - decrease pain dimensions where adjuvants were strong
        if avg_somatic >= 7:
            somatic_adjustment = -base_adjustment
        if avg_visceral >= 7:
            visceral_adjustment = -base_adjustment
        if avg_neuropathic >= 7:
            neuropathic_adjustment = -base_adjustment

    # Update 3D pain learning (also updates base MME)
    base_mme_adjustment = prediction_error * learning_mag * 0.1
    max_adjustment = default_base_mme * 0.25
    base_mme_adjustment = max(-max_adjustment, min(max_adjustment, base_mme_adjustment))

    try:
        result = db.update_procedure_learning_3d(
            procedure_id,
            default_base_mme,
            default_pain_somatic,
            default_pain_visceral,
            default_pain_neuropathic,
            base_mme_adjustment,
            somatic_adjustment,
            visceral_adjustment,
            neuropathic_adjustment
        )

        proc_name = proc_data.iloc[0]['name']

        # Report changes
        if base_mme_adjustment != 0:
            direction = "ökat" if base_mme_adjustment > 0 else "minskat"
            updates.append(
                f"**{proc_name} baseMME:** {learned_data['base_mme']:.1f} -> {result['base_mme']:.1f} "
                f"({direction} {abs(base_mme_adjustment):.1f})"
            )

        if somatic_adjustment != 0 or visceral_adjustment != 0 or neuropathic_adjustment != 0:
            updates.append(
                f"**{proc_name} 3D pain:** somatic {learned_data['pain_somatic']:.1f}→{result['pain_somatic']:.1f}, "
                f"visceral {learned_data['pain_visceral']:.1f}→{result['pain_visceral']:.1f}, "
                f"neuropathic {learned_data['pain_neuropathic']:.1f}→{result['pain_neuropathic']:.1f}"
            )

        logger.info(
            f"Learned 3D pain for {procedure_id}: "
            f"somatic={somatic_adjustment:+.2f}, visceral={visceral_adjustment:+.2f}, "
            f"neuropathic={neuropathic_adjustment:+.2f}"
        )

    except Exception as e:
        logger.error(f"Error updating 3D pain learning: {e}")

    return updates
