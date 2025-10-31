# Anestesidoseringshjälp Alfa V0.8 - Codebase Analysis

This document provides a detailed analysis of the Anestesidoseringshjälp Alfa V0.8 codebase. It covers the application's architecture, data flow, calculation engine, learning system, and postoperative analysis.

## 1. High-Level Architecture

The application consists of two main parts:

1.  **Streamlit Frontend (`oxydoseks.py`):** A comprehensive graphical user interface for anesthesiologists to input patient and procedure data, receive dose recommendations, and log postoperative outcomes.
2.  **FastAPI Backend (`main.py`):** An API backend that exposes some of the application's functionality. It seems to be designed for a different frontend (likely a web application) and is not directly used by the Streamlit application.

The core logic is encapsulated in a set of Python modules, including:

*   `calculation_engine.py`: The rule-based engine for dose calculation.
*   `learning_engine.py`: The back-calculation learning system.
*   `database.py`: The SQLite database for data persistence.
*   `config.py`: The central configuration file for all pharmacological data and application settings.
*   `ui/`: A directory containing the different tabs of the Streamlit UI.

## 2. Input to Output Flow: A Complete Walkthrough

The primary user workflow is centered around the "Dosering & Dosrekommendation" (Dosing & Recommendation) tab in the Streamlit application. Here's a step-by-step walkthrough of the data flow:

### 2.1. User Inputs

The user provides a comprehensive set of inputs, categorized as follows:

**Patient Data:**
*   **Age:** 0-120 years.
*   **Sex:** "Man" or "Kvinna".
*   **Weight:** 0-300 kg.
*   **Height:** 0-250 cm.
*   **ASA Class:** ASA 1 to 5.
*   **Opioid History:** "Naiv" or "Tolerant".
*   **Low Pain Threshold:** Checkbox.
*   **Renal Impairment (GFR < 35):** Checkbox.

**Procedure Data:**
*   **Specialty:** Dropdown list of medical specialties.
*   **Procedure:** Dropdown list of procedures, filtered by the selected specialty.
*   **Surgery Type:** "Elektivt" (Elective) or "Akut" (Emergency).

**Temporal Dosing:**
*   A list of opioid doses (Fentanyl, Oxycodone, Morphine) given at specific times relative to the end of the surgery.

**Adjuvants:**
*   A selection of adjuvants, including NSAIDs, Paracetamol, Catapressan, Betapred, Ketamine, Lidocaine, Droperidol, Infiltration, and Sevoflurane.

### 2.2. Calculation Trigger

The user clicks the "Beräkna Rekommendation" (Calculate Recommendation) button, which triggers the `calculate_rule_based_dose` function in `calculation_engine.py`.

### 2.3. The Calculation Engine

The `calculation_engine.py` module performs a multi-step calculation to determine the recommended dose. This is a purely rule-based system, but with a sophisticated learning layer on top.

**Step 1: Initial MME and Pain Profile**
*   The system retrieves the `baseMME` (base Morphine Milligram Equivalents) and the 3D pain profile (somatic, visceral, neuropathic) for the selected procedure from the database.
*   **Learning:** It checks for learned adjustments to the `baseMME` and pain profile for this procedure and applies them.

**Step 2: Patient Factor Adjustments**
*   The MME is adjusted based on patient factors:
    *   **Age:** An age factor is calculated, with a steeper reduction for elderly patients.
    *   **ASA Class:** The MME is adjusted based on the patient's ASA class.
    *   **Sex:** A sex-specific factor is applied.
    *   **4D Body Composition:** A complex 4D body composition model is used, considering weight, IBW ratio, ABW ratio, and BMI.
    *   **Opioid Tolerance:** The MME is increased for opioid-tolerant patients.
    *   **Pain Threshold:** The MME is increased for patients with a low pain threshold.
    *   **Renal Impairment:** The MME is reduced for patients with renal impairment.
*   **Learning:** Each of these factors can be adjusted by the learning system based on previous outcomes.

**Step 3: Adjuvant Reductions**
*   The MME is reduced based on the selected adjuvants.
*   Each adjuvant has a `potency_percent` that determines the percentage of opioid reduction it provides.
*   The effectiveness of each adjuvant is also adjusted based on a `3D mismatch penalty`, which compares the adjuvant's pain profile to the procedure's pain profile.
*   **Learning:** The `potency_percent` of each adjuvant is a learned value that is adjusted over time.

**Step 4: Synergy and Safety**
*   A synergy factor is applied for certain drug combinations.
*   A safety limit prevents the total MME reduction from exceeding a certain percentage.

**Step 5: Pharmacokinetics**
*   The system accounts for the remaining effect of Fentanyl given during the procedure using a pharmacokinetic model.

**Step 6: Final Adjustments**
*   A final weight adjustment is applied based on the adjusted body weight (ABW).
*   If temporal dosing information is provided, the MME is further adjusted based on the pharmacokinetic models of the given opioids and adjuvants.
*   A user-specific calibration factor is applied.

### 2.4. Machine Learning Integration

*   If there are enough historical cases for the selected procedure (default threshold: 15), the system also runs a prediction with an XGBoost model (`predict_with_xgboost` in `ml_model.py`).
*   The final recommendation is an ensemble of the rule-based dose and the ML-based dose, with the weight of the ML model increasing as more data becomes available.

### 2.5. Output and Display

The final recommended dose is displayed to the user, along with:
*   The engine used for the calculation (Rule-based, XGBoost, or Ensemble).
*   A confidence score based on the number of historical cases.
*   Warnings for high-risk patients (e.g., high BMI, elderly).
*   Feature importance from the ML model, if applicable.

## 3. The Postoperative System and Learning Loop

The application's ability to learn and improve is one of its most powerful features. This is driven by the postoperative data logged by the user.

### 3.1. Logging Postoperative Data

After a case is completed, the user can log the following postoperative data:
*   **VAS Score:** The patient's highest pain score in the first hour.
*   **Rescue Doses:** Any extra opioid doses given in the first hour.
*   **Respiratory Status:** The patient's level of consciousness.
*   **Other Outcomes:** Severe fatigue, reason for post-op time, etc.

### 3.2. The Learning Engine

The `learning_engine.py` module is responsible for processing this outcome data and updating the system's parameters.

**Step 1: Calculate Actual Requirement**
*   The `calculate_actual_requirement` function determines what the opioid requirement *should have been* based on the outcome data. For example, if the patient had a high VAS score and required rescue doses, the actual requirement is calculated to be higher than what was given.

**Step 2: Back-Calculation**
*   The learning engine then back-calculates the adjustments needed to the various parameters (baseMME, patient factors, adjuvant potency, etc.) to have predicted this `actual_requirement`.

**Step 3: Update Learned Values**
*   The learned adjustments are then saved to the `learning_*` tables in the database.
*   The learning process is gradual, with a learning rate that decreases as the system gains more experience.

This continuous feedback loop allows the system to adapt to new evidence and improve its recommendations over time. The move to global learning for many parameters means that every user contributes to the collective knowledge of the system.

## 4. Detailed System Components

### 4.1. User Interface (`ui/`)

The user interface is built with Streamlit and is organized into a set of tabs, each with a specific purpose:

*   **`dosing_tab.py`**: The main interface for dose calculation. It collects all patient, procedure, and adjuvant data.
*   **`history_tab.py`**: Displays a detailed history of all saved cases, with options for filtering, editing, and deleting. It also provides an Excel export feature.
*   **`learning_tab.py`**: Provides insights into the learning system, including the status of the ML model, learned adjustment factors, and various statistics.
*   **`procedures_tab.py`**: Allows users to add and manage their own custom surgical procedures.
*   **`admin_tab.py`**: An admin-only section for user management and system settings.

### 4.2. Calculation Engine (`calculation_engine.py`)

This module is the heart of the rule-based dosing system. It calculates the recommended dose through a multi-step process:

1.  **Initial MME and Pain Profile:** Retrieves the base MME and 3D pain profile for the selected procedure.
2.  **Patient Factor Adjustments:** Adjusts the MME based on age, ASA class, sex, body composition, opioid tolerance, pain threshold, and renal impairment.
3.  **Adjuvant Reductions:** Reduces the MME based on the selected adjuvants, considering their potency and 3D pain profile.
4.  **Synergy and Safety:** Applies synergy factors for drug combinations and enforces safety limits.
5.  **Pharmacokinetics:** Accounts for the remaining effect of Fentanyl.
6.  **Final Adjustments:** Applies a final weight adjustment and a user-specific calibration factor.

### 4.3. Learning Engine (`learning_engine.py`)

This module implements the back-calculation learning system. It learns from the actual outcomes of the anesthesia to improve future recommendations.

*   **`calculate_actual_requirement()`**: Determines the "ground truth" for learning by calculating what the opioid requirement *should have been* based on the outcome data.
*   **`learn_procedure_requirements()`**: Adjusts the base MME for a procedure.
*   **`learn_patient_factors()`**: Adjusts the factors for patient characteristics.
*   **`learn_adjuvant_percentage()`**: Adjusts the potency of adjuvants.
*   **`learn_procedure_3d_pain()`**: Adjusts the 3D pain profile of a procedure.

### 4.4. Database (`database.py`)

The SQLite database stores all the application's data, including:

*   User accounts and sessions.
*   Standard and custom procedures.
*   All case data, including patient inputs, dose recommendations, and postoperative outcomes.
*   All learned parameters for the rule-based engine.

### 4.5. Configuration (`config.py`)

This file is the central source of truth for all pharmacological data and application settings. It contains:

*   **`APP_CONFIG`**: A dictionary of application-level settings.
*   **`LÄKEMEDELS_DATA`**: A dictionary containing all the pharmacological data for the drugs used in the application.

### 4.6. Machine Learning (`ml_model.py`, `meml_model.py`, `train_model.py`)

The application includes two machine learning models:

*   **XGBoost Model (`ml_model.py`):** A pre-trained XGBoost model that can be used to predict the optimal dose. The model is trained using the `train_model.py` script.
*   **Mixed-Effects Model (`meml_model.py`):** A more advanced GPBoost model that is still under development. It is designed to handle the clustered structure of the data.

### 4.7. Authentication and Authorization (`auth.py`)

This module handles user authentication and authorization. It uses `bcrypt` for password hashing and Streamlit's `session_state` for session management.

### 4.8. Pharmacokinetics (`pharmacokinetics.py`, `pk_model.py`)

These modules implement the pharmacokinetic models used in the application.

*   **`pharmacokinetics.py`**: Provides functions to calculate the remaining effect of drugs over time, which is used in the temporal dosing feature.
*   **`pk_model.py`**: Implements a population PK model for oxycodone, which is used to calculate patient-specific PK parameters.

### 4.9. Validation (`validation.py`)

This module provides functions for validating user inputs, recommended doses, and outcome data. It helps to ensure data quality and patient safety.

### 4.10. Migrations (`migrations.py`)

This module manages the database schema and migrations. It ensures that the database schema is always up-to-date with the latest code changes.

## 5. Conclusion

The Anestesidoseringshjälp Alfa V0.8 is a sophisticated and well-architected application that combines a rule-based expert system with a powerful machine learning component. The use of a central configuration file for all pharmacological data, a dedicated learning engine, and a comprehensive database schema makes the system robust, maintainable, and adaptive. The continuous learning loop, driven by postoperative outcome data, is a key feature that allows the system to improve its recommendations over time.
