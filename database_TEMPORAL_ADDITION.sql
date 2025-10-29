-- =================================================================
-- TEMPORAL DOSERING - Lägg till detta i init_database() i database.py
-- Efter custom_procedures tabell (ca rad 142)
-- =================================================================

-- Temporal doses table
CREATE TABLE IF NOT EXISTS temporal_doses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    drug_type TEXT NOT NULL,              -- 'fentanyl', 'nsaid', 'catapressan', 'ketamine', 'lidocaine', 'betapred', 'droperidol', 'oxycodone'
    drug_name TEXT NOT NULL,              -- 'Fentanyl', 'Ibuprofen 400mg', 'Catapressan 75µg', etc.
    dose REAL NOT NULL,                   -- Dos i enheten för läkemedlet
    unit TEXT NOT NULL,                   -- 'mcg', 'mg'
    time_relative_minutes INTEGER NOT NULL,  -- Minuter relativt opslut (negativ = före, positiv = efter)
    administration_route TEXT DEFAULT 'IV',  -- 'IV', 'PO', 'IM', 'SC'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
);

-- Lägg även till i cases-tabellen (kör som ALTER TABLE om redan exister):
-- ALTER TABLE cases ADD COLUMN opslut_timestamp TIMESTAMP;
-- ALTER TABLE cases ADD COLUMN op_duration_minutes INTEGER;
