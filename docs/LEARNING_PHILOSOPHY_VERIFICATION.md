# Learning Philosophy Verification

## User's Learning Philosophy

The system should learn from **three intersecting dimensions**:

### 1. **Procedure Learning** (Same procedure, different patients/adjuvants)
**Focus:** Learn how much MME the procedure requires
- Same surgical procedure (e.g., lap cholecystectomy)
- Across many different patients (ages, weights, sexes, ASA)
- With different combinations of adjuvants
- **Learns mostly:** Procedure baseMME requirements

### 2. **Patient Factor Learning** (Similar patients, different procedures/adjuvants)
**Focus:** Learn what different "types" of patients require
- Patients that are "alike" (e.g., all 70+ year old females, BMI 30)
- Across many different procedures
- With different combinations of adjuvants
- **Learns mostly:** Patient-type dosing patterns (age, weight, sex, ASA, renal)

### 3. **Adjuvant Learning** (Same adjuvants, different procedures/patients)
**Focus:** Learn preference and effectiveness of adjuvants
- Same adjuvants (e.g., parecoxib 40mg, catapressan, NSAIDs)
- Across many different procedures
- Across many different patient types
- **Learns mostly:** Adjuvant effectiveness and pain type selectivity
- **GLOBAL learning:** All users benefit from collective knowledge

## Current Implementation Verification

### ✅ 1. Procedure Learning - CORRECT

**File:** `learning_engine.py` function `learn_procedure_requirements()`

**What it does:**
```python
def learn_procedure_requirements(user_id, requirement_data, current_inputs, procedures_df):
    """
    Learn procedure baseMME from actual requirement.

    Back-calculates: If actual requirement was X mg, what baseMME adjustment
    would have predicted this correctly?
    """
    # Gets procedure_id from current_inputs
    # Looks up default baseMME for this specific procedure
    # Calculates: prediction_error = actual_requirement - recommended
    # Adjusts: baseMME for this procedure

    base_mme_adjustment = prediction_error * learning_mag * 0.1
    db.update_procedure_learning(user_id, procedure_id, base_mme_adjustment)
```

**How it learns:**
- ✅ Learns per-procedure (cholecystectomy learns separately from appendectomy)
- ✅ Learns across different patients (aggregates data from all patient types)
- ✅ Learns across different adjuvant combinations
- ✅ Focuses on baseMME requirements

**Example:** "Lap cholecystectomy consistently needs 15 MME across 50 patients with various adjuvants"

### ✅ 2. Patient Factor Learning - CORRECT

**File:** `learning_engine.py` function `learn_patient_factors()`

**What it does:**
```python
def learn_patient_factors(user_id, requirement_data, current_inputs):
    """
    Learn patient-specific factors from actual requirement.

    Learns:
    - Age factor (elderly need less/more?)
    - 4D Body composition (weight, IBW ratio, ABW ratio, BMI)
    - ASA factor (sicker patients need less/more?)
    - Sex factor (males vs females)
    - Renal factor (GFR <35 patients)
    """
    # Learns if age >= 65
    db.update_age_factor(user_id, age, age_adjustment)

    # Learns for all weights (4D)
    db.update_body_composition_factor(user_id, 'weight', weight_bucket, adjustment)
    db.update_body_composition_factor(user_id, 'ibw_ratio', ibw_ratio_bucket, adjustment)
    db.update_body_composition_factor(user_id, 'abw_ratio', abw_ratio_bucket, adjustment)
    db.update_body_composition_factor(user_id, 'bmi', bmi_bucket, adjustment)

    # Learns for ASA 3-5
    db.update_asa_factor(user_id, asa_class, asa_adjustment)

    # Learns for both sexes
    db.update_sex_factor(user_id, sex, sex_adjustment)

    # Learns for renal impairment
    db.update_renal_factor(user_id, renal_adjustment)
```

**How it learns:**
- ✅ Learns per-patient-type (70yo females learn separately from 30yo males)
- ✅ Learns across different procedures (same patient factors apply to all procedures)
- ✅ Learns across different adjuvant combinations
- ✅ Focuses on patient-type dosing patterns

**Example:** "70-year-old females consistently need 20% less across cholecystectomy, appendectomy, and hernia repair"

### ✅ 3. Adjuvant Learning - CORRECT (GLOBAL)

**File:** `callbacks.py` function `_learn_adjuvant_effectiveness()`

**What it does:**
```python
def _learn_adjuvant_effectiveness(user_id, current_inputs, outcome_data, learning_updates, procedures_df):
    """
    Learn how effective adjuvants were from actual outcome.
    """
    # For each adjuvant used (NSAIDs, Catapressan, Ketamine, etc.)
    _learn_from_adjuvant(user_id, adjuvant_name, pain_type_score,
                        adjuvant_selectivity, base_potency, outcome_data)

def _learn_from_adjuvant(user_id, adjuvant_name, pain_type_score,
                        adjuvant_selectivity, base_potency, outcome_data):
    # Calculate adjustments based on outcome
    selectivity_adj = calculate_selectivity_adjustment(vas, pain_type_score,
                                                      adjuvant_selectivity, rescue)
    potency_adj = calculate_potency_adjustment(vas, rescue_dose, respiratory_issue)

    # GLOBAL learning - NO user_id in storage!
    db.update_adjuvant_learning(adjuvant_name, selectivity_adj, potency_adj)
```

**Database:** `learning_adjuvants` table with PRIMARY KEY `(adjuvant_name)` only (no user_id)

**How it learns:**
- ✅ Learns per-adjuvant (parecoxib learns separately from ketorolac)
- ✅ Learns across different procedures (same adjuvant tested in many surgeries)
- ✅ Learns across different patient types
- ✅ **GLOBAL:** All users contribute to and benefit from collective knowledge
- ✅ Focuses on effectiveness (potency) and pain type matching (selectivity)

**Migration v2:** Aggregates existing per-user data into global learning

**Example:** "Parecoxib 40mg is 15% more effective on visceral pain than initially thought, learned from 200 cases across all users"

## Learning Distribution Example

### Case: 72yo female, 62kg, cholecystectomy, parecoxib + catapressan
**Outcome:** VAS 2, UVA 0mg (perfect), but gave 5.2mg when recommended 7mg

**Learning distribution:**
1. **Procedure learning (30%):** "Cholecystectomy needs 10% less baseMME"
2. **Patient learning (40%):**
   - Age (72yo): "Elderly need 3% less"
   - Weight (62kg): "Patients at 60kg need 2% less"
   - Sex (female): "Females need 2% less"
   - BMI (23.1): "Normal BMI needs 2% less"
3. **Adjuvant learning (30%):**
   - Parecoxib: "2% more effective on visceral pain than expected"
   - Catapressan: "1% more effective on visceral pain than expected"

**Next similar case:**
- Same procedure → benefits from procedure learning
- Similar patient → benefits from patient learning
- Same adjuvants → benefits from adjuvant learning
- **Result:** Recommends ~6.3mg instead of 7mg ✅

## Conclusion

✅ **Current implementation CORRECTLY matches the user's learning philosophy**

The system learns from three intersecting dimensions exactly as described:
- Procedures learn their MME requirements
- Patient types learn their dosing patterns
- Adjuvants learn their effectiveness (globally)

All three dimensions are learned simultaneously and independently, allowing the system to make increasingly accurate predictions as it accumulates experience across all three axes.

## Issues Found

### ❌ Weight Bucketing Too Coarse

**Current:** 10kg buckets (50-60, 60-70, 70-80, etc.)
**Requested:**
- 2.5kg increments until 40kg
- 5kg increments after 40kg

**Impact:** Pediatric and very low weight patients (anorexia, cachexia) need finer granularity

**Fix needed:** Update bucketing logic in `learning_engine.py` and `calculation_engine.py`
