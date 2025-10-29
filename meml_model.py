"""
Mixed-Effects Machine Learning (MEML) Model using GPBoost

This module implements a hierarchical machine learning model that accounts for
the clustered structure of clinical data (patients nested within procedures).

Key Features:
- Fixed effects: Global patient/procedure relationships (age, pain, etc.)
- Random effects: Procedure-specific intercepts (baseline opioid requirement)
- Borrows statistical strength across procedures
- Robust predictions even for rare procedures

Architecture:
GPBoost = Gradient Boosting (fixed effects) + Gaussian Process (random effects)
"""

import logging
import pickle
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import gpboost, provide helpful message if not available
try:
    import gpboost as gpb
    GPBOOST_AVAILABLE = True
except ImportError:
    logger.warning(
        "GPBoost not installed. Install with: pip install gpboost\n"
        "MEML functionality will not be available until installed."
    )
    GPBOOST_AVAILABLE = False


# Model save path
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)
MODEL_PATH = MODEL_DIR / "meml_oxycodone_dose.txt"
FEATURE_NAMES_PATH = MODEL_DIR / "meml_feature_names.pkl"


def prepare_training_data(include_pk_features: bool = True) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Extract and engineer features from database for ML training.

    Args:
        include_pk_features: Whether to include PK-derived features

    Returns:
        Tuple of (X, y, group):
        - X: Feature matrix (n_samples, n_features)
        - y: Target variable (actual dose in mg)
        - group: Cluster IDs (procedure_id)

    Features engineered:
    1. Patient: age, weight, height, sex, LBM
    2. PK (optional): clearance, Vd, half-life
    3. Physiology: GFR, hepatic status, opioid tolerance
    4. Procedure: pain scores (3D), duration
    5. Adjuvants: binary flags for each type
    """
    import database as db
    from calculation_engine import calculate_lean_body_mass

    if include_pk_features:
        import pk_model

    # Get all cases with complete outcome data
    logger.info("Fetching training data from database...")

    # This is a placeholder - in production, implement db.get_all_cases_with_outcomes()
    # For now, return empty data with correct structure
    logger.warning("No training data available yet - database needs cases with outcomes")

    # Create empty dataframe with correct column structure
    feature_columns = [
        'age', 'weight', 'height', 'sex_binary',  # Demographics
        'lbm_kg',  # Body composition
        'gfr', 'hepatic_impairment_binary',  # Physiology
        'opioid_tolerance_binary',  # Tolerance
        'pain_somatic', 'pain_visceral', 'pain_neuropathic',  # Procedure pain
        'nsaid', 'ketamine', 'catapressan', 'droperidol',  # Adjuvants
        'lidocaine', 'betapred'
    ]

    if include_pk_features:
        feature_columns.extend(['pk_clearance', 'pk_vd', 'pk_half_life'])

    X = pd.DataFrame(columns=feature_columns)
    y = pd.Series(dtype=float, name='actual_dose_mg')
    group = pd.Series(dtype=str, name='procedure_id')

    return X, y, group


def train_meml_model(
    X: pd.DataFrame,
    y: pd.Series,
    group: pd.Series,
    params: Optional[Dict] = None
) -> Optional[object]:
    """
    Train Mixed-Effects Machine Learning model using GPBoost.

    Args:
        X: Feature matrix
        y: Target variable (dose in mg)
        group: Cluster IDs (procedure_id)
        params: Optional hyperparameters dict

    Returns:
        Trained GPBoost model (or None if GPBoost not available)

    Model Structure:
    - Fixed effects (gradient boosting): Learns global relationships
    - Random effects (Gaussian process): Learns procedure-specific offsets
    """
    if not GPBOOST_AVAILABLE:
        logger.error("GPBoost not installed - cannot train MEML model")
        return None

    if len(X) < 50:
        logger.warning(
            f"Only {len(X)} training samples - recommend at least 50 for stable training"
        )
        return None

    logger.info(f"Training MEML model on {len(X)} samples...")

    # Default hyperparameters
    if params is None:
        params = {
            'objective': 'regression',  # Predicting continuous dose
            'metric': 'rmse',
            'learning_rate': 0.05,
            'num_leaves': 31,
            'max_depth': 5,
            'min_data_in_leaf': 10,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 1,
            'verbose': -1
        }

    # Split data (80/20 train/validation)
    from sklearn.model_selection import train_test_split

    X_train, X_val, y_train, y_val, group_train, group_val = train_test_split(
        X, y, group, test_size=0.2, random_state=42
    )

    logger.info(f"Training set: {len(X_train)} samples, Validation set: {len(X_val)} samples")

    # Define random effects model (Gaussian process over procedure groups)
    gp_model = gpb.GPModel(group_data=group_train, likelihood="gaussian")

    # Prepare training data for GPBoost
    data_train = gpb.Dataset(X_train, y_train)

    # Train model
    logger.info("Starting GPBoost training...")
    bst = gpb.train(
        params=params,
        train_set=data_train,
        gp_model=gp_model,
        num_boost_round=200,
        valid_sets=[gpb.Dataset(X_val, y_val)],
        early_stopping_rounds=20,
        verbose_eval=False
    )

    # Evaluate on validation set
    y_pred = bst.predict(X_val, group_data_pred=group_val)

    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

    rmse = np.sqrt(mean_squared_error(y_val, y_pred['response_mean']))
    mae = mean_absolute_error(y_val, y_pred['response_mean'])
    r2 = r2_score(y_val, y_pred['response_mean'])

    logger.info(f"Validation metrics: RMSE={rmse:.2f}mg, MAE={mae:.2f}mg, R²={r2:.3f}")

    # Save model
    bst.save_model(str(MODEL_PATH))

    # Save feature names for future use
    with open(FEATURE_NAMES_PATH, 'wb') as f:
        pickle.dump(list(X.columns), f)

    logger.info(f"Model saved to {MODEL_PATH}")

    return bst


def predict_optimal_dose_meml(
    patient_inputs: Dict,
    procedure_data: Dict,
    model_path: Optional[str] = None
) -> Tuple[float, float, List[Tuple[float, float]]]:
    """
    Use trained MEML model to predict optimal dose.

    Strategy:
    1. Test multiple candidate doses (3mg to 15mg)
    2. For each dose, predict probability of success
    3. Choose dose with highest P(success)

    Args:
        patient_inputs: Patient characteristics
        procedure_data: Procedure information
        model_path: Path to saved model (default: MODEL_PATH)

    Returns:
        Tuple of (optimal_dose, confidence, dose_response_curve)
        - optimal_dose: Recommended dose in mg
        - confidence: Predicted probability of success
        - dose_response_curve: List of (dose, P(success)) pairs
    """
    if not GPBOOST_AVAILABLE:
        logger.error("GPBoost not installed")
        return 7.5, 0.5, []  # Fallback to default

    if model_path is None:
        model_path = MODEL_PATH

    if not Path(model_path).exists():
        logger.error(f"No trained model found at {model_path}")
        return 7.5, 0.5, []

    # Load model
    bst = gpb.Booster(model_file=str(model_path))

    # Load feature names
    with open(FEATURE_NAMES_PATH, 'rb') as f:
        feature_names = pickle.load(f)

    # Engineer features for this patient
    features_dict = engineer_features(patient_inputs, procedure_data)

    # Ensure correct feature order
    features = pd.DataFrame([features_dict])[feature_names]

    # Predict for this specific feature set
    procedure_id = patient_inputs.get('procedure_id', 'UNKNOWN')

    pred = bst.predict(features, group_data_pred=[procedure_id], predict_var=True)

    optimal_dose = pred['response_mean'][0]
    confidence = 1.0 / (1.0 + pred['response_var'][0])  # Higher variance → lower confidence

    # Generate dose-response curve (for visualization)
    dose_response = [(optimal_dose, confidence)]

    logger.info(
        f"MEML prediction: {optimal_dose:.1f}mg "
        f"(confidence: {confidence:.2f}) for {procedure_id}"
    )

    return optimal_dose, confidence, dose_response


def engineer_features(patient_inputs: Dict, procedure_data: Dict) -> Dict:
    """
    Convert raw patient/procedure data into ML features.

    Args:
        patient_inputs: Patient characteristics
        procedure_data: Procedure information

    Returns:
        Dictionary of engineered features
    """
    from calculation_engine import calculate_lean_body_mass
    import pk_model

    # Basic demographics
    age = patient_inputs.get('age', 50)
    weight = patient_inputs.get('weight', 75)
    height = patient_inputs.get('height', 175)
    sex = patient_inputs.get('sex', 'Man')
    sex_binary = 1 if sex == 'Man' else 0

    # Body composition
    lbm = calculate_lean_body_mass(weight, height, sex)

    # Physiology
    gfr = patient_inputs.get('gfr', 90)
    hepatic = patient_inputs.get('hepatic_impairment', 'None')
    hepatic_binary = 1 if hepatic.lower() in ['moderate', 'severe'] else 0
    opioid_tolerance = 1 if patient_inputs.get('opioid_tolerance', False) else 0

    # Procedure pain (3D)
    pain_somatic = procedure_data.get('painTypeScore', 5)
    pain_visceral = procedure_data.get('painVisceral', 5)
    pain_neuropathic = procedure_data.get('painNeuropathic', 2)

    # Adjuvants
    nsaid = 1 if patient_inputs.get('nsaid', False) else 0
    ketamine = 1 if patient_inputs.get('ketamine_choice', 'Ej given') != 'Ej given' else 0
    catapressan = 1 if patient_inputs.get('catapressan', False) else 0
    droperidol = 1 if patient_inputs.get('droperidol', False) else 0
    lidocaine = 1 if patient_inputs.get('lidocaine', 'Nej') != 'Nej' else 0
    betapred = 1 if patient_inputs.get('betapred', 'Nej') != 'Nej' else 0

    # PK parameters
    pk_params = pk_model.get_pk_summary(
        age, weight, height, sex,
        gfr if gfr < 90 else None,
        hepatic
    )

    return {
        'age': age,
        'weight': weight,
        'height': height,
        'sex_binary': sex_binary,
        'lbm_kg': lbm,
        'gfr': gfr,
        'hepatic_impairment_binary': hepatic_binary,
        'opioid_tolerance_binary': opioid_tolerance,
        'pain_somatic': pain_somatic,
        'pain_visceral': pain_visceral,
        'pain_neuropathic': pain_neuropathic,
        'nsaid': nsaid,
        'ketamine': ketamine,
        'catapressan': catapressan,
        'droperidol': droperidol,
        'lidocaine': lidocaine,
        'betapred': betapred,
        'pk_clearance': pk_params['clearance_L_per_h'],
        'pk_vd': pk_params['vd_L'],
        'pk_half_life': pk_params['half_life_h']
    }


if __name__ == "__main__":
    print("=== MEML Model Module ===\n")

    if not GPBOOST_AVAILABLE:
        print("GPBoost is not installed. Install with:")
        print("  pip install gpboost")
        print("\nThis module requires GPBoost for hierarchical modeling.")
    else:
        print("GPBoost is available!")
        print(f"GPBoost version: {gpb.__version__}")

    # Test data preparation
    print("\nTesting data preparation...")
    X, y, group = prepare_training_data(include_pk_features=True)
    print(f"  Features: {list(X.columns)}")
    print(f"  Samples: {len(X)} (empty - needs real case data)")

    if len(X) > 0:
        print("\nTesting model training...")
        model = train_meml_model(X, y, group)

        if model:
            print("  Model trained successfully!")
            print(f"  Model saved to: {MODEL_PATH}")
        else:
            print("  Training failed (insufficient data)")
    else:
        print("\nSkipping training - no data available")
        print("Add cases with outcomes to database to enable training")

    print("\n" + "="*60)
    print("MEML Module Status: Ready (waiting for training data)")
