# Ketamine och NSAID Differentiering - Alfa V0.8.2

## Översikt
Två uppdateringar implementerade baserat på klinisk feedback:
1. **Reducerad batch learning aggressivitet** (±0.5 → ±0.3)
2. **Ketamine dosvariering** med 4 olika alternativ

## 1. Batch Learning Aggressivitet Reducerad

### Problem
Batch learning vid fall 15 kunde ge stora justeringar (±0.5 painTypeScore) baserat på begränsad data.

### Lösning
```python
# FÖRE:
if score_diff > 0.3:
    return {'pain_type_adjustment': +0.5, 'confidence': 'strong_somatic_signal'}

# EFTER:
if score_diff > 0.3:
    return {'pain_type_adjustment': +0.3, 'confidence': 'strong_somatic_signal'}
```

### Påverkan
- Stark signal: ±0.5 → ±0.3 (40% minskning)
- Måttlig signal: ±0.2 → ±0.15 (25% minskning)
- Mer konservativ inlärning = stabilare painTypeScore över tid

## 2. Ketamine Dosvariering

### Nya Alternativ (Rullgardinsmeny)
1. **Liten bolus (0.05-0.1 mg/kg)**: -10% MME (multiplier 0.90)
2. **Stor bolus (0.5-1 mg/kg)**: -20% MME (multiplier 0.80)
3. **Liten infusion (0.10-0.15 mg/kg/h)**: -15% MME (multiplier 0.85)
4. **Stor infusion (3 mg/kg/h)**: -30% MME (multiplier 0.70)

### Jämförelse: Gammal vs Ny
| Alternativ | Gammalt | Nytt | Kommentar |
|------------|---------|------|-----------|
| Liten bolus | N/A | -10% | Ny option, minimal reduktion |
| Stor bolus | -15% (generisk bolus) | -20% | Ökad reduktion för högdos |
| Liten infusion | N/A | -15% | Ny option, liknande gammal bolus |
| Stor infusion | -25% (generisk infusion) | -30% | Ökad reduktion för högdos |

### Implementationsdetaljer

#### UI (oxydoseks.py rad 805-817)
```python
ketamine_choice = k_cols[1].selectbox("",
    ["Ej given",
     "Liten bolus (0.05-0.1 mg/kg)",
     "Stor bolus (0.5-1 mg/kg)",
     "Liten infusion (0.10-0.15 mg/kg/h)",
     "Stor infusion (3 mg/kg/h)"],
    key='ketamine_choice')

# Backwards compatibility för gamla fält
if ketamine_choice in ["Liten bolus...", "Stor bolus..."]:
    st.session_state['ketamine'] = 'Bolus'
elif ketamine_choice in ["Liten infusion...", "Stor infusion..."]:
    st.session_state['ketamine'] = 'Infusion'
else:
    st.session_state['ketamine'] = 'Nej'
```

#### Beräkning (oxydoseks.py rad 219-242)
```python
ketamine_choice = inputs.get('ketamine_choice', 'Ej given')
if ketamine_choice != 'Ej given':
    ketamine_multipliers = {
        'Liten bolus (0.05-0.1 mg/kg)': 0.90,
        'Stor bolus (0.5-1 mg/kg)': 0.80,
        'Liten infusion (0.10-0.15 mg/kg/h)': 0.85,
        'Stor infusion (3 mg/kg/h)': 0.70
    }
    base_mult = ketamine_multipliers.get(ketamine_choice, 0.85)

    # Hämta learned multiplier per dosvariering
    learned_mult = db.get_adjuvant_multiplier(user_id, ketamine_choice,
                                              pain_type_score, base_mult)
    # Applicera pain type mismatch penalty
    effective_multiplier = 1 - ((1 - learned_mult) * penalty)
    mme *= effective_multiplier
```

#### Inlärning (oxydoseks.py rad 648-662)
```python
ketamine_choice = current_inputs.get('ketamine_choice', 'Ej given')
if ketamine_choice != 'Ej given':
    med = pc.MEDICATIONS.get('ketamine', {})
    ketamine_base_mults = {
        'Liten bolus (0.05-0.1 mg/kg)': 0.90,
        'Stor bolus (0.5-1 mg/kg)': 0.80,
        'Liten infusion (0.10-0.15 mg/kg/h)': 0.85,
        'Stor infusion (3 mg/kg/h)': 0.70
    }
    base_mult = ketamine_base_mults.get(ketamine_choice, 0.85)
    new_mult = db.update_adjuvant_effectiveness(
        user_id, ketamine_choice, pain_type_score, base_mult,
        adjuvant_adjustment, ...)
    adjuvant_updates.append(f"{ketamine_choice}: {new_mult:.2f}")
```

#### Composite Key (oxydoseks.py rad 291-299)
```python
ketamine_choice = inputs.get('ketamine_choice', 'Ej given')
ketamine_chars = {
    'Liten bolus (0.05-0.1 mg/kg)': 'KBl',
    'Stor bolus (0.5-1 mg/kg)': 'KBs',
    'Liten infusion (0.10-0.15 mg/kg/h)': 'KIl',
    'Stor infusion (3 mg/kg/h)': 'KIs'
}
ketamine_char = ketamine_chars.get(ketamine_choice, 'x')
```

#### Databas (database.py)
```sql
-- Ny kolumn i cases-tabellen
ALTER TABLE cases ADD COLUMN ketamine_choice TEXT;

-- INSERT uppdaterad (rad 223, 249)
INSERT INTO cases (..., ketamine, ketamine_choice, lidocaine, ...)
VALUES (..., ?, ?, ?, ...)
```

## 3. Förväntad Klinisk Påverkan

### Batch Learning
- **Tidigare:** Fall 15 kunde ge painTypeScore ändring från 3 → 3.5 (för stark signal)
- **Nu:** Fall 15 ger max ändring från 3 → 3.3 (mer konservativt)
- **Fördel:** Färre "översving" i painTypeScore, stabilare över tid

### Ketamine Dosvariering
- **Tidigare:** Två val (bolus/infusion), ingen dosdifferentiering
- **Nu:** Fyra val med dos-specifika multipliers och separat inlärning

#### Exempel: Hip Replacement (Höftledsplastik)
**Scenario 1: Liten bolus**
```
baseMME: 26
× Liten bolus ketamine (0.90) = 23.4 MME
→ Dos: ~12 mg oxycodone
```

**Scenario 2: Stor infusion**
```
baseMME: 26
× Stor infusion ketamine (0.70) = 18.2 MME
→ Dos: ~9 mg oxycodone
```

**Skillnad:** 3 mg (25% reduktion med högdos ketamine)

#### Exempel: Laparoskopisk Kolecystektomi (Visceralt ingrepp)
**Scenario 1: Stor bolus (0.5-1 mg/kg)**
```
baseMME: 16
× Stor bolus (0.80) = 12.8 MME
× Pain mismatch penalty (ketamine selectivity 5, procedure 2) → 0.70 av effekt
→ Effektiv multiplier: 1 - (0.2 × 0.7) = 0.86
→ Dos: 11 MME ≈ 5.5 mg oxycodone
```

**Kommentar:** Ketamine mindre effektivt för viscerala ingrepp (penalty applicerad)

## 4. Database Migration

### Befintliga Databaser
Om databasen redan finns:
```python
# Kör detta för att lägga till kolumnen
import sqlite3
conn = sqlite3.connect('anesthesia_dosing.db')
cursor = conn.cursor()
cursor.execute("ALTER TABLE cases ADD COLUMN ketamine_choice TEXT")
conn.commit()
conn.close()
```

### Nya Databaser
Skapas automatiskt med ketamine_choice kolumn inkluderad.

### Backwards Compatibility
- Gamla rader: `ketamine_choice = NULL` (hanteras som "Ej given")
- Gamla beräkningar: `ketamine = 'Bolus'/'Infusion'` mappas till nya choices
- UI: Sätter både `ketamine_choice` (ny) och `ketamine` (gammal) för kompatibilitet

## 5. Kvalitetssäkring

### Testa Följande
1. **Batch learning:**
   - Logga 15 fall med NSAID (5+ fall) och Catapressan (3+ fall)
   - Verifiera att painTypeScore ändras max ±0.3

2. **Ketamine val:**
   - Välj varje ketamine-option och verifiera rätt multiplier appliceras
   - Kontrollera att composite key innehåller rätt kod (KBl, KBs, KIl, KIs)

3. **Inlärning:**
   - Logga fall med olika ketamine-doser
   - Verifiera att varje dos lär sig separat i adjuvant_effectiveness

4. **Database:**
   - Kontrollera att ketamine_choice sparas korrekt
   - Verifiera att gamla fall (NULL) hanteras utan fel

### Förväntat Beteende
✓ Batch learning mer stabil (mindre oscillation)
✓ Ketamine-doser ger olika opioid-reduktion
✓ Högdos ketamine → större MME-reduktion → lägre oxycodone
✓ Separat inlärning per ketamine-dos (precisionsinlärning)

## 6. Nästa Steg (Framtida)

### Kortsiktigt
- [ ] Övervaka stabilitet i painTypeScore efter batch learning
- [ ] Analysera om ketamine multipliers är korrekt kalibrerade
- [ ] Överväg liknande dosvariering för Lidocaine?

### Medellång sikt
- [ ] Implementera viktbaserad ketamine-dosering (mg total istället för mg/kg)
- [ ] Kombinera ketamine bolus + infusion (kan de ges samtidigt?)
- [ ] Exportera ketamine effectiveness-data för forskning

### Långsiktig
- [ ] Machine learning för optimal ketamine-dos per ingrepp
- [ ] Adaptiv dosjustering baserat på patient-respons
- [ ] Multicenterstudie för validering

## Tekniska Ändringar - Sammanfattning

### Filer Modifierade
1. **oxydoseks.py**
   - Rad 148-155: Batch learning max ±0.5 → ±0.3
   - Rad 219-242: Ketamine dose-specific multipliers
   - Rad 291-299: Ketamine composite key chars
   - Rad 440: ketamine_choice i get_current_inputs()
   - Rad 648-662: Ketamine learning per dose
   - Rad 805-817: UI dropdown för ketamine
   - Rad 1246-1253: Info display för ketamine

2. **database.py**
   - Rad 56: ketamine_choice kolumn i schema
   - Rad 223: ketamine_choice i INSERT
   - Rad 249: ketamine_choice i VALUES

3. **test_ketamine_update.py** (ny fil)
   - Testsript för database migration

4. **KETAMINE_NSAID_UPDATE.md** (ny fil)
   - Denna dokumentation

### Git Commit Message (förslag)
```
Implementera ketamine dosvariering och reducera batch learning aggressivitet

- Batch learning: Max justering ±0.5 → ±0.3 (stabilare painTypeScore)
- Ketamine: 4 dosalternativ istället för 2 (liten/stor bolus/infusion)
- Ketamine multipliers: 0.90/0.80/0.85/0.70 baserat på dos
- Separat inlärning per ketamine-dos i adjuvant_effectiveness
- Database: Ny kolumn ketamine_choice i cases-tabellen
- Backwards compatible: Gamla ketamine-fält behålls för XGBoost

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```
