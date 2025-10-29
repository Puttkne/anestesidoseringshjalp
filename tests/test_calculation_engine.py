"""
Unit Tests for Calculation Engine
==================================
Tests for dose calculation, weight adjustments, and age factors.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calculation_engine import (
    calculate_bmi,
    calculate_ideal_body_weight,
    calculate_adjusted_body_weight,
    calculate_age_factor
)


class TestBMICalculation:
    """Test BMI calculation."""

    def test_normal_bmi(self):
        """Test normal BMI calculation."""
        # 75 kg, 175 cm should be ~24.49
        bmi = calculate_bmi(75, 175)
        assert 24.4 < bmi < 24.5

    def test_overweight_bmi(self):
        """Test overweight BMI calculation."""
        # 100 kg, 175 cm should be ~32.65
        bmi = calculate_bmi(100, 175)
        assert 32.6 < bmi < 32.7

    def test_zero_height(self):
        """Test that zero height returns 0."""
        bmi = calculate_bmi(75, 0)
        assert bmi == 0.0

    def test_zero_weight(self):
        """Test that zero weight returns 0."""
        bmi = calculate_bmi(0, 175)
        assert bmi == 0.0

    def test_negative_values(self):
        """Test that negative values return 0."""
        bmi = calculate_bmi(-75, 175)
        assert bmi == 0.0


class TestIdealBodyWeight:
    """Test IBW calculation."""

    def test_male_ibw(self):
        """Test IBW for male."""
        # 175 cm male: 175 - 100 = 75 kg
        ibw = calculate_ideal_body_weight(175, 'Man')
        assert ibw == 75.0

    def test_female_ibw(self):
        """Test IBW for female."""
        # 165 cm female: 165 - 105 = 60 kg
        ibw = calculate_ideal_body_weight(165, 'Kvinna')
        assert ibw == 60.0

    def test_minimum_ibw(self):
        """Test that IBW never goes below 40 kg."""
        # Very short person
        ibw = calculate_ideal_body_weight(100, 'Man')
        assert ibw == 40.0


class TestAdjustedBodyWeight:
    """Test ABW calculation."""

    def test_normal_weight_patient(self):
        """Test that normal weight patients use actual weight."""
        # 75 kg is normal for 175 cm
        abw = calculate_adjusted_body_weight(75, 175, 'Man')
        assert abw == 75.0

    def test_overweight_patient(self):
        """Test adjusted weight for overweight patient."""
        # 100 kg for 175 cm (IBW=75)
        # Overvikt: 100-75=25, ABW: 75 + (25*0.4) = 85
        abw = calculate_adjusted_body_weight(100, 175, 'Man')
        assert abw == 85.0

    def test_slightly_overweight_no_adjustment(self):
        """Test that slight overweight (<20%) uses actual weight."""
        # IBW=75, 20% over = 90
        abw = calculate_adjusted_body_weight(89, 175, 'Man')
        assert abw == 89.0


class TestAgeFactor:
    """Test age-based dose reduction."""

    def test_young_patient_no_reduction(self):
        """Test that young patients get factor 1.0."""
        factor = calculate_age_factor(30)
        assert factor == 1.0

    def test_reference_age_no_reduction(self):
        """Test that reference age (65) gets factor 1.0."""
        factor = calculate_age_factor(65)
        assert factor == 1.0

    def test_elderly_patient_reduction(self):
        """Test that elderly patients get reduced factor."""
        factor = calculate_age_factor(80)
        assert 0.4 < factor < 1.0

    def test_very_elderly_minimum(self):
        """Test that very elderly get minimum factor."""
        factor = calculate_age_factor(100)
        assert factor >= 0.4

    def test_age_factor_decreases_with_age(self):
        """Test that age factor decreases monotonically."""
        factor_70 = calculate_age_factor(70)
        factor_80 = calculate_age_factor(80)
        factor_90 = calculate_age_factor(90)
        assert factor_70 > factor_80 > factor_90


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
