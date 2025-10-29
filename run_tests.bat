@echo off
REM Comprehensive test runner for Anestesidoseringshjälp
REM This script runs the Playwright test suite

echo ========================================
echo Anestesidoseringshjälp Test Suite
echo ========================================
echo.

REM Check if Streamlit is running
echo [INFO] Checking if Streamlit app is running...
curl -s http://localhost:8501 > nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Streamlit app is not running on http://localhost:8501
    echo [INFO] Please start the app first with: streamlit run oxydos_v8.py
    echo.
    choice /C YN /M "Do you want to start the app now"
    if errorlevel 2 goto :skip_start
    if errorlevel 1 goto :start_app
) else (
    echo [OK] Streamlit app is running!
    echo.
    goto :run_tests
)

:start_app
echo [INFO] Starting Streamlit app...
start "Streamlit App" cmd /k "streamlit run oxydos_v8.py"
echo [INFO] Waiting 10 seconds for app to start...
timeout /t 10 /nobreak > nul
goto :run_tests

:skip_start
echo [INFO] Skipping app start. Make sure to start it manually.
echo.

:run_tests
REM Create screenshots directory
if not exist "test_screenshots" mkdir test_screenshots

echo [INFO] Running comprehensive Playwright test suite...
echo.

REM Run the test
python test_comprehensive_playwright.py

REM Check exit code
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo [SUCCESS] All tests passed!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo [FAILURE] Some tests failed!
    echo ========================================
    echo Check test_screenshots folder for visual evidence
)

echo.
echo Screenshots saved in: test_screenshots\
echo.

pause
