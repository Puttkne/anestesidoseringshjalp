# Temporal Dosering - Implementation TODO
**Status:** Design klar, Implementation påbörjad
**Prioritet:** HÖG

## ✅ Genomfört
1. Design dokument skapat: [TEMPORAL_DOSERING_DESIGN.md](TEMPORAL_DOSERING_DESIGN.md)
2. Database schema definierat: [database_TEMPORAL_ADDITION.sql](database_TEMPORAL_ADDITION.sql)

## 📋 Kvarstående Implementation

### 1. DATABASE (KRITISK)
**Fil:** `database.py`

**Steg 1.1 - Lägg till temporal_doses tabell i init_database():**
```python
# Efter custom_procedures tabell (ca rad 142):
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
```

**Steg 1.2 - Lägg till funktioner i database.py:**
```python
def save_temporal_doses(case_id: int, doses: List[Dict]):
    """Spara temporal doser för ett fall"""
    conn = get_connection()
    cursor = conn.cursor()

    for dose in doses:
        cursor.execute('''
            INSERT INTO temporal_doses (
                case_id, drug_type, drug_name, dose, unit,
                time_relative_minutes, administration_route, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            case_id,
            dose['drug_type'],
            dose['drug_name'],
            dose['dose'],
            dose['unit'],
            dose['time'],
            dose.get('route', 'IV'),
            dose.get('notes', '')
        ))

    conn.commit()
    conn.close()

def get_temporal_doses(case_id: int) -> List[Dict]:
    """Hämta temporal doser för ett fall"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM temporal_doses
        WHERE case_id = ?
        ORDER BY time_relative_minutes ASC
    ''', (case_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def delete_temporal_dose(dose_id: int):
    """Radera en temporal dos"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM temporal_doses WHERE id = ?', (dose_id,))

    conn.commit()
    conn.close()
```

---

### 2. CONFIG - Farmakokinetiska Parametrar (HÖG)
**Fil:** `config.py`

**Lägg till temporal parametrar i LÄKEMEDELS_DATA:**
```python
LÄKEMEDELS_DATA = {
    'fentanyl': {
        'name': 'Fentanyl',
        'onset_minutes': 2,
        'peak_minutes': 5,
        'duration_minutes': 30,
        'half_life_alpha': 15,      # Snabb distribution
        'half_life_beta': 210,      # Långsam elimination
        'context_sensitive_ht': 60,
        # ... existing fields
    },
    'ibuprofen_400mg': {
        'name': 'Ibuprofen 400mg',
        'onset_minutes': 30,
        'peak_minutes': 60,
        'duration_minutes': 360,
        # ... existing fields
    },
    # etc för alla läkemedel
}
```

---

### 3. FARMAKOKINETISKA FUNKTIONER (HÖG)
**Ny fil:** `pharmacokinetics.py`

```python
import math
from typing import Dict, List
from config import LÄKEMEDELS_DATA

def calculate_fentanyl_remaining_at_opslut(dose_mcg: float, time_before_opslut_min: int) -> float:
    """
    Beräkna kvarvarande fentanyl-effekt vid opslut.

    Bi-exponentiell decay:
    - Snabb distribution: t½ = 15 min (60%)
    - Långsam elimination: t½ = 210 min (40%)
    """
    if time_before_opslut_min <= 0:
        return dose_mcg

    fast_component = 0.6 * dose_mcg * (0.5 ** (time_before_opslut_min / 15))
    slow_component = 0.4 * dose_mcg * (0.5 ** (time_before_opslut_min / 210))

    return fast_component + slow_component

def calculate_adjuvant_effect_at_time(
    drug_data: dict,
    dose: float,
    time_relative_to_opslut: int,
    postop_time: int = 0
) -> float:
    """
    Beräkna adjuvant-effekt vid given tidpunkt (0-1 scale).

    Trapezoidal curve:
    0 --> onset --> peak (max=1.0) --> duration --> 0
    """
    time_since_admin = postop_time - time_relative_to_opslut

    if time_since_admin < 0:
        return 0.0  # Inte givet än

    t_onset = drug_data.get('onset_minutes', 30)
    t_peak = drug_data.get('peak_minutes', 60)
    t_duration = drug_data.get('duration_minutes', 240)

    # Trapezoidal effect curve
    if time_since_admin < t_onset:
        # Stiger till max
        effect = time_since_admin / t_onset
    elif time_since_admin < t_peak:
        # Max effekt
        effect = 1.0
    elif time_since_admin < t_duration:
        # Avtar linjärt
        effect = 1.0 - ((time_since_admin - t_peak) / (t_duration - t_peak))
    else:
        # Slut på effekt
        effect = 0.0

    return max(0, min(1, effect))

def calculate_total_opioid_auc(temporal_doses: List[Dict], eval_time_postop: int = 60) -> float:
    """
    Beräkna total opioid AUC (Area Under Curve) vid utvärderingstid.

    Returns: MME-minuter
    """
    auc = 0

    for dose_entry in temporal_doses:
        if dose_entry['drug_type'] not in ['fentanyl', 'oxycodone']:
            continue

        dose_time = dose_entry['time']
        dose_amount = dose_entry['dose']

        if dose_entry['drug_type'] == 'fentanyl':
            # För fentanyl, integrera exponentiell decay
            # Approximation: genomsnittlig effekt * duration
            remaining = calculate_fentanyl_remaining_at_opslut(dose_amount, abs(dose_time))
            # Konvertera till MME och multiplicera med genomsnittlig tid (30 min)
            auc += (remaining / 100) * 10 * 30

        elif dose_entry['drug_type'] == 'oxycodone':
            # Oxikodon: längre halveringstid (~3h)
            # Simplified: 1 mg oxycodone = 1.5 MME, duration 180 min
            time_since = eval_time_postop - dose_time
            if time_since > 0:
                remaining_fraction = 0.5 ** (time_since / 180)
                auc += dose_amount * 1.5 * remaining_fraction * 60

    return auc
```

---

### 4. REGELMOTOR INTEGRATION (KRITISK)
**Fil:** `calculation_engine.py`

**Uppdatera `calculate_rule_based_dose()` för temporal support:**
```python
def calculate_rule_based_dose(inputs, procedures_df, temporal_doses=[]):
    """
    Beräkna dos med hänsyn till temporal dosering.

    Args:
        inputs: Standard patient inputs
        procedures_df: Procedures dataframe
        temporal_doses: Lista av tidigare doser med timing
    """
    # 1. Base beräkning
    mme, pain_type_3d, procedure = _get_initial_mme_and_pain_type(inputs, procedures_df)
    mme = _apply_patient_factors(mme, inputs)

    # 2. Temporal fentanyl adjustment
    if temporal_doses:
        import pharmacokinetics as pk

        fentanyl_remaining_mme = 0
        for dose_entry in temporal_doses:
            if dose_entry['drug_type'] == 'fentanyl' and dose_entry['time'] < 0:
                remaining_mcg = pk.calculate_fentanyl_remaining_at_opslut(
                    dose_entry['dose'],
                    abs(dose_entry['time'])
                )
                fentanyl_remaining_mme += (remaining_mcg / 100) * 10

        # Subtrahera från behov
        mme -= fentanyl_remaining_mme

    # 3. Fortsätt som vanligt med adjuvanter etc.
    base_mme_before_adjuvants = mme
    mme = _apply_adjuvants(mme, inputs, pain_type_3d)
    mme = _apply_synergy_and_safety_limits(mme, inputs, base_mme_before_adjuvants)

    # 4. OBS: INTE subtrahera regular fentanyl om temporal finns
    if not temporal_doses:
        mme = _apply_fentanyl_pharmacokinetics(mme, inputs)

    mme = _apply_weight_adjustment(mme, inputs)

    # ... rest of function
```

---

### 5. UI - TEMPORAL INPUT (KRITISK)
**Fil:** `ui/tabs/dosing_tab.py`

**Lägg till section för temporal dosering (efter patient inputs):**
```python
# Efter patient inputs, före "Beräkna dos" knapp

st.divider()
st.subheader("⏱️ Temporal Dosering (Opslut = 0:00)")

# Initialize session state för temporal doses
if 'temporal_doses' not in st.session_state:
    st.session_state.temporal_doses = []

# Input form
with st.expander("➕ Lägg till temporal dos", expanded=True):
    col_drug, col_dose, col_time = st.columns([2, 1, 2])

    with col_drug:
        drug_options = {
            'Fentanyl': 'fentanyl',
            'Ibuprofen 400mg': 'nsaid',
            'Ketorolac 30mg': 'nsaid',
            'Parecoxib 40mg': 'nsaid',
            'Catapressan': 'catapressan',
            'Ketamin (liten bolus)': 'ketamine',
            'Ketamin (stor bolus)': 'ketamine',
            'Lidokain (bolus)': 'lidocaine',
            'Lidokain (infusion)': 'lidocaine',
            'Betapred 4mg': 'betapred',
            'Betapred 8mg': 'betapred',
            'Droperidol': 'droperidol',
            'Oxikodon (rescue)': 'oxycodone',
        }
        selected_drug = st.selectbox("Läkemedel", list(drug_options.keys()), key='temp_drug')

    with col_dose:
        dose_value = st.number_input("Dos", min_value=0.0, step=1.0, key='temp_dose')
        # Auto-select unit based on drug
        if 'fentanyl' in selected_drug.lower() or 'catapressan' in selected_drug.lower():
            unit = 'µg'
        else:
            unit = 'mg'
        st.caption(f"Enhet: {unit}")

    with col_time:
        time_sign = st.radio("Relativt opslut", ['➖ Före', '➕ Efter'], horizontal=True, key='temp_sign')
        col_h, col_m = st.columns(2)
        with col_h:
            hours = st.number_input("Timmar", 0, 10, 0, key='temp_h')
        with col_m:
            minutes = st.number_input("Minuter", 0, 59, 0, key='temp_m')

        time_minutes = hours * 60 + minutes
        if '➖' in time_sign:
            time_minutes = -time_minutes

    col_route, col_add = st.columns([1, 1])
    with col_route:
        route = st.selectbox("Administrering", ['IV', 'PO', 'IM', 'SC'], key='temp_route')

    with col_add:
        st.write("")  # Spacer
        if st.button("➕ Lägg till dos", key='add_temp_dose', use_container_width=True):
            new_dose = {
                'drug_name': selected_drug,
                'drug_type': drug_options[selected_drug],
                'dose': dose_value,
                'unit': unit,
                'time': time_minutes,
                'route': route
            }
            st.session_state.temporal_doses.append(new_dose)
            st.rerun()

# Visa tillagda doser
if st.session_state.temporal_doses:
    st.markdown("**Tillagda temporal doser:**")

    # Sortera efter tid
    sorted_doses = sorted(st.session_state.temporal_doses, key=lambda x: x['time'])

    for idx, dose in enumerate(sorted_doses):
        time_str = format_time_relative(dose['time'])

        col_time, col_drug, col_del = st.columns([1, 3, 1])
        with col_time:
            st.text(time_str)
        with col_drug:
            st.text(f"{dose['drug_name']} {dose['dose']} {dose['unit']} ({dose['route']})")
        with col_del:
            if st.button("❌", key=f"del_temp_{idx}", help="Ta bort"):
                st.session_state.temporal_doses.pop(idx)
                st.rerun()

    # Timeline visualization
    st.markdown("**📊 Tidslinje:**")
    # TODO: Implement timeline visualization

def format_time_relative(minutes: int) -> str:
    """Format time relative to opslut"""
    sign = '+' if minutes >= 0 else '-'
    abs_minutes = abs(minutes)
    hours = abs_minutes // 60
    mins = abs_minutes % 60
    return f"{sign}{hours:01d}:{mins:02d}"
```

---

### 6. UI - SPARA TEMPORAL DOSES (KRITISK)
**Fil:** `callbacks.py`

**Uppdatera `handle_save_and_learn()` för att spara temporal doses:**
```python
def handle_save_and_learn(procedures_df):
    # ... existing code ...

    # After saving case:
    case_id = ...  # Get from save_case() return value

    # Save temporal doses if any
    if st.session_state.get('temporal_doses'):
        import database as db
        db.save_temporal_doses(case_id, st.session_state.temporal_doses)
        # Clear after saving
        st.session_state.temporal_doses = []
```

---

### 7. ML TEMPORAL FEATURES (MEDEL)
**Fil:** `ml_model.py`

**Lägg till i `add_pain_features()`:**
```python
def add_pain_features(row):
    # ... existing code ...

    # Add temporal features if available
    if row.get('temporal_doses'):
        import pharmacokinetics as pk
        temporal_doses = row['temporal_doses']

        # Total fentanyl MME vid opslut
        row['fentanyl_at_opslut_mme'] = sum(
            (pk.calculate_fentanyl_remaining_at_opslut(d['dose'], abs(d['time'])) / 100) * 10
            for d in temporal_doses if d['drug_type'] == 'fentanyl'
        )

        # Total opioid AUC
        row['total_opioid_auc'] = pk.calculate_total_opioid_auc(temporal_doses, 60)

        # Tid sedan sista opioid
        opioid_times = [d['time'] for d in temporal_doses if d['drug_type'] in ['fentanyl', 'oxycodone']]
        if opioid_times:
            row['time_since_last_opioid'] = row.get('postop_minutes', 60) - max(opioid_times)
        else:
            row['time_since_last_opioid'] = 999

        # Antal doser per period
        row['doses_preop'] = len([d for d in temporal_doses if d['time'] < -30])
        row['doses_periop'] = len([d for d in temporal_doses if -30 <= d['time'] < 0])
        row['doses_postop'] = len([d for d in temporal_doses if d['time'] >= 0])

    else:
        # No temporal data - set defaults
        row['fentanyl_at_opslut_mme'] = 0
        row['total_opioid_auc'] = 0
        row['time_since_last_opioid'] = 999
        row['doses_preop'] = 0
        row['doses_periop'] = 0
        row['doses_postop'] = 0

    return row
```

---

### 8. HISTORY TAB - VISA TEMPORAL (LÅG)
**Fil:** `ui/tabs/history_tab.py`

**Lägg till i case details expander:**
```python
# I history tab, när man visar case details:
temporal_doses = db.get_temporal_doses(case['id'])
if temporal_doses:
    with st.expander("⏱️ Temporal Dosering"):
        for dose in temporal_doses:
            time_str = format_time_relative(dose['time_relative_minutes'])
            st.text(f"{time_str} | {dose['drug_name']} {dose['dose']} {dose['unit']} ({dose['administration_route']})")
```

---

## 📊 Prioriterad Implementation Order

### Sprint 1 (KRITISK - 4h):
1. ✅ Design dokument
2. **Database schema & funktioner** (database.py)
3. **Farmakokinetiska funktioner** (pharmacokinetics.py)
4. **Basic UI för temporal input** (dosing_tab.py)

### Sprint 2 (HÖG - 3h):
5. **Regelmotor integration** (calculation_engine.py)
6. **Spara temporal doses** (callbacks.py)
7. **Config farmakokinetiska params** (config.py)

### Sprint 3 (MEDEL - 2h):
8. **ML temporal features** (ml_model.py)
9. **Timeline visualization** (dosing_tab.py)
10. **History tab display** (history_tab.py)

---

## 🧪 Testplan

### Test 1: Simpel Temporal Fentanyl
```python
temporal_doses = [
    {'drug_type': 'fentanyl', 'dose': 200, 'time': -90, 'unit': 'mcg', 'route': 'IV'}
]

# Förväntat: ~60 µg kvar vid opslut
# Dos ska reduceras med ~6 MME
```

### Test 2: Komplex Multi-Drug
```python
temporal_doses = [
    {'drug_type': 'fentanyl', 'dose': 200, 'time': -90, ...},
    {'drug_type': 'fentanyl', 'dose': 50, 'time': -60, ...},
    {'drug_type': 'nsaid', 'drug_name': 'Parecoxib 40mg', 'dose': 40, 'time': -10, ...},
    {'drug_type': 'catapressan', 'dose': 75, 'time': 0, ...},
]

# Förväntat: Fentanyl decay + adjuvant temporal effects
```

### Test 3: Rescue Postop
```python
temporal_doses = [
    {'drug_type': 'oxycodone', 'dose': 5, 'time': 45, 'unit': 'mg', 'route': 'PO'}
]

# Förväntat: Loggas som rescue i postop period
```

---

## 📞 Support & Dokumentation

**Om problem:**
- Kontrollera att `pharmacokinetics.py` importeras korrekt
- Verifiera att `temporal_doses` tabell skapades i databasen
- Testa farmakokinetiska funktioner manuellt först

**Dokumentation för användare:**
- Skapa guide: "Hur man använder Temporal Dosering"
- Video tutorial för UI
- Exempel-cases med vanliga scenarier

---

**Status:** 🟡 Design klar, väntar på implementation
**Estimerad tid kvar:** 9 timmar
**Nästa steg:** Implementera database schema & funktioner
