# Anestesi-assistent Alfa V0.8 - Uppgraderingsguide

## 🆕 Nyheter i Alfa V0.8

### 1. **Säker Autentisering**
- Användare loggar in med sitt användar-ID (första gången skapas kontot automatiskt)
- Admin-konto "blapa" kräver ett lösenord som sätts via miljövariabler.
- Lösenord hashas säkert med bcrypt

### 2. **SQLite Databas**
- Ersätter JSON-filen med en robust SQLite-databas
- Bättre prestanda och skalbarhet
- Stöd för komplexa relationer mellan data

### 3. **Rättighetshantering**
- Vanliga användare kan bara redigera/radera sina egna fall
- Admin "blapa" kan redigera/radera alla fall
- Tydlig visuell indikation (🔒) när åtgärder inte är tillåtna

### 4. **Förbättrad Säkerhet**
- HTTPS-redo (kräver SSL-certifikat vid deployment)
- Session management
- Lösenordsskydd för admin

## 📋 Installation och Uppgradering

### Steg 1: Installera nya beroenden

```bash
pip install -r requirements.txt
```

### Steg 2: Migrera befintlig data (om du har gammal JSON-databas)

```bash
python migrate_to_sqlite.py
```

Detta script kommer:
- Skapa en ny SQLite-databas (`anestesi.db`)
- Migrera alla dina befintliga fall
- Migrera kalibreringsfaktorer
- Migrera custom procedures
- Backa upp din gamla `database.json` fil

### Steg 3: Kör nya applikationen

```bash
streamlit run oxydoseks.py
```

## 🔐 Inloggning

### För vanliga användare:
1. Ange ditt användar-ID (t.ex. "DN123")
2. Klicka "Logga in"
3. Första gången skapas ditt konto automatiskt

### För admin (blapa):
1. Ange användarnamn: `blapa`
2. Ange ditt lösenord
3. Klicka "Logga in"

## 🚀 Deployment till Streamlit Community Cloud

### Förberedelser:

1. **Skapa ett GitHub repository** med följande filer:
   - `oxydoseks.py` (huvudapplikationen)
   - `database.py` (databashantering)
   - `auth.py` (autentisering)
   - `requirements.txt` (beroenden)
   - `.gitignore` (se nedan)

2. **Skapa `.gitignore` fil:**
   ```
   database.json
   database_backup_*.json
   anestesi.db
   *.db
   __pycache__/
   *.pyc
   .env
   backups/
   .venv/
   ```

3. **Pusha till GitHub:**
   ```bash
   git init
   git add oxydoseks.py database.py auth.py requirements.txt .gitignore
   git commit -m "Initial commit of Alfa V0.8"
   git branch -M main
   git remote add origin https://github.com/dittanvändarnamn/anestesi-app.git
   git push -u origin main
   ```

4. **Deploya på Streamlit Community Cloud:**
   - Gå till [share.streamlit.io](https://share.streamlit.io)
   - Logga in med GitHub
   - Välj ditt repository
   - Välj `oxydoseks.py` som main file
   - Klicka "Deploy"

### Viktigt vid deployment:
- SQLite-databasen skapas automatiskt vid första körningen
- Admin-kontot "blapa" skapas automatiskt
- Databasen återställs vid varje omstart på Streamlit Cloud (data går förlorad)
- För persistent data, använd Streamlit Cloud Secrets + extern databas (t.ex. Supabase)

## 🔒 Säkerhet

### Lösenordshantering:
- Admin-lösenord: Lösenordet för admin-kontot sätts via miljövariabler för att undvika att ha det hårdkodat i koden.
- Lösenord hashas med bcrypt innan lagring
- Vanliga användare behöver inget lösenord (identifieras bara med användar-ID)

### Rättigheter:
- **Vanlig användare:** Kan bara se, redigera och radera sina egna fall
- **Admin (blapa):** Kan se, redigera och radera alla fall

### För produktionsmiljö:
1. Sätt `ADMIN_USERNAME` och `ADMIN_PASSWORD` som miljövariabler.
2. Överväg att lägga till HTTPS (SSL-certifikat)

## 📊 Databas-struktur

SQLite-databasen innehåller följande tabeller:
- `users` - Användarkonton
- `cases` - Patientfall
- `edit_history` - Redigeringshistorik
- `user_settings` - Kalibreringsfaktorer per användare
- `custom_procedures` - Användardefinierade procedurer

## 🐛 Felsökning

### Problem: "bcrypt not found"
**Lösning:**
```bash
pip install bcrypt
```

### Problem: "streamlit-authenticator not found"
**Lösning:**
```bash
pip install streamlit-authenticator
```

### Problem: Databasen är tom efter migrering
**Lösning:**
- Kontrollera att `database.json` fanns i samma mapp
- Kör `python migrate_to_sqlite.py` igen
- Kolla backup-filen för att säkerställa att data finns

### Problem: Kan inte logga in som admin
**Lösning:**
- Användarnamn: `blapa` (små bokstäver)
- Lösenord: Se till att du använder rätt lösenord som är satt via miljövariabler.

## 📝 Changelog

### Alfa V0.8 (2025-10-03)
- ✅ Autentisering med bcrypt-hashade lösenord
- ✅ SQLite-databas istället för JSON
- ✅ Rättighetshantering (användare kan bara redigera sina egna fall)
- ✅ Admin-konto "blapa" med fullständiga rättigheter
- ✅ Migreringsskript för befintlig data
- ✅ Förbättrad säkerhet och skalbarhet
- ✅ Redo för deployment på Streamlit Community Cloud

## 📧 Support

Vid frågor eller problem, kontakta utvecklaren.
