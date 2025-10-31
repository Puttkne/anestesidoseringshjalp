# Pain Classification System - Implementation Summary

## Overview
This document describes the pain classification system implemented in the anesthesia dosing application, based on research distinguishing visceral vs somatic pain pathways.

## Pain Type Scale
All surgical procedures are classified on a 0-10 scale:
- **0 = Pure Visceral Pain** (deep organ pain, poorly localized, mediated by sympathetic/parasympathetic nerves)
- **10 = Pure Somatic Pain** (superficial/musculoskeletal, well-localized, mediated by somatic nerves)
- **5 = Mixed Pain** (combination of both pathways)

## Medication Classification
Each adjuvant medication is characterized by three dimensions:

### 1. Pain Selectivity (0-10)
- **0 = Visceral selective** (works best for organ/deep pain)
- **10 = Somatic selective** (works best for superficial/musculoskeletal pain)
- **5 = Non-selective** (works equally for both pain types)

### 2. Analgesic Potency (0-10)
- Measures the overall pain-relieving effectiveness
- 0 = minimal effect, 10 = maximum effect

### 3. Systemic Impact (0-10)
- Measures side effects, particularly postoperative fatigue/sedation
- 0 = minimal CNS effects, 10 = maximum sedation/systemic effects

## Pain Type Mismatch Penalty
When an adjuvant's selectivity doesn't match the procedure's pain type, effectiveness is reduced:

```python
mismatch = abs(procedure_pain_score - adjuvant_selectivity)
- Mismatch > 6: 50% reduced effect
- Mismatch > 4: 70% effect (30% reduction)
- Mismatch > 2: 85% effect (15% reduction)
- Mismatch ≤ 2: 100% effect (no penalty)
```

## Example Medications

### Somatic-Selective (High Score)
- **Ibuprofen**: Selectivity 9, Potency 5, Systemic Impact 0
  - Best for: Orthopedic surgery, superficial procedures
  - Poor for: Laparoscopic surgery, visceral procedures

### Visceral-Selective (Low Score)
- **Clonidine**: Selectivity 2, Potency 4, Systemic Impact 6
  - Best for: Abdominal surgery, urological procedures
  - Poor for: Joint replacement, bone procedures

### Non-Selective (Mid Score)
- **Ketamine**: Selectivity 5, Potency 7, Systemic Impact 8
  - Works for both pain types
  - Higher systemic impact (sedation/fatigue)

## Learning Mechanism

### Rule-Based Engine
1. Calculates pain type mismatch for each adjuvant
2. Applies effectiveness penalty to dose reduction
3. Learns from outcomes to adjust both:
   - Overall calibration factor (per composite key)
   - Adjuvant-specific effectiveness (per pain type)

### XGBoost Engine
Features added to training:
- `painTypeScore`: Procedure's pain type (0-10)
- `avgAdjuvantSelectivity`: Average selectivity of used adjuvants
- `painTypeMismatch`: Absolute difference between procedure and adjuvants

### Adaptive Learning
When a case is saved with postoperative data:
1. **Calibration factor** adjusts overall dose for that configuration
2. **Adjuvant effectiveness** adjusts per medication per pain type
3. Both systems learn independently and cumulatively

Example: If NSAID proves less effective for a visceral procedure (TUR-P):
- System reduces NSAID multiplier from 0.8 → 0.85 (less dose reduction)
- Future visceral cases with NSAID get smaller opioid-sparing benefit
- Somatic procedures (hip replacement) keep higher NSAID effectiveness

## Database Schema

### New Table: `adjuvant_effectiveness`
```sql
CREATE TABLE adjuvant_effectiveness (
    user_id INTEGER,
    adjuvant_name TEXT,
    pain_type_score REAL,          -- Rounded 0-10
    base_multiplier REAL,          -- Original (e.g., 0.8 for NSAID)
    learned_multiplier REAL,       -- Adapted value (0.2 - 2.0)
    pain_selectivity REAL,         -- Medication property
    potency REAL,                  -- Medication property
    systemic_impact REAL,          -- Medication property
    update_count INTEGER,          -- Number of learning events
    last_updated TIMESTAMP,
    UNIQUE(user_id, adjuvant_name, pain_type_score)
)
```

## Implementation Files

### `pain_classification.py`
- `PROCEDURES_WITH_PAIN_SCORES`: 84 procedures with pain type scores
- `MEDICATIONS`: 14 adjuvants with 3D classification
- `calculate_mismatch_penalty()`: Computes effectiveness penalty

### `database.py`
- `get_adjuvant_multiplier()`: Retrieve learned effectiveness
- `update_adjuvant_effectiveness()`: Update after outcome
- `get_all_adjuvant_effectiveness()`: Analytics/display

### `oxydoseks.py`
- **Rule engine**: Applies pain type matching in dose calculation
- **XGBoost**: Adds pain features to training
- **Learning**: Updates both calibration and adjuvant effectiveness
- **UI**: Displays pain type info (🔵 Visceral / 🔴 Somatic / 🟣 Mixed)

## Clinical Benefits

1. **Precision**: Better adjuvant selection based on pain mechanism
2. **Personalization**: System learns which adjuvants work for each user's cases
3. **Optimization**: Balances analgesia vs systemic effects
4. **Transparency**: Users see pain type and can understand recommendations
5. **Continuous Improvement**: Both engines adapt based on real outcomes

## Future Enhancements
- UI to manually adjust medication properties
- Visualization of adjuvant effectiveness across pain types
- Recommendations: "Consider X adjuvant for this visceral procedure"
- Export effectiveness learning data for research
