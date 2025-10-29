"""
Input Validation Module
=======================
Provides comprehensive validation for patient data and dose calculations.
"""

import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

# Constants for validation ranges
MIN_AGE = 0
MAX_AGE = 120
MIN_WEIGHT = 1.0
MAX_WEIGHT = 500.0
MIN_HEIGHT = 30.0
MAX_HEIGHT = 250.0
MIN_BMI = 10.0
MAX_BMI = 80.0

# Recommended dose thresholds (mg) for oxycodone
# NOTE: These apply ONLY to initial recommended dose from calculation (perioperative).
# Outcome data (given dose + UVA in PACU) is NOT validated - procedures may require >20 MME total.
RECOMMENDED_DOSE_THRESHOLD = 10.0  # Warn if recommended starting dose >10mg oxycodone
DANGEROUS_DOSE_THRESHOLD = 30.0  # Dangerous if >30mg - flag as unsafe

# Fentanyl ranges (for intraoperative use)
FENTANYL_HIGH_DOSE = 500  # mcg - warn above this


def validate_patient_inputs(inputs: Dict) -> Tuple[bool, List[str]]:
    """
    Validate all patient input data.

    Args:
        inputs: Dictionary containing patient data

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Age validation
    age = inputs.get('age', 0)
    if not age or age < MIN_AGE or age > MAX_AGE:
        errors.append(f"Ålder måste vara mellan {MIN_AGE} och {MAX_AGE} år")

    # Weight validation
    weight = inputs.get('weight', 0)
    if not weight or weight < MIN_WEIGHT or weight > MAX_WEIGHT:
        errors.append(f"Vikt måste vara mellan {MIN_WEIGHT} och {MAX_WEIGHT} kg")

    # Height validation
    height = inputs.get('height', 0)
    if not height or height < MIN_HEIGHT or height > MAX_HEIGHT:
        errors.append(f"Längd måste vara mellan {MIN_HEIGHT} och {MAX_HEIGHT} cm")

    # BMI validation (if calculated)
    bmi = inputs.get('bmi')
    if bmi and (bmi < MIN_BMI or bmi > MAX_BMI):
        errors.append(f"BMI är utanför normalt intervall ({MIN_BMI}-{MAX_BMI}). Kontrollera vikt och längd.")

    # Required fields
    if not inputs.get('procedure_id'):
        errors.append("Ingrepp måste väljas")

    if not inputs.get('sex'):
        errors.append("Kön måste anges")

    if not inputs.get('asa'):
        errors.append("ASA-klassificering måste anges")

    # Fentanyl dose validation
    fentanyl_dose = inputs.get('fentanylDose', 0)
    if fentanyl_dose < 0:
        errors.append("Fentanyldos kan inte vara negativ")

    # Operation time validation
    optime_minutes = inputs.get('optime_minutes', 0)
    if optime_minutes < 0:
        errors.append("Operationstid kan inte vara negativ")
    elif optime_minutes > 1440:  # 24 hours
        errors.append("VARNING: Operationstid överstiger 24 timmar. Kontrollera värdet.")

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_recommended_dose(dose: float) -> Tuple[bool, str, str]:
    """
    Validate RECOMMENDED dose from calculation (perioperative starting dose).

    This applies ONLY to the initial dose calculated by "Beräkna" button.
    Outcome data (given dose + UVA in PACU) is NOT validated.

    Args:
        dose: Recommended oxycodone dose in mg

    Returns:
        Tuple of (is_safe, severity_level, message)
        severity_level: 'OK', 'WARNING', or 'DANGER'
        is_safe: False if dose is dangerously high (>30mg), True otherwise
    """
    # Check for dangerous doses (>30mg)
    if dose > DANGEROUS_DOSE_THRESHOLD:
        msg = f"🛑 FARLIG DOS: {dose:.1f} mg är farligt hög. Maximal säker dos för perioperativ oxykodon är {DANGEROUS_DOSE_THRESHOLD} mg. Kontrollera beräkningen."
        logger.error(f"Dangerous recommended dose: {dose:.1f} mg exceeds safety threshold {DANGEROUS_DOSE_THRESHOLD} mg")
        return False, 'DANGER', msg

    # Check for high but not dangerous doses (>10mg)
    if dose > RECOMMENDED_DOSE_THRESHOLD:
        msg = f"⚠️ HÖG REKOMMENDERAD DOS: {dose:.1f} mg överstiger {RECOMMENDED_DOSE_THRESHOLD} mg. Överväg om denna startdos är lämplig för perioperativ användning."
        logger.warning(f"High recommended dose: {dose:.1f} mg exceeds threshold {RECOMMENDED_DOSE_THRESHOLD} mg")
        return True, 'WARNING', msg

    return True, 'OK', ''


def validate_fentanyl_dose(dose: float) -> Tuple[bool, str, str]:
    """
    Validate fentanyl dose (intraoperative).

    Args:
        dose: Fentanyl dose in mcg

    Returns:
        Tuple of (is_safe, severity_level, message)
    """
    if dose > FENTANYL_HIGH_DOSE:
        msg = f"⚠️ HÖG FENTANYLDOS: {dose} µg överstiger {FENTANYL_HIGH_DOSE} µg"
        logger.warning(f"High fentanyl dose: {dose} mcg")
        return True, 'WARNING', msg

    return True, 'OK', ''


def validate_outcome_data(outcome_data: Dict) -> Tuple[bool, List[str]]:
    """
    Validate outcome data before saving.

    NOTE: Dose amounts (givenDose, uvaDose) are NOT validated.
    PACU may require high total doses (>20 MME) - this is expected and allowed.

    Args:
        outcome_data: Dictionary containing outcome data

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Given dose validation - only check it's positive
    given_dose = outcome_data.get('givenDose', 0)
    if given_dose <= 0:
        errors.append("Given startdos måste vara större än 0")

    # VAS validation
    vas = outcome_data.get('vas')
    if vas is None or vas < 0 or vas > 10:
        errors.append("VAS måste vara mellan 0 och 10")

    # UVA dose validation - only check it's not negative
    uva_dose = outcome_data.get('uvaDose', 0)
    if uva_dose < 0:
        errors.append("UVA-dos kan inte vara negativ")

    # NO dose amount validation - PACU requirements vary widely

    # Postoperative time validation
    postop_minutes = outcome_data.get('postop_minutes', 0)
    if postop_minutes < 0:
        errors.append("Postoperativ tid kan inte vara negativ")

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_drug_contraindications(inputs: Dict) -> List[str]:
    """
    Check for drug contraindications based on patient characteristics.

    Args:
        inputs: Patient input data

    Returns:
        List of warning messages
    """
    warnings = []

    renal_impairment = inputs.get('renalImpairment', False)
    nsaid_choice = inputs.get('nsaid_choice', 'Ej given')

    # NSAID contraindication with renal impairment
    if renal_impairment and nsaid_choice != 'Ej given':
        warnings.append(
            f"⚠️ KONTRAINDIKATION: {nsaid_choice} ska undvikas vid nedsatt njurfunktion (GFR<50)"
        )

    # Check high-dose opioids in elderly
    age = inputs.get('age', 0)
    if age >= 80:
        opioid_history = inputs.get('opioidHistory', 'Opioidnaiv')
        if opioid_history == 'Opioidnaiv':
            warnings.append(
                "⚠️ VARNING: Högt åldrars patient (≥80 år). Överväg lägre startdos och noggrann övervakning."
            )

    # Check multiple sedatives
    has_droperidol = inputs.get('droperidol', False)
    has_ketamine = inputs.get('ketamine_choice', 'Ej given') != 'Ej given'
    has_catapressan = inputs.get('catapressan_dose', 0) > 0

    sedative_count = sum([has_droperidol, has_ketamine, has_catapressan])
    if sedative_count >= 2:
        warnings.append(
            "⚠️ OBSERVATION: Multipla sedativa medel. Öka övervakning för andningsdepression."
        )

    return warnings
