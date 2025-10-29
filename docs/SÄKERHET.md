# Säkerhetsguide - Admin-konto och Credentials

## ⚠️ SÄKERHETSFIXAR GENOMFÖRDA (2025-10-04)

### Problem: Hårdkodade Admin-credentials
**Tidigare:** Admin-användarnamn "blapa" och lösenord "Flubber1" var hårdkodat i `auth.py`

**Risk:**
- Alla som läser koden kan logga in som admin
- Omöjligt att ändra utan att ändra kod
- Säkerhetsrisk vid GitHub/delning

### Lösning: Miljövariabler + .env fil ✅

---

## Hur Admin-konto Fungerar Nu

### 1. Miljövariabler (Rekommenderat)
Admin-credentials hämtas från miljövariabler:

**Windows (PowerShell):**
```powershell
$env:ADMIN_USERNAME = "ditt_admin_namn"
$env:ADMIN_PASSWORD = "ditt_säkra_lösenord"
```

**Windows (CMD):**
```cmd
set ADMIN_USERNAME=ditt_admin_namn
set ADMIN_PASSWORD=ditt_säkra_lösenord
```

**Linux/Mac:**
```bash
export ADMIN_USERNAME="ditt_admin_namn"
export ADMIN_PASSWORD="ditt_säkra_lösenord"
```

### 2. .env Fil (Enklast för lokal utveckling)

**Steg 1: Kopiera .env.example**
```bash
cp .env.example .env
```

**Steg 2: Redigera .env**
```bash
# .env (denna fil syns ALDRIG i Git!)
ADMIN_USERNAME=din_admin
ADMIN_PASSWORD=K7$mN9@pL2!qR4
```

**Steg 3: Installera python-dotenv (om ej redan installerat)**
```bash
pip install python-dotenv
```

### 3. Default-värden (OSÄKERT - endast för test)
Om inga miljövariabler eller .env finns:
- Username: `admin`
- Password: `changeme123`

**⚠️ VARNING:** Du får en varning i konsolen om du använder default-värden!

---

## Säker Lösenordshantering

### Starkt Lösenord - Krav:
✓ Minst 12 tecken
✓ Stora och små bokstäver
✓ Siffror
✓ Specialtecken (!@#$%^&*)
✓ INTE ord från ordbok

### Exempel på Starka Lösenord:
```
Bra: K7$mN9@pL2!qR4
Bra: P@ssw0rd!2025#Secure
Bra: My$ecur3P@ss2025

Dåligt: password123
Dåligt: Flubber1
Dåligt: admin2025
```

### Generera Starkt Lösenord (Python):
```python
import secrets
import string

alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
password = ''.join(secrets.choice(alphabet) for i in range(16))
print(password)
```

---

## .gitignore - Vad som ALDRIG får checkas in

Följande filer är nu blockerade från Git:

### 🔒 Känsliga filer:
- `.env` - Admin-credentials
- `*.db` - Databaser med patientdata
- `.streamlit/secrets.toml` - Streamlit secrets

### 📁 Andra exkluderade:
- `__pycache__/` - Python cache
- `.venv/` - Virtual environment
- `.vscode/` - IDE-inställningar

**Kolla alltid .gitignore innan du committar!**

---

## Hur Man Ändrar Admin-lösenord

### Metod 1: Via Miljövariabler
1. Ändra miljövariabeln `ADMIN_PASSWORD`
2. Radera databasen: `rm anestesi.db`
3. Starta om appen (ny admin skapas automatiskt)

### Metod 2: Via .env Fil
1. Redigera `.env` filen
2. Radera databasen: `rm anestesi.db`
3. Starta om appen

### Metod 3: Manuellt i Databas (Avancerat)
```python
import bcrypt
import sqlite3

# Skapa nytt hash
new_password = "ditt_nya_lösenord"
salt = bcrypt.gensalt()
new_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8')

# Uppdatera i databas
conn = sqlite3.connect('anestesi.db')
cursor = conn.cursor()
cursor.execute("UPDATE users SET password_hash = ? WHERE is_admin = 1", (new_hash,))
conn.commit()
conn.close()
```

---

## Säkerhetschecklista - Före Produktion

### ✅ Obligatoriskt:
- [ ] Skapa `.env` fil med STARKA lösenord
- [ ] Verifiera att `.env` finns i `.gitignore`
- [ ] Testa att admin-login fungerar med nya credentials
- [ ] Radera gamla databaser med "blapa"-admin
- [ ] Ändra default-lösenord från "changeme123"

### ✅ Rekommenderat:
- [ ] Använd lösenordshanterare (1Password, LastPass, Bitwarden)
- [ ] Dokumentera admin-credentials SÄKERT (ej i Git!)
- [ ] Rotera admin-lösenord var 3:e månad
- [ ] Aktivera 2FA om möjligt (framtida feature)

### ✅ För Produktion:
- [ ] Använd Streamlit Secrets istället för .env
- [ ] Begränsa admin-åtkomst till specifika IP:er
- [ ] Logga alla admin-actions
- [ ] Regelbunden säkerhetsgranskning

---

## Streamlit Secrets (Produktion)

För deployment på Streamlit Cloud:

### 1. Skapa secrets.toml
```toml
# .streamlit/secrets.toml
ADMIN_USERNAME = "din_admin"
ADMIN_PASSWORD = "ditt_säkra_lösenord"
```

### 2. Uppdatera auth.py (redan implementerat)
```python
# Försök Streamlit secrets först
try:
    admin_username = st.secrets.get("ADMIN_USERNAME", os.getenv('ADMIN_USERNAME', 'admin'))
    admin_password = st.secrets.get("ADMIN_PASSWORD", os.getenv('ADMIN_PASSWORD', 'changeme123'))
except:
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('ADMIN_PASSWORD', 'changeme123')
```

### 3. Lägg till secrets på Streamlit Cloud
- Gå till App Settings → Secrets
- Klistra in secrets.toml-innehåll
- Spara och restart app

---

## Vanliga Frågor (FAQ)

### F: Vad händer om jag glömmer admin-lösenordet?
**S:**
1. Stoppa appen
2. Radera databasen (`rm anestesi.db`)
3. Ändra `ADMIN_PASSWORD` i `.env`
4. Starta appen (ny admin skapas)

### F: Kan jag ha flera admin-konton?
**S:** Ja, men kräver manuell skapning:
```python
from auth import hash_password
from database import create_user

hashed = hash_password("ditt_lösenord")
create_user("admin2", hashed, is_admin=True)
```

### F: Hur ser jag vilket admin-konto som är aktivt?
**S:** Kolla databasen:
```sql
SELECT username, is_admin FROM users WHERE is_admin = 1;
```

### F: Varför finns det default-värden om de är osäkra?
**S:** För att appen ska kunna köras första gången utan konfiguration (utveckling). Du får en varning om du använder dem!

---

## Incidenthantering

### Om Admin-credentials Läcker:

**Omedelbart:**
1. ⚠️ Ändra lösenord omedelbart (se ovan)
2. 🔍 Granska loggar för obehörig åtkomst
3. 🚫 Radera eventuella komprometterade användare
4. 📧 Informera berörda om incidenten

**Förebyggande:**
1. Rotera lösenord regelbundet
2. Använd olika lösenord för test/prod
3. Begränsa vem som har tillgång till .env
4. Kryptera .env i molnlagring

---

## Sammanfattning

### ✅ Vad som är fixat:
1. Hårdkodade credentials borttagna
2. Miljövariabler implementerade
3. .env support med python-dotenv
4. .gitignore skapad (blockerar .env)
5. .env.example som mall
6. Lösenordsinstruktioner dokumenterade

### 🔒 Säkerhetsnivå nu:
- **Före:** ⭐☆☆☆☆ (Mycket osäkert - hårdkodat)
- **Efter:** ⭐⭐⭐⭐☆ (Säkert - konfigurerbara credentials)

### 🚀 Nästa Steg:
1. Skapa `.env` fil med starka lösenord
2. Testa admin-login
3. Radera gamla databaser
4. Vid produktion: Använd Streamlit Secrets

---

## Kontaktinformation

**Vid säkerhetsincident:**
- Teknisk support: [kontakt]
- Säkerhetsansvarig: [kontakt]

**Rapportera säkerhetsproblem:**
- Email: security@[domain]
- GitHub: Privat issue (ej public!)

---

*Säkerhetsguide uppdaterad: 2025-10-04*
*Version: 2.0 (Miljövariabler)*
