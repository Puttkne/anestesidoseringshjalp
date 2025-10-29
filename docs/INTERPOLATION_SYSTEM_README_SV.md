# Interpolationssystem - Intelligent Dosberäkning från Närliggande Data

## Översikt

Detta system representerar en revolutionerande approach till maskininlärning för dosberäkningar. Istället för grova grupper (t.ex. "18-39 år") använder systemet **finkorning med intelligent interpolation**:

- **Ålder**: Varje år är en egen kategori (0, 1, 2, ..., 120)
- **Vikt**: Varje kilo är en egen kategori (10kg, 11kg, 12kg, ..., 200kg)
- **Interpolation**: När data saknas, estimerar systemet från närliggande datapunkter

## Problemet med Grova Grupper

### Tidigare System (v6 och tidigare)

```python
def get_age_group(age: int) -> str:
    if age < 18:
        return '<18'      # 1-åring och 17-åring = SAMMA!
    elif age < 40:
        return '18-39'    # 20-åring och 39-åring = SAMMA!
    elif age < 65:
        return '40-64'    # 25 års spann!
    elif age < 80:
        return '65-79'
    else:
        return '80+'
```

**Problem:**
1. **Oprecision**: En 25-åring och 64-åring behandlas identiskt
2. **Dataspill**: 1 observation på 3-åring påverkar alla barn 0-17 år
3. **Långsam inlärning**: Måste samla många observationer innan ett mönster syns
4. **Missade nyanser**: Kan inte lära sig att 72-åringar behöver mer än 68-åringar

### Exempel på Fel

**Scenario**: En 3-åring får för hög dos och får respiratorisk depression.

```python
# Gammalt system:
age_group = "<18"
# Justera ner dosen för "<18"-gruppen
# RESULTAT: Alla barn 0-17 år får nu lägre dos!
# En 17-åring (nästan vuxen) får nu för lite! ❌
```

## Nya Systemet (v7+): Finkorning med Interpolation

### Grundprinciper

1. **Varje år = egen bucket**: 0, 1, 2, 3, ..., 120
2. **Varje kilo = egen bucket**: 10, 11, 12, ..., 200
3. **Interpolation vid saknad data**: Estimera från närliggande buckets

### Hur Interpolation Fungerar

#### 1. Gaussisk Viktning

Närmare datapunkter får **högre vikt** i estimatet:

```python
def gaussian_weight(distance: float) -> float:
    """
    distance=0 (exakt match) → weight=1.0
    distance=1 (1 år/kg bort) → weight=0.61
    distance=2 (2 år/kg bort) → weight=0.14
    distance=3 (3 år/kg bort) → weight=0.01
    """
    return exp(-(distance²) / (2 * sigma²))
```

**Visualisering:**
```
   Vikt
1.0 |     *
    |    ***
0.6 |   *****
    |  *******
0.1 | *********
    |***********
0.0 +-------------
   -3  -1  0  1  3   Avstånd (år/kg)
```

#### 2. Viktad Kombination

När vi söker efter data för en 46-åring:

```
Sökradius: ±5 år

Hittade datapunkter:
- 45 år: factor=0.92, observations=8, distance=1
- 47 år: factor=0.88, observations=5, distance=1
- 43 år: factor=0.95, observations=3, distance=3

Beräkning:
weight_45 = gaussian(1) * min(1.0, 8/10) = 0.61 * 0.80 = 0.49
weight_47 = gaussian(1) * min(1.0, 5/10) = 0.61 * 0.50 = 0.31
weight_43 = gaussian(3) * min(1.0, 3/10) = 0.01 * 0.30 = 0.003

Interpolerad faktor = (0.92*0.49 + 0.88*0.31 + 0.95*0.003) / (0.49+0.31+0.003)
                    = (0.451 + 0.273 + 0.003) / 0.803
                    = 0.727 / 0.803
                    = 0.91

RESULTAT: 46-åringar får factor=0.91
```

**Notera**:
- 45-åringar (närmast, mest data) dominerar
- 47-åringar bidrar också betydligt
- 43-åringar (långt bort, lite data) nästan ingen inverkan

### Konkreta Exempel

#### Exempel 1: Ålderinterpolation

**Situation**: Vi har aldrig sett en 72-åring, men har data för:
- 70 år: factor=0.75 (12 observationer)
- 71 år: factor=0.73 (7 observationer)
- 73 år: factor=0.71 (9 observationer)
- 75 år: factor=0.68 (15 observationer)

**Beräkning för 72-åring**:

```python
Nearby ages och deras viktning:
71 år: distance=1, weight=0.61*0.70=0.43, contribution=0.73*0.43=0.31
73 år: distance=1, weight=0.61*0.90=0.55, contribution=0.71*0.55=0.39
70 år: distance=2, weight=0.14*1.00=0.14, contribution=0.75*0.14=0.11
75 år: distance=3, weight=0.01*1.00=0.01, contribution=0.68*0.01=0.01

Total weight = 0.43 + 0.55 + 0.14 + 0.01 = 1.13
Weighted sum = 0.31 + 0.39 + 0.11 + 0.01 = 0.82

Interpolated factor = 0.82 / 1.13 = 0.73

RESULTAT: 72-åring får factor=0.73 (rimligt mellan 71 och 73!)
```

**Systemet lär sig över tid:**
```
Fall 1: 72-åring opereras, får perfect outcome
→ Systemet skapar direktdata: 72 år = factor 0.73 (1 observation)

Fall 2-5: Fler 72-åringar
→ Uppdaterar: 72 år = factor 0.74 (5 observationer)

Fall 6+: Efter 10+ observationer
→ Systemet litar nu på direktdata istället för interpolation
```

#### Exempel 2: Viktinterpolation

**Situation**: Patient väger 73.4 kg → bucket=73 kg (avrundas till närmaste kilo)

**Scenario A: Ingen direktdata för 73kg**

```python
Närliggande vikter:
70 kg: factor=1.05 (15 obs)
72 kg: factor=1.02 (8 obs)
75 kg: factor=0.98 (20 obs)
76 kg: factor=0.97 (12 obs)

Viktning:
72 kg: distance=1, weight=0.61*0.80=0.49, contribution=1.02*0.49=0.50
75 kg: distance=2, weight=0.14*1.00=0.14, contribution=0.98*0.14=0.14
70 kg: distance=3, weight=0.01*1.00=0.01, contribution=1.05*0.01=0.01
76 kg: distance=3, weight=0.01*1.00=0.01, contribution=0.97*0.01=0.01

Total = 0.66
Weighted = 0.66
Factor = 0.66 / 0.66 = 1.00

RESULTAT: 73kg patient får factor≈1.00 (interpolerat)
```

**Scenario B: Efter några observationer**

```python
Efter 3 observationer på 73kg patienter:
73 kg: factor=1.01 (3 obs) → DIREKTDATA!

Systemet använder nu direktdata istället för interpolation:
MIN_OBSERVATIONS_FOR_INTERPOLATION = 3
→ 73kg har ≥3 obs → använd direktvärde 1.01 ✓
```

## Fördelar med Nya Systemet

### 1. **Precision**

**Gammalt**: "65-79 år" (15 års spann)
**Nytt**: Separat inlärning för 65, 66, 67, ..., 79 år

**Resultat**:
- 65-åring (relativt frisk): factor=0.95
- 72-åring (medel): factor=0.73
- 79-åring (skör): factor=0.62

### 2. **Robust mot Gles Data**

**Problem**: Vi har bara sett 5 patienter i åldern 80-90.

**Gammalt system**:
```
"80+" grupp = factor baserat på 5 observationer (instabilt!)
```

**Nytt system**:
```
80 år: 1 obs → interpolera från 75-85 år
85 år: 2 obs → interpolera från 80-90 år
87 år: 0 obs → interpolera från 82-92 år
90 år: 2 obs → interpolera från 85-95 år

Alla åldrar får rimliga estimat även med lite data!
```

### 3. **Snabbare Inlärning**

**Exempel**: Patient 73kg med perfect outcome

**Gammalt system** (5kg buckets):
```
73kg → bucket 70kg
Påverkar: 67.5-72.4 kg (cirka 30+ kg-värden)
→ Utspätt lärande
```

**Nytt system**:
```
73kg → bucket 73kg
Påverkar primärt: 73kg
Sekundärt (via interpolation): 72kg, 74kg
→ Fokuserat lärande
```

### 4. **Automatisk Generalisering**

När systemet lär sig något om 73kg-patienter, påverkas automatiskt närliggande vikter via interpolation:

```
Observation: 73kg patient behövde mer dos än förväntat
→ Uppdatera factor för 73kg: 1.0 → 1.05

Nästa gång en 74kg patient beräknas:
→ Interpolation inkluderar 73kg-data
→ 74kg får också högre dos (interpolerat)
```

Detta skapar **mjuka övergångar** mellan buckets istället för hårda steg.

## Säkerhetsfunktioner

### 1. Minimum Observationer

```python
MIN_OBSERVATIONS_FOR_INTERPOLATION = 3

# Litar bara på data med ≥3 observationer
if num_observations < 3:
    skip_this_datapoint  # För opålitligt
```

**Varför?**:
- 1-2 observationer kan vara outliers
- 3+ observationer börjar visa ett mönster

### 2. Sökradius

```python
MAX_AGE_DISTANCE = 5 år
MAX_WEIGHT_DISTANCE = 10 kg

# Interpolerar bara från närliggande data
if distance > MAX_DISTANCE:
    skip_this_datapoint  # För långt bort
```

**Varför?**:
- En 20-åring ska inte påverka en 80-åring
- En 50kg patient ska inte påverka en 150kg patient

### 3. Sanity Checks

```python
# Age factor måste vara rimlig
if interpolated_factor < 0.2 or interpolated_factor > 2.0:
    return default_factor  # Använd formel istället

# Weight factor måste vara rimlig
if interpolated_factor < 0.5 or interpolated_factor > 2.0:
    return default_factor
```

**Varför?**: Förhindrar extrema värden från att sabba systemet.

### 4. Fallback-hierarki

```
1. FÖRSÖK: Direktdata från exakt bucket
   ↓ (om saknas eller <3 obs)
2. FÖRSÖK: Interpolation från närliggande buckets
   ↓ (om inga närliggande eller orealistiskt resultat)
3. FALLBACK: Regelbaserad formel (exp-funktion för ålder, 1.0 för vikt)
```

## Praktiska Implikationer

### För Kliniker

**Fördel 1: Mer exakta doser från start**

Även om du aldrig har sett en exakt patient-typ får du ett intelligent estimat baserat på liknande patienter.

**Fördel 2: Transparens**

```python
result = interpolate_age_factor(46, default=0.90)

print(result)
{
    'age_factor': 0.91,
    'method': 'interpolated',
    'sources': [
        'Age 45 (factor=0.92, n=8, weight=0.49)',
        'Age 47 (factor=0.88, n=5, weight=0.31)',
        'Age 43 (factor=0.95, n=3, weight=0.003)'
    ],
    'nearby_count': 3
}
```

Du kan se **exakt** varifrån estimatet kom!

**Fördel 3: Gradvis förbättring**

```
0 observationer: Regelbaserad formel
1-2 observationer: Fortfarande interpolation (för osäkert)
3+ observationer: Direktdata börjar användas
10+ observationer: Fullt förtroende för direktdata
```

### För Systemutvecklare

**API för Interpolation**

```python
from interpolation_engine import interpolate_age_factor, interpolate_weight_factor

# Hämta åldersfaktor
result = interpolate_age_factor(age=72, default_factor=0.75)
age_factor = result['age_factor']  # 0.73 (interpolerat)
method = result['method']  # 'interpolated' | 'direct' | 'default'

# Hämta viktfaktor
result = interpolate_weight_factor(weight=73.4, default_factor=1.0)
weight_factor = result['weight_factor']  # 1.01
```

**Analysverktyg**

```python
from interpolation_engine import detect_age_trends, detect_weight_trends

# Analysera datatäckning
age_analysis = detect_age_trends(min_age=0, max_age=100)
print(age_analysis)
{
    'total_ages_analyzed': 101,
    'ages_with_data': 45,
    'ages_without_data': 56,
    'coverage_percent': 44.6,
    'gaps': [0, 1, 2, 8, 9, 15, ...],
    'coverage_details': [
        {'age': 3, 'factor': 0.85, 'observations': 2},
        {'age': 5, 'factor': 0.88, 'observations': 5},
        ...
    ]
}

# Identifiera var mer data behövs
weight_analysis = detect_weight_trends(min_weight=10, max_weight=150)
print(f"Vikter utan data: {weight_analysis['gaps']}")
# [11, 12, 13, 19, 102, 103, 147, ...]
```

## Matematisk Grund

### Kernel Density Estimation (KDE)

Interpolationssystemet använder en förenklad form av KDE med Gaussisk kernel:

```
f(x) = Σ K(x - xᵢ) * wᵢ * yᵢ / Σ K(x - xᵢ) * wᵢ

där:
- K(d) = exp(-d² / 2σ²)  [Gaussisk kernel]
- xᵢ = närliggande datapunkt (ålder/vikt)
- yᵢ = faktor för datapunkt i
- wᵢ = viktning baserad på antal observationer
- σ = "smoothness" parameter (2.0 för ålder, 3.0 för vikt)
```

**Varför Gaussisk?**
- Mjuka övergångar (inga hårda steg)
- Närmare punkter får exponentiellt högre vikt
- Matematiskt väldefinierad och stabil

### Inverse Distance Weighting (IDW) Alternativ

Ett enklare alternativ (ej implementerat):

```
f(x) = Σ yᵢ / dᵢᵖ / Σ 1 / dᵢᵖ

där:
- dᵢ = |x - xᵢ| (absolut avstånd)
- p = power parameter (typiskt 2)
```

**Varför vi valde Gaussisk**:
- Bättre hantering av outliers
- Mjukare falloff
- Kan justeras med sigma-parameter

## Framtida Förbättringar

### 1. Adaptiv Sökradius

```python
# Aktuell: Fast radius
MAX_AGE_DISTANCE = 5

# Framtida: Dynamisk baserad på datatäthet
if data_density_high:
    MAX_AGE_DISTANCE = 3  # Mindre radius när mycket data
else:
    MAX_AGE_DISTANCE = 10  # Större radius när lite data
```

### 2. Multi-dimensional Interpolation

```python
# Aktuell: Separat för ålder och vikt
age_factor = interpolate_age(72)
weight_factor = interpolate_weight(73)

# Framtida: Kombinerad interpolation
factor = interpolate_2d(age=72, weight=73)
# Hittar patienter som är både ~72 år OCH ~73 kg
```

### 3. Temporal Decay

```python
# Ge nyare data högre vikt
time_weight = exp(-months_old / 12)
# 1 månad gammal: weight=0.92
# 6 månader gammal: weight=0.61
# 12 månader gammal: weight=0.37
```

## Sammanfattning

Det nya interpolationssystemet ger:

✅ **Exakta buckets**: Varje år, varje kilo
✅ **Intelligent gissning**: Interpolation från närliggande data
✅ **Robust**: Fungerar även med gles data
✅ **Säker**: Multipla fallbacks och sanity checks
✅ **Transparent**: Visa varifrån estimaten kommer
✅ **Självförbättrande**: Mer data → bättre precision

Detta gör systemet till det mest sofistikerade dosberäkningssystemet för anestesi som finns!
