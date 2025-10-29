# Migration v4: Global Learning Implementation Summary

## Philosophy

**user_id is ONLY for:**
- ✅ Authentication (who can log in)
- ✅ Case ownership (who created/can edit cases)
- ✅ Data cleanup (delete problematic user's cases)

**ALL learning is GLOBAL:**
- Everyone contributes to collective knowledge
- Everyone benefits from all cases
- No per-user silos

## Migration v4 Status

✅ **COMPLETE** - Created `migrate_to_v4()` in [migrations.py](migrations.py:273-590)

### What the Migration Does

Aggregates all per-user learning data and makes it global:

1. **Procedures** - `PRIMARY KEY (procedure_id)` (no user_id)
2. **Age factors** - `PRIMARY KEY (age_group)` (no user_id)
3. **Sex factors** - `PRIMARY KEY (sex)` (no user_id)
4. **Body composition** - `PRIMARY KEY (metric_type, metric_value)` (no user_id)
5. **ASA factors** - `PRIMARY KEY (asa_class)` (no user_id)
6. **Synergy** - `PRIMARY KEY (drug_combo)` (no user_id)
7. **Renal** - Single global row `PRIMARY KEY CHECK (id=1)`
8. **Opioid tolerance** - Single global row
9. **Pain threshold** - Single global row
10. **Fentanyl kinetics** - Single global row

### Aggregation Strategy

- **Averaged factors** from all users: `AVG(factor)`
- **Summed observations**: `SUM(num_observations)`
- **Preserves all learning** - nothing is lost, just combined

## Database Functions That Need Updating

### Currently Take `user_id`, Should NOT:

| Function | Current Signature | New Signature |
|----------|-------------------|---------------|
| `get_procedure_learning` | `(user_id, procedure_id, ...)` | `(procedure_id, ...)` |
| `update_procedure_learning` | `(user_id, procedure_id, ...)` | `(procedure_id, ...)` |
| `get_age_factor` | `(user_id, age, default)` | `(age, default)` |
| `update_age_factor` | `(user_id, age, default, adj)` | `(age, default, adj)` |
| `get_sex_factor` | `(user_id, sex, default)` | `(sex, default)` |
| `update_sex_factor` | `(user_id, sex, default, adj)` | `(sex, default, adj)` |
| `get_body_composition_factor` | `(user_id, type, value, default)` | `(type, value, default)` |
| `update_body_composition_factor` | `(user_id, type, value, default, adj)` | `(type, value, default, adj)` |
| `get_asa_factor` | `(user_id, asa, default)` | `(asa, default)` |
| `update_asa_factor` | `(user_id, asa, default, adj)` | `(asa, default, adj)` |
| `get_synergy_factor` | `(user_id, drug_combo)` | `(drug_combo)` |
| `update_synergy_factor` | `(user_id, drug_combo, adj)` | `(drug_combo, adj)` |
| `get_renal_factor` | `(user_id, default)` | `(default)` |
| `update_renal_factor` | `(user_id, default, adj)` | `(default, adj)` |
| `get_opioid_tolerance_factor` | `(user_id)` | `()` |
| `update_opioid_tolerance_factor` | `(user_id, adj)` | `(adj)` |
| `get_pain_threshold_factor` | `(user_id)` | `()` |
| `update_pain_threshold_factor` | `(user_id, adj)` | `(adj)` |
| `get_fentanyl_remaining_fraction` | `(user_id)` | `()` |
| `update_fentanyl_learning` | `(user_id, adj)` | `(adj)` |

### Already Global (v2):

| Function | Signature |
|----------|-----------|
| `get_adjuvant_learning` | `(adjuvant_name)` ✅ |
| `update_adjuvant_learning` | `(adjuvant_name, sel_adj, pot_adj)` ✅ |

## Files That Need Updating

### 1. database.py (~1,200 lines)
- Remove `user_id` from all learning function signatures
- Update all SQL queries to remove `WHERE user_id=?`
- Update INSERT/UPDATE queries to not include user_id

### 2. learning_engine.py (~420 lines)
- Remove `user_id` parameter from all `db.get_*` calls
- Remove `user_id` parameter from all `db.update_*` calls
- Keep `user_id` in function signatures (for logging purposes)

### 3. calculation_engine.py (~300 lines)
- Remove `user_id` parameter from all `db.get_*` calls
- Keep conditional checks like `if user_id:` (for authentication)

### 4. callbacks.py (~380 lines)
- Remove `user_id` parameter from learning function calls
- Keep `user_id` for case ownership/creation

## Impact Analysis

### BREAKS (Needs Fixing):
- ❌ All dose calculations (need user_id removed from db calls)
- ❌ All learning updates (need user_id removed from db calls)
- ❌ Tests that use learning functions

### STILL WORKS:
- ✅ Authentication (uses user_id)
- ✅ Case CRUD (uses user_id for ownership)
- ✅ Case history (filters by user_id)
- ✅ User management

## Testing Strategy

After updates complete:

1. **Unit tests** - Update test signatures
2. **Integration test** - Create case, save outcome, verify global learning
3. **Multi-user test** - Two users save cases, both see same learning
4. **Migration test** - Run on database with existing data, verify aggregation

## Rollout Plan

### Phase 1: Migration ✅ DONE
- Created `migrate_to_v4()`
- Aggregates all existing user data
- Updates schema version to 4

### Phase 2: Database Functions (NEXT)
- Update all 18 function signatures in database.py
- Remove user_id from SQL queries
- Test each function individually

### Phase 3: Learning Engine
- Update learning_engine.py to call new signatures
- Remove user_id from all db calls

### Phase 4: Calculation Engine
- Update calculation_engine.py to call new signatures
- Remove user_id from all db calls

### Phase 5: Testing
- Run all tests
- Fix any failures
- Verify global learning works

## Benefits of Global Learning

1. **Faster learning** - More data = better predictions sooner
2. **Collective intelligence** - Everyone benefits from best practices
3. **Reduced variance** - No more "my patients are different" silos
4. **Simpler code** - No user_id management in learning
5. **Better for new users** - Immediate access to existing knowledge

## Revised App Description

"This application calculates personalized oxycodone doses for postoperative pain management by learning from clinical outcomes. It takes patient characteristics, surgical procedure type, and administered adjuvant medications as inputs, then recommends an opioid dose based on baseline requirements and **globally learned patterns from all users**. The system uses multi-dimensional machine learning where procedures learn their baseline requirements, patient factors learn dosing patterns, and adjuvants learn effectiveness - **all shared across the entire user base**. When clinicians record outcomes, the system back-calculates actual requirements and adjusts future recommendations for everyone, creating a continuously improving **collective knowledge base** that helps all anesthesiologists provide safer, more accurate opioid dosing."

## Next Steps

Due to the size of this change (18 function signatures × 3 files + tests), I recommend:

1. **Option A (Fast):** I can provide you with a complete updated database.py file with all changes
2. **Option B (Controlled):** I can update functions one category at a time (procedures, then age, then sex, etc.)
3. **Option C (Manual):** I provide detailed change instructions and you review/apply each

Which approach would you prefer?
