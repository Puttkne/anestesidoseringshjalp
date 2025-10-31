# Comprehensive Test Checklist for Anestesi-assistent Alfa V0.8

Use this checklist for manual testing or to verify automated test coverage.

---

## 🔐 Authentication & Login

- [ ] **Login page displays** on first visit
- [ ] **New user creation** works (enter username without password)
- [ ] **Admin login** works with password (Blapa/Flubber1)
- [ ] **Admin badge** displays after admin login
- [ ] **Logout button** appears when logged in
- [ ] **Logout** returns to login page
- [ ] **Username** displays in header after login

---

## 💊 Dosing & Recommendation Tab

### Patient Data Section

- [ ] **Age input** accepts numeric values (0-120)
- [ ] **Gender dropdown** (Man/Kvinna) works
- [ ] **Weight input** accepts numeric values (0-300 kg)
- [ ] **Height input** accepts numeric values (0-250 cm)
- [ ] **ASA dropdown** (ASA 1-5) works
- [ ] **Opioid history dropdown** (Naiv/Tolerant) works
- [ ] **Low pain threshold checkbox** works
- [ ] **GFR <35 checkbox** works
- [ ] **Opioid tolerance info** appears when "Tolerant" selected

### Procedure Selection

- [ ] **Specialty dropdown** displays all specialties
- [ ] **Procedure dropdown** filters by selected specialty
- [ ] **Procedure list** updates when specialty changes
- [ ] **Surgery type dropdown** (Elektivt/Akut) works

### Temporal Opioid Doses

- [ ] **Drug selection dropdown** (Fentanyl/Oxycodone/Morfin) works
- [ ] **Dose input** accepts values with correct units (µg for Fentanyl, mg for others)
- [ ] **Hours input** accepts values (0-12)
- [ ] **Minutes input** accepts values (0-55)
- [ ] **Postop checkbox** toggles pre/postop timing
- [ ] **"Lägg till opioid" button** adds dose to list
- [ ] **Added doses display** with correct formatting and colors
- [ ] **Time display** shows relative to opslut (surgery end)
- [ ] **Delete button (🗑️)** removes individual doses
- [ ] **Multiple doses** can be added
- [ ] **Doses sort** by time automatically

### Adjuvant Medications

- [ ] **NSAID dropdown** (Ingen/Ibuprofen/Ketorolac/Parecoxib) works
- [ ] **Paracetamol 1g checkbox** works
- [ ] **Catapressan dose input** accepts values (0-150 µg)
- [ ] **Betapred dropdown** (Nej/4mg/8mg) works
- [ ] **Ketamine dose input** accepts values (0-200 mg)
- [ ] **Ketamine infusion checkbox** works
- [ ] **Lidocaine dose input** accepts values (0-200 mg)
- [ ] **Lidocaine infusion checkbox** works
- [ ] **Droperidol checkbox** works
- [ ] **Infiltration checkbox** works
- [ ] **Sevoflurane checkbox** works

### Dose Calculation

- [ ] **"Beräkna Rekommendation" button** calculates dose
- [ ] **Dose recommendation** displays with value
- [ ] **Engine type** displays (Regel/Ensemble/XGBoost)
- [ ] **BMI calculation** displays when weight/height entered
- [ ] **IBW/ABW** displays for overweight patients
- [ ] **Pain type indicator** displays (🔴🔵🟣)
- [ ] **Confidence warning** displays when data is limited
- [ ] **BMI warnings** display for extreme values
- [ ] **Age warnings** display for elderly patients with high doses
- [ ] **Feature importance** expander works (when ML active)
- [ ] **Validation warnings** display for unsafe doses

### Outcome Logging

- [ ] **Administered dose input** pre-fills with recommendation
- [ ] **"Spara Fall (initial)" button** saves case
- [ ] **VAS slider** (0-10) works
- [ ] **UVA dose input** accepts values
- [ ] **Rescue timing checkboxes** work (<30 min / >30 min)
- [ ] **Postop hours input** works (0-48)
- [ ] **Postop minutes input** works (0-55, steps of 5)
- [ ] **Postop reason dropdown** works
- [ ] **Respiratory status radio** works (u.a./Hypopné/Naloxon)
- [ ] **Severe fatigue checkbox** works
- [ ] **"Uppdatera Fall (komplett)" button** updates case

---

## 📊 History & Statistics Tab

### Display & Export

- [ ] **History tab** switches correctly
- [ ] **Case list** displays saved cases
- [ ] **Excel export button** appears when cases exist
- [ ] **Excel download** works
- [ ] **Case count** displays correctly

### Filters

- [ ] **User ID search** filters by username
- [ ] **Procedure filter** filters by procedure name
- [ ] **Min VAS filter** filters by VAS value
- [ ] **Show incomplete checkbox** filters incomplete cases
- [ ] **Max results selector** limits displayed cases
- [ ] **Filter combination** works correctly

### Case Actions

- [ ] **Edit button (📝)** loads case for editing
- [ ] **Delete button (🗑️)** shows confirmation dialog
- [ ] **Delete confirmation** works
- [ ] **Delete cancel** works
- [ ] **Edit permissions** enforced (own cases only unless admin)
- [ ] **Delete permissions** enforced (own cases only unless admin)
- [ ] **Lock icons (🔒)** show for restricted cases

### Case Details

- [ ] **Timestamp** displays correctly
- [ ] **Procedure name** displays correctly
- [ ] **VAS value** displays correctly
- [ ] **Dose value** displays correctly
- [ ] **Created by** displays username
- [ ] **Last modified** info displays when edited
- [ ] **Edit history** expander works
- [ ] **Edit history details** show changes
- [ ] **Temporal doses** expander works
- [ ] **Temporal dose timeline** displays correctly (when multiple doses)

---

## 🧠 Learning & Models Tab

### Model Status Subtab

- [ ] **Model status tab** loads
- [ ] **ML threshold** displays correctly
- [ ] **Procedure list** with case counts displays
- [ ] **Model status** (✅ Aktiv / ⏳ Inaktiv) displays correctly
- [ ] **Dataframe** is sortable and filterable

### Rule Engine Learning Subtab

- [ ] **Regelmotor tab** loads
- [ ] **Adjuvant effectiveness table** displays
- [ ] **All adjuvants** listed with correct values
- [ ] **Pain type columns** (🔴🔵🟢) display correctly
- [ ] **Dose reduction percentages** display correctly
- [ ] **Calibration factors** display when data exists
- [ ] **Calibration factors table** shows fingerprints and multipliers
- [ ] **Factor count** displays correctly

### Statistics Subtab

- [ ] **Statistics tab** loads
- [ ] **Total cases metric** displays correctly
- [ ] **Average VAS metric** displays correctly
- [ ] **VAS >4 percentage** displays correctly
- [ ] **Average dose metric** displays correctly
- [ ] **Statistics per procedure** table displays
- [ ] **VAS distribution chart** displays
- [ ] **Trend charts** display (when ≥5 cases)
- [ ] **User activity** table displays

---

## ➕ Manage Procedures Tab

### Add New Procedure Subtab

- [ ] **Add procedure tab** loads
- [ ] **Procedure name input** works
- [ ] **KVÅ code input** works (optional)
- [ ] **Specialty dropdown** shows all specialties
- [ ] **"<Skapa ny>" specialty option** works
- [ ] **New specialty name input** appears when selected
- [ ] **Base MME input** works (1-50)
- [ ] **Pain type dropdown** works (somatic/visceral/mixed)
- [ ] **"Spara nytt ingrepp" button** creates procedure
- [ ] **Success message** displays after creation
- [ ] **Form validation** prevents empty submissions

### View Added Procedures Subtab

- [ ] **View procedures tab** loads
- [ ] **Custom procedures list** displays
- [ ] **Empty state** shows when no procedures added
- [ ] **Procedure expander** shows details
- [ ] **Specialty** displays correctly
- [ ] **Base MME** displays correctly
- [ ] **Pain type** displays correctly
- [ ] **Procedure ID** displays correctly
- [ ] **Delete button (🗑️)** works for own procedures
- [ ] **Lock icon (🔒)** shows for others' procedures
- [ ] **Delete permissions** enforced correctly

---

## 🔧 Admin Tab (Admin Only)

### Visibility

- [ ] **Admin tab** visible only for admin users
- [ ] **Admin tab** hidden for regular users

### User Management Subtab

- [ ] **User list** displays all users
- [ ] **User count** displays correctly
- [ ] **Admin badge** displays for admin users
- [ ] **User badge** displays for regular users
- [ ] **Case count** displays per user
- [ ] **User ID** displays
- [ ] **Delete button** disabled for admin users
- [ ] **Delete button** enabled for regular users
- [ ] **Delete confirmation** dialog works
- [ ] **User deletion** works correctly
- [ ] **Delete cancel** works

### Create New User

- [ ] **Create user form** displays
- [ ] **Username input** works
- [ ] **"Skapa som admin" checkbox** works
- [ ] **"Skapa Användare" button** creates user
- [ ] **Username validation** prevents short names
- [ ] **Duplicate validation** prevents duplicate usernames
- [ ] **Success message** displays after creation

### ML Settings Subtab

- [ ] **ML settings tab** loads
- [ ] **Target VAS input** works (0-3)
- [ ] **Max dose input** works (10-30)
- [ ] **Current values** display correctly
- [ ] **"Spara ML-Inställningar" button** saves settings
- [ ] **Success message** displays after save
- [ ] **All settings table** displays (if implemented)

### System Status Subtab

- [ ] **System status tab** loads
- [ ] **Total cases metric** displays
- [ ] **User count metric** displays
- [ ] **Standard procedures count** displays
- [ ] **Custom procedures count** displays
- [ ] **Rule engine config** displays
- [ ] **ML engine config** displays
- [ ] **Drug data count** displays
- [ ] **Drug classes** expandable list works

---

## 🔄 Integration & Workflows

### Complete New Case Workflow

- [ ] **1. Login** with new user
- [ ] **2. Enter patient data** (all fields)
- [ ] **3. Select procedure**
- [ ] **4. Add temporal doses** (optional)
- [ ] **5. Select adjuvants** (optional)
- [ ] **6. Calculate recommendation**
- [ ] **7. Review recommendation** and warnings
- [ ] **8. Adjust administered dose**
- [ ] **9. Save initial case**
- [ ] **10. Add postoperative data**
- [ ] **11. Update complete case**
- [ ] **12. View in history tab**
- [ ] **13. Case appears correctly**

### Edit Existing Case Workflow

- [ ] **1. Navigate to History tab**
- [ ] **2. Find case to edit**
- [ ] **3. Click edit button**
- [ ] **4. Return to Dosing tab**
- [ ] **5. Form pre-filled** with case data
- [ ] **6. Modify values**
- [ ] **7. Recalculate** (optional)
- [ ] **8. Update case**
- [ ] **9. Changes saved** correctly
- [ ] **10. Edit history** recorded

### Admin User Management Workflow

- [ ] **1. Login as admin**
- [ ] **2. Navigate to Admin tab**
- [ ] **3. View all users**
- [ ] **4. Create new user**
- [ ] **5. User appears in list**
- [ ] **6. User can login**
- [ ] **7. Admin can delete user** (if needed)

---

## 🎨 UI/UX Checks

### General

- [ ] **Dark theme** applies consistently
- [ ] **Layout** fits 1080p screen without scrolling
- [ ] **Responsive design** works
- [ ] **Loading states** display during operations
- [ ] **Error messages** display clearly
- [ ] **Success messages** display clearly
- [ ] **Icons and emojis** display correctly

### Navigation

- [ ] **Tab switching** works smoothly
- [ ] **Active tab** highlighted correctly
- [ ] **Tab order** correct for all user types
- [ ] **Back navigation** works (browser back button)

### Forms

- [ ] **Input fields** have clear labels
- [ ] **Placeholders** provide helpful hints
- [ ] **Validation** prevents invalid inputs
- [ ] **Error messages** appear inline
- [ ] **Required fields** marked/enforced
- [ ] **Form submission** works correctly

---

## 🛡️ Security & Permissions

- [ ] **Unauthenticated users** redirected to login
- [ ] **Regular users** cannot see Admin tab
- [ ] **Regular users** can only edit own cases
- [ ] **Regular users** can only delete own cases
- [ ] **Admin users** can edit all cases
- [ ] **Admin users** can delete all cases
- [ ] **Admin users** can manage all users
- [ ] **Password protection** works for admin accounts
- [ ] **Case-insensitive usernames** work correctly
- [ ] **Case-sensitive passwords** work correctly

---

## 📊 Data Integrity

- [ ] **Cases save** with correct data
- [ ] **Cases load** with correct data
- [ ] **Calculations** produce consistent results
- [ ] **Timestamps** accurate
- [ ] **User attribution** correct
- [ ] **Edit history** tracks all changes
- [ ] **Temporal doses** save/load correctly
- [ ] **Calibration factors** update correctly

---

## 🚀 Performance

- [ ] **Initial load** < 5 seconds
- [ ] **Tab switching** < 1 second
- [ ] **Calculations** < 2 seconds
- [ ] **Save operations** < 2 seconds
- [ ] **Large datasets** handle gracefully
- [ ] **No memory leaks** during extended use

---

## ✅ Summary

**Total Checkpoints: 250+**

### Coverage by Category:
- Authentication: 7 checks
- Dosing Tab: 60+ checks
- History Tab: 30+ checks
- Learning Tab: 25+ checks
- Procedures Tab: 20+ checks
- Admin Tab: 30+ checks
- Integration: 20+ checks
- UI/UX: 20+ checks
- Security: 10+ checks
- Data Integrity: 8 checks
- Performance: 6 checks

---

## 📝 Notes

- Use this checklist for manual testing
- Automated tests cover most of these checks
- Some checks may require specific data conditions
- Performance checks may vary by system

---

**Last Updated**: 2025-10-19
**Version**: 1.0
