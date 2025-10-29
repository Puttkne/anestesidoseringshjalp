# Database.py Global Learning Changes

## Summary of Changes

Removing `user_id` from all learning function signatures and SQL queries to make all learning global.

## Function Signature Changes

### Procedures (Lines ~1080-1140)

**BEFORE:**
```python
def get_procedure_learning(user_id: int, procedure_id: str, default_base_mme: float, default_pain_type: float) -> Dict:
    ...
    WHERE user_id=? AND procedure_id=?
    ...

def update_procedure_learning(user_id: int, procedure_id: str, default_base_mme: float,
                              default_pain_type: float, base_mme_adj: float, pain_type_adj: float):
    ...
    INSERT OR REPLACE INTO learning_procedures (user_id, procedure_id, ...)
    ...
```

**AFTER:**
```python
def get_procedure_learning(procedure_id: str, default_base_mme: float, default_pain_type: float) -> Dict:
    ...
    WHERE procedure_id=?
    ...

def update_procedure_learning(procedure_id: str, default_base_mme: float,
                              default_pain_type: float, base_mme_adj: float, pain_type_adj: float):
    ...
    INSERT OR REPLACE INTO learning_procedures (procedure_id, ...)
    ...
```

### Age Factors (Lines ~700-760)

**BEFORE:**
```python
def get_age_factor(user_id: int, age: int, default_factor: float) -> float:
    WHERE user_id=? AND age_group=?

def update_age_factor(user_id: int, age: int, default_factor: float, adjustment: float) -> float:
    INSERT OR REPLACE INTO learning_age_factors (user_id, age_group, ...)
```

**AFTER:**
```python
def get_age_factor(age: int, default_factor: float) -> float:
    WHERE age_group=?

def update_age_factor(age: int, default_factor: float, adjustment: float) -> float:
    INSERT OR REPLACE INTO learning_age_factors (age_group, ...)
```

### ASA Factors (Lines ~760-820)

**BEFORE:**
```python
def get_asa_factor(user_id: int, asa_class: str, default_factor: float) -> float:
def update_asa_factor(user_id: int, asa_class: str, default_factor: float, adjustment: float) -> float:
```

**AFTER:**
```python
def get_asa_factor(asa_class: str, default_factor: float) -> float:
def update_asa_factor(asa_class: str, default_factor: float, adjustment: float) -> float:
```

### Sex Factors (Lines ~920-970)

**BEFORE:**
```python
def get_sex_factor(user_id: int, sex: str, default_factor: float) -> float:
def update_sex_factor(user_id: int, sex: str, default_factor: float, adjustment: float) -> float:
```

**AFTER:**
```python
def get_sex_factor(sex: str, default_factor: float) -> float:
def update_sex_factor(sex: str, default_factor: float, adjustment: float) -> float:
```

### Body Composition (Lines ~972-1070)

**BEFORE:**
```python
def get_body_composition_factor(user_id: int, metric_type: str, metric_value: float, default_factor: float) -> float:
def update_body_composition_factor(user_id: int, metric_type: str, metric_value: float,
                                   default_factor: float, adjustment: float) -> float:
```

**AFTER:**
```python
def get_body_composition_factor(metric_type: str, metric_value: float, default_factor: float) -> float:
def update_body_composition_factor(metric_type: str, metric_value: float,
                                   default_factor: float, adjustment: float) -> float:
```

### Renal Factor (Lines ~820-890)

**BEFORE:**
```python
def get_renal_factor(user_id: int, default_factor: float) -> float:
def update_renal_factor(user_id: int, default_factor: float, adjustment: float) -> float:
```

**AFTER:**
```python
def get_renal_factor(default_factor: float) -> float:
def update_renal_factor(default_factor: float, adjustment: float) -> float:
```

### Opioid Tolerance (Lines ~820-890)

**BEFORE:**
```python
def get_opioid_tolerance_factor(user_id: int) -> float:
def update_opioid_tolerance_factor(user_id: int, adjustment: float) -> float:
```

**AFTER:**
```python
def get_opioid_tolerance_factor() -> float:
def update_opioid_tolerance_factor(adjustment: float) -> float:
```

### Pain Threshold (Lines ~820-890)

**BEFORE:**
```python
def get_pain_threshold_factor(user_id: int) -> float:
def update_pain_threshold_factor(user_id: int, adjustment: float) -> float:
```

**AFTER:**
```python
def get_pain_threshold_factor() -> float:
def update_pain_threshold_factor(adjustment: float) -> float:
```

### Synergy (Lines ~1240-1310)

**BEFORE:**
```python
def get_synergy_factor(user_id: int, drug_combo: str) -> float:
def update_synergy_factor(user_id: int, drug_combo: str, adjustment: float) -> float:
```

**AFTER:**
```python
def get_synergy_factor(drug_combo: str) -> float:
def update_synergy_factor(drug_combo: str, adjustment: float) -> float:
```

### Fentanyl (Lines ~1310-1370)

**BEFORE:**
```python
def get_fentanyl_remaining_fraction(user_id: int) -> float:
def update_fentanyl_learning(user_id: int, adjustment: float) -> float:
```

**AFTER:**
```python
def get_fentanyl_remaining_fraction() -> float:
def update_fentanyl_learning(adjustment: float) -> float:
```

### Adjuvants (Already Global - v2)

**NO CHANGE NEEDED:**
```python
def get_adjuvant_learning(adjuvant_name: str):  # Already global!
def update_adjuvant_learning(adjuvant_name: str, selectivity_adj: float, potency_adj: float):
```

## SQL Query Pattern Changes

### Old Pattern (Per-User):
```sql
SELECT factor FROM learning_age_factors
WHERE user_id=? AND age_group=?

INSERT OR REPLACE INTO learning_age_factors (user_id, age_group, factor, num_observations)
VALUES (?, ?, ?, ?)
```

### New Pattern (Global):
```sql
SELECT factor FROM learning_age_factors
WHERE age_group=?

INSERT OR REPLACE INTO learning_age_factors (age_group, factor, num_observations)
VALUES (?, ?, ?)
```

## Files That Need Updating After database.py

### 1. learning_engine.py

**Change all calls:**
```python
# OLD
learned_data = db.get_procedure_learning(user_id, procedure_id, default_base_mme, default_pain_somatic)
db.update_age_factor(user_id, age, default_factor, adjustment)

# NEW
learned_data = db.get_procedure_learning(procedure_id, default_base_mme, default_pain_somatic)
db.update_age_factor(age, default_factor, adjustment)
```

### 2. calculation_engine.py

**Change all calls:**
```python
# OLD
age_factor = db.get_age_factor(user_id, inputs['age'], default_age_factor) if user_id else default_age_factor

# NEW
age_factor = db.get_age_factor(inputs['age'], default_age_factor) if user_id else default_age_factor
# Note: keep the "if user_id" check for authentication, just remove user_id from the function call
```

### 3. callbacks.py

**Change all calls:**
```python
# OLD
db.update_synergy_factor(user_id, drug_combo, synergy_adj)

# NEW
db.update_synergy_factor(drug_combo, synergy_adj)
```

## Testing Checklist

After all changes:

- [ ] Migration v4 runs successfully
- [ ] Can save a case and see learning updates
- [ ] Two different users both see same learned factors
- [ ] No crashes when calling learning functions
- [ ] All unit tests pass
- [ ] Integration test with global learning works

## Total Changes

- **~18 functions** updated (remove user_id parameter)
- **~36 SQL queries** updated (remove user_id from WHERE/INSERT)
- **~50+ function calls** in other files need updating
