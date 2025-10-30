"""
Database Backup and Restore System
Exports/imports database to/from JSON for persistence across Streamlit Cloud reboots
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import database as db

logger = logging.getLogger(__name__)

BACKUP_FILE = "database_backup.json"

def export_database_to_json() -> Dict:
    """
    Export entire database to JSON format.
    Returns dictionary with all tables' data.
    """
    try:
        backup_data = {
            "backup_timestamp": datetime.now().isoformat(),
            "version": "1.0",
            "users": [],
            "cases": [],
            "calibration_factors": [],
            "procedures": []
        }

        # Export users (without password hashes for security - they'll be recreated from secrets)
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, is_admin, created_at FROM users")
                for row in cursor.fetchall():
                    backup_data["users"].append({
                        "id": row[0],
                        "username": row[1],
                        "is_admin": row[2],
                        "created_at": row[3]
                    })
        except Exception as e:
            logger.warning(f"Could not export users: {e}")

        # Export cases
        try:
            cases = db.get_all_cases()
            for case in cases:
                # Convert datetime objects to strings
                case_copy = case.copy()
                if 'timestamp' in case_copy and case_copy['timestamp']:
                    case_copy['timestamp'] = case_copy['timestamp'].isoformat()
                if 'last_modified' in case_copy and case_copy['last_modified']:
                    case_copy['last_modified'] = case_copy['last_modified'].isoformat()
                backup_data["cases"].append(case_copy)
        except Exception as e:
            logger.warning(f"Could not export cases: {e}")

        # Export calibration factors
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, composite_key, calibration, num_cases, last_updated
                    FROM calibration_factors
                """)
                for row in cursor.fetchall():
                    backup_data["calibration_factors"].append({
                        "user_id": row[0],
                        "composite_key": row[1],
                        "calibration": row[2],
                        "num_cases": row[3],
                        "last_updated": row[4]
                    })
        except Exception as e:
            logger.warning(f"Could not export calibration factors: {e}")

        # Export procedures
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, specialty, name, kva_code, baseMME, painTypeScore FROM procedures")
                for row in cursor.fetchall():
                    backup_data["procedures"].append({
                        "id": row[0],
                        "specialty": row[1],
                        "name": row[2],
                        "kva_code": row[3],
                        "baseMME": row[4],
                        "painTypeScore": row[5]
                    })
        except Exception as e:
            logger.warning(f"Could not export procedures: {e}")

        logger.info(f"Database exported: {len(backup_data['cases'])} cases, {len(backup_data['users'])} users")
        return backup_data

    except Exception as e:
        logger.error(f"Failed to export database: {e}")
        return None


def import_database_from_json(backup_data: Dict) -> bool:
    """
    Import database from JSON backup.
    Returns True if successful.
    """
    try:
        if not backup_data or "version" not in backup_data:
            logger.error("Invalid backup data format")
            return False

        logger.info(f"Starting database restore from backup dated {backup_data.get('backup_timestamp', 'unknown')}")

        # Import users (skip if they already exist)
        for user_data in backup_data.get("users", []):
            try:
                existing = db.get_user_by_username(user_data["username"])
                if not existing:
                    # User will be created by auth.initialize_admin() with proper password from secrets
                    logger.info(f"User {user_data['username']} will be created by auth system")
            except Exception as e:
                logger.warning(f"Could not check user {user_data.get('username')}: {e}")

        # Import procedures
        procedures_imported = 0
        for proc_data in backup_data.get("procedures", []):
            try:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR IGNORE INTO procedures (id, specialty, name, kva_code, baseMME, painTypeScore)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        proc_data["id"],
                        proc_data["specialty"],
                        proc_data["name"],
                        proc_data.get("kva_code"),
                        proc_data["baseMME"],
                        proc_data["painTypeScore"]
                    ))
                    conn.commit()
                    procedures_imported += 1
            except Exception as e:
                logger.warning(f"Could not import procedure {proc_data.get('id')}: {e}")

        # Import cases
        cases_imported = 0
        for case_data in backup_data.get("cases", []):
            try:
                # Save case using the database function
                db.save_case(case_data)
                cases_imported += 1
            except Exception as e:
                logger.warning(f"Could not import case {case_data.get('id')}: {e}")

        # Import calibration factors
        calibrations_imported = 0
        for cal_data in backup_data.get("calibration_factors", []):
            try:
                db.save_calibration_factor(
                    cal_data["user_id"],
                    cal_data["composite_key"],
                    cal_data["calibration"],
                    cal_data["num_cases"]
                )
                calibrations_imported += 1
            except Exception as e:
                logger.warning(f"Could not import calibration factor: {e}")

        logger.info(f"Database restored: {cases_imported} cases, {procedures_imported} procedures, {calibrations_imported} calibrations")
        return True

    except Exception as e:
        logger.error(f"Failed to import database: {e}")
        return False


def save_backup_to_file(backup_data: Dict, filepath: str = BACKUP_FILE) -> bool:
    """Save backup data to JSON file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Backup saved to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to save backup file: {e}")
        return False


def load_backup_from_file(filepath: str = BACKUP_FILE) -> Optional[Dict]:
    """Load backup data from JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        logger.info(f"Backup loaded from {filepath}")
        return backup_data
    except FileNotFoundError:
        logger.info(f"No backup file found at {filepath}")
        return None
    except Exception as e:
        logger.error(f"Failed to load backup file: {e}")
        return None


def auto_backup() -> bool:
    """
    Automatic backup: Export database and save to file.
    Returns True if successful.
    """
    backup_data = export_database_to_json()
    if backup_data:
        return save_backup_to_file(backup_data)
    return False


def auto_restore() -> bool:
    """
    Automatic restore: Check if database is empty, restore from backup if needed.
    Returns True if restore was performed.
    """
    try:
        # Check if database has any cases
        all_cases = db.get_all_cases()
        if len(all_cases) > 0:
            logger.info(f"Database already has {len(all_cases)} cases, skipping restore")
            return False

        # Database is empty, try to restore
        logger.info("Database is empty, attempting restore from backup...")
        backup_data = load_backup_from_file()

        if backup_data:
            return import_database_from_json(backup_data)
        else:
            logger.info("No backup file found, starting with fresh database")
            return False

    except Exception as e:
        logger.error(f"Auto-restore failed: {e}")
        return False


def get_backup_info() -> Dict:
    """Get information about the current backup file."""
    try:
        backup_data = load_backup_from_file()
        if backup_data:
            return {
                "exists": True,
                "timestamp": backup_data.get("backup_timestamp", "Unknown"),
                "num_cases": len(backup_data.get("cases", [])),
                "num_users": len(backup_data.get("users", [])),
                "num_calibrations": len(backup_data.get("calibration_factors", []))
            }
        else:
            return {"exists": False}
    except Exception as e:
        logger.error(f"Failed to get backup info: {e}")
        return {"exists": False, "error": str(e)}
