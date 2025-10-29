# LEARNABLE ADJUVANT SYSTEM - Implementation Status

## ✅ COMPLETEDKUND (Database Layer)

### 1. Database Schema Updates
- ✅ Added `learned_selectivity` column to `adjuvant_effectiveness`
- ✅ Added `learned_potency` column to `adjuvant_effectiveness`
- ✅ Added `selectivity_update_count` column
- ✅ Added `potency_update_count` column
- ✅ Added migration code för existing databases

### 2. New Database Functions Created

#### **Selectivity Learning** (Lines 1335-1409)
```python
get_adjuvant_selectivity(user_id, adjuvant_name, pain_type_score, base_selectivity)
update_adjuvant_selectivity(user_id, adjuvant_name, pain_type_score, base_selectivity, adjustment)
```
- **Learning Rate**: VERY SLOW (0.5-2% per case, requires ~50 cases to stabilize)
- **Range**: 1-10 (1=visceral, 10=somatic)
- **Purpose**: Lär sig vilken smärttyp läkemedlet fungerar bäst mot

#### **Potency Learning** (Lines 1411-1485)
```python
get_adjuvant_potency(user_id, adjuvant_name, pain_type_score, base_potency)
update_adjuvant_potency(user_id, adjuvant_name, pain_type_score, base_potency, adjustment)
```
- **Learning Rate**: MODERATE (3-10% per case, requires ~30 cases to stabilize)
- **Range**: 0.5x - 2.0x of base potency
- **Purpose**: Detta är KÄRNAN - lär sig hur mycket MME varje läkemedel reducerar

#### **Synergy Learning** (Already existed, lines 1272-1329)
```python
get_drug_combination_key(adjuvants_dict)
get_synergy_factor(user_id, drug_combination)
update_synergy_factor(user_id, drug_combination, adjustment)
```
- **Learning Rate**: SLOW (3-15% per case, requires ~15 cases to stabilize)
- **Range**: 0.85x - 1.20x (±15-20% effect)
- **Purpose**: Lär sig när kombinationer fungerar bättre/sämre än summan av delarna

---

## 🚧 TODO (Application Layer Integration)

### 3. Update `calculate_rule_based_dose()` in oxydos_v8.py

Nuvarande kod (ca rad 300-500) behöver uppdateras för varje adjuvant:

#### **Current Pattern (NSAID example, ~line 315)**:
```python
if inputs.get('nsaid_choice') and inputs['nsaid_choice'] != 'Ej given':
    nsaid_selectivity = 9  # HÅRDKODAT
    penalty = pc.calculate_mismatch_penalty(pain_type_score, nsaid_selectivity)

    base_mult = 0.80  # HÅRDKODAT

    user_id = auth.get_current_user_id()
    if user_id:
        learned_mult = db.get_adjuvant_multiplier(user_id, "NSAID", pain_type_score, base_mult)
        effective_multiplier = 1 - ((1 - learned_mult) * penalty)
    else:
        effective_multiplier = 1 - ((1 - base_mult) * penalty)
    mme *= effective_multiplier
```

#### **NEW Pattern Needed**:
```python
if inputs.get('nsaid_choice') and inputs['nsaid_choice'] != 'Ej given':
    # BASE VALUES (startpunkt för learning)
    base_selectivity = 9  # Somatic pain
    base_potency_mme = 15  # Reducerar ~15 MME i absolut effekt

    user_id = auth.get_current_user_id()
    if user_id:
        # Lär dig SELECTIVITY (vilken smärttyp det fungerar mot)
        learned_selectivity = db.get_adjuvant_selectivity(user_id, "NSAID", pain_type_score, base_selectivity)
        penalty = pc.calculate_mismatch_penalty(pain_type_score, learned_selectivity)

        # Lär dig POTENCY (hur mycket det reducerar)
        learned_potency_mme = db.get_adjuvant_potency(user_id, "NSAID", pain_type_score, base_potency_mme)

        # Beräkna effekt: absolut reduktion justerad för mismatch
        effective_reduction_mme = learned_potency_mme * penalty
        mme -= effective_reduction_mme
        mme = max(0, mme)  # Kan inte gå under 0
    else:
        # Fallback om ej inloggad
        penalty = pc.calculate_mismatch_penalty(pain_type_score, base_selectivity)
        effective_reduction_mme = base_potency_mme * penalty
        mme -= effective_reduction_mme
        mme = max(0, mme)
```

#### **Apply to ALL adjuvants**:
- [ ] NSAID (~line 315)
- [ ] Catapressan (~line 340)
- [ ] Droperidol (~line 365)
- [ ] Ketamin (~line 380)
- [ ] Lidokain (~line 400)
- [ ] Betapred (~line 422)
- [ ] Sevoflurane (~line 440)
- [ ] Infiltration (~line 460)

#### **Add Synergy Calculation** (AFTER all adjuvants applied):
```python
# Efter att alla adjuvanter har applicerats
user_id = auth.get_current_user_id()
if user_id:
    drug_combo = db.get_drug_combination_key(inputs)
    if drug_combo:  # Minst 2 läkemedel
        synergy_factor = db.get_synergy_factor(user_id, drug_combo)
        # Synergy appliceras på TOTALA effekten
        mme *= synergy_factor
```

---

### 4. Update `handle_save_and_learn()` in oxydos_v8.py

Nuvarande kod (ca rad 700-900) behöver uppdateras:

#### **Current Pattern (simplified)**:
```python
def handle_save_and_learn():
    # ... beräkna error/adjustment ...

    # Uppdatera adjuvant effectiveness
    if nsaid_given:
        db.update_adjuvant_effectiveness(user_id, "NSAID", pain_type_score,
                                        base_mult, adjustment)

    # ... repeat för alla adjuvanter ...
```

#### **NEW Pattern Needed**:
```python
def handle_save_and_learn():
    # ... beräkna error/adjustment ...

    # För varje given adjuvant:
    if nsaid_given:
        # Uppdatera MULTIPLIER (backwards compatibility)
        db.update_adjuvant_effectiveness(user_id, "NSAID", pain_type_score,
                                        base_mult, adjustment)

        # Uppdatera SELECTIVITY (långsamt - specificity för smärttyp)
        # Positiv adjustment om VAS låg OCH rätt smärttyp
        selectivity_adjustment = calculate_selectivity_adjustment(vas, expected_vas, pain_type_score, nsaid_selectivity)
        db.update_adjuvant_selectivity(user_id, "NSAID", pain_type_score,
                                      base_selectivity=9, adjustment=selectivity_adjustment)

        # Uppdatera POTENCY (måttligt snabbt - absolut effekt)
        # Positiv adjustment om VAS låg = läkemedlet funkade bra
        potency_adjustment = calculate_potency_adjustment(vas, expected_vas, rescue_given)
        db.update_adjuvant_potency(user_id, "NSAID", pain_type_score,
                                  base_potency=15, adjustment=potency_adjustment)

    # ... repeat för alla adjuvanter ...

    # Uppdatera SYNERGY (om >= 2 adjuvanter gavs)
    drug_combo = db.get_drug_combination_key(inputs)
    if drug_combo:
        synergy_adjustment = calculate_synergy_adjustment(overall_outcome)
        db.update_synergy_factor(user_id, drug_combo, synergy_adjustment)
```

#### **Helper Functions Needed**:
```python
def calculate_selectivity_adjustment(vas, expected_vas, procedure_pain_type, adjuvant_selectivity):
    """
    Beräkna om läkemedlets selectivity matchade smärttypen bra.
    Returns: -1.0 to +1.0
    """
    # Om outcome bra OCH pain types matchar → positiv
    # Om outcome dåligt OCH pain types matchar → negativ (läkemedlet fungerar inte för denna smärttyp trots match)
    # Om outcome bra men pain types INTE matchar → stor positiv (läkemedlet fungerar bredare än tänkt!)
    pass

def calculate_potency_adjustment(vas, expected_vas, rescue_given):
    """
    Beräkna om läkemedlet hade mer/mindre effekt än förväntat.
    Returns: -1.0 to +1.0
    """
    # Om VAS < expected → positiv (läkemedlet starkare än tänkt)
    # Om VAS > expected → negativ (läkemedlet svagare än tänkt)
    # Om rescue → starkt negativ
    pass

def calculate_synergy_adjustment(overall_outcome):
    """
    Beräkna om kombinationen fungerade bättre/sämre än förväntat.
    Returns: -1.0 to +1.0
    """
    # Baserat på overall outcome jämfört med prediction
    pass
```

---

## 📊 LEARNING HIERARCHY (Speed)

1. **FASTEST: BaseMME** (FAS 3) - ~5-15% learning rate
   - Lär sig grunddosen för ingreppet

2. **FAST: Patient Factors** (FAS 1) - ~5-10% learning rate
   - Ålder, ASA, opioidtolerans, etc.

3. **MODERATE: Adjuvant Potency** (FAS 2 NEW) - ~3-10% learning rate
   - **DETTA ÄR KÄRNAN** - hur mycket varje läkemedel reducerar MME

4. **SLOW: Drug Synergies** (FAS 5) - ~3-15% learning rate (sliding)
   - Kombinationseffekter

5. **VERY SLOW: Adjuvant Selectivity** (FAS 2 NEW) - ~0.5-2% learning rate
   - Kräver många fall för att lära sig vilken smärttyp läkemedlet passar

---

## 🎯 GOAL REMINDER

**Målet**: Lära sig hur ont ingrepp gör (baseMME) och hur mycket patientfaktorer + läkemedel reducerar behovet, för att:
- Patienter vaknar snabbt
- Smärtfria (VAS ≤ 3)
- Korta UVA-tider
- Inget behov av rescue analgetika

**Därför**: Potency learning är KÄRNAN. Det är vad appen ska bli riktigt bra på.

---

## 📝 NEXT STEPS

1. ✅ Database schema updated
2. ✅ Database functions created
3. ⏳ Update `calculate_rule_based_dose()` - NEXT
4. ⏳ Update `handle_save_and_learn()` - AFTER 3
5. ⏳ Create adjustment calculation helpers - AFTER 4
6. ⏳ Test with real data - FINAL
