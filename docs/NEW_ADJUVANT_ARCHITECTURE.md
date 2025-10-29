# NY ADJUVANT-ARKITEKTUR

## PROBLEM MED NUVARANDE SYSTEM

Nuvarande koden har flera problem:
1. **Inkonsekvent approach**: Vissa använder multipliers (0.8), vissa absolut reduktion (sevoflurane)
2. **Duplicerad kod**: Varje adjuvant har nästan identisk kod
3. **Svårt att underhålla**: 200+ rader repetitiv kod
4. **Hårdkodade värden**: Selectivity och potency inte learnable

## NY LÖSNING: UNIFIED ADJUVANT SYSTEM

### Helper Function Pattern
```python
def apply_learnable_adjuvant(
    current_mme: float,
    adjuvant_name: str,
    base_selectivity: float,
    base_potency_mme: float,
    procedure_pain_type: float,
    user_id: int = None
) -> float:
    """
    Apply adjuvant with learnable selectivity and potency.

    Args:
        current_mme: Nuvarande MME-behov
        adjuvant_name: T.ex. "NSAID", "Catapressan"
        base_selectivity: Startpunkt 1-10 (1=visceral, 10=somatic)
        base_potency_mme: Startpunkt för absolut MME-reduktion
        procedure_pain_type: Ingreppets smärttyp (1-10)
        user_id: För learning lookup

    Returns:
        Ny MME efter adjuvant-effekt
    """
    if not user_id:
        # Fallback utan learning
        selectivity = base_selectivity
        potency_mme = base_potency_mme
    else:
        # Learned values
        selectivity = db.get_adjuvant_selectivity(user_id, adjuvant_name, procedure_pain_type, base_selectivity)
        potency_mme = db.get_adjuvant_potency(user_id, adjuvant_name, procedure_pain_type, base_potency_mme)

    # Beräkna mismatch penalty
    penalty = pc.calculate_mismatch_penalty(procedure_pain_type, selectivity)

    # Applicera potency med penalty
    effective_reduction = potency_mme * penalty

    new_mme = max(0, current_mme - effective_reduction)
    return new_mme
```

### Conversion från Multipliers till Absolut Potency

**Gamla systemet** (multiplier):
```python
base_mult = 0.80  # 20% reduktion
mme *= base_mult  # Om MME=50 → 40
```

**Nya systemet** (absolut potency):
```python
base_potency_mme = 10  # Reducerar 10 MME
mme -= base_potency_mme  # Om MME=50 → 40
```

**Varför bättre?**
- **Kliniskt meningsfullt**: "NSAID reducerar ~15 MME" är lättare att förstå än "0.80 multiplier"
- **Learnable**: Systemet kan lära sig exakt hur många MME läkemedlet tar bort
- **Dosresponse**: Olika doser av samma läkemedel = olika potency (redan så för ketamin/lidokain)

### Base Values för Adjuvanter

| Adjuvant | Base Selectivity | Base Potency (MME) | Rationale |
|----------|-----------------|-------------------|-----------|
| **NSAID (Ketorolac)** | 9 (somatic) | 15 MME | Starkt somatiskt, potent COX-hämmare |
| **NSAID (Ibuprofen)** | 9 (somatic) | 8 MME | Somatiskt, lägre potens |
| **NSAID (Parecoxib)** | 9 (somatic) | 11 MME | COX-2 selektiv, lång duration |
| **Catapressan** | 3 (visceral) | 10 MME | Visceralt via α2-agonism, GI/smooth muscle |
| **Droperidol** | 5 (neutral) | 8 MME | Antiemetiskt, neutral smärtselektivitet |
| **Ketamin (liten bolus)** | 5 (neutral) | 5 MME | NMDA-antagonist, neutral |
| **Ketamin (stor bolus)** | 5 (neutral) | 10 MME | Högre dos = mer potency |
| **Ketamin (infusion liten)** | 5 (neutral) | 8 MME | Kontinuerlig effekt |
| **Ketamin (infusion stor)** | 5 (neutral) | 15 MME | Högdos kontinuerlig |
| **Lidokain (bolus)** | 6 (mild somatic) | 5 MME | Na-kanal block, perifera nerver |
| **Lidokain (infusion)** | 6 (mild somatic) | 10 MME | Kontinuerlig systemisk effekt |
| **Betapred (4mg)** | 5 (neutral) | 2 MME | Antiinflammatoriskt, låg potens |
| **Betapred (8mg)** | 5 (neutral) | 4 MME | Dubbel dos = dubbel effekt |
| **Sevoflurane** | 5 (neutral) | 2 MME | Låg postop residual effekt |
| **Infiltration** | 9 (somatic) | 8 MME | Lokalbedövning, starkt somatiskt |

**NOTE**: Dessa är STARTPUNKTER. Systemet lär sig över tid och justerar både selectivity och potency.

### Synergy Learning

Efter alla individuella adjuvanter applicerats:

```python
# Efter alla adjuvanter
mme_after_adjuvants = current_mme

user_id = auth.get_current_user_id()
if user_id:
    drug_combo = db.get_drug_combination_key(inputs)
    if drug_combo:  # Minst 2 läkemedel
        synergy_factor = db.get_synergy_factor(user_id, drug_combo)
        # Synergy multiplicerar TOTAL effekt (appliceras på slutresultat)
        mme = mme_after_adjuvants * synergy_factor
```

**Exempel**:
- NSAID + Betapred ofta synergistiskt (båda antiinflammatoriska)
- Catapressan + Droperidol kan vara antagonistiskt (sedation vs klarhet)

## IMPLEMENTATION PLAN

### Phase 1: ✅ DONE
- Database schema med learned_selectivity, learned_potency
- Database functions: get/update_adjuvant_selectivity, get/update_adjuvant_potency

### Phase 2: IN PROGRESS
- Skapa `apply_learnable_adjuvant()` helper function
- Refaktorera alla 8 adjuvanter att använda helper
- Lägga till synergy i slutet av calculate_rule_based_dose()

### Phase 3: TODO
- Uppdatera handle_save_and_learn() för att kalla update functions
- Skapa adjustment calculation helpers
- Testa systemet

## KÖR PÅ!
