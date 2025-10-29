
import pandas as pd
import xgboost as xgb
import numpy as np
import database as db
from feature_engineering import add_engineered_features
import joblib

def train_and_save_model():
    """
    This script loads all data, trains the XGBoost model, and saves it to a file.
    """
    print("Starting model training...")

    # 1. Load data
    print("Loading data from database...")
    all_cases = db.get_all_cases(user_id=None)
    if not all_cases:
        print("No cases found in the database. Aborting training.")
        return

    cases_df = pd.DataFrame(all_cases)
    all_procedures = db.get_all_procedures() + db.get_all_custom_procedures()
    procedures_df = pd.DataFrame(all_procedures)
    print(f"Loaded {len(cases_df)} cases and {len(procedures_df)} procedures.")

    # 2. Feature Engineering using the centralized function
    print("Performing feature engineering...")
    cases_df['asa'] = cases_df['asa'].astype(str)
    cases_df = add_engineered_features(cases_df, procedures_df)

    # One-hot encode categorical variables
    encode_cols = ['specialty', 'opioidHistory', 'asa', 'nsaid_choice', 'ketamine_choice',
                    'lidocaine', 'betapred', 'sex', 'surgery_type']
    cases_encoded = pd.get_dummies(cases_df, columns=encode_cols, drop_first=True)

    # Define target and features. CRITICAL: 'givenDose' is now a feature.
    y_train = cases_encoded['vas']
    
    exclude_cols = [
        # Target and outcome variables
        'vas', 'uvaDose', 'postop_reason', 'respiratory_status', 'severe_fatigue', 
        'rescue_early', 'rescue_late',
        # Identifiers and metadata
        'id', 'user_id', 'procedure_id', 'timestamp', 'last_modified', 'last_modified_by',
        'compositeKey', 'engine', 'calculation', 'procedure_name', 'created_by',
        # Redundant or raw data
        'outcome', 'raw_input', 'edit_history'
    ]
    
    features = [col for col in cases_encoded.columns if col not in exclude_cols]
    X_train = cases_encoded[features]

    # Handle outliers
    outlier_mask = (cases_encoded['vas'] > 8) | (cases_encoded['uvaDose'] > 15)
    sample_weights = np.where(outlier_mask, 0.5, 1.0)

    # 3. Train the XGBoost model
    print("Training XGBoost model...")
    num_cases = len(cases_df)
    if num_cases < 10:
        xgb_learning_rate = 0.15
        xgb_n_estimators = 50
    elif num_cases < 30:
        xgb_learning_rate = 0.10
        xgb_n_estimators = 75
    else:
        xgb_learning_rate = 0.05
        xgb_n_estimators = 100

    best_max_depth = 3 # Default value
    if num_cases >= 30:
        from sklearn.model_selection import cross_val_score
        best_score = -np.inf

        print("Optimizing hyperparameters...")
        for max_depth in [2, 3, 4, 5]:
            temp_model = xgb.XGBRegressor(
                objective='reg:squarederror',
                n_estimators=xgb_n_estimators,
                learning_rate=xgb_learning_rate,
                max_depth=max_depth,
                random_state=42,
                subsample=0.8,
                colsample_bytree=0.8
            )
            # Ensure there are enough samples for CV
            n_splits = min(5, num_cases // 6 if num_cases // 6 > 1 else 2)
            if n_splits > 1:
                cv_scores = cross_val_score(temp_model, X_train, y_train, cv=n_splits,
                                            scoring='neg_mean_squared_error')
                mean_score = cv_scores.mean()
                if mean_score > best_score:
                    best_score = mean_score
                    best_max_depth = max_depth
        print(f"Best max_depth found: {best_max_depth}")

    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=xgb_n_estimators,
        learning_rate=xgb_learning_rate,
        max_depth=best_max_depth,
        random_state=42,
        subsample=0.8,
        colsample_bytree=0.8
    )
    model.fit(X_train, y_train, sample_weight=sample_weights)
    print("Model training complete.")

    # 4. Save the model and features
    print("Saving model and features to file...")
    model_and_features = {
        'model': model,
        'features': X_train.columns.tolist()
    }
    joblib.dump(model_and_features, 'xgboost_model.joblib')
    print("Model saved successfully to xgboost_model.joblib")

if __name__ == "__main__":
    db.init_database()
    train_and_save_model()
