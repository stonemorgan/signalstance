@echo off
REM =============================================================================
REM SignalStance Audit Suite Runner (Windows)
REM =============================================================================
REM Usage:
REM   scripts\run-audit.bat              Full audit (all phases)
REM   scripts\run-audit.bat --audit-only Only run audit + triage (no fixes)
REM =============================================================================

echo.
echo ================================================================
echo              SignalStance Audit Suite
echo         Comprehensive Codebase Review ^& Fix
echo ================================================================
echo.

cd /d "%~dp0\.."

if not exist audit-reports mkdir audit-reports

set PROMPT=Run the full SignalStance audit workflow through all 4 phases. Save all reports to audit-reports/.

if "%~1"=="--audit-only" (
    echo Mode: Audit + Triage only ^(no implementation^)
    set PROMPT=Run the full SignalStance audit workflow but STOP after Phase 2 ^(Triage^). Do NOT proceed to Phase 3 or Phase 4. Save all reports to audit-reports/.
)

if "%~1"=="--help" (
    echo Usage: scripts\run-audit.bat [OPTIONS]
    echo.
    echo Options:
    echo   --audit-only    Run audit and triage phases only ^(no code changes^)
    echo   --help          Show this help message
    echo.
    echo Output: All reports saved to audit-reports/
    exit /b 0
)

echo Launching audit-suite orchestrator...
echo This will spawn 6+ specialized agents. Expect significant compute usage.
echo.

claude --agent audit-suite -p "%PROMPT%"

echo.
echo ================================================================
echo                    Audit Complete
echo ================================================================
echo.
echo Reports saved to audit-reports/:
dir /b audit-reports\*.md 2>nul || echo   (no reports found)
