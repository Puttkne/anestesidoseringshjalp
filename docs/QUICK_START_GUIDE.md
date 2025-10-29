# Quick Start Guide: Advanced Features

## 🚀 Deploy Phases 4 & 5 (Ready Now!)

### Step 1: Test PK Model
```python
import pk_model

# Get PK parameters for a patient
pk_params = pk_model.get_pk_summary(
    age=75,
    weight=70,
    height=170,
    sex='Man',
    gfr=45,  # If known
    hepatic_impairment='None'  # or 'Mild', 'Moderate', 'Severe'
)

print(f"Clearance: {pk_params['clearance_L_per_h']:.2f} L/h")
print(f"Vd: {pk_params['vd_L']:.0f} L")
print(f"Half-life: {pk_params['half_life_h']:.1f} hours")

# Get human-readable explanations
explanations = pk_model.explain_pk_parameters(pk_params, age=75)
for param, explanation in explanations.items():
    print(f"{param}: {explanation}")
```

### Step 2: Test XAI Dashboard
```python
import explainability

# Generate complete explanation report
report = explainability.generate_explanation_report(
    recommended_dose=7.5,  # Your AI's recommendation
    patient_inputs={
        'age': 75,
        'weight': 70,
        'height': 170,
        'sex': 'Man',
        'gfr': 45,
        'procedure_id': 'LAP_CHOLE',
        'nsaid': True,
        'nsaid_choice': 'parecoxib',
        # ... other inputs
    },
    procedure_data={
        'id': 'LAP_CHOLE',
        'name': 'Laparoskopisk kolecystektomi',
        'painTypeScore': 7
    },
    pk_params=pk_params,  # From step 1
    num_total_cases=100  # Total cases in database
)

# Display results
print(f"Confidence: {report['confidence']:.0%}")
print(f"Explanation: {report['confidence_text']}")

print("\nTop Influential Factors:")
for name, direction, magnitude in report['influential_factors'][:5]:
    arrow = "DOWN" if direction == "DECREASE" else "UP"
    print(f"  [{arrow}] {name} ({magnitude:+.0%})")

print(f"\n{report['comparison_text']}")

if report['alerts']:
    print("\nSafety Alerts:")
    for alert in report['alerts']:
        print(f"  {alert}")
```

### Step 3: Integrate into UI (dosing_tab.py)
```python
# In your dosing calculation function:

# 1. Calculate PK parameters
import pk_model
pk_params = pk_model.get_pk_summary(
    current_inputs['age'],
    current_inputs['weight'],
    current_inputs['height'],
    current_inputs['sex'],
    current_inputs.get('gfr'),
    current_inputs.get('hepatic_impairment', 'None')
)

# 2. Calculate dose (your existing code)
recommended_dose = calculate_dose(...)  # Your current function

# 3. Generate XAI report
import explainability
xai_report = explainability.generate_explanation_report(
    recommended_dose,
    current_inputs,
    procedure_data,
    pk_params,
    len(db.get_all_cases(user_id))  # Total cases
)

# 4. Display in UI
st.markdown("### Recommended Dose")
col1, col2 = st.columns([1, 2])
with col1:
    st.metric("Dose", f"{recommended_dose:.1f} mg")
    confidence_color = "green" if xai_report['confidence'] > 0.7 else "orange"
    st.markdown(f"Confidence: :{confidence_color}[{xai_report['confidence']:.0%}]")

with col2:
    st.info(xai_report['comparison_text'])

# Show PK basis
with st.expander("Pharmacokinetic Basis"):
    st.metric("Clearance", f"{pk_params['clearance_L_per_h']:.2f} L/h")
    st.metric("Volume of Distribution", f"{pk_params['vd_L']:.0f} L")
    st.metric("Half-life", f"{pk_params['half_life_h']:.1f} hours")
    st.caption(xai_report['pk_explanation'])

# Show influential factors
with st.expander("Why This Dose?"):
    st.markdown("**Top Influential Factors:**")
    for name, direction, mag in xai_report['influential_factors'][:5]:
        arrow = "⬇️" if direction == "DECREASE" else "⬆️"
        st.write(f"{arrow} {name} ({mag:+.0%})")

# Show safety alerts
if xai_report['alerts']:
    for alert in xai_report['alerts']:
        if "[ALERT]" in alert:
            st.error(alert)
        else:
            st.warning(alert)
```

---

## 📦 Deploy Phase 6 (When 50+ Cases Available)

### Step 1: Install GPBoost
```bash
pip install gpboost scikit-learn
```

### Step 2: Prepare Training Data
```python
import meml_model

# This will extract features from all cases in database
X, y, group = meml_model.prepare_training_data(include_pk_features=True)

print(f"Training samples: {len(X)}")
print(f"Features: {list(X.columns)}")
print(f"Unique procedures: {group.nunique()}")

# Check if enough data
if len(X) >= 50:
    print("Ready to train!")
else:
    print(f"Need {50 - len(X)} more cases with complete outcomes")
```

### Step 3: Train Model
```python
import meml_model

# Load data
X, y, group = meml_model.prepare_training_data()

# Train model
model = meml_model.train_meml_model(X, y, group)

# Model is automatically saved to: models/meml_oxycodone_dose.txt
```

### Step 4: Make Predictions
```python
import meml_model

# Predict for a new patient
optimal_dose, confidence, dose_response = meml_model.predict_optimal_dose_meml(
    patient_inputs={
        'age': 75,
        'weight': 70,
        # ... all other inputs
    },
    procedure_data={
        'id': 'LAP_CHOLE',
        # ... procedure data
    }
)

print(f"MEML Prediction: {optimal_dose:.1f} mg")
print(f"Confidence: {confidence:.2f}")
```

### Step 5: Champion/Challenger Validation
```python
# Before deploying new model:
# 1. Test on validation set
# 2. Compare RMSE to current rules-based system
# 3. Only deploy if significantly better (e.g., RMSE reduced by >10%)

from sklearn.metrics import mean_squared_error
import numpy as np

# Get validation predictions
y_pred_meml = model.predict(X_val, group_data_pred=group_val)
y_pred_rules = rules_based_predictions(X_val)

rmse_meml = np.sqrt(mean_squared_error(y_val, y_pred_meml['response_mean']))
rmse_rules = np.sqrt(mean_squared_error(y_val, y_pred_rules))

print(f"MEML RMSE: {rmse_meml:.2f} mg")
print(f"Rules RMSE: {rmse_rules:.2f} mg")

if rmse_meml < rmse_rules * 0.9:  # 10% improvement
    print("MEML is better - deploy new model!")
else:
    print("Keep current rules-based system")
```

---

## 📊 Deploy Phase 7 (When 100+ Cases Available)

### Step 1: Install TensorFlow
```bash
pip install tensorflow
```

### Step 2: Collect Sedation Data
```sql
-- Add sedation tracking to database
ALTER TABLE cases ADD COLUMN sedation_level INTEGER DEFAULT 0;
-- 0 = awake, 1 = mild, 2 = moderate, 3 = severe
```

### Step 3: Implement MTL Model
```python
# Create mtl_model.py following architecture in ADVANCED_FEATURES_IMPLEMENTATION.md
# Key components:
# - Input layer: 20 features
# - Shared trunk: 128 → 64 neurons
# - Dose head: regression output
# - Sedation head: classification output
# - Multi-task loss: MSE(dose) + BCE(sedation)
```

---

## 🔮 Deploy Phase 8 (When 500+ Cases Available)

### T-Learner Implementation
```python
# When you have 500+ cases with varied dose assignments:

# 1. Split data by dose level
low_dose_data = data[data['dose'] < 7.5]
high_dose_data = data[data['dose'] >= 7.5]

# 2. Train two models
model_low = train_model(low_dose_data)
model_high = train_model(high_dose_data)

# 3. Predict ITE for new patient
outcome_if_low = model_low.predict(patient_features)
outcome_if_high = model_high.predict(patient_features)

ite = outcome_if_high - outcome_if_low

# 4. Generate full dose-response curve
doses = np.arange(3, 15, 0.5)
outcomes = [predict_outcome_at_dose(patient, d) for d in doses]
```

---

## 🧪 Testing Checklist

### Phase 4 (PK)
- [ ] Test clearance calculation for young patient
- [ ] Test clearance for elderly patient
- [ ] Test renal adjustment (GFR<35)
- [ ] Test hepatic adjustment (moderate/severe)
- [ ] Test LBM calculation
- [ ] Test half-life calculation
- [ ] Validate against literature values

### Phase 5 (XAI)
- [ ] Test confidence with 0 similar cases
- [ ] Test confidence with 50 similar cases
- [ ] Test confidence with 100+ similar cases
- [ ] Test influential factors for elderly patient
- [ ] Test influential factors for opioid-tolerant patient
- [ ] Test safety alerts for high dose + age
- [ ] Test safety alerts for renal impairment
- [ ] Test standard dose comparison

### Phase 6 (MEML)
- [ ] Verify GPBoost installation
- [ ] Test feature engineering
- [ ] Train on synthetic data
- [ ] Validate train/test split
- [ ] Test prediction on new patient
- [ ] Verify model persistence (save/load)
- [ ] Champion/challenger validation

---

## 📞 Troubleshooting

### "GPBoost not installed"
```bash
pip install gpboost
# If fails, try:
conda install -c conda-forge gpboost
```

### "No training data available"
```python
# Check database has cases with outcomes:
import database as db
cases = db.get_all_cases(user_id=1)
print(f"Total cases: {len(cases)}")

# Check how many have complete outcome data:
complete = [c for c in cases if c.get('vas') is not None]
print(f"Cases with outcomes: {len(complete)}")
```

### "Encoding errors" (Swedish characters)
```python
# Already fixed in all files - Swedish characters replaced with ASCII
# If issues persist, ensure UTF-8 encoding:
with open('file.py', 'r', encoding='utf-8') as f:
    content = f.read()
```

### "Feature mismatch" (MEML predictions)
```python
# Ensure feature order matches training:
with open('models/meml_feature_names.pkl', 'rb') as f:
    feature_names = pickle.load(f)

# Reorder features to match:
features_df = features_df[feature_names]
```

---

## 📚 Further Reading

1. **[STRATEGIC_IMPROVEMENT_PLAN.md](STRATEGIC_IMPROVEMENT_PLAN.md)**
   - Gap analysis
   - Detailed roadmap
   - Code examples

2. **[ADVANCED_FEATURES_IMPLEMENTATION.md](ADVANCED_FEATURES_IMPLEMENTATION.md)**
   - Complete technical docs
   - All phases explained
   - Testing & validation

3. **[FINAL_SESSION_SUMMARY.md](FINAL_SESSION_SUMMARY.md)**
   - Complete overview
   - All achievements
   - Next steps

4. **Source Code**
   - [pk_model.py](pk_model.py) - PK calculations
   - [explainability.py](explainability.py) - XAI dashboard
   - [meml_model.py](meml_model.py) - Hierarchical ML

---

## ✅ Quick Checklist

**Immediate Actions**:
- [ ] Test pk_model.py: `python pk_model.py`
- [ ] Test explainability.py: `python explainability.py`
- [ ] Integrate PK into dose calculation
- [ ] Add XAI dashboard to UI
- [ ] Start collecting sedation outcome data

**When 50+ Cases**:
- [ ] Install GPBoost: `pip install gpboost`
- [ ] Train MEML model
- [ ] Validate vs rules-based
- [ ] Deploy if better

**When 100+ Cases**:
- [ ] Install TensorFlow
- [ ] Implement MTL architecture
- [ ] Train multi-task model

**When 500+ Cases**:
- [ ] Implement T-Learner
- [ ] Generate dose-response curves
- [ ] Add to UI for patient decisions

---

**Quick Start Complete!** 🚀

For detailed information, see the comprehensive documentation files listed above.
