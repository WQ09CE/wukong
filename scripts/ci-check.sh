#!/bin/bash
#
# Local CI Check - Run before creating PR
#
# This script mirrors the GitHub Actions CI workflow to catch issues
# before pushing. Prevents the "local passes, CI fails" problem.
#
# Usage:
#   ./scripts/ci-check.sh          # Run all checks
#   ./scripts/ci-check.sh --quick  # Skip slow tests (Windows matrix)
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

QUICK_MODE=false
if [ "$1" = "--quick" ]; then
    QUICK_MODE=true
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Wukong Local CI Check${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Track failures
FAILED=0

# Step 1: Shell Lint
echo -e "${YELLOW}[1/3] Shell Lint (shellcheck)${NC}"
if command -v shellcheck &> /dev/null; then
    if shellcheck install.sh; then
        echo -e "  ${GREEN}✓${NC} install.sh passed"
    else
        echo -e "  ${RED}✗${NC} install.sh failed"
        FAILED=1
    fi
else
    echo -e "  ${YELLOW}⚠${NC} shellcheck not installed, skipping"
    echo "     Install with: brew install shellcheck (macOS) or apt install shellcheck (Linux)"
fi
echo ""

# Step 2: Python Tests
echo -e "${YELLOW}[2/3] Python Tests (pytest)${NC}"

# Try to activate conda if available (for pytest)
CONDA_SH="/opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh"
if [ -f "$CONDA_SH" ]; then
    # shellcheck source=/dev/null
    source "$CONDA_SH"
    conda activate base 2>/dev/null || true
fi

# Find pytest: conda env > system > error
if command -v pytest &> /dev/null; then
    PYTEST_CMD="pytest"
elif python3 -c "import pytest" 2>/dev/null; then
    PYTEST_CMD="python3 -m pytest"
else
    echo -e "  ${RED}✗${NC} pytest not found"
    echo "     Install with: pip install pytest (or conda install pytest)"
    FAILED=1
    PYTEST_CMD=""
fi

if [ -n "$PYTEST_CMD" ]; then
    if $PYTEST_CMD tests/ -v --tb=short; then
        echo -e "  ${GREEN}✓${NC} All tests passed"
    else
        echo -e "  ${RED}✗${NC} Tests failed"
        FAILED=1
    fi
fi
echo ""

# Step 3: Installation Test (optional in quick mode)
echo -e "${YELLOW}[3/3] Installation Test${NC}"
if [ "$QUICK_MODE" = true ]; then
    echo -e "  ${YELLOW}⚠${NC} Skipped (--quick mode)"
else
    TEMP_DIR=$(mktemp -d)
    if bash install.sh "$TEMP_DIR" <<< "n" > /dev/null 2>&1; then
        # Verify key files
        if [ -f "$TEMP_DIR/.claude/rules/00-wukong-core.md" ] && \
           [ -d "$TEMP_DIR/.wukong/runtime" ]; then
            echo -e "  ${GREEN}✓${NC} Installation test passed"
        else
            echo -e "  ${RED}✗${NC} Installation verification failed"
            FAILED=1
        fi
    else
        echo -e "  ${RED}✗${NC} Installation script failed"
        FAILED=1
    fi
    rm -rf "$TEMP_DIR"
fi
echo ""

# Summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}  All checks passed! Safe to create PR.${NC}"
else
    echo -e "${RED}  Some checks failed. Fix before creating PR.${NC}"
fi
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

exit $FAILED
