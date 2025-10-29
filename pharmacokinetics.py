"""
Pharmacokinetics Module - Temporal Dosering System
Beräknar farmakokinetiska effekter över tid för temporal dosering
"""

import math
from typing import Dict, List


def calculate_fentanyl_remaining_at_opslut(dose_mcg: float, time_before_opslut_min: int) -> float:
    """
    Beräkna kvarvarande fentanyl-effekt vid opslut.

    Fentanyl halveringstid:
    - Snabb distribution: t½ = 15 min (60%)
    - Långsam elimination: t½ = 210 min (40%)

    Använder bi-exponentiell modell för att simulera context-sensitive half-time

    Args:
        dose_mcg: Dos i mikrogram
        time_before_opslut_min: Tid innan opslut (positiv = före opslut)

    Returns:
        Kvarvarande dos i mikrogram vid opslut

    Example:
        # Fentanyl 200 µg given 90 min före opslut
        remaining = calculate_fentanyl_remaining_at_opslut(200, 90)
        # remaining ≈ 61 µg (~30% av originaldos)
    """
    if time_before_opslut_min <= 0:
        return dose_mcg

    # Bi-exponentiell decay
    # Fast component: 60% av dosen, t½ = 15 min
    fast_component = 0.6 * dose_mcg * (0.5 ** (time_before_opslut_min / 15))

    # Slow component: 40% av dosen, t½ = 210 min
    slow_component = 0.4 * dose_mcg * (0.5 ** (time_before_opslut_min / 210))

    remaining = fast_component + slow_component
    return max(0, remaining)


def calculate_fentanyl_remaining_at_time(
    dose_mcg: float,
    time_given_relative_to_opslut: int,
    time_evaluate_relative_to_opslut: int
) -> float:
    """
    Beräkna kvarvarande fentanyl vid en godtycklig tidpunkt.

    Args:
        dose_mcg: Dos i mikrogram
        time_given_relative_to_opslut: När dosen gavs (negativ = före opslut)
        time_evaluate_relative_to_opslut: När vi utvärderar (ex: +60 för 1h postop)

    Returns:
        Kvarvarande dos i mikrogram vid utvärderingstidpunkt
    """
    time_since_admin = time_evaluate_relative_to_opslut - time_given_relative_to_opslut

    if time_since_admin < 0:
        return 0.0  # Dosen inte given än

    if time_since_admin == 0:
        return dose_mcg

    # Bi-exponentiell decay
    fast_component = 0.6 * dose_mcg * (0.5 ** (time_since_admin / 15))
    slow_component = 0.4 * dose_mcg * (0.5 ** (time_since_admin / 210))

    remaining = fast_component + slow_component
    return max(0, remaining)


def calculate_adjuvant_effect_at_time(
    drug_data: dict,
    dose: float,
    time_relative_to_opslut: int,
    postop_time: int = 0
) -> float:
    """
    Beräkna adjuvant-effekt vid given tidpunkt.

    Använder trapezoidal effect curve:
    - Onset: Stiger från 0 till 1
    - Peak: Håller max effekt
    - Duration: Avtar linjärt till 0

    Args:
        drug_data: Dictionary från LÄKEMEDELS_DATA med temporal parametrar
        dose: Given dos
        time_relative_to_opslut: När dosen gavs (min relativt opslut)
        postop_time: Tid efter opslut vi utvärderar (min)

    Returns:
        Effektiv potency (0-1 scale)

    Example:
        # Ibuprofen 400mg given -10 min, utvärdera vid +60 min postop
        # => 70 min sedan administrering
        # Onset 30 min, Peak 60 min, Duration 360 min
        # => Full effekt (1.0)
    """
    # Tid sedan administrering
    time_since_admin = postop_time - time_relative_to_opslut

    if time_since_admin < 0:
        return 0.0  # Inte givet än

    # Hämta farmakokinetiska parametrar
    t_onset = drug_data.get('onset_minutes', 30)      # Tid till effekt
    t_peak = drug_data.get('peak_minutes', 60)        # Tid till max effekt
    t_duration = drug_data.get('duration_minutes', 240)  # Total duration

    # Trapezoidal effect curve
    if time_since_admin < t_onset:
        # Stiger till max
        effect = time_since_admin / t_onset
    elif time_since_admin < t_peak:
        # Max effekt
        effect = 1.0
    elif time_since_admin < t_duration:
        # Avtar linjärt
        effect = 1.0 - ((time_since_admin - t_peak) / (t_duration - t_peak))
    else:
        # Slut på effekt
        effect = 0.0

    return max(0, min(1, effect))


def calculate_total_opioid_auc(temporal_doses: List[Dict], duration_minutes: int = 120) -> float:
    """
    Beräkna total opioid Area Under Curve (AUC) för temporal dosering.

    AUC = integral av opioid-koncentration över tid
    Används som ML feature för total opioid-exposition

    Args:
        temporal_doses: Lista av temporal doser
        duration_minutes: Total tid att beräkna AUC för (default 2h)

    Returns:
        AUC i µg·min (mikrogram × minuter)
    """
    auc = 0.0
    time_step = 5  # Beräkna var 5:e minut

    for t in range(-180, duration_minutes, time_step):
        # Summera alla opioider vid tidpunkt t
        total_at_time = 0.0
        for dose_entry in temporal_doses:
            if dose_entry['drug_type'] in ['fentanyl', 'oxycodone']:
                # Konvertera till fentanyl-ekvivalenter
                if dose_entry['drug_type'] == 'fentanyl':
                    dose_mcg = dose_entry['dose']
                elif dose_entry['drug_type'] == 'oxycodone':
                    # Oxikodon: 1 mg PO ≈ 15 µg fentanyl
                    dose_mcg = dose_entry['dose'] * 15

                remaining = calculate_fentanyl_remaining_at_time(
                    dose_mcg,
                    dose_entry['time_relative_minutes'],
                    t
                )
                total_at_time += remaining

        # Trapezoid integration: area = height × width
        auc += total_at_time * time_step

    return auc


def calculate_temporal_fentanyl_mme_at_opslut(temporal_doses: List[Dict]) -> float:
    """
    Beräkna total fentanyl MME vid opslut (tid 0:00).

    Args:
        temporal_doses: Lista av temporal doser

    Returns:
        Total MME från fentanyl vid opslut
    """
    total_mme = 0.0

    for dose_entry in temporal_doses:
        if dose_entry['drug_type'] == 'fentanyl':
            time_before_opslut = -dose_entry['time_relative_minutes']  # Negativ tid = före
            if time_before_opslut > 0:
                remaining_mcg = calculate_fentanyl_remaining_at_opslut(
                    dose_entry['dose'],
                    time_before_opslut
                )
                # Fentanyl: 100 µg = 10 MME
                mme = (remaining_mcg / 100) * 10
                total_mme += mme
            elif time_before_opslut == 0:
                # Given exakt vid opslut
                mme = (dose_entry['dose'] / 100) * 10
                total_mme += mme

    return total_mme


def calculate_temporal_adjuvant_reduction_at_postop(
    temporal_doses: List[Dict],
    drug_database: dict,
    postop_time: int = 60
) -> float:
    """
    Beräkna total adjuvant MME-reduktion vid postop tidpunkt.

    Args:
        temporal_doses: Lista av temporal doser
        drug_database: LÄKEMEDELS_DATA från config.py
        postop_time: Postop tid att utvärdera (default 60 min)

    Returns:
        Total MME-reduktion från adjuvanter
    """
    total_reduction = 0.0

    adjuvant_types = ['nsaid', 'catapressan', 'droperidol', 'ketamine',
                     'lidocaine', 'betapred']

    for dose_entry in temporal_doses:
        if dose_entry['drug_type'] in adjuvant_types:
            # Hitta drug_data baserat på drug_name eller drug_type
            drug_key = _find_drug_key_from_temporal_entry(dose_entry, drug_database)
            if drug_key:
                drug_data = drug_database[drug_key]

                # Beräkna effekt vid postop tidpunkt
                effect = calculate_adjuvant_effect_at_time(
                    drug_data,
                    dose_entry['dose'],
                    dose_entry['time_relative_minutes'],
                    postop_time
                )

                # Effective reduction = base potency × effect
                effective_reduction = drug_data.get('potency_mme', 0) * effect
                total_reduction += effective_reduction

    return total_reduction


def _find_drug_key_from_temporal_entry(dose_entry: Dict, drug_database: dict) -> str:
    """
    Hitta läkemedelsnyckeln i LÄKEMEDELS_DATA baserat på temporal dose entry.

    Args:
        dose_entry: Temporal dose dictionary
        drug_database: LÄKEMEDELS_DATA

    Returns:
        Nyckel i LÄKEMEDELS_DATA eller None
    """
    drug_type = dose_entry['drug_type']
    drug_name = dose_entry['drug_name'].lower()

    # Försök matcha på drug_name
    for key, data in drug_database.items():
        if data['name'].lower() in drug_name or drug_name in data['name'].lower():
            return key

    # Försök matcha på drug_type
    type_mapping = {
        'fentanyl': 'fentanyl',
        'nsaid': 'ibuprofen_400mg',  # Default NSAID
        'catapressan': 'clonidine',
        'droperidol': 'droperidol',
        'ketamine': 'ketamine_small_bolus',  # Default ketamine
        'lidocaine': 'lidocaine_bolus',  # Default lidocaine
        'betapred': 'betamethasone_4mg',  # Default betapred
        'oxycodone': 'oxycodone'
    }

    return type_mapping.get(drug_type, None)


def get_temporal_dose_summary(temporal_doses: List[Dict]) -> Dict:
    """
    Generera sammanfattning av temporal dosering för UI/rapporter.

    Args:
        temporal_doses: Lista av temporal doser

    Returns:
        Dictionary med sammanfattning
    """
    if not temporal_doses:
        return {
            'total_doses': 0,
            'preop_doses': 0,
            'periop_doses': 0,
            'postop_doses': 0,
            'drugs_used': []
        }

    preop = [d for d in temporal_doses if d['time_relative_minutes'] < -30]
    periop = [d for d in temporal_doses if -30 <= d['time_relative_minutes'] < 0]
    postop = [d for d in temporal_doses if d['time_relative_minutes'] >= 0]

    drugs_used = list(set([d['drug_name'] for d in temporal_doses]))

    return {
        'total_doses': len(temporal_doses),
        'preop_doses': len(preop),
        'periop_doses': len(periop),
        'postop_doses': len(postop),
        'drugs_used': drugs_used,
        'earliest_dose_time': min([d['time_relative_minutes'] for d in temporal_doses]),
        'latest_dose_time': max([d['time_relative_minutes'] for d in temporal_doses])
    }


def format_time_relative(minutes: int) -> str:
    """
    Formatera relativ tid för UI-visning.

    Args:
        minutes: Minuter relativt opslut (negativ = före, positiv = efter)

    Returns:
        Formaterad sträng (ex: "-1:30", "+0:45", "0:00")
    """
    if minutes == 0:
        return "0:00"

    sign = "-" if minutes < 0 else "+"
    abs_minutes = abs(minutes)
    hours = abs_minutes // 60
    mins = abs_minutes % 60

    return f"{sign}{hours}:{mins:02d}"


def parse_time_relative(time_str: str) -> int:
    """
    Parsa relativ tidsträng till minuter.

    Args:
        time_str: Tidsträng (ex: "-1:30", "+0:45", "0:00")

    Returns:
        Minuter relativt opslut
    """
    time_str = time_str.strip()

    if time_str == "0:00":
        return 0

    # Extrahera tecken
    sign = 1
    if time_str.startswith('-'):
        sign = -1
        time_str = time_str[1:]
    elif time_str.startswith('+'):
        sign = 1
        time_str = time_str[1:]

    # Parsa timmar:minuter
    parts = time_str.split(':')
    if len(parts) != 2:
        raise ValueError(f"Invalid time format: {time_str}")

    hours = int(parts[0])
    minutes = int(parts[1])

    total_minutes = hours * 60 + minutes
    return total_minutes * sign
