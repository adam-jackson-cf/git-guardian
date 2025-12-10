#!/usr/bin/env bash
# Test script for install.sh
# Verifies the installer works correctly in various modes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
INSTALL_SCRIPT="${REPO_ROOT}/install.sh"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

test_count=0
pass_count=0
fail_count=0

test_pass() {
    test_count=$((test_count + 1))
    pass_count=$((pass_count + 1))
    echo -e "${GREEN}✓${NC} $1"
}

test_fail() {
    test_count=$((test_count + 1))
    fail_count=$((fail_count + 1))
    echo -e "${RED}✗${NC} $1"
    return 1
}

echo "Testing Guardian installer..."
echo ""

# Test 1: Syntax check
echo "Test 1: Syntax validation"
if bash -n "${INSTALL_SCRIPT}"; then
    test_pass "install.sh syntax is valid"
else
    test_fail "install.sh has syntax errors"
fi
echo ""

# Test 2: Help output
echo "Test 2: Help command"
if "${INSTALL_SCRIPT}" --help 2>&1 | grep -q "Guardian Installer"; then
    test_pass "Help command works"
else
    test_fail "Help command failed"
fi
echo ""

# Test 3: Dry run
echo "Test 3: Dry run mode"
output=$("${INSTALL_SCRIPT}" --dry-run --non-interactive 2>&1)
if echo "$output" | grep -qi "guardian\|install"; then
    test_pass "Dry run mode works"
else
    test_fail "Dry run mode failed"
fi
echo ""

# Test 4: Dry run with easy mode
echo "Test 4: Dry run with easy mode"
output=$("${INSTALL_SCRIPT}" --dry-run --easy-mode --non-interactive 2>&1)
if echo "$output" | grep -qi "guardian\|install"; then
    test_pass "Dry run with easy mode works"
else
    test_fail "Dry run with easy mode failed"
fi
echo ""

# Test 5: Minimal mode
echo "Test 5: Minimal mode"
output=$("${INSTALL_SCRIPT}" --dry-run --minimal --non-interactive 2>&1)
if echo "$output" | grep -qi "guardian\|install"; then
    test_pass "Minimal mode works"
else
    test_fail "Minimal mode failed"
fi
echo ""

# Test 6: Uninstall dry run
echo "Test 6: Uninstall dry run"
if "${INSTALL_SCRIPT}" --uninstall --dry-run 2>&1 | grep -q "Would uninstall"; then
    test_pass "Uninstall dry run works"
else
    test_fail "Uninstall dry run failed"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test Results:"
echo "  Total:  ${test_count}"
echo "  Passed: ${pass_count}"
echo "  Failed: ${fail_count}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ ${fail_count} -eq 0 ]]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed${NC}"
    exit 1
fi
