"""
Database Migration System
=========================
Handles schema versioning and migrations.
"""

import sqlite3
import logging
from database import get_connection

logger = logging.getLogger(__name__)

# Current schema version
CURRENT_SCHEMA_VERSION = 8


def get_db_version() -> int:
    """Get current database schema version."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA user_version")
            version = cursor.fetchone()[0]
            return version
    except Exception as e:
        logger.error(f"Error getting database version: {e}")
        return 0


def set_db_version(version: int):
    """Set database schema version."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA user_version = {version}")
            conn.commit()
            logger.info(f"Database version set to {version}")
    except Exception as e:
        logger.error(f"Error setting database version: {e}")
        raise


def add_performance_indexes():
    """
    Add database indexes for frequently queried columns.
    This significantly improves query performance.
    """
    logger.info("Adding performance indexes to database...")

    indexes = [
        # Cases table indexes
        ("idx_cases_user_id", "cases", "user_id"),
        ("idx_cases_procedure_id", "cases", "procedure_id"),
        ("idx_cases_timestamp", "cases", "timestamp DESC"),
        ("idx_cases_user_procedure", "cases", "user_id, procedure_id"),

        # Temporal doses indexes
        ("idx_temporal_doses_case_id", "temporal_doses", "case_id"),
        ("idx_temporal_doses_time", "temporal_doses", "time_relative_minutes"),

        # Learning calibration indexes
        ("idx_learning_calib_user", "learning_calibration", "user_id"),

        # Users indexes
        ("idx_users_username", "users", "username"),
        ("idx_users_created", "users", "created_at DESC"),

        # Procedures indexes
        ("idx_procedures_specialty", "procedures", "specialty"),

        # Custom procedures indexes
        ("idx_custom_proc_specialty", "custom_procedures", "specialty"),
        ("idx_custom_proc_created", "custom_procedures", "created_at DESC"),
    ]

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            for index_name, table_name, columns in indexes:
                try:
                    cursor.execute(f'''
                        CREATE INDEX IF NOT EXISTS {index_name}
                        ON {table_name}({columns})
                    ''')
                    logger.info(f"Created index: {index_name}")
                except Exception as e:
                    logger.warning(f"Could not create index {index_name}: {e}")

            conn.commit()
            logger.info("Performance indexes added successfully")

    except Exception as e:
        logger.error(f"Error adding indexes: {e}")
        raise


def migrate_to_v1():
    """
    Migration to version 1: Add indexes and session tokens table.
    """
    logger.info("Running migration to version 1...")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Add session_tokens table for secure session management
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')

            # Add index for session tokens
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_session_tokens_token
                ON session_tokens(token)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_session_tokens_user
                ON session_tokens(user_id)
            ''')

            conn.commit()
            logger.info("Migration to version 1 completed")

    except Exception as e:
        logger.error(f"Error in migration to v1: {e}")
        raise


def migrate_to_v2():
    """
    Migration to version 2: Make adjuvant learning GLOBAL (remove user_id).

    This makes adjuvant effectiveness learning shared across all users,
    so everyone benefits from collective experience.
    """
    logger.info("Running migration to version 2: Making adjuvant learning global...")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Check if old table exists and has data
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='learning_adjuvants'
            """)
            table_exists = cursor.fetchone()

            if table_exists:
                # Get existing data
                cursor.execute("""
                    SELECT adjuvant_name,
                           AVG(selectivity) as avg_selectivity,
                           AVG(potency) as avg_potency,
                           SUM(total_uses) as total_uses
                    FROM learning_adjuvants
                    GROUP BY adjuvant_name
                """)
                aggregated_data = cursor.fetchall()

                # Drop old table
                cursor.execute("DROP TABLE learning_adjuvants")
                logger.info("Dropped old per-user learning_adjuvants table")

                # Create new global table (no user_id)
                cursor.execute('''
                    CREATE TABLE learning_adjuvants (
                        adjuvant_name TEXT PRIMARY KEY,
                        selectivity REAL,
                        potency REAL,
                        total_uses INTEGER DEFAULT 0
                    )
                ''')
                logger.info("Created new global learning_adjuvants table")

                # Migrate aggregated data
                if aggregated_data:
                    cursor.executemany('''
                        INSERT INTO learning_adjuvants (adjuvant_name, selectivity, potency, total_uses)
                        VALUES (?, ?, ?, ?)
                    ''', aggregated_data)
                    logger.info(f"Migrated {len(aggregated_data)} adjuvant learning entries (aggregated from all users)")
            else:
                # Table doesn't exist yet, just create the new one
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_adjuvants (
                        adjuvant_name TEXT PRIMARY KEY,
                        selectivity REAL,
                        potency REAL,
                        total_uses INTEGER DEFAULT 0
                    )
                ''')
                logger.info("Created new global learning_adjuvants table (no previous data)")

            conn.commit()
            logger.info("Migration to version 2 completed")

    except Exception as e:
        logger.error(f"Error in migration to v2: {e}")
        raise


def migrate_to_v3():
    """
    Migration to version 3: Replace weight category learning with 4D body composition.

    This replaces the old 3-category system (underweight, obese, very_obese) with
    continuous 4D learning across:
    - Actual weight (10kg buckets: 50-60, 60-70, etc.)
    - IBW ratio (0.1 increments: 0.8, 0.9, 1.0, 1.1, etc.)
    - ABW ratio (0.1 increments for overweight patients)
    - BMI (7 categories: 16, 19, 22, 27, 32, 37, 42)

    This allows learning across the full spectrum from super skinny to morbidly obese.
    """
    logger.info("Running migration to version 3: Replacing weight categories with 4D body composition...")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Check if old table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='learning_weight_factors'
            """)
            old_table_exists = cursor.fetchone()

            if old_table_exists:
                logger.info("Dropping old learning_weight_factors table (3-category system)")
                cursor.execute("DROP TABLE learning_weight_factors")

            # Create new 4D body composition table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_body_composition (
                    user_id INTEGER NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    composition_factor REAL DEFAULT 1.0,
                    num_observations INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, metric_type, metric_value),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            logger.info("Created new learning_body_composition table (4D continuous learning)")

            # Add index for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_body_comp_user_metric
                ON learning_body_composition(user_id, metric_type)
            ''')

            conn.commit()
            logger.info("Migration to version 3 completed")
            logger.info("Body composition learning now supports: weight, ibw_ratio, abw_ratio, bmi")

    except Exception as e:
        logger.error(f"Error in migration to v3: {e}")
        raise


def migrate_to_v4():
    """
    Migration to version 4: Make ALL learning GLOBAL (remove user_id).

    Philosophy: Learning should benefit everyone. user_id is only for:
    - Authentication (who can log in)
    - Case ownership (who created this case, for editing/deleting)
    - Data cleanup (delete problematic user's cases)

    All learning tables become global:
    - Procedures learn from everyone
    - Patient factors (age, sex, body composition, ASA, renal) learn from everyone
    - Adjuvants already global (v2)
    - Synergies learn from everyone
    - Fentanyl kinetics learn from everyone
    """
    logger.info("Running migration to version 4: Making ALL learning GLOBAL...")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # 1. PROCEDURES - Aggregate by procedure_id
            logger.info("Making procedure learning global...")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_procedures'")
            if cursor.fetchone():
                # Check if num_cases column exists
                cursor.execute("PRAGMA table_info(learning_procedures)")
                columns = [row[1] for row in cursor.fetchall()]
                has_num_cases = 'num_cases' in columns

                # Get aggregated data
                if has_num_cases:
                    cursor.execute("""
                        SELECT procedure_id,
                               AVG(base_ime) as avg_base_ime,
                               AVG(pain_type) as avg_pain_type,
                               SUM(COALESCE(num_cases, 0)) as total_cases
                        FROM learning_procedures
                        GROUP BY procedure_id
                    """)
                else:
                    cursor.execute("""
                        SELECT procedure_id,
                               AVG(base_ime) as avg_base_ime,
                               AVG(pain_type) as avg_pain_type,
                               0 as total_cases
                        FROM learning_procedures
                        GROUP BY procedure_id
                    """)
                proc_data = cursor.fetchall()

                cursor.execute("DROP TABLE learning_procedures")
                cursor.execute('''
                    CREATE TABLE learning_procedures (
                        procedure_id TEXT PRIMARY KEY,
                        base_ime REAL,
                        pain_type REAL,
                        num_cases INTEGER DEFAULT 0
                    )
                ''')

                if proc_data:
                    cursor.executemany('''
                        INSERT INTO learning_procedures (procedure_id, base_ime, pain_type, num_cases)
                        VALUES (?, ?, ?, ?)
                    ''', proc_data)
                    logger.info(f"Migrated {len(proc_data)} procedure learning entries (aggregated from all users)")

            # 2. AGE FACTORS - Aggregate by age_group
            logger.info("Making age factor learning global...")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_age_factors'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT age_group,
                           AVG(age_factor) as avg_factor,
                           COUNT(*) as total_obs
                    FROM learning_age_factors
                    GROUP BY age_group
                """)
                age_data = cursor.fetchall()

                cursor.execute("DROP TABLE learning_age_factors")
                cursor.execute('''
                    CREATE TABLE learning_age_factors (
                        age_group TEXT PRIMARY KEY,
                        age_factor REAL DEFAULT 1.0,
                        num_observations INTEGER DEFAULT 0
                    )
                ''')

                if age_data:
                    cursor.executemany('''
                        INSERT INTO learning_age_factors (age_group, age_factor, num_observations)
                        VALUES (?, ?, ?)
                    ''', age_data)
                    logger.info(f"Migrated {len(age_data)} age factor entries (aggregated from all users)")

            # 3. SEX FACTORS - Aggregate by sex
            logger.info("Making sex factor learning global...")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_sex_factors'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT sex,
                           AVG(sex_factor) as avg_factor,
                           COUNT(*) as total_obs
                    FROM learning_sex_factors
                    GROUP BY sex
                """)
                sex_data = cursor.fetchall()

                cursor.execute("DROP TABLE learning_sex_factors")
                cursor.execute('''
                    CREATE TABLE learning_sex_factors (
                        sex TEXT PRIMARY KEY,
                        sex_factor REAL DEFAULT 1.0,
                        num_observations INTEGER DEFAULT 0
                    )
                ''')

                if sex_data:
                    cursor.executemany('''
                        INSERT INTO learning_sex_factors (sex, sex_factor, num_observations)
                        VALUES (?, ?, ?)
                    ''', sex_data)
                    logger.info(f"Migrated {len(sex_data)} sex factor entries (aggregated from all users)")

            # 4. BODY COMPOSITION - Aggregate by metric_type and metric_value
            logger.info("Making body composition learning global...")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_body_composition'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT metric_type, metric_value,
                           AVG(composition_factor) as avg_factor,
                           SUM(num_observations) as total_obs
                    FROM learning_body_composition
                    GROUP BY metric_type, metric_value
                """)
                body_data = cursor.fetchall()

                cursor.execute("DROP TABLE learning_body_composition")
                cursor.execute('''
                    CREATE TABLE learning_body_composition (
                        metric_type TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        composition_factor REAL DEFAULT 1.0,
                        num_observations INTEGER DEFAULT 0,
                        PRIMARY KEY (metric_type, metric_value)
                    )
                ''')

                if body_data:
                    cursor.executemany('''
                        INSERT INTO learning_body_composition (metric_type, metric_value, composition_factor, num_observations)
                        VALUES (?, ?, ?, ?)
                    ''', body_data)
                    logger.info(f"Migrated {len(body_data)} body composition entries (aggregated from all users)")

            # 5. ASA FACTORS - Aggregate by asa_class
            logger.info("Making ASA factor learning global...")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_asa_factors'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT asa_class,
                           AVG(asa_factor) as avg_factor,
                           COUNT(*) as total_obs
                    FROM learning_asa_factors
                    GROUP BY asa_class
                """)
                asa_data = cursor.fetchall()

                cursor.execute("DROP TABLE learning_asa_factors")
                cursor.execute('''
                    CREATE TABLE learning_asa_factors (
                        asa_class TEXT PRIMARY KEY,
                        asa_factor REAL DEFAULT 1.0,
                        num_observations INTEGER DEFAULT 0
                    )
                ''')

                if asa_data:
                    cursor.executemany('''
                        INSERT INTO learning_asa_factors (asa_class, asa_factor, num_observations)
                        VALUES (?, ?, ?)
                    ''', asa_data)
                    logger.info(f"Migrated {len(asa_data)} ASA factor entries (aggregated from all users)")

            # 6. SYNERGY - Aggregate by drug_combo
            logger.info("Making synergy learning global...")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_synergy'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT drug_combo,
                           AVG(synergy_factor) as avg_factor,
                           COUNT(*) as total_uses
                    FROM learning_synergy
                    GROUP BY drug_combo
                """)
                synergy_data = cursor.fetchall()

                cursor.execute("DROP TABLE learning_synergy")
                cursor.execute('''
                    CREATE TABLE learning_synergy (
                        drug_combo TEXT PRIMARY KEY,
                        synergy_factor REAL DEFAULT 1.0,
                        num_uses INTEGER DEFAULT 0
                    )
                ''')

                if synergy_data:
                    cursor.executemany('''
                        INSERT INTO learning_synergy (drug_combo, synergy_factor, num_uses)
                        VALUES (?, ?, ?)
                    ''', synergy_data)
                    logger.info(f"Migrated {len(synergy_data)} synergy entries (aggregated from all users)")

            # 7. RENAL FACTOR - Single global value (average all users)
            logger.info("Making renal factor learning global...")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_renal_factor'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT AVG(renal_factor) as avg_factor,
                           COUNT(*) as total_obs
                    FROM learning_renal_factor
                """)
                renal_data = cursor.fetchone()

                cursor.execute("DROP TABLE learning_renal_factor")
                cursor.execute('''
                    CREATE TABLE learning_renal_factor (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        renal_factor REAL DEFAULT 0.75,
                        num_observations INTEGER DEFAULT 0
                    )
                ''')

                if renal_data and renal_data[0]:
                    cursor.execute('''
                        INSERT INTO learning_renal_factor (id, renal_factor, num_observations)
                        VALUES (1, ?, ?)
                    ''', renal_data)
                    logger.info(f"Migrated renal factor: {renal_data[0]:.3f} (aggregated from all users)")

            # 8. OPIOID TOLERANCE - Single global value
            logger.info("Making opioid tolerance learning global...")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_opioid_tolerance'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT AVG(tolerance_factor) as avg_factor,
                           COUNT(*) as total_obs
                    FROM learning_opioid_tolerance
                """)
                tolerance_data = cursor.fetchone()

                cursor.execute("DROP TABLE learning_opioid_tolerance")
                cursor.execute('''
                    CREATE TABLE learning_opioid_tolerance (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        tolerance_factor REAL DEFAULT 1.5,
                        num_observations INTEGER DEFAULT 0
                    )
                ''')

                if tolerance_data and tolerance_data[0]:
                    cursor.execute('''
                        INSERT INTO learning_opioid_tolerance (id, tolerance_factor, num_observations)
                        VALUES (1, ?, ?)
                    ''', tolerance_data)
                    logger.info(f"Migrated opioid tolerance: {tolerance_data[0]:.3f} (aggregated from all users)")

            # 9. PAIN THRESHOLD - Single global value
            logger.info("Making pain threshold learning global...")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_pain_threshold'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT AVG(threshold_factor) as avg_factor,
                           COUNT(*) as total_obs
                    FROM learning_pain_threshold
                """)
                threshold_data = cursor.fetchone()

                cursor.execute("DROP TABLE learning_pain_threshold")
                cursor.execute('''
                    CREATE TABLE learning_pain_threshold (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        threshold_factor REAL DEFAULT 1.2,
                        num_observations INTEGER DEFAULT 0
                    )
                ''')

                if threshold_data and threshold_data[0]:
                    cursor.execute('''
                        INSERT INTO learning_pain_threshold (id, threshold_factor, num_observations)
                        VALUES (1, ?, ?)
                    ''', threshold_data)
                    logger.info(f"Migrated pain threshold: {threshold_data[0]:.3f} (aggregated from all users)")

            # 10. FENTANYL - Single global value
            logger.info("Making fentanyl kinetics learning global...")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_fentanyl'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT AVG(remaining_fraction) as avg_fraction,
                           COUNT(*) as total_obs
                    FROM learning_fentanyl
                """)
                fentanyl_data = cursor.fetchone()

                cursor.execute("DROP TABLE learning_fentanyl")
                cursor.execute('''
                    CREATE TABLE learning_fentanyl (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        remaining_fraction REAL DEFAULT 0.25,
                        num_observations INTEGER DEFAULT 0
                    )
                ''')

                if fentanyl_data and fentanyl_data[0]:
                    cursor.execute('''
                        INSERT INTO learning_fentanyl (id, remaining_fraction, num_observations)
                        VALUES (1, ?, ?)
                    ''', fentanyl_data)
                    logger.info(f"Migrated fentanyl kinetics: {fentanyl_data[0]:.3f} (aggregated from all users)")

            conn.commit()
            logger.info("=" * 80)
            logger.info("Migration to version 4 completed successfully!")
            logger.info("ALL LEARNING IS NOW GLOBAL - Everyone benefits from collective knowledge!")
            logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Error in migration to v4: {e}")
        raise


def migrate_to_v5():
    """
    Migration to version 5: Add percentage-based adjuvant learning.

    This replaces the old IME-based adjuvant learning with a percentage-based system
    that properly scales with patient weight and procedure requirements.

    Table structure:
    - adjuvant_name: Drug identifier (e.g., 'ketamine_small_bolus')
    - potency_percent: Learned percentage reduction (0.0-1.0, e.g., 0.15 = 15% reduction)
    - total_uses: Number of times this adjuvant was used (for weighted learning)
    """
    logger.info("Running migration to version 5: Adding percentage-based adjuvant learning...")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Drop old IME-based table if it exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_adjuvants'")
            if cursor.fetchone():
                logger.info("Dropping old IME-based learning_adjuvants table")
                cursor.execute("DROP TABLE learning_adjuvants")

            # Create new percentage-based table (global learning)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_adjuvants_percent (
                    adjuvant_name TEXT PRIMARY KEY,
                    potency_percent REAL DEFAULT 0.15,
                    total_uses INTEGER DEFAULT 0
                )
            ''')
            logger.info("Created new learning_adjuvants_percent table (percentage-based, global)")

            # Add index for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_adjuvants_percent_name
                ON learning_adjuvants_percent(adjuvant_name)
            ''')

            conn.commit()
            logger.info("Migration to version 5 completed")
            logger.info("Adjuvant learning now uses percentage-based reductions (scales properly)")

    except Exception as e:
        logger.error(f"Error in migration to v5: {e}")
        raise


def migrate_to_v6():
    """
    Migration to version 6: Add 3D pain learning to procedures.

    This extends procedure learning from 1D (somatic pain only) to 3D
    (somatic + visceral + neuropathic pain dimensions).

    Changes:
    - Rename existing 'pain_type' column to 'pain_somatic'
    - Add 'pain_visceral' column (default 5.0)
    - Add 'pain_neuropathic' column (default 2.0)

    This allows procedures to learn the optimal pain profile across all 3 dimensions
    based on actual patient outcomes.
    """
    logger.info("Running migration to version 6: Adding 3D pain learning to procedures...")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Check if table exists and needs migration
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_procedures'")
            if cursor.fetchone():
                # Get existing data
                cursor.execute("SELECT procedure_id, base_ime, pain_type, num_cases FROM learning_procedures")
                existing_data = cursor.fetchall()

                # Drop old table
                cursor.execute("DROP TABLE learning_procedures")
                logger.info("Dropped old 1D learning_procedures table")

                # Create new 3D table
                cursor.execute('''
                    CREATE TABLE learning_procedures (
                        procedure_id TEXT PRIMARY KEY,
                        base_ime REAL,
                        pain_somatic REAL DEFAULT 5.0,
                        pain_visceral REAL DEFAULT 5.0,
                        pain_neuropathic REAL DEFAULT 2.0,
                        num_cases INTEGER DEFAULT 0
                    )
                ''')
                logger.info("Created new 3D learning_procedures table")

                # Migrate existing data (pain_type → pain_somatic, add defaults for visceral/neuropathic)
                if existing_data:
                    migrated_data = [
                        (proc_id, base_ime, pain_type, 5.0, 2.0, num_cases)
                        for proc_id, base_ime, pain_type, num_cases in existing_data
                    ]
                    cursor.executemany('''
                        INSERT INTO learning_procedures
                        (procedure_id, base_ime, pain_somatic, pain_visceral, pain_neuropathic, num_cases)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', migrated_data)
                    logger.info(f"Migrated {len(migrated_data)} procedure entries to 3D pain learning")
            else:
                # Table doesn't exist, create new one
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_procedures (
                        procedure_id TEXT PRIMARY KEY,
                        base_ime REAL,
                        pain_somatic REAL DEFAULT 5.0,
                        pain_visceral REAL DEFAULT 5.0,
                        pain_neuropathic REAL DEFAULT 2.0,
                        num_cases INTEGER DEFAULT 0
                    )
                ''')
                logger.info("Created new 3D learning_procedures table (no previous data)")

            # Add index for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_procedures_id
                ON learning_procedures(procedure_id)
            ''')

            conn.commit()
            logger.info("Migration to version 6 completed")
            logger.info("Procedure learning now supports 3D pain profiles (somatic/visceral/neuropathic)")

    except Exception as e:
        logger.error(f"Error in migration to v6: {e}")
        raise


def migrate_to_v7():
    """
    Migration to version 7: Fine-grained Age & Weight Buckets with Interpolation

    Changes:
    - Creates learning_age_buckets table (every year: 0-120+)
    - Creates learning_weight_buckets table (every kg: 10-200+)
    - Migrates data from old learning_age_factors (groups) to new buckets
    """
    logger.info("Running migration to version 7: Fine-grained Age & Weight Buckets")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # 1. Create learning_age_buckets table (replaces learning_age_factors groups)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_age_buckets (
                    age_bucket INTEGER PRIMARY KEY,
                    age_factor REAL NOT NULL DEFAULT 1.0,
                    num_observations INTEGER DEFAULT 0
                )
            ''')
            logger.info("Created learning_age_buckets table (fine-grained: every year)")

            # 2. Migrate data from old age groups to new buckets
            # Map old groups to representative ages
            age_group_mapping = {
                '<18': list(range(0, 18)),      # 0-17 years
                '18-39': list(range(18, 40)),   # 18-39 years
                '40-64': list(range(40, 65)),   # 40-64 years
                '65-79': list(range(65, 80)),   # 65-79 years
                '80+': list(range(80, 121))     # 80-120 years
            }

            cursor.execute('SELECT * FROM learning_age_factors')
            old_age_data = cursor.fetchall()

            if old_age_data:
                logger.info(f"Migrating {len(old_age_data)} age group(s) to fine-grained buckets...")
                for row in old_age_data:
                    age_group = row['age_group']
                    age_factor = row['age_factor']
                    num_obs = row['num_observations']

                    # Distribute this group's data to all ages in range
                    if age_group in age_group_mapping:
                        ages = age_group_mapping[age_group]
                        # Distribute observations across ages (integer division)
                        obs_per_age = max(1, num_obs // len(ages))

                        for age in ages:
                            cursor.execute('''
                                INSERT OR IGNORE INTO learning_age_buckets
                                (age_bucket, age_factor, num_observations)
                                VALUES (?, ?, ?)
                            ''', (age, age_factor, obs_per_age))

                        logger.info(f"Migrated age group '{age_group}' -> {len(ages)} individual buckets")
            else:
                logger.info("No previous age group data to migrate")

            # 3. Create learning_weight_buckets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_weight_buckets (
                    weight_bucket INTEGER PRIMARY KEY,
                    weight_factor REAL NOT NULL DEFAULT 1.0,
                    num_observations INTEGER DEFAULT 0
                )
            ''')
            logger.info("Created learning_weight_buckets table (fine-grained: every kg)")

            # 4. Add indexes for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_age_buckets
                ON learning_age_buckets(age_bucket)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_weight_buckets
                ON learning_weight_buckets(weight_bucket)
            ''')

            conn.commit()
            logger.info("Migration to version 7 completed")
            logger.info("System now supports:")
            logger.info("  - Fine-grained age learning (every year)")
            logger.info("  - Fine-grained weight learning (every kg)")
            logger.info("  - Intelligent interpolation from nearby data points")

    except Exception as e:
        logger.error(f"Error in migration to v7: {e}")
        raise


def migrate_to_v8():
    """
    Migration to version 8: Rename baseMME to baseIME.
    """
    logger.info("Running migration to version 8: Renaming baseMME to baseIME...")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Rename in procedures table
            try:
                cursor.execute("ALTER TABLE procedures RENAME COLUMN baseMME TO baseIME")
                logger.info("Renamed procedures.baseMME to procedures.baseIME")
            except sqlite3.OperationalError as e:
                if "no such column" in str(e).lower() or "duplicate column" in str(e).lower():
                    logger.warning("Column procedures.baseMME does not exist or already renamed, skipping.")
                else:
                    raise

            # Rename in custom_procedures table
            try:
                cursor.execute("ALTER TABLE custom_procedures RENAME COLUMN baseMME TO baseIME")
                logger.info("Renamed custom_procedures.baseMME to custom_procedures.baseIME")
            except sqlite3.OperationalError as e:
                if "no such column" in str(e).lower() or "duplicate column" in str(e).lower():
                    logger.warning("Column custom_procedures.baseMME does not exist or already renamed, skipping.")
                else:
                    raise

            conn.commit()
            logger.info("Migration to version 8 completed")

    except Exception as e:
        logger.error(f"Error in migration to v8: {e}")
        raise


def run_migrations():
    """
    Run all pending migrations.
    """
    current_version = get_db_version()
    logger.info(f"Current database version: {current_version}")
    logger.info(f"Target database version: {CURRENT_SCHEMA_VERSION}")

    if current_version == CURRENT_SCHEMA_VERSION:
        logger.info("Database is up to date")
        # Still add indexes if they don't exist
        add_performance_indexes()
        return

    # Run migrations in sequence
    if current_version < 1:
        migrate_to_v1()
        add_performance_indexes()
        set_db_version(1)

    if current_version < 2:
        migrate_to_v2()
        set_db_version(2)

    if current_version < 3:
        migrate_to_v3()
        set_db_version(3)

    if current_version < 4:
        migrate_to_v4()
        set_db_version(4)

    if current_version < 5:
        migrate_to_v5()
        set_db_version(5)

    if current_version < 6:
        migrate_to_v6()
        set_db_version(6)

    if current_version < 7:
        migrate_to_v7()
        set_db_version(7)

    if current_version < 8:
        migrate_to_v8()
        set_db_version(8)

    logger.info(f"Migrations completed. Database now at version {CURRENT_SCHEMA_VERSION}")


def create_backup():
    """
    Create a backup of the database before migrations.
    """
    import shutil
    from datetime import datetime

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"anestesi_backup_{timestamp}.db"
        shutil.copy2("anestesi.db", backup_path)
        logger.info(f"Database backup created: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise
