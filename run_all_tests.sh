#!/bin/bash
#
# Run All Tests
#
# Runs the complete test suite and generates a summary report.
# Exit code 0 = all tests passed, 1 = some tests failed
#
# Usage:
#   ./run_all_tests.sh
#   ./run_all_tests.sh --verbose

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if verbose mode
VERBOSE=false
if [[ "$1" == "--verbose" ]]; then
    VERBOSE=true
fi

# Change to script directory
cd "$(dirname "$0")"

echo "================================================================================"
echo "                         FLIGHT DEAL SCRAPER TEST SUITE"
echo "================================================================================"
echo ""
echo "Running comprehensive tests..."
echo ""

# Track results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=()

# Function to run a test
run_test() {
    local test_name="$1"
    local test_script="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo "--------------------------------------------------------------------------------"
    echo "Running: $test_name"
    echo "--------------------------------------------------------------------------------"
    
    if $VERBOSE; then
        if python3 "$test_script"; then
            PASSED_TESTS=$((PASSED_TESTS + 1))
            echo -e "${GREEN}✓ PASSED${NC}: $test_name"
        else
            FAILED_TESTS+=("$test_name")
            echo -e "${RED}✗ FAILED${NC}: $test_name"
        fi
    else
        # Capture output
        if output=$(python3 "$test_script" 2>&1); then
            PASSED_TESTS=$((PASSED_TESTS + 1))
            echo -e "${GREEN}✓ PASSED${NC}: $test_name"
        else
            FAILED_TESTS+=("$test_name")
            echo -e "${RED}✗ FAILED${NC}: $test_name"
            echo "Error output:"
            echo "$output" | tail -20
        fi
    fi
    
    echo ""
}

# Run all tests
run_test "Full System Integration" "test_full_system.py"
run_test "Database Integrity" "test_database_integrity.py"
run_test "Quality Scoring System" "test_quality_scoring.py"

# Print summary
echo "================================================================================"
echo "                              TEST SUMMARY"
echo "================================================================================"
echo ""
echo "Total Tests:  $TOTAL_TESTS"
echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed:       ${RED}$((TOTAL_TESTS - PASSED_TESTS))${NC}"
echo ""

if [ ${#FAILED_TESTS[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
    echo "================================================================================"
    echo ""
    echo "System is ready for production use!"
    echo ""
    echo "Next steps:"
    echo "  1. Set up daily automation (see TESTING_GUIDE.md)"
    echo "  2. Run: python scripts/calculate_price_insights.py --verbose"
    echo "  3. Run: python test_price_insights_scoring.py"
    echo ""
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    echo ""
    echo "Failed tests:"
    for test in "${FAILED_TESTS[@]}"; do
        echo "  - $test"
    done
    echo ""
    echo "================================================================================"
    echo ""
    echo "Please fix the failing tests before proceeding."
    echo "Run with --verbose flag for detailed output:"
    echo "  ./run_all_tests.sh --verbose"
    echo ""
    exit 1
fi
