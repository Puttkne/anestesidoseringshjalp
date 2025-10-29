"""
Unit Tests for Input Validation
================================
Tests for patient data validation and dose safety checks.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from validation import (
    validate_patient_inputs,
    validate_recommended_dose,
    validate_outcome_data,
    validate_drug_contraindications
)


class TestPatientInputValidation:
    """Test patient input validation."""

    def test_valid_patient_data(self):
        """Test that valid patient data passes validation."""
        inputs = {
            'age': 45,
            'weight': 75,
            'height': 175,
            'bmi': 24.5,
            'sex': 'Man',
            'asa': 'ASA 2',
            'procedure_id': 'test_proc',
            'fentanylDose': 100,
            'optime_minutes': 120
        }
        is_valid, errors = validate_patient_inputs(inputs)
        assert is_valid
        assert len(errors) == 0

    def test_invalid_age(self):
        """Test that invalid age fails validation."""
        inputs = {
            'age': 150,  # Too old
            'weight': 75,
            'height': 175,
            'sex': 'Man',
            'asa': 'ASA 2',
            'procedure_id': 'test_proc'
        }
        is_valid, errors = validate_patient_inputs(inputs)
        assert not is_valid
        assert any('ålder' in err.lower() for err in errors)

    def test_invalid_weight(self):
        """Test that invalid weight fails validation."""
        inputs = {
            'age': 45,
            'weight': 0,  # Zero weight
            'height': 175,
            'sex': 'Man',
            'asa': 'ASA 2',
            'procedure_id': 'test_proc'
        }
        is_valid, errors = validate_patient_inputs(inputs)
        assert not is_valid
        assert any('vikt' in err.lower() for err in errors)

    def test_missing_required_fields(self):
        """Test that missing required fields fail validation."""
        inputs = {
            'age': 45,
            'weight': 75,
            'height': 175
            # Missing sex, asa, procedure_id
        }
        is_valid, errors = validate_patient_inputs(inputs)
        assert not is_valid
        assert len(errors) >= 3

    def test_negative_fentanyl_dose(self):
        """Test that negative fentanyl dose fails validation."""
        inputs = {
            'age': 45,
            'weight': 75,
            'height': 175,
            'sex': 'Man',
            'asa': 'ASA 2',
            'procedure_id': 'test_proc',
            'fentanylDose': -100,  # Negative dose
            'optime_minutes': 120
        }
        is_valid, errors = validate_patient_inputs(inputs)
        assert not is_valid
        assert any('fentanyl' in err.lower() for err in errors)


class TestRecommendedDoseValidation:
    """Test recommended dose validation (perioperative)."""

    def test_safe_recommended_dose(self):
        """Test that recommended dose ≤10mg passes without warning."""
        is_safe, severity, msg = validate_recommended_dose(8.0)
        assert is_safe
        assert severity == 'OK'

    def test_recommended_dose_at_threshold(self):
        """Test that dose exactly at 10mg passes without warning."""
        is_safe, severity, msg = validate_recommended_dose(10.0)
        assert is_safe
        assert severity == 'OK'

    def test_high_recommended_dose(self):
        """Test that recommended dose >10mg triggers warning."""
        is_safe, severity, msg = validate_recommended_dose(11.5)
        assert is_safe  # Still allows it
        assert severity == 'WARNING'
        assert 'HÖG REKOMMENDERAD DOS' in msg
        assert '10' in msg  # Should mention threshold

    def test_very_high_recommended_dose(self):
        """Test that very high recommended dose (>15mg) triggers warning."""
        is_safe, severity, msg = validate_recommended_dose(16.0)
        assert is_safe  # Still allows it
        assert severity == 'WARNING'
        assert 'REKOMMENDERAD DOS' in msg


class TestOutcomeDataValidation:
    """Test outcome data validation."""

    def test_valid_outcome_data(self):
        """Test that valid outcome data passes."""
        outcome = {
            'givenDose': 8.0,
            'vas': 3,
            'uvaDose': 2.0,
            'postop_minutes': 120
        }
        is_valid, errors = validate_outcome_data(outcome)
        assert is_valid
        assert len(errors) == 0

    def test_invalid_vas(self):
        """Test that invalid VAS fails validation."""
        outcome = {
            'givenDose': 8.0,
            'vas': 15,  # Too high
            'uvaDose': 0,
            'postop_minutes': 120
        }
        is_valid, errors = validate_outcome_data(outcome)
        assert not is_valid
        assert any('vas' in err.lower() for err in errors)

    def test_zero_given_dose(self):
        """Test that zero given dose fails validation."""
        outcome = {
            'givenDose': 0,  # Invalid
            'vas': 3,
            'uvaDose': 0,
            'postop_minutes': 120
        }
        is_valid, errors = validate_outcome_data(outcome)
        assert not is_valid

    def test_high_total_dose_allowed(self):
        """Test that high total dose (PACU) is allowed without warning."""
        outcome = {
            'givenDose': 12.0,
            'vas': 5,
            'uvaDose': 10.0,  # Total = 22mg - high but allowed for PACU
            'postop_minutes': 120
        }
        is_valid, errors = validate_outcome_data(outcome)
        assert is_valid  # Should be valid
        assert len(errors) == 0  # No errors - PACU can require high doses


class TestContraindications:
    """Test drug contraindication warnings."""

    def test_nsaid_with_renal_impairment(self):
        """Test that NSAID + renal impairment triggers warning."""
        inputs = {
            'renalImpairment': True,
            'nsaid_choice': 'Ketorolac 30mg',
            'age': 45,
            'opioidHistory': 'Opioidnaiv'
        }
        warnings = validate_drug_contraindications(inputs)
        assert len(warnings) > 0
        assert any('KONTRAINDIKATION' in w for w in warnings)

    def test_elderly_opioid_naive(self):
        """Test that elderly opioid-naive patient triggers warning."""
        inputs = {
            'renalImpairment': False,
            'nsaid_choice': 'Ej given',
            'age': 85,
            'opioidHistory': 'Opioidnaiv'
        }
        warnings = validate_drug_contraindications(inputs)
        assert len(warnings) > 0
        assert any('80' in w for w in warnings)

    def test_multiple_sedatives(self):
        """Test that multiple sedatives trigger warning."""
        inputs = {
            'renalImpairment': False,
            'nsaid_choice': 'Ej given',
            'age': 45,
            'opioidHistory': 'Opioidnaiv',
            'droperidol': True,
            'ketamine_choice': 'Liten bolus (0.05-0.1 mg/kg)',
            'catapressan_dose': 75
        }
        warnings = validate_drug_contraindications(inputs)
        assert len(warnings) > 0
        assert any('sedativa' in w.lower() for w in warnings)

    def test_no_contraindications(self):
        """Test that normal case has no warnings."""
        inputs = {
            'renalImpairment': False,
            'nsaid_choice': 'Ibuprofen 400mg',
            'age': 45,
            'opioidHistory': 'Opioidnaiv',
            'droperidol': False,
            'ketamine_choice': 'Ej given',
            'catapressan_dose': 0
        }
        warnings = validate_drug_contraindications(inputs)
        assert len(warnings) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
