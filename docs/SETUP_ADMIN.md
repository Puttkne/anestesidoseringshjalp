# Snabb Setup - Admin-konto

## 🚀 Kom igång på 2 minuter

### Steg 1: Skapa .env fil
```bash
# Kopiera mallen
cp .env.example .env

# Eller skapa manuellt
notepad .env  # Windows
nano .env     # Linux/Mac
```

### Steg 2: Sätt dina credentials i .env
```bash
ADMIN_USERNAME=ditt_admin_namn
ADMIN_PASSWORD=ditt_säkra_lösenord_K7$mN9@pL2!qR4
```

### Steg 3: Installera python-dotenv (om inte redan installerat)
```bash
pip install python-dotenv
```

### Steg 4: Starta appen
```bash
streamlit run oxydoseks.py
```

### Steg 5: Logga in som admin
- Användarnamn: `ditt_admin_namn`
- Lösenord: `ditt_säkra_lösenord_K7$mN9@pL2!qR4`

---

## ⚠️ VIKTIGT

### ✅ GÖR:
- [x] Använd STARKT lösenord (12+ tecken, special chars)
- [x] Förvara .env SÄKERT (lägg i .gitignore)
- [x] Ändra lösenord regelbundet

### ❌ GRÄNG ALDRIG:
- [ ] Checka in .env till Git
- [ ] Dela lösenord i klartext (email, chat)
- [ ] Använd default-lösenord "changeme123"

---

## 🔧 Felsökning

### Problem: "Using default admin password" varning
**Lösning:** Du har inte satt ADMIN_PASSWORD i .env

### Problem: Kan inte logga in
**Lösning:**
1. Kontrollera att .env fil finns
2. Kontrollera stavning i användarnamn/lösenord
3. Radera databas: `rm anestesi.db` och starta om

### Problem: .env fil läses inte in
**Lösning:** Installera python-dotenv: `pip install python-dotenv`

---

## 📝 Exempel .env

```bash
# Admin Credentials
ADMIN_USERNAME=admin123
ADMIN_PASSWORD=MyS3cur3P@ssw0rd!2025

# Tips: Använd lösenordsgenerator för stark säkerhet!
```

---

**Det är allt! Nu är admin-kontot säkert konfigurerat.** 🎉
