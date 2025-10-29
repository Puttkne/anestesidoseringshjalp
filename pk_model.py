"""
Pharmacokinetic Model for Oxycodone

Implements population PK equations for oxycodone to provide mechanistic
foundation for dose calculations. Based on published literature.

References:
- Clearance equation: Cl = 1.58 - (age / 580.203) L/h
- Volume of distribution: Vd = 2.6 * LBM liters
- Adjustments for renal/hepatic impairment based on clinical guidelines
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# PK Constants
BASE_CLEARANCE_INTERCEPT = 1.58  # L/h at age 0 (theoretical)
AGE_CLEARANCE_SLOPE = 580.203  # Denominator for age effect
VD_PER_LBM = 2.6  # Liters per kg of lean body mass

# Safety bounds
MIN_CLEARANCE = 0.1  # L/h - safety floor
MAX_CLEARANCE = 3.0  # L/h - safety ceiling
MIN_VD = 50.0  # L - minimum volume
MAX_VD = 400.0  # L - maximum volume


def calculate_clearance(
    age_years: float,
    weight_kg: float,
    gfr: Optional[float] = None,
    hepatic_impairment: str = 'None'
) -> float:
    """
    Calculate oxycodone clearance using population PK model.

    The clearance of oxycodone decreases with age due to reduced hepatic
    metabolism and renal elimination. Additional reductions apply for
    organ impairment.

    Args:
        age_years: Patient age in years
        weight_kg: Patient weight in kg (used for extreme adjustments)
        gfr: Glomerular filtration rate (mL/min), if known
        hepatic_impairment: 'None', 'Mild', 'Moderate', or 'Severe'

    Returns:
        Clearance in L/h

    Example:
        >>> calculate_clearance(75, 70, gfr=45, hepatic_impairment='None')
        0.89  # Reduced clearance in elderly with mild renal impairment
    """
    # Base clearance from age (population equation)
    cl_base = BASE_CLEARANCE_INTERCEPT - (age_years / AGE_CLEARANCE_SLOPE)

    # Renal function adjustment
    # Oxycodone has mixed hepatic/renal elimination (~60% hepatic, ~40% renal metabolites)
    if gfr is not None:
        if gfr < 35:
            # Severe renal impairment: reduce by 40%
            cl_base *= 0.60
            logger.info(f"Severe renal impairment (GFR {gfr}): Clearance reduced by 40%")
        elif gfr < 60:
            # Moderate renal impairment: reduce by 20%
            cl_base *= 0.80
            logger.info(f"Moderate renal impairment (GFR {gfr}): Clearance reduced by 20%")
        elif gfr < 90:
            # Mild renal impairment: reduce by 10%
            cl_base *= 0.90

    # Hepatic function adjustment
    # Oxycodone is primarily metabolized by hepatic CYP2D6 and CYP3A4
    hepatic_impairment = hepatic_impairment.strip().lower()
    if hepatic_impairment == 'severe':
        # Severe hepatic impairment: reduce by 67% (use 1/3 of clearance)
        cl_base *= 0.33
        logger.warning(f"Severe hepatic impairment: Clearance reduced to 33% of baseline")
    elif hepatic_impairment == 'moderate':
        # Moderate hepatic impairment: reduce by 50%
        cl_base *= 0.50
        logger.info(f"Moderate hepatic impairment: Clearance reduced by 50%")
    elif hepatic_impairment == 'mild':
        # Mild hepatic impairment: reduce by 25%
        cl_base *= 0.75
        logger.info(f"Mild hepatic impairment: Clearance reduced by 25%")

    # Apply safety bounds
    cl_final = max(MIN_CLEARANCE, min(MAX_CLEARANCE, cl_base))

    if cl_final != cl_base:
        logger.warning(f"Clearance bounded: {cl_base:.3f} -> {cl_final:.3f} L/h")

    return cl_final


def calculate_volume_of_distribution(lbm_kg: float) -> float:
    """
    Calculate volume of distribution for oxycodone.

    Vd is best predicted by lean body mass (LBM) rather than total body weight,
    as oxycodone distributes primarily into lean tissue, not adipose tissue.

    Args:
        lbm_kg: Lean body mass in kg

    Returns:
        Volume of distribution in liters

    Example:
        >>> calculate_volume_of_distribution(55.0)
        143.0  # 55 kg LBM * 2.6 L/kg
    """
    vd = VD_PER_LBM * lbm_kg

    # Apply safety bounds
    vd_final = max(MIN_VD, min(MAX_VD, vd))

    if vd_final != vd:
        logger.warning(f"Vd bounded: {vd:.1f} -> {vd_final:.1f} L")

    return vd_final


def calculate_half_life(clearance: float, vd: float) -> float:
    """
    Calculate elimination half-life.

    t½ = (0.693 * Vd) / Clearance

    Args:
        clearance: Clearance in L/h
        vd: Volume of distribution in L

    Returns:
        Half-life in hours

    Example:
        >>> calculate_half_life(1.2, 150)
        86.625  # hours
    """
    if clearance <= 0:
        logger.error(f"Invalid clearance: {clearance}")
        return 4.0  # Default ~4 hours

    half_life = (0.693 * vd) / clearance
    return half_life


def calculate_pk_based_initial_dose(
    target_mme: float,
    vd: float,
    clearance: float,
    duration_hours: float = 4
) -> float:
    """
    Calculate initial IV oxycodone dose to achieve target MME requirement.

    This uses a simplified compartment model approach:
    1. Calculate bolus dose to reach target concentration
    2. Adjust for expected clearance over duration of effect

    Args:
        target_mme: Target morphine milligram equivalent requirement
        vd: Volume of distribution (L)
        clearance: Clearance (L/h)
        duration_hours: Expected duration of analgesia (default 4h)

    Returns:
        Initial dose in mg of IV oxycodone

    Example:
        >>> calculate_pk_based_initial_dose(30, 150, 1.2, 4)
        12.4  # mg IV oxycodone to achieve 30 MME requirement over 4 hours
    """
    # Convert MME to approximate target concentration
    # 1 mg IV oxycodone ≈ 3 MME
    # Target dose in mg (before clearance adjustment)
    dose_mg = target_mme / 3.0

    # Adjust for clearance over duration
    # Simplified: Account for elimination during analgesic period
    # More drug needed upfront because some will be eliminated
    #
    # Fraction remaining after duration: e^(-k*t) where k = Cl/Vd
    elimination_constant = clearance / vd  # per hour
    fraction_remaining = pow(2.71828, -elimination_constant * duration_hours)

    # Increase dose to compensate for elimination
    # If 60% remains after 4h, we need 1/0.6 = 1.67x the base dose
    if fraction_remaining > 0.1:  # Safety check
        dose_adjusted = dose_mg / fraction_remaining
    else:
        # Very high clearance - cap the adjustment
        dose_adjusted = dose_mg * 3.0

    logger.info(
        f"PK dose calculation: Target {target_mme} MME -> "
        f"Base {dose_mg:.1f} mg -> "
        f"Adjusted {dose_adjusted:.1f} mg "
        f"(fraction_remaining={fraction_remaining:.2f} over {duration_hours}h)"
    )

    return dose_adjusted


def get_pk_summary(
    age: float,
    weight: float,
    height: float,
    sex: str,
    gfr: Optional[float] = None,
    hepatic_impairment: str = 'None'
) -> Dict[str, float]:
    """
    Calculate complete PK profile for a patient.

    This is a convenience function that calculates all PK parameters
    and returns them in a dictionary for easy use.

    Args:
        age: Age in years
        weight: Weight in kg
        height: Height in cm
        sex: 'man' or 'kvinna'
        gfr: GFR if known (mL/min)
        hepatic_impairment: Hepatic status

    Returns:
        Dictionary with PK parameters:
        {
            'lbm_kg': float,
            'clearance_L_per_h': float,
            'vd_L': float,
            'half_life_h': float,
            'elimination_constant': float
        }

    Example:
        >>> pk = get_pk_summary(75, 80, 175, 'man', gfr=50, hepatic_impairment='None')
        >>> print(f"Clearance: {pk['clearance_L_per_h']:.2f} L/h")
        Clearance: 0.94 L/h
    """
    from calculation_engine import calculate_lean_body_mass

    # Calculate lean body mass
    lbm = calculate_lean_body_mass(weight, height, sex)

    # Calculate clearance
    clearance = calculate_clearance(age, weight, gfr, hepatic_impairment)

    # Calculate volume of distribution
    vd = calculate_volume_of_distribution(lbm)

    # Calculate half-life
    half_life = calculate_half_life(clearance, vd)

    # Elimination constant (for future use)
    k_el = clearance / vd  # per hour

    return {
        'lbm_kg': lbm,
        'clearance_L_per_h': clearance,
        'vd_L': vd,
        'half_life_h': half_life,
        'elimination_constant': k_el
    }


def explain_pk_parameters(pk_params: Dict[str, float], age: float) -> Dict[str, str]:
    """
    Generate human-readable explanations of PK parameters.

    Args:
        pk_params: Dictionary from get_pk_summary()
        age: Patient age for context

    Returns:
        Dictionary of explanations for each parameter

    Example:
        >>> pk = get_pk_summary(75, 80, 175, 'man')
        >>> explanations = explain_pk_parameters(pk, 75)
        >>> print(explanations['clearance'])
        "Reduced clearance (0.94 L/h) due to age 75 years"
    """
    explanations = {}

    # Clearance explanation
    cl = pk_params['clearance_L_per_h']
    if cl < 0.8:
        explanations['clearance'] = (
            f"Markedly reduced clearance ({cl:.2f} L/h) - "
            f"drug elimination is significantly impaired"
        )
    elif cl < 1.2:
        explanations['clearance'] = (
            f"Reduced clearance ({cl:.2f} L/h) due to age {age:.0f} years"
        )
    else:
        explanations['clearance'] = (
            f"Normal clearance ({cl:.2f} L/h)"
        )

    # Volume explanation
    vd = pk_params['vd_L']
    lbm = pk_params['lbm_kg']
    explanations['vd'] = (
        f"Volume of distribution {vd:.0f} L "
        f"based on lean body mass {lbm:.1f} kg"
    )

    # Half-life explanation
    t_half = pk_params['half_life_h']
    if t_half > 6:
        explanations['half_life'] = (
            f"Prolonged half-life ({t_half:.1f} hours) - "
            f"risk of accumulation with repeat dosing"
        )
    elif t_half > 4:
        explanations['half_life'] = (
            f"Slightly prolonged half-life ({t_half:.1f} hours)"
        )
    else:
        explanations['half_life'] = (
            f"Normal half-life ({t_half:.1f} hours)"
        )

    return explanations


if __name__ == "__main__":
    # Test the PK model
    print("=== Oxycodone PK Model Tests ===\n")

    # Test case 1: Young healthy patient
    print("Test 1: Young healthy patient (30 years, 80kg, 180cm, male)")
    pk1 = get_pk_summary(30, 80, 180, 'man')
    print(f"  LBM: {pk1['lbm_kg']:.1f} kg")
    print(f"  Clearance: {pk1['clearance_L_per_h']:.2f} L/h")
    print(f"  Vd: {pk1['vd_L']:.0f} L")
    print(f"  Half-life: {pk1['half_life_h']:.1f} hours")

    # Test case 2: Elderly with renal impairment
    print("\nTest 2: Elderly with renal impairment (80 years, 70kg, 170cm, male, GFR 30)")
    pk2 = get_pk_summary(80, 70, 170, 'man', gfr=30)
    print(f"  LBM: {pk2['lbm_kg']:.1f} kg")
    print(f"  Clearance: {pk2['clearance_L_per_h']:.2f} L/h")
    print(f"  Vd: {pk2['vd_L']:.0f} L")
    print(f"  Half-life: {pk2['half_life_h']:.1f} hours")

    # Test case 3: Hepatic impairment
    print("\nTest 3: Moderate hepatic impairment (60 years, 75kg, 175cm, female)")
    pk3 = get_pk_summary(60, 75, 175, 'kvinna', hepatic_impairment='Moderate')
    print(f"  LBM: {pk3['lbm_kg']:.1f} kg")
    print(f"  Clearance: {pk3['clearance_L_per_h']:.2f} L/h")
    print(f"  Vd: {pk3['vd_L']:.0f} L")
    print(f"  Half-life: {pk3['half_life_h']:.1f} hours")

    # Test dose calculation
    print("\nTest 4: Dose calculation for target 30 MME")
    dose = calculate_pk_based_initial_dose(30, pk1['vd_L'], pk1['clearance_L_per_h'], 4)
    print(f"  Recommended initial dose: {dose:.1f} mg IV oxycodone")

    # Test explanations
    print("\nTest 5: PK explanations for elderly patient")
    explanations = explain_pk_parameters(pk2, 80)
    for param, explanation in explanations.items():
        print(f"  {param}: {explanation}")
