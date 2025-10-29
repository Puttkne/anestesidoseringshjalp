# Converting to Percentage-Based Adjuvants

## Current Problem

**Fixed MME reductions don't scale physiologically:**

```
Current system:
- Small procedure (8 MME) + Parecoxib (-11 MME) = -3 MME (goes negative!)
- Large procedure (25 MME) + Parecoxib (-11 MME) = 14 MME (only 44% reduction)

Same drug, inconsistent relative effect!
```

## Solution: Percentage-Based Reductions

Convert `potency_mme` to `potency_percent`:

### Conversion Strategy

**Step 1: Calculate baseline percentages**
```
Reference procedure: 15 MME (typical lap cholecystectomy)

Parecoxib: 11 MME / 15 MME = 73% → potency_percent: 0.40 (40% reduction)
Catapressan: 10 MME / 15 MME = 67% → potency_percent: 0.35 (35% reduction)
Ketamine small: 5 MME / 15 MME = 33% → potency_percent: 0.20 (20% reduction)
Ketamine large: 10 MME / 15 MME = 67% → potency_percent: 0.35 (35% reduction)
Lidocaine infusion: 10 MME / 15 MME = 67% → potency_percent: 0.35 (35% reduction)
Betapred 8mg: 4 MME / 15 MME = 27% → potency_percent: 0.15 (15% reduction)
Infiltration: 8 MME / 15 MME = 53% → potency_percent: 0.30 (30% reduction)
Sevoflurane: 2 MME / 15 MME = 13% → potency_percent: 0.08 (8% reduction)
```

**Step 2: New calculation**
```python
# OLD
adjuvant_reduction = drug['potency_mme'] * pain_match_penalty

# NEW
base_mme = procedure['baseMME'] * all_patient_factors
adjuvant_reduction = base_mme * drug['potency_percent'] * pain_match_penalty
```

### Examples with Percentage System

**Small procedure (Minor arthroscopy, 8 MME):**
```
Base: 8 MME
Parecoxib (40%): 8 × 0.40 × 0.95 = -3.0 MME
Result: 5.0 MME ✓ (reasonable)
```

**Large procedure (Total knee, 25 MME):**
```
Base: 25 MME
Parecoxib (40%): 25 × 0.40 × 0.95 = -9.5 MME
Result: 15.5 MME ✓ (proportional)
```

**Very large procedure (Open thoracotomy, 30 MME):**
```
Base: 30 MME
Parecoxib (40%): 30 × 0.40 × 0.65 = -7.8 MME (poor match)
Ketamine large (35%): 30 × 0.35 × 0.96 = -10.1 MME (good match)
Result: 12.1 MME ✓ (scales properly)
```

## Proposed Adjuvant Percentages

| Adjuvant | Current MME | New Percentage | Physiological Rationale |
|----------|-------------|----------------|------------------------|
| **NSAIDs** |
| Ibuprofen 400mg | 8 | 30% | Moderate opioid-sparing |
| Ketorolac 30mg | 15 | 45% | Strong opioid-sparing |
| Parecoxib 40mg | 11 | 40% | Strong opioid-sparing |
| **Alpha-2 Agonists** |
| Catapressan 75mcg | 10 | 35% | Moderate-strong opioid-sparing |
| **NMDA Antagonists** |
| Ketamine small bolus | 5 | 20% | Mild opioid-sparing |
| Ketamine large bolus | 10 | 35% | Moderate opioid-sparing |
| Ketamine small infusion | 8 | 30% | Moderate opioid-sparing |
| Ketamine large infusion | 15 | 45% | Strong opioid-sparing |
| **Sodium Channel Blockers** |
| Lidocaine bolus | 5 | 20% | Mild opioid-sparing |
| Lidocaine infusion | 10 | 35% | Moderate opioid-sparing |
| **Corticosteroids** |
| Betapred 4mg | 2 | 10% | Mild anti-inflammatory |
| Betapred 8mg | 4 | 15% | Moderate anti-inflammatory |
| **Neuroleptics** |
| Droperidol | 8 | 30% | Moderate opioid-sparing |
| **Volatile Anesthetics** |
| Sevoflurane | 2 | 8% | Mild residual effect |
| **Regional** |
| Infiltration | 8 | 30% | Moderate local effect |

## Learning System Changes

### Current: Only learns for specific subgroups
```python
if age >= 65:
    learn_age_factor()

if asa in ['ASA 3', 'ASA 4', 'ASA 5']:
    learn_asa_factor()

if renal_impairment (GFR <35):
    learn_renal_factor()
```

### New: Learn for ALL patient states

**Age - All groups:**
```python
Age <18:     Learn pediatric factor
Age 18-39:   Learn young adult factor (baseline)
Age 40-64:   Learn middle-aged factor
Age 65-79:   Learn elderly factor
Age 80+:     Learn very elderly factor
```

**ASA - All classes:**
```python
ASA 1:  Learn healthy patient factor
ASA 2:  Learn mild disease factor
ASA 3:  Learn severe disease factor
ASA 4:  Learn life-threatening disease factor
ASA 5:  Learn moribund patient factor
```

**Renal function - All levels:**
```python
GFR >90:    Learn normal renal factor
GFR 60-90:  Learn mildly reduced factor
GFR 30-60:  Learn moderately reduced factor
GFR <30:    Learn severely reduced factor
```

**Opioid tolerance:**
```python
Opioid-naive:    Learn baseline tolerance
Opioid-tolerant: Learn increased tolerance (currently 1.5× default)
```

## Implementation Steps

### 1. Update config.py
```python
# Change all potency_mme to potency_percent
'parecoxib_40mg': {
    'potency_percent': 0.40,  # Was: potency_mme: 11
    ...
}
```

### 2. Update calculation_engine.py
```python
# OLD
adjuvant_reduction = learned_potency * penalty

# NEW
base_after_patient_factors = base_mme * age_factor * sex_factor * ...
adjuvant_reduction = base_after_patient_factors * learned_potency_percent * penalty
```

### 3. Update learning_engine.py
```python
# Learn for ALL ages
age_group = get_age_group(age)  # <18, 18-39, 40-64, 65-79, 80+
db.update_age_factor(age_group, default, adjustment)

# Learn for ALL ASA
db.update_asa_factor(asa_class, default, adjustment)

# Learn for ALL renal states
renal_group = get_renal_group(gfr)  # >90, 60-90, 30-60, <30
db.update_renal_factor(renal_group, default, adjustment)

# Learn for opioid tolerance
if opioid_tolerant:
    db.update_opioid_tolerance_factor(default, adjustment)
```

### 4. Update database.py
```python
# Add renal_group column instead of binary yes/no
# Add opioid_tolerance table
# Expand age_group to include all ranges
```

### 5. Migration v5
```python
def migrate_to_v5():
    """
    Convert adjuvant potency from MME to percentage.
    Expand patient factor learning to all states.
    """
    # Convert existing potency values
    # Add new patient factor buckets
```

## Benefits

### Percentage-Based Adjuvants
✅ **Physiologically consistent** - same drug has same relative effect
✅ **Scales automatically** - works for all procedure sizes
✅ **Easier to interpret** - "parecoxib reduces opioid need by 40%"
✅ **Better learning** - percentage changes more stable than MME

### Universal Patient Learning
✅ **More granular** - learns from all patient types
✅ **Better predictions** - "healthy 30yo males need X, sick 70yo females need Y"
✅ **Captures age effects** - learns that 40-64 may differ from 18-39
✅ **Renal spectrum** - learns across GFR ranges, not just <35
✅ **Tolerance patterns** - learns how much more tolerant patients actually need

## Next Steps

1. Create percentage conversion table
2. Update LÄKEMEDELS_DATA in config.py
3. Update calculation_engine.py adjuvant logic
4. Expand patient factor learning conditions
5. Create migration v5
6. Test with various procedure sizes
7. Verify learning works for all patient groups
