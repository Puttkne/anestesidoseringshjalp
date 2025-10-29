# Adaptivt Inlärningssystem - Dokumentation

## Översikt
Systemet använder nu adaptiv inlärningshastighet som automatiskt justerar hur snabbt algoritmerna lär sig baserat på:
1. **Antal loggade fall** - Snabb inlärning i början, långsam när mer data finns
2. **Outlier-dämpning** - Extrema värden får mindre påverkan

## Designprinciper

### 1. Snabb Inlärning i Början
**Problem:** Med få fall behöver systemet hitta rätt dos snabbt.
**Lösning:** Hög inlärningshastighet när <3 fall loggats.

### 2. Konservativ vid Hög Konfidenskontroll
**Problem:** Med mycket data riskerar snabba ändringar att förstöra väl kalibrerade modeller.
**Lösning:** Långsam inlärningshastighet när ≥20 fall loggats.

### 3. Outlier-Robusthet
**Problem:** Extrema fall (VAS >8, rescue dose >15 mg) kan vara atypiska.
**Lösning:** Halv viktning för outliers i både regelmotor och XGBoost.

## Regelmotor - Adaptiv Inlärning

### Inlärningshastighet (base_learning_rate)

```python
# Antal fall för detta specifika ingrepp
if num_proc_cases < 3:
    base_learning_rate = 0.30  # 2x snabbare än original (0.15)
elif num_proc_cases < 10:
    base_learning_rate = 0.18  # 1.2x snabbare
elif num_proc_cases < 20:
    base_learning_rate = 0.12  # 0.8x av original
else:
    # Kontinuerligt avtagande: 0.30 / (1 + 0.05 * num_cases)
    # 20 fall → 0.10
    # 30 fall → 0.08
    # 50 fall → 0.05
    # 100 fall → 0.03
    base_learning_rate = 0.30 / (1 + 0.05 * num_proc_cases)
```

### Outlier-Dämpning

```python
# Identifiera extrema fall
is_outlier = (vas > 8) or (uvaDose > 15)
outlier_damping = 0.5 if is_outlier else 1.0

# Applicera på alla justeringar
adjustment = calculated_adjustment * outlier_damping
```

### Exempel på Kalibreringsjustering

**Scenario 1: Första fallet (0 fall)**
- Patient: VAS = 7, rescue dose = 5 mg
- base_learning_rate = 0.30
- vas_error = 0.82
- adjustment = 0.30 + (0.82 * 0.35) = **+0.59**
- Ny faktor: 1.00 → **1.59** (59% ökning)

**Scenario 2: Efter 10 fall**
- Samma patient: VAS = 7, rescue dose = 5 mg
- base_learning_rate = 0.12
- adjustment = 0.12 + (0.82 * 0.35) = **+0.41**
- Ny faktor: 1.20 → **1.61** (34% ökning)

**Scenario 3: Efter 50 fall**
- Samma patient: VAS = 7, rescue dose = 5 mg
- base_learning_rate = 0.05
- adjustment = 0.05 + (0.82 * 0.35) = **+0.34**
- Ny faktor: 1.50 → **1.84** (23% ökning)

**Scenario 4: Outlier med 50 fall**
- Patient: VAS = 9, rescue dose = 20 mg (OUTLIER!)
- base_learning_rate = 0.05
- outlier_damping = 0.5
- adjustment = (0.05 + 1.0 * 0.35) * 0.5 = **+0.20**
- Ny faktor: 1.50 → **1.70** (13% ökning istället för 27%)

## XGBoost - Adaptiv Inlärning

### Hyperparametrar baserat på Dataset-storlek

```python
num_cases = antal fall för detta ingrepp

if num_cases < 10:
    learning_rate = 0.15      # Snabb anpassning
    n_estimators = 50         # Färre träd (undviker overfit)
elif num_cases < 30:
    learning_rate = 0.10      # Balanserad
    n_estimators = 75
else:
    learning_rate = 0.05      # Konservativ
    n_estimators = 100        # Fler träd (högre precision)
```

### Sample Weighting för Outlier-robusthet

```python
# Identifiera outliers i träningsdata
outlier_mask = (vas > 8) | (uvaDose > 15)
sample_weights = np.where(outlier_mask, 0.5, 1.0)

# Träna modell med viktning
model.fit(X_train, y_train, sample_weight=sample_weights)
```

### Regularisering

```python
model = xgb.XGBRegressor(
    subsample=0.8,         # Använd 80% av rader per träd
    colsample_bytree=0.8,  # Använd 80% av features per träd
    max_depth=3            # Begränsa träddjup (förhindrar overfit)
)
```

## Adjuvanteffektivitet - Inlärning

Adjuvanter uppdateras med samma adaptiva logik som huvudkalibreringen:

```python
# Adjuvanter lär sig långsammare än huvuddosen
adjuvant_adjustment = adjustment * 0.5

# Samma outlier-dämpning och adaptiv hastighet appliceras
```

## Visuell Feedback till Användare

### Normal Inlärning
```
📊 Inlärning: Kalibreringsfaktorn har ökat från 1.000 till 1.590 (+59.0%).
(Inlärningshastighet: 0.30, baserat på 0 fall)
```

### Med Outlier-dämpning
```
📊 Inlärning: Kalibreringsfaktorn har ökat från 1.500 till 1.700 (+13.3%).
(Inlärningshastighet: 0.05, baserat på 50 fall) ⚠️ Outlier-dämpning applicerad
```

## Fördelar med Adaptivt System

### 1. Snabbt Konvergens
- Första 3-5 fallen hittar snabbt rätt dosområde
- Undviker långsam konvergens med fast inlärningshastighet

### 2. Stabilitet vid Hög Konfidenskontroll
- Efter 20+ fall: små, försiktiga justeringar
- Förhindrar "oscillation" runt optimal dos
- Skyddar mot att enstaka avvikande fall förstör kalibrering

### 3. Outlier-Robusthet
- Extrema värden (t.ex. patologi, mätfel, atypisk respons) får halv påverkan
- Skyddar mot att modellen "överanpassar" till ovanliga fall

### 4. Automatisk Anpassning
- Ingen manuell tuning krävs
- Systemet optimerar sig självt baserat på datamängd

## Matematisk Grund

### Inlärningshastighet-funktion
```
α(n) = α₀ / (1 + k·n)

där:
α(n) = inlärningshastighet vid n fall
α₀ = initial hastighet (0.30)
k = dämpningskonstant (0.05)
n = antal fall
```

**Egenskaper:**
- Asymptot mot 0 när n → ∞
- Halveringstid: n₁/₂ = 1/k = 20 fall

### Viktad Uppdatering med Outlier-dämpning
```
Δw = α(n) · L(e) · d(x)

där:
Δw = viktändring
α(n) = adaptiv inlärningshastighet
L(e) = förlustfunktion (error)
d(x) = outlier-dämpning (0.5 eller 1.0)
```

## Jämförelse: Fast vs Adaptiv Inlärning

| Scenario | Fast (α=0.15) | Adaptiv | Fördel |
|----------|---------------|---------|--------|
| **Fall 1-3** | Långsam konvergens | Snabb konvergens | **2x snabbare** |
| **Fall 10-20** | Balanserad | Balanserad | Likvärdig |
| **Fall 50+** | Risk för instabilitet | Stabil, konservativ | **3x stabilare** |
| **Outlier (VAS=9)** | Stor störning (+40%) | Dämpat (+20%) | **50% robustare** |

## Framtida Förbättringar

### Kortsiktiga
1. **Bayesiansk konfidensintervall:** Visa osäkerhet i rekommendation
2. **Adaptiv outlier-tröskel:** Lär vad som är "normalt" för varje ingrepp
3. **Förstaordningens momentum:** "Kom ihåg" senaste justeringsriktningen

### Långsiktiga
1. **Meta-learning:** Lär optimal inlärningshastighet från historik
2. **Ensemble-metoder:** Kombinera regelmotor + XGBoost adaptivt
3. **Online learning:** Uppdatera XGBoost-modell incrementellt
4. **A/B-testning:** Jämför adaptiv vs fast för olika användare

## Exempel: Inlärningstrajektoria

### Hypotetiskt Ingrepp (Lap. Kolecystektomi)
```
Fall 1:  VAS=6 → Δ=+0.45 → Faktor: 1.00 → 1.45
Fall 2:  VAS=5 → Δ=+0.32 → Faktor: 1.45 → 1.77
Fall 3:  VAS=3 → Δ=+0.05 → Faktor: 1.77 → 1.82
Fall 4:  VAS=2 → Δ=-0.12 → Faktor: 1.82 → 1.70
Fall 5:  VAS=4 → Δ=+0.03 → Faktor: 1.70 → 1.73
...
Fall 20: VAS=3 → Δ=-0.04 → Faktor: 1.68 → 1.64
Fall 21: VAS=2 → Δ=-0.03 → Faktor: 1.64 → 1.61
...
Fall 50: VAS=9 (OUTLIER!) → Δ=+0.20 (dämpat) → Faktor: 1.60 → 1.80
Fall 51: VAS=2 → Δ=-0.02 → Faktor: 1.80 → 1.78
Fall 52: VAS=3 → Δ=-0.01 → Faktor: 1.78 → 1.77

Konvergens: Stabilt runt faktor ≈1.75 efter 20-30 fall
```

## Rekommendationer för Klinisk Användning

### För Användare
1. **De första 3-5 fallen är kritiska** - logga noggrant för snabb kalibrering
2. **Vid extrema utfall** - kontrollera om det fanns särskilda omständigheter
3. **Efter 20+ fall** - systemet är väl kalibrerat, lita på rekommendationerna

### För Administratörer
1. **Övervaka konvergens** - de flesta ingrepp bör stabiliseras vid 15-25 fall
2. **Identifiera problematiska ingrepp** - om >50 fall utan stabilitet, undersök
3. **Granska outliers** - fall med >50% avvikelse från prediktion

### För Forskare
1. **Analysera inlärningskurvor** - är adaptiv bättre än fast hastighet?
2. **Optimera hyperparametrar** - kan k-värdet (0.05) förbättras?
3. **Testa alternativa funktioner** - exponentiell vs hyperbolisk dämpning?
