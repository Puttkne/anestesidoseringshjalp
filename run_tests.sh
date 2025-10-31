#!/bin/bash
# Comprehensive test runner for Anestesidoseringshjälp
# This script runs the Playwright test suite

echo "========================================"
echo "Anestesidoseringshjälp Test Suite"
echo "========================================"
echo ""

# Check if Streamlit is running
echo "[INFO] Checking if Streamlit app is running..."
if curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo "[OK] Streamlit app is running!"
    echo ""
else
    echo "[WARNING] Streamlit app is not running on http://localhost:8501"
    echo "[INFO] Please start the app first with: streamlit run oxydoseks.py"
    echo ""
    read -p "Do you want to start the app now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "[INFO] Starting Streamlit app..."
        streamlit run oxydoseks.py &
        STREAMLIT_PID=$!
        echo "[INFO] Waiting 10 seconds for app to start..."
        sleep 10
    else
        echo "[INFO] Skipping app start. Make sure to start it manually."
        echo ""
    fi
fi

# Create screenshots directory
mkdir -p test_screenshots

echo "[INFO] Running comprehensive Playwright test suite..."
echo ""

# Run the test
python test_comprehensive_playwright.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "[SUCCESS] All tests passed!"
    echo "========================================"
else
    echo ""
    echo "========================================"
    echo "[FAILURE] Some tests failed!"
    echo "========================================"
    echo "Check test_screenshots folder for visual evidence"
fi

echo ""
echo "Screenshots saved in: test_screenshots/"
echo ""

# Kill Streamlit if we started it
if [ ! -z "$STREAMLIT_PID" ]; then
    read -p "Stop the Streamlit app? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill $STREAMLIT_PID
        echo "[INFO] Streamlit app stopped"
    fi
fi
