
import pandas as pd
import numpy as np
from config import LÄKEMEDELS_DATA, get_drug_by_ui_choice
import math

def add_engineered_features(cases_df: pd.DataFrame, procedures_df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a DataFrame with cases and adds all calculated features needed
    for both the rule engine and the ML model. Uses LÄKEMEDELS_DATA as the single source of truth.
    This is the centralized location for all feature engineering.
    """
    # Merge with procedure data to get pain scores
    proc_pain_scores = procedures_df[[
        'id', 'somatic_score', 'visceral_score', 'neuropathic_score'
    ]].rename(columns={'id': 'procedure_id'})

    df = pd.merge(cases_df, proc_pain_scores, on='procedure_id', how='left')
    df['somatic_score'] = df['somatic_score'].fillna(5)
    df['visceral_score'] = df['visceral_score'].fillna(5)
    df['neuropathic_score'] = df['neuropathic_score'].fillna(2) # Default neuropathic is lower

    def calculate_adjuvant_profile(row):
        somatic_scores, visceral_scores, neuropathic_scores = [], [], []

        # Helper to add drug scores
        def add_scores(drug):
            if drug:
                somatic_scores.append(drug['somatic_score'])
                visceral_scores.append(drug['visceral_score'])
                neuropathic_scores.append(drug['neuropathic_score'])

        # NSAID
        nsaid_choice = row.get('nsaid_choice', 'Ej given')
        if row.get('nsaid') and nsaid_choice != 'Ej given':
            add_scores(get_drug_by_ui_choice('nsaid', nsaid_choice))

        # Catapressan
        if row.get('catapressan') or row.get('catapressan_dose', 0) > 0:
            add_scores(LÄKEMEDELS_DATA.get('clonidine'))

        # Droperidol
        if row.get('droperidol'):
            add_scores(LÄKEMEDELS_DATA.get('droperidol'))

        # Ketamine
        ketamine_choice = row.get('ketamine_choice', 'Ej given')
        if row.get('ketamine') and row['ketamine'] != 'Nej' and ketamine_choice != 'Ej given':
            add_scores(get_drug_by_ui_choice('ketamine', ketamine_choice))

        # Lidocaine
        lidocaine_choice = row.get('lidocaine', 'Nej')
        if lidocaine_choice != 'Nej':
            add_scores(get_drug_by_ui_choice('lidocaine', lidocaine_choice))

        # Betapred
        betapred_choice = row.get('betapred', 'Nej')
        if betapred_choice != 'Nej':
            add_scores(get_drug_by_ui_choice('betapred', betapred_choice))

        # Calculate average adjuvant profile
        row['avg_adjuvant_somatic'] = np.mean(somatic_scores) if somatic_scores else 5
        row['avg_adjuvant_visceral'] = np.mean(visceral_scores) if visceral_scores else 5
        row['avg_adjuvant_neuropathic'] = np.mean(neuropathic_scores) if neuropathic_scores else 2

        # 3D Mismatch (Euclidean distance)
        distance = math.sqrt(
            (row['somatic_score'] - row['avg_adjuvant_somatic'])**2 +
            (row['visceral_score'] - row['avg_adjuvant_visceral'])**2 +
            (row['neuropathic_score'] - row['avg_adjuvant_neuropathic'])**2
        )
        row['pain_mismatch_3d'] = distance

        # Legacy 1D features for backwards compatibility
        row['painTypeScore'] = row['somatic_score']
        row['avgAdjuvantSelectivity'] = row['avg_adjuvant_somatic']
        row['painTypeMismatch'] = abs(row['painTypeScore'] - row['avgAdjuvantSelectivity'])

        return row

    df = df.apply(calculate_adjuvant_profile, axis=1)
    
    # Note: The temporal features logic from ml_model.py depends on a 'pharmacokinetics.py' file
    # which is not present. This logic should also be moved here once that file is available.
    
    return df
