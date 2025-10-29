# Rapport: Kritiska Fixes - Framsteg och Kvarvarande Arbete
**Datum:** 2025-10-12
**Status:** ⚠️ PÅGÅENDE - 30% Klart

## ✅ GENOMFÖRT

### 1. ✅ Unified LÄKEMEDELS_DATA Skapad
**Fil:** `config.py` (backup: `config_OLD_BACKUP.py`)

**Vad som gjorts:**
- Skapade ny unified struktur `LÄKEMEDELS_DATA` med ALL farmakologisk data
- Implementerade 3D pain scores (somatic/visceral/neuropathic) för ALLA läkemedel
- Lade till `ML_TARGET_VAS` som admin-justerbar parameter
- Lade till `ML_SAFETY_MAX_DOSE` och `ML_SAFETY_MIN_DOSE`
- Skapade hjälpfunktioner:
  - `get_drug_by_ui_choice()` - Hämta läkemedel via UI-val
  - `get_drug()` - Hämta läkemedel via nyckel
  - `calculate_composite_pain_score()` - Beräkna sammansatt smärtprofil
  - `calculate_3d_mismatch_penalty()` - Beräkna 3D mismatch med Euclidean distance

**Läkemedel inkluderade:**
- NSAIDs: Ibuprofen, Ketorolac, Parecoxib (med potency och 3D scores)
- Alpha-2 agonister: Clonidine/Catapressan (dosbaserad)
- NMDA-antagonister: 4 ketamin-varianter (med neuropatisk effekt 9/10)
- Natriumkanalblockerare: Lidokain bolus/infusion
- Kortikosteroider: Betapred 4mg/8mg
- Neuroleptika: Droperidol
- Volatila: Sevoflurane
- Regional: Infiltrationsanestesi

### 2. ✅ Ny Regelmotor Skapad
**Fil:** `calculation_engine_NEW.py`

**Vad som gjorts:**
- Refaktorerade HELA adjuvant-hanteringen för att använda `LÄKEMEDELS_DATA`
- Implementerade `apply_learnable_adjuvant()` med 3D pain matching
- Lade till `calculate_bmi()` som centraliserad funktion
- Uppdaterade `_apply_adjuvants()` för unified data source
- Alla läkemedel hämtas nu från config.py via helper-funktioner

**KVAR:** Ersätt gamla `calculation_engine.py` med den nya versionen

## ⚠️ KRITISKT KVARST ÅENDE ARBETE

### 3. ⚠️ ML-Motor Måste Synkroniseras
**Fil:** `ml_model.py`
**Status:** EJ PÅBÖRJAD

**Vad som måste göras:**
```python
# I ml_model.py, ersätt:
# OLD: selectivities.append(pc.MEDICATIONS.get('ibuprofen', {}).get('painSelectivity', 5))
# NEW: drug = get_drug_by_ui_choice('nsaid', row.get('nsaid_choice'))
#      selectivities.append(drug['somatic_score'])
```

**Ändringar krävda:**
1. Importera från config: `from config import LÄKEMEDELS_DATA, get_drug_by_ui_choice`
2. Ta bort import från pain_classification: `import pain_classification as pc` (EJ LÄNGRE ANVÄND)
3. Uppdatera `add_pain_features()` för att använda `LÄKEMEDELS_DATA`
4. Implementera 3D pain features istället för 1D `painTypeScore`
5. Lägg till säkerhetsgränser på output:
   ```python
   final_dose = max(APP_CONFIG['ML_SAFETY_MIN_DOSE'],
                    min(best_dose, APP_CONFIG['ML_SAFETY_MAX_DOSE']))
   ```

### 4. ⚠️ Authentication - Admin-Only User Creation
**Filer:** `auth.py`, `database.py`
**Status:** EJ PÅBÖRJAD

**Vad som måste göras:**
1. **Ta bort auto-create i auth.py:**
   ```python
   # RADERA DESSA RADER (ca rad 70-79):
   else:
       if password:
           return False
       user_id = create_user(username, password_hash=None, is_admin=False)
       st.session_state.user_id = user_id
       # ... etc
   ```

2. **Skapa admin user management UI:**
   - Nytt flik: "Admin - Användare"
   - Lista alla användare
   - Knapp "Lägg till användare" (endast för admin)
   - Formulär: Username (required)
   - Spara med `db.create_user(username, None, False)`

3. **Lägg till whitelist-check:**
   ```python
   def login_user(username: str, password: str = None) -> bool:
       user = get_user_by_username(username)
       if not user:
           st.error("Användare finns inte. Kontakta admin för att skapa konto.")
           return False
       # ... fortsätt med vanlig login
   ```

### 5. ⚠️ Centralisera Database Schema
**Fil:** `database.py`
**Status:** EJ PÅBÖRJAD

**Problem:** CREATE TABLE körs i nästan varje funktion
**Exempel:**
- `get_calibration_factor()` - rad 362-370
- `get_age_factor()` - rad 444-451
- `get_asa_factor()` - rad 493-500
- etc. (10+ funktioner)

**Lösning:**
1. Flytta ALLA CREATE TABLE till `init_database()`
2. Ta bort CREATE TABLE från alla andra funktioner
3. Skapa en helper: `def _ensure_table_exists(table_name)` om verkligen nödvändigt

### 6. ⚠️ Refaktorera BMI-Beräkning
**Filer:** `dosing_tab.py`, `callbacks.py`
**Status:** FUNKTION SKAPAD, INTE TILLÄMPAT

**Vad som gjorts:**
- `calculation_engine_NEW.py` innehåller `calculate_bmi()` funktion

**Vad som måste göras:**
```python
# I dosing_tab.py (2 ställen):
# OLD:
height_m = current_inputs['height'] / 100
bmi = current_inputs['weight'] / (height_m * height_m)

# NEW:
from calculation_engine import calculate_bmi
bmi = calculate_bmi(current_inputs['weight'], current_inputs['height'])
```

### 7. ⚠️ Ta Bort streamlit-authenticator
**Fil:** `requirements.txt`
**Status:** EJ PÅBÖRJAD

```bash
# Radera rad:
streamlit-authenticator
```

### 8. ⚠️ Admin UI för ML Target VAS
**Fil:** Ny flik i UI eller settings
**Status:** EJ PÅBÖRJAD

**Implementering:**
1. Skapa settings-tabell i database:
   ```sql
   CREATE TABLE IF NOT EXISTS app_settings (
       key TEXT PRIMARY KEY,
       value TEXT,
       last_modified_by INTEGER,
       last_modified TIMESTAMP
   )
   ```

2. Skapa admin-flik med:
   ```python
   if auth.is_admin():
       st.number_input("ML Mål-VAS",
                      min_value=0.0,
                      max_value=5.0,
                      value=APP_CONFIG['ML_TARGET_VAS'],
                      step=0.5,
                      key='ml_target_vas_setting')
       if st.button("Spara ML-inställningar"):
           db.save_setting('ML_TARGET_VAS', st.session_state.ml_target_vas_setting)
   ```

3. I `ml_model.py`:
   ```python
   TARGET_VAS = db.get_setting('ML_TARGET_VAS', APP_CONFIG['ML_TARGET_VAS'])
   ```

### 9. ⚠️ Uppdatera Database Schema för 3D Pain
**Fil:** `database.py`
**Status:** EJ PÅBÖRJAD

**Ändringar i procedures-tabell:**
```sql
ALTER TABLE procedures ADD COLUMN painSomatic INTEGER DEFAULT 5;
ALTER TABLE procedures ADD COLUMN painVisceral INTEGER DEFAULT 5;
ALTER TABLE procedures ADD COLUMN painNeuropathic INTEGER DEFAULT 2;
```

**Migrera existerande data:**
```python
# Om painTypeScore <= 3: Visceral dominant
# Om painTypeScore >= 7: Somatic dominant
# Om 3 < painTypeScore < 7: Mixed
```

### 10. ⚠️ Uppdatera procedures_export.json
**Fil:** `procedures_export.json`
**Status:** EJ PÅBÖRJAD

Lägg till för VARJE procedure:
```json
{
  "painTypeScore": 7,  // KAN BEHÅLLAS som legacy
  "painSomatic": 8,
  "painVisceral": 3,
  "painNeuropathic": 2
}
```

## INSTALLATION AV NYA FILER

**När alla fixes är klara:**
```bash
# 1. Backup gamla filer
cp calculation_engine.py calculation_engine_OLD.py
cp ml_model.py ml_model_OLD.py

# 2. Installera nya
cp calculation_engine_NEW.py calculation_engine.py

# 3. Testa
python -m py_compile calculation_engine.py ml_model.py
python -c "import calculation_engine; import ml_model; print('✅ Import OK')"

# 4. Kör applikationen
streamlit run oxydos_v8.py
```

## TESTPLAN

### Kritiska Tester:
1. ✅ **Config import:** `python -c "from config import LÄKEMEDELS_DATA; print(len(LÄKEMEDELS_DATA))"`
2. ⚠️ **Regelmotor:** Beräkna dos för ett test-case
3. ⚠️ **ML-motor:** Förutsäger dos korrekt
4. ⚠️ **Authentication:** Kan INTE skapa user utan admin
5. ⚠️ **Database init:** Körs EN gång, inte vid varje query
6. ⚠️ **3D Pain:** Procedures har alla 3 dimensioner

### Integrationstester:
1. Skapa admin-användare
2. Admin skapar vanlig användare
3. Vanlig användare loggar in
4. Beräkna dos med olika adjuvanter
5. Spara fall
6. Verifiera att inlärning fungerar
7. Exportera data till Excel

## RISK ASSESSMENT

### HÖGRISK om ej åtgärdat:
1. ⚠️ **ML och Regelmotor ej synkroniserad** - Applikationen ger OLIKA doser beroende på motor
2. ⚠️ **Authentication** - Vem som helst kan skapa konto och förorena data
3. ⚠️ **Database performance** - CREATE TABLE vid varje query = extremt långsamt

### MEDELRISK:
4. ⚠️ **Saknad 3D pain** - Går tillbaka till mindre nyanserad smärtmodell
5. ⚠️ **Ingen admin ML-kontroll** - Kan inte justera target VAS

### LÅGRISK:
6. ⚠️ **BMI duplicerad kod** - Bara kodkvalitet
7. ⚠️ **Oanvänd dependency** - Bara diskutrymme

## NÄSTA STEG (PRIORITERAD ORDNING)

1. **[KRITISK]** Ersätt `calculation_engine.py` med nya versionen
2. **[KRITISK]** Uppdatera `ml_model.py` för unified data
3. **[KRITISK]** Fixa authentication (ta bort auto-create)
4. **[KRITISK]** Centralisera database schema
5. **[MEDEL]** Uppdatera procedures med 3D pain scores
6. **[MEDEL]** Skapa admin UI för ML settings
7. **[LÅG]** Refaktorera BMI-calls
8. **[LÅG]** Ta bort streamlit-authenticator

## ESTIMERAD TID

- **Kritiska fixes (1-4):** 3-4 timmar
- **Medel-prioritet (5-6):** 2-3 timmar
- **Låg-prioritet (7-8):** 30 min
- **Testning:** 1-2 timmar

**TOTALT:** 6-10 timmar arbete

## SUPPORT FILES SKAPADE

1. `config_OLD_BACKUP.py` - Backup av gamla config
2. `config.py` - NYA unified config
3. `calculation_engine_NEW.py` - NY regelmotor
4. `config_NEW.py` - Duplicat (kan raderas)

**Nästa session: Börja med att ersätta gamla filer och fortsätt med ML-motor.**
