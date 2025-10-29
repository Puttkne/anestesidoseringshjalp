# Complete Rules-Based Learning System Description

## Overview

This system provides oxycodone dose recommendations for postoperative pain management. It starts with evidence-based defaults (rules) and continuously learns from actual clinical outcomes to refine its recommendations. The learning is **global** - all users contribute to and benefit from collective knowledge.

## How the System Works

### Phase 1: Initial Recommendation (Rules-Based)

When you have **few or no cases** for a procedure, the system uses evidence-based rules:

#### Step 1: Base Opioid Requirement (Procedure)

Each procedure has a default baseline MME (Morphine Milligram Equivalents) requirement:

**Examples:**
```
Lap cholecystectomy:        15 MME (default)
Lap appendectomy:           12 MME (default)
Open hernia repair:         18 MME (default)
Total knee replacement:     25 MME (default)
Minor arthroscopy:          8 MME (default)
```

**Conversion to oxycodone:**
- 1 mg oxycodone = ~1.5 MME
- 15 MME ≈ 10mg oxycodone

#### Step 2: Patient Factors Adjustment

**Age Factor:**
```
Age <18:        1.3× (children need more per kg)
Age 18-39:      1.0× (baseline)
Age 40-64:      1.0× (baseline)
Age 65-79:      0.8× (elderly need 20% less)
Age 80+:        0.6× (very elderly need 40% less)
```

**Sex Factor:**
```
Male:           1.0× (baseline)
Female:         1.0× (baseline, learns differences)
```

**Body Weight/Composition (Applied via ABW):**
```
Weight adjustment uses Adjusted Body Weight (ABW):
- Normal weight (BMI 18.5-25):     ABW ≈ actual weight
- Overweight (BMI 25-30):          ABW = IBW + 0.4 × (weight - IBW)
- Obese (BMI 30+):                 ABW = IBW + 0.4 × (weight - IBW)
- Underweight (BMI <18.5):         ABW ≈ actual weight

Final dose scaled: dose × (ABW / 75kg)
```

**ASA Physical Status:**
```
ASA 1 (healthy):               1.0× (baseline)
ASA 2 (mild disease):          1.0× (baseline)
ASA 3 (severe disease):        1.0× (learns if needs adjustment)
ASA 4 (life-threatening):      1.0× (learns if needs adjustment)
ASA 5 (moribund):              1.0× (learns if needs adjustment)
```

**Renal Impairment:**
```
GFR >60:        1.0× (normal)
GFR <35:        0.75× (reduce by 25%)
```

**Opioid Tolerance:**
```
Opioid-naive:   1.0× (baseline)
Tolerant:       1.5× (need 50% more)
```

**Low Pain Threshold:**
```
Normal:         1.0× (baseline)
Low threshold:  1.2× (need 20% more)
```

#### Step 3: Adjuvant Reductions

Each adjuvant reduces the opioid requirement based on its **potency** (how much MME it replaces) and **pain type selectivity** (how well it matches the procedure's pain profile).

##### 3D Pain Type System

Procedures have pain profiles on 3 dimensions (0-10 scale):
- **Somatic pain** (skin, muscle, bone) - e.g., orthopedic surgery
- **Visceral pain** (organs) - e.g., abdominal surgery
- **Neuropathic pain** (nerve injury) - e.g., thoracotomy

**Procedure Pain Profile Examples:**
```
Lap cholecystectomy:     Somatic=5, Visceral=7, Neuropathic=2
Lap appendectomy:        Somatic=4, Visceral=8, Neuropathic=2
Total knee replacement:  Somatic=9, Visceral=1, Neuropathic=3
Open thoracotomy:        Somatic=6, Visceral=4, Neuropathic=8
```

##### Adjuvant Pain Profiles & Reductions

Each adjuvant has its own 3D pain profile showing what type of pain it treats best:

**NSAIDs (e.g., Parecoxib 40mg):**
```
Pain profile:     Somatic=9, Visceral=2, Neuropathic=1
Base potency:     11 MME reduction
Best for:         Orthopedic, somatic pain
Poor for:         Visceral, neuropathic pain

Example - Knee replacement (Somatic=9):
  Mismatch penalty: 0.95 (excellent match)
  Reduction: 11 × 0.95 = 10.5 MME

Example - Lap cholecystectomy (Visceral=7):
  Mismatch penalty: 0.65 (poor match)
  Reduction: 11 × 0.65 = 7.2 MME
```

**Catapressan (Alpha-2 Agonist):**
```
Pain profile:     Somatic=3, Visceral=7, Neuropathic=6
Base potency:     10 MME reduction
Best for:         Visceral, laparoscopic surgery
Good for:         Neuropathic pain

Example - Lap cholecystectomy (Visceral=7):
  Mismatch penalty: 0.98 (excellent match)
  Reduction: 10 × 0.98 = 9.8 MME
```

**Ketamine (Low dose 0.05-0.1 mg/kg):**
```
Pain profile:     Somatic=4, Visceral=5, Neuropathic=9
Base potency:     5 MME reduction
Best for:         Neuropathic pain, thoracic surgery
Moderate for:     Other pain types

Example - Thoracotomy (Neuropathic=8):
  Mismatch penalty: 0.96 (excellent match)
  Reduction: 5 × 0.96 = 4.8 MME
```

**Ketamine (High dose 0.5-1.0 mg/kg):**
```
Pain profile:     Somatic=4, Visceral=5, Neuropathic=9
Base potency:     10 MME reduction
```

**Lidocaine Infusion:**
```
Pain profile:     Somatic=6, Visceral=7, Neuropathic=7
Base potency:     10 MME reduction
Best for:         Balanced pain types, abdominal surgery
```

**Betamethasone 8mg:**
```
Pain profile:     Somatic=5, Visceral=5, Neuropathic=3
Base potency:     4 MME reduction
Moderate for:     All pain types
```

**Paracetamol 1g:**
```
Assumed in all cases (not explicitly added)
Baseline analgesic effect
```

**Local Infiltration:**
```
Pain profile:     Somatic=10, Visceral=1, Neuropathic=8
Base potency:     8 MME reduction
Excellent for:    Somatic, incisional pain
Poor for:         Visceral pain
```

**Sevoflurane (vs TIVA):**
```
Pain profile:     Somatic=5, Visceral=5, Neuropathic=2
Base potency:     2 MME reduction
Mild analgesic:   Modest benefit
```

#### Step 4: Fentanyl Offset

If fentanyl was given intraoperatively:
```
Default assumption: 25% remains at end of surgery
Reduction: fentanyl_dose × 0.01 × 1.5 × 0.25

Example: 350mcg fentanyl
  = 350 × 0.01 × 1.5 × 0.25
  = 1.3 MME still active
  Reduce oxycodone recommendation by 1.3 MME
```

#### Step 5: Final Calculation Example

**Patient:** 70yo male, 75kg, ASA 2, lap cholecystectomy
**Adjuvants:** Parecoxib 40mg, Catapressan 75mcg, 350mcg fentanyl
**Operating time:** 90 minutes

**Calculation:**
```
1. Base procedure MME:           15.0 MME
2. Age factor (70yo):            × 0.8 = 12.0 MME
3. Sex factor (male):            × 1.0 = 12.0 MME
4. ASA factor (ASA 2):           × 1.0 = 12.0 MME
5. Weight (75kg):                × (75/75) = 12.0 MME

6. Adjuvant reductions:
   - Parecoxib (visceral match):  -7.2 MME
   - Catapressan (excellent):     -9.8 MME
   Total reduction:               -17.0 MME

7. After adjuvants:              12.0 - 17.0 = -5.0 MME
   Safety minimum (50% of base): max(-5.0, 6.0) = 6.0 MME

8. Fentanyl offset:              -1.3 MME = 4.7 MME

9. Weight scaling (ABW/75):       4.7 × (75/75) = 4.7 MME

10. Convert to oxycodone:         4.7 / 1.5 ≈ 3.1mg

Final recommendation: 3-4mg oxycodone
```

### Phase 2: Learning from Outcomes

When you save a case with outcome data, the system learns:

#### What Gets Recorded

```
Given dose:           5.2mg (what you actually gave)
VAS score:           2 (pain 0-10, first hour PACU)
UVA/rescue dose:     0mg (additional opioid needed)
Respiratory status:  Normal / Desaturation / Apnea
Severe fatigue:      Yes/No
```

#### Back-Calculation of Actual Requirement

The system calculates what dose was **actually needed**:

```python
# If outcome was perfect (VAS ≤3, no rescue)
actual_requirement = given_dose

# If patient needed rescue (UVA dose given)
actual_requirement = given_dose + uva_dose

# If patient had pain (VAS >3)
estimated_deficiency = (VAS - 3) × 0.5  # Rough estimate
actual_requirement = given_dose + estimated_deficiency

# If patient was over-sedated
actual_requirement = given_dose × 0.8  # They needed less
```

**Example - Perfect Outcome:**
```
Recommended: 7.0mg
Actually gave: 5.2mg (clinical judgment)
Outcome: VAS=2, UVA=0mg (perfect)

Actual requirement: 5.2mg
Prediction error: 5.2 - 7.0 = -1.8mg (over-predicted by 26%)
```

#### Learning Distribution

The system distributes learning across all relevant dimensions:

**1. Procedure Learning (30% of error):**
```
If prediction error = -1.8mg
Procedure adjustment = -1.8 × 0.30 × learning_rate = -0.18 MME

Lap cholecystectomy baseMME: 15.0 → 14.82

Next similar case will start lower!
```

**2. Patient Factor Learning (40% of error):**

**Age learning:**
```
If patient was 70yo (elderly):
Age factor adjustment = -1.8 × 0.03 × learning_rate = -0.03

Age factor (65-79): 0.80 → 0.77

Next 70yo patient needs less!
```

**Sex learning:**
```
If patient was female:
Sex adjustment = -1.8 × 0.02 × learning_rate = -0.02

Female factor: 1.00 → 0.98

Next female patient needs slightly less!
```

**Body composition learning (4D):**
```
Weight (70kg bucket):
  Weight factor: 1.00 → 0.98

IBW ratio (1.0×):
  IBW ratio factor: 1.00 → 0.98

BMI (normal):
  BMI factor: 1.00 → 0.98

Next patient with similar body composition needs less!
```

**3. Adjuvant Learning (30% of error - GLOBAL):**
```
If adjuvants were more effective than expected:

Parecoxib potency: 11.0 → 11.2 MME (learned it works better)
Catapressan visceral selectivity: 7.0 → 7.3 (better visceral match)

ALL USERS benefit from this learning immediately!
```

#### Adaptive Learning Rates

Learning is aggressive early, conservative later:

```
Case 1-2:      30% learning rate (learn fast)
Case 3-9:      18% learning rate (moderate)
Case 10-19:    12% learning rate (refined)
Case 20+:      6% + decay (stabilize)
```

**Why?**
- Early cases: Little data, big adjustments needed
- Later cases: Established patterns, small refinements

#### Safety Limits

All learning is clamped to safe ranges:

```
Procedure baseMME:    50-200% of default
Age factors:          0.4-1.5×
Sex factors:          0.85-1.15×
Body composition:     0.6-1.4×
ASA factors:          0.5-1.5×
Renal factor:         0.6-1.0×
Opioid tolerance:     1.0-2.5×
Pain threshold:       1.0-1.8×
Adjuvant potency:     50-200% of default
Adjuvant selectivity: 0-10 (pain type scores)
```

**Maximum change per case:**
- Procedure baseMME: ±25%
- Patient factors: ±5%
- Adjuvants: ±10%

### Phase 3: Mature Learning (Many Cases)

After 50-100 cases, the system becomes highly accurate:

**What has been learned:**
```
Procedures:
  Lap cholecystectomy: 13.2 MME (was 15.0)
  Learned from 87 cases

Age (elderly 65-79):
  Factor: 0.74× (was 0.80×)
  Learned from 34 cases

Sex (female):
  Factor: 0.92× (was 1.00×)
  Learned that females need ~8% less

Body composition (70kg, normal BMI):
  Weight: 0.96×
  IBW ratio: 0.98×
  BMI: 0.99×
  Combined effect: ~7% reduction

Adjuvants (GLOBAL - 2,500 cases from all users):
  Parecoxib 40mg: 11.8 MME (was 11.0)
  Catapressan: Visceral selectivity 7.6 (was 7.0)
  Ketamine high dose: 12.3 MME (was 10.0)

New recommendation for same patient:
  Base: 13.2 × 0.74 × 0.92 × 0.96 = 8.5 MME
  Adjuvants: -18.2 MME (learned effectiveness)
  Safety min: 6.6 MME
  Final: ~4.5mg oxycodone (vs initial 7mg!)
```

## Summary Table: Complete Calculation

| Step | Factor | Initial (Rules) | After Learning | Effect |
|------|--------|----------------|----------------|--------|
| **Procedure** | Lap chole | 15.0 MME | 13.2 MME | -12% |
| **Age** | 70yo | ×0.80 | ×0.74 | -6% |
| **Sex** | Female | ×1.00 | ×0.92 | -8% |
| **Weight** | 70kg | ×1.00 | ×0.96 | -4% |
| **IBW ratio** | 1.0× | ×1.00 | ×0.98 | -2% |
| **BMI** | 23 | ×1.00 | ×0.99 | -1% |
| **ASA** | ASA 2 | ×1.00 | ×1.00 | 0% |
| **Renal** | Normal | ×1.00 | ×1.00 | 0% |
| **Tolerance** | Naive | ×1.00 | ×1.00 | 0% |
| **Pain threshold** | Normal | ×1.00 | ×1.00 | 0% |
| **Subtotal** | | **12.0 MME** | **8.5 MME** | **-29%** |
| **Parecoxib** | 40mg | -7.2 MME | -8.1 MME | Better match |
| **Catapressan** | 75mcg | -9.8 MME | -10.1 MME | Better match |
| **After adjuvants** | | **-5.0 MME** | **-9.7 MME** | Over-reduction |
| **Safety floor** | 50% base | **6.0 MME** | **4.25 MME** | Protection |
| **Fentanyl offset** | 350mcg | -1.3 MME | -1.3 MME | Same |
| **Final MME** | | **4.7 MME** | **3.0 MME** | -36% from rules |
| **Oxycodone** | | **~3mg** | **~2mg** | Refined |

## Key Insights

### Early (Few Cases)
- Uses evidence-based rules
- Conservative recommendations
- Learns aggressively from each case

### Middle (10-50 Cases)
- Mix of rules and learning
- Recommendations refining
- Moderate learning rate

### Mature (50+ Cases)
- Highly personalized
- Accurate predictions
- Conservative learning (stabilized)

### Global Benefits
- **Adjuvants learned globally** - 2,500 cases from all users
- **New users get instant knowledge** - no cold start
- **Best practices propagate** - excellent outcomes spread to everyone
- **Robust against outliers** - weighted averaging dilutes bad data

## The System Never Forgets Rules

Even with extensive learning, the system maintains safety through:
- Default values as fallback
- Safety limits on all learned factors
- Minimum dose floors (50% of calculated)
- Maximum dose warnings (>10mg triggers review)

**This combination of evidence-based rules + continuous learning creates a system that is both safe (rules) and adaptive (learning).**
