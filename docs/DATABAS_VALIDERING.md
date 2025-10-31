# Databas och Applikationsvalidering - Komplett Genomgång

## 1. DATABAS-SCHEMA - Verifiering

### ✅ Tabeller som finns:
1. **users** - Användare och autentisering
2. **cases** - Patientfall och outcomes
3. **edit_history** - Historik över ändringar
4. **user_settings** - Kalibreringsfaktorer per kombination
5. **custom_procedures** - Anpassade ingrepp
6. **adjuvant_effectiveness** - Adjuvant-inlärning
7. **fentanyl_kinetics** - Fentanyl-inlärning
8. **procedure_learning** - baseMME och painTypeScore-inlärning

### ✅ Alla fält i cases-tabellen:
```sql
- id INTEGER PRIMARY KEY
- user_id INTEGER (FK)
- procedure_id TEXT
- specialty TEXT
- surgery_type TEXT
- age INTEGER
- sex TEXT
- weight REAL
- height REAL
- bmi REAL
- ibw REAL
- abw REAL
- asa TEXT
- opioid_history TEXT
- low_pain_threshold INTEGER
- optime_minutes INTEGER
- fentanyl_dose INTEGER
- nsaid INTEGER
- nsaid_choice TEXT ✓ (nytt!)
- catapressan INTEGER
- droperidol INTEGER
- ketamine TEXT
- ketamine_choice TEXT ✓ (nytt!)
- lidocaine TEXT
- betapred TEXT
- given_dose REAL
- vas INTEGER
- uva_dose REAL
- postop_minutes INTEGER
- postop_reason TEXT
- respiratory_status TEXT
- severe_fatigue INTEGER
- rescue_early INTEGER ✓
- rescue_late INTEGER ✓
- calculation_data TEXT (JSON)
- timestamp TIMESTAMP
- last_modified TIMESTAMP
- last_modified_by INTEGER (FK)
```

### ✅ Verifiering: Alla fält används
- ✓ nsaid_choice används i UI och sparas
- ✓ ketamine_choice används i UI och sparas
- ✓ rescue_early/rescue_late används för fentanyl vs baseMME-separation
- ✓ calculation_data sparar hela beräkningen som JSON

---

## 2. INPUT-VALIDERING - UI-nivå

### Patientdata:
| Fält | Min | Max | Steg | Validering |
|------|-----|-----|------|------------|
| **Ålder** | 18 | 100 | 1 | ✓ Räckvidden OK |
| **Vikt** | 30 | 250 | 1 | ✓ Räckvidden OK (extremt övervikt täckt) |
| **Längd** | 100 | 220 | 1 | ✓ Räckvidden OK |
| **Op-tid (h)** | 0 | 12 | 1 | ✓ Räckvidden OK |
| **Op-tid (min)** | 0 | 45 | 15 | ✓ Räckvidden OK |
| **Fentanyl** | 0 | 500 | 25 | ✓ Räckvidden OK (500μg är hög men möjlig) |

### ⚠️ PROBLEM 1: Ålder minimum 18 år
**Nuvarande:** `min=18`
**Problem:** Systemet är ej testat för barn, men barn kan behöva anestesi
**Lösning:** Antingen:
- Lägg till explicit varning: "Ej validerat för <18 år"
- Eller tillåt men varna: "VARNING: Pediatrisk dosering ej validerad"

### ⚠️ PROBLEM 2: Fentanyl max 500μg
**Nuvarande:** `max=500`
**Fråga:** Kan vissa operationer (t.ex. hjärtkirurgi) kräva >500μg?
**Förslag:** Öka till 1000μg med steg 50μg

### Outcome-data:
| Fält | Min | Max | Steg | Validering |
|------|-----|-----|------|------------|
| **Given dos** | 0 | ∞ | 0.25 | ✓ OK |
| **VAS** | 0 | 10 | 1 | ✓ OK |
| **UVA dos** | 0 | ∞ | 0.25 | ✓ OK |
| **Postop tid (h)** | 0 | 48 | 1 | ✓ OK (2 dygn) |
| **Postop tid (min)** | 0 | 55 | 5 | ✓ OK |

### ✅ Alla validerade korrekt!

---

## 3. INLÄRNINGS-GRÄNSER - Verifiering

### System 1: Calibration Factor
**Nuvarande logik:**
```python
learning_rate = 0.30 if num_cases < 3 else 0.15 if num_cases < 10 else 0.05
if rescue_dose > 7: learning_rate *= 2.0  # Max 60%
elif rescue_dose > 4: learning_rate *= 1.5  # Max 45%
```

**Gränser:**
- Initial: 30% justering per fall
- Efter 10 fall: 5% justering
- Med rescue >7mg: 60% justering (aggressivt!)

**⚠️ PROBLEM 3: Ingen övre gräns för calibration_factor**
```python
# SAKNAS:
if calibration_factor > 3.0:  # Max 3× standard-dos
    calibration_factor = 3.0
if calibration_factor < 0.3:  # Min 30% av standard-dos
    calibration_factor = 0.3
```

### System 2: Adjuvant Effectiveness
**Nuvarande logik:**
```python
learning_rate = 0.15 if num_updates < 3 else 0.075 if num_updates < 10 else 0.025
adjustment = learning_rate * adjustment_direction
new_multiplier = old_multiplier + adjustment
```

**⚠️ PROBLEM 4: Ingen gräns för adjuvant multipliers**
NSAID börjar på 0.75 (25% reduktion), men kan teoretiskt bli:
- 0.0 (100% reduktion - orealistiskt!)
- 1.5 (ökar smärta?! - omöjligt!)

**Lösning:**
```python
# Adjuvants ska ALDRIG öka MME
new_multiplier = max(0.5, min(1.0, new_multiplier))
# Min 50% av bas-effekt, max ingen effekt (1.0)
```

### System 3: Fentanyl Remaining Fraction
**Nuvarande logik:**
```python
adjustment = -adjustment_direction * 0.03  # 2-3% justering
new_fraction = old_fraction + adjustment
```

**⚠️ PROBLEM 5: Ingen gräns för fentanyl fraction**
Startar på 0.175 (17.5%), men kan teoretiskt bli:
- Negativ (omöjligt!)
- >1.0 (mer än 100% kvar - omöjligt!)

**Lösning:**
```python
new_fraction = max(0.05, min(0.50, new_fraction))
# Min 5% kvar (snabb metabolisering)
# Max 50% kvar (långsam metabolisering)
```

### System 4: baseMME per Ingrepp
**Nuvarande logik:**
```python
if abs(calibration_factor - 1.0) < 0.15:  # Skydd aktivt
    base_mme_adjustment = adjustment * default_base_mme * 0.10
    new_base_mme = old_base_mme + base_mme_adjustment
```

**⚠️ PROBLEM 6: Ingen gräns för baseMME**
Höftledsplastik börjar på 26 MME, men kan teoretiskt bli:
- 0 MME (ingen smärta - orealistiskt!)
- 100 MME (50 mg oxycodone för höft?!)

**Lösning:**
```python
# Tillåt max ±50% från default
min_base_mme = default_base_mme * 0.5
max_base_mme = default_base_mme * 1.5
new_base_mme = max(min_base_mme, min(max_base_mme, new_base_mme))
```

### System 5: painTypeScore
**Nuvarande logik:**
```python
# Batch learning var 5:e fall efter fall 15
if score_diff > 0.3: adjustment = +0.3  # Reducerat från 0.5 ✓
elif score_diff < -0.3: adjustment = -0.3
```

**✅ KORREKT GRÄNSAD:**
- painTypeScore är 0-10 skala
- Max ±0.3 per batch
- Kommer aldrig gå utanför 0-10

---

## 4. BERÄKNINGSLOGIK - Edge Cases

### Edge Case 1: Extremt överviktig patient
**Scenario:** 180 cm, 200 kg, BMI 61.7
- IBW = 75 kg
- ABW = (200-75)*0.4 + 75 = 125 kg
- Weight factor = 125/75 = 1.67

**Resultat:** Dos ökar med 67%
**Fråga:** Är detta korrekt? Obesa patienter har ofta oförändrat Vd för opioder.

**⚠️ PROBLEM 7: ABW-korrektion kanske för aggressiv**
**Förslag:**
```python
# Begränsa weight_factor
weight_factor = max(0.7, min(1.5, abw / reference_weight))
# Max ±50% dos-justering för vikt
```

### Edge Case 2: Ingen fentanyl given
**Scenario:** Fentanyl = 0 μg
```python
fentanyl_mme_deduction = (fentanyl_dose / 100 * 10) * fentanyl_remaining_fraction
# = 0 / 100 * 10 * 0.175 = 0 ✓ Korrekt!
```

### Edge Case 3: Alla adjuvanter samtidigt
**Scenario:** NSAID + Catapressan + Droperidol + Ketamine + Lidocaine + Betapred
```python
mme = 26  # Höftledsplastik
× 0.75 (NSAID 800mg)
× 0.8 (Catapressan)
× 0.85 (Droperidol)
× 0.70 (Ketamine stor infusion)
× 0.8 (Lidocaine infusion)
× 0.92 (Betapred 8mg)
= 26 × 0.75 × 0.8 × 0.85 × 0.70 × 0.8 × 0.92
= 5.9 MME ≈ 3 mg oxycodone
```

**⚠️ PROBLEM 8: Multiplikativ effekt kan ge för låg dos**
6 adjuvanter → 77% reduktion → 3 mg för höftledsplastik (för lite!)

**Förslag:**
```python
# Maximal total reduktion
total_multiplier = product_of_all_multipliers
if total_multiplier < 0.3:  # Max 70% total reduktion
    total_multiplier = 0.3
mme = base_mme * total_multiplier
```

### Edge Case 4: ASA 5 patient
**Nuvarande:** Ingen ASA-specifik justering i beräkning
**Fråga:** Ska ASA 4-5 patienter få lägre doser (risk för andningsdepression)?

**Förslag:**
```python
if asa == '5':
    mme *= 0.7  # 30% reduktion för moribund patient
elif asa == '4':
    mme *= 0.85  # 15% reduktion för allvarligt sjuk
```

---

## 5. DATABAS-KONSISTENS - Verifiering

### Kontrollera att alla fält verkligen sparas:

**UI → get_current_inputs() → save_case() → Databas**

#### Patientdata:
- ✓ age, sex, weight, height → BMI/IBW/ABW beräknas
- ✓ asa, opioidHistory, lowPainThreshold
- ✓ specialty, surgery_type, procedure_id

#### Operationsdata:
- ✓ optime_minutes (kombinerat från hours + minutes)
- ✓ fentanylDose

#### Adjuvanter:
- ✓ nsaid (bool) + nsaid_choice (text)
- ✓ catapressan, droperidol (bool)
- ✓ ketamine (text för backwards) + ketamine_choice (ny)
- ✓ lidocaine, betapred (text)

#### Outcome:
- ✓ givenDose, vas, uvaDose
- ✓ postop_minutes
- ✓ postop_reason, respiratory_status, severe_fatigue
- ✓ rescue_early, rescue_late

#### Beräkning:
- ✓ calculation_data (hela calculation-objektet som JSON)

### ⚠️ PROBLEM 9: Saknas validering vid sparande
**Nuvarande:** save_case() tar emot case_data utan validering
**Risk:** Felaktig data kan sparas (t.ex. negativ vikt)

**Förslag:**
```python
def save_case(case_data: Dict, user_id: int) -> int:
    # Validera innan sparande
    if case_data.get('weight', 0) < 30 or case_data.get('weight', 0) > 300:
        raise ValueError(f"Ogiltig vikt: {case_data.get('weight')}")
    if case_data.get('age', 0) < 0 or case_data.get('age', 0) > 120:
        raise ValueError(f"Ogiltig ålder: {case_data.get('age')}")
    # ... osv för alla fält
```

---

## 6. INLÄRNINGS-TRIGGERS - Verifiering

### Kontrollera att alla inlärningssystem aktiveras korrekt:

**handle_save_and_learn() i oxydoseks.py rad 445-702:**

1. ✓ **Calibration factor** (rad 580-597)
   - Aktiveras: ALLTID när outcome loggas
   - Hastighet: 30% → 5% baserat på antal fall

2. ✓ **Adjuvant effectiveness** (rad 598-665)
   - Aktiveras: När adjuvant använd OCH adjustment != 0
   - NSAID: Per nsaid_choice (rad 619-632)
   - Catapressan: Generisk (rad 634-639)
   - Droperidol: Generisk (rad 641-646)
   - Ketamine: Per ketamine_choice (rad 648-662)
   - Lidocaine: Saknas! ⚠️
   - Betapred: Saknas! ⚠️

3. ✓ **Fentanyl fraction** (rad 667-680)
   - Aktiveras: Endast vid rescue_early (tidig smärta)
   - Hastighet: 2-3% justering

4. ✓ **baseMME** (rad 685-696)
   - Aktiveras: När abs(calibration_factor - 1.0) < 0.15
   - Skydd: Endast när calibration nära default
   - Hastighet: 10% av avvikelsen

5. ✓ **painTypeScore** (rad 698-707)
   - Aktiveras: Var 5:e fall efter fall 15 (batch)
   - Kräver: ≥5 NSAID-fall OCH ≥3 Catapressan-fall
   - Hastighet: ±0.15-0.3 baserat på signal

### ⚠️ PROBLEM 10: Lidocaine och Betapred inlärning saknas!

**Nuvarande:** Endast NSAID, Catapressan, Droperidol, Ketamine lär sig
**Saknas:** Lidocaine och Betapred

**Förslag:** Lägg till i handle_save_and_learn():
```python
# Efter ketamine learning (rad 662):
if current_inputs.get('lidocaine') and current_inputs['lidocaine'] != 'Nej':
    med = pc.MEDICATIONS.get('lidocaine', {})
    lidocaine_base_mults = {
        'Bolus': 0.90,
        'Infusion': 0.80
    }
    base_mult = lidocaine_base_mults.get(current_inputs['lidocaine'], 0.85)
    new_mult = db.update_adjuvant_effectiveness(...)
    adjuvant_updates.append(f"Lidocaine {current_inputs['lidocaine']}: {new_mult:.2f}")

if current_inputs.get('betapred') and current_inputs['betapred'] != 'Nej':
    med = pc.MEDICATIONS.get('betapred', {})
    betapred_base_mults = {
        '4 mg': 0.96,
        '8 mg': 0.92
    }
    base_mult = betapred_base_mults.get(current_inputs['betapred'], 0.94)
    new_mult = db.update_adjuvant_effectiveness(...)
    adjuvant_updates.append(f"Betapred {current_inputs['betapred']}: {new_mult:.2f}")
```

---

## 7. UI/UX - Användarupplevelse

### Kontrollera att allt är intuitivt och tydligt:

#### ✅ Startsida:
- Login/registrering tydlig
- Autofyll för user_id fungerar ✓

#### ✅ Patientinformation:
- Ålder, vikt, längd med räckvidden ✓
- ASA, opioidhistorik, smärttröskel ✓
- Beräknad BMI/IBW/ABW visas ✓

#### ✅ Operation:
- Procedurval från 84 ingrepp ✓
- Op-tid i timmar + minuter ✓
- Fentanyl-dos ✓

#### ✅ Adjuvanter:
- NSAID: Rullgardinsmeny 4 alternativ ✓
- Catapressan, Droperidol: Toggle ✓
- Ketamine: Rullgardinsmeny 4 alternativ ✓
- Lidocaine: Radio buttons (Nej/Bolus/Infusion) ✓
- Betapred: Radio buttons (Nej/4mg/8mg) ✓

#### ⚠️ PROBLEM 11: Inkonsekvent UI för adjuvanter
- NSAID: Selectbox
- Ketamine: Selectbox
- Lidocaine: Radio buttons
- Betapred: Radio buttons

**Förslag:** Standardisera - antingen alla selectbox eller alla radio buttons

#### ✅ Dosrekommendation:
- Tydlig visning av dos ✓
- Förklaring av beräkning ✓
- Confidence-indikator (grönt/gult/rött) ✓

#### ✅ Outcome-logging:
- Given dos (pre-fylld med rekommendation) ✓
- VAS-skala 0-10 ✓
- Rescue-dos ✓
- Rescue timing (tidig/sen) ✓
- Andningsstatus, trötthet ✓

#### ⚠️ PROBLEM 12: Rescue timing kan vara förvirrande
**Nuvarande:** Två checkboxes "Rescue <30 min" och "Rescue >30 min"
**Risk:** Användare kan välja båda eller ingen

**Förslag:**
```python
rescue_timing = st.radio("När gavs rescue-doser?",
                        ["Ingen rescue", "Tidig (<30 min)", "Sen (>30 min)", "Både tidig och sen"])
```

---

## 8. SÄKERHET OCH GDPR

### Patientintegritet:
- ✓ Inget personnummer lagras
- ✓ Endast ålder, kön, vikt, längd
- ⚠️ SAKNAS: Anonymisering efter 90 dagar (enligt PRESENTATION_OVERSIKT.md)

**Förslag:** Lägg till i database.py:
```python
def anonymize_old_cases(days_old: int = 90):
    """Anonymisera fall äldre än X dagar"""
    conn = get_connection()
    cursor = conn.cursor()
    cutoff_date = datetime.now() - timedelta(days=days_old)

    cursor.execute('''
        UPDATE cases
        SET age = NULL, sex = NULL, weight = NULL, height = NULL,
            bmi = NULL, ibw = NULL, abw = NULL
        WHERE timestamp < ?
    ''', (cutoff_date,))

    conn.commit()
    conn.close()
```

### Lösenordssäkerhet:
- ✓ Bcrypt hashing (i auth.py)
- ✓ Salted hashes

### Databassäkerhet:
- ✓ SQLite med check_same_thread=False
- ⚠️ SAKNAS: Kryptering av databas-fil

---

## 9. PRESTANDA

### Potentiella Flaskhalsar:

1. **Database queries i UI-rendering:**
   - `get_all_cases()` hämtar ALLA fall varje gång
   - Vid 10,000+ fall kan detta bli långsamt

**Förslag:**
```python
def get_cases_paginated(offset: int = 0, limit: int = 100):
    # Paginering istället för att hämta allt
```

2. **XGBoost-träning vid varje outcome:**
   - Nuvarande: Tränar modell varje gång (om >30 fall)
   - Vid 1000+ fall kan detta ta >5 sekunder

**Förslag:**
```python
# Träna endast var 10:e fall
if total_cases % 10 == 0:
    train_xgboost_model()
```

---

## 10. FELHANTERING

### Saknade error handlers:

1. **Database connection failure:**
```python
def get_connection():
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        return conn
    except Exception as e:
        st.error(f"Databasfel: {e}")
        return None
```

2. **Invalid calculation (division by zero):**
```python
if reference_weight == 0:
    weight_factor = 1.0  # Fallback
else:
    weight_factor = abw / reference_weight
```

3. **Missing procedure in pain_classification.py:**
```python
procedure = next((p for p in pc.PROCEDURES_WITH_PAIN_SCORES if p['id'] == procedure_id), None)
if procedure is None:
    st.error(f"Ingrepp {procedure_id} finns ej i databasen!")
    return None
```

---

## SAMMANFATTNING - Kritiska Fixes Behövs

### 🔴 KRITISKA (Måste fixas före produktion):
1. ❌ **Calibration factor** saknar gränser (kan bli 0 eller ∞)
2. ❌ **Adjuvant multipliers** saknar gränser (kan bli <0 eller >1)
3. ❌ **Fentanyl fraction** saknar gränser (kan bli negativ)
4. ❌ **baseMME** saknar gränser (kan bli 0 eller 100+)
5. ❌ **Lidocaine och Betapred** lär sig inte
6. ❌ **Multiplikativ adjuvant-effekt** kan ge för låg dos (total mult <0.3)

### 🟡 VIKTIGA (Bör fixas snart):
7. ⚠️ **ABW weight factor** kanske för aggressiv (max ±50% föreslås)
8. ⚠️ **ASA 4-5** borde reducera dos (säkerhet)
9. ⚠️ **Validering vid sparande** saknas
10. ⚠️ **Rescue timing UI** kan vara förvirrande
11. ⚠️ **Anonymisering** saknas (GDPR)

### 🟢 MINDRE VIKTIGA (Nice to have):
12. 💡 Öka fentanyl max till 1000μg
13. 💡 Standardisera adjuvant-UI (alla selectbox)
14. 💡 Paginering för databas-queries
15. 💡 Bättre error handling

---

## NÄSTA STEG

1. **Fixa kritiska gränser** (calibration, adjuvant, fentanyl, baseMME)
2. **Lägg till Lidocaine/Betapred learning**
3. **Implementera total multiplier floor** (min 0.3)
4. **Lägg till input-validering** i save_case()
5. **Testa edge cases** (extremvikt, alla adjuvanter, ASA 5)
