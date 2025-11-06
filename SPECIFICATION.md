# ANESTESI-ASSISTENT - TECHNICAL SPECIFICATION
**Version:** 0.8
**Date:** 2025-01-06
**Status:** Complete Implementation Specification

---

## TABLE OF CONTENTS
1. [System Overview](#system-overview)
2. [Core Architecture](#core-architecture)
3. [Database Schema](#database-schema)
4. [Calculation Engine](#calculation-engine)
5. [Learning Engine](#learning-engine)
6. [3D Pain Matching System](#3d-pain-matching-system)
7. [Interpolation System](#interpolation-system)
8. [Pharmacokinetics](#pharmacokinetics)
9. [Temporal Dosing](#temporal-dosing)
10. [Security & Safety](#security--safety)
11. [Configuration](#configuration)
12. [API Specifications](#api-specifications)
13. [UI/UX Specifications](#ui-ux-specifications)
14. [Deployment](#deployment)
15. [Testing Strategy](#testing-strategy)
16. [TODO List for Rebuild](#todo-list-for-rebuild)

---

## SYSTEM OVERVIEW

### Purpose
Adaptive Multimodal Opioid Dosing System - Ett intelligent beslutsstöd för postoperativ smärtlindring som:
- Rekommenderar optimal oxycodon-dos baserat på procedur, patient, och adjuvanter
- Lär sig kontinuerligt från verkliga utfall
- Strävar efter att **alltid sänka oxycodon-dosen** medan target VAS uppnås
- Använder 3D-smärtprofiler för precision-matching av läkemedel

### Core Goals
1. **Träffa target VAS** (admin-konfigurerbar, default 3)
2. **Minimera oxycodon-dos** (proactive dose probing vid perfekta utfall)
3. **Balansera multimodal analgesi** (optimera adjuvanter vs opioid)
4. **Lära kontinuerligt** från alla fall (adaptive learning rate)
5. **Säkerhet först** (multiple safety limits och validering)

### Key Metrics
- **Target VAS:** ≤3 (konfigurerbar)
- **Adjuvant Safety Limit:** Max 70% IME reduction
- **Learning Rate:** Adaptive (30% → 12% → damped efter 20 cases)
- **Interpolation Range:** ±5 years (age), ±10 kg (weight)
- **Probing Factor:** 97% of perfect dose (konfigurerbar)

---

## CORE ARCHITECTURE

### Technology Stack
```
Frontend: Streamlit (Python)
Backend: Python 3.10+
Database: SQLite (TinyDB for lightweight JSON storage)
ML: Custom adaptive learning (no external ML libraries)
PK/PD: Custom pharmacokinetic models
```

### Module Structure
```
anestesidoseringshjälp/
├── oxydoseks.py               # Main application entry
├── config.py                  # Unified drug database & config
├── database.py                # Database layer (TinyDB)
├── auth.py                    # Authentication system
├── calculation_engine.py      # Core dose calculation
├── learning_engine.py         # Adaptive learning system
├── pharmacokinetics.py        # PK/PD models
├── interpolation_engine.py    # Gaussian interpolation
├── body_composition_utils.py  # IBW/ABW/BMI bucketing
├── callbacks.py               # Save & learn triggers
├── ui/
│   ├── main_layout.py         # Main UI
│   ├── dosing_tab.py          # Dosing calculator tab
│   ├── history_tab.py         # Case history tab
│   ├── procedures_tab.py      # Procedure management
│   ├── admin_tab.py           # Admin panel
│   └── style.css              # Figma-generated CSS
└── database.json              # TinyDB file
```

### Data Flow (High Level)
```
User Input
    ↓
[Input Validation]
    ↓
[Calculation Engine]
    │
    ├── Procedure baseIME + 3D pain  ← [Procedure Learning]
    ├── Patient factors              ← [Patient Factor Learning]
    ├── Adjuvant reduction           ← [Adjuvant Potency Learning]
    ├── Fentanyl kinetics            ← [Fentanyl Learning]
    └── Temporal dosing (optional)
    ↓
[Recommended Dose (mg oxycodone)]
    ↓
User gives dose → Patient outcome
    ↓
[Back-calculation Learning]
    │
    ├── Calculate actual requirement
    ├── Prediction error
    ├── Outcome quality assessment
    └── Distribute learning across dimensions
    ↓
[Database Updates]
    ↓
[Next Case Benefits from Learning]
```

---

## DATABASE SCHEMA

### 1. Users Table
```python
{
    'id': int (auto-increment),
    'username': str (unique, case-insensitive),
    'password_hash': str (bcrypt),
    'is_admin': bool,
    'created_at': datetime,
    'last_login': datetime
}
```

**Purpose:** Multi-tenant system, separate learning per user
**Key Function:** `get_user_by_username(username)`, `create_user(...)`

---

### 2. Cases Table
```python
{
    'id': int (auto-increment),
    'user_id': int (FK users.id),
    'status': str ('IN_PROGRESS' | 'FINALIZED'),  # NEW: case status
    'timestamp': datetime,

    # Patient Demographics
    'age': int,
    'sex': str ('Man' | 'Kvinna'),
    'weight': float (kg),
    'height': float (cm),
    'ibw': float (kg, ideal body weight),
    'abw': float (kg, adjusted body weight),
    'bmi': float (kg/m²),

    # Patient Factors
    'asa': str ('1' | '2' | '3' | '4' | '5'),  # ASA class (without 'ASA ' prefix)
    'opioidHistory': str ('Opioidnaiv' | 'Opioidtolerant'),
    'lowPainThreshold': bool,
    'renalImpairment': bool,

    # Procedure
    'procedure_id': str,
    'kva_code': str,
    'specialty': str,
    'surgery_type': str ('Elektivt' | 'Akut'),
    'optime_minutes': int,

    # Intraoperative
    'fentanylDose': float (µg),

    # Adjuvants
    'nsaid': bool,
    'nsaid_choice': str ('Paracetamol 1g' | 'Ibuprofen 400mg' | 'Ketorolac 30mg' | 'Parecoxib 40mg' | 'Ej given'),
    'catapressan': bool,
    'catapressan_dose': float (µg),
    'droperidol': bool,
    'ketamine': str ('Nej' | 'value'),
    'ketamine_choice': str,
    'lidocaine': str ('Nej' | 'Bolus' | 'Infusion'),
    'betapred': str ('Nej' | '4 mg' | '8 mg'),
    'sevoflurane': bool,
    'infiltration': bool,

    # Outcome
    'givenDose': float (mg oxycodone, actual dose given),
    'vas': int (0-10, pain score 1h postop),
    'uvaDose': float (mg oxycodone, rescue dose),
    'postop_minutes': int (time to first assessment),
    'postop_reason': str ('Normal återhämtning' | 'Smärtgenombrott...' | 'Andningspåverkan...'),
    'respiratory_status': str ('vaken' | 'sömnig' | 'sederad djupt'),
    'severe_fatigue': bool,
    'rescue_early': bool (rescue < 30 min postop),
    'rescue_late': bool (rescue > 60 min postop),

    # Calculation result (stored for audit)
    'calculation': dict {
        'finalDose': float (recommended dose),
        'compositeKey': str,
        'procedure': dict,
        'engine': str ('Regelmotor' | 'Maskininlärning'),
        'ibw': float,
        'abw': float,
        'actual_weight': float,
        'pain_type_3d': dict {'somatic': X, 'visceral': Y, 'neuropathic': Z}
    }
}
```

**Purpose:** Store all cases with complete audit trail
**Key Functions:**
- `save_case(case_data, user_id)` → case_id
- `update_case(case_id, outcome_data, user_id)`
- `finalize_case(case_id, final_data, user_id)` → marks case as FINALIZED, triggers learning
- `get_case_by_id(case_id)` → case dict
- `get_all_cases(user_id=None)` → list of cases

---

### 3. Temporal Doses Table
```python
{
    'id': int (auto-increment),
    'case_id': int (FK cases.id),
    'drug_type': str ('fentanyl' | 'nsaid' | 'ketamine' | 'lidocaine' | ...),
    'drug_name': str (full drug name),
    'dose': float,
    'units': str ('mg' | 'mcg' | 'mg/kg'),
    'time_relative_minutes': int (negative = before opslut, positive = after, 0 = at opslut),
    'notes': str
}
```

**Purpose:** Store temporal dosing (time-dependent administration)
**Key Functions:**
- `save_temporal_doses(case_id, temporal_doses: list)`
- `get_temporal_doses(case_id)` → list

---

### 4. Procedures Table
```python
{
    'id': str (unique identifier),
    'name': str,
    'specialty': str,
    'kva_code': str (Swedish operation code),
    'baseMME': float (default morphine milligram equivalents),
    'painTypeScore': float (0-10, legacy somatic pain),
    'painVisceral': float (0-10, visceral pain component),
    'painNeuropathic': float (0-10, neuropathic pain component),
    'description': str
}
```

**Purpose:** Catalog of surgical procedures with pain profiles
**Key Functions:**
- `get_procedures_df()` → pandas DataFrame
- `add_procedure(procedure_data)`
- `update_procedure(procedure_id, updates)`

---

### 5. Procedure Learning Table
```python
{
    'procedure_id': str (PK),
    'base_mme': float (learned baseMME),
    'pain_type': float (learned pain score, legacy),
    'num_observations': int,
    'last_updated': datetime
}
```

**Purpose:** Learn procedure-specific baseMME (1D, legacy)
**Key Functions:**
- `get_procedure_learning(user_id, procedure_id, default_base_mme, default_pain)` → dict
- `update_procedure_learning(procedure_id, default_base_mme, default_pain, base_mme_adj, pain_adj)`

---

### 6. Procedure Learning 3D Table  (**NEW in V6**)
```python
{
    'procedure_id': str (PK),  # GLOBAL learning, no user_id
    'base_mme': float (learned baseMME),
    'pain_somatic': float (0-10),
    'pain_visceral': float (0-10),
    'pain_neuropathic': float (0-10),
    'num_observations': int,
    'last_updated': datetime
}
```

**Purpose:** GLOBAL learning of 3D pain profiles for procedures
**Key Functions:**
- `get_procedure_learning_3d(procedure_id, defaults...)` → dict
- `update_procedure_learning_3d(procedure_id, defaults..., adjustments...)`

**How it works:**
- If adjuvants with specific pain profiles (e.g., ketamine: high neuropathic) underperform → increase procedure's neuropathic score
- If adjuvants overperform → decrease corresponding pain dimensions

---

### 7. Age Bucket Learning Table (**Fine-grained: Every year**)
```python
{
    'age_bucket': int (0, 1, 2, ..., 120),  # Every single year is a bucket
    'age_factor': float (dose multiplier),
    'num_observations': int,
    'sum_adjustments': float,
    'last_updated': datetime
}
```

**Purpose:** Learn age-specific dosing (e.g., 72-year-olds need X adjustment)
**Key Functions:**
- `get_age_bucket_learning(age_bucket)` → dict
- `update_age_bucket_learning(age_bucket, default_factor, adjustment)`

**Bucketing:** `age_bucket = int(age)`  (every year is separate)

---

### 8. Weight Bucket Learning Table (**Fine-grained: Every kg**)
```python
{
    'weight_bucket': int (10, 11, 12, ..., 200),  # Every kg is a bucket
    'weight_factor': float (dose multiplier),
    'num_observations': int,
    'sum_adjustments': float,
    'last_updated': datetime
}
```

**Purpose:** Learn weight-specific dosing (e.g., 73kg patients need X adjustment)
**Key Functions:**
- `get_weight_bucket_learning(weight_bucket)` → dict
- `update_weight_bucket_learning(weight_bucket, default_factor, adjustment)`

**Bucketing:** `weight_bucket = int(round(weight))`  (round to nearest kg)

---

### 9. Body Composition Factors Table (**4D learning**)
```python
{
    'dimension': str ('weight' | 'ibw_ratio' | 'abw_ratio' | 'bmi'),
    'bucket': float,  # Dimension-specific bucketing
    'factor': float (dose multiplier),
    'num_observations': int,
    'sum_adjustments': float,
    'last_updated': datetime
}
# Compound PK: (dimension, bucket)
```

**Purpose:** Multi-dimensional body composition learning

**Dimensions:**
1. **weight:** Actual weight (same as weight_bucket_learning, but separate table)
   - Bucketing: Round to nearest kg
   - Example: 73.4 kg → bucket 73

2. **ibw_ratio:** Weight / Ideal Body Weight
   - Bucketing: Round to 0.1 increments (10%)
   - Example: 1.47x → bucket 1.5
   - Captures: Underweight (0.8x), normal (1.0x), overweight (1.5x), obese (2.0x+)

3. **abw_ratio:** Adjusted Body Weight / IBW (for overweight only)
   - Bucketing: Round to 0.1 increments
   - Example: ABW 85kg / IBW 70kg = 1.21 → bucket 1.2
   - Only applied if weight > IBW * 1.2

4. **bmi:** Body Mass Index categories
   - Bucketing: 7 categories
     - 16 (Very underweight, BMI <18)
     - 19 (Underweight, BMI 18-20)
     - 22 (Normal, BMI 20-25)
     - 27 (Overweight, BMI 25-30)
     - 32 (Obese I, BMI 30-35)
     - 37 (Obese II, BMI 35-40)
     - 42 (Obese III, BMI ≥40)

**Key Functions:**
- `get_body_composition_factor(dimension, bucket, default_factor)` → float
- `update_body_composition_factor(dimension, bucket, default_factor, adjustment)`

**Why 4D?**
- Captures different aspects of body composition
- **Weight:** Absolute size (bigger people need more drug)
- **IBW ratio:** How far from ideal (obesity vs emaciation)
- **ABW ratio:** Adjusted dosing for obese (lipophilic drug distribution)
- **BMI:** Independent metabolic/clearance marker

---

### 10. ASA Factors Table
```python
{
    'asa_class': str ('ASA 1' | 'ASA 2' | 'ASA 3' | 'ASA 4' | 'ASA 5'),
    'factor': float (dose multiplier),
    'num_observations': int,
    'sum_adjustments': float,
    'last_updated': datetime
}
```

**Purpose:** Learn if sicker patients (higher ASA) need more/less opioid
**Defaults:** ASA 1-2: 1.0, ASA 3: 0.9, ASA 4: 0.8, ASA 5: 0.7
**Key Functions:**
- `get_asa_factor(asa_class, default_factor)` → float
- `update_asa_factor(asa_class, default_factor, adjustment)`

---

### 11. Sex Factors Table
```python
{
    'sex': str ('Man' | 'Kvinna'),
    'factor': float (dose multiplier),
    'num_observations': int,
    'sum_adjustments': float,
    'last_updated': datetime
}
```

**Purpose:** Learn sex-specific dosing differences
**Default:** 1.0 for both (no inherent difference assumed)
**Key Functions:**
- `get_sex_factor(sex, default_factor)` → float
- `update_sex_factor(sex, default_factor, adjustment)`

---

### 12. Renal Impairment Factor Table
```python
{
    'factor': float (dose multiplier),
    'num_observations': int,
    'sum_adjustments': float,
    'last_updated': datetime
}
```

**Purpose:** Learn dosing adjustment for renal impairment
**Default:** 0.85 (reduce dose 15%)
**Key Functions:**
- `get_renal_factor(default_factor)` → float
- `update_renal_factor(default_factor, adjustment)`

---

### 13. Opioid Tolerance Factor Table
```python
{
    'factor': float (dose multiplier),
    'num_observations': int,
    'sum_adjustments': float,
    'last_updated': datetime
}
```

**Purpose:** Learn dosing adjustment for opioid-tolerant patients
**Default:** 1.5 (increase dose 50%)
**Key Functions:**
- `get_opioid_tolerance_factor(default_factor)` → float
- `update_opioid_tolerance_factor(default_factor, adjustment)`

---

### 14. Pain Threshold Factor Table
```python
{
    'factor': float (dose multiplier),
    'num_observations': int,
    'sum_adjustments': float,
    'last_updated': datetime
}
```

**Purpose:** Learn dosing adjustment for low pain threshold patients
**Default:** 1.2 (increase dose 20%)
**Key Functions:**
- `get_pain_threshold_factor(default_factor)` → float
- `update_pain_threshold_factor(default_factor, adjustment)`

---

### 15. Adjuvant Potency Table (**GLOBAL learning**)
```python
{
    'drug_key': str (from LÄKEMEDELS_DATA, e.g., 'ibuprofen_400mg'),
    'potency_percent': float (0-1, percentage of opioid reduction),
    'num_observations': int,
    'sum_adjustments': float,
    'last_updated': datetime
}
```

**Purpose:** GLOBAL learning of adjuvant effectiveness (percentage-based)
**Example:** If ibuprofen started at 17.5% opioid reduction, system learns it's actually 15% or 20%
**Key Functions:**
- `get_adjuvant_potency_percent(drug_key, default_potency)` → float
- `update_adjuvant_potency_percent(drug_key, default_potency, adjustment)`

**Why percentage-based?**
- Scales correctly for both small and large procedures
- More intuitive than absolute MME values
- Example: Ibuprofen reduces opioid need by 17.5%, regardless if procedure is 5 MME or 30 MME

---

### 16. Fentanyl Kinetics Table
```python
{
    'user_id': int (FK users.id),
    'remaining_fraction': float (0-1, fraction remaining at opslut),
    'num_observations': int,
    'sum_adjustments': float,
    'last_updated': datetime
}
```

**Purpose:** Learn fentanyl elimination kinetics per user
**Default:** 0.25 (25% remaining at opslut)
**Key Functions:**
- `get_fentanyl_remaining_fraction(user_id)` → float
- `update_fentanyl_remaining_fraction(user_id, adjustment)`

**How it's learned:**
- If rescue dose needed early (<30 min postop) → fentanyl wears off faster → decrease fraction
- If late pain (>60 min postop) → fentanyl lasted longer OR base dose too low
- Bi-exponential model: Fast (t½=15min, 60%) + Slow (t½=210min, 40%)

---

### 17. Calibration Factors Table
```python
{
    'user_id': int (FK users.id),
    'composite_key': str (complex key encoding procedure + patient + adjuvants),
    'factor': float (dose multiplier),
    'num_observations': int,
    'sum_adjustments': float,
    'last_updated': datetime
}
```

**Purpose:** Fine-tune dosing for specific combinations
**Example composite key:** `"JXB12-ASA2-N-NIb-x-x-x-x-x"`
- JXB12 = procedure ID
- ASA2 = ASA class 2
- N = not opioid tolerant
- NIb = NSAID Ibuprofen
- x = no catapressan, droperidol, ketamine, lidocaine, betapred

**Key Functions:**
- `get_calibration_factor(user_id, composite_key)` → float
- `update_calibration_factor(user_id, composite_key, adjustment)`

---

### 18. Synergy Factors Table
```python
{
    'drug_combination': str (e.g., 'ibuprofen+ketamine'),
    'factor': float (synergy multiplier),
    'num_observations': int,
    'sum_adjustments': float,
    'last_updated': datetime
}
```

**Purpose:** Learn drug-drug synergy effects
**Example:** Ibuprofen + Ketamine might have synergy → their combined reduction is > sum of parts
**Key Functions:**
- `get_synergy_factor(drug_combo)` → float
- `get_drug_combination_key(inputs)` → str

---

### 19. Edit History Table (Audit Trail)
```python
{
    'id': int (auto-increment),
    'case_id': int (FK cases.id),
    'user_id': int (FK users.id),
    'edited_at': datetime,
    'old_values': dict (what was changed from),
    'new_values': dict (what was changed to),
    'calculation_engine': str ('Regelmotor' | 'Maskininlärning')
}
```

**Purpose:** Complete audit trail of case edits
**Key Functions:**
- `add_edit_history(case_id, user_id, old_values, new_values, engine)`
- `get_edit_history(case_id)` → list

---

### 20. Settings Table
```python
{
    'key': str (unique setting key),
    'value': any (JSON-serializable),
    'description': str,
    'updated_at': datetime,
    'updated_by': int (user_id)
}
```

**Purpose:** Admin-configurable settings
**Key Settings:**
- `TARGET_VAS`: int (default 3) - Target pain score
- `DOSE_PROBE_REDUCTION_FACTOR`: float (default 0.97) - How much to probe down on perfect outcomes
- (Future: ML_ENABLED, ML_THRESHOLD, etc.)

**Key Functions:**
- `get_setting(key, default)` → value
- `set_setting(key, value, user_id)`

---

## CALCULATION ENGINE

### High-Level Flow
```python
def calculate_rule_based_dose(inputs, procedures_df, temporal_doses=None):
    """
    Main calculation function.

    Steps:
    1. Get initial IME and 3D pain from procedure (with learning)
    2. Apply patient factors (age, weight, ASA, sex, etc.)
    3. Save base_ime_before_adjuvants (for percentage calculations)
    4. Apply adjuvants (percentage-based reductions)
    5. Apply synergy and safety limits
    6. Apply fentanyl pharmacokinetics
    7. [Optional] Apply temporal dosing adjustments
    8. Apply weight adjustment (ABW scaling)
    9. Apply calibration factor (final tuning)
    10. Round to 0.25 mg increments

    Returns:
        {
            'finalDose': float (mg oxycodone),
            'compositeKey': str,
            'procedure': dict,
            'engine': "Regelmotor",
            'ibw': float,
            'abw': float,
            'actual_weight': float,
            'pain_type_3d': dict
        }
    """
```

### Step 1: Get Initial IME and 3D Pain
```python
def _get_initial_ime_and_pain_type(inputs, procedures_df):
    # Get procedure from database
    procedure = procedures_df[procedures_df['id'] == inputs['procedure_id']].iloc[0]

    # Default values from procedure
    default_base_ime = float(procedure['baseIME'])
    default_pain_somatic = float(procedure.get('painTypeScore', 5))
    default_pain_visceral = float(procedure.get('painVisceral', 5))
    default_pain_neuropathic = float(procedure.get('painNeuropathic', 2))

    # Get learned 3D pain (GLOBAL learning)
    if user_id:
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

    # No learning, use defaults
    return default_base_ime, {
        'somatic': default_pain_somatic,
        'visceral': default_pain_visceral,
        'neuropathic': default_pain_neuropathic
    }, procedure
```

### Step 2: Apply Patient Factors
```python
def _apply_patient_factors(ime, inputs):
    # 1. AGE FACTOR (with interpolation)
    age = inputs['age']
    default_age_factor = calculate_age_factor(age)  # Exponential decay after 65
    if user_id:
        result = interpolate_age_factor(age, default_age_factor)
        age_factor = result['age_factor']
    else:
        age_factor = default_age_factor
    ime *= age_factor

    # 2. ASA FACTOR
    asa_class = inputs.get('asa', 'ASA 2')
    default_asa_factor = APP_CONFIG['DEFAULTS']['ASA_FACTORS'][asa_num]
    asa_factor = db.get_asa_factor(asa_class, default_asa_factor) if user_id else default_asa_factor
    ime *= asa_factor

    # 3. SEX FACTOR
    sex = inputs.get('sex', 'Man')
    sex_factor = db.get_sex_factor(sex, 1.0) if user_id else 1.0
    ime *= sex_factor

    # 4. BODY COMPOSITION (4D learning)
    if user_id and weight > 0 and height > 0:
        # Calculate metrics
        bmi = calculate_bmi(weight, height)
        ibw = calculate_ideal_body_weight(height, sex)
        abw = calculate_adjusted_body_weight(weight, height, sex)

        # Dimension 1: ACTUAL WEIGHT (with interpolation)
        result = interpolate_weight_factor(weight, 1.0)
        body_comp_factor = result['weight_factor']
        ime *= body_comp_factor

        # Dimension 2: IBW RATIO
        if ibw > 0:
            ibw_ratio = weight / ibw
            ibw_ratio_bucket = get_ibw_ratio_bucket(ibw_ratio)
            ibw_factor = db.get_body_composition_factor('ibw_ratio', ibw_ratio_bucket, 1.0)
            ime *= ibw_factor

        # Dimension 3: ABW RATIO (for overweight patients)
        if weight > ibw * 1.2:
            abw_ratio = abw / ibw
            abw_ratio_bucket = get_abw_ratio_bucket(abw_ratio)
            abw_factor = db.get_body_composition_factor('abw_ratio', abw_ratio_bucket, 1.0)
            ime *= abw_factor

        # Dimension 4: BMI
        bmi_bucket = get_bmi_bucket(bmi)
        bmi_factor = db.get_body_composition_factor('bmi', bmi_bucket, 1.0)
        ime *= bmi_factor

    # 5. OPIOID TOLERANCE
    if inputs['opioidHistory'] == 'Opioidtolerant':
        opioid_factor = db.get_opioid_tolerance_factor() if user_id else 1.5
        ime *= opioid_tolerance_factor

    # 6. LOW PAIN THRESHOLD
    if inputs['lowPainThreshold']:
        pain_threshold_factor = db.get_pain_threshold_factor() if user_id else 1.2
        ime *= pain_threshold_factor

    # 7. RENAL IMPAIRMENT
    if inputs.get('renalImpairment', False):
        renal_factor = db.get_renal_factor() if user_id else 0.85
        ime *= renal_factor

    return ime
```

**Age Factor Formula:**
```python
def calculate_age_factor(age: int) -> float:
    """
    Exponential decay after reference age (65 years).

    Formula: factor = max(0.4, exp((65 - age) / 20))

    Examples:
        age 50: factor = 1.0 (no adjustment)
        age 65: factor = 1.0 (reference)
        age 75: factor = 0.61 (39% reduction)
        age 85: factor = 0.44 (56% reduction)
        age 95: factor = 0.40 (60% reduction, floor)
    """
    if age <= 65:
        return 1.0
    return max(0.4, math.exp((65 - age) / 20))
```

**IBW/ABW Formulas:**
```python
def calculate_ideal_body_weight(height_cm: float, sex: str) -> float:
    """
    IBW = height_cm - adjustment
    Men: height - 100
    Women: height - 105

    Example: Man, 180cm → IBW = 80 kg
    """
    if sex == 'Kvinna':
        return max(40, height_cm - 105)
    else:
        return max(40, height_cm - 100)

def calculate_adjusted_body_weight(actual_weight: float, height_cm: float, sex: str) -> float:
    """
    ABW for overweight patients (weight > IBW * 1.2):
    ABW = IBW + 0.4 * (actual - IBW)

    Example: Man, 180cm, 100kg
        IBW = 80kg
        Overweight: 100 > 80*1.2 (96)
        ABW = 80 + 0.4*(100-80) = 88kg

    If not overweight: ABW = actual weight
    """
    ibw = calculate_ideal_body_weight(height_cm, sex)
    if actual_weight <= ibw * 1.2:
        return actual_weight
    overvikt = actual_weight - ibw
    abw = ibw + (overvikt * 0.4)
    return abw
```

### Step 3-4: Apply Adjuvants (Percentage-Based)
```python
def _apply_adjuvants(base_ime_before_adjuvants, inputs, pain_type_3d):
    """
    CRITICAL: All adjuvant reductions are calculated from base_ime_before_adjuvants,
    NOT from current IME. This ensures correct scaling for all procedure sizes.

    Example:
        Small procedure: base_ime = 5 MME
        Large procedure: base_ime = 30 MME
        Ibuprofen: 17.5% reduction

        Small: reduction = 5 * 0.175 = 0.875 MME
        Large: reduction = 30 * 0.175 = 5.25 MME

        Both get 17.5% benefit, scaled appropriately!
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

    # Catapressan (dose-scaled)
    catapressan_dose = inputs.get('catapressan_dose', 0)
    if catapressan_dose > 0:
        drug_data = LÄKEMEDELS_DATA.get('clonidine')
        if drug_data:
            ref_dose = drug_data.get('reference_dose_mcg', 75)
            dose_scaling = catapressan_dose / ref_dose
            scaled_drug_data = drug_data.copy()
            scaled_drug_data['potency_percent'] = drug_data['potency_percent'] * dose_scaling
            reduction = apply_learnable_adjuvant(base_ime_before_adjuvants, scaled_drug_data, pain_type_3d, user_id)
            total_reduction += reduction

    # Droperidol
    if inputs.get('droperidol', False):
        drug_data = LÄKEMEDELS_DATA.get('droperidol')
        reduction = apply_learnable_adjuvant(base_ime_before_adjuvants, drug_data, pain_type_3d, user_id)
        total_reduction += reduction

    # Ketamine
    ketamine_choice = inputs.get('ketamine_choice', 'Ej given')
    if ketamine_choice != 'Ej given':
        drug_data = get_drug_by_ui_choice('ketamine', ketamine_choice)
        reduction = apply_learnable_adjuvant(base_ime_before_adjuvants, drug_data, pain_type_3d, user_id)
        total_reduction += reduction

    # Lidocaine
    lidocaine_choice = inputs.get('lidocaine', 'Nej')
    if lidocaine_choice != 'Nej':
        drug_data = get_drug_by_ui_choice('lidocaine', lidocaine_choice)
        reduction = apply_learnable_adjuvant(base_ime_before_adjuvants, drug_data, pain_type_3d, user_id)
        total_reduction += reduction

    # Betapred
    betapred_choice = inputs.get('betapred', 'Nej')
    if betapred_choice != 'Nej':
        drug_data = get_drug_by_ui_choice('betapred', betapred_choice)
        reduction = apply_learnable_adjuvant(base_ime_before_adjuvants, drug_data, pain_type_3d, user_id)
        total_reduction += reduction

    # Sevoflurane
    if inputs.get('sevoflurane', False):
        drug_data = LÄKEMEDELS_DATA.get('sevoflurane')
        reduction = apply_learnable_adjuvant(base_ime_before_adjuvants, drug_data, pain_type_3d, user_id)
        total_reduction += reduction

    # Infiltration
    if inputs.get('infiltration', False):
        drug_data = LÄKEMEDELS_DATA.get('infiltration')
        reduction = apply_learnable_adjuvant(base_ime_before_adjuvants, drug_data, pain_type_3d, user_id)
        total_reduction += reduction

    # Apply total reduction
    final_ime = max(0, base_ime_before_adjuvants - total_reduction)
    return final_ime

def apply_learnable_adjuvant(base_ime_before_adjuvants, drug_data, procedure_pain_3d, user_id):
    """
    Calculate adjuvant reduction with 3D pain matching.

    Steps:
    1. Get base potency (percentage)
    2. Get learned potency (GLOBAL learning)
    3. Calculate 3D mismatch penalty
    4. Effective reduction = base_ime * potency * penalty
    """
    base_potency_percent = drug_data.get('potency_percent', 0.0)
    drug_name = drug_data.get('name', '')
    drug_pain_3d = {
        'somatic': drug_data['somatic_score'],
        'visceral': drug_data['visceral_score'],
        'neuropathic': drug_data['neuropathic_score']
    }

    # Get learned potency (GLOBAL)
    if user_id:
        drug_key = next((k for k, v in LÄKEMEDELS_DATA.items() if v.get('name') == drug_name), None)
        if drug_key:
            potency_percent = db.get_adjuvant_potency_percent(drug_key, base_potency_percent)
        else:
            potency_percent = base_potency_percent
    else:
        potency_percent = base_potency_percent

    # Calculate 3D mismatch penalty
    penalty = calculate_3d_mismatch_penalty(procedure_pain_3d, drug_pain_3d)

    # Effective reduction (percentage of base IME)
    effective_reduction = base_ime_before_adjuvants * potency_percent * penalty

    return effective_reduction
```

### Step 5: Synergy and Safety Limits
```python
def _apply_synergy_and_safety_limits(ime, inputs, base_ime_before_adjuvants):
    # Apply drug synergy (if learned)
    user_id = auth.get_current_user_id()
    if user_id:
        drug_combo = db.get_drug_combination_key(inputs)
        if drug_combo:
            synergy_factor = db.get_synergy_factor(drug_combo)
            ime *= synergy_factor

    # SAFETY LIMIT: Adjuvants can't reduce IME more than 70%
    min_ime_allowed = base_ime_before_adjuvants * 0.3
    ime = max(ime, min_ime_allowed)

    return ime
```

### Step 6: Fentanyl Pharmacokinetics
```python
def _apply_fentanyl_pharmacokinetics(ime, inputs):
    """
    Subtract remaining fentanyl IME at opslut.

    Bi-exponential model:
        remaining_fraction = learned value (default 0.25)
        fentanyl_ime_remaining = (dose_mcg / 100) * 10 * remaining_fraction
    """
    user_id = auth.get_current_user_id()
    fentanyl_remaining_fraction = db.get_fentanyl_remaining_fraction() if user_id else 0.25
    fentanyl_ime_remaining = (inputs['fentanylDose'] / 100.0) * 10 * fentanyl_remaining_fraction
    return max(0, ime - fentanyl_ime_remaining)
```

### Step 7: Temporal Dosing (Optional)
```python
def _apply_temporal_adjustments(ime, temporal_doses, pain_type_3d):
    """
    Adjust for temporal dosing (time-dependent drug administration).

    1. Calculate remaining fentanyl IME at opslut (bi-exponential decay)
    2. Calculate adjuvant reduction at postop time (trapezoidal effect curves)
    """
    from pharmacokinetics import (
        calculate_temporal_fentanyl_ime_at_opslut,
        calculate_temporal_adjuvant_reduction_at_postop
    )

    # Subtract remaining fentanyl at opslut
    fentanyl_ime_at_opslut = calculate_temporal_fentanyl_ime_at_opslut(temporal_doses)
    ime -= fentanyl_ime_at_opslut

    # Subtract adjuvant effect at postop time (default 60 min)
    adjuvant_reduction = calculate_temporal_adjuvant_reduction_at_postop(
        temporal_doses,
        LÄKEMEDELS_DATA,
        postop_time=60
    )
    ime -= adjuvant_reduction

    ime = max(0, ime)
    return ime
```

### Step 8: Weight Adjustment (ABW Scaling)
```python
def _apply_weight_adjustment(ime, inputs):
    """
    Scale IME by ABW/75kg ratio.

    Example:
        Patient: 180cm man, 100kg
        ABW = 88kg (adjusted for obesity)
        weight_factor = 88 / 75 = 1.17
        ime *= 1.17
    """
    actual_weight = inputs.get('weight', 75)
    height_cm = inputs.get('height', 175)
    sex = inputs.get('sex', 'Man')

    if height_cm > 0 and actual_weight > 0:
        abw = calculate_adjusted_body_weight(actual_weight, height_cm, sex)
        weight_factor = abw / 75  # Reference weight: 75kg
        ime *= weight_factor

    return ime
```

### Step 9: Calibration Factor
```python
def calculate_rule_based_dose(...):
    # ...previous steps...

    composite_key = _get_composite_key(inputs, procedure)
    user_id = auth.get_current_user_id()
    if user_id:
        calibration_factor = db.get_calibration_factor(user_id, composite_key)
        ime *= calibration_factor

    # Round to 0.25 mg
    final_dose = round(max(0, ime / 0.25)) * 0.25

    return {
        'finalDose': final_dose,
        'compositeKey': composite_key,
        # ...
    }
```

---

## LEARNING ENGINE

### Overview
The learning engine uses **back-calculation** to determine what parameters would have predicted the actual requirement correctly, then distributes adjustments across multiple dimensions.

### Learning Trigger
Learning is ONLY triggered when a case is **finalized**:
```python
# In callbacks.py: handle_save_and_learn(finalize=True)
if finalize:
    # 1. Calculate actual requirement
    requirement_data = calculate_actual_requirement(outcome_data, recommended_dose, num_proc_cases, current_inputs)

    # 2. Learn from it
    learn_patient_factors(user_id, requirement_data, current_inputs)
    learn_adjuvant_percentage(user_id, requirement_data, current_inputs)
    learn_procedure_3d_pain(user_id, requirement_data, current_inputs, procedures_df)
    _learn_fentanyl_kinetics(user_id, requirement_data, current_inputs, outcome_data)
```

### Step 1: Calculate Actual Requirement
```python
def calculate_actual_requirement(outcome_data, recommended_dose, num_proc_cases, current_inputs):
    """
    Determine the ACTUAL opioid requirement from case data.

    This is the KEY insight that drives all learning.

    Args:
        outcome_data: {givenDose, uvaDose, vas, respiratory_status, ...}
        recommended_dose: What the app predicted
        num_proc_cases: Number of previous cases (affects learning rate)
        current_inputs: Patient data (for target_vas from settings)

    Returns:
        {
            'actual_requirement': float (mg),
            'prediction_error': float (actual - recommended),
            'outcome_quality': str ('perfect' | 'underdosed' | 'overdosed' | 'acceptable'),
            'learning_magnitude': float (how strongly to learn),
            'base_learning_rate': float
        }
    """
    # Get configurable targets
    target_vas = db.get_setting('TARGET_VAS', 3)
    probe_factor = db.get_setting('DOSE_PROBE_REDUCTION_FACTOR', 0.97)

    # Adaptive learning rate
    if num_proc_cases < 3:
        base_learning_rate = 0.30  # 30% initial
    elif num_proc_cases < 10:
        base_learning_rate = 0.18  # 18% intermediate
    elif num_proc_cases < 20:
        base_learning_rate = 0.12  # 12% advanced
    else:
        base_learning_rate = 0.30 / (1 + 0.05 * num_proc_cases)  # Decay

    given_dose = outcome_data.get('givenDose', 0)
    uva_dose = outcome_data.get('uvaDose', 0)
    vas = outcome_data.get('vas', 5)
    respiratory_status = outcome_data.get('respiratory_status', 'vaken')
    deeply_sedated = (respiratory_status == 'sederad djupt')
    severe_fatigue = outcome_data.get('severe_fatigue', False)
    respiratory_issue = deeply_sedated or severe_fatigue

    actual_given_total = given_dose + uva_dose

    # ===== OUTCOME CLASSIFICATION =====

    # 1. PERFECT: VAS ≤ target, no rescue, no respiratory issue
    if vas <= target_vas and uva_dose == 0 and not respiratory_issue:
        outcome_quality = 'perfect'

        # A. Clinician gave LESS than recommended → Strong signal to lower
        if given_dose < recommended_dose * 0.95:
            actual_requirement = actual_given_total
            learning_magnitude = base_learning_rate * 1.5  # Boost learning

        # B. Clinician followed recommendation → PROBE for lower dose
        #    This is KEY for "always try to lower dose" behavior
        else:
            actual_requirement = actual_given_total * probe_factor  # 97% of given
            learning_magnitude = base_learning_rate * 0.5  # Mild learning

    # 2. UNDERDOSED: VAS > target or rescue needed
    elif vas > target_vas or uva_dose > 0:
        outcome_quality = 'underdosed'

        # Estimate additional dose that would have been needed
        vas_deficit = max(0, vas - target_vas)
        additional_needed = (vas_deficit / 7) * given_dose * 0.3
        additional_needed += uva_dose * 0.5
        actual_requirement = actual_given_total + additional_needed

        # Strong learning signal
        vas_error = math.sqrt(vas_deficit) / math.sqrt(10 - target_vas)
        uva_error = math.sqrt(min(1, uva_dose / 10)) if uva_dose > 0 else 0
        total_error = max(vas_error, uva_error)
        rescue_boost = 1.5 if uva_dose > 0 else 1.0
        learning_magnitude = (base_learning_rate + total_error * 0.35) * rescue_boost

    # 3. OVERDOSED: Respiratory issues
    elif respiratory_issue:
        outcome_quality = 'overdosed'
        actual_requirement = actual_given_total * 0.85  # Dose was too high
        learning_magnitude = base_learning_rate * 0.8  # Strong negative adjustment

    # 4. ACCEPTABLE: None of the above
    else:
        outcome_quality = 'acceptable'
        actual_requirement = actual_given_total
        learning_magnitude = base_learning_rate * 0.2  # Very mild learning

    # Outlier damping
    is_outlier = vas > 8 or uva_dose > 15
    if is_outlier:
        learning_magnitude *= 0.5  # Dampen extreme cases

    prediction_error = actual_requirement - recommended_dose

    return {
        'actual_requirement': actual_requirement,
        'prediction_error': prediction_error,
        'outcome_quality': outcome_quality,
        'learning_magnitude': learning_magnitude,
        'base_learning_rate': base_learning_rate,
        'given_total': actual_given_total,
        'recommended': recommended_dose
    }
```

### Step 2: Learn Patient Factors
```python
def learn_patient_factors(user_id, requirement_data, current_inputs):
    """
    Distribute learning across patient-specific dimensions.

    Only learns if prediction error > 15%.
    """
    updates = []

    prediction_error = requirement_data['prediction_error']
    recommended = requirement_data['recommended']
    learning_mag = requirement_data['learning_magnitude']

    error_ratio = abs(prediction_error) / (recommended or 1)
    if error_ratio < 0.15:
        return updates  # Too small to learn from

    needs_more = prediction_error > 0  # actual > recommended
    needs_less = prediction_error < 0  # actual < recommended

    # AGE FACTOR
    age = current_inputs.get('age', 50)
    age_adjustment = learning_mag * 0.05 * (1 if needs_more else -1)
    from calculation_engine import calculate_age_factor
    from interpolation_engine import get_age_bucket
    default_factor = calculate_age_factor(age)
    age_bucket = get_age_bucket(age)
    new_factor = db.update_age_bucket_learning(age_bucket, default_factor, age_adjustment)
    updates.append(f"**Åldersfaktor ({age}y):** {default_factor:.2f} -> {new_factor:.2f}")

    # ASA FACTOR
    asa_class = current_inputs.get('asa', 'ASA 2')
    asa_adjustment = learning_mag * 0.05 * (1 if needs_more else -1)
    asa_map = {'ASA 1': 1, 'ASA 2': 2, 'ASA 3': 3, 'ASA 4': 4, 'ASA 5': 5}
    asa_num = asa_map.get(asa_class, 2)
    default_asa_factor = APP_CONFIG['DEFAULTS']['ASA_FACTORS'].get(asa_num, 1.0)
    new_factor = db.update_asa_factor(asa_class, default_asa_factor, asa_adjustment)
    updates.append(f"**{asa_class} faktor:** {default_asa_factor:.2f} -> {new_factor:.2f}")

    # WEIGHT/BODY COMPOSITION (4D)
    weight = current_inputs.get('weight', 0)
    height = current_inputs.get('height', 0)
    sex = current_inputs.get('sex', 'Man')

    if weight > 0 and height > 0:
        bmi = calculate_bmi(weight, height)
        ibw = calculate_ideal_body_weight(height, sex)
        abw = calculate_adjusted_body_weight(weight, height, sex)

        body_comp_adjustment = learning_mag * 0.03 * (1 if needs_more else -1)

        # Dimension 1: Actual weight (interpolated)
        weight_bucket = get_weight_bucket(weight)
        new_factor = db.update_weight_bucket_learning(weight_bucket, 1.0, body_comp_adjustment)
        updates.append(f"**Weight factor ({weight:.1f}kg -> {weight_bucket}kg):** -> {new_factor:.3f}")

        # Dimension 2: IBW ratio
        ibw_ratio = weight / ibw
        ibw_ratio_bucket = get_ibw_ratio_bucket(ibw_ratio)
        new_factor = db.update_body_composition_factor('ibw_ratio', ibw_ratio_bucket, 1.0, body_comp_adjustment)
        updates.append(f"**IBW ratio ({ibw_ratio:.1f}x):** -> {new_factor:.3f}")

        # Dimension 3: ABW ratio (for overweight)
        if weight > ibw * 1.2:
            abw_ratio = abw / ibw
            abw_ratio_bucket = get_abw_ratio_bucket(abw_ratio)
            new_factor = db.update_body_composition_factor('abw_ratio', abw_ratio_bucket, 1.0, body_comp_adjustment)
            updates.append(f"**ABW ratio ({abw_ratio:.1f}x):** -> {new_factor:.3f}")

        # Dimension 4: BMI
        bmi_bucket = get_bmi_bucket(bmi)
        bmi_label = get_bmi_label(bmi)
        new_factor = db.update_body_composition_factor('bmi', bmi_bucket, 1.0, body_comp_adjustment)
        updates.append(f"**BMI factor ({bmi:.1f} - {bmi_label}):** -> {new_factor:.3f}")

    # SEX FACTOR
    if sex in ['Man', 'Kvinna']:
        sex_adjustment = learning_mag * 0.03 * (1 if needs_more else -1)
        new_factor = db.update_sex_factor(sex, 1.0, sex_adjustment)
        sex_swedish = "Män" if sex == "Man" else "Kvinnor"
        updates.append(f"**{sex_swedish} faktor:** -> {new_factor:.2f}")

    # RENAL IMPAIRMENT
    renal_impairment = current_inputs.get('renalImpairment', False)
    if renal_impairment:
        renal_adjustment = learning_mag * 0.04 * (1 if needs_more else -1)
        default_renal = 0.75
        new_factor = db.update_renal_factor(default_renal, renal_adjustment)
        updates.append(f"**Njursvikt faktor:** {default_renal:.2f} -> {new_factor:.2f}")

    return updates
```

### Step 3: Learn Adjuvant Potency (GLOBAL)
```python
def learn_adjuvant_percentage(user_id, requirement_data, current_inputs):
    """
    Learn adjuvant percentage-based potency (GLOBAL learning).

    Only learns if error > 10% AND adjuvants were used.
    """
    updates = []

    prediction_error = requirement_data['prediction_error']
    recommended = requirement_data['recommended']
    learning_mag = requirement_data['learning_magnitude']

    error_ratio = abs(prediction_error) / (recommended or 1)
    if error_ratio < 0.10:
        return updates

    needs_more = prediction_error > 0
    needs_less = prediction_error < 0

    # Identify which adjuvants were used
    adjuvants_used = []

    if current_inputs.get('nsaid') and current_inputs.get('nsaid_choice') != 'Ej given':
        adjuvants_used.append(current_inputs.get('nsaid_choice'))

    if current_inputs.get('catapressan'):
        adjuvants_used.append('catapressan')

    if current_inputs.get('droperidol'):
        adjuvants_used.append('droperidol')

    if current_inputs.get('ketamine_choice') and current_inputs['ketamine_choice'] != 'Ej given':
        adjuvants_used.append(current_inputs.get('ketamine_choice'))

    if current_inputs.get('lidocaine') and current_inputs['lidocaine'] != 'Nej':
        adjuvants_used.append('lidocaine_infusion')

    if current_inputs.get('betapred') and current_inputs['betapred'] != 'Nej':
        adjuvants_used.append('betapred')

    # Learn for each adjuvant
    for adjuvant_name in adjuvants_used:
        drug_data = config.LÄKEMEDELS_DATA.get(adjuvant_name)
        if not drug_data or drug_data.get('class') != 'Adjuvant':
            continue

        default_potency = drug_data.get('potency_percent', 0.15)

        # Adjustment logic:
        # needs_more → adjuvant LESS effective → reduce potency %
        # needs_less → adjuvant MORE effective → increase potency %
        adjustment = learning_mag * 0.02 * (-1 if needs_more else 1)

        # Dampen if multiple adjuvants (can't isolate which one to adjust)
        if len(adjuvants_used) > 1:
            adjustment *= 0.7

        new_potency = db.update_adjuvant_potency_percent(adjuvant_name, default_potency, adjustment)

        updates.append(f"**{drug_data['name']} potency:** {default_potency:.1%} -> {new_potency:.1%}")

    return updates
```

### Step 4: Learn Procedure 3D Pain (GLOBAL)
```python
def learn_procedure_3d_pain(user_id, requirement_data, current_inputs, procedures_df):
    """
    Learn procedure 3D pain profile (GLOBAL learning).

    Logic:
    - If adjuvants underperformed (needs_more) → increase pain dimensions where adjuvants were weak
    - If adjuvants overperformed (needs_less) → decrease pain dimensions where adjuvants were strong

    Only learns if error > 15%.
    """
    updates = []

    procedure_id = current_inputs.get('procedure_id')
    if not procedure_id:
        return updates

    proc_data = procedures_df[procedures_df['id'] == procedure_id]
    if proc_data.empty:
        return updates

    prediction_error = requirement_data['prediction_error']
    recommended = requirement_data['recommended']
    learning_mag = requirement_data['learning_magnitude']

    error_ratio = abs(prediction_error) / (recommended or 1)
    if error_ratio < 0.15:
        return updates

    needs_more = prediction_error > 0

    # Get defaults
    default_base_mme = float(proc_data.iloc[0]['baseMME'])
    default_pain_somatic = float(proc_data.iloc[0].get('painTypeScore', 5))
    default_pain_visceral = float(proc_data.iloc[0].get('painVisceral', 5))
    default_pain_neuropathic = float(proc_data.iloc[0].get('painNeuropathic', 2))

    # Get current learned
    learned_data = db.get_procedure_learning_3d(
        procedure_id,
        default_base_mme,
        default_pain_somatic,
        default_pain_visceral,
        default_pain_neuropathic
    )

    # Identify adjuvants used and their pain profiles
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

    if not adjuvants_used:
        return updates

    # Average adjuvant pain profile
    avg_somatic = sum(a['somatic'] for a in adjuvants_used) / len(adjuvants_used)
    avg_visceral = sum(a['visceral'] for a in adjuvants_used) / len(adjuvants_used)
    avg_neuropathic = sum(a['neuropathic'] for a in adjuvants_used) / len(adjuvants_used)

    base_adjustment = learning_mag * 0.15

    somatic_adjustment = 0
    visceral_adjustment = 0
    neuropathic_adjustment = 0

    if needs_more:
        # Adjuvants underperformed → increase pain where adjuvants were weak
        if avg_somatic < 7:
            somatic_adjustment = base_adjustment
        if avg_visceral < 7:
            visceral_adjustment = base_adjustment
        if avg_neuropathic < 7:
            neuropathic_adjustment = base_adjustment
    else:
        # Adjuvants overperformed → decrease pain where adjuvants were strong
        if avg_somatic >= 7:
            somatic_adjustment = -base_adjustment
        if avg_visceral >= 7:
            visceral_adjustment = -base_adjustment
        if avg_neuropathic >= 7:
            neuropathic_adjustment = -base_adjustment

    # Also update base MME
    base_mme_adjustment = prediction_error * learning_mag * 0.1
    max_adjustment = default_base_mme * 0.25
    base_mme_adjustment = max(-max_adjustment, min(max_adjustment, base_mme_adjustment))

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

    return updates
```

### Step 5: Learn Fentanyl Kinetics
```python
def _learn_fentanyl_kinetics(user_id, requirement_data, current_inputs, outcome):
    """
    Learn fentanyl elimination kinetics.

    Only learns if outcome was 'underdosed' AND fentanyl was given.

    Logic:
    - rescue_early (< 30 min) → fentanyl wears off faster → decrease remaining fraction
    - rescue_late (> 60 min) → fentanyl lasted longer OR base dose too low → don't adjust fentanyl
    - rescue_early AND rescue_late → massive underdose → adjust both
    """
    if current_inputs.get('fentanylDose', 0) <= 0:
        return

    if requirement_data['outcome_quality'] != 'underdosed':
        return

    rescue_early = outcome.get('rescue_early', False)
    rescue_late = outcome.get('rescue_late', False)
    adjustment = requirement_data['learning_magnitude']

    fentanyl_adjustment = 0

    if rescue_early and not rescue_late:
        # Early pain → fentanyl wore off too fast
        fentanyl_adjustment = adjustment * (-0.03)  # Large decrease
        caption = f"💉 Fentanyl-kinetik uppdaterad (tidig smärta): {db.get_fentanyl_remaining_fraction(user_id):.3f} (kortare svans)"
    elif rescue_late and not rescue_early:
        # Late pain only → base dose too low, don't blame fentanyl
        caption = f"📊 Grunddos för låg (sen smärta), calibration_factor justerad"
    elif rescue_early and rescue_late:
        # Both → massive underdose
        fentanyl_adjustment = adjustment * (-0.02)  # Small decrease
        caption = f"⚠️ Både fentanyl-kinetik OCH grunddos justerade (massiv underdosering)"

    if fentanyl_adjustment != 0:
        db.update_fentanyl_remaining_fraction(user_id, fentanyl_adjustment)

    if caption:
        st.caption(caption)
```

---

## 3D PAIN MATCHING SYSTEM

### Pain Dimensions
Every procedure and drug has a 3D pain profile:
- **Somatic:** Musculoskeletal pain (skin, muscle, bone) [0-10]
- **Visceral:** Organ pain (stretching, inflammation) [0-10]
- **Neuropathic:** Nerve pain (burning, shooting) [0-10]

### Drug Pain Profiles (Examples)
```python
# NSAIDs: Strong somatic, weak visceral/neuropathic
'ibuprofen_400mg': {
    'somatic_score': 9,
    'visceral_score': 2,
    'neuropathic_score': 1
}

# Ketamine: Strong neuropathic, moderate somatic/visceral
'ketamine_small_bolus': {
    'somatic_score': 4,
    'visceral_score': 5,
    'neuropathic_score': 9
}

# Clonidine (Catapressan): Strong visceral/neuropathic, weak somatic
'clonidine': {
    'somatic_score': 3,
    'visceral_score': 7,
    'neuropathic_score': 6
}
```

### Procedure Pain Profiles (Examples)
```python
# Knee arthroscopy: Primarily somatic
{
    'somatic': 8,
    'visceral': 2,
    'neuropathic': 1
}

# Laparoscopic cholecystectomy: Mixed somatic/visceral
{
    'somatic': 5,
    'visceral': 7,
    'neuropathic': 2
}

# Nerve decompression surgery: High neuropathic
{
    'somatic': 5,
    'visceral': 2,
    'neuropathic': 8
}
```

### Mismatch Penalty Calculation
```python
def calculate_3d_mismatch_penalty(procedure_pain: dict, drug_pain: dict) -> float:
    """
    Calculate mismatch penalty using Euclidean distance in 3D space.

    Perfect match (distance=0) → penalty=1.0 (full effectiveness)
    Max mismatch (distance=17.3) → penalty=0.5 (50% effectiveness)

    Args:
        procedure_pain: {'somatic': X, 'visceral': Y, 'neuropathic': Z}
        drug_pain: {'somatic': X, 'visceral': Y, 'neuropathic': Z}

    Returns:
        Penalty factor (0.5-1.0)

    Example:
        Procedure: {somatic: 8, visceral: 2, neuropathic: 1}  # Knee arthroscopy
        Ibuprofen: {somatic: 9, visceral: 2, neuropathic: 1}
        Distance = sqrt((8-9)^2 + (2-2)^2 + (1-1)^2) = 1.0
        Normalized = 1.0 / 17.3 = 0.058
        Penalty = 1.0 - 0.058 = 0.94 (excellent match!)

        Same procedure with:
        Ketamine: {somatic: 4, visceral: 5, neuropathic: 9}
        Distance = sqrt((8-4)^2 + (2-5)^2 + (1-9)^2) = 9.43
        Normalized = 9.43 / 17.3 = 0.545
        Penalty = max(0.5, 1.0 - 0.545) = 0.50 (poor match)
    """
    import math

    distance = math.sqrt(
        (procedure_pain['somatic'] - drug_pain['somatic'])**2 +
        (procedure_pain['visceral'] - drug_pain['visceral'])**2 +
        (procedure_pain['neuropathic'] - drug_pain['neuropathic'])**2
    )

    # Max distance: from (0,0,0) to (10,10,10) = sqrt(300) ≈ 17.3
    max_distance = math.sqrt(3 * 10**2)

    normalized_distance = distance / max_distance
    penalty = max(0.5, 1.0 - normalized_distance)

    return penalty
```

### How It Works in Practice
```python
# In apply_learnable_adjuvant():
effective_reduction = base_ime_before_adjuvants * potency_percent * penalty

# Example 1: Perfect match
base_ime = 20 MME
ibuprofen_potency = 0.175 (17.5%)
penalty = 0.94 (excellent match)
reduction = 20 * 0.175 * 0.94 = 3.29 MME

# Example 2: Poor match
base_ime = 20 MME
ketamine_potency = 0.10 (10%)
penalty = 0.50 (poor match)
reduction = 20 * 0.10 * 0.50 = 1.00 MME
```

---

## INTERPOLATION SYSTEM

### Purpose
Allow learning from sparse data by estimating values from nearby observations.

### Gaussian Weighting
```python
def gaussian_weight(distance: float, sigma: float = 1.0) -> float:
    """
    Nearby points get higher weight.

    Examples:
        distance=0 → weight=1.0
        distance=1 → weight=0.61
        distance=2 → weight=0.14
        distance=3 → weight=0.01
    """
    return math.exp(-(distance ** 2) / (2 * sigma ** 2))
```

### Age Interpolation
```python
def interpolate_age_factor(age: int, default_factor: float) -> Dict:
    """
    Steps:
    1. Try to get direct data for this age
    2. If insufficient data, search within ±5 years
    3. Weight nearby ages using Gaussian weighting
    4. Also weight by number of observations (more data = higher trust)
    5. Return weighted average

    Example:
        Target: age 73
        Data:
            age 70: factor=0.70, n=8 observations
            age 72: factor=0.68, n=5 observations
            age 75: factor=0.63, n=10 observations

        Weights:
            age 70: distance=3, gauss=0.14, obs_weight=0.8 → combined=0.11
            age 72: distance=1, gauss=0.61, obs_weight=0.5 → combined=0.30
            age 75: distance=2, gauss=0.36, obs_weight=1.0 → combined=0.36

        Interpolated factor = (0.70*0.11 + 0.68*0.30 + 0.63*0.36) / (0.11+0.30+0.36)
                            = 0.657
    """
    bucket = get_age_bucket(age)  # Just int(age)

    # Try direct data
    try:
        direct_data = db.get_age_bucket_learning(bucket)
        if direct_data and direct_data.get('num_observations', 0) >= 3:
            return {
                'age_factor': direct_data['age_factor'],
                'method': 'direct',
                'num_observations': direct_data['num_observations'],
                'sources': [f"Age {age} (direct data, n={direct_data['num_observations']})"]
            }
    except:
        pass

    # Get nearby ages
    nearby = get_nearby_age_factors(age, max_distance=5)

    if not nearby:
        return {
            'age_factor': default_factor,
            'method': 'default',
            'num_observations': 0,
            'sources': ['Default formula (no nearby data)']
        }

    # Weighted average
    total_weighted_factor = 0.0
    total_weight = 0.0
    sources = []

    for neighbor_age, neighbor_factor, num_obs, distance_weight in nearby:
        observation_weight = min(1.0, num_obs / 10.0)  # Plateau at 10
        combined_weight = distance_weight * observation_weight

        total_weighted_factor += neighbor_factor * combined_weight
        total_weight += combined_weight

        sources.append(f"Age {neighbor_age} (factor={neighbor_factor:.3f}, n={num_obs}, weight={combined_weight:.3f})")

    if total_weight == 0:
        return {'age_factor': default_factor, 'method': 'default', ...}

    interpolated_factor = total_weighted_factor / total_weight

    # Sanity check
    if interpolated_factor < 0.2 or interpolated_factor > 2.0:
        return {'age_factor': default_factor, 'method': 'default', ...}

    return {
        'age_factor': interpolated_factor,
        'method': 'interpolated',
        'num_observations': 0,
        'sources': sources,
        'nearby_count': len(nearby)
    }
```

### Weight Interpolation
Same algorithm as age, but for weight buckets (±10 kg search range).

---

## PHARMACOKINETICS

### Fentanyl Bi-Exponential Model
```python
def calculate_fentanyl_remaining_at_opslut(dose_mcg: float, time_before_opslut_min: int) -> float:
    """
    Bi-exponential decay model:

    Fast component (60%): t½ = 15 min
    Slow component (40%): t½ = 210 min

    Example:
        200 µg given 90 min before opslut
        Fast: 0.6 * 200 * (0.5 ** (90/15)) = 1.88 µg
        Slow: 0.4 * 200 * (0.5 ** (90/210)) = 59.2 µg
        Total remaining: 61.1 µg (~30%)
    """
    if time_before_opslut_min <= 0:
        return dose_mcg

    fast_component = 0.6 * dose_mcg * (0.5 ** (time_before_opslut_min / 15))
    slow_component = 0.4 * dose_mcg * (0.5 ** (time_before_opslut_min / 210))

    remaining = fast_component + slow_component
    return max(0, remaining)
```

### Adjuvant Effect Curves (Trapezoidal)
```python
def calculate_adjuvant_effect_at_time(drug_data, dose, time_relative_to_opslut, postop_time):
    """
    Trapezoidal effect curve:

    Effect
     1.0 |      _____________________
         |     /                      \
         |    /                        \
     0.0 |___/                          \___
         0  onset  peak            duration
              (min)

    Example: Ibuprofen
        onset=30 min, peak=60 min, duration=360 min

        Time since admin = postop_time - time_relative_to_opslut

        Given at -10 min (10 min before opslut), evaluated at +60 min postop
        → Time since admin = 60 - (-10) = 70 min
        → 70 > 60 (peak) → full effect (1.0)

        Evaluated at +300 min postop
        → Time since admin = 310 min
        → 310 < 360 (duration) → declining
        → effect = 1.0 - ((310-60)/(360-60)) = 1.0 - 0.833 = 0.17 (17% effective)
    """
    time_since_admin = postop_time - time_relative_to_opslut

    if time_since_admin < 0:
        return 0.0  # Not given yet

    t_onset = drug_data.get('onset_minutes', 30)
    t_peak = drug_data.get('peak_minutes', 60)
    t_duration = drug_data.get('duration_minutes', 240)

    if time_since_admin < t_onset:
        # Rising phase
        effect = time_since_admin / t_onset
    elif time_since_admin < t_peak:
        # Plateau
        effect = 1.0
    elif time_since_admin < t_duration:
        # Declining phase
        effect = 1.0 - ((time_since_admin - t_peak) / (t_duration - t_peak))
    else:
        # Expired
        effect = 0.0

    return max(0, min(1, effect))
```

---

## TEMPORAL DOSING

### Concept
Instead of single "fentanyl dose during surgery", track WHEN each drug was given relative to opslut (end of surgery).

### Time Convention
- **Negative time:** Before opslut (e.g., -90 = 90 min before end of surgery)
- **Zero:** At opslut
- **Positive time:** After opslut (e.g., +60 = 1h postop)

### Temporal Dose Entry
```python
{
    'drug_type': 'fentanyl',
    'drug_name': 'Fentanyl',
    'dose': 100,  # µg
    'units': 'mcg',
    'time_relative_minutes': -90,  # 90 min before opslut
    'notes': 'Induction'
}
```

### Calculation Flow
```python
def _apply_temporal_adjustments(ime, temporal_doses, pain_type_3d):
    # 1. Calculate remaining fentanyl at opslut
    fentanyl_ime_at_opslut = calculate_temporal_fentanyl_ime_at_opslut(temporal_doses)
    ime -= fentanyl_ime_at_opslut

    # 2. Calculate adjuvant effect at postop time (e.g., 60 min)
    adjuvant_reduction = calculate_temporal_adjuvant_reduction_at_postop(
        temporal_doses,
        LÄKEMEDELS_DATA,
        postop_time=60
    )
    ime -= adjuvant_reduction

    ime = max(0, ime)
    return ime
```

---

## SECURITY & SAFETY

### 1. Authentication
```python
# Admin account (required password)
- Username from env/secrets
- Bcrypt hashed password
- Can access all features

# Regular users (no password)
- Username only (case-insensitive)
- Separate learning per user
- Can only edit own cases
```

### 2. Input Validation
```python
VALIDATION_RULES = {
    'age': (0, 120),
    'weight': (1.0, 500.0),
    'height': (30.0, 250.0),
    'bmi': (10.0, 80.0),
    'fentanylDose': (0, 2000),  # µg
    'givenDose': (0, 100),  # mg oxycodone
    'uvaDose': (0, 100),
    'vas': (0, 10)
}
```

### 3. Dose Safety Limits
```python
# Adjuvant safety limit
min_ime = base_ime_before_adjuvants * 0.3  # Max 70% reduction

# Absolute limits
MAX_DOSE = 30.0  # mg oxycodone (warn if exceeded)
MIN_DOSE = 0.0

# Rounding
final_dose = round(ime / 0.25) * 0.25  # 0.25 mg increments
```

### 4. Learning Safety
```python
# Outlier damping
if vas > 8 or uva_dose > 15:
    learning_magnitude *= 0.5

# Max single-case adjustment
max_base_mme_adjustment = default_base_mme * 0.25  # Max 25% per case

# Sanity checks on interpolated values
if interpolated_factor < 0.2 or > 2.0:
    use default_factor instead
```

### 5. Audit Trail
- All case edits logged with timestamp, user, old/new values
- Cannot delete cases, only mark as invalid
- Complete calculation stored with each case

---

## CONFIGURATION

### config.py Structure
```python
APP_CONFIG = {
    'ML_THRESHOLD_PER_PROCEDURE': 15,  # Cases needed before ML
    'ML_TARGET_VAS': 1.0,  # Target for ML (not used in rule-based)
    'FENTANYL_HALFLIFE_FRACTION': 0.25,  # Default remaining fraction
    'FENTANYL_IME_CONVERSION_FACTOR': 10,  # 100 µg = 10 MME
    'MME_ROUNDING_STEP': 0.25,
    'REFERENCE_WEIGHT_KG': 75,
    'ADJUVANT_SAFETY_LIMIT_FACTOR': 0.3,  # Min 30% of base IME

    'DEFAULTS': {
        'OPIOID_TOLERANCE_FACTOR': 1.5,
        'PAIN_THRESHOLD_FACTOR': 1.2,
        'RENAL_IMPAIRMENT_FACTOR': 0.85,
        'ASA_FACTORS': {1: 1.0, 2: 1.0, 3: 0.9, 4: 0.8, 5: 0.7}
    },

    'LEARNING': {
        'INITIAL_LEARNING_RATE': 0.30,
        'INTERMEDIATE_LEARNING_RATE': 0.18,
        'ADVANCED_LEARNING_RATE': 0.12,
        'LEARNING_RATE_DECAY': 0.05,
        'ERROR_ADJUSTMENT_FACTOR': 0.35,
        'RESPIRATORY_ADJUSTMENT_FACTOR': -0.8,
        'RESCUE_BOOST_HIGH': 2.0,
        'RESCUE_BOOST_MEDIUM': 1.5,
        'OUTLIER_DAMPING_FACTOR': 0.5
    }
}
```

### LÄKEMEDELS_DATA
See full specification in [config.py](config.py:77-346)

Key structure:
```python
'drug_key': {
    'name': str,
    'class': str ('Opioid' | 'NSAID' | 'Adjuvant' | 'Regional'),
    'somatic_score': float (0-10),
    'visceral_score': float (0-10),
    'neuropathic_score': float (0-10),
    'potency_percent': float (0-1, for adjuvants),
    'systemic_impact': int (0-10),
    'onset_minutes': int,
    'peak_minutes': int,
    'duration_minutes': int,
    'ui_choice': str (dropdown value)
}
```

---

## API SPECIFICATIONS

### Core Functions

#### calculate_rule_based_dose
```python
def calculate_rule_based_dose(
    inputs: dict,
    procedures_df: pd.DataFrame,
    temporal_doses: list = None
) -> dict:
    """
    Main calculation function.

    Args:
        inputs: {
            'age', 'sex', 'weight', 'height',
            'asa', 'opioidHistory', 'lowPainThreshold', 'renalImpairment',
            'procedure_id', 'fentanylDose',
            'nsaid_choice', 'catapressan_dose', 'droperidol',
            'ketamine_choice', 'lidocaine', 'betapred',
            'sevoflurane', 'infiltration'
        }
        procedures_df: DataFrame with procedures
        temporal_doses: Optional list of temporal dose dicts

    Returns:
        {
            'finalDose': float (mg oxycodone),
            'compositeKey': str,
            'procedure': dict,
            'engine': "Regelmotor",
            'ibw': float,
            'abw': float,
            'actual_weight': float,
            'pain_type_3d': dict
        }
    """
```

#### save_case
```python
def save_case(case_data: dict, user_id: int) -> int:
    """
    Save new case to database.

    Args:
        case_data: Complete case dictionary (patient + procedure + outcome)
        user_id: User ID

    Returns:
        case_id: int
    """
```

#### finalize_case
```python
def finalize_case(case_id: int, final_data: dict, user_id: int):
    """
    Mark case as FINALIZED and trigger learning.

    Args:
        case_id: Case ID to finalize
        final_data: Final outcome data
        user_id: User ID

    Side effects:
        - Updates case status to 'FINALIZED'
        - Triggers all learning functions
        - Cannot be un-finalized
    """
```

#### calculate_actual_requirement
```python
def calculate_actual_requirement(
    outcome_data: dict,
    recommended_dose: float,
    num_proc_cases: int,
    current_inputs: dict
) -> dict:
    """
    Calculate actual opioid requirement from case outcome.

    Returns:
        {
            'actual_requirement': float,
            'prediction_error': float,
            'outcome_quality': str,
            'learning_magnitude': float,
            'base_learning_rate': float
        }
    """
```

---

## UI/UX SPECIFICATIONS

### Tabs Structure
1. **Dosering** (Main calculator)
   - Patient inputs (age, sex, weight, height, ASA)
   - Patient factors (opioid history, pain threshold, renal)
   - Procedure selection (specialty → procedure)
   - Intraoperative (fentanyl, optime)
   - Adjuvants (NSAIDs, catapressan, droperidol, ketamine, lidocaine, betapred, sevoflurane, infiltration)
   - Temporal dosing (optional, advanced feature)
   - Calculate button → Recommended dose
   - Outcome entry (given dose, VAS, rescue dose, respiratory status)
   - Save (IN_PROGRESS) or Finalize (triggers learning)

2. **Historik** (Case history)
   - List all cases (user's own or all if admin)
   - Filter by date, procedure, outcome
   - View/edit cases
   - Learning insights visualization

3. **Utbildning** (Education/procedures)
   - View procedure catalog
   - Add new procedures (admin only)
   - View 3D pain profiles
   - Drug database reference

4. **Ingrepp** (Admin panel)
   - User management
   - Settings (target VAS, probe factor)
   - Export data
   - Learning statistics
   - Database maintenance

### Design System (Figma)
- See [ui/figma_design.css](ui/figma_design.css)
- Color scheme: Blue gradient (#1173D4 to #24A8A8)
- Typography: Inter font family
- Components: Cards, tabs, inputs, buttons
- Responsive design (mobile-friendly)

---

## DEPLOYMENT

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="your_password"

# Run app
streamlit run oxydoseks.py
```

### Production (Streamlit Cloud)
1. Push to GitHub
2. Connect repository to Streamlit Cloud
3. Set secrets in Streamlit Cloud dashboard:
   ```toml
   [admin]
   username = "admin"
   password_hash = "$2b$12$..."  # bcrypt hash
   ```
4. Deploy

### Docker (Optional)
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "oxydoseks.py"]
```

---

## TESTING STRATEGY

### Unit Tests
- Test all calculation functions with known inputs/outputs
- Test learning algorithms with synthetic data
- Test interpolation with sparse data
- Test pharmacokinetics models
- Test 3D pain matching

### Integration Tests
- Full calculation flow (input → dose → outcome → learning)
- Database operations
- Authentication
- Multi-user scenarios

### Regression Tests
- Verify learning doesn't drift over time
- Check safety limits are never violated
- Ensure deterministic results for same inputs

### Clinical Validation
- Compare recommendations with expert anesthesiologist opinions
- Track prediction errors over time
- Monitor learning convergence

---

## TODO LIST FOR REBUILD

### Phase 1: Core Infrastructure
- [ ] Set up Python 3.10+ environment
- [ ] Install dependencies (streamlit, pandas, bcrypt, tinydb)
- [ ] Create project structure (all modules listed above)
- [ ] Implement config.py with LÄKEMEDELS_DATA
- [ ] Create database.py with TinyDB wrapper
- [ ] Implement auth.py (bcrypt, multi-user)
- [ ] Set up logging

### Phase 2: Calculation Engine
- [ ] Implement calculate_age_factor
- [ ] Implement calculate_ideal_body_weight
- [ ] Implement calculate_adjusted_body_weight
- [ ] Implement calculate_bmi
- [ ] Implement calculate_lean_body_mass
- [ ] Implement _get_initial_ime_and_pain_type
- [ ] Implement _apply_patient_factors (all factors)
- [ ] Implement apply_learnable_adjuvant
- [ ] Implement _apply_adjuvants (all adjuvant types)
- [ ] Implement _apply_synergy_and_safety_limits
- [ ] Implement _apply_fentanyl_pharmacokinetics
- [ ] Implement _apply_weight_adjustment
- [ ] Implement _get_composite_key
- [ ] Implement calculate_rule_based_dose (main function)

### Phase 3: 3D Pain System
- [ ] Implement calculate_3d_mismatch_penalty
- [ ] Add 3D pain scores to all procedures
- [ ] Add 3D pain scores to all drugs
- [ ] Test matching algorithm with various combinations

### Phase 4: Learning Engine
- [ ] Implement calculate_actual_requirement
- [ ] Implement learn_patient_factors
- [ ] Implement learn_adjuvant_percentage
- [ ] Implement learn_procedure_3d_pain
- [ ] Implement _learn_fentanyl_kinetics
- [ ] Add configurable TARGET_VAS and PROBE_FACTOR to settings

### Phase 5: Interpolation
- [ ] Implement gaussian_weight
- [ ] Implement get_nearby_age_factors
- [ ] Implement get_nearby_weight_factors
- [ ] Implement interpolate_age_factor
- [ ] Implement interpolate_weight_factor
- [ ] Test interpolation with sparse data

### Phase 6: Body Composition (4D Learning)
- [ ] Implement get_weight_bucket
- [ ] Implement get_ibw_ratio_bucket
- [ ] Implement get_abw_ratio_bucket
- [ ] Implement get_bmi_bucket
- [ ] Create body_composition_factors table
- [ ] Integrate 4D learning into calculation engine
- [ ] Integrate 4D learning into learning engine

### Phase 7: Pharmacokinetics
- [ ] Implement calculate_fentanyl_remaining_at_opslut
- [ ] Implement calculate_fentanyl_remaining_at_time
- [ ] Implement calculate_adjuvant_effect_at_time
- [ ] Implement calculate_total_opioid_auc
- [ ] Test bi-exponential model accuracy

### Phase 8: Temporal Dosing
- [ ] Create temporal_doses table
- [ ] Implement save_temporal_doses
- [ ] Implement get_temporal_doses
- [ ] Implement calculate_temporal_fentanyl_ime_at_opslut
- [ ] Implement calculate_temporal_adjuvant_reduction_at_postop
- [ ] Implement _apply_temporal_adjustments
- [ ] Create temporal dosing UI

### Phase 9: Database Functions
- [ ] Implement all get_* functions (age, weight, ASA, sex, etc.)
- [ ] Implement all update_* functions
- [ ] Implement get_procedure_learning_3d
- [ ] Implement update_procedure_learning_3d
- [ ] Implement get_adjuvant_potency_percent
- [ ] Implement update_adjuvant_potency_percent
- [ ] Implement case CRUD (create, read, update, finalize)
- [ ] Implement edit history tracking

### Phase 10: Callbacks & Integration
- [ ] Implement get_current_inputs
- [ ] Implement _get_outcome_data_from_state
- [ ] Implement _save_or_update_case_in_db
- [ ] Implement handle_save_and_learn
- [ ] Connect calculation → outcome → learning pipeline

### Phase 11: UI - Main Layout
- [ ] Create main_layout.py
- [ ] Implement header with logo and user info
- [ ] Implement tab navigation
- [ ] Add logout functionality

### Phase 12: UI - Dosing Tab
- [ ] Create dosing_tab.py
- [ ] Patient demographics section
- [ ] Patient factors section
- [ ] Procedure selection (specialty → procedure)
- [ ] Intraoperative section
- [ ] Adjuvants section (all types)
- [ ] Temporal dosing section (advanced)
- [ ] Calculate button
- [ ] Results display
- [ ] Outcome entry form
- [ ] Save/Finalize buttons

### Phase 13: UI - History Tab
- [ ] Create history_tab.py
- [ ] Case list with filters
- [ ] Case detail view
- [ ] Edit case functionality
- [ ] Learning insights visualization
- [ ] Export functionality

### Phase 14: UI - Education Tab
- [ ] Create procedures_tab.py
- [ ] Procedure catalog display
- [ ] Add procedure form (admin only)
- [ ] 3D pain profile visualization
- [ ] Drug reference database

### Phase 15: UI - Admin Tab
- [ ] Create admin_tab.py
- [ ] User management
- [ ] Settings panel (target VAS, probe factor)
- [ ] Data export
- [ ] Learning statistics dashboard
- [ ] Database maintenance tools

### Phase 16: Styling
- [ ] Apply Figma CSS (figma_design.css)
- [ ] Customize Streamlit theme
- [ ] Responsive design testing
- [ ] Accessibility improvements

### Phase 17: Testing
- [ ] Write unit tests for all calculation functions
- [ ] Write unit tests for learning functions
- [ ] Write integration tests for full flow
- [ ] Test interpolation edge cases
- [ ] Test 3D pain matching
- [ ] Test temporal dosing
- [ ] Test multi-user scenarios
- [ ] Clinical validation with test cases

### Phase 18: Documentation
- [ ] Write README.md (user manual)
- [ ] Write SPECIFICATION.md (technical spec) ← YOU ARE HERE
- [ ] Add inline code documentation
- [ ] Create deployment guide
- [ ] Create troubleshooting guide
- [ ] Create video tutorials (optional)

### Phase 19: Security & Safety
- [ ] Implement input validation
- [ ] Add dose safety checks
- [ ] Test authentication
- [ ] Audit trail verification
- [ ] Penetration testing (basic)

### Phase 20: Deployment
- [ ] Test local deployment
- [ ] Set up Streamlit Cloud deployment
- [ ] Configure secrets management
- [ ] Set up backup strategy
- [ ] Monitor error logs
- [ ] Performance optimization

### Phase 21: Maintenance & Monitoring
- [ ] Set up logging and monitoring
- [ ] Create backup/restore procedures
- [ ] Plan for database migrations
- [ ] User feedback collection
- [ ] Continuous learning monitoring
- [ ] Performance metrics tracking

---

## NOTES FOR DEVELOPERS

### Critical Design Decisions

1. **Percentage-based adjuvants:** Scales correctly for all procedure sizes
2. **3D pain matching:** More accurate than single pain score
3. **GLOBAL learning for procedures/adjuvants:** Benefits all users
4. **Per-user learning for patient factors:** Captures practice variation
5. **Interpolation:** Handles sparse data gracefully
6. **Bi-exponential fentanyl:** Clinically validated model
7. **Probing on perfect outcomes:** Drives dose reduction
8. **Adaptive learning rate:** Fast initial learning, stable long-term
9. **Outlier damping:** Prevents single bad case from ruining model
10. **Safety limits:** Multiple layers (adjuvant cap, sanity checks, outlier detection)

### Performance Considerations
- TinyDB is fast for <10,000 cases
- For larger datasets, migrate to PostgreSQL/MySQL
- Interpolation is O(n) per calculation but n is small (±5-10 datapoints)
- No expensive ML training, all updates are incremental

### Future Enhancements
- [ ] Web-based (React + FastAPI) for better UX
- [ ] Real ML models (XGBoost, neural nets) alongside rule-based
- [ ] Multi-site deployment with central learning database
- [ ] Mobile app for bedside use
- [ ] Integration with EHR systems
- [ ] Predictive analytics for complications
- [ ] A/B testing framework for comparing algorithms

---

**END OF SPECIFICATION**

This document contains EVERYTHING needed to rebuild the application from scratch with no loss of functionality or information.
