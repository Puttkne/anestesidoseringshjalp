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