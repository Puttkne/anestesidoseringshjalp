"""
Unified Configuration for Anestesidoseringshjälp
==================================================
KRITISK: Detta är den ENDA källan för farmakologiska data.
Både regelmotorn och ML-motorn MÅSTE använda denna fil.

Pain Type Scores (3-dimensionella):
- somatic_score: 0-10 (0=ingen somatisk effekt, 10=ren somatisk effekt)
- visceral_score: 0-10 (0=ingen visceral effekt, 10=ren visceral effekt)
- neuropathic_score: 0-10 (0=ingen neuropatisk effekt, 10=ren neuropatisk effekt)

Potency: MME-ekvivalent reduktion (hur mycket opioid som kan ersättas)
"""

APP_CONFIG = {
    # ML och dosering
    'ML_THRESHOLD_PER_PROCEDURE': 15,
    'ML_TARGET_VAS': 1.0,  # Admin-justerbar från UI
    'FENTANYL_HALFLIFE_FRACTION': 0.25,
    'FENTANYL_MME_CONVERSION_FACTOR': 10,
    'MME_ROUNDING_STEP': 0.25,
    'REFERENCE_WEIGHT_KG': 75,
    'ADJUVANT_SAFETY_LIMIT_FACTOR': 0.3,  # Max 70% MME reduction
    'ML_SAFETY_MAX_DOSE': 20.0,  # Absolut maxdos från ML
    'ML_SAFETY_MIN_DOSE': 0.0,  # Absolut mindos från ML

    # Default patient factors
    'DEFAULTS': {
        'OPIOID_TOLERANCE_FACTOR': 1.5,
        'PAIN_THRESHOLD_FACTOR': 1.2,
        'RENAL_IMPAIRMENT_FACTOR': 0.85,
        'ASA_FACTORS': {1: 1.0, 2: 1.0, 3: 0.9, 4: 0.8, 5: 0.7}
    },

    # Inlärningsparametrar
    'LEARNING': {
        'BASE_MME_SAFETY_OVERRIDE_MULTIPLIER': 0.15,
        'BASE_MME_NORMAL_LEARNING_MULTIPLIER': 0.05,
        'FENTANYL_KINETICS_ADJ_SMALL': -0.02,
        'FENTANYL_KINETICS_ADJ_LARGE': -0.03,
        'INITIAL_LEARNING_RATE': 0.30,
        'INTERMEDIATE_LEARNING_RATE': 0.18,
        'ADVANCED_LEARNING_RATE': 0.12,
        'LEARNING_RATE_DECAY': 0.05,
        'ERROR_ADJUSTMENT_FACTOR': 0.35,
        'RESPIRATORY_ADJUSTMENT_FACTOR': -0.8,
        'LOW_DOSE_SUCCESS_ADJUSTMENT_MULTIPLIER': -1.5,
        'RESCUE_BOOST_HIGH': 2.0,
        'RESCUE_BOOST_MEDIUM': 1.5,
        'OUTLIER_DAMPING_FACTOR': 0.5
    },

    # Valideringsparametrar
    'VALIDATION': {
        'MIN_AGE': 0,
        'MAX_AGE': 120,
        'MIN_WEIGHT': 1.0,
        'MAX_WEIGHT': 500.0,
        'MIN_HEIGHT': 30.0,
        'MAX_HEIGHT': 250.0,
        'MIN_BMI': 10.0,
        'MAX_BMI': 80.0,
        'RECOMMENDED_DOSE_THRESHOLD': 10.0,  # Warn if >10mg oxycodone
        'DANGEROUS_DOSE_THRESHOLD': 30.0,  # Flag as unsafe if >30mg
        'FENTANYL_HIGH_DOSE': 500  # mcg
    }
}

# ==============================================================================
# LÄKEMEDELS_DATA - UNIFIED SOURCE OF TRUTH
# ==============================================================================
# Denna dictionary är den ENDA källan för farmakologisk data.
# Både regelmotorn (calculation_engine.py) och ML-motorn (ml_model.py)
# MÅSTE hämta data från denna struktur.
# ==============================================================================

LÄKEMEDELS_DATA = {
    # ========== OPIOIDER ==========
    'fentanyl': {
        'name': 'Fentanyl',
        'class': 'Opioid',
        'somatic_score': 5,
        'visceral_score': 5,
        'neuropathic_score': 3,
        'potency_mme': 10,  # 100 µg = 10 MME
        'systemic_impact': 9,
        'units': 'mcg',
        'onset_minutes': 2,
        'peak_minutes': 5,
        'duration_minutes': 30,
        'half_life_alpha': 15,  # Snabb distribution
        'half_life_beta': 210,  # Långsam elimination
        'context_sensitive_ht': 60  # Efter 2h infusion
    },
    'oxycodone': {
        'name': 'Oxycodon (µ-agonist)',
        'class': 'Opioid',
        'somatic_score': 5,
        'visceral_score': 5,
        'neuropathic_score': 3,
        'potency_mme': 1.0,  # Reference drug
        'systemic_impact': 9,
        'units': 'mg',
        'onset_minutes': 30,  # PO
        'peak_minutes': 60,
        'duration_minutes': 240  # 4 timmar
    },

    # ========== NSAIDs ==========
    'paracetamol_1g': {
        'name': 'Paracetamol 1g',
        'class': 'NSAID',
        'somatic_score': 7,
        'visceral_score': 3,
        'neuropathic_score': 1,
        'potency_percent': 0.15,  # 15% opioid reduction (STARTING VALUE - will learn from here)
        'systemic_impact': 0,
        'units': 'mg',
        'ui_choice': 'Paracetamol 1g',
        'onset_minutes': 30,
        'peak_minutes': 60,
        'duration_minutes': 240  # 4 timmar
    },
    'ibuprofen_400mg': {
        'name': 'Ibuprofen 400mg',
        'class': 'NSAID',
        'somatic_score': 9,
        'visceral_score': 2,
        'neuropathic_score': 1,
        'potency_percent': 0.175,  # 17.5% opioid reduction (STARTING VALUE - will learn from here)
        'systemic_impact': 1,
        'units': 'mg',
        'ui_choice': 'Ibuprofen 400mg',
        'onset_minutes': 30,
        'peak_minutes': 60,
        'duration_minutes': 360,  # 6 timmar
        'bioavailability': 0.8  # PO
    },
    'ketorolac_30mg': {
        'name': 'Ketorolac 30mg',
        'class': 'NSAID',
        'somatic_score': 9,
        'visceral_score': 2,
        'neuropathic_score': 1,
        'potency_percent': 0.20,  # 20% opioid reduction (STARTING VALUE - will learn from here)
        'systemic_impact': 2,
        'units': 'mg',
        'ui_choice': 'Ketorolac 30mg',
        'onset_minutes': 10,  # IV
        'peak_minutes': 30,
        'duration_minutes': 300  # 5 timmar
    },
    'parecoxib_40mg': {
        'name': 'Parecoxib 40mg (COX-2)',
        'class': 'NSAID',
        'somatic_score': 9,
        'visceral_score': 2,
        'neuropathic_score': 1,
        'potency_percent': 0.20,  # 20% opioid reduction (STARTING VALUE - will learn from here)
        'systemic_impact': 1,
        'units': 'mg',
        'ui_choice': 'Parecoxib 40mg',
        'onset_minutes': 15,  # IV
        'peak_minutes': 45,
        'duration_minutes': 360  # 6 timmar
    },

    # ========== ALPHA-2 AGONISTER ==========
    'clonidine': {
        'name': 'Catapressan (Klonidin α2-agonist)',
        'class': 'Adjuvant',
        'somatic_score': 3,
        'visceral_score': 7,
        'neuropathic_score': 6,
        'potency_percent': 0.075,  # 7.5% opioid reduction (STARTING VALUE - will learn from here)
        'reference_dose_mcg': 75,
        'systemic_impact': 8,
        'units': 'mcg',
        'onset_minutes': 30,
        'peak_minutes': 90,
        'duration_minutes': 480  # 8 timmar
    },

    # ========== NMDA-ANTAGONISTER ==========
    'ketamine_small_bolus': {
        'name': 'Ketamin liten bolus (0.05-0.1 mg/kg)',
        'class': 'Adjuvant',
        'somatic_score': 4,
        'visceral_score': 5,
        'neuropathic_score': 9,
        'potency_percent': 0.10,  # 10% opioid reduction (STARTING VALUE - will learn from here)
        'systemic_impact': 6,
        'units': 'mg/kg',
        'ui_choice': 'Liten bolus (0.05-0.1 mg/kg)',
        'onset_minutes': 5,
        'peak_minutes': 15,
        'duration_minutes': 60
    },
    'ketamine_large_bolus': {
        'name': 'Ketamin stor bolus (0.5-1 mg/kg)',
        'class': 'Adjuvant',
        'somatic_score': 4,
        'visceral_score': 5,
        'neuropathic_score': 9,
        'potency_percent': 0.20,  # 20% opioid reduction (STARTING VALUE - will learn from here)
        'systemic_impact': 8,
        'units': 'mg/kg',
        'ui_choice': 'Stor bolus (0.5-1 mg/kg)',
        'onset_minutes': 5,
        'peak_minutes': 15,
        'duration_minutes': 90
    },
    'ketamine_small_infusion': {
        'name': 'Ketamin liten infusion (0.10-0.15 mg/kg/h)',
        'class': 'Adjuvant',
        'somatic_score': 4,
        'visceral_score': 5,
        'neuropathic_score': 9,
        'potency_percent': 0.30,  # 30% opioid reduction (was: 8 MME)
        'systemic_impact': 7,
        'units': 'mg/kg/h',
        'ui_choice': 'Liten infusion (0.10-0.15 mg/kg/h)',
        'onset_minutes': 10,
        'peak_minutes': 30,
        'duration_minutes': 180  # Medan infusion pågår + 1h
    },
    'ketamine_large_infusion': {
        'name': 'Ketamin stor infusion (3 mg/kg/h)',
        'class': 'Adjuvant',
        'somatic_score': 4,
        'visceral_score': 5,
        'neuropathic_score': 9,
        'potency_percent': 0.50,  # 50% opioid reduction (was: 15 MME)
        'systemic_impact': 9,
        'units': 'mg/kg/h',
        'ui_choice': 'Stor infusion (3 mg/kg/h)',
        'onset_minutes': 10,
        'peak_minutes': 30,
        'duration_minutes': 240  # Medan infusion pågår + 2h
    },

    # ========== NATRIUMKANALBLOCKERARE ==========
    'lidocaine_bolus': {
        'name': 'Lidokain Bolus',
        'class': 'Adjuvant',
        'somatic_score': 4,
        'visceral_score': 6,
        'neuropathic_score': 7,
        'potency_percent': 0.20,  # 20% opioid reduction (was: 5 MME)
        'systemic_impact': 4,
        'units': 'mg',
        'ui_choice': 'Bolus',
        'onset_minutes': 5,
        'peak_minutes': 15,
        'duration_minutes': 60
    },
    'lidocaine_infusion': {
        'name': 'Lidokain Infusion',
        'class': 'Adjuvant',
        'somatic_score': 4,
        'visceral_score': 6,
        'neuropathic_score': 7,
        'potency_percent': 0.35,  # 35% opioid reduction (was: 10 MME)
        'systemic_impact': 5,
        'units': 'mg/h',
        'ui_choice': 'Infusion',
        'onset_minutes': 10,
        'peak_minutes': 30,
        'duration_minutes': 180  # Medan infusion pågår + 1h
    },

    # ========== KORTIKOSTEROIDER ==========
    'betamethasone_4mg': {
        'name': 'Betapred 4mg',
        'class': 'Adjuvant',
        'somatic_score': 6,
        'visceral_score': 4,
        'neuropathic_score': 2,
        'potency_percent': 0.025,  # 2.5% opioid reduction (STARTING VALUE - will learn from here)
        'systemic_impact': 2,
        'units': 'mg',
        'ui_choice': '4 mg',
        'onset_minutes': 120,  # 2 timmar
        'peak_minutes': 240,  # 4 timmar
        'duration_minutes': 720  # 12 timmar
    },
    'betamethasone_8mg': {
        'name': 'Betapred 8mg',
        'class': 'Adjuvant',
        'somatic_score': 6,
        'visceral_score': 4,
        'neuropathic_score': 2,
        'potency_percent': 0.05,  # 5% opioid reduction (STARTING VALUE - will learn from here)
        'systemic_impact': 3,
        'units': 'mg',
        'ui_choice': '8 mg',
        'onset_minutes': 120,  # 2 timmar
        'peak_minutes': 240,  # 4 timmar
        'duration_minutes': 720  # 12 timmar
    },

    # ========== NEUROLEPTIKA ==========
    'droperidol': {
        'name': 'Droperidol',
        'class': 'Adjuvant',
        'somatic_score': 5,
        'visceral_score': 5,
        'neuropathic_score': 4,
        'potency_percent': 0.30,  # 30% opioid reduction (was: 8 MME)
        'systemic_impact': 9,
        'units': 'mg',
        'onset_minutes': 10,
        'peak_minutes': 30,
        'duration_minutes': 180  # 3 timmar
    },

    # ========== VOLATILA ANESTETI ==========
    'sevoflurane': {
        'name': 'Sevoflurane',
        'class': 'Adjuvant',
        'somatic_score': 5,
        'visceral_score': 5,
        'neuropathic_score': 3,
        'potency_percent': 0.08,  # 8% opioid reduction (was: 2 MME)
        'systemic_impact': 8,
        'units': 'vol%',
        'onset_minutes': 2,
        'peak_minutes': 5,
        'duration_minutes': 30  # Efter sömn/opslut
    },

    # ========== LOKAL ANESTESI ==========
    'infiltration': {
        'name': 'Infiltrationsanestesi',
        'class': 'Regional',
        'somatic_score': 10,
        'visceral_score': 1,
        'neuropathic_score': 8,
        'potency_percent': 0.15,  # 15% opioid reduction for laparoscopic surgery (STARTING VALUE - will learn from here)
        'systemic_impact': 0,
        'units': 'ml',
        'onset_minutes': 5,
        'peak_minutes': 15,
        'duration_minutes': 180  # Beror på volym och koncentration
    }
}

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_drug_by_ui_choice(drug_type: str, ui_choice: str):
    """
    Hämta läkemedelsdata baserat på UI-val.

    Args:
        drug_type: 'nsaid', 'ketamine', 'lidocaine', 'betapred', etc.
        ui_choice: Värdet från UI dropdown (t.ex. "Ibuprofen 400mg")

    Returns:
        Dict med läkemedelsdata eller None
    """
    for key, drug in LÄKEMEDELS_DATA.items():
        if drug.get('ui_choice') == ui_choice:
            return drug
    return None

def get_drug(drug_key: str):
    """
    Hämta läkemedelsdata via nyckel.

    Args:
        drug_key: Nyckel i LÄKEMEDELS_DATA (t.ex. 'ibuprofen_400mg')

    Returns:
        Dict med läkemedelsdata eller None
    """
    return LÄKEMEDELS_DATA.get(drug_key)

def calculate_composite_pain_score(somatic: float, visceral: float, neuropathic: float) -> dict:
    """
    Beräkna sammansatt smärtprofil från 3D-scores.

    Returns:
        {
            'dominant_type': str,  # 'somatic', 'visceral', 'neuropathic', or 'mixed'
            'somatic': float,
            'visceral': float,
            'neuropathic': float,
            'total': float
        }
    """
    total = somatic + visceral + neuropathic

    # Bestäm dominant typ (>50% av total)
    if somatic > (total * 0.5):
        dominant = 'somatic'
    elif visceral > (total * 0.5):
        dominant = 'visceral'
    elif neuropathic > (total * 0.5):
        dominant = 'neuropathic'
    else:
        dominant = 'mixed'

    return {
        'dominant_type': dominant,
        'somatic': somatic,
        'visceral': visceral,
        'neuropathic': neuropathic,
        'total': total
    }

def calculate_3d_mismatch_penalty(
    procedure_pain: dict,
    drug_pain: dict
) -> float:
    """
    Beräkna mismatch-penalty baserat på 3D-smärtprofiler.

    Args:
        procedure_pain: {'somatic': X, 'visceral': Y, 'neuropathic': Z}
        drug_pain: {'somatic': X, 'visceral': Y, 'neuropathic': Z}

    Returns:
        float: Penalty factor (0.5-1.0, där 1.0 = perfekt match)
    """
    # Euclidean distance i 3D-rymden
    import math
    distance = math.sqrt(
        (procedure_pain['somatic'] - drug_pain['somatic'])**2 +
        (procedure_pain['visceral'] - drug_pain['visceral'])**2 +
        (procedure_pain['neuropathic'] - drug_pain['neuropathic'])**2
    )

    # Maximal möjlig distance (från 0,0,0 till 10,10,10)
    max_distance = math.sqrt(3 * 10**2)

    # Normalisera till 0-1 och invertera (1 = perfekt match)
    normalized_distance = distance / max_distance

    # Konvertera till penalty (stor mismatch = 0.5, perfekt match = 1.0)
    penalty = max(0.5, 1.0 - normalized_distance)

    return penalty
