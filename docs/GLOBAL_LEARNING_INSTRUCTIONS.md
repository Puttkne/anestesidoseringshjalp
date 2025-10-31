# Global Learning Migration - Complete Instructions

## What You Have Now

✅ **Migration v4** - Ready to run (in [migrations.py](migrations.py))
✅ **Updated README** - Documents global learning philosophy and cleanup procedures
✅ **Automated conversion scripts** - Ready to update all code files

## Step-by-Step Instructions

### Step 1: Run Conversion Scripts

These scripts will automatically update all function signatures to remove `user_id`:

```bash
# 1. Update database.py (creates backup automatically)
python convert_to_global_learning.py

# 2. Update learning_engine.py, calculation_engine.py, callbacks.py
python update_other_files_for_global_learning.py
```

**What these scripts do:**
- Create timestamped backups (`.backup_YYYYMMDD_HHMMSS`)
- Remove `user_id` from ~18 function signatures in database.py
- Remove `user_id` from ~50+ function calls in other files
- Update all SQL queries to use global tables

### Step 2: Start the Application

```bash
streamlit run oxydoseks.py
```

**What happens automatically:**
- Migration v4 detects database version < 4
- Aggregates all per-user learning data
- Creates new global tables (no user_id in PRIMARY KEY)
- Logs progress: "Making learning global..."
- Sets database version to 4

### Step 3: Verify Global Learning

**Test 1: Save a case**
1. Log in as User A
2. Create a case with an outcome
3. See learning updates in UI

**Test 2: Verify it's global**
1. Log out
2. Log in as User B (different user)
3. Create similar case
4. Should see **same learned factors** as User A saw
5. Both users contribute to same global knowledge

**Test 3: Check database**
```sql
-- Should NOT have user_id column
SELECT * FROM learning_procedures;
SELECT * FROM learning_age_factors;
SELECT * FROM learning_sex_factors;

-- Should show aggregated data
SELECT procedure_id, base_mme, num_cases FROM learning_procedures;
```

## Files Modified

### By Conversion Scripts:
1. ✅ `database.py` - All learning functions now global
2. ✅ `learning_engine.py` - All db calls updated
3. ✅ `calculation_engine.py` - All db calls updated
4. ✅ `callbacks.py` - All db calls updated

### Already Updated:
5. ✅ `migrations.py` - v4 migration ready
6. ✅ `README.md` - Documents global learning & cleanup
7. ✅ `body_composition_utils.py` - Already global-compatible

## What Changed

### Before (Per-User):
```python
# Database function
def get_age_factor(user_id: int, age: int, default: float) -> float:
    cursor.execute("SELECT age_factor FROM learning_age_factors WHERE user_id=? AND age_group=?")

# Function call
age_factor = db.get_age_factor(user_id, 67, 1.0)
```

### After (Global):
```python
# Database function
def get_age_factor(age: int, default: float) -> float:
    cursor.execute("SELECT age_factor FROM learning_age_factors WHERE age_group=?")

# Function call
age_factor = db.get_age_factor(67, 1.0)
```

## Rollback Instructions

If something goes wrong:

```bash
# Restore from backups (created automatically by scripts)
cp database.py.backup_YYYYMMDD_HHMMSS database.py
cp learning_engine.py.backup_YYYYMMDD_HHMMSS learning_engine.py
cp calculation_engine.py.backup_YYYYMMDD_HHMMSS calculation_engine.py
cp callbacks.py.backup_YYYYMMDD_HHMMSS callbacks.py

# Reset database to version 3
sqlite3 anestesi.db "PRAGMA user_version = 3"
```

## Expected Behavior After Migration

### Global Learning Works:
- ✅ User A saves case → learning updates
- ✅ User B sees User A's learning
- ✅ Both users contribute to same knowledge base
- ✅ Procedure baseMME shared globally
- ✅ Age factors shared globally
- ✅ All patient factors shared globally
- ✅ Adjuvants shared globally

### User Isolation Still Works:
- ✅ Each user only sees their own cases in history
- ✅ Each user can only edit their own cases
- ✅ Admin can delete user's cases: `DELETE FROM cases WHERE user_id=?`
- ✅ Cases table still has user_id column

## Troubleshooting

### Error: "no such column: user_id"
**Cause:** Migration v4 ran, but code not updated yet
**Fix:** Run the conversion scripts

### Error: "too many SQL variables"
**Cause:** Function call still passing user_id
**Fix:** Check that conversion scripts ran successfully

### Error: "table learning_procedures has no column named user_id"
**Cause:** Migration v4 completed, this is expected
**Fix:** Make sure all code files are updated

### Learning not appearing for other users
**Cause:** May be caching or auth issue
**Fix:**
1. Log out both users
2. Clear browser cache
3. Log back in
4. Verify database has global tables

## Verification Checklist

After running conversion scripts:

- [ ] No syntax errors when importing modules
- [ ] Migration v4 runs successfully on app start
- [ ] Can save a case and see learning updates
- [ ] Different users see same learned factors
- [ ] Database tables have no user_id in PRIMARY KEY
- [ ] All backups created successfully
- [ ] Application starts without errors

## Benefits Summary

### Before (Per-User Learning):
- ❌ Each user learns in isolation
- ❌ New users start from scratch
- ❌ Slower learning (less data)
- ❌ Fragmented knowledge

### After (Global Learning):
- ✅ Everyone learns together
- ✅ New users get instant knowledge
- ✅ Faster learning (more data)
- ✅ Collective intelligence
- ✅ Best practices auto-propagate

## Next Steps

1. Run `python convert_to_global_learning.py`
2. Run `python update_other_files_for_global_learning.py`
3. Start application
4. Test with multiple users
5. Enjoy global learning! 🎯
