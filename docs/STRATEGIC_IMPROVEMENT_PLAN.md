# Strategic Improvement Plan: Blueprint vs. Current Implementation

**Date**: 2025-10-18
**Current System**: v6 (Adjuvant % Learning + 3D Pain Learning)
**Reference**: Technical Blueprint for Personalized IV Oxycodone Dosing

---

## Executive Summary

After analyzing the comprehensive technical blueprint against our current implementation, I've identified **significant alignment** in core architecture but **critical opportunities** for enhancement. Our system has strong foundations but can evolve toward the blueprint's vision of a true "Learning Health System" with causal reasoning capabilities.

**Current State**: ✅ Solid Phase 1-3 implementation with global learning
**Blueprint Vision**: 🎯 Advanced hybrid PK/PD-ML system with causal inference
**Gap**: Methodology upgrade from simple back-calculation to rigorous pharmacometric modeling

---

## Part 1: Current Implementation Strengths

### ✅ What We Got Right

#### 1. **Global Learning Philosophy** ✓ ALIGNED
**Blueprint**: "All users contribute to and benefit from shared knowledge"
**Our Implementation**: All learning tables are global (no user_id), exactly as specified

#### 2. **3D Pain Matching** ✓ ALIGNED
**Blueprint**: "Pain type (somatic vs. visceral) can influence relative efficacy"
**Our Implementation**: Full 3D pain learning (somatic/visceral/neuropathic) in v6

#### 3. **Percentage-Based Adjuvants** ✓ ALIGNED
**Blueprint**: Adjuvants reduce by percentage (e.g., 15%) that scales with procedure size
**Our Implementation**: Exact match - percentage-based potency in v5

#### 4. **Hyperbolic Learning Decay** ✓ ALIGNED
**Blueprint**: Learning rate never reaches zero, continues indefinitely
**Our Implementation**: `0.30 / (1 + 0.05 * cases)` - perfect match

#### 5. **Database Architecture** ✓ STRONG
**Blueprint**: Relational model, standardized units, extensible schema
**Our Implementation**: SQLite with proper normalization, foreign keys, indexes

#### 6. **Structured Data Collection** ✓ ALIGNED
**Blueprint**: "Structured, closed-ended questions and standardized scales"
**Our Implementation**: Drop-downs, sliders, validated inputs throughout UI

---

## Part 2: Critical Gaps Identified

### 🔴 GAP 1: Lack of Pharmacokinetic Foundation

**Blueprint Requirement**:
> "The engine will employ a hybrid architecture that integrates a mechanistic Pharmacokinetic/Pharmacodynamic (PK/PD) framework with a supervised machine learning algorithm."

**Current Implementation**:
- Simple rules-based percentage adjustments (age, renal, hepatic)
- No actual PK model calculating clearance, volume of distribution, or half-life
- No integration of mechanistic equations like: `Cl = 1.58 - (age / 580.203)`

**Impact**:
- System cannot provide **mechanistically-grounded explanations**
- Missing the "why" behind recommendations (just empirical patterns)
- Less trustworthy for clinicians used to PK reasoning

**Example from Blueprint**:
```python
# Blueprint approach:
PK_Predicted_Clearance = 1.58 - (age / 580.203)  # L/h
Vd = 2.6 * LBM_kg  # Volume based on lean body mass
Initial_Dose = (Target_Concentration * Vd) / Bioavailability
ML_Adjustment = model.predict([PK_Predicted_Clearance, LBM, ...])
Final_Dose = Initial_Dose + ML_Adjustment
```

**Our Current Approach**:
```python
# Simple multiplicative adjustments:
base_mme = 25.0
if age >= 65: base_mme *= 0.80
if gfr < 35: base_mme *= 0.75
# No actual PK calculation
```

---

### 🟡 GAP 2: No Mixed-Effects Machine Learning (MEML)

**Blueprint Requirement**:
> "The core algorithm will be a Mixed-Effects Machine Learning (MEML) model, such as GPBoost, which combines gradient boosting trees with Gaussian process-based random effects."

**Current Implementation**:
- Simple back-calculation learning
- No hierarchical modeling of procedure clusters
- No "borrowing statistical strength" across rare procedures

**Impact**:
- For **rare procedures** (few cases), our system has no pattern to learn from
- Standard ML would fail here; MEML would transfer knowledge from common surgeries
- Less data-efficient, especially critical for solo practitioner with limited cases

**Blueprint's Solution**:
```
Fixed Effects: Global relationships (age → opioid need)
Random Effects: Procedure-specific intercepts & slopes
→ Rare procedures benefit from knowledge learned on common ones
```

---

### 🟡 GAP 3: Weak Explainability (XAI) Dashboard

**Blueprint Requirement**:
> "An opaque recommendation like 'Give 7.5 mg' forces the clinician into an untenable choice: blindly trust the algorithm or ignore it entirely."

**Current Implementation**:
- We show a single recommended dose
- Learning updates are displayed AFTER saving
- No **SHAP values** or feature importance before the decision
- No confidence scores

**Blueprint's XAI Dashboard Includes**:
1. **Confidence Score**: "92% confidence in this recommendation"
2. **Top 3-5 Influential Factors**: "Reduced dose due to: Age > 75, GFR < 35"
3. **Comparison to Standard**: "Standard range: 5-15 mg. AI suggests: 7.2 mg"
4. **Safety Alerts**: Drug interactions, allergy warnings

**What We Should Add**:
- Pre-recommendation explainability panel
- SHAP or LIME for feature importance
- Confidence intervals, not just point estimates

---

### 🟠 GAP 4: No Causal Inference / Individualized Treatment Effects (ITE)

**Blueprint Vision** (Phase 3 evolution):
> "The ultimate evolution involves moving from prediction to causal reasoning: 'For this specific patient, what is the causal effect on the outcome of choosing dose A versus dose B?'"

**Current Implementation**:
- Purely predictive: "Given this patient, what's the best dose?"
- Cannot answer counterfactuals: "What if I give 5mg vs 10mg?"

**Blueprint's Goal**:
- Generate **personalized dose-response curves**
- Visualize risk/benefit trade-offs across dose ranges
- Enable shared decision-making: "7.5mg → 2pt pain decrease but 40% more nausea"

**Techniques Mentioned**:
- Meta-learners (T-Learner, X-Learner)
- CATE (Conditional Average Treatment Effect) estimation
- Deep causal models

**Why This Matters**:
- Empowers **patient preference alignment**
- Moves from "one perfect dose" to "informed dose selection"
- True personalized medicine

---

### 🟢 GAP 5: Missing Multi-Task Learning (MTL)

**Blueprint Enhancement**:
> "Instead of training one model to predict the composite outcome, an MTL model, typically a neural network, is trained to predict multiple related outcomes simultaneously."

**Current Implementation**:
- Single outcome: Was the patient at VAS 1-2 and awake? (binary success)
- No simultaneous prediction of adverse events

**Blueprint's MTL Approach**:
```
Shared Trunk → Common patient/procedure representation
    ↓
Task 1: Predict optimal dose (regression)
Task 2: Predict P(nausea) (classification)
Task 3: Predict P(sedation) (classification)
Task 4: Predict P(rescue doses) (classification)
```

**Advantage**:
- More data-efficient (tasks share knowledge)
- Better risk/benefit analysis
- Single model learns holistic patient response

---

### 🟢 GAP 6: No Pharmacogenomic Readiness

**Blueprint Design**:
> "To prepare for the eventual integration of pharmacogenomic data, the Patients table includes nullable fields such as CYP2D6_Phenotype."

**Current Implementation**:
- No CYP2D6 or CYP3A4 fields in database
- Missing future-proofing for precision medicine

**Blueprint Justification**:
> "Oxycodone metabolism is heavily dependent on CYP2D6 and CYP3A4 enzyme systems, and genetic polymorphisms cause significant inter-individual variability."

**What to Add**:
```sql
ALTER TABLE patients ADD COLUMN cyp2d6_phenotype VARCHAR(30) NULL;
ALTER TABLE patients ADD COLUMN cyp3a4_phenotype VARCHAR(30) NULL;
-- Values: Poor, Intermediate, Normal, Ultrarapid Metabolizer
```

---

## Part 3: Detailed Improvement Roadmap

### Phase 4: Foundational PK/PD Integration (IMMEDIATE - Next 2-4 weeks)

**Objective**: Add mechanistic pharmacokinetic backbone to current system

#### 4.1 Implement Population PK Model
**File**: Create `pk_model.py`

**Key Functions**:
```python
def calculate_clearance(age_years: float, weight_kg: float,
                        gfr: float = 100, hepatic_status: str = 'normal') -> float:
    """
    Calculate oxycodone clearance using population PK equations.

    Base equation from literature: Cl = 1.58 - (age / 580.203) L/h
    Adjustments:
    - Renal impairment: Reduce by factor based on GFR
    - Hepatic impairment: Reduce by 33-50%

    Returns clearance in L/h
    """
    # Base clearance from age
    cl_base = 1.58 - (age_years / 580.203)

    # Renal adjustment
    if gfr < 35:
        cl_base *= 0.6  # 40% reduction
    elif gfr < 60:
        cl_base *= 0.8  # 20% reduction

    # Hepatic adjustment
    if hepatic_status == 'moderate':
        cl_base *= 0.5
    elif hepatic_status == 'severe':
        cl_base *= 0.33

    return max(0.1, cl_base)  # Safety floor

def calculate_volume_of_distribution(lbm_kg: float) -> float:
    """
    Vd = 2.6 * LBM (from literature)
    Returns volume in liters
    """
    return 2.6 * lbm_kg

def calculate_pk_based_dose(target_concentration: float, vd: float,
                            clearance: float, duration_hours: float = 4) -> float:
    """
    Calculate dose to achieve target concentration.

    For IV bolus: Dose = C_target * Vd
    For sustained effect over duration: incorporate clearance

    Returns dose in mg
    """
    bolus_dose = target_concentration * vd  # mg

    # Adjust for clearance over duration
    # Simplified: account for 50% cleared over 4 hours
    if duration_hours > 0:
        clearance_adjusted = bolus_dose * (1 + (clearance * duration_hours / vd) * 0.5)
        return clearance_adjusted

    return bolus_dose
```

#### 4.2 Create Hybrid Recommendation Function
**File**: `calculation_engine.py` - new function

```python
def calculate_hybrid_dose(inputs: dict, procedures_df, user_id: int = None) -> dict:
    """
    Hybrid PK/PD + ML dose calculation.

    Steps:
    1. Calculate PK-based dose (mechanistic foundation)
    2. If ML model exists and trained, get ML adjustment
    3. Combine: Final = PK_dose + ML_residual
    4. Return both components for explainability
    """
    import pk_model

    # 1. PK-based dose calculation
    lbm = calculate_lean_body_mass(inputs['weight'], inputs['height'], inputs['sex'])
    clearance = pk_model.calculate_clearance(
        inputs['age'],
        inputs['weight'],
        inputs.get('gfr', 100),
        inputs.get('hepatic_status', 'normal')
    )
    vd = pk_model.calculate_volume_of_distribution(lbm)

    # Target: Achieve moderate analgesia (equivalent to 20-30 ng/mL plasma)
    # Convert to mg based on procedure pain severity
    procedure = procedures_df[procedures_df['id'] == inputs['procedure_id']].iloc[0]
    base_mme = procedure['baseMME']

    # Convert MME to target concentration (rough approximation)
    target_concentration_ng_ml = base_mme * 0.8  # Empirical conversion
    target_concentration_mg_L = target_concentration_ng_ml / 1000  # ng/mL to mg/L

    pk_dose_mg = pk_model.calculate_pk_based_dose(
        target_concentration_mg_L,
        vd,
        clearance,
        duration_hours=4
    )

    # Convert from mg to MME for adjuvant calculations
    pk_dose_mme = pk_dose_mg * 3  # 1mg IV oxy = 3 MME

    # 2. Apply adjuvant reductions (percentage-based)
    final_mme_after_adjuvants = apply_all_adjuvants(
        pk_dose_mme,
        inputs,
        procedure,
        user_id
    )

    # 3. ML adjustment (if available - future)
    ml_adjustment_mme = 0  # Placeholder for Phase 5
    # if ml_model_trained:
    #     features = engineer_features(inputs, clearance, vd, lbm)
    #     ml_adjustment_mme = ml_model.predict_residual(features)

    final_mme = final_mme_after_adjuvants + ml_adjustment_mme
    final_dose_mg = final_mme / 3

    return {
        'recommended_dose': final_dose_mg,
        'pk_component': pk_dose_mg,
        'adjuvant_reduction': pk_dose_mg - (final_mme_after_adjuvants / 3),
        'ml_adjustment': ml_adjustment_mme / 3,
        'clearance': clearance,
        'vd': vd,
        'lbm': lbm
    }
```

#### 4.3 Update UI to Show PK Explanation
**File**: `ui/tabs/dosing_tab.py`

Add explanation panel:
```python
with st.expander("🔬 Pharmacokinetic Basis", expanded=False):
    st.write("**Mechanistic Dose Calculation:**")
    st.metric("Predicted Clearance", f"{result['clearance']:.2f} L/h")
    st.metric("Volume of Distribution", f"{result['vd']:.1f} L")
    st.metric("Lean Body Mass", f"{result['lbm']:.1f} kg")

    st.write("**Dose Breakdown:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("PK-based Dose", f"{result['pk_component']:.1f} mg")
    with col2:
        st.metric("Adjuvant Reduction", f"-{result['adjuvant_reduction']:.1f} mg")
    with col3:
        st.metric("Final Dose", f"{result['recommended_dose']:.1f} mg")
```

**Timeline**: 1-2 weeks
**Priority**: HIGH (foundation for all future work)
**Dependencies**: None
**Risk**: Low (additive, doesn't break existing system)

---

### Phase 5: Explainable AI Dashboard (IMMEDIATE - Weeks 3-4)

**Objective**: Add SHAP-based explainability and confidence scores

#### 5.1 Install & Integrate SHAP
```bash
pip install shap
```

**File**: Create `explainability.py`

```python
import shap
import numpy as np
from typing import Dict, List, Tuple

def explain_recommendation(
    recommended_dose: float,
    patient_inputs: Dict,
    pk_components: Dict,
    procedure_data: Dict
) -> Dict:
    """
    Generate explainability report for dose recommendation.

    Returns:
        {
            'confidence': float (0-1),
            'influential_factors': [(feature, direction, magnitude), ...],
            'comparison_to_standard': str,
            'alerts': [str, ...]
        }
    """

    # Calculate confidence based on:
    # - Number of similar cases in database
    # - Variance in outcomes for similar patients
    # - Distance from learned patterns
    confidence = calculate_confidence(patient_inputs, procedure_data)

    # Identify influential factors
    factors = []

    # Age effect
    if patient_inputs['age'] >= 80:
        factors.append(('Age ≥80 years', 'DECREASE', 0.4))
    elif patient_inputs['age'] >= 65:
        factors.append(('Age ≥65 years', 'DECREASE', 0.2))

    # Renal function
    if patient_inputs.get('gfr', 100) < 35:
        factors.append(('Severe renal impairment (GFR<35)', 'DECREASE', 0.3))

    # Procedure pain level
    pain_level = procedure_data.get('painTypeScore', 5)
    if pain_level >= 8:
        factors.append(('High-pain procedure (score 8-10)', 'INCREASE', 0.25))

    # Adjuvants
    if patient_inputs.get('nsaid'):
        factors.append(('NSAID co-administration', 'DECREASE', 0.15))

    # Sort by magnitude
    factors.sort(key=lambda x: x[2], reverse=True)

    # Standard dose range
    standard_range = get_standard_range(procedure_data['id'])
    comparison = f"Standard range: {standard_range[0]:.1f}-{standard_range[1]:.1f} mg. AI recommends: {recommended_dose:.1f} mg"

    # Safety alerts
    alerts = check_safety_alerts(patient_inputs, recommended_dose)

    return {
        'confidence': confidence,
        'influential_factors': factors[:5],  # Top 5
        'comparison_to_standard': comparison,
        'alerts': alerts
    }

def calculate_confidence(patient_inputs: Dict, procedure_data: Dict) -> float:
    """
    Calculate recommendation confidence based on training data density.
    """
    import database as db

    # Get number of similar cases
    similar_cases = db.get_similar_cases_count(
        procedure_id=patient_inputs['procedure_id'],
        age_range=(patient_inputs['age'] - 10, patient_inputs['age'] + 10),
        weight_range=(patient_inputs['weight'] - 15, patient_inputs['weight'] + 15)
    )

    # Confidence increases with more similar cases (saturates at 100 cases)
    base_confidence = min(similar_cases / 100, 0.95)

    # Reduce confidence if patient is outlier (very old, very young, extreme weight)
    if patient_inputs['age'] < 20 or patient_inputs['age'] > 90:
        base_confidence *= 0.8
    if patient_inputs['weight'] < 40 or patient_inputs['weight'] > 130:
        base_confidence *= 0.9

    return max(0.3, base_confidence)  # Minimum 30% confidence

def check_safety_alerts(patient_inputs: Dict, dose: float) -> List[str]:
    """Check for safety concerns."""
    alerts = []

    # Age + high dose
    if patient_inputs['age'] >= 80 and dose > 10:
        alerts.append("⚠️ High dose (>10mg) in patient ≥80 years - consider reducing")

    # Renal + dose
    if patient_inputs.get('gfr', 100) < 35 and dose > 8:
        alerts.append("⚠️ Dose >8mg with GFR<35 - risk of accumulation")

    # Allergy check
    if 'oxycodone' in patient_inputs.get('allergies', '').lower():
        alerts.append("🚨 ALLERGY ALERT: Patient allergic to oxycodone!")

    # Drug interactions (if adjuvants recorded)
    if patient_inputs.get('benzodiazepine', False):
        alerts.append("⚠️ Concurrent benzodiazepine use - increased sedation risk")

    return alerts
```

#### 5.2 Add XAI Dashboard to UI
**File**: `ui/tabs/dosing_tab.py`

```python
# After dose calculation
explanation = explainability.explain_recommendation(
    result['recommended_dose'],
    current_inputs,
    result,  # PK components
    procedure_data
)

# Display XAI Dashboard
st.markdown("### 📊 Recommendation Explanation")

col1, col2 = st.columns([1, 2])
with col1:
    confidence_color = "green" if explanation['confidence'] > 0.7 else "orange" if explanation['confidence'] > 0.5 else "red"
    st.markdown(f"**Confidence:** :{confidence_color}[{explanation['confidence']:.0%}]")

with col2:
    st.info(explanation['comparison_to_standard'])

# Influential factors
st.markdown("**Key Factors Influencing This Dose:**")
for factor, direction, magnitude in explanation['influential_factors']:
    arrow = "⬇️" if direction == "DECREASE" else "⬆️"
    st.write(f"{arrow} {factor} ({magnitude:+.0%} effect)")

# Safety alerts
if explanation['alerts']:
    for alert in explanation['alerts']:
        if "🚨" in alert:
            st.error(alert)
        else:
            st.warning(alert)
```

**Timeline**: 1 week
**Priority**: HIGH (critical for clinical trust)
**Dependencies**: None
**Risk**: Low

---

### Phase 6: Mixed-Effects ML Model (MEDIUM TERM - Months 2-3)

**Objective**: Replace simple back-calculation with GPBoost MEML

#### 6.1 Setup GPBoost Environment
```bash
pip install gpboost scikit-learn
```

#### 6.2 Implement MEML Training Pipeline
**File**: Create `ml_training.py`

```python
import gpboost as gpb
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

def prepare_training_data() -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Extract and engineer features from database for ML training.

    Returns:
        X: Feature matrix (n_samples, n_features)
        y: Target variable (success: 1, failure: 0)
        group: Cluster IDs (procedure_type)
    """
    import database as db

    # Get all cases with outcomes
    cases = db.get_all_cases_with_outcomes()

    # Engineer features
    features = []
    targets = []
    groups = []

    for case in cases:
        # Patient features
        age = case['age']
        lbm = calculate_lean_body_mass(case['weight'], case['height'], case['sex'])

        # PK-derived features
        clearance = pk_model.calculate_clearance(age, case['weight'],
                                                  case.get('gfr', 100))
        vd = pk_model.calculate_volume_of_distribution(lbm)

        # Procedure features
        procedure_pain = case['procedure_pain_somatic']  # From learned data

        # Adjuvant features (binary)
        nsaid_given = 1 if case['nsaid'] else 0
        ketamine_given = 1 if case['ketamine'] != 'Nej' else 0

        # Actual dose given
        dose_given = case['given_dose']

        # Feature vector
        features.append([
            age, lbm, clearance, vd,
            procedure_pain, nsaid_given, ketamine_given,
            dose_given
        ])

        # Target: Was outcome successful? (VAS 1-2 and awake)
        success = (case['vas'] in [1, 2] and
                   case.get('sedation_level', 0) <= 1)
        targets.append(1 if success else 0)

        # Group: Procedure type (for random effects)
        groups.append(case['procedure_id'])

    X = pd.DataFrame(features, columns=[
        'age', 'lbm', 'clearance', 'vd',
        'procedure_pain', 'nsaid', 'ketamine', 'dose'
    ])
    y = pd.Series(targets)
    group = pd.Series(groups)

    return X, y, group

def train_meml_model(X, y, group):
    """
    Train Mixed-Effects Machine Learning model using GPBoost.
    """
    # Split data
    X_train, X_test, y_train, y_test, group_train, group_test = train_test_split(
        X, y, group, test_size=0.2, random_state=42
    )

    # Define random effects group structure
    gp_model = gpb.GPModel(group_data=group_train, likelihood="bernoulli")

    # Train GPBoost model
    data_train = gpb.Dataset(X_train, y_train)

    params = {
        'objective': 'binary',
        'learning_rate': 0.05,
        'max_depth': 5,
        'num_leaves': 31,
        'verbose': 0
    }

    bst = gpb.train(
        params=params,
        train_set=data_train,
        gp_model=gp_model,
        num_boost_round=100
    )

    # Evaluate
    y_pred = bst.predict(X_test, group_data_pred=group_test,
                         predict_var=True)

    from sklearn.metrics import roc_auc_score, accuracy_score
    auc = roc_auc_score(y_test, y_pred['response_mean'])

    print(f"Model AUC: {auc:.3f}")

    # Save model
    bst.save_model('models/meml_oxycodone_dose.txt')

    return bst

def predict_optimal_dose_meml(patient_inputs: dict, procedure_data: dict,
                               model_path: str = 'models/meml_oxycodone_dose.txt'):
    """
    Use trained MEML model to predict optimal dose.

    Strategy: Test multiple candidate doses, predict P(success) for each,
    choose dose with highest probability.
    """
    # Load model
    bst = gpb.Booster(model_file=model_path)

    # Calculate PK features
    lbm = calculate_lean_body_mass(...)
    clearance = pk_model.calculate_clearance(...)
    vd = pk_model.calculate_volume_of_distribution(...)

    # Test dose range (e.g., 3mg to 15mg in 0.5mg increments)
    candidate_doses = np.arange(3, 15.5, 0.5)
    success_probs = []

    for dose in candidate_doses:
        # Create feature vector for this dose
        features = pd.DataFrame([[
            patient_inputs['age'],
            lbm, clearance, vd,
            procedure_data['painTypeScore'],
            1 if patient_inputs.get('nsaid') else 0,
            1 if patient_inputs.get('ketamine') != 'Nej' else 0,
            dose
        ]], columns=['age', 'lbm', 'clearance', 'vd',
                     'procedure_pain', 'nsaid', 'ketamine', 'dose'])

        # Predict P(success) for this dose
        pred = bst.predict(features, group_data_pred=[patient_inputs['procedure_id']])
        success_probs.append(pred['response_mean'][0])

    # Find dose with highest P(success)
    optimal_idx = np.argmax(success_probs)
    optimal_dose = candidate_doses[optimal_idx]
    confidence = success_probs[optimal_idx]

    return optimal_dose, confidence, list(zip(candidate_doses, success_probs))
```

**Timeline**: 3-4 weeks
**Priority**: MEDIUM (significant upgrade but complex)
**Dependencies**: Phase 4 (PK model must exist first)
**Risk**: MEDIUM (need sufficient training data - maybe 100+ cases)

---

### Phase 7: Multi-Task Learning for Adverse Events (LONG TERM - Months 4-6)

**Objective**: Simultaneous prediction of dose + nausea + sedation + rescue needs

#### 7.1 Design MTL Architecture
**Framework**: TensorFlow/Keras or PyTorch

**Architecture**:
```
Input Layer (patient + procedure features)
    ↓
Shared Dense Layers (128 → 64 neurons) [Common representation]
    ↓
    ├─→ Task 1: Dose Regression (1 output neuron)
    ├─→ Task 2: Nausea Classification (sigmoid, 1 output)
    ├─→ Task 3: Sedation Classification (sigmoid, 1 output)
    └─→ Task 4: Rescue Dose Needed (sigmoid, 1 output)
```

**File**: Create `mtl_model.py`

```python
import tensorflow as tf
from tensorflow import keras

def build_mtl_model(input_dim: int):
    """Build Multi-Task Learning model."""

    # Input
    inputs = keras.Input(shape=(input_dim,), name='patient_features')

    # Shared trunk
    shared = keras.layers.Dense(128, activation='relu', name='shared_1')(inputs)
    shared = keras.layers.Dropout(0.3)(shared)
    shared = keras.layers.Dense(64, activation='relu', name='shared_2')(shared)
    shared = keras.layers.Dropout(0.2)(shared)

    # Task-specific heads
    dose_head = keras.layers.Dense(32, activation='relu')(shared)
    dose_output = keras.layers.Dense(1, name='dose')(dose_head)  # Regression

    nausea_head = keras.layers.Dense(16, activation='relu')(shared)
    nausea_output = keras.layers.Dense(1, activation='sigmoid', name='nausea')(nausea_head)

    sedation_head = keras.layers.Dense(16, activation='relu')(shared)
    sedation_output = keras.layers.Dense(1, activation='sigmoid', name='sedation')(sedation_head)

    rescue_head = keras.layers.Dense(16, activation='relu')(shared)
    rescue_output = keras.layers.Dense(1, activation='sigmoid', name='rescue')(rescue_head)

    # Build model
    model = keras.Model(
        inputs=inputs,
        outputs={
            'dose': dose_output,
            'nausea': nausea_output,
            'sedation': sedation_output,
            'rescue': rescue_output
        }
    )

    # Compile with task-specific losses and weights
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss={
            'dose': 'mse',
            'nausea': 'binary_crossentropy',
            'sedation': 'binary_crossentropy',
            'rescue': 'binary_crossentropy'
        },
        loss_weights={
            'dose': 1.0,
            'nausea': 0.5,
            'sedation': 0.5,
            'rescue': 0.3
        },
        metrics={
            'dose': 'mae',
            'nausea': 'accuracy',
            'sedation': 'accuracy',
            'rescue': 'accuracy'
        }
    )

    return model
```

**Timeline**: 6-8 weeks
**Priority**: LOW (nice-to-have, not critical)
**Dependencies**: Phase 6 (need ML pipeline established)
**Risk**: MEDIUM (requires diverse outcome data - nausea, sedation)

---

### Phase 8: Causal Inference & ITE (ADVANCED - Months 6-12)

**Objective**: Estimate individualized treatment effects for different doses

**Approach**: Meta-learners (T-Learner or X-Learner)

**Conceptual Implementation**:
```python
# T-Learner approach (simplest)
# Train TWO separate models:
# Model 0: Predict outcome for patients who received LOW dose (e.g., <7mg)
# Model 1: Predict outcome for patients who received HIGH dose (e.g., ≥7mg)

# For new patient:
outcome_if_low = model_0.predict(patient_features)
outcome_if_high = model_1.predict(patient_features)
ITE = outcome_if_high - outcome_if_low  # Causal effect of high vs low dose
```

**Why This is Hard**:
- Requires **large dataset** (1000+ cases)
- Need **balanced treatment assignment** (can't all be same dose)
- **Confounding** must be addressed (adjusting for all covariates)

**Blueprint's Vision**:
> "The UI could display: 'For this patient, increasing the dose from 5 mg to 7.5 mg is predicted to cause a 2-point decrease in pain but a 40% increase in the probability of nausea.'"

**Timeline**: 3-6 months (research-grade implementation)
**Priority**: LOW (cutting-edge research, not clinically necessary yet)
**Dependencies**: Phase 7 (MTL for adverse event prediction)
**Risk**: HIGH (needs extensive data, advanced ML expertise)

---

## Part 4: Immediate Action Plan (Next 30 Days)

### Week 1-2: PK Foundation
- [ ] Create `pk_model.py` with clearance/Vd functions
- [ ] Integrate PK calculation into `calculation_engine.py`
- [ ] Test PK dose vs current rules-based dose (compare outputs)
- [ ] Update UI to show PK components (clearance, Vd, LBM)

### Week 3: XAI Dashboard
- [ ] Create `explainability.py` with confidence scoring
- [ ] Implement influential factors extraction
- [ ] Add safety alert checks
- [ ] Update dosing_tab.py with XAI panel

### Week 4: Testing & Refinement
- [ ] End-to-end test: PK + XAI + learning
- [ ] Validate PK model outputs against literature
- [ ] User testing (if possible with clinician feedback)
- [ ] Documentation update

---

## Part 5: What We Should NOT Change (Preserve These)

### ✅ Keep Current Strengths

1. **Global Learning Architecture** - Already perfect, don't touch
2. **3D Pain Matching** - Ahead of blueprint, keep as-is
3. **Percentage-Based Adjuvants** - Exactly as specified, keep
4. **Hyperbolic Decay Formula** - Mathematically sound, keep
5. **Database Schema** - Well-normalized, keep structure
6. **UI Data Collection** - Structured inputs work well, keep

---

## Part 6: Critical Implementation Principles

### 1. **Backward Compatibility**
- New PK model must work alongside current rules-based system
- Don't break existing learning loops
- Allow gradual transition (hybrid mode initially)

### 2. **Safety First**
- All new models: validate outputs against clinical guidelines
- Implement hard limits (e.g., max 20mg dose, never negative)
- XAI must flag concerning recommendations

### 3. **Data Quality Over Quantity**
- Don't deploy ML models until 50-100 quality cases collected
- PK model can work immediately (based on literature, not data)
- XAI can work immediately (rule-based explainability)

### 4. **Incremental Deployment**
- Phase 4 (PK): Low risk, high value - do first
- Phase 5 (XAI): Low risk, high value - do second
- Phase 6 (MEML): Medium risk, high value - do when data available
- Phase 7-8: Research-grade, only if time/data permits

---

## Part 7: Success Metrics

### How to Measure Improvement After Each Phase

**Phase 4 (PK Integration)**:
- [ ] System can explain dose in terms of clearance/Vd
- [ ] Dose recommendations align with PK literature
- [ ] Clinician reports increased trust in "mechanistic" explanations

**Phase 5 (XAI Dashboard)**:
- [ ] Every recommendation shows confidence score
- [ ] Top 3 factors always visible
- [ ] Safety alerts catch edge cases (age + high dose, etc.)

**Phase 6 (MEML)**:
- [ ] Model AUC > 0.75 on validation set
- [ ] Predictions for rare procedures improve (borrow strength)
- [ ] Learning stabilizes (less variance in recommendations)

**Phase 7 (MTL)**:
- [ ] Simultaneous prediction of 4 outcomes with shared accuracy gain
- [ ] Risk/benefit trade-offs visualized for clinician

**Phase 8 (Causal ITE)**:
- [ ] Generate patient-specific dose-response curves
- [ ] Enable "what-if" scenario testing in UI

---

## Conclusion

Our current implementation (v6) has **excellent foundations** but is operating at a "sophisticated rules + simple learning" level. The blueprint envisions a **true pharmacometric-ML hybrid** with causal reasoning.

**What We Built Well**:
- Global learning ✓
- 3D pain matching ✓
- Percentage adjuvants ✓
- Database architecture ✓

**What We Must Add** (Priority Order):
1. **PK mechanistic foundation** (CRITICAL - adds trust & explainability)
2. **XAI dashboard** (CRITICAL - enables clinical adoption)
3. **MEML with random effects** (HIGH VALUE - better data efficiency)
4. **MTL for adverse events** (NICE TO HAVE - holistic modeling)
5. **Causal ITE** (RESEARCH - cutting edge, not essential)

**Recommended Path**: Execute Phase 4 + 5 immediately (Weeks 1-4). This transforms the system from "black box learning" to "explainable pharmacometric-ML hybrid" without requiring extensive new data. Phase 6+ can wait until 100+ cases accumulated.

---

**Next Steps**: Should I proceed with implementing Phase 4 (PK Foundation) immediately, or would you like to discuss/refine this plan first?
