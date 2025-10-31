import math
import logging
from typing import Dict, Tuple
import database as db
import auth
from config import APP_CONFIG, LÄKEMEDELS_DATA, get_drug_by_ui_choice, calculate_3d_mismatch_penalty
from body_composition_utils import (
    get_weight_bucket,
    get_ibw_ratio_bucket,
    get_abw_ratio_bucket,
    get_bmi_bucket
)
from interpolation_engine import interpolate_age_factor, interpolate_weight_factor

# Configure logging
logger = logging.getLogger(__name__)

# Age calculation constants
MIN_AGE_FACTOR = 0.4
REFERENCE_AGE = 65
AGE_STEEPNESS = 20

# Weight calculation constants
WEIGHT_ADJUSTMENT_FACTOR = 0.4
OVERWEIGHT_THRESHOLD_MULTIPLIER = 1.2
MIN_IDEAL_WEIGHT = 40

# Height adjustment constants (for IBW calculation)
MALE_HEIGHT_ADJUSTMENT = 100
FEMALE_HEIGHT_ADJUSTMENT = 105

# Unit conversion constants
CM_TO_METERS = 100

def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """
    Beräkna BMI enligt SI-enheter.

    Args:
        weight_kg: Vikt i kg
        height_cm: Längd i cm

    Returns:
        BMI (kg/m²)
    """
    if height_cm <= 0 or weight_kg <= 0:
        return 0.0
    height_m = height_cm / CM_TO_METERS  # Konvertera cm till meter
    return weight_kg / (height_m * height_m)

def calculate_ideal_body_weight(height_cm: float, sex: str = 'Man') -> float:
    """
    Beräkna ideal kroppsvikt (IBW).

    Args:
        height_cm: Längd i cm
        sex: Kön ('Man' eller 'Kvinna')

    Returns:
        Ideal body weight i kg
    """
    if sex == 'Kvinna':
        ibw = height_cm - FEMALE_HEIGHT_ADJUSTMENT
    else:
        ibw = height_cm - MALE_HEIGHT_ADJUSTMENT
    return max(MIN_IDEAL_WEIGHT, ibw)

def calculate_adjusted_body_weight(actual_weight: float, height_cm: float, sex: str = 'Man') -> float:
    """
    Beräkna justerad kroppsvikt (ABW) för överviktiga patienter.

    Args:
        actual_weight: Verklig vikt i kg
        height_cm: Längd i cm
        sex: Kön ('Man' eller 'Kvinna')

    Returns:
        Adjusted body weight i kg
    """
    ibw = calculate_ideal_body_weight(height_cm, sex)
    if actual_weight <= ibw * OVERWEIGHT_THRESHOLD_MULTIPLIER:
        return actual_weight
    overvikt = actual_weight - ibw
    abw = ibw + (overvikt * WEIGHT_ADJUSTMENT_FACTOR)
    return abw

def calculate_lean_body_mass(weight_kg: float, height_cm: float, sex: str = 'Man') -> float:
    """
    Beräkna lean body mass (LBM) using James formula.

    LBM is fat-free mass and is important for drug distribution calculations,
    especially for lipophobic drugs like oxycodone which distribute primarily
    into lean tissue.

    James formula:
    - Men: LBM = 1.10 * W - 128 * (W/H)²
    - Women: LBM = 1.07 * W - 148 * (W/H)²
    where W = weight in kg, H = height in meters

    Args:
        weight_kg: Actual weight in kg
        height_cm: Height in cm
        sex: 'Man' or 'Kvinna'

    Returns:
        Lean body mass in kg

    Example:
        >>> calculate_lean_body_mass(80, 180, 'Man')
        63.6  # kg
    """
    if height_cm <= 0 or weight_kg <= 0:
        return weight_kg * 0.75  # Rough estimate: 75% of total body weight

    height_m = height_cm / 100.0

    if sex == 'Kvinna':
        # James formula for women: LBM = 1.07*W - 148*(W/H)²
        lbm = 1.07 * weight_kg - 148 * ((weight_kg / height_m) ** 2)
    else:
        # James formula for men: LBM = 1.10*W - 128*(W/H)²
        lbm = 1.10 * weight_kg - 128 * ((weight_kg / height_m) ** 2)

    # Ensure LBM is reasonable (at least 40% of body weight, max 95%)
    lbm = max(weight_kg * 0.40, min(weight_kg * 0.95, lbm))

    return lbm

def calculate_age_factor(age: int) -> float:
    """
    Beräkna åldersfaktor för dos-justering.

    Patienter över {REFERENCE_AGE} år får exponentiellt minskad dos.

    Args:
        age: Ålder i år

    Returns:
        Ålder-justeringsfaktor (0.4-1.0)
    """
    if age <= REFERENCE_AGE:
        return 1.0
    return max(MIN_AGE_FACTOR, math.exp((REFERENCE_AGE - age) / AGE_STEEPNESS))

def apply_learnable_adjuvant(
    base_ime_before_adjuvants: float,
    drug_data: dict,
    procedure_pain_3d: dict,
    user_id: int = None
) -> float:
    """
    Beräkna adjuvant-reduktion med 3D pain matching och percentage-based potency.

    Args:
        base_ime_before_adjuvants: Base IME efter patient factors, före adjuvants
        drug_data: Dictionary från LÄKEMEDELS_DATA
        procedure_pain_3d: {'somatic': X, 'visceral': Y, 'neuropathic': Z}
        user_id: User ID för global inlärning

    Returns:
        IME reduction från denna adjuvant
    """
    if not drug_data:
        return 0.0

    # Hämta basdata - nu percentage-based
    base_potency_percent = drug_data.get('potency_percent', 0.0)
    drug_name = drug_data.get('name', '')
    drug_pain_3d = {
        'somatic': drug_data['somatic_score'],
        'visceral': drug_data['visceral_score'],
        'neuropathic': drug_data['neuropathic_score']
    }

    # IMPLEMENTED IN V5: Global percentage-based adjuvant learning
    if user_id:
        try:
            # Get learned percentage from global database
            # Note: Uses drug key from LÄKEMEDELS_DATA (e.g., 'ibuprofen', 'ketamine_small_bolus')
            # Need to match against database keys
            drug_key = next((k for k, v in LÄKEMEDELS_DATA.items() if v.get('name') == drug_name), None)
            if drug_key:
                potency_percent = db.get_adjuvant_potency_percent(drug_key, base_potency_percent)
            else:
                potency_percent = base_potency_percent
        except Exception as e:
            logger.warning(f"Could not get learned adjuvant potency for {drug_name}: {e}")
            potency_percent = base_potency_percent
    else:
        potency_percent = base_potency_percent

    # Beräkna 3D mismatch penalty
    penalty = calculate_3d_mismatch_penalty(procedure_pain_3d, drug_pain_3d)

    # Beräkna reduktion som % av base IME (inte nuvarande IME!)
    # Detta säkerställer att adjuvants skalar korrekt med procedur-storlek
    effective_reduction = base_ime_before_adjuvants * potency_percent * penalty

    return effective_reduction

def _get_initial_ime_and_pain_type(inputs, procedures_df):
    user_id = auth.get_current_user_id()
    procedure = procedures_df[procedures_df['id'] == inputs['procedure_id']].iloc[0]
    default_base_ime = float(procedure['baseIME'])

    # Hämta 3D pain scores (eller använd gamla painTypeScore som somatisk default)
    default_pain_somatic = float(procedure.get('painTypeScore', 5))
    default_pain_visceral = float(procedure.get('painVisceral', 5))
    default_pain_neuropathic = float(procedure.get('painNeuropathic', 2))

    if user_id:
        # IMPLEMENTED IN V6: Global 3D pain learning
        try:
            learned = db.get_procedure_learning_3d(
                inputs['procedure_id'],
                default_base_ime,
                default_pain_somatic,
                default_pain_visceral,
                default_pain_neuropathic
            )
            return learned['base_ime'], {
                'somatic': learned['pain_somatic'],
                'visceral': learned['pain_visceral'],
                'neuropathic': learned['pain_neuropathic']
            }, procedure
        except Exception as e:
            logger.warning(f"Could not get 3D pain learning for {inputs['procedure_id']}: {e}")
            # Fall back to old 1D learning
            learned = db.get_procedure_learning(user_id, inputs['procedure_id'], default_base_ime, default_pain_somatic)
            return learned['base_ime'], {
                'somatic': learned.get('pain_type', default_pain_somatic),
                'visceral': default_pain_visceral,
                'neuropathic': default_pain_neuropathic
            }, procedure

    return default_base_ime, {
        'somatic': default_pain_somatic,
        'visceral': default_pain_visceral,
        'neuropathic': default_pain_neuropathic
    }, procedure

def _apply_patient_factors(ime, inputs):
    user_id = auth.get_current_user_id()

    # Age factor with INTERPOLATION
    # Uses fine-grained buckets (every year) with intelligent interpolation from nearby ages
    default_age_factor = calculate_age_factor(inputs['age'])
    if user_id:
        try:
            from interpolation_engine import interpolate_age_factor
            result = interpolate_age_factor(inputs['age'], default_age_factor)
            age_factor = result['age_factor']
            # Log interpolation method for transparency
            if result['method'] == 'interpolated':
                logger.debug(f"Age {inputs['age']}: Interpolated from {result.get('nearby_count', 0)} nearby ages")
        except Exception as e:
            logger.warning(f"Age interpolation failed, using default: {e}")
            age_factor = default_age_factor
    else:
        age_factor = default_age_factor
    ime *= age_factor

    # ASA factor
    asa_map = {'ASA 1': 1, 'ASA 2': 2, 'ASA 3': 3, 'ASA 4': 4, 'ASA 5': 5}
    asa_class = inputs.get('asa', 'ASA 2')
    asa_num = asa_map.get(asa_class, 2)
    default_asa_factor = APP_CONFIG['DEFAULTS']['ASA_FACTORS'].get(asa_num, 1.0)
    asa_factor = db.get_asa_factor(asa_class, default_asa_factor) if user_id else default_asa_factor
    ime *= asa_factor

    # Sex factor
    sex = inputs.get('sex', 'Man')
    default_sex_factor = 1.0
    sex_factor = db.get_sex_factor(sex, default_sex_factor) if user_id else default_sex_factor
    ime *= sex_factor

    # 4D Body composition learning (NEW)
    # Uses BUCKETING for proximity matching - similar patients benefit from each other's learning
    # Even if we've never seen this exact patient, we learn from nearby buckets
    if user_id:
        weight = inputs.get('weight', 0)
        height = inputs.get('height', 0)
        if weight > 0 and height > 0:
            bmi = calculate_bmi(weight, height)
            ibw = calculate_ideal_body_weight(height, sex)
            abw = calculate_adjusted_body_weight(weight, height, sex)

            # Dimension 1: ACTUAL WEIGHT with INTERPOLATION (every kg)
            # 73.4kg patient (bucket=73) can interpolate from 70kg, 72kg, 75kg, etc
            try:
                from interpolation_engine import interpolate_weight_factor
                result = interpolate_weight_factor(weight, 1.0)
                body_comp_factor = result['weight_factor']
                if result['method'] == 'interpolated':
                    logger.debug(f"Weight {weight:.1f}kg: Interpolated from {result.get('nearby_count', 0)} nearby weights")
            except Exception as e:
                logger.warning(f"Weight interpolation failed, using default: {e}")
                weight_bucket = get_weight_bucket(weight)
                body_comp_factor = db.get_body_composition_factor('weight', weight_bucket, 1.0) if hasattr(db, 'get_body_composition_factor') else 1.0
            ime *= body_comp_factor

            if ibw > 0:
                # Dimension 2: IBW RATIO (0.1 increments)
                # 1.47x patient benefits from learning on 1.5x bucket
                ibw_ratio = weight / ibw
                ibw_ratio_bucket = get_ibw_ratio_bucket(ibw_ratio)
                ibw_factor = db.get_body_composition_factor('ibw_ratio', ibw_ratio_bucket, 1.0)
                ime *= ibw_factor

                # Dimension 3: ABW RATIO (for overweight patients, 0.1 increments)
                # 1.34x ABW patient benefits from learning on 1.3x bucket
                if weight > ibw * 1.2:
                    abw_ratio = abw / ibw
                    abw_ratio_bucket = get_abw_ratio_bucket(abw_ratio)
                    abw_factor = db.get_body_composition_factor('abw_ratio', abw_ratio_bucket, 1.0)
                    ime *= abw_factor

            # Dimension 4: BMI (7 categories)
            # BMI 33.2 patient benefits from learning on obese class I (32) bucket
            bmi_bucket = get_bmi_bucket(bmi)
            bmi_factor = db.get_body_composition_factor('bmi', bmi_bucket, 1.0)
            ime *= bmi_factor

    # Opioid tolerance
    if inputs['opioidHistory'] == 'Opioidtolerant':
        default_opioid_factor = APP_CONFIG['DEFAULTS']['OPIOID_TOLERANCE_FACTOR']
        opioid_factor = db.get_opioid_tolerance_factor() if user_id else default_opioid_factor
        ime *= opioid_factor

    # Pain threshold
    if inputs['lowPainThreshold']:
        default_pain_threshold_factor = APP_CONFIG['DEFAULTS']['PAIN_THRESHOLD_FACTOR']
        pain_threshold_factor = db.get_pain_threshold_factor() if user_id else default_pain_threshold_factor
        ime *= pain_threshold_factor

    # Renal impairment
    if inputs.get('renalImpairment', False):
        default_renal_factor = APP_CONFIG['DEFAULTS']['RENAL_IMPAIRMENT_FACTOR']
        renal_factor = db.get_renal_factor() if user_id else default_renal_factor
        ime *= renal_factor

    return ime

def _apply_adjuvants(base_ime_before_adjuvants, inputs, pain_type_3d):
    """
    Applicera alla adjuvanter med unified LÄKEMEDELS_DATA.

    VIKTIGT: Alla adjuvant-reductions är percentage-based och beräknas från
    base_ime_before_adjuvants, inte från varandra. Detta säkerställer korrekt
    skalning för både små och stora procedurer.

    Args:
        base_ime_before_adjuvants: Base IME efter patient factors, före adjuvants
        inputs: Patient inputs
        pain_type_3d: {'somatic': X, 'visceral': Y, 'neuropathic': Z}

    Returns:
        Final IME efter alla adjuvant-reductions
    """
    user_id = auth.get_current_user_id()
    total_reduction = 0.0

    # NSAID
    nsaid_choice = inputs.get('nsaid_choice', 'Ej given')
    if nsaid_choice != 'Ej given':
        drug_data = get_drug_by_ui_choice('nsaid', nsaid_choice)
        if drug_data:
            reduction = apply_learnable_adjuvant(base_ime_before_adjuvants, drug_data, pain_type_3d, user_id)
            total_reduction += reduction

    # Catapressan (dosbaserad - skala percentage med dos)
    catapressan_dose = inputs.get('catapressan_dose', 0)
    if catapressan_dose > 0:
        drug_data = LÄKEMEDELS_DATA.get('clonidine')
        if drug_data:
            # Skala potensen baserat på dos
            ref_dose = drug_data.get('reference_dose_mcg', 75)
            dose_scaling = catapressan_dose / ref_dose
            scaled_drug_data = drug_data.copy()
            scaled_drug_data['potency_percent'] = drug_data['potency_percent'] * dose_scaling
            reduction = apply_learnable_adjuvant(base_ime_before_adjuvants, scaled_drug_data, pain_type_3d, user_id)
            total_reduction += reduction

    # Droperidol
    if inputs.get('droperidol', False):
        drug_data = LÄKEMEDELS_DATA.get('droperidol')
        if drug_data:
            reduction = apply_learnable_adjuvant(base_ime_before_adjuvants, drug_data, pain_type_3d, user_id)
            total_reduction += reduction

    # Ketamin
    ketamine_choice = inputs.get('ketamine_choice', 'Ej given')
    if ketamine_choice != 'Ej given':
        drug_data = get_drug_by_ui_choice('ketamine', ketamine_choice)
        if drug_data:
            reduction = apply_learnable_adjuvant(base_ime_before_adjuvants, drug_data, pain_type_3d, user_id)
            total_reduction += reduction

    # Lidokain
    lidocaine_choice = inputs.get('lidocaine', 'Nej')
    if lidocaine_choice != 'Nej':
        drug_data = get_drug_by_ui_choice('lidocaine', lidocaine_choice)
        if drug_data:
            reduction = apply_learnable_adjuvant(base_ime_before_adjuvants, drug_data, pain_type_3d, user_id)
            total_reduction += reduction

    # Betapred
    betapred_choice = inputs.get('betapred', 'Nej')
    if betapred_choice != 'Nej':
        drug_data = get_drug_by_ui_choice('betapred', betapred_choice)
        if drug_data:
            reduction = apply_learnable_adjuvant(base_ime_before_adjuvants, drug_data, pain_type_3d, user_id)
            total_reduction += reduction

    # Sevoflurane
    if inputs.get('sevoflurane', False):
        drug_data = LÄKEMEDELS_DATA.get('sevoflurane')
        if drug_data:
            reduction = apply_learnable_adjuvant(base_ime_before_adjuvants, drug_data, pain_type_3d, user_id)
            total_reduction += reduction

    # Infiltration
    if inputs.get('infiltration', False):
        drug_data = LÄKEMEDELS_DATA.get('infiltration')
        if drug_data:
            reduction = apply_learnable_adjuvant(base_ime_before_adjuvants, drug_data, pain_type_3d, user_id)
            total_reduction += reduction

    # Apply total reduction
    final_ime = max(0, base_ime_before_adjuvants - total_reduction)

    return final_ime

def _apply_synergy_and_safety_limits(ime, inputs, base_ime_before_adjuvants):
    user_id = auth.get_current_user_id()
    if user_id:
        drug_combo = db.get_drug_combination_key(inputs)
        if drug_combo:
            synergy_factor = db.get_synergy_factor(drug_combo)
            ime *= synergy_factor

    min_ime_allowed = base_ime_before_adjuvants * APP_CONFIG['ADJUVANT_SAFETY_LIMIT_FACTOR']
    ime = max(ime, min_ime_allowed)

    return ime

def _apply_fentanyl_pharmacokinetics(ime, inputs):
    user_id = auth.get_current_user_id()
    fentanyl_remaining_fraction = db.get_fentanyl_remaining_fraction() if user_id else APP_CONFIG['FENTANYL_HALFLIFE_FRACTION']
    fentanyl_ime_remaining = (inputs['fentanylDose'] / 100.0) * APP_CONFIG['FENTANYL_IME_CONVERSION_FACTOR'] * fentanyl_remaining_fraction
    return max(0, ime - fentanyl_ime_remaining)

def _apply_weight_adjustment(ime, inputs):
    actual_weight = inputs.get('weight', APP_CONFIG['REFERENCE_WEIGHT_KG'])
    height_cm = inputs.get('height', 175)
    sex = inputs.get('sex', 'Man')

    if height_cm > 0 and actual_weight > 0:
        abw = calculate_adjusted_body_weight(actual_weight, height_cm, sex)
        weight_factor = abw / APP_CONFIG['REFERENCE_WEIGHT_KG']
        ime *= weight_factor

    return ime

def _apply_temporal_adjustments(ime, temporal_doses, pain_type_3d):
    """
    Justera IME baserat på temporal dosering.

    Beräknar kvarvarande fentanyl vid opslut och adjuvant-effekt vid postop tidpunkt.

    Args:
        ime: Current IME
        temporal_doses: List of temporal dose dictionaries
        pain_type_3d: Procedure pain profile

    Returns:
        Adjusted IME
    """
    from pharmacokinetics import (
        calculate_temporal_fentanyl_ime_at_opslut,
        calculate_temporal_adjuvant_reduction_at_postop
    )

    # Beräkna kvarvarande fentanyl IME vid opslut
    fentanyl_ime_at_opslut = calculate_temporal_fentanyl_ime_at_opslut(temporal_doses)
    ime -= fentanyl_ime_at_opslut

    # Beräkna adjuvant-reduktion vid postop tid (default 60 min)
    adjuvant_reduction = calculate_temporal_adjuvant_reduction_at_postop(
        temporal_doses,
        LÄKEMEDELS_DATA,
        postop_time=60
    )
    ime -= adjuvant_reduction

    # Säkerställ att IME inte blir negativ
    ime = max(0, ime)

    return ime

def _get_composite_key(inputs, procedure):
    asa_map = {'ASA 1': 1, 'ASA 2': 2, 'ASA 3': 3, 'ASA 4': 4, 'ASA 5': 5}
    asa_num = asa_map.get(inputs.get('asa', 'ASA 2'), 2)
    opioid_char = 'T' if inputs['opioidHistory'] == 'Opioidtolerant' else 'N'

    nsaid_map = {
        'Ibuprofen 400mg': 'NIb',
        'Ketorolac 30mg': 'NKe',
        'Parecoxib 40mg': 'NPa',
    }
    nsaid_char = nsaid_map.get(inputs.get('nsaid_choice', 'Ej given'), 'x')

    catapressan_char = 'C' if inputs.get('catapressan_dose', 0) > 0 else 'x'
    droperidol_char = 'D' if inputs.get('droperidol', False) else 'x'
    ketamine_chars = {'Liten bolus (0.05-0.1 mg/kg)': 'KBl', 'Stor bolus (0.5-1 mg/kg)': 'KBs', 'Liten infusion (0.10-0.15 mg/kg/h)': 'KIl', 'Stor infusion (3 mg/kg/h)': 'KIs'}
    ketamine_char = ketamine_chars.get(inputs.get('ketamine_choice', 'Ej given'), 'x')
    lidocaine_char = 'LB' if inputs.get('lidocaine', 'Nej') == 'Bolus' else ('LI' if inputs.get('lidocaine', 'Nej') == 'Infusion' else 'x')
    betapred_char = 'B4' if inputs.get('betapred', 'Nej') == '4 mg' else ('B8' if inputs.get('betapred', 'Nej') == '8 mg' else 'x')

    return f"{procedure['id']}-ASA{asa_num}-{opioid_char}-{nsaid_char}-{catapressan_char}-{droperidol_char}-{ketamine_char}-{lidocaine_char}-{betapred_char}"

def calculate_rule_based_dose(inputs, procedures_df, temporal_doses=None):
    """
    Beräkna regelbaserad dos med optional temporal dosering.

    Args:
        inputs: Patient inputs dictionary
        procedures_df: Procedures dataframe
        temporal_doses: List of temporal dose dictionaries (optional)
    """
    try:
        ime, pain_type_3d, procedure = _get_initial_ime_and_pain_type(inputs, procedures_df)
        ime = _apply_patient_factors(ime, inputs)
        base_ime_before_adjuvants = ime
        ime = _apply_adjuvants(ime, inputs, pain_type_3d)
        ime = _apply_synergy_and_safety_limits(ime, inputs, base_ime_before_adjuvants)
        ime = _apply_fentanyl_pharmacokinetics(ime, inputs)

        # Apply temporal dosing adjustments if provided
        if temporal_doses:
            ime = _apply_temporal_adjustments(ime, temporal_doses, pain_type_3d)

        ime = _apply_weight_adjustment(ime, inputs)

        composite_key = _get_composite_key(inputs, procedure)
        user_id = auth.get_current_user_id()
        if user_id:
            calibration_factor = db.get_calibration_factor(user_id, composite_key)
            ime *= calibration_factor

        final_dose = round(max(0, ime / 0.25)) * 0.25

        actual_weight = inputs.get('weight', 75)
        height_cm = inputs.get('height', 175)
        sex = inputs.get('sex', 'Man')
        ibw = calculate_ideal_body_weight(height_cm, sex) if height_cm > 0 else None
        abw = calculate_adjusted_body_weight(actual_weight, height_cm, sex) if height_cm > 0 and actual_weight > 0 else None

        return {
            'finalDose': final_dose,
            'compositeKey': composite_key,
            'procedure': procedure.to_dict(),
            'engine': "Regelmotor",
            'ibw': ibw,
            'abw': abw,
            'actual_weight': actual_weight,
            'pain_type_3d': pain_type_3d
        }
    except (KeyError, IndexError):
        return {}

# Learning functions from old code (unchanged for now)
def calculate_selectivity_adjustment(vas, procedure_pain_type, adjuvant_selectivity, rescue_given):
    mismatch = abs(procedure_pain_type - adjuvant_selectivity)
    outcome_good = (vas <= 3 and not rescue_given)

    if mismatch > 5 and outcome_good:
        return +0.5
    elif mismatch < 2 and not outcome_good:
        return -0.3
    else:
        return 0.0

def calculate_potency_adjustment(vas, rescue_dose, respiratory_issue):
    if respiratory_issue:
        return -0.2

    if rescue_dose > 5:
        return -0.8
    elif rescue_dose > 0:
        return -0.4
    elif vas <= 2:
        return +0.3
    elif vas <= 3:
        return +0.1
    elif vas > 5:
        return -0.3
    else:
        return 0.0

def calculate_synergy_adjustment(overall_outcome_score):
    if overall_outcome_score < -0.3:
        return +0.4
    elif overall_outcome_score < 0:
        return +0.2
    elif overall_outcome_score > 0.5:
        return -0.4
    elif overall_outcome_score > 0.2:
        return -0.2
    else:
        return 0.0

def _calculate_learning_adjustment(outcome, final_dose, num_proc_cases):
    cfg = APP_CONFIG['LEARNING']
    if num_proc_cases < 3: base_learning_rate = cfg['INITIAL_LEARNING_RATE']
    elif num_proc_cases < 10: base_learning_rate = cfg['INTERMEDIATE_LEARNING_RATE']
    elif num_proc_cases < 20: base_learning_rate = cfg['ADVANCED_LEARNING_RATE']
    else: base_learning_rate = cfg['INITIAL_LEARNING_RATE'] / (1 + cfg['LEARNING_RATE_DECAY'] * num_proc_cases)

    postop_reason = outcome.get('postop_reason', 'Normal återhämtning')
    vas_error = math.sqrt(outcome['vas'] - 4) / math.sqrt(6) if outcome['vas'] > 4 else 0
    uva_dose_error = math.sqrt(min(1, outcome['uvaDose'] / 10)) if outcome['uvaDose'] > 0 else 0
    total_error = max(vas_error, uva_dose_error)

    rescue_boost = 1.0
    if outcome.get('uvaDose', 0) > 7: rescue_boost = cfg['RESCUE_BOOST_HIGH']
    elif outcome.get('uvaDose', 0) > 4: rescue_boost = cfg['RESCUE_BOOST_MEDIUM']

    is_outlier = outcome['vas'] > 8 or outcome.get('uvaDose', 0) > 15
    outlier_damping = cfg['OUTLIER_DAMPING_FACTOR'] if is_outlier else 1.0

    adjustment = 0
    if postop_reason == "Smärtgenombrott/redosering (för låg dos)" or total_error > 0:
        adjustment = (base_learning_rate + (total_error * cfg['ERROR_ADJUSTMENT_FACTOR'])) * rescue_boost * outlier_damping
    elif postop_reason == "Andningspåverkan/trötthet (för hög dos)" or outcome['respiratory_status'] == 'sederad djupt' or outcome.get('severe_fatigue', False):
        adjustment = base_learning_rate * cfg['RESPIRATORY_ADJUSTMENT_FACTOR'] * outlier_damping
    elif postop_reason == "Klinisk rutin (t.ex. blödningsrisk)" and total_error > 0:
        adjustment = (base_learning_rate + (total_error * cfg['ERROR_ADJUSTMENT_FACTOR'])) * outlier_damping
    elif outcome['givenDose'] < final_dose and outcome['vas'] <= 3:
        reduction_ratio = (final_dose - outcome['givenDose']) / (final_dose or 1)
        adjustment = -(base_learning_rate * reduction_ratio * cfg['LOW_DOSE_SUCCESS_ADJUSTMENT_MULTIPLIER']) * outlier_damping

    return adjustment

