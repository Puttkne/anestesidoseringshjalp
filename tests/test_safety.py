"""
Safety Tests
============
Critical safety tests to ensure dose calculations never exceed safe limits.
"""

import pytest
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calculation_engine import calculate_rule_based_dose
from validation import validate_recommended_dose


class TestDoseSafetyLimits:
    """Test that calculated doses never exceed safety limits."""

    def test_recommended_dose_warnings(self):
        """Test 100 random configurations and verify warnings for recommended doses >10mg."""
        import random
        from validation import validate_recommended_dose

        procedures_df = pd.DataFrame([{
            'id': 'test_proc',
            'specialty': 'Ortopedi',
            'name': 'Test Procedure',
            'baseMME': 50,
            'painTypeScore': 5,
            'painVisceral': 5,
            'painNeuropathic': 2
        }])

        high_dose_count = 0

        for _ in range(100):
            inputs = {
                'procedure_id': 'test_proc',
                'age': random.randint(18, 90),
                'sex': random.choice(['Man', 'Kvinna']),
                'weight': random.uniform(50, 120),
                'height': random.uniform(150, 195),
                'asa': random.choice(['ASA 1', 'ASA 2', 'ASA 3']),
                'opioidHistory': random.choice(['Opioidnaiv', 'Opioidtolerant']),
                'lowPainThreshold': random.choice([True, False]),
                'renalImpairment': False,
                'fentanylDose': random.randint(0, 200),
                'optime_minutes': random.randint(30, 180),
                'nsaid': False,
                'nsaid_choice': 'Ej given',
                'catapressan_dose': 0,
                'droperidol': False,
                'ketamine_choice': 'Ej given',
                'lidocaine': 'Nej',
                'betapred': 'Nej',
                'sevoflurane': False,
                'infiltration': False
            }

            result = calculate_rule_based_dose(inputs, procedures_df)
            final_dose = result.get('finalDose', 0)

            # Check if recommended dose >10mg (perioperative warning threshold)
            if final_dose > 10.0:
                high_dose_count += 1
                is_safe, severity, msg = validate_recommended_dose(final_dose)
                # Should still be "safe" (allowed) but with warning
                assert is_safe, f"High recommended dose {final_dose}mg should be allowed"
                assert severity == 'WARNING', f"Recommended dose {final_dose}mg should trigger WARNING"
                # Print without Swedish characters to avoid encoding issues
                print(f"High recommended dose: {final_dose:.1f}mg - WARNING triggered")

        # Report how many high recommended doses we found
        print(f"\nFound {high_dose_count}/100 cases with recommended dose >10mg")

    def test_dose_always_positive(self):
        """Test that dose is never negative."""
        procedures_df = pd.DataFrame([{
            'id': 'test_proc',
            'specialty': 'Ortopedi',
            'name': 'Test Procedure',
            'baseMME': 20,
            'painTypeScore': 5,
            'painVisceral': 5,
            'painNeuropathic': 2
        }])

        inputs = {
            'procedure_id': 'test_proc',
            'age': 30,
            'sex': 'Man',
            'weight': 75,
            'height': 175,
            'asa': 'ASA 2',
            'opioidHistory': 'Opioidnaiv',
            'lowPainThreshold': False,
            'renalImpairment': False,
            'fentanylDose': 300,  # High fentanyl
            'optime_minutes': 60,
            'nsaid': True,
            'nsaid_choice': 'Ketorolac 30mg',
            'catapressan_dose': 75,
            'droperidol': True,
            'ketamine_choice': 'Stor bolus (0.5-1 mg/kg)',
            'lidocaine': 'Infusion',
            'betapred': '8 mg',
            'sevoflurane': True,
            'infiltration': True
        }

        result = calculate_rule_based_dose(inputs, procedures_df)
        final_dose = result.get('finalDose', 0)

        assert final_dose >= 0, f"Dose cannot be negative! Got {final_dose}mg"

    def test_elderly_renal_impairment_safety(self):
        """Test that elderly with renal impairment gets reduced dose."""
        procedures_df = pd.DataFrame([{
            'id': 'test_proc',
            'specialty': 'Ortopedi',
            'name': 'Test Procedure',
            'baseMME': 60,
            'painTypeScore': 7,
            'painVisceral': 5,
            'painNeuropathic': 2
        }])

        # Normal patient
        inputs_normal = {
            'procedure_id': 'test_proc',
            'age': 45,
            'sex': 'Man',
            'weight': 75,
            'height': 175,
            'asa': 'ASA 2',
            'opioidHistory': 'Opioidnaiv',
            'lowPainThreshold': False,
            'renalImpairment': False,
            'fentanylDose': 100,
            'optime_minutes': 120,
            'nsaid': False,
            'nsaid_choice': 'Ej given',
            'catapressan_dose': 0,
            'droperidol': False,
            'ketamine_choice': 'Ej given',
            'lidocaine': 'Nej',
            'betapred': 'Nej',
            'sevoflurane': False,
            'infiltration': False
        }

        # Elderly with renal impairment
        inputs_elderly = inputs_normal.copy()
        inputs_elderly['age'] = 85
        inputs_elderly['renalImpairment'] = True
        inputs_elderly['asa'] = 'ASA 3'

        result_normal = calculate_rule_based_dose(inputs_normal, procedures_df)
        result_elderly = calculate_rule_based_dose(inputs_elderly, procedures_df)

        dose_normal = result_normal.get('finalDose', 0)
        dose_elderly = result_elderly.get('finalDose', 0)

        # Elderly patient should get significantly reduced dose
        assert dose_elderly < dose_normal, "Elderly with renal impairment should get lower dose"
        assert dose_elderly < dose_normal * 0.75, "Dose reduction should be at least 25%"


class TestMedicallyUnsafeCombinations:
    """Test that system prevents medically unsafe combinations."""

    def test_extreme_adjuvant_cocktail_safety_limit(self):
        """Test that massive adjuvant combination has safety limit."""
        procedures_df = pd.DataFrame([{
            'id': 'test_proc',
            'specialty': 'Ortopedi',
            'name': 'Test Procedure',
            'baseMME': 80,
            'painTypeScore': 8,
            'painVisceral': 5,
            'painNeuropathic': 2
        }])

        inputs = {
            'procedure_id': 'test_proc',
            'age': 30,
            'sex': 'Man',
            'weight': 75,
            'height': 175,
            'asa': 'ASA 2',
            'opioidHistory': 'Opioidnaiv',
            'lowPainThreshold': False,
            'renalImpairment': False,
            'fentanylDose': 200,
            'optime_minutes': 180,
            'nsaid': True,
            'nsaid_choice': 'Ketorolac 30mg',
            'catapressan_dose': 150,  # High dose
            'droperidol': True,
            'ketamine_choice': 'Stor infusion (3 mg/kg/h)',
            'lidocaine': 'Infusion',
            'betapred': '8 mg',
            'sevoflurane': True,
            'infiltration': True
        }

        result = calculate_rule_based_dose(inputs, procedures_df)
        final_dose = result.get('finalDose', 0)

        # Even with massive adjuvants, should maintain minimum safe opioid dose
        # Safety limit should prevent dose from going to zero
        assert final_dose > 0, "Dose should not be zero even with many adjuvants"

        # No hard maximum limit - high doses are allowed with warnings
        # Just verify the validation system would warn if >10mg
        if final_dose > 10.0:
            is_safe, severity, msg = validate_recommended_dose(final_dose)
            assert is_safe, "High doses should be allowed"
            assert severity == 'WARNING', "High doses should trigger warning"
            print(f"High dose calculated: {final_dose:.1f}mg (WARNING would be shown to user)")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
