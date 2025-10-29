"""
Test Runner
===========
Run all tests and generate coverage report.
"""

import pytest
import sys

def run_all_tests():
    """Run all tests with coverage."""
    args = [
        'tests/',
        '-v',
        '--tb=short',
        '--cov=.',
        '--cov-report=html',
        '--cov-report=term',
        '-W', 'ignore::DeprecationWarning'
    ]

    exit_code = pytest.main(args)
    return exit_code


def run_unit_tests():
    """Run only unit tests."""
    args = [
        'tests/test_calculation_engine.py',
        'tests/test_validation.py',
        '-v'
    ]
    return pytest.main(args)


def run_safety_tests():
    """Run only safety tests."""
    args = [
        'tests/test_safety.py',
        '-v',
        '-s'  # Show print statements for safety test details
    ]
    return pytest.main(args)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'unit':
            exit_code = run_unit_tests()
        elif sys.argv[1] == 'safety':
            exit_code = run_safety_tests()
        else:
            print("Usage: python run_tests.py [unit|safety]")
            print("  No args: Run all tests")
            print("  unit: Run only unit tests")
            print("  safety: Run only safety tests")
            exit_code = 1
    else:
        exit_code = run_all_tests()

    sys.exit(exit_code)
