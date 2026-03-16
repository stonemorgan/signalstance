#!/usr/bin/env bash
# =============================================================================
# SignalStance Audit Suite Runner
# =============================================================================
# Runs a comprehensive 4-phase audit of the SignalStance codebase using
# specialized Claude Code agents.
#
# Usage:
#   ./scripts/run-audit.sh              # Full audit (all phases)
#   ./scripts/run-audit.sh --audit-only # Only run audit + triage (no fixes)
#   ./scripts/run-audit.sh --resume     # Resume a previously interrupted audit
#
# Output: All reports saved to audit-reports/
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              SignalStance Audit Suite                       ║"
echo "║         Comprehensive Codebase Review & Fix                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Parse arguments
AUDIT_ONLY=false
RESUME=false
for arg in "$@"; do
    case $arg in
        --audit-only)
            AUDIT_ONLY=true
            echo -e "${YELLOW}Mode: Audit + Triage only (no implementation)${NC}"
            ;;
        --resume)
            RESUME=true
            echo -e "${YELLOW}Mode: Resuming previous audit${NC}"
            ;;
        --help|-h)
            echo "Usage: ./scripts/run-audit.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --audit-only    Run audit and triage phases only (no code changes)"
            echo "  --resume        Resume a previously interrupted audit"
            echo "  --help, -h      Show this help message"
            echo ""
            echo "Output:"
            echo "  All reports are saved to audit-reports/"
            echo ""
            echo "Phases:"
            echo "  1. AUDIT      6 specialized agents analyze the codebase in parallel"
            echo "  2. TRIAGE     Findings synthesized into a priority-ranked report"
            echo "  3. IMPLEMENT  Critical and High priority fixes applied"
            echo "  4. TEST       Test coverage built around fixes"
            exit 0
            ;;
    esac
done

cd "$PROJECT_DIR"

# Create output directory
mkdir -p audit-reports

# Timestamp for this run
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
echo -e "${BLUE}Audit started: ${TIMESTAMP}${NC}"
echo -e "${BLUE}Project: ${PROJECT_DIR}${NC}"
echo ""

# Build the prompt based on mode
if [ "$AUDIT_ONLY" = true ]; then
    PROMPT="Run the full SignalStance audit workflow but STOP after Phase 2 (Triage). Do NOT proceed to Phase 3 (Implementation) or Phase 4 (Testing). Save all reports to audit-reports/."
elif [ "$RESUME" = true ]; then
    PROMPT="Resume the SignalStance audit workflow. Check audit-reports/ for any existing reports from a previous run. Continue from where the previous run left off — skip phases whose reports already exist."
else
    PROMPT="Run the full SignalStance audit workflow through all 4 phases. Save all reports to audit-reports/."
fi

# Run the audit suite
echo -e "${GREEN}Launching audit-suite orchestrator...${NC}"
echo -e "${YELLOW}This will spawn 6+ specialized agents. Expect significant compute usage.${NC}"
echo ""

claude --agent audit-suite -p "$PROMPT"

# Check results
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗"
echo -e "║                    Audit Complete                           ║"
echo -e "╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ -d "audit-reports" ]; then
    echo -e "${GREEN}Reports saved to audit-reports/:${NC}"
    ls -la audit-reports/*.md 2>/dev/null || echo "  (no reports found)"
else
    echo -e "${RED}No audit-reports directory found. Something went wrong.${NC}"
fi
