# Temporal Dosering System - Design
**Datum:** 2025-10-13
**Koncept:** Opslut = Tidpunkt 0:00

## Koncept

### Tidslinje:
```
Preoperativt  |  Perioperativt  |  Opslut  |  Postoperativt
   -3:00      |      -1:30       |  0:00    |    +0:30
     ↓        |        ↓          |    ↓     |      ↓
  Premedicinering  Induktion/Underhåll  Sömn  Uppvaknande
```

### Exempel:
- **Induktion fentanyl 200 µg @ -1:30** (90 min före opslut)
- **Opstartdos fentanyl 50 µg @ -1:00** (60 min före opslut)
- **NSAID ibuprofen 400mg @ -0:15** (15 min före opslut)
- **Catapressan 75 µg @ +0:00** (vid opslut)
- **Rescue oxikodon 5mg @ +0:45** (45 min efter opslut)

## Databasschema

### Ny Tabell: `temporal_doses`
```sql
CREATE TABLE temporal_doses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    drug_type TEXT NOT NULL,           -- 'fentanyl', 'nsaid', 'catapressan', etc.
    drug_name TEXT NOT NULL,            -- 'Fentanyl', 'Ibuprofen 400mg', etc.
    dose REAL NOT NULL,                 -- Dos i enheten för läkemedlet
    unit TEXT NOT NULL,                 -- 'mcg', 'mg', etc.
    time_relative_minutes INTEGER NOT NULL,  -- Minuter relativt opslut (negativ = före, positiv = efter)
    administration_route TEXT,          -- 'IV', 'PO', 'IM', etc.
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
)
```

### Uppdatera `cases` tabell:
```sql
ALTER TABLE cases ADD COLUMN opslut_timestamp TIMESTAMP;
ALTER TABLE cases ADD COLUMN op_duration_minutes INTEGER;  -- Faktisk op-tid
```

## UI Design

### Dosering Tab - Temporal Input Section:
```
┌─────────────────────────────────────────────────────────────┐
│ 📅 Temporal Dosering (Opslut = 0:00)                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ ➕ Lägg till dos:                                            │
│   Läkemedel: [Dropdown: Fentanyl, NSAID, Catapressan...]   │
│   Dos: [___] Enhet: [µg/mg]                                 │
│   Tid: [-] [1]:[30] (före opslut) / [+] [0]:[45] (efter)   │
│   Administrering: [IV ▾]                                    │
│   [Lägg till]                                               │
│                                                              │
│ Tillagda doser:                                             │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ -1:30 | Fentanyl 200 µg (IV)          [❌ Ta bort]  │   │
│ │ -1:00 | Fentanyl 50 µg (IV)           [❌ Ta bort]  │   │
│ │ -0:15 | Ibuprofen 400mg (PO)          [❌ Ta bort]  │   │
│ │  0:00 | Catapressan 75 µg (IV)        [❌ Ta bort]  │   │
│ │ +0:45 | Oxikodon 5mg (PO) [RESCUE]    [❌ Ta bort]  │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ 📊 Visualisering:                                            │
│ [-1:30]────[-1:00]────[-0:15]──[0:00]──[+0:45]             │
│    F200      F50        IBU      CAT      OXY               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Farmakokinetisk Modellering

### Fentanyl Temporal Decay:
```python
def calculate_fentanyl_remaining_at_opslut(dose_mcg: float, time_before_opslut_min: int) -> float:
    """
    Beräkna kvarvarande fentanyl-effekt vid opslut.

    Fentanyl halveringstid: ~3.5 timmar (210 min)
    Context-sensitive half-time: För 1-2h infusion ~30-60 min

    Använder bi-exponentiell modell:
    - Snabb distribution: t½ = 15 min (60%)
    - Långsam elimination: t½ = 210 min (40%)
    """
    if time_before_opslut_min <= 0:
        return dose_mcg

    # Bi-exponentiell decay
    fast_component = 0.6 * dose_mcg * (0.5 ** (time_before_opslut_min / 15))
    slow_component = 0.4 * dose_mcg * (0.5 ** (time_before_opslut_min / 210))

    remaining = fast_component + slow_component
    return remaining

# Exempel:
# Fentanyl 200 µg @ -90 min:
# Fast: 0.6 * 200 * (0.5^6) = 1.875 µg
# Slow: 0.4 * 200 * (0.5^0.43) = 59.5 µg
# Total: ~61 µg kvar vid opslut (~30% av originaldos)
```

### NSAID/Adjuvanter Temporal Effect:
```python
def calculate_adjuvant_effect_at_time(
    drug_data: dict,
    dose: float,
    time_relative_to_opslut: int,
    postop_time: int = 0
) -> float:
    """
    Beräkna adjuvant-effekt vid given tidpunkt.

    Args:
        drug_data: Dictionary från LÄKEMEDELS_DATA
        dose: Given dos
        time_relative_to_opslut: När dosen gavs (min)
        postop_time: Tid efter opslut vi utvärderar (min)

    Returns:
        Effektiv potency (0-1 scale)
    """
    # Tid sedan administrering
    time_since_admin = postop_time - time_relative_to_opslut

    if time_since_admin < 0:
        return 0.0  # Inte givet än

    # Hämta farmakokinetiska parametrar
    t_onset = drug_data.get('onset_minutes', 30)     # Tid till effekt
    t_peak = drug_data.get('peak_minutes', 60)       # Tid till max effekt
    t_duration = drug_data.get('duration_minutes', 240)  # Total duration

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
```

## Uppdaterad LÄKEMEDELS_DATA

Lägg till temporal parametrar:
```python
LÄKEMEDELS_DATA = {
    'fentanyl': {
        'name': 'Fentanyl',
        'onset_minutes': 2,
        'peak_minutes': 5,
        'duration_minutes': 30,
        'half_life_alpha': 15,      # Snabb distribution
        'half_life_beta': 210,      # Långsam elimination
        'context_sensitive_ht': 60  # Efter 2h infusion
    },
    'ibuprofen_400mg': {
        'name': 'Ibuprofen 400mg',
        'onset_minutes': 30,
        'peak_minutes': 60,
        'duration_minutes': 360,    # 6 timmar
        'bioavailability': 0.8      # PO
    },
    'clonidine': {
        'name': 'Catapressan (Klonidin)',
        'onset_minutes': 30,
        'peak_minutes': 90,
        'duration_minutes': 480,    # 8 timmar
    },
    # ... etc
}
```

## Regelmotor Integration

### Uppdaterad `calculate_rule_based_dose()`:
```python
def calculate_rule_based_dose_with_temporal(inputs, procedures_df, temporal_doses=[]):
    """
    Beräkna dos med hänsyn till temporal dosering.

    Args:
        inputs: Standard patient inputs
        procedures_df: Procedures dataframe
        temporal_doses: Lista av tidigare doser med timing
            [{'drug': 'fentanyl', 'dose': 200, 'time': -90, 'unit': 'mcg'}, ...]
    """
    # 1. Beräkna base MME som vanligt
    mme, pain_type_3d, procedure = _get_initial_mme_and_pain_type(inputs, procedures_df)
    mme = _apply_patient_factors(mme, inputs)

    # 2. Beräkna kvarvarande effekt från temporal fentanyl
    fentanyl_remaining_mme = 0
    for dose_entry in temporal_doses:
        if dose_entry['drug'] == 'fentanyl':
            remaining_mcg = calculate_fentanyl_remaining_at_opslut(
                dose_entry['dose'],
                abs(dose_entry['time'])  # Negativ tid = före opslut
            )
            fentanyl_remaining_mme += (remaining_mcg / 100) * 10  # Till MME

    # 3. Beräkna effektiv adjuvant-reduktion vid postop tid
    # (Använd genomsnittlig postop tid 60 min som default)
    effective_adjuvant_reduction = 0
    for dose_entry in temporal_doses:
        if dose_entry['drug'] in ['nsaid', 'catapressan', 'droperidol', ...]:
            drug_data = get_drug_from_temporal_entry(dose_entry)
            if drug_data:
                effect = calculate_adjuvant_effect_at_time(
                    drug_data,
                    dose_entry['dose'],
                    dose_entry['time'],
                    postop_time=60  # Default 1h postop
                )
                effective_adjuvant_reduction += drug_data['potency_mme'] * effect

    # 4. Justera MME
    mme -= fentanyl_remaining_mme
    mme -= effective_adjuvant_reduction
    mme = max(0, mme)

    # 5. Fortsätt som vanligt...
    return final_dose
```

## ML Features

### Nya temporal features för XGBoost:
```python
def add_temporal_features(row, temporal_doses):
    """Lägg till temporal features för ML."""

    # Total fentanyl MME vid opslut
    row['fentanyl_at_opslut_mme'] = sum(
        calculate_fentanyl_remaining_at_opslut(d['dose'], abs(d['time']))
        for d in temporal_doses if d['drug'] == 'fentanyl'
    ) / 100 * 10

    # Total opioid load (area under curve)
    row['total_opioid_auc'] = calculate_opioid_auc(temporal_doses)

    # Tid sedan sista opioid-dos vid postop utvärdering
    opioid_times = [d['time'] for d in temporal_doses if d['drug'] in ['fentanyl', 'oxycodone']]
    if opioid_times:
        row['time_since_last_opioid'] = row['postop_minutes'] - max(opioid_times)

    # Antal doser per tidsperiod
    row['doses_preop'] = len([d for d in temporal_doses if d['time'] < -30])
    row['doses_periop'] = len([d for d in temporal_doses if -30 <= d['time'] < 0])
    row['doses_early_postop'] = len([d for d in temporal_doses if 0 <= d['time'] < 60])

    # NSAID timing (optimal = -30 till +15 min)
    nsaid_doses = [d for d in temporal_doses if d['drug'] == 'nsaid']
    if nsaid_doses:
        nsaid_time = nsaid_doses[0]['time']
        row['nsaid_timing_optimal'] = 1 if -30 <= nsaid_time <= 15 else 0
        row['nsaid_given_minutes_from_opslut'] = nsaid_time

    return row
```

## Användningsfall

### Fall 1: Standard Laparoskopi
```python
temporal_doses = [
    {'drug': 'fentanyl', 'dose': 200, 'time': -90, 'unit': 'mcg', 'route': 'IV'},
    {'drug': 'fentanyl', 'dose': 50, 'time': -60, 'unit': 'mcg', 'route': 'IV'},
    {'drug': 'nsaid', 'name': 'Parecoxib 40mg', 'dose': 40, 'time': -10, 'unit': 'mg', 'route': 'IV'},
    {'drug': 'catapressan', 'dose': 75, 'time': 0, 'unit': 'mcg', 'route': 'IV'},
]

# Vid opslut (0:00):
# - Fentanyl 200 @ -90: ~60 µg kvar = 6 MME
# - Fentanyl 50 @ -60: ~25 µg kvar = 2.5 MME
# - Total fentanyl @ opslut: 8.5 MME

# Vid postop +60 min:
# - Parecoxib: Full effekt (givet @ -10, nu +70 min sedan)
# - Catapressan: Full effekt (givet @ 0, nu +60 min sedan)
# - Fentanyl: Nästan slut
```

### Fall 2: Lång Operation med Omtitrering
```python
temporal_doses = [
    # Induktion
    {'drug': 'fentanyl', 'dose': 300, 'time': -150, 'unit': 'mcg', 'route': 'IV'},

    # Underhåll
    {'drug': 'fentanyl', 'dose': 50, 'time': -90, 'unit': 'mcg', 'route': 'IV'},
    {'drug': 'fentanyl', 'dose': 50, 'time': -45, 'unit': 'mcg', 'route': 'IV'},

    # Före opslut
    {'drug': 'nsaid', 'name': 'Ketorolac 30mg', 'dose': 30, 'time': -20, 'unit': 'mg', 'route': 'IV'},

    # Vid opslut
    {'drug': 'betapred', 'dose': 8, 'time': 0, 'unit': 'mg', 'route': 'IV'},

    # Postop rescue
    {'drug': 'oxycodone', 'dose': 5, 'time': 45, 'unit': 'mg', 'route': 'PO'},
]
```

## Fördelar

### Kliniska Fördelar:
1. **Precision:** Exakt timing av läkemedel dokumenteras
2. **Farmakokinetik:** Hänsyn tas till halveringstider och kontext
3. **Optimering:** ML kan lära sig optimal timing
4. **Evidens:** Data för att bevisa/motbevisa timing-strategier

### ML-Fördelar:
1. **Nya features:** Temporal patterns kan upptäckas
2. **Kausal inference:** Timing → Outcome relationer
3. **Personalisering:** Optimal timing per patient/ingrepp
4. **Prediktiv:** Förutsäg rescue-behov baserat på temporal profil

### Forskningsfördelar:
1. **Publikationer:** Temporal dosering är underutforskat
2. **Guidelines:** Kan skapa evidensbaserade timing-rekommendationer
3. **Benchmarking:** Jämför olika timing-strategier

## Implementation Priority

1. **Fas 1 (KRITISK):** Database schema + Basic UI
2. **Fas 2 (HÖG):** Temporal fentanyl decay i regelmotor
3. **Fas 3 (MEDEL):** Full farmakokinetik för alla adjuvanter
4. **Fas 4 (LÅG):** Avancerad ML temporal features

## Nästa Steg

1. Uppdatera database schema
2. Skapa UI för temporal input
3. Implementera farmakokinetiska funktioner
4. Integrera i regelmotor
5. Testa med mock data
6. Dokumentera för användare
