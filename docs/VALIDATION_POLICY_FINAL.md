# Dose Validation Policy - FINAL

## Summary: Only Validate Recommended Dose from Calculation

**Key Principle:** Validation applies ONLY to the initial recommended dose calculated by "Beräkna" button (perioperative start dose). Outcome data (given dose + UVA in PACU) is NOT validated.

---

## What Gets Validated

### ✅ Recommended Dose from Calculation (Perioperative)
- **Function:** `validate_recommended_dose(dose)`
- **Threshold:** >10mg oxycodone
- **When:** After clicking "Beräkna" button
- **Warning:** "⚠️ HÖG REKOMMENDERAD DOS: X mg överstiger 10 mg"
- **Action:** Show warning banner, but allow calculation to complete

### ❌ Outcome Data (NOT Validated)
- **Given dose** (what was actually administered)
- **UVA dose** (rescue dose in PACU)
- **Total dose** (given + UVA)
- **Rationale:** PACU requirements vary widely, procedures may need >20 MME total

---

## Why This Policy?

### Perioperative Recommendation (Validated)
- **Goal:** Safe starting dose for perioperative use
- **Context:** Prophylactic, given before pain develops
- **Typical range:** 5-10mg oxycodone
- **Reasoning:**
  - Higher starting doses increase side effect risk
  - Can always give rescue doses if needed
  - Conservative approach is safer

### PACU Outcome (Not Validated)
- **Goal:** Adequate pain relief achieved
- **Context:** Reactive, treating actual pain
- **Typical range:** Highly variable (0-25+ mg total)
- **Reasoning:**
  - Some procedures genuinely require high doses (22+ MME)
  - Individual variation is enormous
  - Opioid-tolerant patients may need 20+ mg
  - Pain is already present - must treat it
  - Clinical judgment essential

---

## Examples

### Scenario 1: Major Orthopedic Surgery
**Calculation:**
- Procedure: Hip replacement (baseMME: 60)
- Patient: 75kg male, ASA 2, opioid-naive
- Adjuvants: NSAID + Catapressan
- **Recommended dose: 11mg** → ⚠️ WARNING shown
- User sees warning, decides to proceed

**Outcome:**
- Given dose: 10mg (reduced based on warning)
- VAS in PACU: 6
- UVA dose: 12mg (needed for pain control)
- **Total: 22mg** → ✅ NO WARNING, saves successfully
- Acceptable - patient was in pain and needed rescue

### Scenario 2: Minor Laparoscopy
**Calculation:**
- Procedure: Diagnostic laparoscopy (baseMME: 30)
- Patient: 60kg female, ASA 1
- Adjuvants: NSAID
- **Recommended dose: 7mg** → ✅ No warning

**Outcome:**
- Given dose: 7mg
- VAS in PACU: 2
- UVA dose: 0mg
- **Total: 7mg** → ✅ No warning

### Scenario 3: Opioid-Tolerant Patient
**Calculation:**
- Procedure: Abdominal surgery (baseMME: 70)
- Patient: Chronic pain, tramadol 400mg/day
- Tolerance factor: 1.5×
- **Recommended dose: 14mg** → ⚠️ WARNING shown
- Clinical decision: Proceed with high dose due to tolerance

**Outcome:**
- Given dose: 14mg
- VAS in PACU: 4
- UVA dose: 8mg
- **Total: 22mg** → ✅ NO WARNING
- Expected for opioid-tolerant patient

---

## Implementation

### 1. In Calculation Display (After "Beräkna")
```python
from validation import validate_recommended_dose

# After calculation
final_dose = calculation_result['finalDose']

# Validate recommended dose
is_safe, severity, msg = validate_recommended_dose(final_dose)

if severity == 'WARNING':
    st.warning(msg)
    st.caption("Detta är en rekommendation för perioperativ användning. Du kan fortsätta om det är kliniskt motiverat.")

# Always show the dose (never block)
st.success(f"Rekommenderad startdos: {final_dose} mg")
```

### 2. In Outcome Saving (NO Validation)
```python
from validation import validate_outcome_data

# Get outcome data
outcome = {
    'givenDose': given_dose,
    'uvaDose': uva_dose,
    'vas': vas,
    'postop_minutes': postop_minutes,
    # ... other fields
}

# Validate - NO dose checks, only logical errors
is_valid, errors = validate_outcome_data(outcome)

if not is_valid:
    for error in errors:
        st.error(error)
    return

# Save - no warnings about high doses
save_case(outcome)
st.success("Case saved successfully")
```

---

## API Reference

### `validate_recommended_dose(dose: float)`
**Purpose:** Validate perioperative starting dose recommendation

**Parameters:**
- `dose`: Recommended oxycodone dose in mg

**Returns:**
- `(is_safe, severity, message)`
- `is_safe`: Always `True` (warnings only)
- `severity`: 'OK' or 'WARNING'
- `message`: Swedish warning text or empty string

**Example:**
```python
is_safe, severity, msg = validate_recommended_dose(11.5)
# Returns: (True, 'WARNING', '⚠️ HÖG REKOMMENDERAD DOS: 11.5 mg överstiger 10 mg...')
```

### `validate_outcome_data(outcome_data: Dict)`
**Purpose:** Validate outcome data for logical errors only (NOT dose amounts)

**Parameters:**
- `outcome_data`: Dictionary with outcome fields

**Returns:**
- `(is_valid, errors)`
- `is_valid`: Boolean
- `errors`: List of error messages

**Checks:**
- Given dose > 0 (not zero)
- VAS between 0-10
- UVA dose ≥ 0 (not negative)
- Postop time ≥ 0
- **Does NOT check dose amounts**

---

## Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| **Recommended dose** | >10mg | ⚠️ Warning |
| Given dose | Any | ✅ Allowed |
| UVA dose | Any | ✅ Allowed |
| Total dose | Any | ✅ Allowed |
| Fentanyl (intraop) | >500µg | ⚠️ Warning |

---

## Testing

### Test Commands
```bash
# Run all validation tests
python tests/run_tests.py unit

# Run safety tests
python tests/run_tests.py safety
```

### Test Coverage
1. ✅ Recommended dose ≤10mg → No warning
2. ✅ Recommended dose >10mg → Warning shown
3. ✅ Outcome with high doses → No warnings
4. ✅ Total dose 22mg → Allowed without warning
5. ✅ 100 random configs → Warnings only for recommended >10mg

---

## FAQ

**Q: Why don't you validate outcome doses?**
A: Because PACU requirements are highly variable. A patient in severe pain with VAS 8 may legitimately need 20+ mg total. We can't pre-define a "safe" limit for reactive treatment.

**Q: What if someone enters 100mg by mistake?**
A: They would still see the VAS field. If they give 100mg, VAS should be 0. The mismatch would be caught during learning/review. Also, we could add "outlier detection" in the future.

**Q: Why 10mg threshold for recommended dose?**
A: Based on clinical practice:
- Most patients: 5-10mg adequate
- >10mg: Higher side effect risk for prophylactic dose
- Can always escalate in PACU if needed

**Q: What about opioid-tolerant patients?**
A: The calculation already applies 1.5× tolerance factor. If that results in >10mg recommendation, warning is shown but clinician can proceed. In PACU, they can give whatever is needed.

**Q: Can I change the 10mg threshold?**
A: Yes, edit `RECOMMENDED_DOSE_THRESHOLD` in `validation.py`.

---

## Future Enhancements

Potential improvements:
1. **Outlier detection:** Flag cases where dose-VAS relationship is unusual
2. **Trend analysis:** Alert if user consistently gives much higher/lower than recommended
3. **Context-aware thresholds:** Higher threshold for procedures with baseMME >80
4. **Peer comparison:** Show how your dosing compares to similar cases

---

**Policy effective: 2025-10-17**
**Validation applies ONLY to recommended doses, NOT outcome data.**
