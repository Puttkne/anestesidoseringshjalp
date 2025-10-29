"""
Body Composition Utility Functions
===================================
Centralized functions for body composition calculations and bucketing.
"""


def get_weight_bucket(weight: float) -> float:
    """
    Get the weight bucket for learning.

    Uses finer granularity for low weights:
    - 2.5kg increments until 40kg (for pediatric and very low weight patients)
    - 5kg increments after 40kg

    Args:
        weight: Actual weight in kg

    Returns:
        Bucketed weight value

    Examples:
        15.3kg -> 15.0
        22.8kg -> 22.5
        38.2kg -> 37.5
        45.7kg -> 45.0
        72.3kg -> 70.0
        120.5kg -> 120.0
    """
    if weight < 40:
        # 2.5kg increments: 10.0, 12.5, 15.0, 17.5, ..., 37.5, 40.0
        return round(weight / 2.5) * 2.5
    else:
        # 5kg increments: 40, 45, 50, 55, ..., 180, 185
        return round(weight / 5) * 5


def get_ibw_ratio_bucket(ibw_ratio: float) -> float:
    """
    Get the IBW ratio bucket for learning.

    Uses 0.1 increments (10% ranges).

    Args:
        ibw_ratio: weight / IBW ratio

    Returns:
        Bucketed IBW ratio

    Examples:
        0.63 -> 0.6
        0.98 -> 1.0
        1.47 -> 1.5
        2.35 -> 2.4
    """
    return round(ibw_ratio, 1)


def get_abw_ratio_bucket(abw_ratio: float) -> float:
    """
    Get the ABW ratio bucket for learning.

    Uses 0.1 increments (10% ranges).
    Only used for overweight patients (weight > IBW * 1.2).

    Args:
        abw_ratio: ABW / IBW ratio

    Returns:
        Bucketed ABW ratio

    Examples:
        1.18 -> 1.2
        1.34 -> 1.3
        1.52 -> 1.5
    """
    return round(abw_ratio, 1)


def get_bmi_bucket(bmi: float) -> float:
    """
    Get the BMI bucket for learning.

    Uses 7 categories covering full spectrum:
    - Very Underweight: BMI <18 (bucket=16)
    - Underweight: BMI 18-20 (bucket=19)
    - Normal: BMI 20-25 (bucket=22)
    - Overweight: BMI 25-30 (bucket=27)
    - Obese Class I: BMI 30-35 (bucket=32)
    - Obese Class II: BMI 35-40 (bucket=37)
    - Obese Class III: BMI ≥40 (bucket=42)

    Args:
        bmi: BMI value

    Returns:
        Bucketed BMI category value

    Examples:
        16.2 -> 16
        19.3 -> 19
        23.5 -> 22
        28.1 -> 27
        33.2 -> 32
        38.5 -> 37
        45.7 -> 42
    """
    if bmi < 18:
        return 16  # Very underweight
    elif bmi < 20:
        return 19  # Underweight
    elif bmi < 25:
        return 22  # Normal
    elif bmi < 30:
        return 27  # Overweight
    elif bmi < 35:
        return 32  # Obese class I
    elif bmi < 40:
        return 37  # Obese class II
    else:
        return 42  # Obese class III (morbidly obese)


def get_bmi_label(bmi: float) -> str:
    """
    Get descriptive label for BMI value.

    Args:
        bmi: BMI value

    Returns:
        Human-readable BMI category label
    """
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    elif bmi < 35:
        return "Obese I"
    elif bmi < 40:
        return "Obese II"
    else:
        return "Obese III"
