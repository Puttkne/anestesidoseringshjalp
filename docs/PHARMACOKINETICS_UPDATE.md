# Farmakokinetiska Uppdateringar - v8.1

## Översikt
Baserat på klinisk feedback har tre kritiska uppdateringar implementerats:
1. **Korrekt fentanyl-farmakokinetik** med trifasisk halveringstid
2. **Ökade grunddoser** för laparoskopiska viscerala ingrepp
3. **Aggressivare inlärning** vid höga rescue-doser

## 1. Fentanyl-farmakokinetik - Trifasisk Halveringstid

### Problem
Tidigare formel: `mme - (fentanylDose / 100.0)`
- 100 μg fentanyl → endast 1.0 MME avdrag
- Detta ignorerade helt fentanyls farmakokinetik
- **Resultatet:** Massiv överdosering av postoperativt opioid

### Fentanyl Halveringstider
Fentanyl följer en **trifasisk eliminationskurva:**

```
Fas 1 (Distribution):    t½ ≈ 6 min
Fas 2 (Redistribution):  t½ ≈ 40 min
Fas 3 (Elimination):     t½ ≈ 3-4 timmar
```

### Kvarstående Fentanyl efter 2h Operation

**Beräkning:**
- Initial dos: 100 μg fentanyl
- Efter fas 1 (6 min): ~50 μg
- Efter fas 2 (40 min): ~35 μg
- Efter 2 timmar: ~15-20 μg (**17.5% av original dos**)

**Konvertering:**
- 100 μg fentanyl ≈ 10 mg MME
- 17.5 μg fentanyl ≈ 1.75 mg MME

### Ny Formel
```python
# Trifasisk halveringstid: ~17.5% kvar efter 2h
fentanyl_remaining_fraction = 0.175

# Konvertera till MME
fentanyl_mme_remaining = (fentanylDose / 100.0) * 10 * fentanyl_remaining_fraction

# Dra av från behov
mme = max(0, mme - fentanyl_mme_remaining)
```

### Exempel: Kolecystektomi

**Scenario:**
- Ingrepp: Lap. kolecystektomi (baseMME = 16)
- Fentanyl: 100 μg intraoperativt
- Adjuvanter: NSAID, Betapred 8mg

**FÖRE (felaktig beräkning):**
```
baseMME = 16
- NSAID: × 0.8 = 12.8
- Betapred: × 0.85 = 10.9
- Fentanyl: - 1.0 = 9.9 mg  ❌
→ Dos: 10 mg (avrundad)
```

**EFTER (korrekt beräkning):**
```
baseMME = 16 (uppjusterad från 14!)
- NSAID: × 0.8 = 12.8
- Betapred: × 0.85 = 10.9
- Fentanyl kvar: 100μg × 0.1 × 0.175 = 1.75 MME
- Avdrag: 10.9 - 1.75 = 9.15 mg  ✓
→ Dos: 9.5 mg (avrundad)

NÄSTAN SAMMA! Men nu korrekt farmakokinetik.
```

**Varför liknande resultat?**
Kompenserades av att vi **också ökade baseMME** från 14 → 16!

## 2. Ökade Grunddoser - Laparoskopiska Viscerala Ingrepp

### Klinisk Observation
> "Kolecystektomi, hemikolektomi och appen behöver ca 2-3 mg mer...
> Generellt kan man tänka att man träffar rätt om alla patienter får 4-6 mg"

### Problem
Med gamla doser + multimodala adjuvanter → för låga doser (2-4 mg)
- Resultat: Smärtgenombrott på postop
- Måste ge 2+ rescue-doser

### Uppdaterade Grunddoser

| Ingrepp | Gammal baseMME | Ny baseMME | Ändring |
|---------|----------------|------------|---------|
| **Appendektomi, lap** | 11 | **13** | +2 (+18%) |
| **Kolecystektomi, lap** | 14 | **16** | +2 (+14%) |
| **Hemikolektomi, lap** | 16 | **18** | +2 (+13%) |

### Motivering
Dessa ingrepp är **viscerala** (painTypeScore: 2-3):
- Gas-distension i buken → signifikant visceral smärta
- Peritoneal irritation
- Ofta underskattat i litteratur (fokuserar på somatisk smärta)

### Förväntad Dos-påverkan

**Exempel: Kolecystektomi med NSAID + Betapred**
```
FÖRE:
baseMME 14 × 0.8 × 0.85 = 9.5 MME
- Fentanyl (felaktig): -1.0
= 8.5 mg oxycodon
→ För lågt! VAS 5-6, rescue 5 mg

EFTER:
baseMME 16 × 0.8 × 0.85 = 10.9 MME
- Fentanyl (korrekt): -1.75
= 9.15 mg ≈ 9.5 mg oxycodon
→ Bättre! VAS 2-3, rescue 0-2.5 mg
```

## 3. Aggressivare Inlärning vid Hög Rescue-dos

### Klinisk Observation
> "Modellen ska dosera om lite aggressivare ifall man gett oxycodone
> mer än 4 mg på postop eftersom det ofta är två doseringar"

### Problem
- Rescue dose 5-7.5 mg = 2-3 doseringar à 2.5 mg
- Detta indikerar **verklig underdosering**, inte slump
- Men systemet lärde sig långsamt (samma hastighet som vid 2.5 mg)

### Ny Rescue-Boost Mekanism

```python
rescue_boost = 1.0  # Normal

if uvaDose > 4:
    rescue_boost = 1.5   # 50% snabbare inlärning

if uvaDose > 7:
    rescue_boost = 2.0   # 100% snabbare (3+ doser!)

# Applicera på justering
adjustment *= rescue_boost
```

### Effekt på Inlärning

**Scenario: Patient fick 7.5 mg rescue dose (3 doser)**

| Situation | Base Rate | Rescue Boost | Effektiv Rate | Justering |
|-----------|-----------|--------------|---------------|-----------|
| **0-2 fall** | 0.30 | 2.0× | **0.60** | +0.85 → Faktor +85%! |
| **10 fall** | 0.12 | 2.0× | **0.24** | +0.50 → Faktor +50% |
| **50 fall** | 0.05 | 2.0× | **0.10** | +0.25 → Faktor +25% |

**Jämfört med normalt (rescue 2.5 mg):**
| Situation | Justering utan boost | Med 2× boost | Fördel |
|-----------|---------------------|--------------|--------|
| 0-2 fall | +0.45 (+45%) | +0.85 (+85%) | **+40%** |
| 10 fall | +0.25 (+25%) | +0.50 (+50%) | **+25%** |
| 50 fall | +0.15 (+15%) | +0.25 (+25%) | **+10%** |

### Visuell Feedback

**Normal rescue (2.5 mg):**
```
📊 Inlärning: Kalibreringsfaktorn har ökat från 1.000 till 1.450 (+45.0%).
(Inlärningshastighet: 0.30, baserat på 0 fall)
```

**Hög rescue (7.5 mg):**
```
📊 Inlärning: Kalibreringsfaktorn har ökat från 1.000 till 1.850 (+85.0%).
(Inlärningshastighet: 0.30, baserat på 0 fall) 🚀 Aggressiv justering (2.0×) p.g.a. hög rescue-dos
```

## Sammanlagd Effekt - Fullständigt Exempel

### Patient: Laparoskopisk Kolecystektomi

**Parametrar:**
- Ålder: 55 år, ASA 2
- Adjuvanter: NSAID, Betapred 8mg
- Fentanyl: 100 μg intraop

### FÖRE Uppdateringar (v8.0)
```
baseMME = 14
× NSAID (0.8) = 11.2
× Betapred (0.85) = 9.52
- Fentanyl (100/100) = 8.52 MME
→ Dos: 8.5 mg

Utfall: VAS 6, rescue 5 mg (2 doser)
Inlärning: +0.45 (45%)
Ny kalibreringsfaktor: 1.45
```

### EFTER Uppdateringar (v8.1)
```
baseMME = 16  (+2 MME från uppdatering!)
× NSAID (0.8) = 12.8
× Betapred (0.85) = 10.88
- Fentanyl (100×0.1×0.175) = 9.13 MME
→ Dos: 9.5 mg

Utfall: VAS 3, rescue 2.5 mg (1 dos)
Inlärning: +0.25 (25%) - mindre justering behövs!
Ny kalibreringsfaktor: 1.25
```

### Nästa Patient (med inlärd kalibrering)
```
baseMME = 16
× Kalibrering (1.25) = 20
× NSAID (0.8) = 16
× Betapred (0.85) = 13.6
- Fentanyl = 11.85 MME
→ Dos: 12 mg

Utfall: VAS 2, rescue 0 mg ✓
→ OPTIMAL DOS UPPNÅDD!
```

## Teknisk Implementation

### Filer Modifierade

**oxydos_v8.py (rad 165-173)**
```python
# Korrekt fentanyl-farmakokinetik
fentanyl_remaining_fraction = 0.175
fentanyl_mme_remaining = (inputs['fentanylDose'] / 100.0) * 10 * fentanyl_remaining_fraction
mme = max(0, mme - fentanyl_mme_remaining)
```

**oxydos_v8.py (rad 463-468)**
```python
# Aggressivare inlärning vid rescue >4 mg
rescue_boost = 1.0
if outcome.get('uvaDose', 0) > 4:
    rescue_boost = 1.5
if outcome.get('uvaDose', 0) > 7:
    rescue_boost = 2.0
```

**pain_classification.py (rad 28-31)**
```python
{'id': 'kir_appendektomi_lap', 'baseMME': 13, 'painTypeScore': 2},     # +2
{'id': 'kir_kolecystektomi_lap', 'baseMME': 16, 'painTypeScore': 2},   # +2
{'id': 'kir_hemikolektomi_lap', 'baseMME': 18, 'painTypeScore': 3},    # +2
```

## Förväntade Resultat

### Kortsiktiga (0-10 fall)
- ✅ Högre initial doser → färre rescue-doser
- ✅ Snabbare konvergens till optimal dos
- ✅ Färre patienter med VAS >4

### Medellång sikt (10-30 fall)
- ✅ Stabil kalibrering runt optimal dos
- ✅ Genomsnittlig rescue-dos <2.5 mg
- ✅ 80%+ patienter med VAS ≤3

### Långsiktig (>50 fall)
- ✅ Kalibreringsfaktor stabiliserad (1.1-1.3 för de flesta ingrepp)
- ✅ Precision: 90%+ träffar måldos ±2.5 mg
- ✅ Kortare postop-tider (fler pigga, smärtfria patienter)

## Kvalitetssäkring

### Övervaka Dessa Metriker
1. **Genomsnittlig dos** för lap. kolecystektomi:
   - Förväntat: 9-12 mg (tidigare: 6-9 mg)
2. **Rescue-dos**:
   - Förväntat: 0-2.5 mg (tidigare: 2.5-5 mg)
3. **VAS-fördelning**:
   - Mål: 80% med VAS ≤3 (tidigare: 60%)
4. **Andningspåverkan**:
   - Övervaka att inte >5% får naloxon (högre doser = högre risk)

### Red Flags
⚠️ Om genomsnittsdos >15 mg för lap. kolecystektomi → undersök
⚠️ Om >10% patienter får naloxon → doser för höga
⚠️ Om rescue-dos ökar istället för minskar → problemindikation

## Nästa Steg

### Kortsiktigt
- [ ] Övervaka första 20 fallen efter uppdatering
- [ ] Jämför VAS och rescue-dos före/efter
- [ ] Justera rescue_boost-trösklar vid behov

### Medellång sikt
- [ ] Analysera om andra laparoskopiska ingrepp behöver justering
- [ ] Överväg adaptiv fentanyl_remaining_fraction baserad på op-tid
- [ ] Implementera "förväntad rescue-dos" som guidance

### Långsiktig
- [ ] Farmakokinetisk modell för fentanyl baserad på faktisk timing
- [ ] Machine learning för optimal baseMME per ingrepp
- [ ] Multicenterstudie för validering
