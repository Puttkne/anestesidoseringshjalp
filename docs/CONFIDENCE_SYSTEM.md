# Konfidenssystem - Implementationsöversikt

## Översikt
Systemet visar nu varningar när det har låg konfidenskontroll för dosrekommendationer och uppmuntrar användare att logga utfall även i dessa fall för att förbättra algoritmerna.

## Konfidenskritierier

### Låg Konfidenskontroll definieras som:
```python
low_confidence = (num_proc_cases < 3 and abs(calibration_factor - 1.0) < 0.1) or num_total_cases < 5
```

**Kriterier:**
1. **Färre än 3 fall** för detta specifika ingrepp OCH systemet har inte lärt sig (kalibreringsfaktor ~1.0)
2. **ELLER** totalt **färre än 5 fall** i hela databasen

### Hög/Normal Konfidenskontroll:
- ≥3 fall för ingreppet OCH systemet har lärt sig
- ELLER ≥10 fall för ingreppet (XGBoost-modellen aktiveras)

## Användargränssnitt vid Låg Konfidenskontroll

### 1. Varningsmeddelande (Vänster kolumn - Rekommendation)
```
⚠️ Låg konfidenskontroll - Använd kliniskt omdömme!

📊 Detta ingrepp har endast X loggade fall. Systemet kan inte ge en
tillförlitlig dosrekommendation ännu.

Vi uppmuntrar dig starkt att logga given dos och utfall så att
algoritmerna kan lära sig och förbättras för framtida fall!

💡 Förslag från basmodell: X mg (Regelmotor)
⚙️ Använd denna som en utgångspunkt och justera efter klinisk bedömning.
```

### 2. Uppmuntran till Loggning (Höger kolumn - Logga Utfall)
```
✨ Ditt bidrag är särskilt värdefullt!
Genom att logga detta fall hjälper du systemet att lära sig och
ge bättre rekommendationer nästa gång.
```

### 3. Normal Visning (vid tillräcklig data)
```
Motor: Regelmotor | XGBoost (X fall)
[Stor metric med dos]

ℹ️ Baserad på X tidigare fall för detta ingrepp  (om <10 fall)
```

## Användarflöde

### Scenario 1: Första fallet för ett nytt ingrepp
1. Användaren väljer ett ingrepp som aldrig loggats
2. System visar: "⚠️ Låg konfidenskontroll"
3. Basmodellens förslag visas som referens
4. Användare använder kliniskt omdömme
5. **Uppmuntras kraftigt** att logga given dos och utfall
6. När loggat → bidrar till framtida rekommendationer

### Scenario 2: Få fall (1-2 loggade)
1. Visar varning om låg konfidenskontroll
2. Förslag baserat på regelmotor + de tidigare fallen
3. Uppmuntrar loggning för att nå ≥3 fall

### Scenario 3: Tillräcklig data (≥3 fall, lärt sig)
1. Normal visning med metrisk dos
2. Visar antal tidigare fall om <10
3. Standard uppmuntran att logga för kontinuerlig förbättring

### Scenario 4: Mycket data (≥10 fall)
1. XGBoost-modellen aktiveras
2. Visar "Motor: XGBoost (X fall)"
3. Hög konfidensnivå, men loggar fortfarande för förbättring

## Procedurdatabas

### Aktuell Status
- **84 totala ingrepp** klassificerade
- Fördelning per specialitet:
  - Kirurgi: 24 ingrepp
  - Ortopedi: 18 ingrepp
  - Gynekologi: 16 ingrepp
  - Urologi: 11 ingrepp
  - ÖNH: 9 ingrepp
  - Tand: 6 ingrepp

### Smärttyp-fördelning
- **Visceral (0-3):** 23 ingrepp (27%)
  - Exempel: TUR-P, Ureteroskopi, Laparoskopisk kolecystektomi
- **Blandad (4-6):** 13 ingrepp (15%)
  - Exempel: Kejsarsnitt, Öppen kolektomi, Explorativ laparotomi
- **Somatisk (7-10):** 48 ingrepp (58%)
  - Exempel: Höftprotes, Ljumskbråck, Tonsillektomi

## Fördelar med Konfidenssystemet

### 1. Patientsäkerhet
- Varnar när systemet inte har tillräcklig data
- Uppmuntrar kliniskt omdömme över algoritmisk rekommendation
- Transparent om osäkerhetsnivå

### 2. Kontinuerlig Förbättring
- Uppmuntrar loggning även vid låg konfidenskontroll
- Bygger databas för sällsynta ingrepp
- Accelererar inlärning för nya procedurer

### 3. Användarförtroende
- Ärlig om systemets begränsningar
- Visar antal fall som ligger till grund för rekommendation
- Tydligt när användarens bidrag är särskilt värdefullt

### 4. Datadriven Utveckling
- Identifierar vilka ingrepp som behöver mer data
- Möjliggör riktad datainsamling
- Stödjer kvalitetssäkring av rekommendationer

## Teknisk Implementation

### Filer Modifierade
- **oxydoseks.py (rad 573-607):** Konfidenskontroll i rekommendationsvy
- **oxydoseks.py (rad 657-679):** Uppmuntran i loggningsvy

### Beräkningslogik
```python
# Hämta antal fall
num_proc_cases = antal fall för detta ingrepp
num_total_cases = totalt antal fall i databasen
calibration_factor = inlärd kalibreringsfaktor

# Beslut
if (num_proc_cases < 3 and abs(calibration_factor - 1.0) < 0.1) or num_total_cases < 5:
    # Visa låg konfidensvarning
    low_confidence = True
else:
    # Normal visning
    low_confidence = False
```

## Framtida Förbättringar

### Kortsiktiga
- Visa konfidenspoäng (0-100%) baserat på antal fall och learning
- Grafer som visar konfidens per specialitet
- Exportera "low confidence procedures" för riktad datainsamling

### Långsiktiga
- Bayesiansk konfidensintervall för dosrekommendation
- Meta-learning: lära från liknande ingrepp
- Collaborative filtering: dela anonymiserad data mellan användare
- Adaptive sampling: föreslå vilka ingrepp som bör prioriteras för loggning

## Rekommendationer för Användning

### För Kliniker
1. **Respektera varningen** - använd alltid kliniskt omdömme vid låg konfidenskontroll
2. **Logga systematiskt** - även negativa utfall hjälper systemet lära
3. **Komplettera data** - kom tillbaka och uppdatera postop-data när tillgängligt

### För Administratörer
1. **Övervaka låg-konfidensfall** - identifiera vilka ingrepp som behöver mer data
2. **Uppmuntra datainsamling** - incitament för att logga sällsynta procedurer
3. **Kvalitetskontroll** - granska rekommendationer för ingrepp med 3-10 fall

### För Forskning
1. **Analysera inlärningskurvor** - hur många fall krävs för tillförlitliga rekommendationer?
2. **Jämför visceral vs somatisk** - skiljer sig datakrav baserat på smärttyp?
3. **Utvärdera transfer learning** - kan data från liknande ingrepp användas?
