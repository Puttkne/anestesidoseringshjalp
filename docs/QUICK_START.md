# Quick Start Guide - Updated Anestesi-assistent v8.0

## What's New? 🎉

All critical fixes and improvements have been implemented:
- ✅ Thread-safe database connections
- ✅ Comprehensive error handling
- ✅ Input validation
- ✅ 12mg maximum dose safety limit (oxycodone)
- ✅ Database migrations and indexes
- ✅ Proper logging system
- ✅ Session token security
- ✅ Comprehensive test suite

## Installation

### 1. Install Dependencies
```bash
# Main dependencies (if not already installed)
pip install streamlit pandas bcrypt python-dotenv

# Development/Testing dependencies
pip install -r requirements-dev.txt
```

### 2. First Run
```bash
streamlit run oxydos_v8.py
```

**On first run, the system will:**
- Initialize the database
- Run migrations (add indexes and session table)
- Create a backup (anestesi_backup_YYYYMMDD_HHMMSS.db)
- Clean up expired sessions

You'll see log messages like:
```
2025-10-17 14:23:45 - __main__ - INFO - Application started
2025-10-17 14:23:45 - __main__ - INFO - Database initialized
2025-10-17 14:23:45 - migrations - INFO - Running migration to version 1...
2025-10-17 14:23:46 - migrations - INFO - Performance indexes added successfully
```

## Running Tests

### Safety Tests (CRITICAL - Run These First!)
```bash
python tests/run_tests.py safety
```

Expected output:
```
tests/test_safety.py::TestDoseSafetyLimits::test_dose_never_exceeds_absolute_maximum PASSED [33%]
tests/test_safety.py::TestDoseSafetyLimits::test_dose_always_positive PASSED [66%]
tests/test_safety.py::TestDoseSafetyLimits::test_elderly_renal_impairment_safety PASSED [100%]

========== 3 passed in 2.34s ==========
```

### All Tests
```bash
python tests/run_tests.py
```

### Unit Tests Only
```bash
python tests/run_tests.py unit
```

## Key Features to Test

### 1. Dose Safety Validation
Try entering a high oxycodone dose (e.g., 15mg) - you should see:
- ❌ Error preventing save
- 🚨 "KRITISKT: Dos överstiger säker maxdos (12.0 mg)"

### 2. Input Validation
Try invalid data:
- Age > 120: Error message
- Weight = 0: Error message
- Missing required fields: Multiple error messages

### 3. Contraindication Warnings
Test these scenarios:
- **NSAID + Renal Impairment:** ⚠️ KONTRAINDIKATION warning
- **Age ≥80 + Opioid-naive:** ⚠️ VARNING for elderly
- **Multiple sedatives:** ⚠️ OBSERVATION warning

### 4. Session Management
- Log in → Session token created
- Close browser → Session persists (24h)
- Inactive for 2h → Auto-logout

## Configuration

### Admin User (Optional)
Create a `.env` file:
```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password_here
```

**Without `.env`:** Regular users can self-register.

## Logging

### View Logs
```bash
# Real-time log monitoring
tail -f anestesi_app.log

# Or on Windows:
Get-Content anestesi_app.log -Wait
```

### Log Levels
- **INFO:** Normal operations (login, dose calculations, migrations)
- **WARNING:** Potential issues (dose above typical max)
- **ERROR:** Actual errors (database errors, validation failures)

## Database

### File Location
- **Main database:** `anestesi.db`
- **Backups:** `anestesi_backup_*.db`

### Manual Backup
```bash
# Windows
copy anestesi.db anestesi_manual_backup.db

# Linux/Mac
cp anestesi.db anestesi_manual_backup.db
```

### Check Database Version
```python
import sqlite3
conn = sqlite3.connect('anestesi.db')
cursor = conn.cursor()
cursor.execute("PRAGMA user_version")
print(f"Database version: {cursor.fetchone()[0]}")
```

## Troubleshooting

### Issue: Tests fail on first run
**Solution:** Make sure test database doesn't exist:
```bash
rm test_anestesi.db  # If it exists
python tests/run_tests.py
```

### Issue: Migration errors
**Solution:** Check logs and restore from backup:
```bash
# Check the error in logs
cat anestesi_app.log | grep ERROR

# Restore from backup if needed
copy anestesi_backup_YYYYMMDD_HHMMSS.db anestesi.db
```

### Issue: Import errors
**Solution:** Verify all dependencies installed:
```bash
pip install -r requirements-dev.txt
```

### Issue: Dose calculations seem wrong
**Solution:** Run safety tests to verify:
```bash
python tests/run_tests.py safety
```

## Performance Tips

### Large Databases
If you have >10,000 cases:
1. Indexes are automatically created (done ✅)
2. Consider periodic `VACUUM` to optimize:
```python
import sqlite3
conn = sqlite3.connect('anestesi.db')
conn.execute('VACUUM')
conn.close()
```

### Slow Queries
Check if indexes exist:
```python
import sqlite3
conn = sqlite3.connect('anestesi.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
print(cursor.fetchall())
```

Should see: `idx_cases_user_id`, `idx_cases_procedure_id`, etc.

## Security Checklist

- [ ] `.env` file with admin credentials (gitignored)
- [ ] Regular database backups
- [ ] Log file reviewed for errors
- [ ] Tests passing (especially safety tests)
- [ ] HTTPS enabled (for production)

## What to Monitor

### After Deployment
1. **Log file size:** `anestesi_app.log` (rotate if >100MB)
2. **Database size:** `anestesi.db` (backup regularly)
3. **Error rate:** Check logs for ERROR entries
4. **Dose calculations:** Periodically run safety tests

### Red Flags 🚩
- Any ERROR in logs
- Safety tests failing
- Database > 1GB without vacuum
- Sessions not expiring

## Support

### Getting Help
1. Check `anestesi_app.log` first
2. Run relevant tests
3. Review `IMPROVEMENTS_SUMMARY.md`
4. Check database integrity

### Reporting Issues
Include:
1. Last 50 lines of `anestesi_app.log`
2. Test results
3. Steps to reproduce
4. Database version (`PRAGMA user_version`)

---

**Everything is ready to use! Start the app and test the new features.** 🚀
