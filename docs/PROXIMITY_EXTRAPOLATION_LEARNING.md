# Proximity and Extrapolation Learning

## The Challenge

**Question:** What if we've never seen a patient with these exact stats before?

**Example:** 67-year-old female, 72.3kg, BMI 28.4, undergoing laparoscopic appendectomy with parecoxib + catapressan

## The Solution: Multi-Dimensional Bucketing

The system uses **proximity matching through bucketing** - patients with similar characteristics share learned knowledge. Even if you've never seen this exact patient, the system extrapolates from nearby experience.

## How Proximity Learning Works

### 1. **Procedure Learning** - Exact Match

```python
procedure_id = 'lap_appendectomy'
learned_baseMME = db.get_procedure_learning(user_id, 'lap_appendectomy')
# Uses learned baseMME from ALL your lap appendectomy cases
```

**Proximity:** Exact procedure match
**Extrapolation:** Aggregates learning from all patients with this procedure

### 2. **Patient Factor Learning** - Bucketed Proximity

#### Age (Continuous bucketing):
```python
age = 67
# Learns from all patients 65-79 years old
if age >= 65 and age < 80:
    age_factor = learned_factor_for_elderly
```

#### Weight (Fine-grained bucketing):
```python
weight = 72.3kg
weight_bucket = get_weight_bucket(72.3)  # Returns 70.0
# Patient benefits from all learning on 70-75kg patients
# Bucket size: 2.5kg until 40kg, then 5kg
```

**Finer granularity for edge cases:**
- Pediatric: 15.3kg → bucket 15.0 (learned from 15.0-17.5kg)
- Low weight: 38.7kg → bucket 37.5 (learned from 37.5-40.0kg)
- Normal: 72.3kg → bucket 70.0 (learned from 70-75kg)
- Obese: 127.8kg → bucket 125.0 (learned from 125-130kg)

#### IBW Ratio (0.1 increments):
```python
weight = 72.3kg
ibw = 65kg
ratio = 72.3 / 65 = 1.11
ratio_bucket = get_ibw_ratio_bucket(1.11)  # Returns 1.1

# Patient benefits from all patients with 1.05-1.15 IBW ratio
# This captures "10% over ideal weight" category
```

#### BMI (7 categories):
```python
bmi = 28.4
bmi_bucket = get_bmi_bucket(28.4)  # Returns 27 (Overweight category)

# Patient benefits from all overweight patients (BMI 25-30)
```

#### Sex (Binary):
```python
sex = 'Kvinna'
# Benefits from all female patient learning
```

### 3. **Adjuvant Learning** - GLOBAL Proximity

```python
adjuvant = 'Parecoxib 40mg'
# Benefits from ALL users' experience with parecoxib across ALL procedures and ALL patients
# This is the most powerful extrapolation!
```

## Practical Example

### Scenario: Never-Before-Seen Patient

**Patient:**
- 67yo female, 72.3kg, 165cm, BMI 26.6
- Lap appendectomy
- Parecoxib 40mg + Catapressan 75mcg

**Has the system seen this exact combination?** Probably not!

**But the system extrapolates from:**

#### Procedure Learning:
- ✓ Have done 15 lap appendectomies
- → Learned baseMME = 13.2 (vs default 15)

#### Age Learning:
- ✓ Have treated 8 patients aged 65-79
- → Learned elderly_factor = 0.82 (vs default 0.80)

#### Weight Learning (4D):
- ✓ Have treated 3 patients in 70-75kg bucket
  → weight_factor = 0.98
- ✓ Have treated 5 patients with IBW ratio 1.0-1.2×
  → ibw_ratio_factor = 1.02
- ✓ Have treated 4 patients with BMI 25-30
  → bmi_factor = 1.01
- (No ABW learning - not overweight enough)

#### Sex Learning:
- ✓ Have treated 22 female patients
- → female_factor = 0.95

#### Adjuvant Learning (GLOBAL):
- ✓ ALL USERS have used parecoxib 40mg in 847 cases
  → potency = 11.3 MME (vs default 11)
  → selectivity_visceral = 2.8 (vs default 2)
- ✓ ALL USERS have used catapressan 75mcg in 1,203 cases
  → potency = 10.2 MME (vs default 10)
  → selectivity_visceral = 7.3 (vs default 7)

### Result: Good Recommendation from Extrapolation

**Calculation:**
```python
mme = 13.2  # Learned procedure baseMME
mme *= 0.82  # Age factor (elderly)
mme *= 0.95  # Sex factor (female)
mme *= 0.98  # Weight factor (70kg bucket)
mme *= 1.02  # IBW ratio factor (1.1× bucket)
mme *= 1.01  # BMI factor (overweight bucket)
# = 13.2 × 0.82 × 0.95 × 0.98 × 1.02 × 1.01 = 10.5 MME

# Adjuvants (3D pain matching)
parecoxib_reduction = 11.3 × visceral_penalty(2.8 vs 7) = 6.8 MME
catapressan_reduction = 10.2 × visceral_penalty(7.3 vs 7) = 10.1 MME
mme -= (6.8 + 10.1) = 10.5 - 16.9 = negative!

# Safety limit (50% of baseMME)
mme = max(10.5 * 0.5, mme) = 5.25 MME

# Weight adjustment (ABW)
abw = 65 + 0.4 × (72.3 - 65) = 67.9kg
mme *= (67.9 / 75) = 5.25 × 0.91 = 4.8 MME

# Final: 5.0mg oxycodone
```

**Confidence:** HIGH - Even though we've never seen this exact patient, we have:
- Direct experience with this procedure (15 cases)
- Direct experience with elderly patients (8 cases)
- Direct experience with female patients (22 cases)
- Direct experience with similar weight/BMI patients (multiple buckets)
- **Global experience with these adjuvants (2,050 cases from all users!)**

## Interpolation vs Extrapolation

### Interpolation (Safer)
**Definition:** Estimating within known data ranges

**Example:**
- Have treated 70kg and 80kg patients
- New patient is 75kg
- **Interpolation:** Use 70kg bucket (within known range)
- **Confidence:** HIGH

### Extrapolation (Less certain, but necessary)
**Definition:** Estimating outside known data ranges

**Example:**
- Have treated patients with BMI 25-35
- New patient has BMI 42 (morbidly obese)
- **Extrapolation:** Use BMI 42 bucket (outside direct experience)
- **Initial factor:** 1.0 (default, no learning yet)
- **Confidence:** MEDIUM (no data yet, but system will learn)

**Safety:** System defaults to 1.0× (no adjustment) for buckets without data, then learns from outcomes

## Bucketing Strategy

### Why Bucketing Works

1. **Reduces Sparsity:** Instead of needing 1000s of unique patient combinations, we need ~50 buckets × 10 procedures = 500 learning points

2. **Enables Generalization:** 72.3kg patient benefits from 70kg, 75kg, and nearby weight learning

3. **Balances Precision vs Data Requirements:**
   - Too fine (0.1kg buckets): Requires millions of patients
   - Too coarse (50kg buckets): Loses clinical nuance
   - **Our approach:** Finer for critical ranges (pediatric), coarser for normal ranges

### Bucket Sizes

| Dimension | Bucket Size | Rationale |
|-----------|------------|-----------|
| **Weight <40kg** | 2.5kg | Pediatric patients need precise dosing |
| **Weight ≥40kg** | 5kg | Adults tolerate wider variance |
| **IBW Ratio** | 0.1 (10%) | Captures meaningful body composition differences |
| **ABW Ratio** | 0.1 (10%) | Only for overweight patients |
| **BMI** | 7 categories | Clinical BMI categories |
| **Age <65** | No learning | Normal dosing |
| **Age 65-79** | 1 bucket | Elderly |
| **Age 80+** | 1 bucket | Very elderly |

## Learning Across Dimensions

The system learns **independently** across all dimensions, then **multiplies** factors:

```python
dose = baseMME  # Procedure learning
dose *= age_factor  # Patient factor learning
dose *= sex_factor
dose *= weight_factor
dose *= ibw_ratio_factor
dose *= bmi_factor
# ... more patient factors

dose -= adjuvant_reductions  # Adjuvant learning (GLOBAL)
```

**This means:**
- A 67yo female with BMI 26.6 at 72kg benefits from:
  - Age learning (all elderly patients)
  - Sex learning (all female patients)
  - Weight learning (all 70-75kg patients)
  - BMI learning (all overweight patients)
  - IBW learning (all 1.1× ratio patients)

**Even if this exact combination has never been seen!**

## Confidence Tracking

The system tracks `num_observations` for each bucket:

```sql
SELECT num_observations FROM learning_body_composition
WHERE user_id=1 AND metric_type='weight' AND metric_value=70.0;
-- Result: 12 observations
```

**Future enhancement:** Could weight recommendations by confidence:
- High confidence (>10 observations): Full weight on learned factor
- Medium confidence (3-10 observations): Partial weight
- Low confidence (<3 observations): Lean toward default

## Summary

✅ **The system DOES use proximity and extrapolation**

**How:**
1. **Bucketing** groups similar patients together
2. **Independent dimensions** allow partial matches (same weight, different age)
3. **Global adjuvant learning** shares knowledge across all users
4. **Default factors (1.0×)** ensure safety when no data exists
5. **Multiplicative factors** combine evidence from all dimensions

**Result:** Even for never-before-seen patient combinations, the system provides good recommendations by extrapolating from nearby experience across multiple dimensions.

**Example confidence:**
- Exact match: Seen this patient 5 times → HIGH
- Close proximity: Seen 70kg females aged 65-79 → HIGH
- Partial match: Seen 72kg patients but not elderly → MEDIUM
- Extrapolation: Never seen BMI 42, default to 1.0× → LOW (learns quickly)
- Global adjuvants: 2,000+ cases worldwide → VERY HIGH
