"""
Interpolation Engine - Intelligent Estimation från Närliggande Datapunkter
===========================================================================
Detta system kan estimera dosberäkningar för åldrar och vikter där vi saknar data
genom att analysera mönster från närliggande datapunkter.

Exempel:
- Vi har data för 45-åringar och 47-åringar, men inte 46-åringar
- Systemet interpolerar: age_factor(46) ≈ genomsnitt av age_factor(45) och age_factor(47)

Detta gör systemet robust även med gles data (sparse data).
"""

import logging
import math
from typing import Dict, List, Tuple, Optional
import database as db

logger = logging.getLogger(__name__)

# Interpolationsparametrar
MAX_AGE_DISTANCE = 5  # Max avstånd för åldersinterpolation (år)
MAX_WEIGHT_DISTANCE = 10  # Max avstånd för viktinterpolation (kg)
MIN_OBSERVATIONS_FOR_INTERPOLATION = 3  # Minsta antal observationer för att lita på en datapunkt


def get_age_bucket(age: int) -> int:
    """
    Returnera exakt ålder som bucket (varje år är en egen kategori).

    Args:
        age: Ålder i år

    Returns:
        Ålder som bucket (samma som input)

    Examples:
        >>> get_age_bucket(5)
        5
        >>> get_age_bucket(72)
        72
    """
    return int(age)


def get_weight_bucket(weight: float) -> int:
    """
    Returnera vikt avrundad till närmaste hela kilo.

    Args:
        weight: Vikt i kg

    Returns:
        Vikt avrundad till närmaste kilo

    Examples:
        >>> get_weight_bucket(73.4)
        73
        >>> get_weight_bucket(73.7)
        74
        >>> get_weight_bucket(15.2)
        15
    """
    return int(round(weight))


def gaussian_weight(distance: float, sigma: float = 1.0) -> float:
    """
    Beräkna Gaussisk viktning baserat på avstånd.

    Närmare datapunkter får högre vikt i interpolationen.

    Args:
        distance: Avstånd från målpunkten (ex: 2 år skillnad)
        sigma: Standardavvikelse (kontrollerar hur snabbt vikten minskar)

    Returns:
        Vikt mellan 0 och 1 (1 = exakt match, ~0 = långt bort)

    Examples:
        >>> gaussian_weight(0)  # Exakt match
        1.0
        >>> gaussian_weight(1)  # 1 år/kg bort
        0.61
        >>> gaussian_weight(3)  # 3 år/kg bort
        0.01
    """
    return math.exp(-(distance ** 2) / (2 * sigma ** 2))


def get_nearby_age_factors(target_age: int, max_distance: int = MAX_AGE_DISTANCE) -> List[Tuple[int, float, int, float]]:
    """
    Hämta ålderfaktorer från närliggande åldrar.

    Args:
        target_age: Målålder vi vill interpolera för
        max_distance: Max avstånd i år att söka

    Returns:
        List of tuples: (age, age_factor, num_observations, distance_weight)
        Sorterad efter avstånd (närmast först)
    """
    nearby_factors = []

    # Sök inom +/- max_distance år
    for age_offset in range(-max_distance, max_distance + 1):
        neighbor_age = target_age + age_offset

        if neighbor_age < 0:
            continue

        # Hämta data från databas
        try:
            data = db.get_age_bucket_learning(neighbor_age)

            if data and data.get('num_observations', 0) >= MIN_OBSERVATIONS_FOR_INTERPOLATION:
                distance = abs(age_offset)
                weight = gaussian_weight(distance, sigma=2.0)

                nearby_factors.append((
                    neighbor_age,
                    data['age_factor'],
                    data['num_observations'],
                    weight
                ))
        except Exception as e:
            logger.debug(f"No data for age {neighbor_age}: {e}")
            continue

    # Sortera efter avstånd
    nearby_factors.sort(key=lambda x: abs(x[0] - target_age))

    return nearby_factors


def get_nearby_weight_factors(target_weight: int, max_distance: int = MAX_WEIGHT_DISTANCE) -> List[Tuple[int, float, int, float]]:
    """
    Hämta viktfaktorer från närliggande vikter.

    Args:
        target_weight: Målvikt vi vill interpolera för (i kg)
        max_distance: Max avstånd i kg att söka

    Returns:
        List of tuples: (weight, weight_factor, num_observations, distance_weight)
        Sorterad efter avstånd (närmast först)
    """
    nearby_factors = []

    # Sök inom +/- max_distance kg
    for weight_offset in range(-max_distance, max_distance + 1):
        neighbor_weight = target_weight + weight_offset

        if neighbor_weight < 1:
            continue

        # Hämta data från databas
        try:
            data = db.get_weight_bucket_learning(neighbor_weight)

            if data and data.get('num_observations', 0) >= MIN_OBSERVATIONS_FOR_INTERPOLATION:
                distance = abs(weight_offset)
                weight = gaussian_weight(distance, sigma=3.0)

                nearby_factors.append((
                    neighbor_weight,
                    data['weight_factor'],
                    data['num_observations'],
                    weight
                ))
        except Exception as e:
            logger.debug(f"No data for weight {neighbor_weight}: {e}")
            continue

    # Sortera efter avstånd
    nearby_factors.sort(key=lambda x: abs(x[0] - target_weight))

    return nearby_factors


def interpolate_age_factor(age: int, default_factor: float) -> Dict:
    """
    Interpolera ålderfaktor från närliggande åldrar om direktdata saknas.

    Algoritm:
    1. Försök hämta exakt data för denna ålder
    2. Om data saknas eller är otillräcklig, hitta närliggande åldrar
    3. Väg samman deras faktorer baserat på avstånd (Gaussisk viktning)

    Args:
        age: Målålder
        default_factor: Default-värde från regelbaserad formel (fallback)

    Returns:
        Dict med:
            - 'age_factor': Interpolerad/faktisk faktor
            - 'method': 'direct', 'interpolated', eller 'default'
            - 'num_observations': Antal observationer (0 för interpolerade)
            - 'sources': Lista över källor som användes
    """
    # Validate default_factor
    if default_factor is None:
        default_factor = 1.0  # Use 1.0 as neutral default if None provided

    bucket = get_age_bucket(age)

    # 1. Försök hämta direktdata
    try:
        direct_data = db.get_age_bucket_learning(bucket)
        if direct_data and direct_data.get('num_observations', 0) >= MIN_OBSERVATIONS_FOR_INTERPOLATION:
            return {
                'age_factor': direct_data['age_factor'],
                'method': 'direct',
                'num_observations': direct_data['num_observations'],
                'sources': [f"Age {age} (direct data, n={direct_data['num_observations']})"]
            }
    except Exception as e:
        logger.debug(f"No direct data for age {age}: {e}")

    # 2. Interpolera från närliggande åldrar
    nearby = get_nearby_age_factors(age)

    if not nearby:
        # Ingen data alls, använd default
        return {
            'age_factor': default_factor,
            'method': 'default',
            'num_observations': 0,
            'sources': ['Default formula (no nearby data)']
        }

    # 3. Vägt genomsnitt baserat på Gaussisk viktning
    total_weighted_factor = 0.0
    total_weight = 0.0
    sources = []

    for neighbor_age, neighbor_factor, num_obs, distance_weight in nearby:
        # Vikta också med antal observationer (mer data = mer förtroende)
        observation_weight = min(1.0, num_obs / 10.0)  # Plateau vid 10 observationer
        combined_weight = distance_weight * observation_weight

        total_weighted_factor += neighbor_factor * combined_weight
        total_weight += combined_weight

        sources.append(f"Age {neighbor_age} (factor={neighbor_factor:.3f}, n={num_obs}, weight={combined_weight:.3f})")

    if total_weight == 0:
        # Säkerhetscheck
        return {
            'age_factor': default_factor,
            'method': 'default',
            'num_observations': 0,
            'sources': ['Default formula (insufficient nearby data)']
        }

    interpolated_factor = total_weighted_factor / total_weight

    # Sanity check: interpolerad faktor ska vara rimlig
    if interpolated_factor < 0.2 or interpolated_factor > 2.0:
        logger.warning(f"Interpolated age factor {interpolated_factor:.3f} for age {age} is out of range, using default")
        return {
            'age_factor': default_factor,
            'method': 'default',
            'num_observations': 0,
            'sources': [f'Default formula (interpolated value {interpolated_factor:.3f} out of range)']
        }

    return {
        'age_factor': interpolated_factor,
        'method': 'interpolated',
        'num_observations': 0,  # Detta är en estimat, inte verklig data
        'sources': sources,
        'nearby_count': len(nearby)
    }


def interpolate_weight_factor(weight: float, default_factor: float) -> Dict:
    """
    Interpolera viktfaktor från närliggande vikter om direktdata saknas.

    Samma algoritm som interpolate_age_factor men för vikt.

    Args:
        weight: Målvikt i kg
        default_factor: Default-värde (fallback)

    Returns:
        Dict med interpolerad faktor och metadata
    """
    # Validate default_factor
    if default_factor is None:
        default_factor = 1.0  # Use 1.0 as neutral default if None provided

    bucket = get_weight_bucket(weight)

    # 1. Försök hämta direktdata
    try:
        direct_data = db.get_weight_bucket_learning(bucket)
        if direct_data and direct_data.get('num_observations', 0) >= MIN_OBSERVATIONS_FOR_INTERPOLATION:
            return {
                'weight_factor': direct_data['weight_factor'],
                'method': 'direct',
                'num_observations': direct_data['num_observations'],
                'sources': [f"Weight {bucket}kg (direct data, n={direct_data['num_observations']})"]
            }
    except Exception as e:
        logger.debug(f"No direct data for weight {bucket}kg: {e}")

    # 2. Interpolera från närliggande vikter
    nearby = get_nearby_weight_factors(bucket)

    if not nearby:
        return {
            'weight_factor': default_factor,
            'method': 'default',
            'num_observations': 0,
            'sources': ['Default value (no nearby data)']
        }

    # 3. Vägt genomsnitt
    total_weighted_factor = 0.0
    total_weight = 0.0
    sources = []

    for neighbor_weight, neighbor_factor, num_obs, distance_weight in nearby:
        observation_weight = min(1.0, num_obs / 10.0)
        combined_weight = distance_weight * observation_weight

        total_weighted_factor += neighbor_factor * combined_weight
        total_weight += combined_weight

        sources.append(f"Weight {neighbor_weight}kg (factor={neighbor_factor:.3f}, n={num_obs}, weight={combined_weight:.3f})")

    if total_weight == 0:
        return {
            'weight_factor': default_factor,
            'method': 'default',
            'num_observations': 0,
            'sources': ['Default value (insufficient nearby data)']
        }

    interpolated_factor = total_weighted_factor / total_weight

    # Sanity check
    if interpolated_factor < 0.5 or interpolated_factor > 2.0:
        logger.warning(f"Interpolated weight factor {interpolated_factor:.3f} for {bucket}kg is out of range, using default")
        return {
            'weight_factor': default_factor,
            'method': 'default',
            'num_observations': 0,
            'sources': [f'Default value (interpolated value {interpolated_factor:.3f} out of range)']
        }

    return {
        'weight_factor': interpolated_factor,
        'method': 'interpolated',
        'num_observations': 0,
        'sources': sources,
        'nearby_count': len(nearby)
    }


def detect_age_trends(min_age: int = 0, max_age: int = 100) -> Dict:
    """
    Analysera trender i åldersdata för att upptäcka mönster.

    Detta kan användas för att identifiera:
    - I vilka åldersintervall behöver vi mer data?
    - Finns det oväntade "hopp" i dosbehovet?
    - Vilka åldrar har bra täckning?

    Args:
        min_age: Minimum ålder att analysera
        max_age: Maximum ålder att analysera

    Returns:
        Dict med analys av datatäckning och trender
    """
    coverage = []
    gaps = []

    for age in range(min_age, max_age + 1):
        try:
            data = db.get_age_bucket_learning(age)
            if data and data.get('num_observations', 0) > 0:
                coverage.append({
                    'age': age,
                    'factor': data['age_factor'],
                    'observations': data['num_observations']
                })
            else:
                gaps.append(age)
        except:
            gaps.append(age)

    return {
        'total_ages_analyzed': max_age - min_age + 1,
        'ages_with_data': len(coverage),
        'ages_without_data': len(gaps),
        'coverage_percent': len(coverage) / (max_age - min_age + 1) * 100,
        'coverage_details': coverage,
        'gaps': gaps
    }


def detect_weight_trends(min_weight: int = 10, max_weight: int = 150) -> Dict:
    """
    Analysera trender i viktdata för att upptäcka mönster.

    Args:
        min_weight: Minimum vikt att analysera (kg)
        max_weight: Maximum vikt att analysera (kg)

    Returns:
        Dict med analys av datatäckning och trender
    """
    coverage = []
    gaps = []

    for weight in range(min_weight, max_weight + 1):
        try:
            data = db.get_weight_bucket_learning(weight)
            if data and data.get('num_observations', 0) > 0:
                coverage.append({
                    'weight': weight,
                    'factor': data['weight_factor'],
                    'observations': data['num_observations']
                })
            else:
                gaps.append(weight)
        except:
            gaps.append(weight)

    return {
        'total_weights_analyzed': max_weight - min_weight + 1,
        'weights_with_data': len(coverage),
        'weights_without_data': len(gaps),
        'coverage_percent': len(coverage) / (max_weight - min_weight + 1) * 100,
        'coverage_details': coverage,
        'gaps': gaps
    }
