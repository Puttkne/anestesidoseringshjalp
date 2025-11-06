# Anestesi-assistent Alfa V0.8 - En Djupgående Teknisk Förklaring

Välkommen till Anestesi-assistenten, ett avancerat beslutsstöd för anestesipersonal. Detta dokument ger en detaljerad teknisk översikt av applikationens alla delar, från användargränssnittet till de underliggande algoritmerna och maskininlärningssystemen. Målet är att ge en fullständig förståelse för hur varje enskild del fungerar och interagerar med helheten.

## 🆕 **NYA I VERSION 7: INTERPOLATIONSSYSTEM**

Version 7 introducerar ett revolutionerande interpolationssystem för ålder och vikt:

- ✅ **Finkorning**: Varje år (0-120) och varje kilo (10-200kg) är egna kategorier
- ✅ **Intelligent interpolation**: Estimerar från närliggande datapunkter när direktdata saknas
- ✅ **Gaussisk viktning**: Närmare data får exponentiellt högre vikt
- ✅ **Robust**: Fungerar även med gles data

**📖 Läs mer**: Se [INTERPOLATION_SYSTEM_README_SV.md](INTERPOLATION_SYSTEM_README_SV.md) för fullständig dokumentation!

---

## Innehållsförteckning
1.  [Systemarkitektur](#systemarkitektur)
2.  [Databashantering & Backup](#databashantering--backup) **⭐ NYTT!**
    *   [Hur Backup-systemet Fungerar](#hur-backup-systemet-fungerar)
    *   [Skapa och Hantera Backups](#skapa-och-hantera-backups)
    *   [Återställning från Backup](#återställning-från-backup)
    *   [Utvecklingsworkflow med Git](#utvecklingsworkflow-med-git)
3.  [Användargränssnittet (UI) - Detaljerad Genomgång](#användargränssnittet-ui---detaljerad-genomgång)
4.  [Regelbaserade Beräkningsmotorn - Steg för Steg](#regelbaserade-beräkningsmotorn---steg-för-steg)
    *   [Exempelberäkning](#exempelberäkning)
5.  [Inlärningssystemet - Back-Calculation i Detalj](#inlärningssystemet---back-calculation-i-detalj)
    *   [Steg 1: Beräkna Faktiskt Behov (`calculate_actual_requirement`)](#steg-1-beräkna-faktiskt-behov-calculate_actual_requirement)
    *   [Steg 2: Fördela Prediktionsfelet](#steg-2-fördela-prediktionsfelet)
6.  [XGBoost ML-Modell - Under Huven](#xgboost-ml-modell---under-huven)
    *   [Vad är Gradient Boosting?](#vad-är-gradient-boosting)
    *   [Mål-sökande Iteration i Praktiken](#mål-sökande-iteration-i-praktiken)
    *   [Exempel på Funktionsteknik (Feature Engineering)](#exempel-på-funktionsteknik-feature-engineering)
7.  [Djupdykning: Ålder och Vikt - Interpolationssystem (NYA!)](#djupdykning-ålder-och-vikt---interpolationssystem)
    *   [Åldershantering: Finkorning med Interpolation](#åldershantering-finkorning-med-interpolation)
    *   [Vikthantering: Varje Kilo Räknas](#vikthantering-varje-kilo-räknas)
    *   [Hur Interpolation Fungerar](#hur-interpolation-fungerar)
8.  [Kärnkomponenter och Datastrukturer](#kärnkomponenter-och-datastrukturer)
    *   [3D Smärtprofilen](#3d-smärtprofilen)
    *   [4D Kroppssammansättning](#4d-kroppssammansättning)
    *   [Globala Lärandeparametrar](#globala-lärandeparametrar)

---

## Systemarkitektur

Applikationen är byggd i Python med **Streamlit** som webb-ramverk. Den består av två huvudsakliga beräkningsmotorer som arbetar parallellt för att ge en dosrekommendation:

1.  **Regelbaserad Motor (`calculation_engine.py`):** En helt transparent och deterministisk motor. Den använder en serie av matematiska formler och logiska regler baserade på farmakologiska principer. Denna motor är kopplad till ett **globalt inlärningssystem (`learning_engine.py`)** som kontinuerligt justerar motorparametrar baserat på kliniska utfall.

2.  **XGBoost ML-Modell (`ml_model.py`):** En maskininlärningsmodell (Extrem Gradient Boosting) som tränats på historisk data. Den är inte direkt kopplad till det regelbaserade inlärningssystemet, utan måste träna om från grunden på den ackumulerade datan i databasen för att uppdateras. Den fungerar som en oberoende "second opinion".

Data lagras i en **SQLite-databas (`anestesi.db`)**, som hanteras via modulen `database.py`. All logik är separerad i moduler för att underlätta underhåll och utveckling.

---

## Databashantering & Backup

**🆕 NYTT I Alfa V0.8:** Automatiskt backup- och återställningssystem för databaspersistens!

### Problemet med Streamlit Cloud

Streamlit Community Cloud använder **ephemeral (tillfällig) lagring**, vilket innebär:

- ✅ **Data bevaras** när appen går i viloläge
- ⚠️ **Data KAN FÖRLORAS** när appen omstartar eller redeployeras
- 🔄 **Lösning:** Automatiskt backup-system med GitHub-integration

### Hur Backup-systemet Fungerar

Systemet använder **SQLite med automatisk JSON-backup** för att bevara data mellan omstarter:

#### Arkitektur

```
Lokalt (utveckling):
anestesi.db (SQLite) ─────► database_backup.json (JSON)
     ↓                              ↓
Patientdata                   Exporterad backup
Kalibreringsfaktorer         (säker för GitHub)
Användare
Procedurer

Streamlit Cloud (produktion):
Startar med tom databas
     ↓
Upptäcker tom databas
     ↓
Återställer från database_backup.json (från GitHub)
     ↓
Fortsätter med bevarad data ✓
```

#### Säkerhetsfunktioner

- 🔐 **Lösenord INTE i backup** - Endast användarnamn sparas, lösenord återskapas från Streamlit Secrets
- ✅ **database.json skyddad** - Lokal databas med potentiellt känslig data går ALDRIG till GitHub
- ✅ **database_backup.json säker** - Innehåller endast strukturerad data för återställning
- 🔒 **Admin-kontroller** - Endast administratörer kan skapa/återställa backups

### Skapa och Hantera Backups

#### Första Gången (Initial Setup)

1. **Deploya appen till Streamlit Cloud**
2. **Logga in som admin**
   - Användarnamn: `Blapa`
   - Lösenord: `Flubber1`

3. **Använd appen och logga några fall**
   - Detta skapar initial data i databasen

4. **Skapa första backupen:**
   - Gå till **Admin-fliken** → **Systemstatus**
   - Scrolla ner till **"Backup & Återställning"**
   - Klicka **"💾 Skapa Backup Nu"**
   - Vänta tills meddelandet "✅ Backup skapad!" visas

5. **Commit backup till GitHub:**
   ```bash
   # I VS Code eller terminal
   git add database_backup.json
   git commit -m "Add initial database backup"
   git push
   ```

6. **Nu är din data säker!** 🎉

#### Regelbunden Backup (Rekommenderat)

Skapa backups regelbundet, särskilt efter:
- Att ha loggat många nya fall (t.ex. varje vecka)
- Efter viktiga inställningsändringar i Admin-panelen
- Före planerade uppdateringar av applikationen

**Snabbprocess:**
```bash
# 1. Öppna appen → Admin → Skapa Backup Nu
# 2. I terminal:
git add database_backup.json
git commit -m "Update database backup - $(date +%Y-%m-%d)"
git push
```

#### Backup-information

I Admin-panelen ser du:
- ✅ **Backup Status** - Finns backup, när skapades den
- 📊 **Innehåll** - Antal fall, användare, kalibreringsfaktorer
- 📅 **Tidsstämpel** - Exakt när backupen skapades

### Återställning från Backup

#### Automatisk Återställning (Standard)

När appen startar på Streamlit Cloud:

```python
# I oxydoseks.py - initialize_session()
restore_performed = database_backup.auto_restore()
```

**Logik:**
1. Kollar om `anestesi.db` är tom (0 fall)
2. Om tom: Leta efter `database_backup.json`
3. Om backup finns: Återställ automatiskt alla data
4. Om ingen backup: Starta med fresh database

**Resultat:** Data bevaras automatiskt mellan omstarter! ✓

#### Manuell Återställning

Om du behöver återställa manuellt (t.ex. efter dataförlust):

1. **Gå till Admin → Systemstatus → Backup & Återställning**
2. **Klicka "♻️ Återställ från Backup"**
3. **Bekräfta varningen** (detta ersätter nuvarande data!)
4. **Vänta på "✅ Databas återställd!"**

#### Återställning från Fil

Om du har sparat en backup-fil lokalt:

1. **Admin → Systemstatus → Export/Import Backup-fil**
2. **Välj fil** under "⬆️ Ladda upp Backup"
3. **Klicka "📤 Importera Backup"**
4. **Vänta på import**

### Export och Nedladdning

#### Ladda ner Backup (Säker Förvaring)

För att spara en kopia lokalt på din dator:

1. **Admin → Systemstatus → Export/Import**
2. **Klicka "📥 Exportera Backup (JSON)"**
3. **Klicka "💾 Ladda ner backup.json"**
4. **Spara filen** - Den får automatiskt tidsstämpel: `anestesi_backup_20251030_143022.json`

**Användningsområden:**
- Arkivering av historisk data
- Migrering mellan installationer
- Extra säkerhetskopiering utanför GitHub

#### Backup-filformat

```json
{
  "backup_timestamp": "2025-10-30T14:30:22.123456",
  "version": "1.0",
  "users": [
    {
      "id": 1,
      "username": "Blapa",
      "is_admin": 1,
      "created_at": "2025-10-30T10:00:00"
    }
  ],
  "cases": [
    {
      "id": 1,
      "user_id": 1,
      "age": 45,
      "weight": 75,
      "procedure_id": "knee_arthroplasty",
      "given_dose": 7.5,
      "vas": 2,
      ...
    }
  ],
  "calibration_factors": [...],
  "procedures": [...]
}
```

### Utvecklingsworkflow med Git

#### Daglig Utveckling

```bash
# 1. Gör kodändringar i VS Code
# 2. Testa lokalt
streamlit run oxydoseks.py

# 3. Commit kod (INTE database_backup.json om den inte ändrats)
git add oxydoseks.py calculation_engine.py
git commit -m "Fix: Updated dose calculation logic"
git push

# 4. Streamlit Cloud auto-redeployar (2-3 min)
```

#### Efter Betydelsefull Dataändring

```bash
# 1. Använd appen, logga nya fall
# 2. Skapa backup via Admin-panelen
# 3. Commit backup
git add database_backup.json
git commit -m "Backup: Added 25 new cases"
git push
```

#### Workflow-tips

- ✅ **DO:** Commit `database_backup.json` efter datainsamling
- ✅ **DO:** Skapa backup innan stora kodändringar
- ❌ **DON'T:** Commit `anestesi.db` eller `database.json` (skyddade av `.gitignore`)
- ❌ **DON'T:** Commit `.env` eller `secrets.toml` (innehåller lösenord)

### Felsökning

#### "Ingen backup hittades"

**Problem:** Admin-panelen visar ingen backup.

**Lösning:**
```bash
# Kontrollera om fil finns
ls database_backup.json

# Om den inte finns, skapa en:
# 1. Öppna appen lokalt
# 2. Admin → Skapa Backup Nu
# 3. Commit och pusha
```

#### "Backup skapad men data försvann ändå"

**Problem:** Backup skapades men committades inte till GitHub.

**Lösning:**
```bash
# Kolla git status
git status

# Om database_backup.json är "modified" eller "untracked":
git add database_backup.json
git commit -m "Add database backup"
git push

# Nu kommer Streamlit Cloud ha tillgång till backupen
```

#### "Import från backup misslyckades"

**Problem:** Felmeddelande vid återställning.

**Möjliga orsaker:**
1. Korrupt backup-fil
2. Fel format
3. Databaslåsning

**Lösning:**
```bash
# 1. Kontrollera fil-format
cat database_backup.json | head -20

# 2. Verifiera JSON-syntax
python -c "import json; json.load(open('database_backup.json'))"

# 3. Om korrupt, använd tidigare backup eller skapa ny
```

### Avancerad Användning

#### Automatisk Periodisk Backup (Framtida Feature)

För att automatisera backups kan du sätta upp en GitHub Action:

```yaml
# .github/workflows/auto-backup.yml
name: Scheduled Database Backup
on:
  schedule:
    - cron: '0 2 * * 0'  # Varje söndag kl 02:00
  workflow_dispatch:  # Manuell trigger

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Trigger backup via API
        run: |
          # Implementera backup-trigger
          echo "Scheduled backup completed"
```

#### Migrering mellan Miljöer

För att flytta data från lokal utveckling till produktion:

1. **Lokalt:** Exportera backup via Admin-panelen
2. **Ladda ner** backup-filen
3. **Produktionsmiljö:** Importera backup via Admin-panelen
4. **Verifiera** att all data finns

#### Dataanalys från Backup

Backupfilen är ren JSON och kan analyseras:

```python
import json
import pandas as pd

# Läs backup
with open('database_backup.json', 'r') as f:
    backup = json.load(f)

# Analysera fall
cases_df = pd.DataFrame(backup['cases'])
print(f"Totalt antal fall: {len(cases_df)}")
print(f"Genomsnittlig dos: {cases_df['given_dose'].mean():.2f} mg")
print(f"Vanligaste ingrepp: {cases_df['procedure_id'].value_counts().head()}")
```

### Säkerhetsöverväganden

#### Vad Sparas INTE i Backup

- ❌ **Lösenordshashar** - Säkerhet först
- ❌ **Sessionstokens** - Föråldras ändå
- ❌ **Temporära cachade beräkningar**
- ❌ **Loggfiler med potentiell känslig info**

#### Vad Sparas i Backup

- ✅ **Användarnamn** (inga lösenord)
- ✅ **Patientfall** (ålder, vikt, doser, utfall)
- ✅ **Kalibreringsfaktorer** (ML-lärandeparametrar)
- ✅ **Procedurer** (kirurgiska ingrepp och metadata)

#### GDPR-överväganden

Backupfilen innehåller **inga personuppgifter** som kan identifiera patienter:
- Inga personnummer
- Inga namn
- Inga adresser
- Endast kliniska parametrar (ålder, vikt, doser, VAS-score)

**Juridisk bedömning:** Ansvar ligger hos användaren att säkerställa att loggad data följer lokala dataskyddsregler.

---

## Användargränssnittet (UI) - Detaljerad Genomgång

Varje reglage och inmatningsfält är en feature (en variabel) som direkt eller indirekt påverkar slutresultatet. Här är en mer detaljerad förklaring av deras inverkan:

*   **Ålder:** Används i `calculate_age_factor`. Formeln `max(0.4, math.exp((65 - age) / 20))` används för patienter över 65. Detta skapar en exponentiell minskning av dosen. En 85-åring får en initial faktor på `exp(-20/20) = 0.36`, vilket avrundas upp till `0.4`, alltså en 60% dosreduktion jämfört med en person under 65. Denna faktor är självlärande.

*   **Vikt & Längd:** Används för att beräkna flera viktmått. **Lean Body Mass (LBM)** är särskilt viktigt för lipofoba (fettlösliga) läkemedel som distribueras i mager vävnad. Överviktiga patienter doseras inte baserat på totalvikt, utan på **Adjusted Body Weight (ABW)**, som är en kompromiss mellan idealvikt och verklig vikt (`ABW = IBW + 0.4 * (VerkligVikt - IBW)`). Detta förhindrar överdosering.

*   **ASA-klass:** Mappas till en numerisk faktor (t.ex. ASA 1 -> 1.0, ASA 2 -> 1.0, ASA 3 -> 1.1, ASA 4 -> 1.2). En högre siffra indikerar en skörare patient som kan behöva en *högre* dos på grund av ökad stressrespons, men detta kan läras om till att bli en reducerande faktor om data visar det.

*   **Opioidtolerant:** Applicerar en kraftig multiplikator på dosen (t.ex. 1.5x - 2.5x). Denna faktor är en av de mest inflytelserika och är starkt självlärande.

*   **Adjuvanter:** Varje adjuvant har en `potency_percent` i `config.py`. Detta är den **maximala** MME-reduktionen den kan ge. Om Ibuprofen har 15% potens, kan den minska en bas-MME på 20 mg med som mest 3 mg. Den faktiska reduktionen moduleras av 3D-smärtmatchningen.

*   **Fentanyl:** Systemet antar en halveringstid och beräknar hur mycket Fentanyl-MME som återstår vid operationens slut. Formeln tar hänsyn till den givna dosen och tiden som förflutit. Detta är en direkt subtraktion från den totala MME:n.

## Regelbaserade Beräkningsmotorn - Steg för Steg

Motorn utför en pipeline av beräkningar i en fast ordning. Varje steg bygger på det föregående.

1.  **Initialisering:** Hämtar `baseMME` och 3D-smärtprofil (`pain_somatic`, `pain_visceral`, `pain_neuropathic`) för det valda ingreppet från databasen. Dessa värden är redan påverkade av tidigare inlärning.

2.  **Patientfaktorer:** Justerar `baseMME` med alla relevanta patientfaktorer (ålder, ASA, etc.). `MME = baseMME * age_factor * asa_factor * ...`

3.  **4D Kroppskomposition:** Applicerar de fyra inlärda faktorerna från kroppssammansättningssystemet. `MME = MME * weight_bucket_factor * ibw_ratio_factor * ...`

4.  **Adjuvant-beräkning:** Detta är ett kritiskt steg.
    a.  En `base_mme_before_adjuvants` sparas undan. Detta är MME-värdet *innan* adjuvant-reduktioner.
    b.  För varje adjuvant beräknas en reduktion: `reduktion = base_mme_before_adjuvants * adjuvant.potency_percent * mismatch_penalty`.
    c.  `mismatch_penalty` beräknas genom att jämföra adjuvantens 3D-profil med ingreppets 3D-profil. En större skillnad ger en högre penalty (lägre effekt).
    d.  Alla individuella reduktioner summeras till en `total_reduction`.

5.  **Applicera Adjuvant-reduktion:** `MME = base_mme_before_adjuvants - total_reduction`.

6.  **Säkerhetsgränser:** Systemet säkerställer att `MME` inte är lägre än `base_mme_before_adjuvants * ADJUVANT_SAFETY_LIMIT_FACTOR` (t.ex. 0.3). Detta förhindrar att en stor mängd adjuvanter eliminerar opioid-dosen helt.

7.  **Farmakokinetik:** Kvarvarande Fentanyl-MME subtraheras från `MME`.

8.  **Viktjustering & Kalibrering:** En slutgiltig viktjustering baserad på ABW appliceras, och en individuell användarkalibreringsfaktor kan också tillämpas.

9.  **Finalisering:** `final_dose = max(0, MME / 0.25) * 0.25`. Dosen omvandlas från MME till Oxikodon (mg) och avrundas.

### Exempelberäkning

*   **Patient:** 80 år, 80kg, 170cm, ASA 2, för en knäprotes.
*   **Ingrepp (Knäprotes):** `baseMME` = 25, Smärtprofil: {somatisk: 9, visceral: 2, neuropatisk: 4}.
*   **Adjuvanter:** Ibuprofen (Potens: 15%, Profil: {s: 8, v: 5, n: 2}).

1.  **Bas-MME:** 25 mg.
2.  **Åldersfaktor (80 år):** `exp((65-80)/20) = 0.47`. MME = 25 * 0.47 = 11.75 mg.
3.  **Kroppskomposition:** Anta att inlärda faktorer är 1.0. MME förblir 11.75 mg. Detta blir `base_mme_before_adjuvants`.
4.  **Adjuvant (Ibuprofen):**
    *   `potency_percent` = 0.15.
    *   `mismatch_penalty`: Liten skillnad mellan ingreppets (9,2,4) och adjuvantens (8,5,2) profiler. Anta penalty = 0.9.
    *   `reduktion` = 11.75 * 0.15 * 0.9 = 1.59 mg.
5.  **Applicera reduktion:** MME = 11.75 - 1.59 = 10.16 mg.
6.  **Slutgiltig dos:** 10.16 mg MME motsvarar ca 5 mg Oxikodon. Avrundas till 5.0 mg.

## Inlärningssystemet - Back-Calculation i Detalj

Detta är den mest komplexa delen av systemet. Målet är att justera de interna parametrarna så att den rekommenderade dosen i framtiden bättre matchar det faktiska behovet.

### Steg 1: Beräkna Faktiskt Behov (`calculate_actual_requirement`)

Denna funktion är central. Den tar kliniskt utfall och omvandlar det till en siffra: "den dos patienten *borde* ha fått".

*   **Perfekt utfall:** Om `VAS <= 3`, `uvaDose == 0` och inga biverkningar, var den givna dosen perfekt. `actual_requirement = givenDose`.
*   **Underdosering:** Om `VAS > 4` eller `uvaDose > 0`, behövde patienten mer. `actual_requirement` beräknas som `givenDose + uvaDose` plus en extra mängd baserad på hur hög VAS var. En hög VAS indikerar att även `givenDose` var för låg.
*   **Överdosering:** Om patienten hade andningspåverkan eller var kraftigt sederad, var dosen för hög. `actual_requirement` sätts till en lägre dos, t.ex. `givenDose * 0.85`.

Funktionen returnerar också en `learning_magnitude`, som är högre vid stora avvikelser (hög VAS, mycket rescue) och lägre vid små avvikelser. Denna magnitud styrs av en adaptiv inlärningstakt som minskar med antalet fall för ett visst ingrepp.

### Steg 2: Fördela Prediktionsfelet

Felet (`prediction_error = actual_requirement - recommended_dose`) fördelas proportionerligt till de olika parametrarna som bidrog till felet.

*   **`learn_procedure_requirements`:** Justerar `baseMME`. Om `prediction_error` är positiv (systemet rekommenderade för lite), ökas `baseMME` med en liten del av felet: `base_mme_adjustment = prediction_error * learning_magnitude * 0.1`.

*   **`learn_patient_factors`:** Justerar faktorer för ålder, ASA, etc. Om en 85-årig patient konsekvent behöver mer dos än rekommenderat, kommer `age_factor` för åldersgruppen "80+" att justeras uppåt.

*   **`learn_adjuvant_percentage`:** Om `prediction_error` är positiv (patienten behövde mer dos) trots användning av en adjuvant, betyder det att adjuvantens effekt överskattades. Dess `potency_percent` justeras därför nedåt. `adjustment = learning_magnitude * 0.02 * -1`.

*   **`learn_procedure_3d_pain`:** Detta är det mest sofistikerade lärandet. Om en patient behövde mer dos (`prediction_error > 0`) och de använda adjuvanterna var svaga mot neuropatisk smärta, drar systemet slutsatsen att ingreppet troligen har en högre neuropatisk komponent än vad som tidigare var känt. `neuropathic_adjustment` blir då positiv.

## XGBoost ML-Modell - Under Huven

### Vad är Gradient Boosting?

Föreställ dig att du försöker förutsäga en patients VAS-poäng. En enkel modell kanske bara tittar på `baseMME` och gör en grov gissning. Denna modell har många fel (residualer).

Gradient Boosting bygger en serie av "svaga" modeller (beslutsträd) i sekvens. Varje nytt träd tränas inte på att förutsäga VAS, utan på att förutsäga **felen** från föregående träd. Genom att addera förutsägelsen från varje nytt träd, korrigeras felen successivt och modellen blir extremt precis.
XGBoost är en mycket effektiv och optimerad implementation av denna teknik.

### Mål-sökande Iteration i Praktiken

Modellens direkta output är en förutsägelse av VAS. För att omvandla detta till en dosrekommendation, skapas en loop:

```python
predictions = {}
for test_dose in np.arange(0, 20.5, 0.5):
    # Skapa en kopia av patientens data
    predict_row = patient_data.copy()
    # Sätt den simulerade dosen
    predict_row['givenDose'] = test_dose
    # Förutsäg VAS för denna dos
    predicted_vas = model.predict(predict_row)[0]
    predictions[test_dose] = predicted_vas

# Hitta den dos som ger VAS närmast målet (t.ex. 1.0)
best_dose = min(predictions, key=lambda k: abs(predictions[k] - 1.0))
```

Detta gör att vi kan ställa frågan: "Vilken dos måste vi ge för att uppnå ett visst smärtresultat?", vilket är en mycket kraftfullare ansats än att bara fråga "Vad blir smärtan?".

### Exempel på Funktionsteknik (Feature Engineering)

Modellen får inte bara rådata. `feature_engineering.py` skapar nya, mer meningsfulla variabler:

*   **Interaktionstermer:** `age * bmi` - kanske är effekten av högt BMI annorlunda för äldre patienter?
*   **Ratio-variabler:** `fentanyl_dose / weight` - dos per kilo är ofta mer informativt än absolut dos.
*   **Polynomiala features:** `age^2` - för att fånga icke-linjära samband.
*   **Kategoriska kombinationer:** En feature kan representera kombinationen "ASA 3" och "Opioidtolerant".

Detta hjälper modellen att fånga komplexa samband som annars skulle kräva mycket djupare beslutsträd.

## Djupdykning: Ålder och Vikt - Interpolationssystem

**🆕 NYTT I VERSION 7:** Systemet använder nu finkorning med intelligent interpolation istället för grova grupper!

En vanlig fråga är exakt hur ålder och vikt påverkar dosen, och om doseringen är "viktbaserad". Svaret är att systemet använder en betydligt mer sofistikerad metod än en enkel mg/kg-beräkning. Både ålder och vikt hanteras genom ett revolutionerande "interpolationssystem" som lär sig från exakta datapunkter och estimerar intelligent när data saknas.

### Åldershantering: Finkorning med Interpolation

#### Grundformeln (Startpunkt)

Systemet utgår från en farmakokinetisk standardformel för patienter över 65 år: `exp((65 - age) / 20)`. Denna formel ger en initial, exponentiell minskning av dosen. **Detta är dock bara fallback-värdet.**

#### Det Nya Bucketing-systemet (v7+)

**Tidigare (v6):** 5 grova åldersgrupper
```
<18, 18-39, 40-64, 65-79, 80+
Problem: 25-åring och 64-åring = SAMMA grupp!
```

**Nu (v7):** Individuella buckets för varje år
```
0, 1, 2, 3, ..., 119, 120
Varje år är en egen kategori!
```

#### Intelligent Interpolation

**Scenario:** Vi beräknar dos för en 72-åring som vi aldrig sett tidigare.

**Steg 1:** Försök hämta direktdata
```python
direktdata = get_age_bucket_learning(72)
# Ingen data finns för exakt 72 år
```

**Steg 2:** Sök närliggande åldrar (±5 år)
```python
Närliggande data:
- 70 år: factor=0.75 (12 observationer)
- 71 år: factor=0.73 (7 observationer)
- 73 år: factor=0.71 (9 observationer)
- 75 år: factor=0.68 (15 observationer)
```

**Steg 3:** Gaussisk viktning
```python
För 71 år (1 år bort):
  avstånd = 1
  distance_weight = exp(-1²/2*2²) = 0.61
  obs_weight = min(1.0, 7/10) = 0.70
  total_weight = 0.61 * 0.70 = 0.43

För 73 år (1 år bort):
  total_weight = 0.61 * 0.90 = 0.55

För 70 år (2 år bort):
  total_weight = 0.14 * 1.00 = 0.14
```

**Steg 4:** Viktat genomsnitt
```python
interpolerad_faktor = (0.73*0.43 + 0.71*0.55 + 0.75*0.14) / (0.43+0.55+0.14)
                    = 0.73

RESULTAT: 72-åring får factor=0.73 ✓
```

**Över tid:** När vi samlar data för 72-åringar ersätts interpolationen med direktdata!

### Vikthantering: Varje Kilo Räknas

Doseringen är **inte** viktbaserad i den meningen att man tar en fast mg/kg-dos. En sådan metod är för trubbig och leder ofta till farlig överdosering av överviktiga patienter. Istället är vikten en central parameter i en komplex modell som använder flera olika viktmått.

**Vilken vikt används?**

*   **Ideal Body Weight (IBW):** Används som referenspunkt för att bedöma övervikt.
*   **Adjusted Body Weight (ABW):** Används i en **slutgiltig skalning** av dosen. I steget `_apply_weight_adjustment` multipliceras den nästan färdiga MME-dosen med `(abw / REFERENCE_WEIGHT_KG)`. Detta är en kritisk punkt: dosen skalar med den **justerade kroppsvikten**, inte den faktiska, vilket är en säkerhetsmekanism mot överdosering.
*   **Lean Body Mass (LBM):** Används inte i en direkt formel, men är en fundamental farmakokinetisk parameter. Läkemedelsdistributionen (särskilt för opioider) är starkt kopplad till LBM. Genom att träna på och lära av data från patienter med olika kroppssammansättning, lär sig systemet indirekt att anpassa dosen till LBM.
*   **Faktisk Vikt:** Används primärt för att beräkna BMI och de förhållanden som ingår i 4D-inlärningssystemet.

**🆕 Finkornad Viktbucketing med Interpolation (v7+)**

#### Det Nya Systemet: Varje Kilo Räknas

**Tidigare (v6):** Grova vikthinkar
```
2.5kg-intervall upp till 40kg: 37.5, 40.0
5kg-intervall därefter: 70, 75, 80...
Problem: 72kg och 74kg = SAMMA hink (70kg)!
```

**Nu (v7):** Individuella buckets för varje kilo
```
10, 11, 12, 13, ..., 199, 200
Patient 73.4kg → bucket 73kg (avrundas till närmaste)
Patient 73.7kg → bucket 74kg
```

#### Viktinterpolation i Praktiken

**Scenario:** Patient väger 73.4kg → bucket 73kg (ingen tidigare data)

**Steg 1:** Sök närliggande vikter (±10kg)
```python
Närliggande data:
- 70kg: factor=1.05 (15 obs)
- 72kg: factor=1.02 (8 obs)
- 75kg: factor=0.98 (20 obs)
- 76kg: factor=0.97 (12 obs)
```

**Steg 2:** Gaussisk viktning (σ=3.0 för vikt)
```python
72kg (1kg bort):  weight = 0.61 * 0.80 = 0.49
75kg (2kg bort):  weight = 0.14 * 1.00 = 0.14
70kg (3kg bort):  weight = 0.01 * 1.00 = 0.01
```

**Steg 3:** Interpolera
```python
factor = (1.02*0.49 + 0.98*0.14 + 1.05*0.01) / 0.64
       = 1.00

RESULTAT: 73kg patient får factor≈1.00 (intelligent gissning!)
```

**Efter 3+ observationer:**  Systemet använder direktdata istället!

**4D Kroppssammansättning - Komplett System**

Systemet kombinerar nu finkornad viktbucketing MED traditionella body composition metrics:

1.  **Dimension 1: Faktisk Vikt (med Interpolation)**
    *   **Buckets:** Varje kilo (10-200kg)
    *   **Exempel:** 73.4kg → bucket 73kg → interpolera från 70-76kg
    *   **Lärande:** Exakt faktor för varje viktnivå

2.  **Dimension 2: IBW-förhållande**
    *   **Buckets:** 0.1-intervall (0.6, 0.7, 0.8, ..., 2.5)
    *   **Exempel:** Patient 1.47x IBW → bucket 1.5
    *   **Lärande:** Fångar grad av över/undervikt

3.  **Dimension 3: ABW-förhållande**
    *   **Buckets:** 0.1-intervall
    *   **Lärande:** Hur väl ABW-formeln fungerar

4.  **Dimension 4: BMI**
    *   **Buckets:** 7 kliniska kategorier (16, 19, 22, 27, 32, 37, 42)
    *   **Lärande:** BMI-klassspecifika faktorer

**Total Beräkning:**
```python
MME = baseMME
    * age_factor (interpolerad från närliggande åldrar)
    * weight_factor (interpolerad från närliggande vikter)
    * ibw_ratio_factor
    * abw_ratio_factor
    * bmi_factor
    * asa_factor
    * ...
```

### Hur Interpolation Fungerar

Se [INTERPOLATION_SYSTEM_README_SV.md](INTERPOLATION_SYSTEM_README_SV.md) för:
- Matematisk grund (Gaussisk kernel, KDE)
- Säkerhetsfunktioner (minimum observationer, sanity checks)
- Praktiska exempel
- Analysverktyg (`detect_age_trends`, `detect_weight_trends`)

## Kärnkomponenter och Datastrukturer

### 3D Smärtprofilen

Detta är en central datastruktur som representeras som en dictionary, t.ex. `{'somatic': 8, 'visceral': 3, 'neuropathic': 2}`. Siffrorna är på en skala 1-10.

*   **Varför 3D?** Verklig smärta är sällan endimensionell. Ett kirurgiskt ingrepp kan involvera både hudsnitt (somatisk) och manipulation av inre organ (visceral). Genom att modellera detta kan systemet bättre matcha adjuvanter till den specifika smärttypen.
*   **Mismatch Penalty:** Beräkningen av `mismatch_penalty` är en form av viktad distans mellan ingreppets och adjuvantens smärtvektorer. Ju längre ifrån varandra de är i det 3-dimensionella rummet, desto lägre blir den slutgiltiga effekten.

### 4D Kroppssammansättning

Detta system löser problemet med att dosera till patienter med extrem kroppsvikt. Istället för att förlita sig på en enda formel, använder det en **icke-parametrisk, datadriven metod**.

*   **Bucketing:** Genom att gruppera patienter i "buckets" (t.ex. BMI 30-35), kan systemet lära sig en specifik justeringsfaktor för just den gruppen, oberoende av andra grupper. Detta kallas "proximity-based learning".
*   **Varför 4D?** En patient kan ha högt BMI men vara väldigt muskulös (hög LBM), medan en annan kan ha samma BMI men hög fettprocent. Genom att använda fyra olika mått (Vikt, IBW-ratio, ABW-ratio, BMI) får systemet en mer komplett bild av kroppssammansättningen och kan göra mer nyanserade justeringar.

### Globala Lärandeparametrar

Övergången från lokalt till globalt lärande var en kritisk utveckling i v5-v6. I databasen lagras inte bara enskilda fall, utan aggregerade, globala parametrar.

*   **`adjuvant_potency_learning`:** En tabell som lagrar den inlärda `potency_percent` för varje adjuvant (t.ex. `ibuprofen`, `ketamine_small_bolus`).
*   **`procedure_learning_3d`:** En tabell som lagrar den inlärda `base_mme` och 3D-smärtprofilen för varje kirurgiskt ingrepp.
*   **`body_composition_learning`:** En tabell som lagrar de inlärda justeringsfaktorerna för varje bucket i 4D-systemet.

**Fördelen:** Varje enskilt fall som rapporteras in, oavsett från vilken användare, bidrar till att förbättra dessa centrala parametrar. Detta leder till en exponentiellt snabbare och mer robust inlärning för hela systemet, eftersom det drar nytta av en mycket större och mer varierad datamängd.

---

## Säkerhetssystem - Fem Lager av Skydd

Anestesi-assistenten har fem oberoende säkerhetslager som tillsammans förhindrar farlig dosering:

### Lager 1: Hårdkodade Säkerhetsgränser

**Absoluta tak och golv som ALDRIG kan läras bort:**

```python
# I config.py - APP_CONFIG['SAFETY_LIMITS']
ABSOLUTE_MIN_DOSE = 0.0      # Kan aldrig ge negativ dos
ABSOLUTE_MAX_DOSE = 20.0     # Max 20mg oxycodon startdos
MIN_AGE = 0
MAX_AGE = 120
MIN_WEIGHT = 10.0            # Minst 10kg
MAX_WEIGHT = 200.0           # Max 200kg
```

**Dessa gränser kan INTE överskritas av:**
- Inlärning
- Användarinput
- ML-modell
- Kalibreringsfaktorer

### Lager 2: Adjuvant Säkerhetsgräns

**Förhindrar att adjuvanter eliminerar opioiddosen helt:**

```python
ADJUVANT_SAFETY_LIMIT_FACTOR = 0.3  # 30% av bas-MME måste bevaras
```

**Exempel:**
```
Bas-MME före adjuvanter: 15 mg
Beräknad total adjuvantreduktion: 12 mg (80% reduktion!)

Säkerhetskontroll:
minimum_allowed = 15 * 0.3 = 4.5 mg
total_reduction = min(12, 15 - 4.5) = 10.5 mg
Final MME = 15 - 10.5 = 4.5 mg ✓

RESULTAT: Patienten får minst 4.5mg, inte 3mg
```

**Varför?** Även med perfekta adjuvanter behöver patienten ofta en basal opioiddos för intraoperativ stabilitet.

### Lager 3: Adaptiv Inlärningshastighet

**Inlärningen bromsar in automatiskt:**

```python
def get_adaptive_learning_rate(num_cases):
    if num_cases < 10:
        return 0.30    # 30% - snabb initial anpassning
    elif num_cases < 30:
        return 0.18    # 18% - medium anpassning
    elif num_cases < 100:
        return 0.12    # 12% - långsam anpassning
    else:
        return max(0.03, 0.12 * math.exp(-num_cases / 200))
        # Exponentiell decay mot 3% med fler fall
```

**Effekt:**
- **Early phase (0-10 fall):** Stora justeringar för snabb kalibrering
- **Consolidation (10-30 fall):** Medeljusteringar
- **Mature phase (30-100 fall):** Små justeringar
- **Expert phase (100+ fall):** Minimala justeringar, hög stabilitet

**Varför?** Förhindrar att enstaka extremfall förstör väletablerade parametrar.

### Lager 4: Probing på Perfekta Utfall

**"Det hade kunnat gå lika bra med mindre dos"**

När utfallet är PERFEKT (VAS ≤ 2, ingen rescue, inga biverkningar):

```python
# Systemet antar att 97% av dosen hade räckt
actual_requirement = givenDose * 0.97

# Detta driver konstant dosreduktion
prediction_error = actual_requirement - recommended_dose
# Om error < 0: recommended_dose var för hög → minska
```

**Exempel:**
```
Patient fick: 10mg
VAS: 1 (perfekt)
Rescue: 0
Biverkningar: Inga

Systemet slutsats: "9.7mg hade räckt"
recommended_dose var 10mg
→ prediction_error = -0.3mg
→ Nästa patient får 9.7mg istället

Efter många perfekta utfall → dosen sjunker gradvis
```

**Varför?** Systemets primära mål är att hitta LÄGSTA EFFEKTIVA DOS, inte att "spela säkert" med högre doser.

### Lager 5: Sanity Checks vid Interpolation

**När interpolation används (gles data):**

```python
# I interpolation_engine.py
SANITY_CHECK_MAX_FACTOR = 2.0  # Max 2x justering
SANITY_CHECK_MIN_FACTOR = 0.5  # Min 0.5x justering

def sanity_check_factor(interpolated_factor, default_factor):
    # Tillåt max 2x avvikelse från default
    max_allowed = default_factor * SANITY_CHECK_MAX_FACTOR
    min_allowed = default_factor * SANITY_CHECK_MIN_FACTOR

    return max(min_allowed, min(max_allowed, interpolated_factor))
```

**Exempel:**
```
Default åldersfaktor för 72-åring: 0.65
Interpolerad faktor från data: 1.8 (misstänkt hög!)

Sanity check:
max_allowed = 0.65 * 2.0 = 1.30
clamped = min(1.30, 1.8) = 1.30 ✓

RESULTAT: Interpolation kan max dubblera faktorn
```

**Varför?** Skyddar mot outliers och felaktig data som kan ge extrema interpolationer.

---

## Komplett Användarguide - Alla Flikar

### Flik 1: Dosering (Huvudfunktion)

**Syfte:** Beräkna och rekommendera oxycodondos för ett kirurgiskt ingrepp.

#### Steg-för-Steg Workflow:

**1. Patientdata (Vänster kolumn)**

- **Ålder** (0-120 år)
  - Används för: Åldersfaktor, farmakokinetik
  - Exempel: 75 år → exponentiell dosreduktion

- **Kön** (Man/Kvinna)
  - Används för: IBW-beräkning, LBM-beräkning
  - Exempel: Kvinna 165cm → IBW = 60kg

- **Vikt** (10-200 kg)
  - Används för: ABW-beräkning, BMI, 4D learning
  - Exempel: 85kg + 165cm → BMI=31.2

- **Längd** (100-220 cm)
  - Används för: IBW, ABW, BMI

- **ASA-klass** (ASA 1-4)
  - ASA 1: Helt frisk (faktor 1.0)
  - ASA 2: Lindrig systemsjukdom (faktor 1.0)
  - ASA 3: Svår systemsjukdom (faktor 1.1)
  - ASA 4: Livshotande sjukdom (faktor 1.2)

- **Opioidhistorik**
  - Opioidnaiv: Standard (faktor 1.0)
  - Sporadisk användning: Liten tolerans (faktor 1.3)
  - Regelbunden användning: Betydande tolerans (faktor 1.8)
  - Daglig användning: Hög tolerans (faktor 2.5)

- **Låg smärttröskel** (checkbox)
  - Markera om patienten har känd hyperalgesi
  - Ökar dosen med ~20%

- **Nedsatt njurfunktion** (checkbox)
  - Markera om GFR <30 eller dialys
  - Minskar dosen (försiktighetsprincip)

**2. Ingreppsinformation (Höger kolumn)**

- **Specialitet** (dropdown)
  - Ortopedi, Allmänkirurgi, Urologi, Gynekologi, etc.
  - Filtrerar tillgängliga ingrepp

- **Ingrepp** (dropdown)
  - Välj specifikt kirurgiskt ingrepp
  - Varje ingrepp har: baseMME + 3D smärtprofil

- **Typ av kirurgi**
  - Elektivt: Planerad operation (standard)
  - Akut: Brådskande operation (ökad stressrespons)

- **Operationstid**
  - Timmar (0-12) + Minuter (0-59)
  - Används för: Fentanylkinetik, farmakokinetik

**3. Intraoperativa Läkemedel**

**Fentanyl:**
```
Dos (µg): 0-500
Timing: Registrera när given (för kinetikberäkning)

Beräkning:
- Bi-exponentiell decay (t½fast=15min, t½slow=210min)
- Kvarvarande MME vid op-slut subtraheras från behov
```

**NSAID/Paracetamol:**
```
Dropdown-alternativ:
- Ej given
- Ibuprofen 400mg
- Ibuprofen 600mg
- Ibuprofen 800mg
- Diklofenak 50mg
- Diklofenak 75mg
- Paracetamol 1g (checkbox ELLER dropdown)

3D-profil (Ibuprofen): Somatic=8, Visceral=5, Neuropathic=2
Potency: 15% av bas-MME
```

**Catapressan (Klonidin):**
```
Dos (µg): 0-150
3D-profil: Somatic=3, Visceral=7, Neuropathic=8
Potency: 12% av bas-MME
Bonus: Sympatisk dämpning, anti-hyperalgesic
```

**Droperidol:**
```
Checkbox (standard 0.625mg)
3D-profil: Somatic=2, Visceral=4, Neuropathic=5
Potency: 8% av bas-MME
Bonus: Antiemetisk effekt
```

**Ketamin:**
```
Alternativ:
- Nej
- Liten bolus (10-20mg)
- Stor bolus (30-50mg)
- Infusion (0.1-0.3 mg/kg/h)

3D-profil: Somatic=4, Visceral=6, Neuropathic=9
Potency: 18-35% beroende på dos
Mekanism: NMDA-antagonist, anti-hyperalgesi
```

**Lidokain:**
```
Alternativ:
- Nej
- Liten dos (50mg bolus)
- Medel dos (1mg/kg bolus + 1mg/kg/h)
- Hög dos (1.5mg/kg bolus + 2mg/kg/h)

3D-profil: Somatic=5, Visceral=7, Neuropathic=7
Potency: 12-25%
```

**Betapred (Betametason):**
```
Alternativ:
- Nej
- 4mg
- 8mg

3D-profil: Somatic=6, Visceral=8, Neuropathic=4
Potency: 10-15%
Mekanism: Antiinflammatorisk
```

**Sevofluran:**
```
Checkbox (volatil anestesi)
Effekt: Modifierar opioidsvar
```

**Infiltration:**
```
Checkbox (lokal infiltrationsanestesi)
3D-profil: Somatic=9, Visceral=2, Neuropathic=3
Potency: 20%
```

**4. Beräkning och Resultat**

Klicka **"Beräkna Dos"**:

```
Resultat visas i stor grön ruta:

┌────────────────────────────────────────┐
│  REKOMMENDERAD STARTDOS                │
│                                        │
│        7.5 mg Oxikodon                │
│                                        │
│  (2.5ml av 5mg/ml = 12.5ml)           │
│                                        │
│  Baserad på: Regelbaserad motor       │
│  Justerad för: Ålder, vikt, adjuvanter│
└────────────────────────────────────────┘

Detaljerad Uppdelning:
├─ Bas-MME för ingrepp: 18.0 mg
├─ Efter patientfaktorer: 14.2 mg
│  ├─ Åldersfaktor (75 år): 0.68x
│  ├─ ASA 2: 1.0x
│  └─ Opioidnaiv: 1.0x
├─ Efter adjuvanter: 10.5 mg
│  ├─ Ibuprofen 800mg: -2.4 mg
│  ├─ Catapressan 75µg: -1.3 mg
│  └─ Safety limit bevarad: ✓
├─ Efter fentanyl: 8.9 mg
│  └─ Kvarvarande fentanyl: 1.6 mg
└─ Slutgiltig dos: 7.5 mg (avrundad till 2.5mg-steg)
```

**5. Spara Fall**

Efter operationen, registrera utfall:

**Knapp 1: 💾 Spara Som Pågående**
```
Använd när:
- Operationen är klar men utfall ej känt
- Du vill spara för senare redigering
- Patienten fortfarande i uppvaket

Effekt:
✅ Fallet sparas i databasen
✅ Status: IN_PROGRESS
❌ Ingen inlärning sker
✅ Kan redigeras från Historik-fliken
```

**Knapp 2: ✅ Spara och Slutför**
```
Använd när:
- Utfallet är känt och komplett
- VAS, rescue, biverkningar dokumenterade
- Fallet är klart för inlärning

Effekt:
✅ Fallet sparas i databasen
✅ Status: FINALIZED
✅ INLÄRNING TRIGGAS OMEDELBART
✅ Parametrar uppdateras baserat på utfall
❌ Kan EJ redigeras efteråt (för dataintegritet)
```

**Utfallsdata att registrera:**

- **Given startdos** (mg): Faktisk dos du gav patienten
- **VAS-score** (0-10): Smärta i uppvaket
  - 0-2: Perfekt
  - 3-4: Acceptabelt
  - 5-6: Måttlig underdosering
  - 7-10: Kraftig underdosering

- **Rescue-opioid** (mg): Extra opioid i uppvaket

- **Postop tid** (timmar + minuter): Tid i uppvaket

- **Postop anledning**:
  - Normal återhämtning
  - Smärta (tidig/sen)
  - Illamående
  - Andningspåverkan
  - Sedering

- **Andningsstatus**:
  - Vaken och alert
  - Lätt sederad
  - Måttligt sederad
  - Kraftigt sederad

- **Kraftig trötthet** (checkbox)
- **Tidig rescue** (<1h) (checkbox)
- **Sen rescue** (>1h) (checkbox)

**6. Temporal Dosering (Avancerat)**

För komplexa fall med multipla doser över tid:

```
Klicka "Lägg till temporal dos"

┌─────────────────────────────────────┐
│ Tid: [__] minuter efter op-start   │
│ Läkemedel: [Fentanyl ▼]            │
│ Dos: [___] µg                       │
│ [Lägg till]                         │
└─────────────────────────────────────┘

Exempel:
T=0:    Fentanyl 150µg
T=45:   Fentanyl 50µg
T=90:   Fentanyl 50µg
T=120:  Op-slut

Systemet beräknar kvarvarande från ALLA doser:
Total kvarvarande vid op-slut =
  + 150µg efter 120min (liten rest)
  + 50µg efter 75min (viss rest)
  + 50µg efter 30min (större rest)
= ~45µg morphine-equivalenter
```

---

### Flik 2: Historik

**Syfte:** Granska, redigera och analysera tidigare fall.

#### Funktioner:

**1. Fallöversikt (Tabell)**

```
┌────┬─────┬─────┬──────┬─────────────┬──────┬─────┬────────┬──────────┐
│ ID │ Åld │ Vkt │ Ingr │ Given Dos   │ VAS  │ Res │ Status │ Åtgärd   │
├────┼─────┼─────┼──────┼─────────────┼──────┼─────┼────────┼──────────┤
│ 45 │ 72  │ 85  │ TKA  │ 7.5mg       │ 2    │ 0   │ FINAL  │ [Visa]   │
│ 44 │ 58  │ 68  │ Lap  │ 5.0mg       │ 4    │ 2.5 │ FINAL  │ [Visa]   │
│ 43 │ 81  │ 72  │ THA  │ 6.0mg       │ -    │ -   │ IN_PR  │ [Edit]   │
└────┴─────┴─────┴──────┴─────────────┴──────┴─────┴────────┴──────────┘

Filter:
├─ Alla fall / Mina fall / Andras fall
├─ Status: Alla / IN_PROGRESS / FINALIZED
├─ Datumintervall: [Start] - [Slut]
└─ Ingrepp: Alla / Specifikt ingrepp
```

**2. Visa Fall (Klicka "Visa")**

```
═══════════════════════════════════════
FALLDETALJER - Case ID: 45
═══════════════════════════════════════

PATIENT:
├─ Ålder: 72 år
├─ Kön: Man
├─ Vikt: 85 kg
├─ Längd: 175 cm
├─ BMI: 27.8 (Övervikt)
├─ IBW: 75 kg (ratio: 1.13)
├─ ABW: 79 kg
├─ ASA: 2
├─ Opioidhistorik: Naiv
└─ Nedsatt njurfunktion: Nej

INGREPP:
├─ Specialitet: Ortopedi
├─ Ingrepp: Total Knäprotes (TKA)
├─ KVÅ-kod: NGB09
├─ Typ: Elektivt
└─ Op-tid: 95 minuter

ADJUVANTER:
├─ Ibuprofen: 800mg
├─ Catapressan: 75µg
├─ Fentanyl: 200µg (T=-10min)
└─ Infiltration: Ja

REKOMMENDATION:
├─ Regelbaserad motor: 7.5 mg
├─ Base MME: 18.0 mg
├─ Efter faktorer: 13.1 mg
├─ Efter adjuvanter: 9.2 mg
└─ Efter fentanyl: 7.5 mg

UTFALL:
├─ Given dos: 7.5 mg
├─ VAS: 2
├─ Rescue: 0 mg
├─ Postop tid: 2h 15min
├─ Andning: Vaken och alert
└─ Status: FINALIZED ✓

INLÄRNING:
├─ Outcome: PERFECT
├─ Actual requirement: 7.3 mg (97% probing)
├─ Prediction error: -0.2 mg
└─ Parametrar uppdaterade:
    ├─ Age 72: factor 0.730 → 0.728
    ├─ Weight 85kg: factor 1.05 → 1.04
    └─ Ibuprofen potency: 15.2% → 15.4%

[Tillbaka till lista]
```

**3. Redigera Fall (Klicka "Edit")**

**ENDAST för IN_PROGRESS-fall:**

```
⚠️ Redigera Fall - Case ID: 43
Status: IN_PROGRESS

Du kan nu:
├─ Uppdatera utfallsdata (VAS, rescue)
├─ Korrigera felaktig inmatning
├─ Lägga till saknad information
└─ Slutföra fallet för inlärning

[Formulär med alla fält förifyllda...]

Knappar:
├─ [💾 Uppdatera och Behåll Pågående]
│  └─ Sparar ändringar, status=IN_PROGRESS
│
└─ [✅ Uppdatera och Slutför]
   └─ Sparar ändringar, status=FINALIZED, triggar inlärning
```

**GDPR-notering:** Inga personuppgifter sparas. Alla fall är anonyma.

**4. Radera Fall (Admin)**

**ENDAST admin kan radera:**

```
⚠️ VARNING: Radera Fall?

Detta kommer att:
├─ Ta bort fallet permanent från databasen
├─ Ta bort alla associerade temporal doses
├─ INTE återställa inlärda parametrar
└─ Denna åtgärd kan EJ ångras

Skriv "RADERA" för att bekräfta: [________]

[Avbryt] [Radera Fall]
```

**5. Export och Analys**

```
[📊 Exportera alla fall till CSV]
└─ Laddar ner: anestesi_cases_20251106.csv

[📈 Visa statistik]
├─ Totalt antal fall: 127
├─ Genomsnittlig dos: 6.8 mg
├─ Genomsnittlig VAS: 2.4
├─ Perfect outcomes: 68%
├─ Underdosing: 24%
└─ Overdosing: 8%

[📉 Visualisera trender]
└─ Öppnar Utbildning-fliken med grafer
```

---

### Flik 3: Utbildning

**Syfte:** Visualisera systemets inlärning och datamönster.

#### Avsnitt:

**1. Dosrekommendation över Tid**

```
Graf: Genomsnittlig rekommenderad dos (mg)

20mg │
     │    ●
15mg │  ●   ●
     │●       ●   ●
10mg │           ●   ● ● ● ●──●──●──●
     │
 5mg │
     └────────────────────────────────────
      0   20   40   60   80  100  120
              Antal fall

Observation: Dosen stabiliserar efter ~60 fall
```

**2. VAS-Distribution**

```
Histogram: VAS-score fördelning

50 │         ██
   │         ██
40 │      ██ ██
   │      ██ ██
30 │   ██ ██ ██
   │   ██ ██ ██ ██
20 │██ ██ ██ ██ ██
   │██ ██ ██ ██ ██ ██
10 │██ ██ ██ ██ ██ ██ ██
   └──────────────────────
   0  1  2  3  4  5  6  7+
         VAS-score

Målprofil: Majoritet 0-3 ✓
```

**3. Inlärningshastighet**

```
Graf: Learning rate över tid

30% │●
    │
20% │   ●
    │      ●
10% │         ●─●─●─●
    │                   ●────●────●
 0% │
    └────────────────────────────────────
     0   10  20  30  50  80  100  120
              Antal fall

Adaptive decay: 30% → 18% → 12% → 3%
```

**4. Adjuvant Potency Learning**

```
Tabell: Inlärda adjuvantpotenser

┌──────────────────┬─────────┬─────────┬────────┐
│ Adjuvant         │ Initial │ Current │ Change │
├──────────────────┼─────────┼─────────┼────────┤
│ Ibuprofen 800mg  │ 15.0%   │ 15.8%   │ +5.3%  │
│ Catapressan 75µg │ 12.0%   │ 13.2%   │ +10.0% │
│ Ketamin bolus    │ 18.0%   │ 19.4%   │ +7.8%  │
│ Lidokain infusion│ 22.0%   │ 20.1%   │ -8.6%  │
│ Infiltration     │ 20.0%   │ 21.5%   │ +7.5%  │
└──────────────────┴─────────┴─────────┴────────┘

Antal observationer: [visa per adjuvant]
```

**5. Procedur 3D Pain Profiles**

```
3D Visualization: Knäprotes (TKA)

       Neuropathic
            ▲
            │
          5 │      ●
            │     /|\
            │    / | \
            │   /  |  \
          0 │──────┼────────► Somatic
           0│      9 \
            │         \
         Visceral      2

Initial: (S:8, V:2, N:3)
Learned: (S:9, V:2, N:5) ← Neuropatisk ökat!

Implikation: TKA har mer neuropatisk komponent än tidigare känt
→ Ketamin och Catapressan blir mer effektiva
```

**6. Body Composition Learning**

```
Heatmap: Viktbuckets (learning factors)

       2.0 │
           │
   IBW 1.5 │        1.1  1.0  0.9  0.8
   ratio   │        1.2  1.1  1.0  0.9  0.8
       1.0 │   1.3  1.2  1.1  1.0  0.9  0.8
           │   1.4  1.3  1.2  1.1  1.0  0.9
       0.5 │   1.5  1.4  1.3  1.2  1.1  1.0
           └────────────────────────────────
           50  60  70  80  90 100 110 (kg)

Färgkodning:
├─ Blå (>1.0): Behöver mer dos än genomsnitt
└─ Röd (<1.0): Behöver mindre dos än genomsnitt
```

**7. Age Trend Analysis**

```
Graf: Åldersfaktor (interpolerad)

1.2 │
    │●●●●●●●●●●●
1.0 │            ●●●●●●●●●●●●●●●●
    │                              ●●
0.8 │                                ●●
    │                                  ●●
0.6 │
    │
0.4 │                                   ●
    └────────────────────────────────────
     0   20   40   60   80  100  120
              Ålder (år)

Observationer med direktdata: ●
Interpolerade värden: ○
```

**8. Kalibreringsfaktor per Användare**

```
(Endast synlig för Admin)

Tabell: Användarspecifika kalibringar

┌──────────┬────────┬───────────┬─────────────┐
│ User     │ Falls  │ Cal Factor│ Trend       │
├──────────┼────────┼───────────┼─────────────┤
│ Blapa    │ 45     │ 0.98      │ Konservativ │
│ DrSmith  │ 23     │ 1.05      │ Aggressiv   │
│ Nurse01  │ 67     │ 1.00      │ Standard    │
└──────────┴────────┴───────────┴─────────────┘

Notering: Kalibreringsfaktorer är per användare för att
fånga individuella preferenser och lokala protokoll.
```

---

### Flik 4: Ingrepp (Admin)

**Syfte:** Hantera och konfigurera kirurgiska ingrepp i databasen.

**ENDAST tillgänglig för administratörer.**

#### Funktioner:

**1. Ingreppsöversikt**

```
Filter:
├─ Specialitet: [Alla ▼]
├─ Sök: [__________________]
└─ Sortera: [Base MME ▼]

┌────┬───────────────────┬──────┬─────────┬────┬────┬────┬──────────┐
│ ID │ Namn              │ Spec │ KVÅ-kod │ S  │ V  │ N  │ Base MME │
├────┼───────────────────┼──────┼─────────┼────┼────┼────┼──────────┤
│ 12 │ Total Knäprotes   │ Orto │ NGB09   │ 9  │ 2  │ 5  │ 18.0     │
│ 34 │ Laparoskopi Chole │ Allm │ JKA20   │ 5  │ 8  │ 2  │ 14.0     │
│ 56 │ TUR-P             │ Urol │ KFE10   │ 4  │ 7  │ 3  │ 12.0     │
└────┴───────────────────┴──────┴─────────┴────┴────┴────┴──────────┘

Kolumnförklaring:
S = Somatic pain (1-10)
V = Visceral pain (1-10)
N = Neuropathic pain (1-10)
```

**2. Lägg till Nytt Ingrepp**

```
[+ Lägg till ingrepp]

┌─────────────────────────────────────────────┐
│ SKAPA NYTT INGREPP                          │
├─────────────────────────────────────────────┤
│                                             │
│ Namn: [_____________________________]      │
│                                             │
│ Specialitet: [Ortopedi ▼]                  │
│                                             │
│ KVÅ-kod: [______]  (valfritt)              │
│                                             │
│ Base MME: [___] mg                         │
│   Rekommendation: 10-25mg för de flesta    │
│                                             │
│ 3D SMÄRTPROFIL:                            │
│   Somatic (hudsnitt, skelett): [_]         │
│   Visceral (inre organ): [_]               │
│   Neuropathic (nervskada risk): [_]        │
│                                             │
│ Beskrivning: [___________________]         │
│              [___________________]         │
│                                             │
│ [Avbryt]  [Skapa Ingrepp]                  │
└─────────────────────────────────────────────┘
```

**Exempel - Skapa Total Höftprotes:**

```
Namn: Total Höftprotes
Specialitet: Ortopedi
KVÅ-kod: NGB19
Base MME: 20 mg
  └─ Större ingrepp än TKA, mer vävnadstrauma

3D Smärtprofil:
  Somatic: 9    ← Stort hudsnitt, skelettmanipulation
  Visceral: 2   ← Minimal organpåverkan
  Neuropathic: 6 ← Risk för nervpåverkan (ischiasnerv)

Beskrivning: Elektiv total höftartroplastik, främre eller
bakre approach. Betydande postoperativ smärta, främst
somatisk men med neuropatisk komponent.

[Skapa Ingrepp] ✓

RESULTAT:
✅ Ingrepp skapat med ID: 78
✅ Base MME: 20 mg (initialt)
✅ 3D-profil: (9, 2, 6)
✅ Status: Aktiv
🧠 Systemet kommer lära sig över tid och justera parametrarna!
```

**3. Redigera Ingrepp**

```
Klicka på ett ingrepp → [Redigera]

⚠️ VARNING
Detta ingrepp har 45 loggade fall i databasen.

Ändringar du gör här påverkar ENDAST nya beräkningar.
Historiska fall förblir oförändrade.

Rekommendation: Skapa nytt ingrepp istället om
ändringen är dramatisk (t.ex. ny operationsmetod).

[Fortsätt redigera] [Avbryt]

─────────────────────────────────────────────

REDIGERA: Total Knäprotes

Current values:
├─ Base MME: 18.0 mg (learned from 45 cases)
├─ Somatic: 9
├─ Visceral: 2
└─ Neuropathic: 5 (learned, initial was 3)

Vad vill du ändra?

Base MME: [18.0] mg
  └─ ⚠️ Detta kommer ERSÄTTA inlärd parameter!
      Använd endast om fundamentalt fel upptäckts.

3D-profil:
  Somatic: [9]
  Visceral: [2]
  Neuropathic: [5]
  └─ ℹ️ Dessa kan justeras om ny evidens tillkommit

Specialitet: [Ortopedi ▼]
KVÅ-kod: [NGB09]
Beskrivning: [...]

[Avbryt] [Spara ändringar]
```

**4. Inaktivera Ingrepp**

```
För ingrepp som inte längre ska användas:

[🚫 Inaktivera ingrepp]

Effekt:
├─ Ingreppet försvinner från dropdown i Dosering-fliken
├─ Historiska fall med detta ingrepp förblir synliga
├─ Inlärda parametrar bevaras
└─ Kan aktiveras igen senare

[Bekräfta inaktivering]
```

**5. Visa Ingreppstatistik**

```
Klicka på ingrepp → [Visa statistik]

═══════════════════════════════════════
STATISTIK: Total Knäprotes (TKA)
═══════════════════════════════════════

ANVÄNDNING:
├─ Totalt antal fall: 45
├─ Unikt antal användare: 8
├─ Första fall: 2024-08-15
└─ Senaste fall: 2025-11-06

DOSERING:
├─ Rekommenderad dos (median): 7.5 mg
├─ Rekommenderad dos (range): 5.0-12.5 mg
├─ Genomsnittlig given dos: 7.8 mg
└─ Dos-trend: ↓ -1.2mg över tid

UTFALL:
├─ Perfect outcomes: 68% (31/45)
├─ Acceptable outcomes: 22% (10/45)
├─ Underdosed: 8% (4/45)
├─ Overdosed: 0% (0/45)
└─ Genomsnittlig VAS: 2.1

INLÄRNING:
├─ Base MME: 16.0 → 18.0 mg (+12.5%)
├─ Somatic: 8 → 9 (+12.5%)
├─ Visceral: 2 → 2 (oförändrat)
├─ Neuropathic: 3 → 5 (+66.7%)
└─ Learning rate: 7% (mature phase)

BÄST MATCHADE ADJUVANTER:
(Baserat på 3D pain matching)
1. Infiltration (match: 95%)
2. Ibuprofen (match: 88%)
3. Catapressan (match: 72%)
4. Ketamin (match: 68%)
5. Lidokain (match: 65%)

[Exportera till CSV] [Tillbaka]
```

**6. Bulk-import Ingrepp**

```
För att lägga till många ingrepp samtidigt:

[📥 Importera från CSV]

Format:
┌────────────────────────────────────────────────────────────┐
│ name,specialty,kva_code,base_mme,s,v,n,description         │
│ Total Knäprotes,Ortopedi,NGB09,18,9,2,5,"Elektiv TKA"     │
│ Laparochole,Allmänkirurgi,JKA20,14,5,8,2,"Lap chole"      │
└────────────────────────────────────────────────────────────┘

[Välj fil] [Importera]

Validering:
✅ 2 ingrepp hittade
✅ Alla kolumner OK
⚠️ "Total Knäprotes" finns redan - skippa eller uppdatera?
  [Skippa] [Uppdatera]

[Slutför import]
```

---

## Konfiguration och Anpassning

### config.py - Det Centrala Konfigurationssystemet

All farmakologisk data, säkerhetsgränser och inlärningsparametrar finns i [config.py](config.py).

#### APP_CONFIG Struktur:

```python
APP_CONFIG = {
    'SAFETY_LIMITS': {
        'ABSOLUTE_MIN_DOSE': 0.0,
        'ABSOLUTE_MAX_DOSE': 20.0,
        'MIN_AGE': 0,
        'MAX_AGE': 120,
        'MIN_WEIGHT': 10.0,
        'MAX_WEIGHT': 200.0,
        'MIN_HEIGHT': 100.0,
        'MAX_HEIGHT': 220.0,
        'ADJUVANT_SAFETY_LIMIT_FACTOR': 0.3  # 30% minimum
    },

    'LEARNING': {
        'INITIAL_LEARNING_RATE': 0.30,      # 30% för <10 fall
        'MEDIUM_LEARNING_RATE': 0.18,        # 18% för 10-30 fall
        'MATURE_LEARNING_RATE': 0.12,        # 12% för 30-100 fall
        'EXPERT_LEARNING_RATE': 0.03,        # 3% för 100+ fall
        'DECAY_FACTOR': 200,                 # Exponentiell decay

        'PERFECT_OUTCOME_PROBING': 0.97,     # Anta 97% hade räckt
        'UNDERDOSING_VAS_THRESHOLD': 4,      # VAS >4 = underdoserad
        'OVERDOSING_RESP_THRESHOLD': 8,      # SpO2 <92% eller RR <8

        'PROCEDURE_LEARNING_WEIGHT': 0.10,   # 10% till baseMME
        'ADJUVANT_LEARNING_WEIGHT': 0.02,    # 2% till potency
        'PATIENT_LEARNING_WEIGHT': 0.08,     # 8% till faktorer
        '3D_PAIN_LEARNING_WEIGHT': 0.05,     # 5% till pain profile

        'FENTANYL_KINETICS_ADJ_LARGE': -0.05,  # -5% för tidig smärta
        'FENTANYL_KINETICS_ADJ_SMALL': -0.02,  # -2% för båda
    },

    'PHARMACOKINETICS': {
        'FENTANYL_T_HALF_FAST': 15.0,       # minuter
        'FENTANYL_T_HALF_SLOW': 210.0,      # minuter
        'FENTANYL_FAST_FRACTION': 0.6,      # 60% fast compartment
        'FENTANYL_SLOW_FRACTION': 0.4,      # 40% slow compartment

        'MORPHINE_EQUIVALENCE_FACTOR': 0.25,  # Oxy:Morphine = 1:0.25
    },

    'BODY_COMPOSITION': {
        'REFERENCE_WEIGHT_KG': 70.0,
        'IBW_MALE_FACTOR': 100,             # Längd - 100
        'IBW_FEMALE_FACTOR': 105,           # Längd - 105
        'ABW_ADJUSTMENT': 0.4,              # IBW + 0.4*(TBW-IBW)
    },

    'INTERPOLATION': {
        'AGE_SEARCH_RADIUS': 5,             # ±5 år
        'WEIGHT_SEARCH_RADIUS': 10,         # ±10 kg
        'AGE_SIGMA': 2.0,                   # Gaussian stddev
        'WEIGHT_SIGMA': 3.0,                # Gaussian stddev
        'MIN_OBSERVATIONS_FOR_DIRECT': 3,   # Min obs för direktdata
        'OBSERVATION_WEIGHT_THRESHOLD': 10,  # Full weight vid 10+ obs
        'SANITY_CHECK_MAX_FACTOR': 2.0,     # Max 2x justering
        'SANITY_CHECK_MIN_FACTOR': 0.5,     # Min 0.5x justering
    },

    'UI': {
        'DEFAULT_TARGET_VAS': 1.0,
        'DOSE_ROUNDING_STEP': 2.5,          # Avrunda till 2.5mg-steg
        'MAX_TEMPORAL_DOSES': 10,           # Max antal temporal doser
    }
}
```

#### LÄKEMEDELS_DATA Struktur:

```python
LÄKEMEDELS_DATA = {
    'ibuprofen_800': {
        'name': 'Ibuprofen 800mg',
        'class': 'NSAID',
        'somatic_score': 8,
        'visceral_score': 5,
        'neuropathic_score': 2,
        'potency_percent': 0.15,            # 15% MME-reduktion
        'onset_minutes': 30,
        'peak_minutes': 120,
        'duration_minutes': 360,
        'notes': 'COX-hämmare, antiinflammatorisk'
    },

    'catapressan_75': {
        'name': 'Catapressan 75µg',
        'class': 'Adjuvant',
        'somatic_score': 3,
        'visceral_score': 7,
        'neuropathic_score': 8,
        'potency_percent': 0.12,            # 12% MME-reduktion
        'onset_minutes': 20,
        'peak_minutes': 90,
        'duration_minutes': 480,
        'notes': 'α2-agonist, sympatisk dämpning'
    },

    'ketamine_bolus_small': {
        'name': 'Ketamin liten bolus (10-20mg)',
        'class': 'Adjuvant',
        'somatic_score': 4,
        'visceral_score': 6,
        'neuropathic_score': 9,
        'potency_percent': 0.18,            # 18% MME-reduktion
        'onset_minutes': 2,
        'peak_minutes': 15,
        'duration_minutes': 60,
        'notes': 'NMDA-antagonist, anti-hyperalgesi'
    },

    'lidocaine_infusion_medium': {
        'name': 'Lidokain infusion medium (1mg/kg+1mg/kg/h)',
        'class': 'Adjuvant',
        'somatic_score': 5,
        'visceral_score': 7,
        'neuropathic_score': 7,
        'potency_percent': 0.20,            # 20% MME-reduktion
        'onset_minutes': 10,
        'peak_minutes': 60,
        'duration_minutes': 240,
        'notes': 'Na-kanalblockerare, antiinflammatorisk'
    },

    # ... Total 25+ läkemedel definierade
}
```

#### Använda Konfigurationen:

```python
from config import APP_CONFIG, LÄKEMEDELS_DATA

# Hämta säkerhetsgräns
max_dose = APP_CONFIG['SAFETY_LIMITS']['ABSOLUTE_MAX_DOSE']

# Hämta learning rate
if num_cases < 10:
    lr = APP_CONFIG['LEARNING']['INITIAL_LEARNING_RATE']

# Hämta läkemedelsdata
ibu_data = LÄKEMEDELS_DATA['ibuprofen_800']
ibu_potency = ibu_data['potency_percent']  # 0.15
ibu_3d = {
    'somatic': ibu_data['somatic_score'],
    'visceral': ibu_data['visceral_score'],
    'neuropathic': ibu_data['neuropathic_score']
}
```

---

## Admin-funktioner

### Systemstatus och Övervakning

**Placering:** Admin-flik → Systemstatus

#### Visade Metrics:

```
═══════════════════════════════════════
SYSTEMSTATUS
═══════════════════════════════════════

DATABASE:
├─ Databas: SQLite (anestesi.db)
├─ Storlek: 2.4 MB
├─ Totalt antal fall: 127
│  ├─ FINALIZED: 108 (85%)
│  └─ IN_PROGRESS: 19 (15%)
├─ Antal användare: 12
├─ Antal ingrepp: 34
└─ Senaste backup: 2025-11-05 14:32

INLÄRNING:
├─ Globala parametrar:
│  ├─ Procedures learned: 28/34
│  ├─ Adjuvants learned: 12/12
│  ├─ Age buckets with data: 67/121
│  └─ Weight buckets with data: 89/191
├─ Learning status: ACTIVE
├─ Average learning rate: 9.2%
└─ Last learning: 2 minutes ago

PERFORMANCE:
├─ Average calculation time: 42ms
├─ Average learning time: 18ms
├─ Database query time: 5ms
└─ Uptime: 3 days, 14 hours

BACKUP:
├─ Backup exists: ✓
├─ Backup timestamp: 2025-11-05 14:32:18
├─ Backup size: 1.8 MB
├─ Cases in backup: 108
└─ Auto-restore: ENABLED

ERRORS (Last 24h):
└─ No errors logged ✓
```

### Användarhantering

**Placering:** Admin-flik → Användare

#### Funktioner:

**1. Skapa Ny Användare**

```
[+ Skapa användare]

┌─────────────────────────────────────────┐
│ SKAPA NY ANVÄNDARE                      │
├─────────────────────────────────────────┤
│                                         │
│ Användarnamn: [______________]         │
│   ℹ️ Case-insensitive (Blapa = blapa)  │
│                                         │
│ Administratör: [  ] Checkbox            │
│                                         │
│ Lösenord:                               │
│   ⚠️ Admin: MÅSTE ha lösenord          │
│   ℹ️ Vanlig: Inget lösenord (endast   │
│      användarnamn för inloggning)       │
│                                         │
│   [______________] (endast om admin)    │
│                                         │
│ [Avbryt] [Skapa användare]              │
└─────────────────────────────────────────┘
```

**2. Användarlista**

```
┌────┬─────────────┬────────┬──────────┬──────────────────────┐
│ ID │ Användarnamn│ Admin  │ Antal fall│ Senaste aktivitet   │
├────┼─────────────┼────────┼──────────┼──────────────────────┤
│ 1  │ Blapa       │ ✓      │ 45       │ 2025-11-06 10:23    │
│ 2  │ DrSmith     │        │ 23       │ 2025-11-05 16:47    │
│ 3  │ Nurse01     │        │ 67       │ 2025-11-06 09:15    │
│ 4  │ TestUser    │        │ 0        │ Aldrig              │
└────┴─────────────┴────────┴──────────┴──────────────────────┘

Åtgärder per användare:
├─ [Visa fall] - Lista alla användarens fall
├─ [Statistik] - Visa användarstatistik
├─ [Återställ lösenord] - Endast admin-användare
└─ [Radera] - ⚠️ Raderar INTE fall, endast användarkonto
```

**3. Användarstatistik**

```
Klicka [Statistik] på en användare:

═══════════════════════════════════════
ANVÄNDARSTATISTIK: DrSmith
═══════════════════════════════════════

AKTIVITET:
├─ Registrerad sedan: 2024-09-12
├─ Totalt antal fall: 23
│  ├─ FINALIZED: 18
│  └─ IN_PROGRESS: 5
├─ Första fall: 2024-09-15
└─ Senaste fall: 2025-11-05

DOSERING:
├─ Genomsnittlig rekommenderad dos: 7.2 mg
├─ Genomsnittlig given dos: 7.8 mg
│  └─ Diff: +0.6 mg (+8.3%)
├─ Kalibreringsfaktor: 1.05
└─ Dos-trend: ↓ -0.8mg över tid

UTFALL:
├─ Perfect: 61% (11/18)
├─ Acceptable: 28% (5/18)
├─ Underdosed: 11% (2/18)
├─ Overdosed: 0% (0/18)
├─ Genomsnittlig VAS: 2.6
└─ Genomsnittlig rescue: 0.8 mg

MEST ANVÄNDA INGREPP:
1. Total Knäprotes: 8 fall
2. Laparoscopi Chole: 6 fall
3. Total Höftprotes: 4 fall

MEST ANVÄNDA ADJUVANTER:
1. Ibuprofen: 95% (19/20)
2. Catapressan: 60% (12/20)
3. Infiltration: 45% (9/20)

BIDRAG TILL INLÄRNING:
├─ Procedure updates: 18
├─ Adjuvant updates: 34
├─ Patient factor updates: 45
└─ 3D pain updates: 12
```

### Databashantering (Avancerat)

**Placering:** Admin-flik → Databas

#### Funktioner:

**1. Reset Learning Parameters**

```
⚠️⚠️⚠️ FARLIG OPERATION ⚠️⚠️⚠️

ÅTERSTÄLL INLÄRNINGSPARAMETRAR

Detta kommer att:
├─ Återställa ALLA inlärda parametrar till defaults
├─ Radera alla adjuvant potency learnings
├─ Radera alla 3D pain profile learnings
├─ Radera alla body composition factors
├─ Radera alla age/weight factors
├─ BEVARA alla fall i databasen
└─ Systemet börjar lära från grunden igen

Användningsfall:
- Efter fundamental ändring av algoritm
- Om inlärning gått fel systematiskt
- För forskning/testing

Skriv "RESET LEARNING" för att bekräfta:
[_________________________]

[Avbryt] [Återställ parametrar]
```

**2. Vacuum Database**

```
OPTIMERA DATABAS

SQLite-databaser fragmenteras över tid och kan
bli större än nödvändigt.

Vacuum kommer att:
├─ Komprimera databasen
├─ Återvinna oanvänt utrymme
├─ Optimera index
└─ Förbättra prestanda

Nuvarande storlek: 2.4 MB
Uppskattat efter vacuum: ~1.8 MB
Tidsåtgång: ~5 sekunder

[Vacuum Database]

✅ Vacuum slutförd!
Ny storlek: 1.8 MB (-25%)
```

**3. Export Full Database**

```
EXPORTERA KOMPLETT DATABAS

Skapar en fullständig SQL-dump av hela databasen:
├─ All tabell-struktur
├─ Alla data
├─ Alla index
└─ Kan återställas till ny SQLite-databas

[Exportera SQL-dump]

Filen sparas som: anestesi_full_export_20251106_103022.sql
Storlek: 3.2 MB
[Ladda ner]
```

**4. Analysera Datakvalitet**

```
DATAKVALITETRAPPORT

FALL-KVALITET:
├─ Fall med kompletta data: 98% (125/127)
├─ Fall med saknad postop-tid: 2 fall
├─ Fall med extrema värden: 0 fall
└─ Möjliga dubbletter: 0 fall

INLÄRNINGS-KVALITET:
├─ Buckets med ≥10 observations: 34%
├─ Buckets med 3-9 observations: 28%
├─ Buckets med interpolerad data: 38%
└─ Ingrepp med <5 fall: 6 st

REKOMMENDATIONER:
⚠️ 6 ingrepp har <5 fall - rekommendationer osäkra
ℹ️ Samla mer data för åldrar: 15-20, 95-100
ℹ️ Samla mer data för vikter: 45-50kg, 110-120kg

[Exportera full rapport]
```

### Finjustering och Kalibrering

**Placering:** Admin-flik → Kalibrering

#### Global Calibration Factor:

```
GLOBAL KALIBRERINGSFAKTOR

Denna faktor multipliceras med ALLA dosrekommendationer.

Använd för:
├─ Justera för lokala protokoll
├─ Kompensera för systematisk bias
└─ Anpassa för specifik patientpopulation

Nuvarande värde: 1.00 (standard)

Ny faktor: [____] (0.5 - 2.0)

Exempel:
├─ 0.90 = 10% lägre doser globalt
├─ 1.00 = Standard
└─ 1.10 = 10% högre doser globalt

⚠️ Används SÄLLAN! Låt inlärningssystemet jobba först.

[Uppdatera global faktor]
```

#### Per-Procedure Kalibrering:

```
JUSTERA SPECIFIKT INGREPP

Ingrepp: [Total Knäprotes ▼]

Nuvarande parametrar:
├─ Base MME: 18.0 mg (learned from 45 cases)
├─ Learning count: 45
└─ Last update: 2025-11-06 09:23

Manuell justering:
Base MME: [18.0] → [____]

⚠️ Detta ERSÄTTER inlärd parameter!
   Använd endast vid fundamental felkalibrering.

Alternativt: Justera learning weight:
[ ] Dubbel learning rate för detta ingrepp
    └─ Nästa 10 fall får 2x learning magnitude

[Tillämpa justering]
```

---

## Felsökning och Vanliga Problem

### Problem: Rekommenderad dos verkar för hög/låg

**Möjliga orsaker:**

1. **För få fall loggade för ingreppet**
   ```
   Diagnos: Gå till Utbildning → Ingrepp-statistik
   Lösning: Logga fler fall, systemet lär sig med varje fall
   ```

2. **Adjuvanter inte registrerade korrekt**
   ```
   Diagnos: Kontrollera att alla adjuvanter markerats
   Lösning: Dubbelkolla NSAID, catapressan, infiltration etc
   ```

3. **Fentanyl-timing fel**
   ```
   Diagnos: Fentanyl given nära op-slut → stor kvarvarande MME
   Lösning: Registrera temporal dosering med exakta tider
   ```

4. **Ovanlig patientgrupp**
   ```
   Diagnos: Extrem ålder, vikt eller opioidtolerans
   Lösning: Normalt, systemet justerar efter fler observationer
   ```

### Problem: Inlärning verkar inte funka

**Diagnos:**

```python
# Kontrollera att fall är FINALIZED:
Admin → Historik → Filter: Status=IN_PROGRESS

IN_PROGRESS-fall triggar INGEN inlärning!
```

**Lösning:**
1. Öppna IN_PROGRESS-fallet
2. Registrera utfallsdata (VAS, rescue, etc)
3. Klicka "✅ Spara och Slutför"
4. Kontrollera att learning updates visas

**Vanligt misstag:**
```
❌ Spara som pågående → Ingen learning
✅ Spara och slutför → Learning triggas!
```

### Problem: VAS högt trots "bra" dos

**Tänk på:**

1. **Timing av VAS-mätning**
   - För tidig mätning? Opioider når peak efter 30-60min
   - Rätt tidpunkt: 1-2h postop

2. **Övriga smärtkällor**
   - Urinretention?
   - Lägesrelaterad smärta?
   - Inflammation (inte opioid-responsiv)?

3. **Patientförväntningar**
   - VAS 3-4 kan vara acceptabelt mål
   - VAS 0 är sällan realistiskt direkt postop

4. **Rescue-opioid**
   - Dokumentera rescue-dos → systemet lär sig

**Systemets respons:**
```
Om VAS=7 + rescue=5mg:
actual_requirement = givenDose + rescue + VAS_penalty
                   = 7.5 + 5.0 + 2.0
                   = 14.5 mg

Nästa liknande patient: Rekommendation närmare 14.5mg
```

### Problem: Databas återställs vid omstart (Streamlit Cloud)

**Orsak:** Ephemeral storage - normal för Streamlit Cloud

**Lösning:** Backup-systemet (se Databashantering sektion)

**Snabbfix:**
```bash
1. Admin → Skapa Backup Nu
2. git add database_backup.json
3. git commit -m "Backup database"
4. git push
5. Streamlit auto-redeployar med backup ✓
```

### Problem: Kan inte logga in som admin

**Möjliga orsaker:**

1. **Fel lösenord**
   - Lösenord är case-sensitive: Flubber1 ≠ flubber1
   - Användarnamn är case-insensitive: Blapa = blapa

2. **Secrets inte konfigurerade (Streamlit Cloud)**
   ```toml
   # I Streamlit Cloud Dashboard → Settings → Secrets:
   [admin]
   username = "Blapa"
   password_hash = "$2b$12$..."
   ```

3. **Environment variables saknas (lokalt)**
   ```bash
   # .env fil:
   ADMIN_USERNAME=Blapa
   ADMIN_PASSWORD=Flubber1
   ```

**Återställa admin-lösenord:**
```python
# I Python-console eller temporary script:
import bcrypt
password = "NyttLösenord123"
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
print(hashed.decode())
# Kopiera hash till secrets eller databas
```

### Problem: Temporal dosering fungerar inte

**Vanliga fel:**

1. **Tider i fel ordning**
   ```
   ❌ T=120, T=60, T=0 (bakvänd)
   ✅ T=0, T=60, T=120 (kronologisk)
   ```

2. **Tid efter op-slut**
   ```
   Op-tid: 90 minuter
   ❌ Temporal dos T=120min (efter slut!)
   ✅ Temporal dos T=80min (före slut)
   ```

3. **Fel läkemedel valt**
   ```
   Kontrollera dropdown: Fentanyl, Morfin, Oxycodon?
   Dos i rätt enhet? (µg för fentanyl, mg för övriga)
   ```

**Debug:**
```
Admin → Systemstatus → Logga temporal debugging
└─ Visar alla temporal doses och beräknade kvarvarande
```

### Problem: Interpolation ger konstiga värden

**Diagnos:**
```
Utbildning-flik → Age Trend Analysis
└─ Leta efter stora hopp mellan närliggande åldrar
```

**Möjliga orsaker:**

1. **Outlier i data**
   ```
   Lösning: Identifiera och granska extremfallet
   Admin → Historik → Sortera på Recommended Dose
   ```

2. **För få datapunkter**
   ```
   Interpolation med <3 närliggande punkter → osäker
   Lösning: Samla mer data för ålders/viktområdet
   ```

3. **Sanity check träffar**
   ```
   Interpolerad faktor clampas till 0.5-2.0x default
   Detta är NORMALT och SÄKERT
   ```

**Inaktivera interpolation (emergency):**
```python
# I config.py (ENDAST I NÖDFALL):
APP_CONFIG['INTERPOLATION']['ENABLED'] = False
└─ Återgår till direktdata + defaults
```

---

## Vanliga Frågor (FAQ)

### Allmänt om Systemet

**F: Vad är Anestesi-assistenten?**
> A: Ett beslutsstöd för oxycodon-dosering vid anestesi. Systemet kombinerar farmakologiska regler med adaptiv maskininlärning för att rekommendera patientspecifika startdoser.

**F: Ersätter systemet klinisk bedömning?**
> A: NEJ. Systemet är ett beslutsstöd, inte ett beslutssystem. Den slutgiltiga bedömningen och ansvaret ligger alltid hos ansvarig anestesipersonal.

**F: Hur träffsäker är systemet?**
> A: Träffsäkerheten ökar med antal loggade fall:
> - 0-10 fall: ~60% perfekt utfall
> - 10-30 fall: ~70% perfekt utfall
> - 30-100 fall: ~75% perfekt utfall
> - 100+ fall: ~80% perfekt utfall

**F: Vilka ingrepp stöds?**
> A: Systemet startar med 34 vanliga kirurgiska ingrepp. Admins kan lägga till egna ingrepp med specifika smärtprofiler.

### Om Dosering

**F: Varför föreslår systemet lägre dos än vårt protokoll?**
> A: Systemets mål är att hitta LÄGSTA EFFEKTIVA DOS. Om utfallen är perfekta, fortsätter systemet sänka dosen gradvis (probing). Detta är designat beteende för opioidsparande.

**F: Kan jag ignorera rekommendationen och ge annan dos?**
> A: JA. Registrera bara den faktiska givna dosen i "Given startdos"-fältet. Systemet lär sig från utfallet oavsett vilken dos du gav.

**F: Hur hanterar systemet extrema vikter?**
> A: Genom 4D body composition learning (vikt, IBW-ratio, ABW-ratio, BMI) och viktjustering baserad på ABW istället för total vikt. Detta förhindrar överdosering av överviktiga patienter.

**F: Vad händer om jag glömmer en adjuvant?**
> A: Rekommendationen blir för hög (adjuvanten hade reducerat dosen). När du loggar utfallet lär sig systemet att patienten behövde mindre, men gissar fel orsak. Viktigt att alltid registrera ALLA adjuvanter korrekt.

### Om Inlärning

**F: När sker inlärning?**
> A: ENDAST när ett fall "Sparas och slutförs" (FINALIZED). "Spara som pågående" triggar ingen inlärning.

**F: Kan jag ångra inlärning från ett felaktigt fall?**
> A: Nej, direkt ångra går inte. MEN: Enskilda fall har minimal påverkan (learning rate 3-30%). Radera det felaktiga fallet och logga rätt fall, så korrigerar systemet sig efter några fall.

**F: Varför lär systemet långsammare över tid?**
> A: Adaptiv learning rate. Med få fall: snabb anpassning (30%). Med många fall: långsam justering (3%) för stabilitet. Detta förhindrar att enskilda extremfall förstör väletablerade parametrar.

**F: Lär systemet från alla användares fall?**
> A: JA för procedures, adjuvanter och 3D pain (globalt lärande). NEJ för vissa patientfaktorer (per-user learning). Detta ger snabbare konvergens samtidigt som individuella preferenser respekteras.

**F: Vad är "probing på perfekta utfall"?**
> A: När utfallet är perfekt (VAS ≤2, ingen rescue), antar systemet att 97% av dosen hade räckt. Detta driver gradvis dosreduktion mot lägsta effektiva dos.

### Om Adjuvanter

**F: Varför minskar inte adjuvanter dosen mer?**
> A: Två anledningar:
> 1. 3D pain mismatch - adjuvanten passar inte smärttypen
> 2. Adjuvant safety limit - systemet garanterar minst 30% av bas-dosen bevaras

**F: Vilka adjuvanter är mest effektiva?**
> A: Beror på ingreppets smärtprofil:
> - Somatic (kirurgiskt trauma): NSAID, infiltration
> - Visceral (organsmärta): Lidokain, Catapressan
> - Neuropathic (nervskada): Ketamin, Catapressan

**F: Kan jag lägga till egna adjuvanter?**
> A: Ja (kräver kodändring i config.py):
> 1. Definiera läkemedel i LÄKEMEDELS_DATA
> 2. Ange 3D smärtprofil och potency_percent
> 3. Lägg till i UI (callbacks.py)

### Om Säkerhet

**F: Kan systemet rekommendera farligt höga doser?**
> A: Nej. Absolut max är 20mg oxycodon (hårdkodat). Dessutom: fem oberoende säkerhetslager förhindrar farlig dosering.

**F: Vad händer om inlärning går fel?**
> A: Flera skyddsmekanism:
> - Adaptiv learning rate bromsar över tid
> - Sanity checks vid interpolation
> - Safety limits kan ej läras bort
> - Admin kan reset learning parameters

**F: Är patientdata säker?**
> A: Systemet sparar INGA personuppgifter (namn, personnummer). Endast anonyma kliniska parametrar (ålder, vikt, doser, VAS). Följ lokal GDPR-tolkning.

### Om Tekniska Detaljer

**F: Vad är skillnaden mellan regelbaserad motor och XGBoost?**
> A:
> - **Regelbaserad**: Transparent, lär kontinuerligt, farmakologiskt motiverad
> - **XGBoost**: Black-box, måste tränas om, empiriskt datadriven
> - Båda ger rekommendation, regelbaserad används primärt

**F: Hur fungerar temporal dosering?**
> A: Bi-exponentiell farmakokinetik:
> - 60% fast compartment (t½=15min)
> - 40% slow compartment (t½=210min)
> - Kvarvarande från alla doser summeras vid op-slut

**F: Vad är interpolation?**
> A: När exakt data saknas (t.ex. ingen 73-åring loggad), estimerar systemet från närliggande åldrar med Gaussisk viktning. Se [INTERPOLATION_SYSTEM_README_SV.md](INTERPOLATION_SYSTEM_README_SV.md).

**F: Vilken databas används?**
> A: SQLite (lokal fil). Enkel, snabb, ingen server behövs. Backupsystem för persistens på Streamlit Cloud.

### Om Deployment

**F: Kan jag köra systemet lokalt?**
> A: Ja:
> ```bash
> pip install -r requirements.txt
> streamlit run oxydoseks.py
> ```

**F: Hur deployar jag till Streamlit Cloud?**
> A:
> 1. Pusha kod till GitHub
> 2. Gå till share.streamlit.io
> 3. Välj repository och branch
> 4. Konfigurera secrets (admin credentials)
> 5. Deploy!

**F: Kostar det något?**
> A: Streamlit Community Cloud är gratis för public repos. Privata repos kräver Streamlit Team.

**F: Kan jag använda annan databas än SQLite?**
> A: Ja (kräver kodändring):
> - PostgreSQL för multi-user production
> - MySQL för enterprise deployment
> - Ändra database.py connection string

---

## Utveckling och Bidrag

### Projektstruktur

```
anestesidoseringshjälp/
├── oxydoseks.py              # Huvudfil (Streamlit app)
├── database.py               # Databashantering (SQLite)
├── calculation_engine.py     # Regelbaserad dosberäkning
├── learning_engine.py        # Back-calculation inlärning
├── callbacks.py              # UI callbacks och save/learn triggers
├── auth.py                   # Autentisering och användarhantering
├── config.py                 # Konfiguration och läkemedelsdata
├── pharmacokinetics.py       # PK/PD-modeller (temporal dosering)
├── interpolation_engine.py   # Gaussisk interpolation
├── body_composition_utils.py # 4D body composition bucketing
├── database_backup.py        # Backup/restore-system
├── requirements.txt          # Python-dependencies
├── .streamlit/
│   └── config.toml          # Streamlit-konfiguration
├── .env.example             # Exempel på miljövariabler
├── README.md                # Denna fil
├── SPECIFICATION.md         # Teknisk specifikation och TODO
└── anestesi.db              # SQLite-databas (skapas automatiskt)
```

### Installation och Deployment

**Se [SPECIFICATION.md - Deployment Section](SPECIFICATION.md#deployment) för detaljerade installationsinstruktioner.**

**Snabbstart Lokalt:**

```bash
# Klona och installera
git clone https://github.com/Puttkne/anestesidoseringshjalp.git
cd anestesidoseringshjalp
pip install -r requirements.txt

# Konfigurera admin (skapa .env)
echo "ADMIN_USERNAME=Blapa" > .env
echo "ADMIN_PASSWORD=Flubber1" >> .env

# Starta
streamlit run oxydoseks.py
```

**Deployment till Streamlit Cloud:**

Se detaljerad guide i Databashantering & Backup-sektionen ovan.

---

## Sammanfattning

Detta README-dokument innehåller all information som behövs för att:

✅ **Förstå systemet** - Vad det gör och hur det fungerar
✅ **Använda systemet** - Komplett användarguide för alla flikar
✅ **Administrera systemet** - Admin-funktioner och användarhantering
✅ **Felsöka problem** - Vanliga problem och lösningar
✅ **Konfigurera systemet** - Alla parametrar och säkerhetsgränser
✅ **Förstå säkerheten** - Fem lager av skyddsfunktioner
✅ **Lära sig tekniken** - Interpolation, 3D pain matching, back-calculation
✅ **Bidra till utveckling** - Kod, buggar, förbättringar

För djupare teknisk dokumentation och byggritning, se **[SPECIFICATION.md](SPECIFICATION.md)**.

---

**Dokumentversion:** 1.0
**Senast uppdaterad:** 2025-11-06
**Författare:** Patrick (Puttkne) med hjälp av Claude (Anthropic)
**Dokumentstatus:** Komplett sanningsdokument ✓

---

*Tack för att du använder Anestesi-assistenten! Tillsammans kan vi förbättra postoperativ smärtlindring och minska opioidanvändning.* 🎯