
import streamlit as st
import pandas as pd
import xgboost as xgb
import numpy as np
from config import APP_CONFIG
from feature_engineering import add_engineered_features
import database as db
import joblib
import os

MODEL_PATH = 'xgboost_model.joblib'

def predict_with_xgboost(current_patient_inputs, procedures_df):
    """
    Predicts the best dose using a pre-trained XGBoost model.
    Uses the centralized feature_engineering module.
    """
    TARGET_VAS = db.get_setting('ML_TARGET_VAS', APP_CONFIG.get('ML_TARGET_VAS', 1.0)) if hasattr(db, 'get_setting') else APP_CONFIG.get('ML_TARGET_VAS', 1.0)

    # 1. Load the pre-trained model
    if not os.path.exists(MODEL_PATH):
        st.error("ML-modellfilen (xgboost_model.joblib) hittades inte. Kör train_model.py för att skapa den.")
        return {'finalDose': 0.0, 'engine': "ML-Modell ej tränad"}

    try:
        model_and_features = joblib.load(MODEL_PATH)
        model = model_and_features['model']
        trained_features = model_and_features['features']
    except Exception as e:
        st.error(f"Kunde inte ladda ML-modellen: {e}")
        return {'finalDose': 0.0, 'engine': "ML-Laddningsfel"}

    try:
        # 2. Feature Engineering for the new input
        predict_df = pd.DataFrame([current_patient_inputs])
        predict_df['asa'] = predict_df['asa'].astype(str)
        
        # Use the centralized feature engineering function
        predict_df = add_engineered_features(predict_df, procedures_df)

        # One-hot encode and align columns
        encode_cols = ['specialty', 'opioidHistory', 'asa', 'nsaid_choice', 'ketamine_choice',
                      'lidocaine', 'betapred', 'sex', 'surgery_type']
        predict_encoded = pd.get_dummies(predict_df, columns=encode_cols, drop_first=True)

        predict_aligned = pd.DataFrame(columns=trained_features)
        for col in trained_features:
            if col in predict_encoded.columns:
                predict_aligned[col] = predict_encoded[col]
            else:
                predict_aligned[col] = 0
        predict_aligned = predict_aligned.astype(float)

        # 3. Make predictions by iterating through test doses
        predictions = {}
        # Ensure 'givenDose' is in the aligned dataframe before starting the loop
        if 'givenDose' not in predict_aligned.columns:
             st.error("'givenDose' saknas i modellens features. Träna om modellen.")
             return {'finalDose': 0.0, 'engine': "ML-Featurefel"}

        for test_dose in np.arange(0, 20.5, 0.5):
            predict_row = predict_aligned.copy()
            predict_row['givenDose'] = test_dose
            
            # Ensure column order is the same as in training
            predict_row = predict_row[trained_features]

            predicted_vas = model.predict(predict_row)[0]
            predictions[test_dose] = predicted_vas

        best_dose = min(predictions, key=lambda k: abs(predictions[k] - TARGET_VAS))

        # Apply safety limits from config
        min_dose = APP_CONFIG.get('ML_SAFETY_MIN_DOSE', 0.0)
        max_dose = APP_CONFIG.get('ML_SAFETY_MAX_DOSE', 20.0)
        final_dose = max(min_dose, min(best_dose, max_dose))
        final_dose = round(final_dose / 0.25) * 0.25 # Round to nearest 0.25

        # Extract feature importance
        feature_importance = None
        if hasattr(model, 'feature_importances_'):
            importance_scores = model.feature_importances_
            feature_importance = pd.DataFrame({
                'feature': trained_features,
                'importance': importance_scores
            }).sort_values('importance', ascending=False)

        return {
            'finalDose': final_dose,
            'engine': f"XGBoost (Pre-trained)",
            'feature_importance': feature_importance,
            'raw_ml_dose': best_dose,
            'safety_limits_applied': (best_dose != final_dose)
        }

    except Exception as e:
        st.error(f"Ett fel uppstod i ML-motorn: {e}")
        return {'finalDose': 0.0, 'engine': "ML-Fel"}
