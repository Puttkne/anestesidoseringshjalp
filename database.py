import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import threading

# Configure logging
logger = logging.getLogger(__name__)

DB_PATH = "anestesi.db"
_local = threading.local()

@contextmanager
def get_connection():
    """
    Context manager för thread-safe databasanslutningar.

    Använd alltid med 'with' statement:
    with get_connection() as conn:
        cursor = conn.cursor()
        ...
    """
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def _row_to_case_dict(row: sqlite3.Row) -> Dict:
    """Konvertera en databasrad till en case dictionary."""
    if not row:
        return None

    case = dict(row)
    # Konvertera boolean fields
    case['lowPainThreshold'] = bool(case.pop('low_pain_threshold', 0))
    case['nsaid'] = bool(case.pop('nsaid', 0))
    case['catapressan'] = bool(case.pop('catapressan', 0))
    case['droperidol'] = bool(case.pop('droperidol', 0))
    case['severe_fatigue'] = bool(case.pop('severe_fatigue', 0))
    case['renalImpairment'] = bool(case.pop('renal_impairment', 0))

    # Konvertera naming
    case['opioidHistory'] = case.pop('opioid_history', '')
    case['givenDose'] = case.pop('given_dose', 0)
    case['uvaDose'] = case.pop('uva_dose', 0)
    case['optimeMinutes'] = case.pop('optime_minutes', 0)
    case['fentanylDose'] = case.pop('fentanyl_dose', 0)
    case['specialty'] = case.pop('specialty', '')
    case['surgeryType'] = case.pop('surgery_type', '')
    case['kvaCode'] = case.pop('kva_code', '')

    # Parse calculation data
    if case.get('calculation_data'):
        case['calculation'] = json.loads(case['calculation_data'])

    # Konvertera timestamps
    if case.get('timestamp'):
        case['timestamp'] = datetime.fromisoformat(case['timestamp'])
    if case.get('last_modified'):
        case['last_modified'] = datetime.fromisoformat(case['last_modified'])

    return case

def init_database():
    """Initialisera databastabeller"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Användartabell
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    is_admin INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Procedures table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS procedures (
                    id TEXT PRIMARY KEY,
                    specialty TEXT NOT NULL,
                    name TEXT NOT NULL,
                    kva_code TEXT,
                    baseIME INTEGER NOT NULL,
                    painTypeScore INTEGER NOT NULL
                )
            ''')

            # Fall-tabell
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    procedure_id TEXT NOT NULL,
                    kva_code TEXT,
                    specialty TEXT,
                    surgery_type TEXT,
                    age INTEGER,
                    sex TEXT,
                    weight REAL,
                    height REAL,
                    bmi REAL,
                    ibw REAL,
                    abw REAL,
                    asa TEXT,
                    opioid_history TEXT,
                    low_pain_threshold INTEGER,
                    renal_impairment INTEGER DEFAULT 0,
                    optime_minutes INTEGER,
                    fentanyl_dose INTEGER,
                    nsaid INTEGER,
                    nsaid_choice TEXT,
                    catapressan INTEGER,
                    droperidol INTEGER,
                    ketamine TEXT,
                    ketamine_choice TEXT,
                    lidocaine TEXT,
                    betapred TEXT,
                    sevoflurane INTEGER DEFAULT 0,
                    infiltration INTEGER DEFAULT 0,
                    given_dose REAL,
                    vas INTEGER,
                    uva_dose REAL,
                    postop_minutes INTEGER,
                    postop_reason TEXT,
                    respiratory_status TEXT,
                    severe_fatigue INTEGER,
                    rescue_early INTEGER DEFAULT 0,
                    rescue_late INTEGER DEFAULT 0,
                    calculation_data TEXT,
                    status TEXT DEFAULT 'IN_PROGRESS' NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_modified TIMESTAMP,
                    last_modified_by INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (last_modified_by) REFERENCES users(id)
                )
            ''')

            # Add status column if it doesn't exist (for backward compatibility)
            try:
                cursor.execute("SELECT status FROM cases LIMIT 1")
            except sqlite3.OperationalError:
                logger.info("Adding 'status' column to 'cases' table.")
                cursor.execute("ALTER TABLE cases ADD COLUMN status TEXT DEFAULT 'IN_PROGRESS' NOT NULL")


            # Custom procedures table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS custom_procedures (
                    id TEXT PRIMARY KEY,
                    specialty TEXT NOT NULL,
                    name TEXT NOT NULL,
                    kva_code TEXT,
                    baseIME INTEGER NOT NULL,
                    painType TEXT NOT NULL,
                    painTypeScore INTEGER NOT NULL,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            ''')

            # Temporal doses table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS temporal_doses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id INTEGER NOT NULL,
                    drug_type TEXT NOT NULL,
                    drug_name TEXT NOT NULL,
                    dose REAL NOT NULL,
                    unit TEXT NOT NULL,
                    time_relative_minutes INTEGER NOT NULL,
                    administration_route TEXT DEFAULT 'IV',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
                )
            ''')

            # App Settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    last_modified_by INTEGER,
                    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Learning system tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_calibration (
                    user_id INTEGER,
                    composite_key TEXT,
                    calibration_factor REAL DEFAULT 1.0,
                    total_cases INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, composite_key)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_age_factors (
                    user_id INTEGER,
                    age_group TEXT,
                    age_factor REAL,
                    PRIMARY KEY (user_id, age_group)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_asa_factors (
                    user_id INTEGER,
                    asa_class TEXT,
                    asa_factor REAL,
                    PRIMARY KEY (user_id, asa_class)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_opioid_tolerance (
                    user_id INTEGER PRIMARY KEY,
                    tolerance_factor REAL DEFAULT 1.5
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_pain_threshold (
                    user_id INTEGER PRIMARY KEY,
                    threshold_factor REAL DEFAULT 1.2
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_renal_factor (
                    user_id INTEGER PRIMARY KEY,
                    renal_factor REAL DEFAULT 0.85
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_procedures (
                    user_id INTEGER,
                    procedure_id TEXT,
                    base_ime REAL,
                    pain_type REAL,
                    total_cases INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, procedure_id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_adjuvants (
                    user_id INTEGER,
                    adjuvant_name TEXT,
                    selectivity REAL,
                    potency REAL,
                    total_uses INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, adjuvant_name)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_synergy (
                    user_id INTEGER,
                    drug_combo TEXT,
                    synergy_factor REAL DEFAULT 1.0,
                    PRIMARY KEY (user_id, drug_combo)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_fentanyl (
                    user_id INTEGER PRIMARY KEY,
                    remaining_fraction REAL DEFAULT 0.25
                )
            ''')

            # Session tokens table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')

            conn.commit()

            # Load default procedures from JSON if table is empty
            cursor.execute('SELECT COUNT(*) as count FROM procedures')
            row = cursor.fetchone()
            if row['count'] == 0:
                import os
                import json
                json_path = 'procedures_export.json'
                if os.path.exists(json_path):
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            procedures_data = json.load(f)
                        for proc in procedures_data:
                            cursor.execute('''
                                INSERT INTO procedures (id, specialty, name, kva_code, baseIME, painTypeScore)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (
                                proc['id'],
                                proc['specialty'],
                                proc['name'],
                                proc.get('kva_code'),
                                proc['baseIME'],
                                proc.get('painTypeScore', proc.get('somatic_score', 5))
                            ))
                        conn.commit()
                        logger.info(f"Loaded {len(procedures_data)} default procedures from {json_path}")
                    except Exception as e:
                        logger.error(f"Warning: Could not load default procedures: {e}")
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in init_database: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in init_database: {e}")
        raise

def get_all_procedures() -> List[Dict]:
    """Hämta alla procedures"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM procedures')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_all_procedures: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_all_procedures: {e}")
        raise

def get_case_by_id(case_id: int) -> Optional[Dict]:
    """Hämta ett specifikt fall"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM cases WHERE id = ?', (case_id,))
            row = cursor.fetchone()
            return _row_to_case_dict(row)
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_case_by_id: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_case_by_id: {e}")
        raise

def get_all_cases(user_id=None) -> List[Dict]:
    """Hämta alla fall, filtrera på user_id om angiven"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute('SELECT * FROM cases WHERE user_id = ? ORDER BY timestamp DESC', (user_id,))
            else:
                cursor.execute('SELECT * FROM cases ORDER BY timestamp DESC')
            rows = cursor.fetchall()
            return [_row_to_case_dict(row) for row in rows]
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_all_cases: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_all_cases: {e}")
        raise

def get_all_finalized_cases(user_id=None) -> List[Dict]:
    """Hämta alla slutförda (finalized) fall, filtrera på user_id om angiven."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("SELECT * FROM cases WHERE user_id = ? AND status = 'FINALIZED' ORDER BY timestamp DESC", (user_id,))
            else:
                cursor.execute("SELECT * FROM cases WHERE status = 'FINALIZED' ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            return [_row_to_case_dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error in get_all_finalized_cases: {e}")
        raise

def get_all_custom_procedures() -> List[Dict]:
    """Hämta alla custom procedures"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM custom_procedures ORDER BY created_at DESC')
            rows = cursor.fetchall()
            procedures = []
            for row in rows:
                proc = dict(row)
                procedures.append(proc)
            return procedures
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_all_custom_procedures: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_all_custom_procedures: {e}")
        raise

def save_custom_procedure(proc_data: Dict, user_id: int):
    """Spara ett nytt custom procedure"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Konvertera painType till painTypeScore
            pain_type_map = {'somatic': 9, 'visceral': 2, 'mixed': 5}
            pain_type = proc_data.get('painType', 'mixed')
            pain_type_score = pain_type_map.get(pain_type, 5)
            cursor.execute('''
                INSERT INTO custom_procedures (
                    id, specialty, name, kva_code, baseIME, painType, painTypeScore, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                proc_data['id'],
                proc_data['specialty'],
                proc_data['name'],
                proc_data.get('kva_code'),
                proc_data['baseIME'],
                pain_type,
                pain_type_score,
                user_id
            ))
            conn.commit()
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in save_custom_procedure: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in save_custom_procedure: {e}")
        raise

def delete_custom_procedure(procedure_id: str):
    """Radera ett custom procedure"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM custom_procedures WHERE id = ?', (procedure_id,))
            conn.commit()
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in delete_custom_procedure: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in delete_custom_procedure: {e}")
        raise

def save_case(case_data: Dict, user_id: int) -> int:
    """
    Spara ett nytt fall.

    Returns:
        case_id: ID of the newly created case
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO cases (
                    user_id, procedure_id, kva_code, specialty, surgery_type,
                    age, sex, weight, height, bmi, ibw, abw,
                    asa, opioid_history, low_pain_threshold, renal_impairment,
                    optime_minutes, fentanyl_dose,
                    nsaid, nsaid_choice, catapressan, droperidol,
                    ketamine, ketamine_choice, lidocaine, betapred,
                    sevoflurane, infiltration,
                    given_dose, vas, uva_dose,
                    postop_minutes, postop_reason, respiratory_status, severe_fatigue,
                    rescue_early, rescue_late,
                    calculation_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                case_data.get('procedure_id'),
                case_data.get('kva_code'),
                case_data.get('specialty'),
                case_data.get('surgery_type', 'Elektivt'),
                case_data.get('age'),
                case_data.get('sex'),
                case_data.get('weight'),
                case_data.get('height'),
                case_data.get('bmi'),
                case_data.get('ibw'),
                case_data.get('abw'),
                case_data.get('asa'),
                case_data.get('opioidHistory'),
                int(case_data.get('lowPainThreshold', False)),
                int(case_data.get('renalImpairment', False)),
                case_data.get('optime_minutes', 0),
                case_data.get('fentanylDose', 0),
                int(case_data.get('nsaid', False)),
                case_data.get('nsaid_choice', 'Ej given'),
                int(case_data.get('catapressan', False)),
                int(case_data.get('droperidol', False)),
                case_data.get('ketamine', 'Nej'),
                case_data.get('ketamine_choice', 'Ej given'),
                case_data.get('lidocaine', 'Nej'),
                case_data.get('betapred', 'Nej'),
                int(case_data.get('sevoflurane', False)),
                int(case_data.get('infiltration', False)),
                case_data.get('givenDose', 0),
                case_data.get('vas', 0),
                case_data.get('uvaDose', 0),
                case_data.get('postop_minutes', 0),
                case_data.get('postop_reason', 'Normal återhämtning'),
                case_data.get('respiratory_status', 'vaken'),
                int(case_data.get('severe_fatigue', False)),
                int(case_data.get('rescue_early', False)),
                int(case_data.get('rescue_late', False)),
                json.dumps(case_data.get('calculation', {}))
            ))
            case_id = cursor.lastrowid
            conn.commit()
            return case_id
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in save_case: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in save_case: {e}")
        raise

def update_case(case_id: int, updated_data: Dict, user_id: int):
    """Uppdatera ett befintligt fall"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE cases SET
                    given_dose = ?,
                    vas = ?,
                    uva_dose = ?,
                    postop_minutes = ?,
                    postop_reason = ?,
                    respiratory_status = ?,
                    severe_fatigue = ?,
                    rescue_early = ?,
                    rescue_late = ?,
                    bmi = ?,
                    ibw = ?,
                    abw = ?,
                    last_modified = ?,
                    last_modified_by = ?
                WHERE id = ?
            ''', (
                updated_data.get('givenDose', 0),
                updated_data.get('vas', 0),
                updated_data.get('uvaDose', 0),
                updated_data.get('postop_minutes', 0),
                updated_data.get('postop_reason', 'Normal återhämtning'),
                updated_data.get('respiratory_status', 'vaken'),
                int(updated_data.get('severe_fatigue', False)),
                int(updated_data.get('rescue_early', False)),
                int(updated_data.get('rescue_late', False)),
                updated_data.get('bmi'),
                updated_data.get('ibw'),
                updated_data.get('abw'),
                datetime.now().isoformat(),
                user_id,
                case_id
            ))
            conn.commit()
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in update_case: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in update_case: {e}")
        raise

def finalize_case(case_id: int, final_data: Dict, user_id: int):
    """Uppdaterar ett fall med slutgiltig data och markerar det som slutfört."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Omfattande uppdatering av alla fält som kan ändras
            cursor.execute('''
                UPDATE cases SET
                    procedure_id = ?, kva_code = ?, specialty = ?, surgery_type = ?,
                    age = ?, sex = ?, weight = ?, height = ?, bmi = ?, ibw = ?, abw = ?,
                    asa = ?, opioid_history = ?, low_pain_threshold = ?, renal_impairment = ?,
                    optime_minutes = ?, fentanyl_dose = ?,
                    nsaid = ?, nsaid_choice = ?, catapressan = ?, droperidol = ?,
                    ketamine = ?, ketamine_choice = ?, lidocaine = ?, betapred = ?,
                    sevoflurane = ?, infiltration = ?,
                    given_dose = ?, vas = ?, uva_dose = ?,
                    postop_minutes = ?, postop_reason = ?, respiratory_status = ?, severe_fatigue = ?,
                    rescue_early = ?, rescue_late = ?,
                    calculation_data = ?,
                    status = 'FINALIZED',
                    last_modified = ?,
                    last_modified_by = ?
                WHERE id = ?
            ''', (
                final_data.get('procedure_id'), final_data.get('kva_code'), final_data.get('specialty'), final_data.get('surgery_type', 'Elektivt'),
                final_data.get('age'), final_data.get('sex'), final_data.get('weight'), final_data.get('height'), final_data.get('bmi'), final_data.get('ibw'), final_data.get('abw'),
                final_data.get('asa'), final_data.get('opioidHistory'), int(final_data.get('lowPainThreshold', False)), int(final_data.get('renalImpairment', False)),
                final_data.get('optime_minutes', 0), final_data.get('fentanylDose', 0),
                int(final_data.get('nsaid', False)), final_data.get('nsaid_choice', 'Ej given'), int(final_data.get('catapressan', False)), int(final_data.get('droperidol', False)),
                final_data.get('ketamine', 'Nej'), final_data.get('ketamine_choice', 'Ej given'), final_data.get('lidocaine', 'Nej'), final_data.get('betapred', 'Nej'),
                int(final_data.get('sevoflurane', False)), int(final_data.get('infiltration', False)),
                final_data.get('givenDose', 0), final_data.get('vas', 0), final_data.get('uvaDose', 0),
                final_data.get('postop_minutes', 0), final_data.get('postop_reason', 'Normal återhämtning'), final_data.get('respiratory_status', 'vaken'), int(final_data.get('severe_fatigue', False)),
                int(final_data.get('rescue_early', False)), int(final_data.get('rescue_late', False)),
                json.dumps(final_data.get('calculation', {})),
                datetime.now().isoformat(),
                user_id,
                case_id
            ))
            conn.commit()
            logger.info(f"Case {case_id} has been finalized by user {user_id}.")
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in finalize_case: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in finalize_case: {e}")
        raise

def delete_case(case_id: int):
    """Radera ett fall"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cases WHERE id = ?', (case_id,))
            conn.commit()
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in delete_case: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in delete_case: {e}")
        raise

def add_edit_history(case_id: int, user_id: int, old_data: Dict, new_data: Dict, engine: str):
    """
    Lägg till redigeringshistorik för ett fall.

    Args:
        case_id: ID of the case being edited
        user_id: ID of the user making the edit
        old_data: Previous values (givenDose, vas, uvaDose)
        new_data: New values
        engine: Calculation engine used
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Create table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS edit_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    old_given_dose REAL,
                    new_given_dose REAL,
                    old_vas INTEGER,
                    new_vas INTEGER,
                    old_uva_dose REAL,
                    new_uva_dose REAL,
                    engine TEXT,
                    edited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

            cursor.execute('''
                INSERT INTO edit_history (
                    case_id, user_id,
                    old_given_dose, new_given_dose,
                    old_vas, new_vas,
                    old_uva_dose, new_uva_dose,
                    engine
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                case_id, user_id,
                old_data.get('givenDose'), new_data.get('givenDose'),
                old_data.get('vas'), new_data.get('vas'),
                old_data.get('uvaDose'), new_data.get('uvaDose'),
                engine
            ))
            conn.commit()
            logger.info(f"Added edit history for case {case_id} by user {user_id}")

    except Exception as e:
        logger.error(f"Error in add_edit_history: {e}")
        raise

def get_edit_history(case_id: int) -> List[Dict]:
    """
    Hämta redigeringshistorik för ett fall.

    Args:
        case_id: ID of the case

    Returns:
        List of edit history dictionaries with timestamp, user, and changes
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='edit_history'
            """)
            if not cursor.fetchone():
                return []

            cursor.execute('''
                SELECT eh.*, u.username
                FROM edit_history eh
                LEFT JOIN users u ON eh.user_id = u.id
                WHERE eh.case_id = ?
                ORDER BY eh.edited_at DESC
            ''', (case_id,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    except Exception as e:
        logger.error(f"Error in get_edit_history: {e}")
        return []

# ============ User management ============

def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Hämta användare via ID"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_user_by_id: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_user_by_id: {e}")
        raise

def get_user_by_username(username: str) -> Optional[Dict]:
    """Hämta användare via användarnamn (case-insensitive)"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Case-insensitive username lookup
            cursor.execute('SELECT * FROM users WHERE LOWER(username) = LOWER(?)', (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_user_by_username: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_user_by_username: {e}")
        raise

def create_user(username: str, password_hash: Optional[str], is_admin: bool = False) -> int:
    """Skapa ny användare

    Args:
        username: Username (will be stored as provided, but lookups are case-insensitive)
        password_hash: Bcrypt password hash (case-sensitive) or None for regular users
        is_admin: Whether this is an admin user

    Returns:
        User ID of created user
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Check if username already exists (case-insensitive)
            cursor.execute('SELECT id FROM users WHERE LOWER(username) = LOWER(?)', (username,))
            if cursor.fetchone():
                raise ValueError(f"Username '{username}' already exists (case-insensitive)")

            cursor.execute('''
                INSERT INTO users (username, password_hash, is_admin)
                VALUES (?, ?, ?)
            ''', (username, password_hash, int(is_admin)))
            user_id = cursor.lastrowid
            conn.commit()
            return user_id
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in create_user: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in create_user: {e}")
        raise

# ============ Learning system - calibration factors ============

def get_calibration_factor(user_id: int, composite_key: str) -> float:
    """Hämta kalibreringsfaktor för en specifik konfiguration"""
    if not user_id or not composite_key:
        return 1.0

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT calibration_factor FROM learning_calibration
                WHERE user_id = ? AND composite_key = ?
            ''', (user_id, composite_key))
            row = cursor.fetchone()
            return row['calibration_factor'] if row else 1.0
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_calibration_factor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_calibration_factor: {e}")
        raise

def update_calibration_factor(user_id: int, composite_key: str, adjustment: float):
    """Uppdatera kalibreringsfaktor"""
    if not user_id or not composite_key:
        return

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            current_factor = get_calibration_factor(user_id, composite_key)
            new_factor = max(0.5, min(2.0, current_factor + adjustment))
            cursor.execute('''
                INSERT OR REPLACE INTO learning_calibration (user_id, composite_key, calibration_factor, total_cases)
                VALUES (?, ?, ?, COALESCE((SELECT total_cases FROM learning_calibration WHERE user_id = ? AND composite_key = ?), 0) + 1)
            ''', (user_id, composite_key, new_factor, user_id, composite_key))
            conn.commit()
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in update_calibration_factor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in update_calibration_factor: {e}")
        raise

def get_all_calibration_factors(user_id: int) -> Dict[str, float]:
    """Hämta alla kalibreringsfaktorer för en användare"""
    if not user_id:
        return {}

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT composite_key, calibration_factor FROM learning_calibration
                WHERE user_id = ?
            ''', (user_id,))
            rows = cursor.fetchall()
            return {row['composite_key']: row['calibration_factor'] for row in rows}
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_all_calibration_factors: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_all_calibration_factors: {e}")
        raise

# ============ Learning system - patient factors ============

def get_age_group(age: int) -> str:
    """Returnera åldersgrupp"""
    if age < 18:
        return '<18'
    elif age < 40:
        return '18-39'
    elif age < 65:
        return '40-64'
    elif age < 80:
        return '65-79'
    else:
        return '80+'

def get_age_factor(age: int, default_factor: float) -> float:
    """Hämta ålderfaktor (GLOBAL för alla användare sedan v4)"""
    age_group = get_age_group(age)

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT age_factor FROM learning_age_factors
                WHERE age_group = ?
            ''', (age_group,))
            row = cursor.fetchone()
            return row['age_factor'] if row else default_factor
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_age_factor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_age_factor: {e}")
        raise

def update_age_factor(age: int, default_factor: float, adjustment: float) -> float:
    """Uppdatera åldersfaktor (GLOBAL för alla användare sedan v4)"""
    if adjustment == 0:
        return default_factor

    age_group = get_age_group(age)
    current_factor = get_age_factor(age, default_factor)
    new_factor = max(0.4, min(1.5, current_factor + adjustment))

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Get current observations count
            cursor.execute('SELECT num_observations FROM learning_age_factors WHERE age_group = ?', (age_group,))
            row = cursor.fetchone()
            num_obs = (row['num_observations'] + 1) if row else 1

            cursor.execute('''
                INSERT OR REPLACE INTO learning_age_factors (age_group, age_factor, num_observations)
                VALUES (?, ?, ?)
            ''', (age_group, new_factor, num_obs))
            conn.commit()
            return new_factor
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in update_age_factor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in update_age_factor: {e}")
        raise

def get_asa_factor(asa_class: str, default_factor: float) -> float:
    """Hämta ASA-faktor (GLOBAL för alla användare sedan v4)"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT asa_factor FROM learning_asa_factors
                WHERE asa_class = ?
            ''', (asa_class,))
            row = cursor.fetchone()
            return row['asa_factor'] if row else default_factor
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_asa_factor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_asa_factor: {e}")
        raise

def update_asa_factor(asa_class: str, default_factor: float, adjustment: float) -> float:
    """Uppdatera ASA-faktor (GLOBAL för alla användare sedan v4)"""
    if adjustment == 0:
        return default_factor

    current_factor = get_asa_factor(asa_class, default_factor)
    new_factor = max(0.5, min(1.5, current_factor + adjustment))

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Get current observations count
            cursor.execute('SELECT num_observations FROM learning_asa_factors WHERE asa_class = ?', (asa_class,))
            row = cursor.fetchone()
            num_obs = (row['num_observations'] + 1) if row else 1

            cursor.execute('''
                INSERT OR REPLACE INTO learning_asa_factors (asa_class, asa_factor, num_observations)
                VALUES (?, ?, ?)
            ''', (asa_class, new_factor, num_obs))
            conn.commit()
            return new_factor
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in update_asa_factor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in update_asa_factor: {e}")
        raise

def get_opioid_tolerance_factor() -> float:
    """Hämta opioid tolerans faktor (GLOBAL för alla användare sedan v4)"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT tolerance_factor FROM learning_opioid_tolerance WHERE id = 1')
            row = cursor.fetchone()
            return row['tolerance_factor'] if row else 1.5
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_opioid_tolerance_factor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_opioid_tolerance_factor: {e}")
        raise

def update_opioid_tolerance_factor(adjustment: float) -> float:
    """Uppdatera opioid tolerans faktor (GLOBAL för alla användare sedan v4)"""
    if adjustment == 0:
        return 1.5

    current = get_opioid_tolerance_factor()
    new_factor = max(1.0, min(2.5, current + adjustment))

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Get current observations count
            cursor.execute('SELECT num_observations FROM learning_opioid_tolerance WHERE id = 1')
            row = cursor.fetchone()
            num_obs = (row['num_observations'] + 1) if row else 1

            cursor.execute('''
                INSERT OR REPLACE INTO learning_opioid_tolerance (id, tolerance_factor, num_observations)
                VALUES (1, ?, ?)
            ''', (new_factor, num_obs))
            conn.commit()
            return new_factor
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in update_opioid_tolerance_factor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in update_opioid_tolerance_factor: {e}")
        raise

def get_pain_threshold_factor() -> float:
    """Hämta smärttröskel faktor (GLOBAL för alla användare sedan v4)"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT threshold_factor FROM learning_pain_threshold WHERE id = 1')
            row = cursor.fetchone()
            return row['threshold_factor'] if row else 1.2
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_pain_threshold_factor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_pain_threshold_factor: {e}")
        raise

def update_pain_threshold_factor(adjustment: float) -> float:
    """Uppdatera smärttröskel faktor (GLOBAL för alla användare sedan v4)"""
    if adjustment == 0:
        return 1.2

    current = get_pain_threshold_factor()
    new_factor = max(1.0, min(1.8, current + adjustment))

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Get current observations count
            cursor.execute('SELECT num_observations FROM learning_pain_threshold WHERE id = 1')
            row = cursor.fetchone()
            num_obs = (row['num_observations'] + 1) if row else 1

            cursor.execute('''
                INSERT OR REPLACE INTO learning_pain_threshold (id, threshold_factor, num_observations)
                VALUES (1, ?, ?)
            ''', (new_factor, num_obs))
            conn.commit()
            return new_factor
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in update_pain_threshold_factor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in update_pain_threshold_factor: {e}")
        raise

def get_renal_factor() -> float:
    """Hämta njurfaktorn (GLOBAL för alla användare sedan v4)"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT renal_factor FROM learning_renal_factor WHERE id = 1')
            row = cursor.fetchone()
            return row['renal_factor'] if row else 0.75
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_renal_factor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_renal_factor: {e}")
        raise

def update_renal_factor(default_factor: float, adjustment: float) -> float:
    """Uppdatera njurfaktor (GLOBAL för alla användare sedan v4)"""
    if adjustment == 0:
        return default_factor

    current = get_renal_factor()
    new_factor = max(0.6, min(1.0, current + adjustment))

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Get current observations count
            cursor.execute('SELECT num_observations FROM learning_renal_factor WHERE id = 1')
            row = cursor.fetchone()
            num_obs = (row['num_observations'] + 1) if row else 1

            cursor.execute('''
                INSERT OR REPLACE INTO learning_renal_factor (id, renal_factor, num_observations)
                VALUES (1, ?, ?)
            ''', (new_factor, num_obs))
            conn.commit()
            return new_factor
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in update_renal_factor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in update_renal_factor: {e}")
        raise

# ============ Learning system - sex factors ============

def get_sex_factor(sex: str, default_factor: float) -> float:
    """Hämta könsfaktor (GLOBAL för alla användare sedan v4)"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Ensure table exists (in case migrations didn't run)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_sex_factors (
                    sex TEXT PRIMARY KEY,
                    sex_factor REAL DEFAULT 1.0,
                    num_observations INTEGER DEFAULT 0
                )
            ''')

            cursor.execute('''
                SELECT sex_factor FROM learning_sex_factors
                WHERE sex = ?
            ''', (sex,))
            row = cursor.fetchone()
            return row['sex_factor'] if row else default_factor
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_sex_factor: {e}")
        return default_factor
    except sqlite3.OperationalError as e:
        logger.warning(f"Table issue in get_sex_factor: {e}, using default")
        return default_factor
    except Exception as e:
        logger.error(f"Error in get_sex_factor: {e}")
        return default_factor

def update_sex_factor(sex: str, default_factor: float, adjustment: float) -> float:
    """Uppdatera könsfaktor (GLOBAL för alla användare sedan v4)"""
    if adjustment == 0:
        return default_factor

    current = get_sex_factor(sex, default_factor)
    new_factor = max(0.85, min(1.15, current + adjustment))

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Get current observations count
            cursor.execute('SELECT num_observations FROM learning_sex_factors WHERE sex = ?', (sex,))
            row = cursor.fetchone()
            num_obs = (row['num_observations'] + 1) if row else 1

            cursor.execute('''
                INSERT OR REPLACE INTO learning_sex_factors (sex, sex_factor, num_observations)
                VALUES (?, ?, ?)
            ''', (sex, new_factor, num_obs))
            conn.commit()
            return new_factor
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in update_sex_factor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in update_sex_factor: {e}")
        raise

# ============ Learning system - body composition factors (4D: Weight, IBW, ABW, BMI) ============

def get_body_composition_factor(metric_type: str, metric_value: float, default_factor: float) -> float:
    """
    Hämta kroppsviktsfaktor baserat på specifik metrik (GLOBAL för alla användare sedan v4).

    Args:
        metric_type: 'weight' | 'ibw_ratio' | 'abw_ratio' | 'bmi'
        metric_value: The bucketed value (e.g., 120 for weight, 1.8 for ibw_ratio, 32 for bmi)
        default_factor: Default multiplier if not learned

    Returns:
        Learned factor or default
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT composition_factor FROM learning_body_composition
                WHERE metric_type = ? AND metric_value = ?
            ''', (metric_type, metric_value))
            row = cursor.fetchone()
            return row['composition_factor'] if row else default_factor
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_body_composition_factor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_body_composition_factor: {e}")
        raise

def update_body_composition_factor(metric_type: str, metric_value: float,
                                   default_factor: float, adjustment: float) -> float:
    """
    Uppdatera kroppsviktsfaktor för en specifik metrik (GLOBAL för alla användare sedan v4).

    Args:
        metric_type: 'weight' | 'ibw_ratio' | 'abw_ratio' | 'bmi'
        metric_value: The bucketed value
        default_factor: Default multiplier
        adjustment: Learning adjustment to apply

    Returns:
        New factor after adjustment
    """
    if adjustment == 0:
        return default_factor

    current = get_body_composition_factor(metric_type, metric_value, default_factor)
    new_factor = max(0.6, min(1.4, current + adjustment))

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Get current number of observations
            cursor.execute('''
                SELECT num_observations FROM learning_body_composition
                WHERE metric_type = ? AND metric_value = ?
            ''', (metric_type, metric_value))
            row = cursor.fetchone()
            num_obs = (row['num_observations'] + 1) if row else 1

            cursor.execute('''
                INSERT OR REPLACE INTO learning_body_composition (metric_type, metric_value, composition_factor, num_observations)
                VALUES (?, ?, ?, ?)
            ''', (metric_type, metric_value, new_factor, num_obs))
            conn.commit()

            logger.info(
                f"Updated body composition: {metric_type}={metric_value}, "
                f"factor={new_factor:.3f}, observations={num_obs}"
            )
            return new_factor
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in update_body_composition_factor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in update_body_composition_factor: {e}")
        raise

# ============ Learning system - procedure learning ============

def get_procedure_learning(user_id: int, procedure_id: str, default_base_ime: float, default_pain_type: float) -> Dict:
    """Hämta inlärd data för ett ingrepp"""
    if not user_id or not procedure_id:
        return {
            'base_ime': default_base_ime,
            'pain_type': default_pain_type,
            'total_cases': 0
        }

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_procedures (
                    user_id INTEGER,
                    procedure_id TEXT,
                    base_ime REAL,
                    pain_type REAL,
                    total_cases INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, procedure_id)
                )
            ''')
            cursor.execute('''
                SELECT base_ime, pain_type, total_cases FROM learning_procedures
                WHERE user_id = ? AND procedure_id = ?
            ''', (user_id, procedure_id))
            row = cursor.fetchone()
            if row:
                return {
                    'base_ime': row['base_ime'],
                    'pain_type': row['pain_type'],
                    'total_cases': row['total_cases']
                }
            else:
                return {
                    'base_ime': default_base_ime,
                    'pain_type': default_pain_type,
                    'total_cases': 0
                }
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_procedure_learning: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_procedure_learning: {e}")
        raise

def update_procedure_learning(procedure_id: str, default_base_ime: float,
                              default_pain_type: float, base_ime_adjustment: float,
                              pain_type_adjustment: float) -> Dict:
    """Uppdatera inlärd data för ett ingrepp"""
    if not user_id or not procedure_id:
        return {'base_ime': default_base_ime, 'pain_type': default_pain_type}

    current = get_procedure_learning(procedure_id, default_base_ime, default_pain_type)
    new_base_ime = max(default_base_ime * 0.5, min(default_base_ime * 2.0,
                                                     current['base_ime'] + base_ime_adjustment))
    new_pain_type = max(0, min(10, current['pain_type'] + pain_type_adjustment))

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO learning_procedures (procedure_id, base_ime, pain_type, total_cases)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, procedure_id, new_base_ime, new_pain_type, current['total_cases'] + 1))
            conn.commit()
            return {'base_ime': new_base_ime, 'pain_type': new_pain_type}
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in update_procedure_learning: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in update_procedure_learning: {e}")
        raise

# ============ Learning system - adjuvant learning ============

def get_adjuvant_selectivity(adjuvant_name: str, procedure_pain_type: float, default_selectivity: float) -> float:
    """
    Hämta inlärd selektivitet för ett adjuvant (GLOBAL för alla användare).

    Args:
        adjuvant_name: Name of the adjuvant
        procedure_pain_type: Pain type of the procedure (for compatibility)
        default_selectivity: Default value if not learned

    Returns:
        Learned or default selectivity value
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT selectivity FROM learning_adjuvants
                WHERE adjuvant_name = ?
            ''', (adjuvant_name,))
            row = cursor.fetchone()
            return row['selectivity'] if row else default_selectivity
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_adjuvant_selectivity: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_adjuvant_selectivity: {e}")
        raise

def get_adjuvant_potency(adjuvant_name: str, procedure_pain_type: float, default_potency: float) -> float:
    """
    Hämta inlärd potens för ett adjuvant (GLOBAL för alla användare).

    Args:
        adjuvant_name: Name of the adjuvant
        procedure_pain_type: Pain type of the procedure (for compatibility)
        default_potency: Default value if not learned

    Returns:
        Learned or default potency value
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT potency FROM learning_adjuvants
                WHERE adjuvant_name = ?
            ''', (adjuvant_name,))
            row = cursor.fetchone()
            return row['potency'] if row else default_potency
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_adjuvant_potency: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_adjuvant_potency: {e}")
        raise

def update_adjuvant_learning(adjuvant_name: str, selectivity_adj: float, potency_adj: float):
    """
    Uppdatera adjuvant inlärning (GLOBAL för alla användare).

    Args:
        adjuvant_name: Name of the adjuvant
        selectivity_adj: Adjustment to selectivity value
        potency_adj: Adjustment to potency value
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Hämta nuvarande värden
            cursor.execute('''
                SELECT selectivity, potency, total_uses FROM learning_adjuvants
                WHERE adjuvant_name = ?
            ''', (adjuvant_name,))
            row = cursor.fetchone()
            if row:
                new_selectivity = max(0, min(10, row['selectivity'] + selectivity_adj))
                new_potency = max(0, row['potency'] + potency_adj)
                new_uses = row['total_uses'] + 1
            else:
                new_selectivity = 5 + selectivity_adj
                new_potency = 5 + potency_adj
                new_uses = 1
            cursor.execute('''
                INSERT OR REPLACE INTO learning_adjuvants (adjuvant_name, selectivity, potency, total_uses)
                VALUES (?, ?, ?, ?)
            ''', (adjuvant_name, new_selectivity, new_potency, new_uses))
            conn.commit()
            logger.info(f"Updated global learning for {adjuvant_name}: selectivity={new_selectivity:.2f}, potency={new_potency:.2f}, uses={new_uses}")
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in update_adjuvant_learning: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in update_adjuvant_learning: {e}")
        raise

# ============ Learning system - synergy ============

def get_drug_combination_key(inputs: Dict) -> str:
    """Generera en nyckel för läkemedelskombination"""
    drugs = []
    if inputs.get('nsaid') and inputs.get('nsaid_choice') != 'Ej given':
        drugs.append('NSAID')
    if inputs.get('catapressan_dose', 0) > 0:
        drugs.append('Catapressan')
    if inputs.get('droperidol'):
        drugs.append('Droperidol')
    if inputs.get('ketamine_choice') and inputs['ketamine_choice'] != 'Ej given':
        drugs.append('Ketamine')
    if inputs.get('lidocaine') and inputs['lidocaine'] != 'Nej':
        drugs.append('Lidocaine')
    if inputs.get('betapred') and inputs['betapred'] != 'Nej':
        drugs.append('Betapred')

    if len(drugs) < 2:
        return None

    return '+'.join(sorted(drugs))

def get_synergy_factor(drug_combo: str) -> float:
    """Hämta synergifaktor för läkemedelskombination (GLOBAL)"""
    if not drug_combo:
        return 1.0

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_synergy (
                    drug_combo TEXT PRIMARY KEY,
                    synergy_factor REAL DEFAULT 1.0
                )
            ''')
            cursor.execute('''
                SELECT synergy_factor FROM learning_synergy
                WHERE drug_combo = ?
            ''', (drug_combo,))
            row = cursor.fetchone()
            return row['synergy_factor'] if row else 1.0
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_synergy_factor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_synergy_factor: {e}")
        raise

def update_synergy_factor(drug_combo: str, adjustment: float) -> float:
    """Uppdatera synergifaktor (GLOBAL)"""
    if not drug_combo or adjustment == 0:
        return 1.0

    current = get_synergy_factor(drug_combo)
    new_factor = max(0.5, min(1.5, current + adjustment))

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO learning_synergy (drug_combo, synergy_factor)
                VALUES (?, ?)
            ''', (drug_combo, new_factor))
            conn.commit()
            return new_factor
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in update_synergy_factor: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in update_synergy_factor: {e}")
        raise

# ============ Learning system - fentanyl kinetics ============

def get_fentanyl_remaining_fraction(user_id=None) -> float:
    """Hämta fentanyl remaining fraction"""
    if not user_id:
        return 0.25

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_fentanyl (
                    user_id INTEGER PRIMARY KEY,
                    remaining_fraction REAL DEFAULT 0.25
                )
            ''')
            cursor.execute('SELECT remaining_fraction FROM learning_fentanyl WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return row['remaining_fraction'] if row else 0.25
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_fentanyl_remaining_fraction: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_fentanyl_remaining_fraction: {e}")
        raise

def update_fentanyl_remaining_fraction(user_id: int, adjustment: float) -> float:
    """Uppdatera fentanyl remaining fraction"""
    if not user_id or adjustment == 0:
        return 0.25

    current = get_fentanyl_remaining_fraction()
    new_fraction = max(0.1, min(0.5, current + adjustment))

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO learning_fentanyl (user_id, remaining_fraction)
                VALUES (?, ?)
            ''', (user_id, new_fraction))
            conn.commit()
            return new_fraction
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in update_fentanyl_remaining_fraction: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in update_fentanyl_remaining_fraction: {e}")
        raise# =================================================================
# LÄGG TILL DESSA FUNKTIONER I SLUTET AV database.py
# =================================================================

def get_all_users() -> List[Dict]:
    """Hämta alla användare"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_all_users: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_all_users: {e}")
        raise

def delete_user(user_id: int):
    """Radera en användare (endast för admin via UI)"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Radera användaren
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in delete_user: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in delete_user: {e}")
        raise

# ============ App Settings (för ML Target VAS, etc.) ============

def get_setting(key: str, default_value=None):
    """Hämta en app-inställning"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Skapa settings-tabell om den inte finns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    last_modified_by INTEGER,
                    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('SELECT value FROM app_settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            if row:
                # Försök konvertera till float om det ser ut som ett nuimer
                try:
                    return float(row['value'])
                except (ValueError, TypeError):
                    return row['value']
            return default_value
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_setting: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_setting: {e}")
        raise

def save_setting(key: str, value, user_id: int = None):
    """Spara en app-inställning"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO app_settings (key, value, last_modified_by, last_modified)
                VALUES (?, ?, ?, ?)
            ''', (key, str(value), user_id, datetime.now().isoformat()))
            conn.commit()
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in save_setting: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in save_setting: {e}")
        raise

def get_all_settings() -> List[Dict]:
    """Hämta alla app-inställningar"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM app_settings ORDER BY key')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_all_settings: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_all_settings: {e}")
        raise

# ============ Temporal Dosing ============

def save_temporal_doses(case_id: int, temporal_doses: List[Dict]):
    """
    Spara temporal doser för ett fall med batch insert för bättre prestanda.

    Args:
        case_id: ID för det fall som doserna hör till
        temporal_doses: Lista med dos-dictionaries
    """
    if not temporal_doses:
        return

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Förbered data för batch insert
            batch_data = [
                (
                    case_id,
                    dose_entry['drug_type'],
                    dose_entry['drug_name'],
                    dose_entry['dose'],
                    dose_entry['unit'],
                    dose_entry['time_relative_minutes'],
                    dose_entry.get('administration_route', 'IV'),
                    dose_entry.get('notes', '')
                )
                for dose_entry in temporal_doses
            ]

            # Batch insert - mycket snabbare än loop
            cursor.executemany('''
                INSERT INTO temporal_doses (
                    case_id, drug_type, drug_name, dose, unit,
                    time_relative_minutes, administration_route, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', batch_data)

            conn.commit()
            logger.info(f"Saved {len(temporal_doses)} temporal doses for case {case_id}")

    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in save_temporal_doses: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in save_temporal_doses: {e}")
        raise

def get_temporal_doses(case_id: int) -> List[Dict]:
    """Hämta temporal doser för ett fall"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM temporal_doses
                WHERE case_id = ?
                ORDER BY time_relative_minutes ASC
            ''', (case_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_temporal_doses: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_temporal_doses: {e}")
        raise

def delete_temporal_dose(dose_id: int):
    """Radera en temporal dos"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM temporal_doses WHERE id = ?', (dose_id,))
            conn.commit()
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in delete_temporal_dose: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in delete_temporal_dose: {e}")
        raise

def get_all_temporal_doses_for_procedure(procedure_id: str, user_id: int = None) -> List[Dict]:
    """Hämta alla temporal doser för ett specifikt ingrepp (för ML training)"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute('''
                    SELECT td.* FROM temporal_doses td
                    JOIN cases c ON td.case_id = c.id
                    WHERE c.procedure_id = ? AND c.user_id = ? AND c.status = 'FINALIZED'
                    ORDER BY c.timestamp DESC, td.time_relative_minutes ASC
                ''', (procedure_id, user_id))
            else:
                cursor.execute('''
                    SELECT td.* FROM temporal_doses td
                    JOIN cases c ON td.case_id = c.id
                    WHERE c.procedure_id = ? AND c.status = 'FINALIZED'
                    ORDER BY c.timestamp DESC, td.time_relative_minutes ASC
                ''', (procedure_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_all_temporal_doses_for_procedure: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_all_temporal_doses_for_procedure: {e}")
        raise


# ============ Learning system - PERCENTAGE-BASED adjuvant learning (NEW in v5) ============

def get_adjuvant_potency_percent(adjuvant_name: str, default_potency_percent: float) -> float:
    """
    Hämta inlärd percentage-based potency för ett adjuvant (GLOBAL för alla användare).

    Args:
        adjuvant_name: Name of the adjuvant (e.g., 'ketamine_small_bolus')
        default_potency_percent: Default percentage reduction (0.0-1.0, e.g., 0.15 = 15%)

    Returns:
        Learned or default potency percentage
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT potency_percent FROM learning_adjuvants_percent
                WHERE adjuvant_name = ?
            ''', (adjuvant_name,))
            row = cursor.fetchone()
            return row['potency_percent'] if row else default_potency_percent
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_adjuvant_potency_percent: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_adjuvant_potency_percent: {e}")
        raise


def update_adjuvant_potency_percent(adjuvant_name: str, default_potency_percent: float,
                                    adjustment: float) -> float:
    """
    Uppdatera percentage-based adjuvant potency (GLOBAL för alla användare).

    Args:
        adjuvant_name: Name of the adjuvant
        default_potency_percent: Default percentage
        adjustment: Learning adjustment to apply (e.g., +0.02 = increase by 2%)

    Returns:
        New potency percentage after adjustment
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Hämta nuvarande värden
            cursor.execute('''
                SELECT potency_percent, total_uses FROM learning_adjuvants_percent
                WHERE adjuvant_name = ?
            ''', (adjuvant_name,))
            row = cursor.fetchone()

            if row:
                current_potency = row['potency_percent']
                current_uses = row['total_uses']
            else:
                current_potency = default_potency_percent
                current_uses = 0

            # Apply adjustment with bounds (0% to 50% reduction)
            new_potency = max(0.0, min(0.50, current_potency + adjustment))
            new_uses = current_uses + 1

            cursor.execute('''
                INSERT OR REPLACE INTO learning_adjuvants_percent
                (adjuvant_name, potency_percent, total_uses)
                VALUES (?, ?, ?)
            ''', (adjuvant_name, new_potency, new_uses))

            conn.commit()
            logger.info(
                f"Updated global adjuvant % learning for {adjuvant_name}: "
                f"potency={new_potency:.1%} (was {current_potency:.1%}), uses={new_uses}"
            )
            return new_potency

    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in update_adjuvant_potency_percent: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in update_adjuvant_potency_percent: {e}")
        raise


# ============ Learning system - 3D PAIN procedure learning (NEW in v6) ============

def get_procedure_learning_3d(procedure_id: str, default_base_ime: float,
                               default_pain_somatic: float, default_pain_visceral: float,
                               default_pain_neuropathic: float) -> Dict:
    """
    Hämta inlärd 3D pain data för ett ingrepp (GLOBAL för alla användare).

    Args:
        procedure_id: Procedure identifier
        default_base_ime: Default base IME requirement
        default_pain_somatic: Default somatic pain score (0-10)
        default_pain_visceral: Default visceral pain score (0-10)
        default_pain_neuropathic: Default neuropathic pain score (0-10)

    Returns:
        Dictionary with learned values or defaults
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT base_ime, pain_somatic, pain_visceral, pain_neuropathic, num_cases
                FROM learning_procedures
                WHERE procedure_id = ?
            ''', (procedure_id,))
            row = cursor.fetchone()

            if row:
                return {
                    'base_ime': row['base_ime'],
                    'pain_somatic': row['pain_somatic'],
                    'pain_visceral': row['pain_visceral'],
                    'pain_neuropathic': row['pain_neuropathic'],
                    'num_cases': row['num_cases']
                }
            else:
                return {
                    'base_ime': default_base_ime,
                    'pain_somatic': default_pain_somatic,
                    'pain_visceral': default_pain_visceral,
                    'pain_neuropathic': default_pain_neuropathic,
                    'num_cases': 0
                }
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in get_procedure_learning_3d: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_procedure_learning_3d: {e}")
        raise


def update_procedure_learning_3d(procedure_id: str, default_base_ime: float,
                                  default_pain_somatic: float, default_pain_visceral: float,
                                  default_pain_neuropathic: float,
                                  base_ime_adjustment: float,
                                  pain_somatic_adjustment: float,
                                  pain_visceral_adjustment: float,
                                  pain_neuropathic_adjustment: float) -> Dict:
    """
    Uppdatera 3D pain learning för ett ingrepp (GLOBAL för alla användare).

    Args:
        procedure_id: Procedure identifier
        default_base_ime: Default base IME
        default_pain_somatic/visceral/neuropathic: Default pain scores
        base_ime_adjustment: Adjustment to base IME
        pain_somatic/visceral/neuropathic_adjustment: Adjustments to pain dimensions

    Returns:
        Dictionary with new learned values
    """
    try:
        current = get_procedure_learning_3d(
            procedure_id, default_base_ime,
            default_pain_somatic, default_pain_visceral, default_pain_neuropathic
        )

        # Apply adjustments with bounds
        new_base_ime = max(
            default_base_ime * 0.5,
            min(default_base_ime * 2.0, current['base_ime'] + base_ime_adjustment)
        )
        new_pain_somatic = max(0, min(10, current['pain_somatic'] + pain_somatic_adjustment))
        new_pain_visceral = max(0, min(10, current['pain_visceral'] + pain_visceral_adjustment))
        new_pain_neuropathic = max(0, min(10, current['pain_neuropathic'] + pain_neuropathic_adjustment))
        new_num_cases = current['num_cases'] + 1

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO learning_procedures
                (procedure_id, base_ime, pain_somatic, pain_visceral, pain_neuropathic, num_cases)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (procedure_id, new_base_ime, new_pain_somatic, new_pain_visceral,
                   new_pain_neuropathic, new_num_cases))
            conn.commit()

            logger.info(
                f"Updated 3D procedure learning for {procedure_id}: "
                f"IME={new_base_ime:.1f}, somatic={new_pain_somatic:.1f}, "
                f"visceral={new_pain_visceral:.1f}, neuropathic={new_pain_neuropathic:.1f}, "
                f"cases={new_num_cases}"
            )

            return {
                'base_ime': new_base_ime,
                'pain_somatic': new_pain_somatic,
                'pain_visceral': new_pain_visceral,
                'pain_neuropathic': new_pain_neuropathic,
                'num_cases': new_num_cases
            }

    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error in update_procedure_learning_3d: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in update_procedure_learning_3d: {e}")
        raise


# ============ Explainability support functions ============

def get_similar_cases_count(
    procedure_id: str,
    age_range: tuple,
    weight_range: tuple
) -> int:
    """
    Count number of similar cases in database for confidence scoring.
    
    Args:
        procedure_id: Procedure ID to match
        age_range: (min_age, max_age) tuple
        weight_range: (min_weight, max_weight) tuple
    
    Returns:
        Number of similar cases
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM cases
                WHERE procedure_id = ?
                  AND age BETWEEN ? AND ?
                  AND weight BETWEEN ? AND ?
                  AND status = 'FINALIZED'
            ''', (procedure_id, age_range[0], age_range[1],
                  weight_range[0], weight_range[1]))
            
            result = cursor.fetchone()
            return result[0] if result else 0
    
    except Exception as e:
        logger.error(f"Error in get_similar_cases_count: {e}")
        return 0


# ============ NEW: Fine-grained Age Bucket Learning (every year) ============

def get_age_bucket_learning(age_bucket: int) -> Optional[Dict]:
    """
    Hämta inlärningsdata för specifik åldersbucket (varje år).

    Args:
        age_bucket: Ålder i år (0, 1, 2, ..., 120)

    Returns:
        Dict med 'age_factor' och 'num_observations', eller None
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT age_factor, num_observations
                FROM learning_age_buckets
                WHERE age_bucket = ?
            ''', (age_bucket,))
            row = cursor.fetchone()
            if row:
                return {
                    'age_factor': row['age_factor'],
                    'num_observations': row['num_observations']
                }
            return None
    except Exception as e:
        logger.debug(f"No data for age bucket {age_bucket}: {e}")
        return None


def update_age_bucket_learning(age_bucket: int, default_factor: float, adjustment: float) -> float:
    """
    Uppdatera åldersfaktor för specifik bucket (varje år).

    Args:
        age_bucket: Ålder i år
        default_factor: Default värde om ingen tidigare data finns
        adjustment: Justering att applicera

    Returns:
        Ny age_factor
    """
    if adjustment == 0:
        return default_factor

    # Hämta nuvarande faktor
    data = get_age_bucket_learning(age_bucket)
    if data:
        current_factor = data['age_factor']
        num_obs = data['num_observations']
    else:
        current_factor = default_factor
        num_obs = 0

    # Beräkna ny faktor med safety limits
    new_factor = max(0.3, min(2.0, current_factor + adjustment))
    new_num_obs = num_obs + 1

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO learning_age_buckets (age_bucket, age_factor, num_observations)
                VALUES (?, ?, ?)
            ''', (age_bucket, new_factor, new_num_obs))
            conn.commit()
            return new_factor
    except Exception as e:
        logger.error(f"Error updating age bucket {age_bucket}: {e}")
        raise


# ============ NEW: Fine-grained Weight Bucket Learning (every kg) ============

def get_weight_bucket_learning(weight_bucket: int) -> Optional[Dict]:
    """
    Hämta inlärningsdata för specifik viktbucket (varje kg).

    Args:
        weight_bucket: Vikt i kg (10, 11, 12, ..., 200)

    Returns:
        Dict med 'weight_factor' och 'num_observations', eller None
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT weight_factor, num_observations
                FROM learning_weight_buckets
                WHERE weight_bucket = ?
            ''', (weight_bucket,))
            row = cursor.fetchone()
            if row:
                return {
                    'weight_factor': row['weight_factor'],
                    'num_observations': row['num_observations']
                }
            return None
    except Exception as e:
        logger.debug(f"No data for weight bucket {weight_bucket}kg: {e}")
        return None


def update_weight_bucket_learning(weight_bucket: int, default_factor: float, adjustment: float) -> float:
    """
    Uppdatera viktfaktor för specifik bucket (varje kg).

    Args:
        weight_bucket: Vikt i kg
        default_factor: Default värde om ingen tidigare data finns
        adjustment: Justering att applicera

    Returns:
        Ny weight_factor
    """
    if adjustment == 0:
        return default_factor

    # Hämta nuvarande faktor
    data = get_weight_bucket_learning(weight_bucket)
    if data:
        current_factor = data['weight_factor']
        num_obs = data['num_observations']
    else:
        current_factor = default_factor
        num_obs = 0

    # Beräkna ny faktor med safety limits
    new_factor = max(0.5, min(2.0, current_factor + adjustment))
    new_num_obs = num_obs + 1

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO learning_weight_buckets (weight_bucket, weight_factor, num_observations)
                VALUES (?, ?, ?)
            ''', (weight_bucket, new_factor, new_num_obs))
            conn.commit()
            return new_factor
    except Exception as e:
        logger.error(f"Error updating weight bucket {weight_bucket}kg: {e}")
        raise
