"""
Explainable AI (XAI) Module for Oxycodone Dosing System

Provides SHAP-style feature importance, confidence scoring, and safety alerts
to make dose recommendations transparent and trustworthy for clinicians.

This module transforms opaque recommendations into explainable decisions by:
1. Identifying top influential factors
2. Calculating confidence scores based on training data density
3. Comparing to standard clinical ranges
4. Flagging safety concerns
"""

import logging
from typing import Dict, List, Tuple, Optional
import database as db

logger = logging.getLogger(__name__)

# Standard dose ranges by procedure category (mg IV oxycodone)
STANDARD_DOSE_RANGES = {
    'low_pain': (3.0, 8.0),      # Minor procedures
    'moderate_pain': (5.0, 12.0), # Moderate procedures
    'high_pain': (8.0, 15.0),     # Major procedures
    'default': (5.0, 10.0)        # Fallback
}

# Safety thresholds
MAX_DOSE_ELDERLY = 10.0  # mg for age >=80
MAX_DOSE_RENAL = 8.0     # mg for GFR <35
MAX_DOSE_HEPATIC = 7.0   # mg for severe hepatic impairment
MAX_DOSE_ABSOLUTE = 20.0 # Never exceed


def calculate_confidence(
    patient_inputs: Dict,
    procedure_data: Dict,
    num_total_cases: int = 0
) -> Tuple[float, str]:
    """
    Calculate confidence score for the recommendation.

    Confidence is based on:
    1. Number of similar cases in training data (data density)
    2. Patient similarity to training population (outlier detection)
    3. Procedure familiarity (has this been done before?)

    Args:
        patient_inputs: Patient characteristics
        procedure_data: Procedure information
        num_total_cases: Total number of cases in database

    Returns:
        Tuple of (confidence_score, confidence_explanation)
        - confidence_score: 0.0 to 1.0
        - confidence_explanation: Human-readable reason

    Example:
        >>> confidence, explanation = calculate_confidence(inputs, proc, 150)
        >>> print(f"{confidence:.0%}: {explanation}")
        85%: High confidence - 42 similar cases in database
    """
    # Get similar cases count from database
    similar_cases = db.get_similar_cases_count(
        procedure_id=patient_inputs.get('procedure_id'),
        age_range=(
            patient_inputs.get('age', 50) - 10,
            patient_inputs.get('age', 50) + 10
        ),
        weight_range=(
            patient_inputs.get('weight', 75) - 15,
            patient_inputs.get('weight', 75) + 15
        )
    ) if num_total_cases > 0 else 0

    # Base confidence from data density
    # Saturates at 100 similar cases → 95% confidence
    base_confidence = min(similar_cases / 100.0, 0.95)

    # Penalty for being an outlier
    age = patient_inputs.get('age', 50)
    weight = patient_inputs.get('weight', 75)

    outlier_penalty = 0.0
    outlier_reasons = []

    if age < 20 or age > 90:
        outlier_penalty += 0.15
        outlier_reasons.append(f"extreme age ({age}y)")

    if weight < 40 or weight > 130:
        outlier_penalty += 0.10
        outlier_reasons.append(f"extreme weight ({weight}kg)")

    # Check if procedure has any learning data
    procedure_cases = db.get_procedure_learning_3d(
        patient_inputs.get('procedure_id', ''),
        0, 5, 5, 2
    ).get('num_cases', 0)

    if procedure_cases == 0:
        outlier_penalty += 0.20
        outlier_reasons.append("no prior cases for this procedure")

    # Final confidence
    confidence = max(0.30, base_confidence - outlier_penalty)

    # Generate explanation
    if confidence >= 0.80:
        explanation = f"Hog tillforlitlighet - {similar_cases} liknande fall i databasen"
    elif confidence >= 0.60:
        explanation = f"Mattlig tillforlitlighet - {similar_cases} liknande fall"
    elif confidence >= 0.40:
        explanation = f"Begransad tillforlitlighet - {similar_cases} liknande fall"
    else:
        explanation = "Lag tillforlitlighet - " + ", ".join(outlier_reasons) if outlier_reasons else "fa liknande fall"

    return confidence, explanation


def identify_influential_factors(
    patient_inputs: Dict,
    procedure_data: Dict,
    pk_params: Optional[Dict] = None
) -> List[Tuple[str, str, float]]:
    """
    Identify the top factors influencing the dose recommendation.

    This is a rule-based approximation of SHAP values, identifying which
    patient/procedure characteristics have the largest impact on the final dose.

    Args:
        patient_inputs: Patient characteristics
        procedure_data: Procedure data
        pk_params: Pharmacokinetic parameters (if available)

    Returns:
        List of (factor_name, direction, magnitude) tuples
        - factor_name: Human-readable factor description
        - direction: 'INCREASE' or 'DECREASE'
        - magnitude: Relative effect size (0.0 to 1.0)

    Example:
        >>> factors = identify_influential_factors(inputs, proc, pk)
        >>> for name, direction, mag in factors[:3]:
        ...     print(f"{name}: {direction} ({mag:+.0%})")
        Alder >=80 ar: DECREASE (-40%)
        Svar njursvikt (GFR<35): DECREASE (-30%)
        Smartsam procedur (score 9): INCREASE (+30%)
    """
    factors = []

    # 1. Age effect
    age = patient_inputs.get('age', 50)
    if age >= 80:
        factors.append(('Alder >=80 ar', 'DECREASE', 0.40))
    elif age >= 70:
        factors.append(('Alder 70-79 ar', 'DECREASE', 0.25))
    elif age >= 65:
        factors.append(('Alder 65-69 ar', 'DECREASE', 0.15))

    # 2. Renal function
    gfr = patient_inputs.get('gfr')
    if gfr is not None:
        if gfr < 35:
            factors.append(('Svar njursvikt (GFR<35)', 'DECREASE', 0.30))
        elif gfr < 60:
            factors.append(('Mattlig njursvikt (GFR<60)', 'DECREASE', 0.15))

    # 3. Hepatic function
    hepatic = patient_inputs.get('hepatic_impairment', 'None')
    if hepatic.lower() == 'severe':
        factors.append(('Svar leversvikt', 'DECREASE', 0.50))
    elif hepatic.lower() == 'moderate':
        factors.append(('Mattlig leversvikt', 'DECREASE', 0.30))

    # 4. Opioid tolerance
    if patient_inputs.get('opioid_tolerance', False):
        factors.append(('Opioidtolerans', 'INCREASE', 0.75))

    # 5. Procedure pain intensity
    pain_somatic = procedure_data.get('painTypeScore', 5)
    if pain_somatic >= 8:
        factors.append(('Mycket smartsam procedur (score >=8)', 'INCREASE', 0.30))
    elif pain_somatic >= 6:
        factors.append(('Smartsam procedur (score >=6)', 'INCREASE', 0.15))
    elif pain_somatic <= 3:
        factors.append(('Lagsmartsam procedur (score <=3)', 'DECREASE', 0.15))

    # 6. Adjuvants (opioid-sparing)
    adjuvant_effects = []
    if patient_inputs.get('nsaid', False):
        nsaid_name = patient_inputs.get('nsaid_choice', 'NSAID')
        adjuvant_effects.append((f'{nsaid_name} (NSAID)', 'DECREASE', 0.15))

    if patient_inputs.get('ketamine_choice', 'Ej given') != 'Ej given':
        ketamine_type = patient_inputs.get('ketamine_choice', 'Ketamin')
        adjuvant_effects.append((f'{ketamine_type}', 'DECREASE', 0.10))

    if patient_inputs.get('catapressan', False):
        adjuvant_effects.append(('Catapressan (klonidin)', 'DECREASE', 0.12))

    if patient_inputs.get('droperidol', False):
        adjuvant_effects.append(('Droperidol', 'DECREASE', 0.08))

    if patient_inputs.get('lidocaine', 'Nej') != 'Nej':
        adjuvant_effects.append(('Lidokain-infusion', 'DECREASE', 0.20))

    if patient_inputs.get('betapred', 'Nej') != 'Nej':
        adjuvant_effects.append(('Betametason', 'DECREASE', 0.15))

    # Add adjuvants if present
    factors.extend(adjuvant_effects)

    # 7. PK parameters (if available)
    if pk_params:
        clearance = pk_params.get('clearance_L_per_h', 1.2)
        if clearance < 0.8:
            factors.append(('Kraftigt nedsatt clearance (PK)', 'DECREASE', 0.35))
        elif clearance < 1.0:
            factors.append(('Nedsatt clearance (PK)', 'DECREASE', 0.20))

        half_life = pk_params.get('half_life_h', 4)
        if half_life > 8:
            factors.append(('Forlangd halveringstid (>8h)', 'DECREASE', 0.15))

    # Sort by magnitude (most influential first)
    factors.sort(key=lambda x: x[2], reverse=True)

    return factors


def get_standard_dose_range(procedure_data: Dict) -> Tuple[float, float]:
    """
    Get standard clinical dose range for this procedure.

    Args:
        procedure_data: Procedure information

    Returns:
        Tuple of (min_dose, max_dose) in mg IV oxycodone
    """
    pain_score = procedure_data.get('painTypeScore', 5)

    if pain_score >= 8:
        return STANDARD_DOSE_RANGES['high_pain']
    elif pain_score >= 5:
        return STANDARD_DOSE_RANGES['moderate_pain']
    elif pain_score >= 3:
        return STANDARD_DOSE_RANGES['low_pain']
    else:
        return STANDARD_DOSE_RANGES['default']


def check_safety_alerts(
    patient_inputs: Dict,
    recommended_dose: float,
    pk_params: Optional[Dict] = None
) -> List[str]:
    """
    Check for safety concerns with the recommended dose.

    Args:
        patient_inputs: Patient characteristics
        recommended_dose: The dose being recommended (mg)
        pk_params: PK parameters if available

    Returns:
        List of alert messages (empty if no concerns)

    Example:
        >>> alerts = check_safety_alerts(inputs, 12.0, pk)
        >>> for alert in alerts:
        ...     print(alert)
        [WARN] Hog dos (>10mg) for patient >=80 ar - overvag reducering
    """
    alerts = []

    # Check absolute maximum
    if recommended_dose > MAX_DOSE_ABSOLUTE:
        alerts.append(
            f"[ALERT] VARNING: Dos {recommended_dose:.1f}mg overstiger sakerhets"
            f"grans ({MAX_DOSE_ABSOLUTE}mg) - anvand lagre dos!"
        )

    # Age + high dose
    age = patient_inputs.get('age', 50)
    if age >= 80 and recommended_dose > MAX_DOSE_ELDERLY:
        alerts.append(
            f"[WARN] Hog dos ({recommended_dose:.1f}mg) for patient >=80 ar "
            f"(rekommenderat max {MAX_DOSE_ELDERLY}mg) - overvag reducering"
        )

    # Renal impairment + high dose
    gfr = patient_inputs.get('gfr')
    if gfr is not None and gfr < 35 and recommended_dose > MAX_DOSE_RENAL:
        alerts.append(
            f"[WARN] Dos {recommended_dose:.1f}mg med GFR<35 "
            f"(rekommenderat max {MAX_DOSE_RENAL}mg) - risk for ackumulering"
        )

    # Hepatic impairment + high dose
    hepatic = patient_inputs.get('hepatic_impairment', 'None')
    if hepatic.lower() == 'severe' and recommended_dose > MAX_DOSE_HEPATIC:
        alerts.append(
            f"[WARN] Dos {recommended_dose:.1f}mg med svar leversvikt "
            f"(rekommenderat max {MAX_DOSE_HEPATIC}mg)"
        )

    # Allergy check
    allergies = patient_inputs.get('allergies', '').lower()
    if 'oxycodon' in allergies or 'oxikodon' in allergies:
        alerts.append(
            "[ALERT] ALLERGIVARNING: Patient allergisk mot oxikodon!"
        )

    # PK-based alerts
    if pk_params:
        half_life = pk_params.get('half_life_h', 4)
        if half_life > 10:
            alerts.append(
                f"[WARN] Mycket forlangd halveringstid ({half_life:.0f}h) - "
                f"risk for ackumulering vid upprepade doser"
            )

        clearance = pk_params.get('clearance_L_per_h', 1.2)
        if clearance < 0.5:
            alerts.append(
                f"[WARN] Kraftigt nedsatt clearance ({clearance:.2f} L/h) - "
                f"tat overvakning rekommenderas"
            )

    # Drug interactions
    if patient_inputs.get('benzodiazepine', False):
        alerts.append(
            "[WARN] Samtidig bensodiazepinbehandling - okad risk for sedering"
        )

    return alerts


def generate_explanation_report(
    recommended_dose: float,
    patient_inputs: Dict,
    procedure_data: Dict,
    pk_params: Optional[Dict] = None,
    num_total_cases: int = 0
) -> Dict:
    """
    Generate complete explainability report for a dose recommendation.

    This is the main function that brings together all XAI components:
    confidence, influential factors, comparison to standard, and safety alerts.

    Args:
        recommended_dose: The recommended dose (mg IV oxycodone)
        patient_inputs: Patient characteristics
        procedure_data: Procedure information
        pk_params: PK parameters (optional)
        num_total_cases: Total cases in database

    Returns:
        Dictionary with complete explanation:
        {
            'confidence': float (0-1),
            'confidence_text': str,
            'influential_factors': [(name, direction, magnitude), ...],
            'standard_range': (min, max),
            'comparison_text': str,
            'alerts': [str, ...],
            'pk_explanation': str (if pk_params provided)
        }

    Example:
        >>> report = generate_explanation_report(7.5, inputs, proc, pk, 100)
        >>> print(report['confidence_text'])
        "Hog tillforlitlighet - 42 liknande fall i databasen"
        >>> print(report['comparison_text'])
        "Standard: 5-12mg. AI rekommenderar: 7.5mg (inom normalintervall)"
    """
    # Calculate confidence
    confidence, confidence_text = calculate_confidence(
        patient_inputs, procedure_data, num_total_cases
    )

    # Identify influential factors
    factors = identify_influential_factors(
        patient_inputs, procedure_data, pk_params
    )

    # Get standard range
    min_dose, max_dose = get_standard_dose_range(procedure_data)

    # Generate comparison text
    if recommended_dose < min_dose:
        comparison_text = (
            f"Standard: {min_dose:.1f}-{max_dose:.1f}mg. "
            f"AI rekommenderar: {recommended_dose:.1f}mg "
            f"(lagre an standard, anpassat for patientens profil)"
        )
    elif recommended_dose > max_dose:
        comparison_text = (
            f"Standard: {min_dose:.1f}-{max_dose:.1f}mg. "
            f"AI rekommenderar: {recommended_dose:.1f}mg "
            f"(hogre an standard, anpassat for patientens profil)"
        )
    else:
        comparison_text = (
            f"Standard: {min_dose:.1f}-{max_dose:.1f}mg. "
            f"AI rekommenderar: {recommended_dose:.1f}mg (inom normalintervall)"
        )

    # Check safety alerts
    alerts = check_safety_alerts(patient_inputs, recommended_dose, pk_params)

    # PK explanation (if available)
    pk_explanation = None
    if pk_params:
        from pk_model import explain_pk_parameters
        pk_explanations = explain_pk_parameters(pk_params, patient_inputs.get('age', 50))
        pk_explanation = " | ".join(pk_explanations.values())

    return {
        'confidence': confidence,
        'confidence_text': confidence_text,
        'influential_factors': factors,
        'standard_range': (min_dose, max_dose),
        'comparison_text': comparison_text,
        'alerts': alerts,
        'pk_explanation': pk_explanation
    }


if __name__ == "__main__":
    # Test the explainability module
    print("=== Explainability Module Tests ===\n")

    # Test case 1: Elderly patient with renal impairment
    test_inputs_1 = {
        'age': 82,
        'weight': 68,
        'height': 168,
        'sex': 'Man',
        'gfr': 28,
        'procedure_id': 'LAP_CHOLE',
        'nsaid': True,
        'nsaid_choice': 'parecoxib',
        'ketamine_choice': 'Ej given',
        'opioid_tolerance': False
    }

    test_procedure_1 = {
        'id': 'LAP_CHOLE',
        'name': 'Laparoskopisk kolecystektomi',
        'painTypeScore': 7
    }

    test_pk_1 = {
        'clearance_L_per_h': 0.75,
        'vd_L': 145,
        'half_life_h': 134,
        'lbm_kg': 56
    }

    print("Test 1: Elderly patient (82y) with renal impairment (GFR 28)")
    report1 = generate_explanation_report(
        6.5, test_inputs_1, test_procedure_1, test_pk_1, 100
    )

    print(f"\nTillforlitlighet: {report1['confidence']:.0%}")
    print(f"  {report1['confidence_text']}")

    print(f"\nTopp 5 paverkande faktorer:")
    for name, direction, mag in report1['influential_factors'][:5]:
        arrow = "DOWN" if direction == "DECREASE" else "UP"
        print(f"  [{arrow}] {name} ({mag:+.0%})")

    print(f"\n{report1['comparison_text']}")

    if report1['alerts']:
        print(f"\nSakerhetsvarningar:")
        for alert in report1['alerts']:
            print(f"  {alert}")

    if report1['pk_explanation']:
        print(f"\nFarmakokinetisk forklaring:")
        print(f"  {report1['pk_explanation']}")

    print("\n" + "="*60 + "\n")

    # Test case 2: Young opioid-tolerant patient
    test_inputs_2 = {
        'age': 35,
        'weight': 85,
        'height': 180,
        'sex': 'Man',
        'procedure_id': 'TKA',
        'opioid_tolerance': True,
        'nsaid': False
    }

    test_procedure_2 = {
        'id': 'TKA',
        'name': 'Total knaledsplastik',
        'painTypeScore': 9
    }

    print("Test 2: Young opioid-tolerant patient (35y)")
    report2 = generate_explanation_report(
        15.0, test_inputs_2, test_procedure_2, None, 50
    )

    print(f"\nTillforlitlighet: {report2['confidence']:.0%}")
    print(f"  {report2['confidence_text']}")

    print(f"\nTopp paverkande faktorer:")
    for name, direction, mag in report2['influential_factors'][:5]:
        arrow = "DOWN" if direction == "DECREASE" else "UP"
        print(f"  [{arrow}] {name} ({mag:+.0%})")

    print(f"\n{report2['comparison_text']}")

    if report2['alerts']:
        print(f"\nSakerhetsvarningar:")
        for alert in report2['alerts']:
            print(f"  {alert}")
