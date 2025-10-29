# Dose Validation Policy

## Philosophy: Clinical Judgment Takes Precedence

The system provides **guidance and warnings**, not hard limits. Clinical judgment always takes precedence over algorithmic recommendations.

---

## Dose Levels for Oxycodone

### ✅ Normal Range (0-8 mg)
- **Status:** OK
- **Action:** No warnings
- **Display:** Normal green/neutral

### 📊 Upper Range (8-10 mg)
- **Status:** INFO
- **Warning:** "OBS: Dos närmar sig övre gräns (8 mg)"
- **Action:** Allow, show informational note
- **Display:** Light yellow/info icon

### 💊 Above Typical Max (10-12 mg)
- **Status:** WARNING
- **Warning:** "VARNING: Dos överstiger typisk maxdos (10 mg)"
- **Action:** Allow, show warning banner
- **Display:** Yellow/orange warning icon

### ⚠️ High Dose (12-15 mg)
- **Status:** HIGH
- **Warning:** "HÖG DOS: Överstiger 12 mg. Överväg om denna dos är kliniskt motiverad."
- **Action:** Allow, show strong warning banner
- **Display:** Orange warning with emphasis

### ⚠️ Very High Dose (>15 mg)
- **Status:** VERY_HIGH
- **Warning:** "MYCKET HÖG DOS: Detta är en extremt hög dos - dubbelkolla klinisk motivering."
- **Action:** Allow, show critical warning banner
- **Display:** Red/orange critical warning with strong emphasis

---

## When Warnings Appear

### 1. During Dose Calculation
When the system calculates a recommended dose:
- **8-10 mg:** Info note below calculation
- **10-12 mg:** Yellow warning banner
- **>12 mg:** Orange/red warning banner with clinical review prompt
- **>15 mg:** Strong red banner requiring acknowledgment

### 2. When Saving Outcomes
When a user enters actual given doses:
- Validation runs on `givenDose`
- Validation runs on `uvaDose`
- Validation runs on **total dose** (`givenDose + uvaDose`)
- Warnings displayed but **saving is not blocked**
- High dose warnings logged for audit trail

### 3. In Case History
When reviewing past cases:
- High doses marked with warning icon
- Click to see what warning was shown
- Helps identify patterns of high-dose use

---

## Implementation Details

### Validation Function
```python
validate_dose_safety(drug: str, dose: float) -> Tuple[bool, str, str]
```

**Returns:**
- `is_safe`: Always `True` (warnings only, no blocking)
- `severity_level`: 'OK', 'INFO', 'WARNING', 'HIGH', 'VERY_HIGH'
- `message`: Swedish warning text for display

### Example Usage
```python
from validation import validate_dose_safety

# Check a dose
is_safe, severity, msg = validate_dose_safety('oxycodone', 13.5)

if severity == 'VERY_HIGH':
    st.error(msg)
elif severity == 'HIGH':
    st.warning(msg)
elif severity == 'WARNING':
    st.warning(msg)
elif severity == 'INFO':
    st.info(msg)
# If 'OK', show nothing
```

---

## Total Dose Considerations

### Given Dose + UVA Dose
The system also validates the **total dose** (start dose + rescue dose):

```python
total_dose = givenDose + uvaDose

if total_dose > 15.0:
    "⚠️ MYCKET HÖG TOTAL DOS: 16 mg (start + UVA) är extremt hög"
elif total_dose > 12.0:
    "💊 HÖG TOTAL DOS: 13 mg (start + UVA) överstiger 12 mg"
```

This catches cases where:
- Initial dose was reasonable (e.g., 8 mg)
- But large rescue doses were needed (e.g., 8 mg UVA)
- Total = 16 mg → System flags this for review

---

## Hard Errors (That DO Block Saving)

Only **logical errors** block saving:

1. **Negative doses** - Physically impossible
2. **Zero start dose** - Invalid outcome data
3. **VAS outside 0-10** - Invalid scale value
4. **Missing required fields** - Can't save incomplete data

High doses are **NOT** hard errors - they're warnings.

---

## Rationale

### Why Allow High Doses?

1. **Opioid-tolerant patients** may genuinely need >12mg
2. **Complex/severe procedures** may require higher doses
3. **Individual variation** is significant in pain response
4. **Clinical context** not fully captured by algorithm

### Why Warn Anyway?

1. **Catch data entry errors** (e.g., 120mg instead of 12mg)
2. **Prompt clinical review** of high-dose decisions
3. **Audit trail** for quality assurance
4. **Learning opportunity** to review high-dose cases

### Examples of Valid High-Dose Scenarios

- **Opioid-tolerant patient**, chronic pain history, major orthopedic surgery
- **Failed regional block**, patient in severe pain, large surgery
- **Morbid obesity** (150+ kg), actual weight-based dosing
- **Revision surgery** with significant tissue trauma

---

## Testing

### Safety Tests Verify:
1. ✅ Doses >12mg are **allowed**
2. ✅ Doses >12mg trigger **HIGH** severity warning
3. ✅ Doses >15mg trigger **VERY_HIGH** severity warning
4. ✅ Warnings are **logged** for audit
5. ✅ Total dose (start + UVA) is validated

### Test Command:
```bash
python tests/run_tests.py safety
```

---

## Logging

All high doses are logged:

```
2025-10-17 15:34:21 - validation - WARNING - High dose for oxycodone: 13.5 mg exceeds 12.0 mg
```

This creates an audit trail for:
- Quality review
- Pattern identification
- Individual clinician feedback
- System learning

---

## Future Enhancements

Potential improvements:
1. **Context-aware thresholds** (higher for opioid-tolerant)
2. **Procedure-specific limits** (higher for major surgery)
3. **Weight-based validation** (higher for obesity)
4. **Cumulative dose tracking** (24h total)
5. **Automatic incident reports** for very high doses

---

## Summary

| Dose Range | Severity | Action | Blocked? |
|------------|----------|--------|----------|
| 0-8 mg | OK | None | No |
| 8-10 mg | INFO | Show info | No |
| 10-12 mg | WARNING | Show warning | No |
| 12-15 mg | HIGH | Show strong warning | No |
| >15 mg | VERY_HIGH | Show critical warning | No |

**Key Point:** Clinical judgment > Algorithm. We **warn**, we don't **block**.
