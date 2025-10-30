# GitHub Actions Workflows

This directory contains automated workflows for the Anestesidoseringshjälp app.

## Weekly Backup Workflow

**File:** `weekly-backup.yml`

### Schedule
- **Frequency:** Every Friday at 18:00 UTC
- **Local Time:** 19:00 CET (winter) / 20:00 CEST (summer)

### What It Does

1. **Checks for backup file** - Looks for `database_backup.json` in the repository
2. **Detects changes** - Compares current backup with last committed version
3. **Commits changes** - If backup has changed, commits and pushes to GitHub
4. **Creates issue on failure** - Opens GitHub issue if workflow fails

### Manual Trigger

You can manually run this workflow:

1. Go to **Actions** tab on GitHub
2. Select **Weekly Database Backup**
3. Click **Run workflow**
4. Choose branch (usually `master`)
5. Click **Run workflow**

### How to Create a New Backup

The workflow only commits existing changes. To create a fresh backup:

1. **Open your app:** https://anestesidoseringshjalp.streamlit.app
2. **Login as admin:** Username: `Blapa`, Password: `Flubber1`
3. **Go to Admin tab** → System Status
4. **Click "Create Backup Now"**
5. **Wait for next Friday** - Workflow will auto-commit it
6. **OR manually run workflow** - Commits immediately

### Backup Flow

```
Friday 18:00 UTC
    ↓
GitHub Actions starts
    ↓
Checks database_backup.json
    ↓
Has it changed since last commit?
    ↓
Yes                No
    ↓                ↓
Commit & Push    Skip (no changes)
    ↓                ↓
✅ Done         ℹ️ Done
```

### Monitoring

#### Success
- Workflow shows ✅ green checkmark in Actions tab
- Commit message: `🤖 Automated weekly backup - YYYY-MM-DD HH:MM`

#### Failure
- Workflow shows ❌ red X in Actions tab
- Automatic GitHub issue created with error details
- Check email notifications (if enabled)

### Troubleshooting

#### "No backup file found"
**Problem:** `database_backup.json` doesn't exist

**Solution:**
1. Open app → Admin → Create Backup Now
2. Locally run: `git add database_backup.json && git commit -m "Initial backup" && git push`

#### "No changes detected"
**Problem:** Backup hasn't changed since last Friday

**Solution:**
- This is normal! Means no new data was added
- Workflow will commit automatically when backup is updated

#### Workflow failed
**Problem:** Error in GitHub Actions

**Solution:**
1. Check Actions tab for error logs
2. Verify GitHub token permissions
3. Re-run workflow manually
4. Check created issue for details

### Configuration

To change the schedule, edit `.github/workflows/weekly-backup.yml`:

```yaml
on:
  schedule:
    # Current: Friday 18:00 UTC
    - cron: '0 18 * * 5'

    # Examples:
    # Daily at 02:00: '0 2 * * *'
    # Monday 12:00: '0 12 * * 1'
    # Every Sunday: '0 0 * * 0'
```

Cron format: `minute hour day-of-month month day-of-week`

### Security

- ✅ Uses GitHub's built-in `GITHUB_TOKEN`
- ✅ No custom secrets needed
- ✅ Read-only access except for commits
- ✅ Only commits `database_backup.json`

### Dependencies

Minimal Python dependencies:
- streamlit (for compatibility checks)
- pandas (for data validation)
- requests (for potential API calls)

All installed automatically by workflow.

---

**Questions?** Check the [main README](../../README.md) for full backup documentation.
