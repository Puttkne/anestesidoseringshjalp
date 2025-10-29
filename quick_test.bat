@echo off
REM Quick Test Runner for Anestesi-assistent v8.0
REM Run this to execute the full test suite

echo ================================================================================
echo   ANESTESI-ASSISTENT V8.0 - COMPREHENSIVE TEST SUITE
echo ================================================================================
echo.
echo Running all 44 tests...
echo.

python run_comprehensive_tests.py

echo.
echo ================================================================================
echo   TEST SUITE COMPLETED
echo ================================================================================
echo.
echo Check test_reports\ folder for detailed HTML reports
echo.
pause
