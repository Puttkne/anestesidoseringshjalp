# KVÅ-kodimplementering

## Översikt
KVÅ-koder (Klassifikation av Vårdåtgärder) har lagts till för alla 84 standardiserade ingrepp i systemet. Detta ger:
- **Standardiserad kodning** för dataexport till anestesiprogram
- **Unik identifiering** som del av ingreppets fingeravtryck
- **Kompatibilitet** med svenska vårdregister

## Implementation

### 1. Procedurdefinitioner (pain_classification.py)
Alla 84 ingrepp har nu `kva_code`:

```python
{'id': 'kir_appendektomi_lap',
 'specialty': 'Kirurgi',
 'name': 'Appendektomi, laparoskopisk',
 'kva_code': 'JEA01',  # <-- NYTT
 'baseMME': 17,
 'painTypeScore': 2}
```

### 2. Databasschema

#### cases-tabell
```sql
CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    procedure_id TEXT NOT NULL,
    kva_code TEXT,  -- <-- NYTT
    specialty TEXT,
    ...
)
```

#### custom_procedures-tabell
```sql
CREATE TABLE IF NOT EXISTS custom_procedures (
    id TEXT PRIMARY KEY,
    specialty TEXT NOT NULL,
    name TEXT NOT NULL,
    kva_code TEXT,  -- <-- NYTT (för framtida manuella ingrepp)
    base_mme INTEGER NOT NULL,
    ...
)
```

### 3. Dataflöde

#### Vid val av ingrepp:
```python
# oxydos_v8.py:480 - get_current_inputs()
proc_row = procedures_df[
    (procedures_df['name'] == procedure_name) &
    (procedures_df['specialty'] == specialty)
]
if not proc_row.empty:
    procedure_id = proc_row.iloc[0]['id']
    kva_code = proc_row.iloc[0].get('kva_code', None)  # <-- Hämtas här
```

#### Vid sparande av fall:
```python
# database.py:223 - save_case()
INSERT INTO cases (
    user_id, procedure_id, kva_code, specialty, ...  # <-- Sparas här
) VALUES (?, ?, ?, ?, ...)
```

## KVÅ-koder per Specialitet

### Gynekologi (16 ingrepp)
- **LCD00** - Hysterektomi, abdominell (öppen)
- **LCD01** - Hysterektomi, laparoskopisk (TLH)
- **LCD04** - Hysterektomi, vaginal
- **LCD96** - Endometrioskirurgi, extensiv (lap)
- **LCC10** - Myomektomi (öppen)
- **LAF01** - Ovariell cystektomi (lap)
- **LAD00** - Salpingektomi (vid X)
- **JAD00** - Laparoskopi, diagnostisk
- **MAB00** - Kejsarsnitt (med spinal/EDA)
- **LCA10** - Dilatation & Skrapning (D&C)
- **LCB00** - Konisering
- **LCD99** - Hysteroskopi, operativ
- **KCF10** - Inkontinensslinga (TVT/TOT)
- **MAE20** - Perinealruptur grad 3-4, sutur
- **LFA20** - Vulvektomi
- **PJH00** - Bäckenutrymning (exenteration)

### Kirurgi (25 ingrepp)
- **JEA01** - Appendektomi, laparoskopisk
- **JKA21** - Kolecystektomi, laparoskopisk
- **JKA20** - Kolecystektomi, öppen
- **JFH01** - Hemikolektomi, laparoskopisk
- **JFH00** - Hemikolektomi, öppen
- **JFH10** - Sigmoideumresektion (öppen)
- **JFH31** - Låg främre resektion (rektum)
- **JFH40** - Abdominoperineal resektion (APR)
- **JAH10** - Ljumskbråck, öppen (Lichtenstein)
- **JAH11** - Ljumskbråck, laparoskopisk (TEP/TAPP)
- **JAH20** - Ventralbråck, öppen
- **JDF20** - Obesitaskirurgi (Bypass/Sleeve)
- **JAW96** - Explorativ laparotomi
- **JLC33** - Whipples operation
- **JJC20** - Leverresektion
- **JDC20** - Gastrektomi (partiell/total)
- **JBW96** - Esofagusresektion
- **HAC20** - Mastektomi
- **HAC10** - Partiell mastektomi
- **BAB00** - Thyroidektomi / Hemithyroidektomi
- **BAA00** - Parathyroidektomi
- **JNA01** - Splenektomi, laparoskopisk
- **JJH10** - Hemorrojdektomi
- **JJH20** - Fistula-in-ano

### Ortopedi (19 ingrepp)
- **NFB30** - Höftprotes, total
- **NGB30** - Knäprotes, total
- **NFJ62** - Höftfrakturkirurgi (spik/protes)
- **NHJ42** - Femurfraktur, märgspik
- **NHJ52** - Tibiafraktur, märgspik
- **NHJ92** - Fotledsfraktur (ORIF)
- **NCJ72** - Handledsfraktur, platta (ORIF)
- **NAJ42** - Axelfraktur / Skulderprotes
- **NAG59** - Ryggkirurgi, fusion (1-2 nivåer)
- **ABC46** - Ryggdekompression (Laminektomi)
- **NGD21** - ACL-rekonstruktion
- **NAL66** - Rotatorkuff-sutur
- **NAW01** - Skulderartroskopi (dekompression)
- **NGE51** - Meniskresektion, artroskopisk
- **ACC55** - Karpaltunnelklyvning
- **NHM99** - Hallux valgus-kirurgi
- **NHQ10** - Amputation, underben
- **NCF10** - Excision av ganglion, handled

### Urologi (11 ingrepp)
- **KEC21** - Prostatektomi, laparoskopisk/robot
- **KAC11** - Nefrektomi, laparoskopisk
- **KAC10** - Nefrektomi, öppen
- **KCC40** - Cystektomi med blåssubstitut
- **KED30** - TUR-P (hyvling av prostata)
- **KCE10** - TUR-B (blåstumör)
- **KBA10** - Ureteroskopi (stenextraktion)
- **KAD20** - PCNL (perkutan njurstenskirurgi)
- **KAG00** - ESWL (stötvågsbehandling njursten)
- **KGA20** - Hydrocelektomi
- **KFF00** - Vasektomi

### ÖNH (9 ingrepp)
- **EMB20** - Tonsillektomi
- **DAC20** - Näs- & bihålekirurgi (FESS)
- **DAD20** - Septoplastik
- **DRD00** - Parotidektomi
- **AAF10** - Halskörtelutrymning
- **DQW01** - Mikrolaryngoskopi (MLS)
- **DCA20** - Mastoidektomi
- **DQA96** - Sömnapnékirurgi (UPPP)
- **DCC00** - Tympanoplastik

### Tand (6 ingrepp)
- **GAH10** - Visdomstandsextraktion, komplicerad
- **DHW96** - Ortognatisk kirurgi (käkförflyttning)
- **DHJ99** - Mandibelfraktur (ORIF)
- **GAH20** - Multipla extraktioner
- **DHE96** - Benaugmentation (käke)
- **DGW01** - TMJ-artroskopi (käkled)

## Användning

### För användaren:
- **Synligt:** Klartext-namn (t.ex. "Appendektomi, laparoskopisk")
- **Osynligt:** KVÅ-kod sparas automatiskt i databasen (JEA01)

### För dataexport:
```sql
SELECT
    kva_code,
    procedure_id,
    specialty,
    given_dose,
    vas,
    uva_dose
FROM cases
WHERE user_id = ?
ORDER BY timestamp DESC
```

### För anestesiprogram:
KVÅ-koden kan användas för:
- Automatisk journalföring
- Koppling till operationsregister
- Kvalitetsregisterrapportering
- Forskningsdatauttag

## Framtida Förbättringar

### 1. Validering
- Kontrollera KVÅ-koder mot officiellt register
- Uppdatera vid ändringar i KVÅ-systemet
- Varna vid ogiltiga koder

### 2. Manuella ingrepp
- UI för att lägga till KVÅ-kod när användare skapar eget ingrepp
- Fritextsök i KVÅ-register
- Autocomplete för KVÅ-kodval

### 3. Integration
- Export till DIPS/Cosmic/Orbit
- Import från operationsplaneringsystem
- API för direktintegration

### 4. Analytics
- Aggregerad statistik per KVÅ-kod
- Nationell jämförelse (om anonymiserad data delas)
- Benchmarking mot riktlinjer

## Migration för Befintliga Databaser

Om du har en befintlig databas, kör:

```python
import sqlite3

conn = sqlite3.connect('anestesi.db')
cursor = conn.cursor()

# Lägg till kolumn i cases-tabell
cursor.execute('ALTER TABLE cases ADD COLUMN kva_code TEXT')

# Lägg till kolumn i custom_procedures-tabell
cursor.execute('ALTER TABLE custom_procedures ADD COLUMN kva_code TEXT')

conn.commit()
conn.close()
```

**OBS:** Detta lägger till kolumnen men fyller inte i historiska fall. Framtida fall kommer automatiskt få KVÅ-kod.

## Kodkälla
KVÅ-koderna är baserade på:
- Socialstyrelsens klassifikation av vårdåtgärder (KVÅ)
- Version: 2024
- Källa: https://www.socialstyrelsen.se/utveckla-verksamhet/e-halsa/klassificering-och-koder/kva/

**Viktigt:** Koderna bör verifieras mot din regions specifika implementation och uppdateras vid KVÅ-revisioner.
