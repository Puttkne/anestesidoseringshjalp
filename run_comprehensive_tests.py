"""
Comprehensive Test Runner for Anestesi-assistent v8.0
Runs the full test suite and generates a detailed report.
"""

import subprocess
import sys
import io
import os
from pathlib import Path
from datetime import datetime
import json

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("Checking dependencies...")

    required_packages = {
        'pytest': 'pytest',
        'playwright': 'playwright',
        'requests': 'requests'
    }

    missing = []
    for package, pip_name in required_packages.items():
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (missing)")
            missing.append(pip_name)

    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False

    print("  ✓ All dependencies installed")
    return True

def check_playwright_browsers():
    """Check if Playwright browsers are installed"""
    print("\nChecking Playwright browsers...")

    try:
        result = subprocess.run(
            ["playwright", "install", "--dry-run", "chromium"],
            capture_output=True,
            text=True
        )

        if "chromium" in result.stdout.lower():
            print("  ℹ️  Playwright browsers may need installation")
            print("  Run: playwright install chromium")
            return False
        else:
            print("  ✓ Playwright browsers installed")
            return True
    except Exception as e:
        print(f"  ⚠️  Could not check Playwright installation: {e}")
        return False

def create_test_report_dir():
    """Create directory for test reports"""
    report_dir = Path("test_reports")
    report_dir.mkdir(exist_ok=True)
    return report_dir

def run_tests(test_file=None, verbose=True, screenshots=True):
    """Run the test suite"""
    print("\n" + "=" * 80)
    print("RUNNING COMPREHENSIVE TEST SUITE")
    print("=" * 80)

    report_dir = create_test_report_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Prepare pytest command (use python -m pytest for Windows compatibility)
    cmd = [sys.executable, "-m", "pytest"]

    if test_file:
        cmd.append(test_file)
    else:
        cmd.append("tests/test_full_app_comprehensive.py")

    if verbose:
        cmd.append("-v")
        cmd.append("-s")

    # Add HTML report
    html_report = report_dir / f"test_report_{timestamp}.html"
    cmd.extend(["--html", str(html_report), "--self-contained-html"])

    # Add JUnit XML report
    xml_report = report_dir / f"test_report_{timestamp}.xml"
    cmd.extend(["--junit-xml", str(xml_report)])

    # Add traceback style
    cmd.append("--tb=short")

    print(f"\nRunning: {' '.join(cmd)}")
    print(f"HTML Report: {html_report}")
    print(f"XML Report: {xml_report}")
    print("\n")

    # Run tests
    start_time = datetime.now()
    result = subprocess.run(cmd)
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n" + "=" * 80)
    print("TEST SUITE COMPLETED")
    print("=" * 80)
    print(f"Duration: {duration:.2f} seconds")
    print(f"Exit code: {result.returncode}")

    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. Check the reports for details.")

    print(f"\nReports saved to: {report_dir.absolute()}")

    return result.returncode

def run_specific_test_class(class_name):
    """Run a specific test class"""
    print(f"\nRunning specific test class: {class_name}")

    cmd = [
        "pytest",
        "tests/test_full_app_comprehensive.py",
        "-k", class_name,
        "-v", "-s"
    ]

    result = subprocess.run(cmd)
    return result.returncode

def list_available_tests():
    """List all available test classes and tests"""
    print("\n" + "=" * 80)
    print("AVAILABLE TESTS")
    print("=" * 80)

    cmd = [
        "pytest",
        "tests/test_full_app_comprehensive.py",
        "--collect-only", "-q"
    ]

    subprocess.run(cmd)

def print_usage():
    """Print usage information"""
    print("""
Usage: python run_comprehensive_tests.py [options]

Options:
    --all               Run all tests (default)
    --auth              Run only authentication tests
    --dosing            Run only dosing tab tests
    --history           Run only history tab tests
    --learning          Run only learning tab tests
    --procedures        Run only procedures tab tests
    --admin             Run only admin tab tests
    --integration       Run only integration tests
    --list              List all available tests
    --check             Check dependencies only
    --help              Show this help message

Examples:
    python run_comprehensive_tests.py
    python run_comprehensive_tests.py --auth
    python run_comprehensive_tests.py --dosing
    python run_comprehensive_tests.py --list
""")

def main():
    """Main entry point"""
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print_usage()
        return 0

    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies before running tests.")
        return 1

    check_playwright_browsers()

    if "--check" in args:
        return 0

    if "--list" in args:
        list_available_tests()
        return 0

    # Run specific test class
    test_mapping = {
        "--auth": "TestAuthentication",
        "--dosing": "TestDosingTab",
        "--history": "TestHistoryTab",
        "--learning": "TestLearningTab",
        "--procedures": "TestProceduresTab",
        "--admin": "TestAdminTab",
        "--integration": "TestIntegration"
    }

    for arg, class_name in test_mapping.items():
        if arg in args:
            return run_specific_test_class(class_name)

    # Run all tests
    return run_tests()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
