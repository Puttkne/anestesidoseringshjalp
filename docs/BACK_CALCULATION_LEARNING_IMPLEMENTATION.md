# Back-Calculation Learning Implementation Plan

## Problem Statement

**Case A (Current Bug):**
- App recommends: 7mg oxycodone
- Clinician gives: 5.2mg (clinical judgment)
- Outcome: Perfect (VAS 0-2, no rescue, no side effects)
- **Current behavior:** NO LEARNING (adjustment=0 because outcome is perfect)
- **Required behavior:** Learn that for this patient+procedure+adjuvants, 5.2mg was sufficient, so future recommendations should be lower

## Solution: Back-Calculation from Actual Requirement

Instead of learning "increase/decrease based on outcome quality," we learn "what was the actual requirement?"

### Key Changes Needed

#### 1. Replace `_calculate_learning_adjustment_from_outcome()` with `_calculate_actual_requirement()`

**New function signature:**
```python
def _calculate_actual_requirement(outcome_data, recommended_dose, num_proc_cases):
    """
    Calculate the ACTUAL opioid requirement from case data.

    Returns:
        {
            'actual_requirement': float,  # What was actually needed (mg)
            'prediction_error': float,     # actual - recommended (negative = over-predicted)
            'outcome_quality': str,        # 'perfect', 'good', 'underdosed', 'overdosed'
            'learning_magnitude': float,   # How strongly to learn (0-1)
            'base_learning_rate': float    # Adaptive rate based on experience
        }
    """
```

**Logic:**
```python
given_total = givenDose + uvaDose

if VAS <= 3 and uvaDose == 0 and no side effects:
    # PERFECT - the dose given was exactly right
    actual_requirement = given_total
    # If given < recommended → we over-predicted

elif VAS > 4 or uvaDose > 0:
    # UNDERDOSED - estimate what should have been given
    vas_deficit = max(0, VAS - 3)
    additional_needed = (vas_deficit / 7) * given_total * 0.3
    additional_needed += uvaDose * 0.5
    actual_requirement = given_total + additional_needed

elif respiratory_issue or severe_fatigue:
    # OVERDOSED - should have given less
    actual_requirement = given_total * 0.85

prediction_error = actual_requirement - recommended_dose
```

#### 2. Update `_learn_procedure_requirements()`

**Current (BROKEN):**
```python
def _learn_procedure_requirements(..., adjustment, ...):
    if not procedure_id or adjustment == 0:
        return  # BUG: No learning on perfect outcomes!

    base_mme_adjustment = adjustment * default_base_mme * multiplier
```

**New (FIXED):**
```python
def _learn_procedure_requirements(..., requirement_data, ...):
    if not procedure_id:
        return

    actual_req = requirement_data['actual_requirement']
    recommended = requirement_data['recommended']
    prediction_error = requirement_data['prediction_error']

    # Back-calculate what baseMME adjustment would explain this error
    # prediction_error = (actual_baseMME - default_baseMME) * all_multipliers
    # Solve for actual_baseMME adjustment needed

    base_mme_adjustment = prediction_error * requirement_data['learning_magnitude'] * 0.1

    # Clamp adjustments to prevent over-correction
    base_mme_adjustment = max(-default_base_mme * 0.2, min(default_base_mme * 0.2, base_mme_adjustment))
```

#### 3. Update `handle_save_and_learn()`

**Current:**
```python
adjustment = _calculate_learning_adjustment_from_outcome(outcome_data, num_proc_cases)
_learn_procedure_requirements(user_id, adjustment, ...)
```

**New:**
```python
# Get the recommended dose from calculation
recommended_dose = st.session_state.current_calculation.get('finalDose', 0)

# Calculate actual requirement
requirement_data = _calculate_actual_requirement(outcome_data, recommended_dose, num_proc_cases)

# Learn from actual requirement
_learn_procedure_requirements(user_id, requirement_data, ...)
_learn_adjuvant_effectiveness(user_id, requirement_data, ...)
_learn_patient_factors(user_id, requirement_data, ...)  # NEW
```

#### 4. Create `_learn_patient_factors()` (NEW FUNCTION)

This learns that certain patient types (age, ASA, weight) need different doses:

```python
def _learn_patient_factors(user_id, requirement_data, current_inputs):
    """
    Learn patient-specific factors from actual requirements.

    E.g., if 72yo woman consistently needs less than predicted,
    increase the age factor for elderly patients.
    """
    actual_req = requirement_data['actual_requirement']
    recommended = requirement_data['recommended']

    if actual_req < recommended * 0.8:  # Significantly less needed
        # This patient type needs less
        # Update age_factor, asa_factor, etc.
        db.update_age_factor(user_id, current_inputs['age'], adjustment=-0.05)
        db.update_asa_factor(user_id, current_inputs['asa'], adjustment=-0.05)

    elif actual_req > recommended * 1.2:  # Significantly more needed
        # This patient type needs more
        db.update_age_factor(user_id, current_inputs['age'], adjustment=+0.05)
        db.update_asa_factor(user_id, current_inputs['asa'], adjustment=+0.05)
```

## Implementation Steps

1. ✅ Make adjuvant learning global (DONE)
2. ✅ Verify 3D pain types are correct (DONE - already implemented)
3. ⏳ Implement `_calculate_actual_requirement()`
4. ⏳ Update `_learn_procedure_requirements()` to use requirement_data
5. ⏳ Update `handle_save_and_learn()` to pass recommended_dose
6. ⏳ Implement `_learn_patient_factors()`
7. ⏳ Update `_learn_adjuvant_effectiveness()` to use requirement_data (optional refinement)
8. ⏳ Test with Case A scenario

## Expected Behavior After Fix

**Case A:**
- App recommends: 7mg
- You give: 5.2mg
- Outcome: Perfect
- **Learning:** actual_requirement = 5.2mg, prediction_error = -1.8mg (over-predicted by 26%)
- **Updates:**
  - Cholecystectomy baseMME reduced by ~10% for this user
  - Adjuvant effectiveness slightly increased (they worked better than expected)
  - Patient factors slightly adjusted (this patient type needs less)

**Case B (next time):**
- Same patient, same procedure, same adjuvants
- **Recommended dose: ~6.3mg** (down from 7mg, learned from Case A)

**Case C (appendectomy):**
- Uses SAME adjuvant learning from Case A
- Different procedure baseMME (appendectomy has its own)
- Result: Benefits from improved adjuvant effectiveness estimates

## Files to Modify

1. `callbacks.py` - Main learning logic
2. `database.py` - Add `update_age_factor()`, `update_asa_factor()` if not present
3. `tests/test_learning.py` - NEW: Test back-calculation logic

## Key Principle

**Learn from WHAT ACTUALLY HAPPENED, not from deviation from prediction.**

The actual requirement is determined by:
- `givenDose` (what you gave)
- `uvaDose` (rescue needed)
- `VAS` (pain level achieved)
- `Side effects` (if overdosed)

This tells us what the patient+procedure+adjuvants ACTUALLY needed. We then back-calculate what parameter adjustments would have predicted this correctly.
