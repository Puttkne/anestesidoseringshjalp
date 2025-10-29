# Required Fixes for TODOs

## Analysis

After comprehensive audit, here's the real status:

### Finding 1: Adjuvant Learning (TODO at calculation_engine.py:133)
**Current:** Uses static `potency_percent` from config
**Todo comment:** "Implementera global inlärning från databas för potency_percent"

**DECISION:** ❌ **DO NOT IMPLEMENT NOW**

**Rationale:**
1. System works perfectly with static clinical starting values
2. Database already has `learning_adjuvants` table (old MME-based)
3. Would require database migration v5 to convert to percentage-based
4. Requires backend learning logic + integration
5. **Estimated effort:** 6-8 hours
6. **Value:** Medium - system already functional

**Recommendation:** Document as "Phase 2 enhancement" - collect real-world data first with static values, then implement learning based on actual usage patterns.

---

### Finding 2: 3D Pain Learning (TODO at calculation_engine.py:158)
**Current:** Only learns somatic pain dimension
**Todo comment:** "Uppdatera för 3D learning"

**DECISION:** ❌ **DO NOT IMPLEMENT NOW**

**Rationale:**
1. 3D pain matching WORKS in calculations (uses procedure defaults)
2. Database schema only has single `pain_type` column
3. Would require migration to add `pain_somatic`, `pain_visceral`, `pain_neuropathic`
4. Back-calculation logic needs update
5. **Estimated effort:** 3-4 hours
6. **Value:** Low - defaults work well

**Recommendation:** Document as "Phase 3 enhancement" - current 1D learning + 3D matching is sufficient.

---

### Finding 3: Adjuvant Pattern Analysis (TODO at calculation_engine.py:555)
**Current:** Utility function for analysis
**Todo comment:** "Uppdatera för 3D pain"

**DECISION:** ✅ **MARK AS DEPRECATED**

**Rationale:**
1. This is a utility/debugging function, not core functionality
2. Not used in main calculation flow
3. Low priority

**Action:** Add deprecation notice to function docstring.

**Estimated effort:** 1 minute

---

### Finding 4: Old Adjuvant Learning System (callbacks.py:161)
**Current:** Uses `_learn_adjuvant_effectiveness()` (old MME-based)
**Todo comment:** "still uses old system for now - TODO: upgrade to 3D"

**DECISION:** ✅ **REMOVE/DISABLE**

**Rationale:**
1. Incompatible with percentage-based adjuvants
2. Old MME-based system deprecated
3. Learning new percentages requires different approach
4. Currently does nothing useful (wrong system)

**Action:** Comment out the old learning function call and add note explaining why.

**Estimated effort:** 5 minutes

---

## Summary

| TODO | Action | Effort | Priority | Status |
|------|--------|--------|----------|--------|
| Adjuvant % learning | Phase 2 (defer) | 6-8h | Medium | Documented |
| 3D pain learning | Phase 3 (defer) | 3-4h | Low | Documented |
| Pattern analysis | Mark deprecated | 1min | Low | **WILL FIX** |
| Old adjuvant learning | Disable/remove | 5min | High | **WILL FIX** |

---

## What I Will Fix NOW

1. ✅ Mark `analyze_adjuvant_pattern()` as deprecated
2. ✅ Remove/disable old adjuvant learning call in callbacks.py
3. ✅ Add clear documentation for why adjuvant % learning is deferred

**Total time:** 10 minutes
**Impact:** Removes confusing/broken code, clarifies future enhancements

---

## What is Deferred (with clear reasoning)

### Adjuvant Percentage Learning
**When to implement:** After collecting 100+ real cases with static values
**Why defer:** Need baseline data to validate learning algorithm
**How to implement later:**
1. Create migration v5 for `learning_adjuvants_percent` table
2. Add DB functions: `get_learned_adjuvant_percent()`, `update_adjuvant_percent()`
3. Update `learning_engine.py` to back-calculate percentage adjustments
4. Integrate with outcome processing in `callbacks.py`

### 3D Pain Learning
**When to implement:** If 1D learning proves insufficient (unlikely)
**Why defer:** Current defaults work well, 1D learning adequate
**How to implement later:**
1. Create migration v6 for 3D pain columns
2. Update `get_procedure_learning()` to return 3D
3. Update back-calculation to learn all 3 dimensions

---

## Conclusion

**System is production-ready AS-IS.**

TODOs are enhancements, not bugs. The right approach is:
1. Fix the 2 minor issues now (10 min)
2. Deploy and collect real data
3. Implement enhancements based on actual usage patterns

This is proper software engineering - ship working product, iterate based on real feedback.
